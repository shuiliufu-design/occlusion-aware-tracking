"""真实挂包误检裁剪 + 构造 LOST 上下文；不是端到端错误瓶子实验。"""

import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import shlex
import sys

import cv2

from appearance_recovery import RecoveryState, extract_feature, load_config
from run_target_state import box_iou, load_baseline, sha256, write_json


def restore_bank(machine, recovery_output, config):
    refs = json.loads((recovery_output / 'references.json').read_text(encoding='utf-8'))
    for entry in refs['references']:
        crop = cv2.imread(str(recovery_output / entry['crop']))
        height, width = crop.shape[:2]
        detection = {**entry['detection'], 'bbox_xyxy': [0, 0, width, height]}
        feature = extract_feature(crop, detection, config)
        if not feature['valid']:
            raise ValueError('保存的参考裁剪无法重建')
        feature['aspect_ratio'] = entry['quality']['aspect_ratio']
        machine.bank.samples.append({'frame_index': entry['frame_index'], 'detection': entry['detection'], 'feature': feature})
    machine.bank.freeze('MODULE_FIXTURE_LOADED_FROZEN_REFERENCE')
    if machine.bank.digest() != refs['sha256']:
        raise ValueError('重建参考的特征校验不一致')
    return refs['sha256']


def forced_lost_machine(rows, run_info, output, config):
    init = run_info['config']
    machine = RecoveryState(rows[init['init_frame']], init['init_box'], init['missing_frames'], config, init['init_iou'], init['target_uid'])
    restore_bank(machine, output, config)
    machine.lost = True
    machine.state = 'LOST'
    machine.active_id = None
    machine.next_frame = len(rows) + init['init_frame']
    machine.missing_count = init['missing_frames']
    machine.first_missing_frame = machine.next_frame - init['missing_frames']
    machine.confirmed_lost_frame = machine.next_frame - 1
    machine.loss_episodes = 1
    return machine


def validate(args):
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('模块验证输出必须为空')
    info, rows = load_baseline(args.baseline, args.source)
    run_info = json.loads((args.recovery_output / 'run_info.json').read_text(encoding='utf-8'))
    config = run_info['appearance_config']
    if not 0 <= args.negative_start < args.negative_end <= len(rows):
        raise ValueError('负例原帧范围无效')
    args.output.mkdir(parents=True, exist_ok=True)
    machine = forced_lost_machine(rows, run_info, args.recovery_output, config)
    digest = machine.bank.digest()
    cap = cv2.VideoCapture(str(args.source))
    cases, counts = [], Counter()
    index = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if args.negative_start <= index < args.negative_end:
                matching = [d for d in rows[index]['detections'] if box_iou(d['bbox_xyxy'], args.negative_box) >= 0.5]
                if len(matching) != 1:
                    raise ValueError(f'挂包人工区域没有唯一检测匹配: f{index}')
                detection = matching[0]
                constructed = {**rows[index], 'frame_index': machine.next_frame, 'detections': [copy.deepcopy(detection)],
                               'tracks': [copy.deepcopy(t) for t in rows[index]['tracks'] if t['track_id'] == detection['track_id']]}
                result, events = machine.step(constructed, frame)
                candidate = result['recovery_candidates'][0]
                counts[candidate['decision']] += 1
                feature = extract_feature(frame, detection, config)
                if 'crop' in feature:
                    crop = feature['crop']
                else:
                    x1, y1, x2, y2 = map(round, detection['bbox_xyxy'])
                    crop = frame[y1:y2, x1:x2]
                cv2.imwrite(str(args.output / f'bag_frame_{index:06d}.png'), crop)
                cases.append({'source_frame_index': index, 'source_timestamp_seconds': rows[index]['timestamp_seconds'],
                              'source_pos_msec_seconds': rows[index]['source_pos_msec_seconds'],
                              'original_baseline_row': rows[index], 'constructed_input': constructed,
                              'candidate': candidate, 'program_accepted': result['recovery_confirmed'],
                              'fixture_truth': 'OTHER_OBJECT_BAG_REGION', 'events': events})
            index += 1
    finally:
        cap.release()
    if not cases or any(case['program_accepted'] for case in cases) or counts['REJECTED_APPEARANCE'] < 1:
        raise ValueError('挂包外观拒绝分支未通过，不能只靠低分无绑定宣称外观拒绝')
    # 重复真实参考裁剪产生两个等分候选；只检验竞争歧义分支。
    ambiguity = forced_lost_machine(rows, run_info, args.recovery_output, config)
    sample = ambiguity.bank.samples[0]
    crop = sample['feature']['crop']
    height, width = crop.shape[:2]
    native_id = max(t['track_id'] for row in rows for t in row['tracks']) + 1
    data = []
    for _ in range(config['confirmation_frames'] + 1):
        detections = [{**sample['detection'], 'detection_index': offset, 'bbox_xyxy': [0, 0, width, height], 'track_id': native_id + offset} for offset in range(2)]
        synthetic = {'frame_index': ambiguity.next_frame, 'timestamp_seconds': ambiguity.next_frame / info['nominal_fps'],
                     'source_pos_msec_seconds': None, 'detections': detections, 'tracks': copy.deepcopy(detections)}
        result, _ = ambiguity.step(synthetic, crop)
        data.append(result)
    if ambiguity.accepts or any(c['decision'] != 'AMBIGUOUS' for row in data for c in row['recovery_candidates']):
        raise ValueError('等分竞争构造例未暂缓')
    if machine.bank.digest() != digest or ambiguity.bank.digest() != digest:
        raise ValueError('模块候选污染冻结参考')
    report = {'scope': 'real bag detection crops + constructed LOST context; not end-to-end false-bottle recovery',
              'command': shlex.join(sys.orig_argv), 'config': config,
              'code_sha256': sha256(Path(__file__)),
              'recovery_run_info_sha256': sha256(args.recovery_output / 'run_info.json'),
              'source_sha256': info['source_sha256'], 'reference_sha256': digest,
              'reference_frames': machine.bank.summary()['sample_frames'],
              'negative_selection': {'frames': [args.negative_start, args.negative_end], 'manual_bbox_xyxy': args.negative_box},
              'bag_decision_counts': dict(counts), 'bag_program_accepts': machine.accepts,
              'bag_cases': cases, 'equal_score_fixture_accepted': ambiguity.accepts,
              'equal_score_fixture_frames': len(data), 'reference_unchanged': True,
              'real_wrong_bottle_validation': 'PENDING_INPUT',
              'notes': ['挂包位于初始化前，仅重用其真实裁剪与分数作为模块输入；未改写原始基线。',
                        '等分例是同一真实参考裁剪的重复候选，不代表真实画面同时出现两个瓶子。']}
    write_json(args.output / 'module_validation.json', report)
    write_json(args.output / 'ambiguity_fixture.json', data)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--recovery-output', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--negative-start', type=int, required=True)
    parser.add_argument('--negative-end', type=int, required=True)
    parser.add_argument('--negative-box', type=float, nargs=4, required=True)
    args = parser.parse_args()
    try:
        result = validate(args)
    except (ValueError, OSError, KeyError, IndexError, cv2.error) as exc:
        parser.exit(1, f'模块验证失败: {exc}\n')
    print(json.dumps({key: result[key] for key in ('bag_decision_counts', 'bag_program_accepts', 'equal_score_fixture_accepted', 'reference_unchanged')}, ensure_ascii=False, indent=2))
