"""核查真实替代瓶子的拒绝；人工身份区间独立于算法分数。"""

import argparse
from collections import Counter
import json
from pathlib import Path
import shlex
import sys
import tempfile
from types import SimpleNamespace

import cv2

try:
    from .run_target_state import box_iou, sha256, write_json
except ImportError:
    from run_target_state import box_iou, sha256, write_json


def summarize_negative(rows, events, annotation):
    interval = annotation['negative_interval']
    start, end = interval['start_frame'], interval['end_frame_exclusive']
    if not 0 <= start < end or interval['identity'] in ('UNCERTAIN', annotation['target_uid']):
        raise ValueError('负例区间/身份无效')
    if annotation['original_target_removed'] is not True or annotation['original_target_reappears'] is not False:
        raise ValueError('需要拍摄者确认原目标已移除且没有重现')
    if not annotation['operator_confirmation'] or not annotation['confirmation_basis']:
        raise ValueError('缺少独立身份依据')
    selected = [row for row in rows if start <= row['frame_index'] < end]
    if [r['frame_index'] for r in selected] != list(range(start, end)):
        raise ValueError('记录未覆盖完整人工可见区间')
    counts, failures = Counter(), Counter()
    evidence, wrong_positions, frames_without_detection, qualified = [], [], [], 0
    for row in selected:
        index = row['frame_index']
        if row['position_known'] or row['current_target_bbox_xyxy'] is not None or row['target_observed_this_frame']:
            wrong_positions.append(index)
        matches = [d for d in row['detections'] if box_iou(d['bbox_xyxy'], interval['bbox_xyxy']) >= interval['match_iou_min']]
        if len(matches) > 1:
            raise ValueError(f'人工区域匹配不唯一: f{index}')
        if not matches:
            frames_without_detection.append(index)
            continue
        detection = matches[0]
        candidates = [c for c in row['recovery_candidates'] if c['detection_index'] == detection['detection_index']]
        if len(candidates) != 1:
            counts['NOT_A_RECOVERY_CANDIDATE'] += 1
            continue
        candidate = candidates[0]
        best = candidate['best_reference']
        quality_ok = candidate['quality']['valid'] and best is not None
        if candidate['decision'] == 'REJECTED_APPEARANCE' and (
                not quality_ok or best['appearance_passed'] or all(best['gates'].values())):
            raise ValueError(f'外观拒绝字符串与实际质量/门槛矛盾: f{index}')
        qualified += int(quality_ok)
        counts[candidate['decision']] += 1
        if best:
            failures.update(k for k, passed in best['gates'].items() if not passed)
        evidence.append({'frame_index': index, 'timestamp_seconds': row['timestamp_seconds'],
                         'source_pos_msec_seconds': row['source_pos_msec_seconds'],
                         'detection': detection, 'quality': candidate['quality'],
                         'decision': candidate['decision'], 'best_reference': best,
                         'confirmation_count': candidate['confirmation_count'],
                         'bound_to_target': candidate['bound_to_target']})
    accepts = [e['frame_index'] for e in events if e['event_type'] == 'RECOVERY_ACCEPTED']
    bound_frames = [e['frame_index'] for e in evidence if e['bound_to_target'] or e['confirmation_count']]
    if wrong_positions or accepts or bound_frames:
        verdict = 'FAIL'
    elif qualified and counts['REJECTED_APPEARANCE'] == qualified:
        verdict = 'PASS'
    else:
        verdict = 'UNVERIFIED'
    return {'verdict': verdict, 'visible_frames': len(selected), 'qualified_candidate_frames': qualified,
            'candidate_decisions': dict(counts), 'frames_without_matched_detection': frames_without_detection,
            'failed_gate_frame_counts': dict(failures), 'incorrect_current_position_frames': wrong_positions,
            'program_accept_frames_entire_run': accepts, 'binding_or_confirmation_frames': bound_frames,
            'evidence': evidence,
            'notes': ['原目标被取走，本负例预期不恢复；通用 unrecovered_events 不计为恢复失败。',
                      '只将质量合格且有外观证据的候选计入真实拒绝；无检测和质量暂缓不算拒绝。',
                      '人工区域用于评价匹配，未传入候选选择或外观门控。']}


def validate(args):
    from appearance_recovery import ReferenceBank, compare_feature, extract_feature, public_feature
    from review_recovery import read_rows, review
    from validate_recovery_fixture import restore_bank

    if args.report.exists():
        raise ValueError('报告已存在，请换路径，保留原结果')
    info = json.loads((args.output / 'run_info.json').read_text(encoding='utf-8'))
    annotation = json.loads(args.annotations.read_text(encoding='utf-8'))
    if annotation['source_sha256'] != info['source_sha256'] or annotation['target_uid'] != info['config']['target_uid']:
        raise ValueError('身份记录与运行视频/目标不一致')
    if not info['recovery_enabled']:
        raise ValueError('真实拒绝验证需要开启外观模块')
    # 每次对当前输入重做原核查，结果写入临时目录，保留已有报告。
    # 不把可能已过期的 review.json 布尔值当作当前证据。
    with tempfile.TemporaryDirectory(prefix='wrong_bottle_review_') as directory:
        review_output = Path(directory)
        for entry in args.output.iterdir():
            if entry.name not in ('review.json', 'evaluation.json'):
                (review_output / entry.name).symlink_to(entry.resolve(), target_is_directory=entry.is_dir())
        result = review(review_output, [])
    if not result['record_checks_passed'] or sha256(Path(info['source'])) != annotation['source_sha256']:
        raise ValueError('基础核查/原视频校验失败')
    for name, digest in info['code_sha256'].items():
        if sha256(Path(__file__).with_name(name)) != digest:
            raise ValueError('运行核心代码已变化')
    rows, events = read_rows(args.output / 'frames.jsonl'), read_rows(args.output / 'events.jsonl')
    summary = summarize_negative(rows, events, annotation)
    config = info['appearance_config']
    holder = SimpleNamespace(bank=ReferenceBank(info['config']['init_frame'], config))
    digest = restore_bank(holder, args.output, config)
    refs = json.loads((args.output / 'references.json').read_text(encoding='utf-8'))
    if sha256(args.output / 'references.json') != info['references_json_sha256']:
        raise ValueError('参考记录已变化')
    for entry in refs['references']:
        if sha256(args.output / entry['crop']) != entry['crop_sha256']:
            raise ValueError('参考裁剪已变化')
    by_index = {entry['frame_index']: entry for entry in summary['evidence']}
    cap, index, checked = cv2.VideoCapture(info['source']), 0, 0
    try:
        if not cap.isOpened():
            raise ValueError('原视频打不开')
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if index in by_index:
                entry = by_index[index]
                feature = extract_feature(frame, entry['detection'], config)
                best, _ = compare_feature(feature, holder.bank.samples, config)
                if public_feature(feature) != entry['quality'] or best != entry['best_reference']:
                    raise ValueError(f'原像素重算与运行证据不一致: f{index}')
                checked += 1
            index += 1
    finally:
        cap.release()
    if index != info['source_decoded_frames'] or checked != len(by_index) or digest != holder.bank.digest():
        raise ValueError('重解码/证据覆盖/参考冻结不一致')
    report = {'command': shlex.join(sys.orig_argv), 'output': str(args.output),
              'source_sha256': info['source_sha256'], 'annotations': str(args.annotations),
              'annotations_sha256': sha256(args.annotations), 'run_info_sha256': sha256(args.output / 'run_info.json'),
              'frames_sha256': sha256(args.output / 'frames.jsonl'), 'events_sha256': sha256(args.output / 'events.jsonl'),
              'validator_sha256': sha256(Path(__file__)), 'reference_sha256': digest,
              'negative_interval': annotation['negative_interval'],
              'identity_basis': annotation['confirmation_basis'], 'operator_confirmation': annotation['operator_confirmation'],
              'raw_pixel_evidence_recomputed_frames': checked, 'source_redecoded_frames': index,
              'current_record_review': result,
              **summary, 'scope': '单段已查看的开发负例；不是保留测试或普遍拒绝能力。',
              'input_limitations': annotation.get('limitations', [])}
    write_json(args.report, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--annotations', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate(args)
    except (ValueError, OSError, KeyError, IndexError, cv2.error) as exc:
        parser.exit(1, f'真实错误瓶子核查失败: {exc}\n')
    print(json.dumps({key: result[key] for key in ('verdict', 'visible_frames', 'qualified_candidate_frames',
                                                  'candidate_decisions', 'program_accept_frames_entire_run')}, ensure_ascii=False, indent=2))
    if result['verdict'] != 'PASS':
        parser.exit(1, '本段尚未通过真实错误瓶子的拒绝验证，保留报告。\n')
