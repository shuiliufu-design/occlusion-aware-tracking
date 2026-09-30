"""M2 第一步：复用 M1 记录，指定目标、判断丢失、报告未经身份核验的候选。"""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shlex
import sys


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def box_iou(a, b):
    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0.0


class TargetState:
    """初始 ID 只作原生连续跟踪的引用；确认丢失后永不自动恢复绑定。"""

    def __init__(self, initial_row, manual_box, missing_frames, init_iou=0.5):
        if missing_frames < 1 or not 0 < init_iou <= 1:
            raise ValueError('缺失阈值须 >=1，初始化 IoU 须在 (0,1]')
        if len(manual_box) != 4 or not all(math.isfinite(v) for v in manual_box) or not (manual_box[0] < manual_box[2] and manual_box[1] < manual_box[3]):
            raise ValueError('人工框须为有限、正面积的 xyxy 坐标')
        # 人工框与检测框匹配；只有已关联的 bottle 可以初始化。
        matches = [d for d in initial_row['detections']
                   if d['class_name'] == 'bottle' and box_iou(manual_box, d['bbox_xyxy']) >= init_iou]
        if len(matches) != 1 or matches[0]['track_id'] is None:
            raise ValueError('人工框未唯一匹配已关联瓶子；请换帧或缩小指定框')
        detection = matches[0]
        tracks = [t for t in initial_row['tracks']
                  if t['track_id'] == detection['track_id'] and t['detection_index'] == detection['detection_index']]
        if len(tracks) != 1:
            raise ValueError('初始化检测与轨迹映射不一致')
        self.initialization = {'frame_index': initial_row['frame_index'], 'manual_bbox_xyxy': list(manual_box),
                               'selected_detection_index': detection['detection_index'],
                               'initial_native_track_id': detection['track_id'],
                               'initial_detection_iou': box_iou(manual_box, detection['bbox_xyxy']),
                               'class_id': detection['class_id'], 'class_name': detection['class_name'],
                               'basis': 'manual box on source frame; unique IoU match to associated detection'}
        self.native_id = detection['track_id']
        self.class_id = detection['class_id']
        self.threshold = missing_frames
        self.next_frame = initial_row['frame_index']
        self.missing_count = 0
        self.first_missing_frame = None
        self.confirmed_lost_frame = None
        self.last_observation = None
        self.loss_latched = False
        self.state = None

    def step(self, row):
        frame_index = row['frame_index']
        if frame_index != self.next_frame:
            raise ValueError('状态机输入帧索引必须连续')
        self.next_frame += 1
        previous = self.state
        candidates = []
        observation = None
        native = [t for t in row['tracks'] if t['track_id'] == self.native_id and t['class_id'] == self.class_id]
        if not self.loss_latched and native:
            if len(native) != 1:
                raise ValueError('同一帧存在重复目标轨迹')
            track = native[0]
            observation = {'frame_index': frame_index, 'bbox_xyxy': track['bbox_xyxy'],
                           'native_track_id': track['track_id'], 'detection_index': track['detection_index'],
                           'detection_score': track['detection_score'],
                           'basis': 'native continuity from manually initialized track; identity not independently verified'}
            self.last_observation = observation
            self.missing_count = 0
            self.first_missing_frame = None
            self.state, reason = 'TRACKING', 'native_track_observed'
        else:
            self.missing_count += 1
            if self.first_missing_frame is None:
                self.first_missing_frame = frame_index
            if not self.loss_latched and self.missing_count >= self.threshold:
                self.loss_latched = True
                self.confirmed_lost_frame = frame_index
            if self.loss_latched:
                # 分数、框、类别和 ID 是候选证据；均不作为原目标身份确认。
                candidates = [{**d, 'identity_check': {'performed': False, 'status': 'UNVERIFIED'},
                               'candidate_basis': 'same class only; may be another bottle or false positive',
                               'bound_to_target': False}
                              for d in row['detections'] if d['class_id'] == self.class_id]
                self.state = 'RECOVERY_CANDIDATE' if candidates else 'LOST'
                reason = 'unverified_candidate_present' if candidates else 'no_candidate_after_confirmed_loss'
            else:
                self.state, reason = 'TRACKING', 'missing_below_threshold'
        result = {**row, 'state': self.state, 'reason': reason,
                  'initial_native_track_id': self.native_id,
                  'target_observed_this_frame': observation is not None,
                  'pending_loss': not self.loss_latched and self.missing_count > 0,
                  'consecutive_missing_frames': self.missing_count,
                  'first_missing_frame': self.first_missing_frame,
                  'confirmed_lost_frame': self.confirmed_lost_frame,
                  'loss_latched': self.loss_latched,
                  'current_target_bbox_xyxy': observation['bbox_xyxy'] if observation else None,
                  'position_known': observation is not None,
                  'last_observed_target': self.last_observation,
                  'recovery_candidates': candidates, 'recovery_confirmed': False}
        event = None
        if previous != self.state:
            event = {key: result[key] for key in ('frame_index', 'timestamp_seconds', 'source_pos_msec_seconds',
                                                  'reason', 'consecutive_missing_frames', 'first_missing_frame',
                                                  'confirmed_lost_frame', 'current_target_bbox_xyxy')}
            event.update({'from_state': previous, 'to_state': self.state,
                          'candidate_evidence': candidates, 'recovery_confirmed': False})
        return result, event


def load_baseline(baseline, source):
    info = json.loads((baseline / 'run_info.json').read_text(encoding='utf-8'))
    rows = [json.loads(line) for line in (baseline / 'frames.jsonl').read_text(encoding='utf-8').splitlines()]
    if not info['completed'] or info['custom_recovery_enabled']:
        raise ValueError('需要已完成、未启用自定义恢复的原始基线')
    if sha256(source) != info['source_sha256']:
        raise ValueError('原视频 SHA-256 与基线不一致')
    if not rows or len(rows) != info['frames_processed'] or len(rows) != info['tracker_updates']:
        raise ValueError('基线记录数与处理帧数/跟踪更新数不一致')
    fps = info['nominal_fps']
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError('基线 FPS 无效')
    for index, row in enumerate(rows):
        if row['frame_index'] != index or not math.isclose(row['timestamp_seconds'], index / fps):
            raise ValueError(f'基线帧索引/时间错误: {index}')
        for d_index, detection in enumerate(row['detections']):
            if detection['detection_index'] != d_index:
                raise ValueError(f'基线检测索引错误: {index}')
        for track in row['tracks']:
            detection = row['detections'][track['detection_index']]
            if track['track_id'] != detection['track_id'] or track['class_id'] != detection['class_id']:
                raise ValueError(f'基线轨迹关联错误: {index}')
    return info, rows


def draw(frame, row):
    import cv2
    for candidate in row['recovery_candidates']:
        x1, y1, x2, y2 = map(round, candidate['bbox_xyxy'])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 190, 255), 3)
        label = f"UNVERIFIED native:{candidate['track_id']} det:{candidate['detection_score']:.2f}"
        cv2.putText(frame, label, (max(0, x1), max(140, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 190, 255), 2)
    box = row['current_target_bbox_xyxy']
    if box is not None:
        x1, y1, x2, y2 = map(round, box)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (50, 230, 80), 3)
        cv2.putText(frame, f"SELECTED native:{row['initial_native_track_id']}", (max(0, x1), max(140, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 230, 80), 2)
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 118), (20, 20, 20), -1)
    lines = [f"f{row['frame_index']}  {row['timestamp_seconds']:.2f}s  {row['state']}",
             f"missing:{row['consecutive_missing_frames']}  position:{'OBSERVED' if row['position_known'] else 'UNKNOWN'}",
             'CANDIDATES ARE NOT IDENTITY VERIFIED' if row['loss_latched'] else
             ('Missing below threshold; no current box' if row['pending_loss'] else 'Manually selected native track')]
    for n, line in enumerate(lines):
        cv2.putText(frame, line, (12, 28 + n * 34), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)


def run(args):
    import cv2
    if args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())):
        raise ValueError('输出目录须为空；请使用新路径')
    info, rows = load_baseline(args.baseline, args.source)
    end = args.end_frame if args.end_frame is not None else len(rows)
    if not 0 <= args.init_frame < end <= len(rows):
        raise ValueError('需满足 0 <= 初始化帧 < 结束帧 <= 基线帧数')
    x1, y1, x2, y2 = args.init_box
    if not (0 <= x1 < x2 <= info['width'] and 0 <= y1 < y2 <= info['height']):
        raise ValueError('人工框须位于原图范围内')
    machine = TargetState(rows[args.init_frame], args.init_box, args.missing_frames, args.init_iou)
    cap = cv2.VideoCapture(str(args.source))
    writer = None
    count = 0
    events, states = [], Counter()
    try:
        if not cap.isOpened():
            raise ValueError('无法打开原视频')
        # 顺序解码而非随机 seek，保留与 v2 相同的原帧索引。
        ok, frame = cap.read()
        if not ok or frame is None:
            raise ValueError('原视频无法解码')
        if frame.shape[:2] != (info['height'], info['width']):
            raise ValueError('原视频尺寸与基线不一致')
        args.output.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(str(args.output / 'status.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), info['nominal_fps'], (info['width'], info['height']))
        if not writer.isOpened():
            raise ValueError('无法创建状态视频')
        with (args.output / 'frames.jsonl').open('w', encoding='utf-8') as stream:
            index = 0
            while ok and frame is not None:
                if index >= len(rows) or frame.shape[:2] != (info['height'], info['width']):
                    raise ValueError('原视频帧数/尺寸与基线不一致')
                if args.init_frame <= index < end:
                    result, event = machine.step(rows[index])
                    result['output_frame_index'] = count
                    stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + '\n')
                    states[result['state']] += 1
                    if event:
                        events.append(event)
                    draw(frame, result)
                    writer.write(frame)
                    if count == 0 or event:
                        if not cv2.imwrite(str(args.output / f'frame_{index:06d}.jpg'), frame):
                            raise ValueError('预览保存失败')
                    count += 1
                index += 1
                ok, frame = cap.read()
            if index != len(rows) or count != end - args.init_frame:
                raise ValueError('原视频解码帧数/输出记录数与基线不一致')
    finally:
        cap.release()
        if writer is not None:
            writer.release()
    with (args.output / 'events.jsonl').open('w', encoding='utf-8') as stream:
        for event in events:
            stream.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + '\n')
    result_info = {'completed': True, 'command': shlex.join(sys.orig_argv),
                   'source': str(args.source), 'source_sha256': info['source_sha256'],
                   'baseline': str(args.baseline),
                   'baseline_sha256': {name: sha256(args.baseline / name) for name in ('frames.jsonl', 'run_info.json', 'bytetrack.yaml')},
                   'runner_sha256': sha256(Path(__file__)),
                   'baseline_conditions': {key: info[key] for key in ('model_sha256', 'tracker', 'tracker_config', 'inference', 'versions')},
                   'initialization': machine.initialization,
                   'config': {'init_frame': args.init_frame, 'init_box': args.init_box, 'init_iou': args.init_iou,
                              'missing_frames': args.missing_frames, 'missing_seconds_estimated': args.missing_frames / info['nominal_fps'],
                              'end_frame_exclusive': end},
                   'width': info['width'], 'height': info['height'], 'nominal_fps': info['nominal_fps'],
                   'source_decoded_frames': index, 'frames_processed': count,
                   'state_frame_counts': dict(states), 'transition_events': len(events),
                   'output_video': 'status.mp4', 'custom_state_module_enabled': True,
                   'identity_check_enabled': False, 'automatic_rebinding_enabled': False,
                   'notes': ['复用固定 M1 记录，不重跑或修改 YOLO/ByteTrack。',
                             '状态视频从初始化帧开始；JSONL 保留原帧索引/估算时间/源时间；output_frame_index 从 0 开始。',
                             'TRACKING 缺失宽限期仍清空当前框并报告 UNKNOWN；达到阈值进入丢失锁定。',
                             '确认丢失后任何同类检测（含原 ID）仅作候选；候选消失回 LOST，永不自动回 TRACKING。',
                             '候选检测分数不代表身份或跟踪可靠性；历史框不是当前位置。',
                             'mp4v 恒定名义帧率、无音频；未进行身份/遮挡标注或性能评价。']}
    write_json(args.output / 'run_info.json', result_info)
    return result_info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--init-frame', type=int, required=True, help='原视频从 0 开始的初始化帧')
    parser.add_argument('--init-box', type=float, nargs=4, required=True, metavar=('X1', 'Y1', 'X2', 'Y2'))
    parser.add_argument('--missing-frames', type=int, default=10)
    parser.add_argument('--init-iou', type=float, default=0.5)
    parser.add_argument('--end-frame', type=int, help='原视频结束帧，exclusive；默认至视频结束')
    args = parser.parse_args()
    try:
        result = run(args)
    except (ValueError, OSError, KeyError, IndexError) as exc:
        parser.exit(1, f'M2 运行失败: {exc}\n如已有部分输出，保留并换新目录重跑。\n')
    print(json.dumps({'frames_processed': result['frames_processed'], 'state_frame_counts': result['state_frame_counts'],
                      'output': str(args.output)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
