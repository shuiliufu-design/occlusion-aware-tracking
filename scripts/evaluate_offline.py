"""用独立人工事件统一评价现有 M2 开启/关闭开发结果；只读旧结果。"""

import argparse
from collections import Counter
import json
from pathlib import Path
import shlex
import subprocess
import sys

try:
    from .evaluation_sources import (check_counts, read_json, read_rows, run_historical_checks,
                                     snapshot, verify_snapshot)
    from .run_target_state import box_iou, sha256, write_json
except ImportError:
    from evaluation_sources import (check_counts, read_json, read_rows, run_historical_checks,
                                    snapshot, verify_snapshot)
    from run_target_state import box_iou, sha256, write_json


STATUS_MEANINGS = {
    'PASS': '在明确标注/核查的范围内满足该项要求',
    'FAIL': '在明确标注范围发现失败；并非工具运行失败',
    'UNVERIFIED': '尚未取得所需真实输入或独立依据',
    'NOT_APPLICABLE': '本事件没有机会，或该组没有执行此项机制',
    'UNEVALUATED': '当前记录/标注覆盖不足，尚不能给出此项判断',
}


def interval_indices(interval):
    start, end = interval['start_frame'], interval['end_frame_exclusive']
    if type(start) is not int or type(end) is not int or not 0 <= start < end:
        raise ValueError('人工区间必须为非空整数 [start_frame,end_frame_exclusive)')
    return range(start, end)


def validate_annotation(case, annotation, info):
    if case['annotations_sha256'] != sha256(Path(case['annotations'])):
        raise ValueError('原人工记录 SHA 不匹配')
    if annotation['source_sha256'] != info['source_sha256'] or annotation['target_uid'] != info['config']['target_uid']:
        raise ValueError('人工记录视频/物理目标不匹配')
    if not case['episode_id'] or not case['physical_identity'] or not case['interval_basis']:
        raise ValueError('缺少独立事件/身份/边界依据')
    if case['expected_return'] is not None and type(case['expected_return']) is not bool:
        raise ValueError('expected_return 只能是 true/false/null')
    if not annotation.get('operator_confirmation') or not annotation.get('confirmation_basis'):
        raise ValueError('缺少拍摄者物理身份依据')
    indices = interval_indices(case['evaluation_interval'])
    if indices.start < info['config']['init_frame'] or indices.stop > info['config']['end_frame_exclusive']:
        raise ValueError('人工事件超出共同运行区间')
    if case['expected_return'] is True:
        frame = case['recognizable_reappearance_frame']
        if frame != annotation.get('recognizable_reappearance_frame') or frame not in indices:
            raise ValueError('不能改变旧人工可辨认重现帧或使用区间外帧')
    elif case['expected_return'] is False:
        if not annotation.get('original_target_removed') or annotation.get('original_target_reappears') is not False:
            raise ValueError('无返回机会需要拍摄者确认取走且未再入镜')
        if case['recognizable_reappearance_frame'] is not None:
            raise ValueError('无返回机会不能填写重现帧')
    for interval in [*case['target_absent_intervals'], *case['visible_controls']]:
        sub = interval_indices(interval)
        if sub.start < indices.start or sub.stop > indices.stop:
            raise ValueError('人工子区间超出评价窗')
    for control in case['visible_controls']:
        if control['identity'] != annotation['target_uid'] or not control['annotator'] or not control['basis']:
            raise ValueError('可见控制点缺少独立身份证据')
        if sha256(Path(control['evidence'])) != control['evidence_sha256']:
            raise ValueError('可见控制原图变化')
    if 'negative_interval' in annotation:
        # 直接沿用旧半开区间，不能把632误当排除端点。
        sub = interval_indices(annotation['negative_interval'])
        if sub.start < indices.start or sub.stop > indices.stop:
            raise ValueError('旧替代瓶子区间超出评价窗')


def candidate_category(candidate, enabled):
    if not enabled:
        return 'IDENTITY_CHECK_NOT_APPLICABLE'
    decision = candidate['decision']
    quality = candidate.get('quality', {}).get('valid') is True
    best = candidate.get('best_reference')
    if decision == 'REJECTED_APPEARANCE':
        if not quality or best is None or best['appearance_passed'] or all(best['gates'].values()):
            raise ValueError('拒绝字符串与质量/外观证据矛盾')
    if decision == 'DEFERRED_QUALITY':
        if quality:
            raise ValueError('质量暂缓却质量合格')
        return 'QUALITY_DEFERRED'
    if not quality or best is None:
        return 'INSUFFICIENT_EVIDENCE'
    return {'REJECTED_APPEARANCE': 'QUALIFIED_APPEARANCE_REJECTED',
            'ACCEPTABLE': 'QUALIFIED_ACCEPTABLE', 'AMBIGUOUS': 'QUALIFIED_AMBIGUOUS'}.get(decision, 'QUALIFIED_OTHER')


def coverage(rows, enabled, interval=None):
    """每帧输出覆盖分类；人工 ROI 只用于评价匹配，绝不送回算法。"""
    selected = rows
    if interval is not None:
        indices = interval_indices(interval)
        selected = [r for r in rows if r['frame_index'] in indices]
        if [r['frame_index'] for r in selected] != list(indices):
            raise ValueError('记录缺少人工区间帧')
    frame_counts, candidate_counts, decisions, gate_failures = Counter(), Counter(), Counter(), Counter()
    records = []
    for row in selected:
        detections = [d for d in row['detections'] if d['class_name'] == 'bottle']
        if interval is not None:
            detections = [d for d in detections if box_iou(d['bbox_xyxy'], interval['bbox_xyxy']) >= interval['match_iou_min']]
            if len(detections) > 1:
                raise ValueError(f"人工区域检测匹配不唯一: f{row['frame_index']}")
        matched = {d['detection_index'] for d in detections}
        candidates = [c for c in row['recovery_candidates'] if c['detection_index'] in matched]
        if not detections:
            frame_counts['NO_MATCHED_DETECTION'] += 1
        elif not candidates:
            frame_counts['DETECTED_NOT_RECOVERY_CANDIDATE'] += 1
        else:
            frame_counts['WITH_CANDIDATE'] += 1
        categories = []
        for candidate in candidates:
            category = candidate_category(candidate, enabled)
            categories.append(category)
            candidate_counts[category] += 1
            decisions[candidate.get('decision', 'UNVERIFIED')] += 1
            best = candidate.get('best_reference')
            if best is not None:
                gate_failures.update(k for k, passed in best['gates'].items() if not passed)
        for category in set(categories):
            frame_counts[category] += 1
        records.append({'frame_index': row['frame_index'], 'matched_detections': len(detections),
                        'candidate_count': len(candidates), 'categories': categories,
                        'position_known': row['position_known']})
    qualified = sum(count for key, count in candidate_counts.items() if key.startswith('QUALIFIED_')) if enabled else None
    return {'evaluation_frames': len(selected), 'frame_counts': dict(frame_counts),
            'candidate_observations': sum(candidate_counts.values()), 'candidate_counts': dict(candidate_counts),
            'qualified_candidate_observations': qualified,
            'appearance_rejected_observations': candidate_counts['QUALIFIED_APPEARANCE_REJECTED'] if enabled else None,
            'candidate_decisions': dict(decisions), 'failed_gate_observation_counts': dict(gate_failures),
            'quality_and_appearance_applicable': enabled, 'frames': records}


def evaluate_episode(info, rows, events, case, annotation, match_iou_min=0.5):
    indices = interval_indices(case['evaluation_interval'])
    by_frame = {r['frame_index']: r for r in rows}
    if any(i not in by_frame for i in indices):
        raise ValueError('事件评价窗记录不完整')
    accepts = [e for e in events if e['event_type'] == 'RECOVERY_ACCEPTED' and e['frame_index'] in indices]
    labels = {k['frame_index']: k for k in annotation.get('keyframes', [])}
    absent = {i for interval in case['target_absent_intervals'] for i in interval_indices(interval)}
    verdicts, delays = [], []
    for accept in accepts:
        frame = accept['frame_index']
        label = labels.get(frame)
        verdict, reason, iou = 'UNEVALUATED', '缺少该接受帧的独立身份/框依据', None
        if frame in absent:
            verdict, reason = 'INCORRECT', '人工确认原目标已取走，不能输出原目标位置'
        elif label and label['identity'] not in ('UNCERTAIN', 'UNKNOWN'):
            iou = box_iou(label['bbox_xyxy'], accept['candidate']['bbox_xyxy'])
            if label['identity'] != annotation['target_uid']:
                verdict, reason = 'INCORRECT', '人工标签为其他实体'
            elif iou < match_iou_min:
                verdict, reason = 'INCORRECT', '身份有依据，但恢复框未达到评价IoU'
            elif case['expected_return'] is True and frame >= case['recognizable_reappearance_frame']:
                verdict, reason = 'CORRECT', '独立同一物理身份、接受帧人工框与返回事件一致'
        verdicts.append({'accept_frame': frame, 'verdict': verdict, 'reason': reason, 'annotation_iou': iou,
                         'active_native_track_id': accept['active_native_track_id'],
                         'physical_identity_basis': annotation['confirmation_basis']})
        if verdict == 'CORRECT':
            start = case['recognizable_reappearance_frame']
            delays.append({'accept_frame': frame, 'recognizable_reappearance_frame': start,
                           'latency_frames': frame - start,
                           'latency_seconds_frame_fps': (frame - start) / info['nominal_fps'],
                           'latency_seconds_source_time': by_frame[frame]['source_pos_msec_seconds'] - by_frame[start]['source_pos_msec_seconds'],
                           'timing_basis': annotation['reappearance_criterion'], 'annotator': annotation['timing_annotator']})
    counts = Counter(item['verdict'] for item in verdicts)
    expected = case['expected_return']
    opportunity = int(expected is True)
    correct_event = int(opportunity and counts['CORRECT'] > 0)
    unknown_event = int(opportunity and not correct_event and counts['UNEVALUATED'] > 0)
    missed = int(opportunity and not correct_event and not unknown_event)
    status = ('PASS' if correct_event else 'UNEVALUATED' if unknown_event else 'FAIL') if expected is True else (
        'NOT_APPLICABLE' if expected is False else 'UNVERIFIED')
    wrong_positions = sorted(i for i in absent if by_frame[i]['position_known'] or by_frame[i]['current_target_bbox_xyxy'] is not None)
    controls = {i for control in case['visible_controls'] for i in interval_indices(control)}
    unknown_visible = sorted(i for i in controls if not by_frame[i]['position_known'])
    visible = {'status': ('FAIL' if unknown_visible else 'PASS') if controls else 'UNEVALUATED',
               'annotated_frames': len(controls), 'unknown_frames': unknown_visible,
               'unknown_count': len(unknown_visible) if controls else None,
               'incorrect_lost_frames': sorted(i for i in controls if by_frame[i]['state'] == 'LOST'),
               'evidence': [{'frame_index': i, 'state': by_frame[i]['state'], 'position_known': by_frame[i]['position_known'],
                             'active_track_evidence': by_frame[i].get('active_track_evidence'),
                             'detections': by_frame[i]['detections']} for i in sorted(controls)],
               'whole_video_false_alarm_rate': None, 'whole_video_status': 'UNEVALUATED',
               'note': '仅独立诊断控制点；TRACKING状态也可能UNKNOWN。未标注帧不当作正确或零误报。'}
    negative_coverage = coverage(rows, info['recovery_enabled'], annotation['negative_interval']) if 'negative_interval' in annotation else None
    if negative_coverage is None or not info['recovery_enabled']:
        appearance_status = 'NOT_APPLICABLE'
    elif counts['INCORRECT'] or wrong_positions:
        appearance_status = 'FAIL'
    elif negative_coverage['qualified_candidate_observations'] == 0:
        appearance_status = 'UNVERIFIED'
    elif counts['UNEVALUATED']:
        appearance_status = 'UNEVALUATED'
    elif negative_coverage['qualified_candidate_observations'] == negative_coverage['appearance_rejected_observations']:
        appearance_status = 'PASS'
    else:
        appearance_status = 'FAIL'
    return {'episode_id': case['episode_id'], 'event_type': case['event_type'],
            'expected_return': expected, 'physical_identity': case['physical_identity'],
            'evaluation_interval': case['evaluation_interval'], 'interval_basis': case['interval_basis'],
            'annotators': {key: annotation.get(key) for key in ('physical_identity_annotator', 'visual_annotator', 'timing_annotator')},
            'operator_confirmation': annotation['operator_confirmation'],
            'return_evaluation': {'status': status, 'expected_return_opportunities': opportunity,
                                  'correctly_recovered_events': correct_event, 'unrecovered_events': missed,
                                  'unevaluated_return_events': unknown_event,
                                  'success_rate': correct_event / opportunity if opportunity and not unknown_event else None,
                                  'latency_status': 'PASS' if delays else 'NOT_APPLICABLE', 'latencies': delays or None},
            'acceptance_evaluation': {'program_accepts': len(accepts), 'correct_accepts': counts['CORRECT'],
                                      'incorrect_accepts': counts['INCORRECT'], 'unevaluated_accepts': counts['UNEVALUATED'],
                                      'results': verdicts},
            'no_wrong_binding': {'status': 'FAIL' if counts['INCORRECT'] else 'UNEVALUATED' if counts['UNEVALUATED'] else 'PASS',
                                 'note': '程序接受逐项核查；没有接受不证明外观核验能力。'},
            'incorrect_current_position': {'status': ('FAIL' if wrong_positions else 'PASS') if absent else 'UNEVALUATED',
                                           'annotated_absent_frames': len(absent), 'incorrect_frames': wrong_positions,
                                           'whole_video_status': 'UNEVALUATED'},
            'visible_target_unknown': visible,
            'wrong_candidate_appearance_rejection': {'status': appearance_status,
                                                    'replacement_events': int(case['event_type'] == 'DIFFERENT_BOTTLE_REPLACEMENT'),
                                                    'coverage': negative_coverage,
                                                    'note': '关闭组外观质量/拒绝指标不适用；候选帧数不是独立事件数。'}}


def evaluate(protocol_path, output):
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('输出目录须为空；保留旧结果，请使用新路径')
    protocol = read_json(protocol_path)
    if protocol['schema_version'] != 1 or not 0 < protocol['match_iou_min'] <= 1:
        raise ValueError('评价格式版本或IoU无效')
    # 输出创建前固定所有旧输出及核心文件；此后任何变化都使运行失败。
    protected = snapshot([Path('outputs'), Path('configs/recovery.json'), Path('scripts'),
                          *[Path(read_json(Path(r['output']) / 'run_info.json')['source'])
                            for c in protocol['cases'] for r in c['runs']]])
    for evidence in protocol['evidence']:
        if sha256(Path(evidence['path'])) != evidence['sha256']:
            raise ValueError(f"独立证据 SHA 不匹配: {evidence['path']}")
    fix_path = Path('outputs/m2_disabled_stats_fix/fix_report.json')
    fix = read_json(fix_path)
    if sha256(Path(fix['audit_evidence'])) != fix['audit_sha256']:
        raise ValueError('统计修复引用的04证据不一致')
    # 核对04清单内旧输出（代码改动已由历史Git快照处理）。
    historical = read_json('outputs/m2_step2_04_review/preservation_before.json')
    verify_snapshot({p: digest for p, digest in historical.items() if Path(p).parts[0] == 'outputs'})
    for item in fix['cases']:
        for name, key in [('run_info.json', 'run_info_sha256'), ('review.json', 'review_sha256')]:
            if sha256(Path(item['new_output']) / name) != item[key]:
                raise ValueError('新关闭结果与统计修复证据不一致')
    output.mkdir(parents=True, exist_ok=True)
    checks_dir = output / 'source_checks'
    checks_dir.mkdir()
    write_json(output / 'protocol.json', protocol)
    write_json(output / 'preservation_before.json', protected)
    results, summaries, sources = [], [], []
    seen_runs, seen_episodes = set(), set()
    for case in protocol['cases']:
        if case['episode_id'] in seen_episodes:
            raise ValueError('人工事件ID重复；不得扩增机会分母')
        seen_episodes.add(case['episode_id'])
        annotation = read_json(case['annotations'])
        common = None
        for run in case['runs']:
            if run['run_id'] in seen_runs:
                raise ValueError('运行ID重复')
            seen_runs.add(run['run_id'])
            directory = Path(run['output'])
            info = read_json(directory / 'run_info.json')
            if info['recovery_enabled'] is not run['recovery_enabled']:
                raise ValueError('组别与原记录开启/关闭不一致')
            validate_annotation(case, annotation, info)
            pair = {k: info[k] for k in ('source_sha256', 'baseline_sha256', 'config', 'config_sha256', 'baseline_conditions', 'nominal_fps')}
            if common is not None and pair != common:
                raise ValueError('开启/关闭未共享相同输入、初始化、检测与配置')
            common = pair
            rows, events = read_rows(directory / 'frames.jsonl'), read_rows(directory / 'events.jsonl')
            diagnostic = check_counts(info, rows, events)
            provenance = run_historical_checks(run, checks_dir,
                Path(case['annotations']) if info['recovery_enabled'] and case['expected_return'] is False else None)
            whole = coverage(rows, info['recovery_enabled'])
            if whole['candidate_decisions'] != info['candidate_decision_counts']:
                raise ValueError('候选判定次数与运行汇总不一致')
            episode = evaluate_episode(info, rows, events, case, annotation, protocol['match_iou_min'])
            episode.update({'run_id': run['run_id'], 'case_id': case['case_id'], 'recovery_enabled': info['recovery_enabled'],
                            'source': info['source'], 'source_sha256': info['source_sha256'],
                            'annotations': case['annotations'], 'annotations_sha256': case['annotations_sha256'],
                            'algorithm_diagnostics': diagnostic, 'whole_run_candidate_coverage': whole})
            if provenance['record_checks'].get('raw_pixel_recomputed_frames') is not None:
                negative = episode['wrong_candidate_appearance_rejection']['coverage']
                if provenance['record_checks']['raw_pixel_recomputed_frames'] != negative['candidate_observations']:
                    raise ValueError('像素重算覆盖与新评价候选数不一致')
            results.append(episode)
            summaries.append({key: episode[key] for key in ('run_id', 'case_id', 'episode_id', 'expected_return', 'recovery_enabled',
                              'return_evaluation', 'acceptance_evaluation', 'no_wrong_binding', 'algorithm_diagnostics') } | {
                'appearance_rejection_status': episode['wrong_candidate_appearance_rejection']['status'],
                'annotated_negative_coverage': {k: v for k, v in episode['wrong_candidate_appearance_rejection']['coverage'].items() if k != 'frames'}
                    if episode['wrong_candidate_appearance_rejection']['coverage'] else None,
                'whole_run_candidate_observations': whole['candidate_observations'],
                'whole_run_candidate_frames': whole['frame_counts'].get('WITH_CANDIDATE', 0),
                'whole_run_candidate_decisions': whole['candidate_decisions'],
                'visible_target_unknown': {k: v for k, v in episode['visible_target_unknown'].items() if k != 'evidence'},
                'incorrect_current_position': episode['incorrect_current_position']})
            sources.append({'run_id': run['run_id'], 'output': run['output'], 'original_command': info['command'],
                            'historical_code_checks': provenance,
                            'input_sha256': {name: sha256(directory / name) for name in ('run_info.json', 'frames.jsonl', 'events.jsonl', 'references.json')}})
    write_json(output / 'per_event_results.json', results)
    with (output / 'candidate_coverage.jsonl').open('w', encoding='utf-8') as stream:
        for item in results:
            for kind, data in [('whole_run', item['whole_run_candidate_coverage']),
                               ('manual_other_bottle_interval', item['wrong_candidate_appearance_rejection']['coverage'])]:
                if data:
                    for row in data['frames']:
                        stream.write(json.dumps({'run_id': item['run_id'], 'episode_id': item['episode_id'], 'scope': kind, **row}) + '\n')
    summary = {'scope': protocol['scope'], 'status_meanings': STATUS_MEANINGS, 'groups': summaries,
               'unverified_scopes': [{'scope': scope, 'status': 'UNVERIFIED'} for scope in protocol['unverified_scopes']],
               'whole_video_visibility_evaluation': {'status': 'UNEVALUATED', 'false_alarm_rate': None},
               'annotation_limits': protocol['annotation_limits'],
               'note': '评价完成不改变00的验收/冻结/M3决策；FAIL项如实保留，无全项目固定false或PENDING_INPUT。'}
    write_json(output / 'summary.json', summary)
    verify_snapshot(protected)
    write_json(output / 'preservation_after.json', {p: sha256(Path(p)) for p in protected})
    write_json(output / 'run_info.json', {'completed': True, 'command': shlex.join(sys.orig_argv),
               'protocol_path': str(protocol_path), 'protocol_sha256': sha256(protocol_path),
               'evaluation_code_sha256': {name: sha256(Path(__file__).with_name(name))
                                          for name in ('evaluate_offline.py', 'evaluation_sources.py')},
               'git_head_at_execution': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
               'sources': sources, 'independent_evidence': protocol['evidence'],
               'old_files_preserved': len(protected), 'historical_output_files_rechecked': sum(Path(p).parts[0] == 'outputs' for p in historical),
               'scope': protocol['scope'], 'no_inference_or_state_changes': True})
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = evaluate(args.protocol, args.output)
    except (ValueError, OSError, KeyError, IndexError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, 'stderr', None) or str(exc)
        parser.exit(1, f'离线评价失败（旧输入不覆盖）: {detail}\n')
    print(json.dumps({'completed': True, 'groups': [{'run_id': g['run_id'], **g['return_evaluation'],
                      'appearance_rejection_status': g['appearance_rejection_status'],
                      'visible_control_status': g['visible_target_unknown']['status']} for g in result['groups']]},
                     ensure_ascii=False, indent=2))
