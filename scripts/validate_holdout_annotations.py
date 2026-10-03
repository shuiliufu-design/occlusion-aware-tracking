"""只核查 HOLDOUT 来源、公共缓存和独立标注；不推进 A/B/C 状态或评价效果。"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

import cv2

try:
    from .evaluate_comparison import validate_labels
    from .evaluation_sources import read_json, verify_snapshot
    from .m3_common import checked_file, empty_output, load_case, load_protocol
    from .review_baseline import review as review_baseline
    from .run_target_state import TargetState, sha256, write_json
except ImportError:
    from evaluate_comparison import validate_labels
    from evaluation_sources import read_json, verify_snapshot
    from m3_common import checked_file, empty_output, load_case, load_protocol
    from review_baseline import review as review_baseline
    from run_target_state import TargetState, sha256, write_json


def validate_frame_labels(frames, start, end, stride, width, height):
    """完整固定抽样和人工几何边界；UNKNOWN/局部不猜完整框。"""
    seen, fixed = set(), set()
    for label in frames:
        i = label['frame_index']
        if type(i) is not int or i in seen or not start <= i < end:
            raise ValueError('标注帧重复/越界')
        seen.add(i)
        if label['origin'] not in ('FIXED_SAMPLE', 'EVENT_KEYFRAME'):
            raise ValueError('标注来源无效')
        if label['origin'] == 'FIXED_SAMPLE':
            if (i - start) % stride:
                raise ValueError('关键帧混入固定抽样')
            fixed.add(i)
        if label['identity'] not in ('T1', 'OTHER_BOTTLE', 'UNKNOWN', 'UNCERTAIN'):
            raise ValueError('人工身份编码无效')
        visibility = label['visibility']
        if visibility not in ('CLEAR', 'PARTIAL', 'OCCLUDED', 'UNCERTAIN'):
            raise ValueError('人工可见性编码无效')
        box = label.get('bbox_xyxy')
        if visibility == 'CLEAR':
            if label['identity'] not in ('T1', 'OTHER_BOTTLE') or box is None:
                raise ValueError('清楚可见须有确定身份与人工框')
        elif box is not None:
            raise ValueError('本标注包局部/未知不可补完整框')
        if box is not None and (len(box) != 4 or
                not all(type(v) in (int, float) and math.isfinite(v) for v in box) or
                not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)):
            raise ValueError('人工框超出原图或无效')
        if visibility == 'OCCLUDED' and label['identity'] != 'UNKNOWN':
            raise ValueError('完全遮挡不能伪造可见身份')
        if visibility == 'UNCERTAIN' and label['identity'] != 'UNCERTAIN':
            raise ValueError('不确定边界不能强判身份')
        for key in ('timestamp_seconds', 'source_pos_msec_seconds'):
            value = label[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError('人工原帧时间无效')
    planned = set(range(start, end, stride))
    if fixed != planned:
        raise ValueError('固定抽样缺帧或多出样本')
    return {'fixed_samples_planned': len(planned), 'fixed_samples_checked': len(fixed),
            'additional_keyframes': len(seen - fixed), 'unreviewed_fixed_samples': [],
            'fixed_partial_or_uncertain_geometry': [k['frame_index'] for k in frames
                if k['origin'] == 'FIXED_SAMPLE' and k['visibility'] in ('PARTIAL', 'UNCERTAIN')],
            'uncertain_frames': [k['frame_index'] for k in frames if k['identity'] == 'UNCERTAIN'],
            'fixed_visibility_counts': dict(Counter(k['visibility'] for k in frames if k['origin'] == 'FIXED_SAMPLE'))}


def validate_visibility_intervals(intervals, frames, start, end):
    cursor = start
    for span in intervals:
        if type(span['start_frame']) is not int or type(span['end_frame_exclusive']) is not int:
            raise ValueError('可见区间须是原帧整数')
        if span['start_frame'] != cursor or not cursor < span['end_frame_exclusive'] <= end:
            raise ValueError('可见区间存在空隙/重叠/越界')
        cursor = span['end_frame_exclusive']
    if cursor != end:
        raise ValueError('可见区间未覆盖处理范围')
    for label in frames:
        span = next(s for s in intervals if s['start_frame'] <= label['frame_index'] < s['end_frame_exclusive'])
        if any(span[k] != label[k] for k in ('identity', 'visibility')):
            raise ValueError('原帧标签与可见区间不一致')


def validate_event(event, physical, labels, expected_return):
    if event['expected_return'] is not expected_return:
        raise ValueError('人工返回机会与用户物理操作矛盾')
    start = event['recognizable_reappearance_frame']
    if expected_return:
        label = labels.get(start)
        if not label or label['identity'] != 'T1' or label['visibility'] not in ('CLEAR', 'PARTIAL'):
            raise ValueError('期待返回缺少可辨认T1原图')
    elif (start is not None or physical.get('original_target_removed') is not True
          or physical.get('original_target_reappears') is not False):
        raise ValueError('零返回机会不得产生返回帧/延迟')


def validate(protocol_path, output):
    empty_output(output)
    protocol = load_protocol(protocol_path)  # 同时实际核查正式冻结与共同规则。
    if protocol['stage'] != 'HOLDOUT':
        raise ValueError('本入口只核查HOLDOUT输入准备')
    freeze = read_json(checked_file(protocol['frozen_manifest']))
    registry = read_json(checked_file(protocol['confirmed_input_registry']))
    confirmation = read_json(registry['physical_identity_evidence'])
    preparation = read_json(checked_file(protocol['annotation_manifest_before_cache']))
    root = Path(protocol['annotation_manifest_before_cache']['path']).parent
    inputs = read_json(root / 'input_registry.json')
    if inputs['comparison_status'] != 'NOT_STARTED' or preparation['comparison_has_run']:
        raise ValueError('标注交付不能冒充三组对照结果')
    for case in preparation['cases']:
        for key in ('initialization', 'physical_identity_annotation', 'evaluation_labels',
                    'manual_event', 'visibility_intervals', 'coverage', 'timeline'):
            checked_file(case[key])
    registered = {c['case_id']: c for c in registry['cases']}
    confirmed = {c['case_id']: c for c in confirmation['cases']}
    locked = {c['case_id']: c for c in preparation['cases']}
    supplied = {c['case_id']: c for c in inputs['cases']}
    ids = [c['case_id'] for c in protocol['cases']]
    if len(ids) != 3 or set(ids) != set(registered) or set(ids) != set(locked):
        raise ValueError('三片登记不完整/重复')
    excluded = {s['sha256'] for s in freeze['excluded_development_sources']}
    if len(excluded) != 3 or len({c['source_sha256'] for c in protocol['cases']}) != 3:
        raise ValueError('三片开发排除或三份新来源不完整')
    results = []
    for case in protocol['cases']:
        cid = case['case_id']; registered_case = registered[cid]; supplied_case = supplied[cid]
        if (sha256(Path(registered_case['source_path'])) != registered_case['sha256']
                or sha256(Path(case['source'])) != registered_case['sha256']
                or case['source_sha256'] in excluded):
            raise ValueError('原件/副本不一致或使用开发来源')
        if (not confirmed[cid]['user_confirmed'] or confirmed[cid]['source_sha256'] != case['source_sha256']
                or confirmed[cid]['expected_original_target_return'] is not registered_case['expected_original_target_return']):
            raise ValueError('物理确认未绑定本片来源')
        if case['recording_protocol_deviations'] != registered_case['timing_observations']['deviations']:
            raise ValueError('原拍摄偏差被删除或改写')
        info, rows = load_case(case, protocol)
        if (not info['completed'] or info['runner_sha256'] != freeze['executed_code_sha256']['scripts/run_baseline.py']
                or len(rows) != registered_case['video_info']['frames_read']):
            raise ValueError('公共缓存来源/冻结脚本/帧数无效')
        for path, digest in supplied_case['cache_all_files_sha256'].items():
            if sha256(Path(path)) != digest:
                raise ValueError('新公共缓存改变')
        initialization = read_json(checked_file(locked[cid]['initialization']))
        if not initialization['locked_before_detection_cache'] or any(
                initialization[k] != case['initialization'][k] for k in ('frame_index', 'bbox_xyxy', 'match_iou_min')):
            raise ValueError('早期初始化在推理后重选')
        if case['initialization']['match_iou_min'] != protocol['match_iou_min']:
            raise ValueError('初始化IoU改变冻结规则')
        init = case['initialization']
        # 只检查唯一初始化映射，绝不调用 step 或运行任一组逐帧状态。
        choice = TargetState(rows[init['frame_index']], init['bbox_xyxy'],
                             protocol['missing_frames'], init['match_iou_min']).initialization
        if choice != supplied_case['initial_unique_detection_match']:
            raise ValueError('初始化映射证据不一致')
        physical, supplemental, labels, raw_checks = validate_labels(case, protocol)
        if case['evaluation_labels'] != locked[cid]['evaluation_labels']:
            raise ValueError('推理前标签包被替换')
        if 'annotation_adapter_basis' in physical:
            adapter = physical['annotation_adapter_basis']
            if (adapter['path'] != locked[cid]['physical_identity_annotation']['path']
                    or adapter['sha256'] != locked[cid]['physical_identity_annotation']['sha256']
                    or adapter['label_sha256'] != case['evaluation_labels']['sha256']):
                raise ValueError('负例区域适配缺少推理前真值依据')
            original_physical = read_json(checked_file(locked[cid]['physical_identity_annotation']))
            if any(physical[k] != v for k, v in original_physical.items()):
                raise ValueError('负例适配改变已固定物理事实')
            negative = physical['negative_interval']
            if labels[negative['start_frame']]['bbox_xyxy'] != negative['bbox_xyxy']:
                raise ValueError('负例区域不来自原图人工框')
        elif case['physical_identity_annotation'] != locked[cid]['physical_identity_annotation']:
            raise ValueError('推理前身份包被替换')
        coverage = validate_frame_labels(supplemental['frames'], init['frame_index'],
                                        case['end_frame_exclusive'], protocol['fixed_sample_stride'],
                                        info['width'], info['height'])
        spans = read_json(checked_file(case['annotation_provenance']['visibility_intervals']))['intervals']
        validate_visibility_intervals(spans, supplemental['frames'], init['frame_index'], case['end_frame_exclusive'])
        if len(case['events']) != 1 or case['events'][0] != read_json(checked_file(locked[cid]['manual_event'])):
            raise ValueError('人工事件数量/内容变化')
        validate_event(case['events'][0], physical, labels, registered_case['expected_original_target_return'])
        timeline = read_json(checked_file(locked[cid]['timeline']))
        cap = cv2.VideoCapture(case['source']); decoded = 0
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if decoded >= len(rows):
                    raise ValueError('原视频超出缓存范围')
                row = rows[decoded]; original_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
                if (frame.shape[:2] != (info['height'], info['width'])
                        or not math.isclose(row['source_pos_msec_seconds'], original_time, abs_tol=1e-9)
                        or timeline['frames'][decoded]['source_pos_msec_seconds'] != original_time):
                    raise ValueError('原视频/缓存/原帧时间轴不一致')
                if decoded in labels:
                    label = labels[decoded]
                    if (not math.isclose(label['timestamp_seconds'], row['timestamp_seconds'], abs_tol=1e-9)
                            or label['source_pos_msec_seconds'] != original_time):
                        raise ValueError('标签时间不是原帧时间')
                decoded += 1
        finally:
            cap.release()
        if decoded != len(rows) or len(timeline['frames']) != decoded:
            raise ValueError('原视频/公共缓存/标注时间轴帧数不一致')
        # 冻结核查器在临时只读链接上检查缓存，预览不用于标注或筛片。
        with tempfile.TemporaryDirectory(prefix='holdout_cache_check_') as temporary:
            temporary = Path(temporary)
            for entry in Path(case['baseline']['path']).iterdir():
                if entry.resolve().is_file():
                    (temporary / entry.name).symlink_to(entry.resolve())
            reviewed = review_baseline(temporary, [])
            baseline_checks = {k: reviewed[k] for k in ('record_checks_passed', 'records',
                                      'output_decoded_frames', 'source_time_monotonic')}
        results.append({'case_id': cid, 'source_sha256': case['source_sha256'],
            'all_three_development_sources_excluded': True, 'initialization': choice,
            'expected_return_opportunities': int(registered_case['expected_original_target_return']),
            'raw_labels': raw_checks, 'source_decoded_frames': decoded, 'baseline_checks': baseline_checks,
            'annotation_coverage': coverage, 'recording_protocol_deviations': case['recording_protocol_deviations'],
            'recognizable_reappearance_frame': physical['recognizable_reappearance_frame'],
            'first_other_recognizable_frame': physical.get('first_other_recognizable_frame'),
            'comparison_status': 'NOT_STARTED', 'effect_evaluation_status': 'NOT_STARTED'})
    before = read_json(root / 'old_artifacts_before.json')
    verify_snapshot(before)
    output.mkdir(parents=True)
    report = {'input_annotation_checks_passed': True, 'command': shlex.join(sys.orig_argv),
              'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'validator_sha256': sha256(Path(__file__)), 'protocol_sha256': sha256(protocol_path),
              'frozen_manifest_sha256': sha256(checked_file(protocol['frozen_manifest'])),
              'formal_freeze_check': 'PASS_FROZEN_UNCHANGED', 'shared_policy_unchanged': True,
              'old_files_preserved': len(before), 'independent_manual_events': len(results),
              'expected_return_opportunities': sum(r['expected_return_opportunities'] for r in results),
              'fixed_samples_planned': sum(r['annotation_coverage']['fixed_samples_planned'] for r in results),
              'fixed_samples_checked': sum(r['annotation_coverage']['fixed_samples_checked'] for r in results),
              'raw_annotation_images_verified': sum(r['raw_labels']['raw_annotation_images_verified'] for r in results),
              'public_cache_inference_runs_per_clip': 1, 'comparison_status': 'NOT_STARTED',
              'effect_evaluation_status': 'NOT_STARTED', 'speed_status': 'UNVERIFIED', 'cases': results,
              'note': 'PASS只表示输入/标注/公共缓存核查；不代表三组效果验收。完整框缺口与无逐帧精确框保留。'}
    write_json(output / 'annotation_checks.json', report)
    write_json(output / 'preservation_after.json', {p: sha256(Path(p)) for p in before})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate(args.protocol, args.output)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'HOLDOUT输入/标注核查失败: {exc}\n')
    print(json.dumps({k: result[k] for k in ('input_annotation_checks_passed', 'fixed_samples_checked',
                          'raw_annotation_images_verified', 'old_files_preserved', 'comparison_status')}, ensure_ascii=False))
