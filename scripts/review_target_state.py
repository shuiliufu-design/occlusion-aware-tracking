"""核对 M2 记录、原始基线证据、空位置规则、状态事件与视频解码。"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path

import cv2
import numpy as np

from run_target_state import sha256, write_json


def review(output, selected_frames):
    info = json.loads((output / 'run_info.json').read_text(encoding='utf-8'))
    baseline = Path(info['baseline'])
    for name, digest in info['baseline_sha256'].items():
        if sha256(baseline / name) != digest:
            raise ValueError(f'基线文件发生变化: {name}')
    if sha256(Path(info['source'])) != info['source_sha256']:
        raise ValueError('原视频发生变化')
    original = [json.loads(line) for line in (baseline / 'frames.jsonl').read_text(encoding='utf-8').splitlines()]
    rows = [json.loads(line) for line in (output / 'frames.jsonl').read_text(encoding='utf-8').splitlines()]
    events = [json.loads(line) for line in (output / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
    start, end = info['config']['init_frame'], info['config']['end_frame_exclusive']
    if len(rows) != end - start or len(rows) != info['frames_processed']:
        raise ValueError('记录数与运行配置不一致')
    if any(not start <= index < end for index in selected_frames):
        raise ValueError('预览帧不在输出区间内')
    transitions, counts = [], Counter()
    previous_state, last_observation = None, None
    lost = False
    missing_count = 0
    for offset, row in enumerate(rows):
        index = start + offset
        if row['frame_index'] != index or row['output_frame_index'] != offset:
            raise ValueError('原帧索引/输出索引错误')
        if any(row[key] != original[index][key] for key in original[index]):
            raise ValueError(f'原基线证据被改动: {index}')
        counts[row['state']] += 1
        if row['recovery_confirmed'] or row['initial_native_track_id'] != info['initialization']['initial_native_track_id']:
            raise ValueError('不应自动确认恢复或修改初始 ID')
        if row['target_observed_this_frame']:
            if lost or row['state'] != 'TRACKING' or row['current_target_bbox_xyxy'] is None:
                raise ValueError('丢失后自动绑定或观察位置不一致')
            missing_count = 0
            last_observation = row['last_observed_target']
            if last_observation['frame_index'] != index:
                raise ValueError('观察框时间错误')
        else:
            missing_count += 1
            if row['current_target_bbox_xyxy'] is not None or row['position_known']:
                raise ValueError('无观察时宣称知道目标当前位置')
            if row['last_observed_target'] != last_observation:
                raise ValueError('候选/历史框被认作原目标的新观察')
        if row['consecutive_missing_frames'] != missing_count:
            raise ValueError('连续缺失计数错误')
        if missing_count >= info['config']['missing_frames']:
            lost = True
        if row['loss_latched'] != lost:
            raise ValueError('丢失阈值或锁定状态错误')
        candidates = row['recovery_candidates']
        if lost:
            expected_candidates = [d for d in original[index]['detections'] if d['class_id'] == info['initialization']['class_id']]
            if [{key: c[key] for key in d} for c, d in zip(candidates, expected_candidates)] != expected_candidates or len(candidates) != len(expected_candidates):
                raise ValueError('候选与检测证据不一致')
            if row['state'] != ('RECOVERY_CANDIDATE' if candidates else 'LOST'):
                raise ValueError('候选出现/消失状态错误')
        elif row['state'] != 'TRACKING' or candidates:
            raise ValueError('确认丢失前状态错误')
        if row['position_known'] != row['target_observed_this_frame']:
            raise ValueError('位置已知标志错误')
        if any(c['bound_to_target'] or c['identity_check'] != {'performed': False, 'status': 'UNVERIFIED'} for c in candidates):
            raise ValueError('候选未经核验却被认定身份')
        if row['state'] != previous_state:
            transitions.append((index, previous_state, row['state']))
        previous_state = row['state']
    if [(e['frame_index'], e['from_state'], e['to_state']) for e in events] != transitions or len(events) != info['transition_events']:
        raise ValueError('状态转换事件与逐帧记录不一致')
    for event in events:
        row = rows[event['frame_index'] - start]
        if event['candidate_evidence'] != row['recovery_candidates'] or event['recovery_confirmed']:
            raise ValueError('事件候选证据不一致')
        if any(event[key] != row[key] for key in ('timestamp_seconds', 'source_pos_msec_seconds', 'reason', 'consecutive_missing_frames', 'first_missing_frame', 'confirmed_lost_frame', 'current_target_bbox_xyxy')):
            raise ValueError('事件时间/缺失证据与逐帧记录不一致')
    if dict(counts) != info['state_frame_counts']:
        raise ValueError('状态统计不一致')
    cap = cv2.VideoCapture(str(output / info['output_video']))
    tiles, decoded = [], 0
    try:
        if not cap.isOpened():
            raise ValueError('状态视频无法打开')
        if not math.isclose(cap.get(cv2.CAP_PROP_FPS), info['nominal_fps'], rel_tol=1e-3):
            raise ValueError('输出 FPS 不一致')
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if decoded >= len(rows) or frame.shape[:2] != (info['height'], info['width']):
                raise ValueError('状态视频帧数/尺寸错误')
            index = start + decoded
            if index in selected_frames:
                if not cv2.imwrite(str(output / f'frame_{index:06d}.jpg'), frame):
                    raise ValueError('单帧保存失败')
                tile = np.full((340, 180, 3), 245, np.uint8)
                tile[:320] = cv2.resize(frame, (180, 320))
                cv2.putText(tile, f'f{index} {rows[decoded]["state"]}', (2, 334), cv2.FONT_HERSHEY_SIMPLEX, 0.30, (20, 20, 20), 1)
                tiles.append(tile)
            decoded += 1
    finally:
        cap.release()
    if decoded != len(rows):
        raise ValueError('状态视频重解码帧数与记录不一致')
    if tiles:
        columns = 4
        sheet = np.full((math.ceil(len(tiles) / columns) * 340, columns * 180, 3), 245, np.uint8)
        for offset, tile in enumerate(tiles):
            y, x = (offset // columns) * 340, (offset % columns) * 180
            sheet[y:y + 340, x:x + 180] = tile
        if not cv2.imwrite(str(output / 'contact_sheet.jpg'), sheet):
            raise ValueError('预览保存失败')
    result = {'record_checks_passed': True, 'baseline_evidence_unchanged': True,
              'records': len(rows), 'output_decoded_frames': decoded, 'state_frame_counts': dict(counts),
              'transitions': transitions, 'selected_preview_frames': selected_frames,
              'automatic_rebinding_observed': False,
              'notes': ['只核查记录/状态规则/视频一致性，不证明物理身份、真实遮挡区间或恢复成功。']}
    write_json(output / 'review.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='*', default=[])
    args = parser.parse_args()
    try:
        print(json.dumps(review(args.output, args.frames), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, IndexError) as exc:
        parser.exit(1, f'M2 核查失败: {exc}\n')
