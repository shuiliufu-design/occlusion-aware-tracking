"""M2 第二步：复用 M1 检测，保存冻结外观参考、恢复关联和证据。"""

import argparse
from collections import Counter
import json
from pathlib import Path
import platform
import shlex
import sys

import cv2
import numpy as np

try:
    from .appearance_recovery import DEFAULT_CONFIG_PATH, RecoveryState, load_config, public_feature
    from .run_target_state import TargetState, load_baseline, sha256, write_json
except ImportError:
    from appearance_recovery import DEFAULT_CONFIG_PATH, RecoveryState, load_config, public_feature
    from run_target_state import TargetState, load_baseline, sha256, write_json


def draw(frame, row):
    for candidate in row['recovery_candidates']:
        x1, y1, x2, y2 = map(round, candidate['bbox_xyxy'])
        color = (0, 190, 255) if candidate.get('decision') in ('ACCEPTABLE', 'AMBIGUOUS') else (70, 100, 255)
        if not candidate.get('bound_to_target'):
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{candidate.get('decision', 'UNVERIFIED')} native:{candidate['track_id']} n:{candidate.get('confirmation_count', 0)}"
            cv2.putText(frame, label, (max(0, x1 - 20), max(145, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.46, color, 2)
    if row['current_target_bbox_xyxy'] is not None:
        x1, y1, x2, y2 = map(round, row['current_target_bbox_xyxy'])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (50, 230, 80), 3)
        cv2.putText(frame, f"{row['target_uid']} native:{row['active_native_track_id']}",
                    (max(0, x1), max(145, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 230, 80), 2)
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 130), (20, 20, 20), -1)
    lines = [f"f{row['frame_index']} {row['timestamp_seconds']:.2f}s {row['state']}",
             f"{row['target_uid']} native:{row['active_native_track_id']} missing:{row['consecutive_missing_frames']} position:{'OBSERVED' if row['position_known'] else 'UNKNOWN'}",
             'RULE ACCEPTANCE; PHYSICAL ID EVALUATED SEPARATELY' if row['recovery_confirmed'] else
             ('APPEARANCE RULES; SCORES ARE NOT ID PROBABILITIES' if row['recovery_enabled'] else 'RECOVERY DISABLED; UNVERIFIED CANDIDATES ONLY')]
    for offset, line in enumerate(lines):
        cv2.putText(frame, line, (12, 28 + offset * 36), cv2.FONT_HERSHEY_SIMPLEX, 0.53, (255, 255, 255), 1)


def run(args):
    if args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())):
        raise ValueError('输出目录必须为空，请使用新路径')
    config = load_config(args.config)
    info, rows = load_baseline(args.baseline, args.source)
    end = args.end_frame if args.end_frame is not None else len(rows)
    if not 0 <= args.init_frame < end <= len(rows):
        raise ValueError('初始化/结束帧范围无效')
    x1, y1, x2, y2 = args.init_box
    if not 0 <= x1 < x2 <= info['width'] or not 0 <= y1 < y2 <= info['height']:
        raise ValueError('人工框必须在原图内')
    machine = RecoveryState(rows[args.init_frame], args.init_box, args.missing_frames, config, args.init_iou, args.target_uid)
    disabled = TargetState(rows[args.init_frame], args.init_box, args.missing_frames, args.init_iou) if args.disable_recovery else None
    preserved_paths = [args.baseline]
    if args.step1_output:
        preserved_paths.append(args.step1_output)
    preserved = {str(p): sha256(p) for root in preserved_paths for p in root.rglob('*') if p.is_file()}
    cap = cv2.VideoCapture(str(args.source))
    writer = None
    events, states = [], Counter()
    counts = Counter()
    saved_references, count, index = 0, 0, 0
    try:
        if not cap.isOpened():
            raise ValueError('原视频无法打开')
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'references').mkdir()
        writer = cv2.VideoWriter(str(args.output / 'status.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), info['nominal_fps'], (info['width'], info['height']))
        if not writer.isOpened():
            raise ValueError('无法创建状态视频')
        with (args.output / 'frames.jsonl').open('w', encoding='utf-8') as stream:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if index >= len(rows) or frame.shape[:2] != (info['height'], info['width']):
                    raise ValueError('原视频帧数或尺寸与基线不一致')
                if args.init_frame <= index < end:
                    if disabled:
                        result, event = disabled.step(rows[index])
                        result.update({'target_uid': args.target_uid, 'active_native_track_id': disabled.native_id if not disabled.loss_latched else None})
                        frame_events = [{**event, 'event_type': 'STATE_TRANSITION'}] if event else []
                    else:
                        result, frame_events = machine.step(rows[index], frame)
                    result['output_frame_index'] = count
                    result['recovery_enabled'] = not args.disable_recovery
                    stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + '\n')
                    states[result['state']] += 1
                    counts.update(c.get('decision', 'UNVERIFIED') for c in result['recovery_candidates'])
                    events.extend(frame_events)
                    for reference in machine.bank.samples[saved_references:]:
                        path = args.output / 'references' / f"frame_{reference['frame_index']:06d}.png"
                        if not cv2.imwrite(str(path), reference['feature']['crop']):
                            raise ValueError('参考裁剪保存失败')
                        saved_references += 1
                    draw(frame, result)
                    writer.write(frame)
                    if count == 0 or frame_events:
                        if not cv2.imwrite(str(args.output / f'frame_{index:06d}.jpg'), frame):
                            raise ValueError('状态预览保存失败')
                    count += 1
                index += 1
            if index != len(rows) or count != end - args.init_frame:
                raise ValueError('原视频解码或输出帧数不一致')
    finally:
        cap.release()
        if writer is not None:
            writer.release()
    machine.bank.freeze('END_OF_RUN' if not disabled else 'RECOVERY_DISABLED')
    refs = []
    for sample in machine.bank.samples:
        filename = f"references/frame_{sample['frame_index']:06d}.png"
        refs.append({'frame_index': sample['frame_index'], 'detection': sample['detection'],
                     'quality': public_feature(sample['feature']), 'crop': filename, 'crop_sha256': sha256(args.output / filename)})
    if machine.bank.samples:
        np.savez_compressed(args.output / 'references/features.npz',
                            cap_hist=np.stack([s['feature']['cap_hist'] for s in machine.bank.samples]),
                            label_hist=np.stack([s['feature']['label_hist'] for s in machine.bank.samples]),
                            texture=np.stack([s['feature']['texture'] for s in machine.bank.samples]))
    reference_info = {**machine.bank.summary(), 'references': refs, 'sampling_decisions': machine.bank.decisions}
    write_json(args.output / 'references.json', reference_info)
    with (args.output / 'events.jsonl').open('w', encoding='utf-8') as stream:
        for event in events:
            stream.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + '\n')
    after = {str(p): sha256(p) for root in preserved_paths for p in root.rglob('*') if p.is_file()}
    if after != preserved:
        raise ValueError('原始输出发生变化')
    write_json(args.output / 'preservation.json', {'all_unchanged': True, 'before': preserved, 'after': after})
    result_info = {'completed': True, 'command': shlex.join(sys.orig_argv), 'source': str(args.source),
                   'source_sha256': info['source_sha256'], 'baseline': str(args.baseline),
                   'baseline_sha256': {name: sha256(args.baseline / name) for name in ('run_info.json', 'frames.jsonl', 'bytetrack.yaml')},
                   'code_sha256': {name: sha256(Path(__file__).with_name(name)) for name in ('run_recovery.py', 'appearance_recovery.py')},
                   'config_path': str(args.config), 'config_sha256': sha256(args.config), 'appearance_config': config,
                   'config': {'init_frame': args.init_frame, 'init_box': args.init_box, 'init_iou': args.init_iou,
                              'missing_frames': args.missing_frames, 'missing_seconds_estimated': args.missing_frames / info['nominal_fps'],
                              'end_frame_exclusive': end, 'target_uid': args.target_uid},
                   'initialization': machine.initialization, 'recovery_enabled': not args.disable_recovery,
                   'baseline_conditions': {key: info[key] for key in ('model_sha256', 'tracker', 'tracker_config', 'inference', 'versions')},
                   'versions': {'python': platform.python_version(), 'opencv': cv2.__version__, 'numpy': np.__version__},
                   'detections_reused': True, 'reference_bank': machine.bank.summary(),
                   'references_json_sha256': sha256(args.output / 'references.json'),
                   'width': info['width'], 'height': info['height'], 'nominal_fps': info['nominal_fps'],
                   'source_decoded_frames': index, 'frames_processed': count, 'state_frame_counts': dict(states),
                   # 第一阶段确认丢失后永不自动恢复，因此关闭分支最多一段丢失。
                   # 候选消失/重现的状态切换不开始新的丢失段。
                   'candidate_decision_counts': dict(counts),
                   'loss_episodes': int(disabled.loss_latched) if disabled else machine.loss_episodes,
                   'recovery_attempts': machine.attempts, 'program_accepts': machine.accepts,
                   'events': len(events), 'output_video': 'status.mp4',
                   'notes': ['参考只用初始化后的因果合格观察；轨迹仍在时跳过低质量帧，首次轨迹缺失/确认丢失即冻结；候选及恢复画面不更新。',
                             'score 与程序接受不证明物理身份；人工评价从独立标注另算。',
                             '新增模块关闭时委托原 TargetState，逐帧退回第一步仅候选行为。',
                             '视频从初始化帧开始，记录保留原帧号及两种时间，mp4v、名义 FPS、无音频。']}
    write_json(args.output / 'run_info.json', result_info)
    return result_info


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--step1-output', type=Path, help='需要检查保全的第一步结果目录')
    parser.add_argument('--init-frame', type=int, required=True)
    parser.add_argument('--init-box', type=float, nargs=4, required=True)
    parser.add_argument('--init-iou', type=float, default=0.5)
    parser.add_argument('--missing-frames', type=int, default=10)
    parser.add_argument('--end-frame', type=int)
    parser.add_argument('--target-uid', default='T1')
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument('--disable-recovery', action='store_true')
    args = parser.parse_args()
    try:
        result = run(args)
    except (ValueError, OSError, KeyError, IndexError, cv2.error) as exc:
        parser.exit(1, f'M2 第二步运行失败: {exc}\n保留部分输出并使用新目录重跑。\n')
    print(json.dumps({key: result[key] for key in ('frames_processed', 'state_frame_counts', 'program_accepts', 'reference_bank')}, ensure_ascii=False, indent=2))
