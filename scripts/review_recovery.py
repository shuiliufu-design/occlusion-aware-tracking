"""核对恢复证据、输出保全、连续确认、视频与独立身份记录。"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path

import cv2
import numpy as np

try:
    from .run_target_state import box_iou, sha256, write_json
except ImportError:
    from run_target_state import box_iou, sha256, write_json


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def check_appearance(judgment, config):
    best = judgment['best_reference']
    if best is None:
        if judgment['confirmation_count']:
            raise ValueError('无外观证据却累计确认')
        return
    comparisons = judgment['reference_comparisons']
    chosen = max(comparisons, key=lambda c: c['score'])
    if any(best[key] != chosen[key] for key in chosen):
        raise ValueError('最佳参考证据混合或未选最高分')
    for comparison in comparisons:
        cap, label, ncc = (comparison[key] for key in ('cap_distance', 'label_distance', 'texture_ncc'))
        wc, wl, wt = config['score_weights']
        score = wc * (1 - cap) + wl * (1 - label) + wt * ((ncc + 1) / 2)
        if not math.isclose(score, comparison['score'], abs_tol=1e-10):
            raise ValueError('外观排序分数错误')
        if config.get('texture_alignment_enabled', False):
            alignment = comparison['texture_alignment']
            dx, dy = alignment['shift_xy']
            width, height = config['texture_width'], config['texture_height']
            mx, my = math.floor(config['texture_max_shift_fraction_x'] * width), math.floor(config['texture_max_shift_fraction_y'] * height)
            a, b = alignment['candidate_region_xyxy'], alignment['reference_region_xyxy']
            expected_a = [max(0, -dx), max(0, -dy), min(width, width-dx), min(height, height-dy)]
            expected_b = [a[0]+dx, a[1]+dy, a[2]+dx, a[3]+dy]
            overlap = (a[2]-a[0]) * (a[3]-a[1]) / (width*height)
            if (type(dx) is not int or type(dy) is not int or abs(dx) > mx or abs(dy) > my or
                    alignment['mode'] != 'BOUNDED_TRANSLATION' or alignment['max_shift_xy'] != [mx, my] or
                    a != expected_a or b != expected_b or
                    not math.isclose(overlap, alignment['overlap_fraction'], abs_tol=1e-12) or
                    overlap < config['texture_min_overlap_fraction'] or
                    min(alignment['candidate_gray_std'], alignment['reference_gray_std']) < config['min_gray_std'] or
                    not all(math.isfinite(alignment[key]) for key in ('ncc', 'candidate_gray_std', 'reference_gray_std')) or
                    alignment['ncc'] != ncc or not 0 < alignment['valid_shifts'] <= alignment['tested_shifts']):
                raise ValueError('有界纹理对齐证据非法')
            zero = alignment['zero_shift_ncc']
            if zero is not None and (not math.isfinite(zero) or ncc < zero):
                raise ValueError('零位移/最佳对齐NCC矛盾')
    gates = {'cap_color': best['cap_distance'] <= config['cap_distance_max'],
             'label_color': best['label_distance'] <= config['label_distance_max'],
             'label_texture': best['texture_ncc'] >= config['texture_ncc_min'],
             'aspect_ratio': config['aspect_ratio_min'] <= best['aspect_ratio_relative'] <= config['aspect_ratio_max'],
             'score': best['score'] >= config['score_min']}
    if gates != best['gates'] or best['appearance_passed'] != all(gates.values()):
        raise ValueError('门控结果与分量不一致')
    if judgment['confirmation_count'] and (judgment['decision'] != 'ACCEPTABLE' or not all(gates.values()) or judgment['track_id'] is None or judgment['confirmation_blockers']):
        raise ValueError('不合格或未关联候选累计确认')


def evaluate_identity(info, rows, events, annotation_path):
    accepts = [event for event in events if event['event_type'] == 'RECOVERY_ACCEPTED']
    result = {'recovery_attempts': info['recovery_attempts'], 'program_accepts': len(accepts),
              'correct_accepts': 0, 'incorrect_accepts': 0, 'unevaluated_accepts': 0,
              'unrecovered_events': info['loss_episodes'] - len({event['loss_episode_id'] for event in accepts}),
              'acceptance_results': [], 'real_wrong_bottle_validation': 'PENDING_INPUT',
              'real_ambiguity_validation': 'PENDING_INPUT', 'same_packaging_validation': 'PENDING_INPUT',
              'm2_step2_fully_accepted': False}
    annotation = json.loads(annotation_path.read_text(encoding='utf-8')) if annotation_path else None
    if annotation and annotation['source_sha256'] != info['source_sha256']:
        raise ValueError('身份记录视频校验不一致')
    for event in accepts:
        index = event['frame_index']
        label = next((item for item in annotation['keyframes'] if item['frame_index'] == index), None) if annotation else None
        verdict = 'UNEVALUATED'
        if label and label['identity'] != 'UNCERTAIN' and box_iou(label['bbox_xyxy'], event['candidate']['bbox_xyxy']) >= 0.5:
            verdict = 'CORRECT' if label['identity'] == info['config']['target_uid'] else 'INCORRECT'
        key = {'CORRECT': 'correct_accepts', 'INCORRECT': 'incorrect_accepts', 'UNEVALUATED': 'unevaluated_accepts'}[verdict]
        result[key] += 1
        item = {'accept_frame': index, 'verdict': verdict, 'basis': annotation['confirmation_basis'] if annotation else None}
        if annotation and verdict == 'CORRECT':
            reappearance = annotation['recognizable_reappearance_frame']
            if not info['config']['init_frame'] <= reappearance <= index:
                raise ValueError('可辨认重现帧范围无效')
            by_index = {row['frame_index']: row for row in rows}
            start = by_index[reappearance]
            item.update({'recognizable_reappearance_frame': reappearance,
                         'latency_frames': index - reappearance,
                         'latency_seconds_frame_fps': (index - reappearance) / info['nominal_fps'],
                         'latency_seconds_source_time': event['source_pos_msec_seconds'] - start['source_pos_msec_seconds'],
                         'timing_annotator': annotation['timing_annotator'],
                         'timing_basis': annotation['reappearance_criterion']})
        result['acceptance_results'].append(item)
    return result


def review(output, selected_frames, annotations=None):
    info = json.loads((output / 'run_info.json').read_text(encoding='utf-8'))
    for name, digest in info['code_sha256'].items():
        if sha256(Path(__file__).with_name(name)) != digest:
            raise ValueError(f'运行代码已变化，需保留旧结果并用新目录重跑: {name}')
    if sha256(Path(info['config_path'])) != info['config_sha256'] or sha256(Path(info['source'])) != info['source_sha256']:
        raise ValueError('配置或原视频已变化')
    preservation = json.loads((output / 'preservation.json').read_text(encoding='utf-8'))
    if preservation['before'] != preservation['after'] or any(sha256(Path(path)) != digest for path, digest in preservation['before'].items()):
        raise ValueError('原始输出保全校验失败')
    original = read_rows(Path(info['baseline']) / 'frames.jsonl')
    rows, events = read_rows(output / 'frames.jsonl'), read_rows(output / 'events.jsonl')
    refs = json.loads((output / 'references.json').read_text(encoding='utf-8'))
    if sha256(output / 'references.json') != info['references_json_sha256']:
        raise ValueError('参考记录变化')
    for reference in refs['references']:
        if sha256(output / reference['crop']) != reference['crop_sha256']:
            raise ValueError('参考裁剪变化')
    start, end = info['config']['init_frame'], info['config']['end_frame_exclusive']
    if len(rows) != info['frames_processed'] or len(rows) != end - start:
        raise ValueError('输出记录数与配置不一致')
    if any(not start <= index < end for index in selected_frames):
        raise ValueError('预览帧不在输出区间')
    previous_digest, previous_state = None, None
    transition_keys = []
    missing = 0
    counts = Counter()
    disabled_rows = None
    if not info['recovery_enabled']:
        step1_paths = [Path(path).parent for path in preservation['before']
                       if path.endswith('/run_info.json') and
                       json.loads(Path(path).read_text()).get('custom_state_module_enabled') is True and
                       json.loads(Path(path).read_text()).get('identity_check_enabled') is False]
        if step1_paths:
            disabled_rows = {row['frame_index']: row for row in read_rows(step1_paths[0] / 'frames.jsonl')}
    for offset, row in enumerate(rows):
        index = start + offset
        if row['frame_index'] != index or row['output_frame_index'] != offset:
            raise ValueError('原帧索引或输出索引不连续')
        if any(row[key] != original[index][key] for key in original[index]):
            raise ValueError('原生检测/跟踪或时间被改写')
        if disabled_rows and any(row[key] != disabled_rows[index][key] for key in disabled_rows[index]):
            raise ValueError('关闭恢复后未退回第一步行为')
        counts[row['state']] += 1
        if row['target_observed_this_frame']:
            missing = 0
            if not row['position_known'] or row['current_target_bbox_xyxy'] is None or row['state'] != 'TRACKING':
                raise ValueError('观察与状态/位置不一致')
        else:
            missing += 1
            if row['position_known'] or row['current_target_bbox_xyxy'] is not None:
                raise ValueError('无可靠观察时填写当前位置')
        if row['consecutive_missing_frames'] != missing:
            raise ValueError('缺失计数不连续')
        if info['recovery_enabled']:
            bank = row['reference_bank']
            if any(frame > index or frame >= start + info['appearance_config']['reference_wait_frames'] for frame in bank['sample_frames']):
                raise ValueError('参考使用未来或窗口外帧')
            if previous_digest is not None and bank['sha256'] != previous_digest:
                raise ValueError('冻结参考被更新')
            if bank['frozen']:
                previous_digest = bank['sha256']
            for judgment in row['recovery_candidates']:
                check_appearance(judgment, info['appearance_config'])
            active = row.get('active_track_evidence')
            if active and active.get('best_reference'):
                check_appearance({**active, 'confirmation_count': 0}, info['appearance_config'])
            ranked = sorted([c for c in row['recovery_candidates'] if c['best_reference'] is not None], key=lambda c:c['best_reference']['score'], reverse=True)
            progressing = [c for c in row['recovery_candidates'] if c['confirmation_count']]
            if progressing:
                if len(progressing) != 1 or progressing[0] is not ranked[0]:
                    raise ValueError('确认了非最高分候选')
                if len(ranked) > 1 and ranked[0]['best_reference']['score'] - ranked[1]['best_reference']['score'] + 1e-12 < info['appearance_config']['competition_margin']:
                    raise ValueError('差值不足仍累计确认')
            if row['target_observed_this_frame'] and row['active_track_evidence'] and row['active_track_evidence'].get('best_reference'):
                if not row['active_track_evidence']['best_reference']['appearance_passed']:
                    raise ValueError('活动轨迹未通过外观仍作观察')
        if row['state'] != previous_state:
            transition_keys.append((index, previous_state, row['state']))
        previous_state = row['state']
    if dict(counts) != info['state_frame_counts']:
        raise ValueError('状态计数不一致')
    if not info['recovery_enabled']:
        confirmed_losses = {row['confirmed_lost_frame'] for row in rows
                            if row['confirmed_lost_frame'] is not None}
        if info['loss_episodes'] != len(confirmed_losses):
            raise ValueError('关闭分支丢失次数与逐帧确认丢失记录不一致')
    actual_transitions = [(e['frame_index'], e['from_state'], e['to_state']) for e in events if e['event_type'] == 'STATE_TRANSITION']
    if actual_transitions != transition_keys:
        raise ValueError('状态事件与记录不一致')
    accepts = [e for e in events if e['event_type'] == 'RECOVERY_ACCEPTED']
    if len(accepts) != info['program_accepts'] or sum(r['recovery_confirmed'] for r in rows) != len(accepts):
        raise ValueError('程序接受数与逐帧/事件不一致')
    for event in accepts:
        count = info['appearance_config']['confirmation_frames']
        interval = rows[event['frame_index'] - start - count + 1:event['frame_index'] - start + 1]
        if len(interval) != count:
            raise ValueError('接受前确认帧数不足')
        previous_box = None
        for expected_count, row in enumerate(interval, 1):
            candidates = [c for c in row['recovery_candidates'] if c['confirmation_count'] == expected_count]
            if len(candidates) != 1 or candidates[0]['track_id'] != event['active_native_track_id']:
                raise ValueError('接受混用了候选/计数')
            if previous_box is not None and box_iou(previous_box, candidates[0]['bbox_xyxy']) < info['appearance_config']['continuity_iou_min']:
                raise ValueError('接受期间空间连续性不足')
            previous_box = candidates[0]['bbox_xyxy']
        final = interval[-1]
        if not final['target_observed_this_frame'] or final['active_native_track_id'] != event['active_native_track_id'] or final['current_target_bbox_xyxy'] != event['candidate']['bbox_xyxy']:
            raise ValueError('绑定与当前位置不一致')
    cap = cv2.VideoCapture(str(output / 'status.mp4'))
    tiles, decoded = [], 0
    try:
        if not cap.isOpened():
            raise ValueError('状态视频打不开')
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if decoded >= len(rows) or frame.shape[:2] != (info['height'], info['width']):
                raise ValueError('输出视频帧数/尺寸不一致')
            index = start + decoded
            if index in selected_frames:
                if not cv2.imwrite(str(output / f'frame_{index:06d}.jpg'), frame):
                    raise ValueError('单帧预览保存失败')
                tile = np.full((340, 180, 3), 245, np.uint8)
                tile[:320] = cv2.resize(frame, (180, 320))
                cv2.putText(tile, f'f{index} {rows[decoded]["state"]}', (2, 334), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (20, 20, 20), 1)
                tiles.append(tile)
            decoded += 1
    finally:
        cap.release()
    if decoded != len(rows):
        raise ValueError('视频解码数与记录不同')
    if tiles:
        sheet = np.full((math.ceil(len(tiles)/4)*340, 720, 3), 245, np.uint8)
        for offset, tile in enumerate(tiles):
            y, x = offset//4*340, offset%4*180
            sheet[y:y+340, x:x+180] = tile
        if not cv2.imwrite(str(output / 'contact_sheet.jpg'), sheet):
            raise ValueError('状态预览拼图保存失败')
    result = {'record_checks_passed': True, 'output_decoded_frames': decoded,
              'original_output_files_preserved': len(preservation['before']), 'state_frame_counts': dict(counts),
              'program_accepts': len(accepts), 'reference_frozen': refs['frozen'],
              'disabled_matches_step1': disabled_rows is not None if not info['recovery_enabled'] else None,
              'notes': ['本核查验证证据/规则/视频一致性，物理身份依据单独评价。']}
    if info['recovery_enabled']:
        evaluation = evaluate_identity(info, rows, events, annotations)
        if annotations:
            evaluation['annotations'] = str(annotations)
            evaluation['annotations_sha256'] = sha256(annotations)
        write_json(output / 'evaluation.json', evaluation)
        result['identity_evaluation'] = evaluation
    write_json(output / 'review.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frames', type=int, nargs='*', default=[])
    parser.add_argument('--annotations', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(review(args.output, args.frames, args.annotations), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, IndexError) as exc:
        parser.exit(1, f'恢复核查失败: {exc}\n')
