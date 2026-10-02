"""核对本次固定诊断窗、旧/新规则评价、默认/关闭回归与证据保全。"""

import argparse
from collections import Counter
import json
from pathlib import Path
import shlex
import sys

import cv2

from appearance_recovery import RecoveryState, compare_feature, extract_feature
from evaluation_sources import read_json, read_rows, verify_code, verify_snapshot
from run_target_state import box_iou, sha256, write_json
from validate_recovery_fixture import restore_bank


def require(condition, message):
    if not condition:
        raise ValueError(message)


def review(root, report_path=None, evaluation_legacy=None, evaluation_aligned=None):
    report_path = report_path or root / 'comparison.json'
    if report_path.exists():
        raise ValueError('比较报告已存在，请保留并换新根目录')
    manifest = read_json(root / 'run_manifest.json')
    annotation = read_json(root / 'diagnosis/visibility_annotations.json')
    verify_snapshot(read_json(root / 'old_artifacts_before.json'))
    require(sha256(annotation['source']) == annotation['source_sha256'], '诊断原视频变化')
    for label in annotation['frames']:
        require(sha256(label['raw_image']) == label['raw_image_sha256'], '诊断原图变化')
    runs = {name: read_rows(Path(item['path']) / 'frames.jsonl') for name, item in manifest['runs'].items()}
    infos = {name: read_json(Path(item['path']) / 'run_info.json') for name, item in manifest['runs'].items()}
    for name, item in manifest['runs'].items():
        require(sha256(Path(item['path']) / 'run_info.json') == item['run_info_sha256'], '运行清单变化')
        verify_code(infos[name], manifest['candidate_revision'])
    original = {
        'legacy_positive': 'outputs/tabletop_02_m2_step2_v3',
        'legacy_negative': 'outputs/tabletop_wrong_bottle_01_m2_step2',
        'aligned_disabled_positive': 'outputs/tabletop_02_m2_step2_disabled_v2',
        'aligned_disabled_negative': 'outputs/tabletop_wrong_bottle_01_m2_disabled_v2',
    }
    equivalence = {}
    for name, old in original.items():
        for filename in ('frames.jsonl', 'events.jsonl'):
            require(read_rows(root/name/filename) == read_rows(Path(old)/filename), f'{name}旧字段/事件未完全复现')
        equivalence[name] = {'frames': len(runs[name]), 'all_fields_and_events_identical': True,
                             'video_sha256_identical': sha256(root/name/'status.mp4') == sha256(Path(old)/'status.mp4')}
    base_config = read_json('configs/recovery.json')
    new_config = infos['aligned_negative']['appearance_config']
    require({k: new_config[k] for k in base_config} == base_config, '原参数/门槛发生变化')
    for case in ('positive', 'negative'):
        require(infos[f'legacy_{case}']['reference_bank'] == infos[f'aligned_{case}']['reference_bank'], '冻结参考改变')
        require(infos[f'legacy_{case}']['references_json_sha256'] == infos[f'aligned_{case}']['references_json_sha256'], '参考采样/像素改变')
    mode_rows = {mode: {r['frame_index']: r for r in runs[f'{mode}_negative']} for mode in ('legacy', 'aligned')}
    diagnostics, counts, improved = [], {mode: Counter() for mode in mode_rows}, []
    for label in annotation['frames']:
        index, visibility = label['frame_index'], label['visibility']
        item = {'frame_index': index, 'visibility': visibility, 'expected_current_position': label['expected_current_position']}
        for mode, rows in mode_rows.items():
            row = rows[index]
            known = row['position_known']
            counts[mode][visibility + '_FRAMES'] += 1
            counts[mode][visibility + ('_KNOWN' if known else '_UNKNOWN')] += 1
            if visibility in ('PARTIAL_UNRELIABLE', 'FULLY_OCCLUDED'):
                require(not known and row['current_target_bbox_xyxy'] is None, f'{mode}在不可靠/遮挡帧给出位置f{index}')
            if mode == 'aligned' and visibility == 'CLEAR_VISIBLE':
                require(known and row['target_observed_this_frame'], f'新规则可见帧仍UNKNOWN f{index}')
                require(box_iou(label['bbox_xyxy'], row['current_target_bbox_xyxy']) >= .5, f'新当前框不匹配人工T1 f{index}')
                evidence = row['active_track_evidence']
                require(evidence['quality']['valid'] and evidence['best_reference']['appearance_passed'], '改善无合格外观证据')
                matches = [d for d in row['detections'] if d['bbox_xyxy'] == row['current_target_bbox_xyxy']]
                require(len(matches) == 1, '当前位置并非来自当前检测')
            item[mode] = {'state': row['state'], 'position_known': known,
                          'current_bbox_xyxy': row['current_target_bbox_xyxy'],
                          'missing': row['consecutive_missing_frames'], 'active_track_evidence': row['active_track_evidence']}
        if visibility == 'CLEAR_VISIBLE' and not item['legacy']['position_known'] and item['aligned']['position_known']:
            improved.append(index)
        diagnostics.append(item)
    require(improved == [180], '诊断改善范围与要求不一致，需核对失败案例')
    focus = mode_rows['aligned'][180]
    partial_first = next(l['frame_index'] for l in annotation['frames'] if l['visibility'] == 'PARTIAL_UNRELIABLE')
    first = mode_rows['aligned'][partial_first]
    require(not first['active_track_evidence']['quality']['valid'] and
            'CAP_INSUFFICIENT_COLOR' in first['active_track_evidence']['quality']['reasons'], 'f181质量被绕过')
    threshold = infos['aligned_negative']['config']['missing_frames']
    for index in range(partial_first, annotation['diagnostic_interval']['end_frame_exclusive']):
        row = mode_rows['aligned'][index]
        require(row['first_missing_frame'] == partial_first and row['consecutive_missing_frames'] == index-partial_first+1,
                '新缺失计数不一致')
        require((row['confirmed_lost_frame'] is not None) == (index-partial_first+1 >= threshold), '新丢失确认未遵守阈值')
    # 从原视频的诊断帧独立于输出重新取特征，逐参考对齐分量必须完全相同。
    info = infos['aligned_negative']
    baseline = read_rows(Path(info['baseline'])/'frames.jsonl')
    c = info['config']
    machine = RecoveryState(baseline[c['init_frame']], c['init_box'], c['missing_frames'], new_config, c['init_iou'])
    restore_bank(machine, root/'aligned_negative', new_config)
    raw = cv2.imread(str(root/'diagnosis/raw_000180.png'))
    detection = next(d for d in baseline[180]['detections'] if d['bbox_xyxy'] == focus['current_target_bbox_xyxy'])
    feature = extract_feature(raw, detection, new_config)
    best, comparisons = compare_feature(feature, machine.bank.samples, new_config)
    require(best == focus['active_track_evidence']['best_reference'] and
            comparisons == focus['active_track_evidence']['reference_comparisons'], '原图对齐分量重算不一致')
    summary_dirs = {'legacy': evaluation_legacy or root/'evaluation_legacy',
                    'aligned': evaluation_aligned or root/'evaluation_aligned'}
    summaries = {mode: read_json(directory/'summary.json') for mode, directory in summary_dirs.items()}
    metrics = {}
    for mode, summary in summaries.items():
        groups = {g['run_id']: g for g in summary['groups']}
        pos, neg = groups['positive_enabled'], groups['negative_enabled']
        require(pos['return_evaluation']['expected_return_opportunities'] == 1 and pos['acceptance_evaluation']['correct_accepts'] == 1 and
                pos['acceptance_evaluation']['incorrect_accepts'] == pos['acceptance_evaluation']['unevaluated_accepts'] == 0, '正例身份恢复回归未通过')
        require(neg['return_evaluation']['expected_return_opportunities'] == 0 and neg['return_evaluation']['unrecovered_events'] == 0,
                '负例返回机会口径改变')
        require(neg['acceptance_evaluation']['program_accepts'] == 0 and neg['whole_run_candidate_observations'] == 149, '负例误接受/候选覆盖改变')
        coverage = neg['annotated_negative_coverage']
        require(coverage['qualified_candidate_observations'] == coverage['appearance_rejected_observations'] == 148, '148帧合格拒绝未保住')
        require(neg['incorrect_current_position']['incorrect_frames'] == [], '负例错误当前位置')
        require(groups['negative_disabled']['appearance_rejection_status'] == 'NOT_APPLICABLE', '关闭核验口径改变')
        metrics[mode] = {'positive_return': pos['return_evaluation'], 'negative_return': neg['return_evaluation'],
                         'negative_rejection': coverage, 'visibility_control': neg['visible_target_unknown']}
    fixture = read_json(root/'module_fixture/module_validation.json')
    require(fixture['bag_decision_counts'] == {'DEFERRED_QUALITY': 5, 'REJECTED_APPEARANCE': 2} and
            fixture['bag_program_accepts'] == fixture['equal_score_fixture_accepted'] == 0 and fixture['reference_unchanged'], '挂包/歧义夹具回归失败')
    with (root/'diagnostic_by_frame.jsonl').open('w', encoding='utf-8') as stream:
        for row in diagnostics:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False)+'\n')
    with (root/'alignment_components.jsonl').open('w', encoding='utf-8') as stream:
        for name in ('legacy_positive', 'legacy_negative', 'aligned_positive', 'aligned_negative'):
            for row in runs[name]:
                evidence = [('active', row.get('active_track_evidence'))] + [('candidate', c) for c in row['recovery_candidates']]
                for kind, item in evidence:
                    if item and item.get('best_reference'):
                        for comparison in item['reference_comparisons']:
                            stream.write(json.dumps({'run': name, 'frame_index': row['frame_index'], 'evidence_kind': kind,
                                'selected_reference': comparison['reference_frame_index']==item['best_reference']['reference_frame_index'],
                                **comparison}, ensure_ascii=False, allow_nan=False)+'\n')
    old = read_json(root/'old_artifacts_before.json')
    verify_snapshot(old)
    write_json(root/'old_artifacts_after.json', {p: sha256(p) for p in old})
    report = {'verdict': 'PASS', 'scope': 'two viewed development videos; not holdout/freeze/general identity accuracy',
              'command': shlex.join(sys.orig_argv), 'checker_sha256': sha256(Path(__file__)),
              'candidate_revision': manifest['candidate_revision'], 'configuration_sha256': sha256('configs/recovery_f180_dev.json'),
              'evaluation_sources': {mode: {'path': str(directory), 'summary_sha256': sha256(directory/'summary.json'),
                                           'run_info_sha256': sha256(directory/'run_info.json')}
                                     for mode, directory in summary_dirs.items()},
              'original_configuration_unchanged': True, 'original_parameters_and_thresholds_unchanged': True,
              'default_and_disabled_equivalence': equivalence, 'reference_sampling_unchanged': True,
              'diagnostic_annotation_sha256': sha256(root/'diagnosis/visibility_annotations.json'),
              'diagnostic_counts': {mode: dict(c) for mode, c in counts.items()}, 'improved_visible_frames': improved,
              'uncertain_frames': [l['frame_index'] for l in annotation['frames'] if l['visibility']=='UNCERTAIN_BOUNDARY'],
              'focus_old_best': mode_rows['legacy'][180]['active_track_evidence']['best_reference'], 'focus_new_best': best,
              'focus_current_bbox_manual_iou': box_iou(next(l for l in annotation['frames'] if l['frame_index']==180)['bbox_xyxy'], focus['current_target_bbox_xyxy']),
              'new_first_missing_frame': partial_first, 'new_confirmed_lost_frame': partial_first+threshold-1,
              'old_confirmed_lost_frame': mode_rows['legacy'][195]['confirmed_lost_frame'],
              'metrics': metrics, 'module_fixture': {k:fixture[k] for k in ('bag_decision_counts','bag_program_accepts','equal_score_fixture_frames','equal_score_fixture_accepted','reference_unchanged')},
              'old_artifact_files_preserved': len(old), 'whole_video_false_alarm_rate': None,
              'whole_video_false_alarm_status': 'UNEVALUATED',
              'unverified': ['background-visible replacement','real double-bottle ambiguity','same-packaging substitution','independent holdout','strict speed comparison'],
              'note': '新搜索会改变分数分布；当前颜色也拒绝替代瓶子，未证明纹理独立身份能力。'}
    write_json(report_path, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--evaluation-legacy', type=Path)
    parser.add_argument('--evaluation-aligned', type=Path)
    args = parser.parse_args()
    try:
        result = review(args.root, args.report, args.evaluation_legacy, args.evaluation_aligned)
    except (ValueError, OSError, KeyError, IndexError) as exc:
        parser.exit(1, f'开发回归核查失败: {exc}\n')
    print(json.dumps({k: result[k] for k in ('verdict','diagnostic_counts','improved_visible_frames','new_first_missing_frame','new_confirmed_lost_frame','old_artifact_files_preserved')}, ensure_ascii=False, indent=2))
