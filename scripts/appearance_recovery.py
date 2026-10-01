"""冻结外观参考与受限场景的目标关联；外观分数不是物理身份概率。"""

from collections import Counter
import hashlib
import json
import math
from pathlib import Path

import cv2
import numpy as np

try:
    from .run_target_state import TargetState, box_iou
except ImportError:
    from run_target_state import TargetState, box_iou

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / 'configs/recovery.json'
ARRAY_KEYS = ('cap_hist', 'label_hist', 'texture', 'crop')


def load_config(path=DEFAULT_CONFIG_PATH):
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    expected = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding='utf-8'))
    if config.keys() != expected.keys():
        raise ValueError('恢复配置缺项或含未知项')
    integer_keys = ('reference_target_samples', 'reference_min_samples', 'reference_wait_frames',
                    'min_width', 'min_height', 'h_bins', 's_bins', 'min_color_pixels',
                    'texture_width', 'texture_height', 'confirmation_frames')
    for key in integer_keys:
        if type(config[key]) is not int or config[key] <= 0:
            raise ValueError(f'{key} 必须为正整数')
    if not config['reference_min_samples'] <= config['reference_target_samples'] <= config['reference_wait_frames']:
        raise ValueError('参考数量需满足 minimum <= target <= wait')
    for key in ('min_detection_score', 'min_color_fraction', 'cap_distance_max', 'label_distance_max',
                'score_min', 'competition_margin', 'continuity_iou_min'):
        if not math.isfinite(config[key]) or not 0 <= config[key] <= 1:
            raise ValueError(f'{key} 必须在 [0,1]')
    for key in ('min_saturation', 'min_value'):
        if type(config[key]) is not int or not 0 <= config[key] <= 255:
            raise ValueError(f'{key} 必须在 uint8 范围')
    if not -1 <= config['texture_ncc_min'] <= 1 or not math.isfinite(config['texture_ncc_min']):
        raise ValueError('纹理门槛必须在 [-1,1]')
    if not 0 < config['aspect_ratio_min'] <= config['aspect_ratio_max'] or not math.isfinite(config['aspect_ratio_max']):
        raise ValueError('形状比例门槛无效')
    if not math.isfinite(config['min_gray_std']) or config['min_gray_std'] < 0:
        raise ValueError('灰度标准差门槛无效')
    weights = config['score_weights']
    if len(weights) != 3 or any(not math.isfinite(x) or x < 0 for x in weights) or not math.isclose(sum(weights), 1):
        raise ValueError('三项排序权重需非负且和为 1')
    for key in ('cap_region', 'label_region'):
        x1, y1, x2, y2 = config[key]
        if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
            raise ValueError(f'{key} 必须为正面积归一化区域')
    if config['resize_interpolation'] != 'INTER_AREA' or config['pixel_rounding'] != 'floor lower, ceil upper':
        raise ValueError('本版本只实现 INTER_AREA 及 floor/ceil 取整规则')
    return config


def public_feature(feature):
    return {key: value for key, value in feature.items() if key not in ARRAY_KEYS}


def extract_feature(frame, detection, config):
    feature = {'valid': False, 'reasons': [], 'regions': {}}
    if frame is None or not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8:
        feature['reasons'].append('INVALID_IMAGE')
        return feature
    box = detection['bbox_xyxy']
    if len(box) != 4 or not all(math.isfinite(v) for v in box):
        feature['reasons'].append('INVALID_BOX')
        return feature
    x1, y1, x2, y2 = box
    height, width = frame.shape[:2]
    score = detection['detection_score']
    if not math.isfinite(score) or score < config['min_detection_score']:
        feature['reasons'].append('LOW_DETECTION_SCORE')
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
        feature['reasons'].append('BOX_NOT_FULLY_IN_IMAGE')
    if x2 - x1 < config['min_width'] or y2 - y1 < config['min_height']:
        feature['reasons'].append('CROP_TOO_SMALL')
    if feature['reasons']:
        return feature
    pixel_box = [math.floor(x1), math.floor(y1), math.ceil(x2), math.ceil(y2)]
    a, b, c, d = pixel_box
    crop = frame[b:d, a:c].copy()
    feature.update({'pixel_box_xyxy': pixel_box, 'aspect_ratio': (y2 - y1) / (x2 - x1), 'crop': crop})
    regions = {}
    for name in ('cap', 'label'):
        rx1, ry1, rx2, ry2 = config[name + '_region']
        ch, cw = crop.shape[:2]
        region_box = [math.floor(rx1 * cw), math.floor(ry1 * ch), math.ceil(rx2 * cw), math.ceil(ry2 * ch)]
        a, b, c, d = region_box
        region = crop[b:d, a:c]
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        mask = ((hsv[:, :, 1] >= config['min_saturation']) & (hsv[:, :, 2] >= config['min_value'])).astype(np.uint8) * 255
        count = int(np.count_nonzero(mask))
        fraction = count / mask.size
        feature['regions'][name] = {'pixel_box_xyxy': region_box, 'colored_pixels': count, 'colored_fraction': fraction}
        if count < config['min_color_pixels'] or fraction < config['min_color_fraction']:
            feature['reasons'].append(name.upper() + '_INSUFFICIENT_COLOR')
        else:
            hist = cv2.calcHist([hsv], [0, 1], mask, [config['h_bins'], config['s_bins']], [0, 180, 0, 256])
            feature[name + '_hist'] = (hist / hist.sum()).astype(np.float32)
        regions[name] = region
    gray = cv2.cvtColor(regions['label'], cv2.COLOR_BGR2GRAY)
    texture = cv2.resize(gray, (config['texture_width'], config['texture_height']), interpolation=cv2.INTER_AREA)
    feature['gray_std'] = float(texture.std())
    if feature['gray_std'] < config['min_gray_std']:
        feature['reasons'].append('DEGENERATE_TEXTURE')
    feature['texture'] = texture
    feature['valid'] = not feature['reasons']
    return feature


def compare_feature(feature, references, config):
    comparisons = []
    for reference in references:
        other = reference['feature']
        if not feature['valid'] or not other['valid']:
            continue
        cap = float(cv2.compareHist(feature['cap_hist'], other['cap_hist'], cv2.HISTCMP_BHATTACHARYYA))
        label = float(cv2.compareHist(feature['label_hist'], other['label_hist'], cv2.HISTCMP_BHATTACHARYYA))
        ncc = float(cv2.matchTemplate(feature['texture'], other['texture'], cv2.TM_CCOEFF_NORMED)[0, 0])
        if not all(math.isfinite(v) for v in (cap, label, ncc)):
            continue
        ratio = feature['aspect_ratio'] / other['aspect_ratio']
        wc, wl, wt = config['score_weights']
        score = wc * (1 - cap) + wl * (1 - label) + wt * ((ncc + 1) / 2)
        comparisons.append({'reference_frame_index': reference['frame_index'], 'cap_distance': cap,
                            'label_distance': label, 'texture_ncc': ncc, 'aspect_ratio_relative': ratio,
                            'score': score})
    if not comparisons:
        return None, []
    best = max(comparisons, key=lambda item: item['score'])
    # 先选最佳 S，再对同一参考检查全部门槛，不能拼接不同参考的有利分量。
    gates = {'cap_color': best['cap_distance'] <= config['cap_distance_max'],
             'label_color': best['label_distance'] <= config['label_distance_max'],
             'label_texture': best['texture_ncc'] >= config['texture_ncc_min'],
             'aspect_ratio': config['aspect_ratio_min'] <= best['aspect_ratio_relative'] <= config['aspect_ratio_max'],
             'score': best['score'] >= config['score_min']}
    return {**best, 'gates': gates, 'appearance_passed': all(gates.values())}, comparisons


class ReferenceBank:
    def __init__(self, init_frame, config):
        self.init_frame, self.config = init_frame, config
        self.samples, self.decisions = [], []
        self.frozen = False
        self.freeze_reason = None

    @property
    def ready(self):
        return len(self.samples) >= self.config['reference_min_samples']

    def freeze(self, reason):
        if not self.frozen:
            self.frozen, self.freeze_reason = True, reason

    def observe(self, row, detection, feature, acceptable):
        if self.frozen:
            return
        index = row['frame_index']
        qualified = detection is not None and feature['valid'] and acceptable
        self.decisions.append({'frame_index': index, 'qualified': qualified,
                               'quality': public_feature(feature) if feature else None})
        if detection is None:
            self.freeze('FIRST_TARGET_TRACK_MISSING')
        elif feature['valid'] and not acceptable:
            self.freeze('APPEARANCE_INCONSISTENT_DURING_COLLECTION')
        elif qualified:
            for key in ARRAY_KEYS:
                feature[key].setflags(write=False)
            self.samples.append({'frame_index': index, 'detection': dict(detection), 'feature': feature})
            if len(self.samples) >= self.config['reference_target_samples']:
                self.freeze('TARGET_SAMPLE_COUNT_REACHED')
        if index - self.init_frame + 1 >= self.config['reference_wait_frames']:
            self.freeze('REFERENCE_WINDOW_EXPIRED')

    def digest(self):
        digest = hashlib.sha256()
        for sample in self.samples:
            digest.update(json.dumps({'frame': sample['frame_index'], 'detection': sample['detection']}, sort_keys=True).encode())
            for key in ARRAY_KEYS:
                digest.update(sample['feature'][key].tobytes())
        return digest.hexdigest()

    def summary(self):
        return {'samples': len(self.samples), 'frozen': self.frozen, 'freeze_reason': self.freeze_reason,
                'status': 'READY' if self.ready else ('INSUFFICIENT_REFERENCE' if self.frozen else 'COLLECTING'),
                'sample_frames': [s['frame_index'] for s in self.samples], 'sha256': self.digest()}


def judge_candidates(detections, features, bank, config):
    judgments = []
    duplicates = Counter(d['track_id'] for d in detections if d['track_id'] is not None)
    for detection, feature in zip(detections, features):
        best, comparisons = compare_feature(feature, bank.samples, config) if feature['valid'] and bank.ready else (None, [])
        if not feature['valid']:
            decision, reasons = 'DEFERRED_QUALITY', list(feature['reasons'])
        elif not bank.ready:
            decision, reasons = 'DEFERRED_QUALITY', ['INSUFFICIENT_REFERENCE']
        elif best is None:
            decision, reasons = 'DEFERRED_QUALITY', ['NONFINITE_COMPARISON']
        elif not best['appearance_passed']:
            decision, reasons = 'REJECTED_APPEARANCE', [key for key, passed in best['gates'].items() if not passed]
        else:
            decision, reasons = 'ACCEPTABLE', []
        blockers = []
        if detection['track_id'] is None:
            blockers.append('UNASSIGNED_NATIVE_ID')
        elif duplicates[detection['track_id']] > 1:
            blockers.append('DUPLICATE_NATIVE_ID')
            if decision == 'ACCEPTABLE':
                decision, reasons = 'DEFERRED_QUALITY', ['DUPLICATE_NATIVE_ID']
        judgments.append({**detection, 'quality': public_feature(feature), 'best_reference': best,
                          'reference_comparisons': comparisons, 'decision': decision, 'reasons': reasons,
                          'confirmation_blockers': blockers, 'bound_to_target': False,
                          'verification_basis': 'appearance_heuristic', 'confirmation_count': 0,
                          'competition_margin': None})
    # 所有可计算且质量合格的候选均参与竞争，含某项外观门槛失败的高分候选。
    ranked = sorted([j for j in judgments if j['best_reference'] is not None],
                    key=lambda j: j['best_reference']['score'], reverse=True)
    winner = None
    if ranked:
        top = ranked[0]
        margin = top['best_reference']['score'] - ranked[1]['best_reference']['score'] if len(ranked) > 1 else None
        top['competition_margin'] = margin
        margin_ok = (margin is None or margin >= config['competition_margin'] or
                     math.isclose(margin, config['competition_margin'], rel_tol=0, abs_tol=1e-12))
        for judgment in ranked:
            if judgment['decision'] != 'ACCEPTABLE':
                continue
            if judgment is not top or not margin_ok:
                judgment['decision'] = 'AMBIGUOUS'
                judgment['reasons'] = ['COMPETITION_MARGIN_TOO_SMALL' if not margin_ok else 'NOT_HIGHEST_SCORE_CANDIDATE']
        if top['decision'] == 'ACCEPTABLE' and margin_ok and not top['confirmation_blockers']:
            winner = top
    return judgments, winner


class RecoveryState:
    def __init__(self, initial_row, manual_box, missing_frames, config, init_iou=0.5, target_uid='T1'):
        self.initialization = TargetState(initial_row, manual_box, missing_frames, init_iou).initialization
        self.config, self.threshold, self.target_uid = config, missing_frames, target_uid
        self.initial_id = self.initialization['initial_native_track_id']
        self.active_id = self.initial_id
        self.class_id = self.initialization['class_id']
        self.bank = ReferenceBank(initial_row['frame_index'], config)
        self.next_frame = initial_row['frame_index']
        self.state = None
        self.missing_count = 0
        self.first_missing_frame = self.confirmed_lost_frame = None
        self.lost = False
        self.last_observation = None
        self.streak_id = self.streak_box = self.streak_start = None
        self.streak_count = 0
        self.loss_episodes = self.attempts = self.accepts = 0

    def step(self, row, frame):
        if row['frame_index'] != self.next_frame:
            raise ValueError('恢复模块帧索引必须连续')
        self.next_frame += 1
        previous = self.state
        detections = [d for d in row['detections'] if d['class_id'] == self.class_id]
        features = [extract_feature(frame, d, self.config) for d in detections]
        native = [(d, f) for d, f in zip(detections, features) if d['track_id'] == self.active_id and self.active_id is not None]
        observation, active_evidence = None, None
        judgments, events = [], []
        accepted_now = False
        if not self.lost:
            reliable = False
            detection, feature = native[0] if len(native) == 1 else (None, None)
            if feature and feature['valid']:
                if self.bank.ready:
                    best, comparisons = compare_feature(feature, self.bank.samples, self.config)
                    active_evidence = {'quality': public_feature(feature), 'best_reference': best, 'reference_comparisons': comparisons}
                    reliable = best is not None and best['appearance_passed']
                elif not self.bank.frozen:
                    reliable = True  # 初始人工选择的少量合格观察，用于因果建库。
                    active_evidence = {'quality': public_feature(feature), 'basis': 'manual_initialization_bootstrap'}
            elif feature:
                active_evidence = {'quality': public_feature(feature), 'best_reference': None}
            self.bank.observe(row, detection, feature, reliable)
            if reliable:
                observation = self.make_observation(row, detection)
                self.missing_count = 0
                self.first_missing_frame = None
                self.state = 'TRACKING'
            else:
                self.missing_count += 1
                if self.first_missing_frame is None:
                    self.first_missing_frame = row['frame_index']
                self.state = 'TRACKING'
                if self.missing_count >= self.threshold:
                    self.bank.freeze('CONFIRMED_LOSS_DURING_COLLECTION')
                    self.lost = True
                    self.confirmed_lost_frame = row['frame_index']
                    self.loss_episodes += 1
                    self.active_id = None
        else:
            self.missing_count += 1
        if self.lost:
            judgments, winner = judge_candidates(detections, features, self.bank, self.config)
            self.state = 'RECOVERY_CANDIDATE' if detections else 'LOST'
            count, reset_reason = 0, None
            if winner:
                native_id = winner['track_id']
                continuity = self.streak_box is not None and box_iou(self.streak_box, winner['bbox_xyxy']) >= self.config['continuity_iou_min']
                if native_id == self.streak_id and continuity:
                    count = self.streak_count + 1
                else:
                    reset_reason = 'ID_CHANGE_OR_SPATIAL_JUMP' if self.streak_count else None
                    count = 1
                    self.streak_start = row['frame_index']
                    self.attempts += 1
                    events.append({'event_type': 'RECOVERY_ATTEMPT_STARTED', 'candidate_native_id': native_id})
                self.streak_id, self.streak_box = native_id, winner['bbox_xyxy']
                winner['confirmation_count'] = count
                if count >= self.config['confirmation_frames']:
                    winner['bound_to_target'] = True
                    self.active_id = native_id
                    self.accepts += 1
                    accepted_now = True
                    observation = self.make_observation(row, winner)
                    events.append({'event_type': 'RECOVERY_ACCEPTED', 'candidate': winner,
                                   'confirmation_start_frame': self.streak_start, 'loss_episode_id': self.loss_episodes,
                                   'first_missing_frame': self.first_missing_frame, 'confirmed_lost_frame': self.confirmed_lost_frame,
                                   'initial_native_track_id': self.initial_id, 'active_native_track_id': native_id,
                                   'verification_basis': 'appearance_heuristic', 'physical_identity_evaluation': 'NOT_EVALUATED'})
                    self.lost = False
                    self.missing_count = 0
                    self.first_missing_frame = self.confirmed_lost_frame = None
                    self.state = 'TRACKING'
            else:
                reset_reason = 'CANDIDATE_ABSENT_OR_INELIGIBLE' if self.streak_count else None
                self.streak_id = self.streak_box = self.streak_start = None
            if reset_reason:
                events.append({'event_type': 'RECOVERY_CONFIRMATION_RESET', 'reason': reset_reason, 'previous_count': self.streak_count})
            self.streak_count = count if not accepted_now else 0
            if accepted_now:
                self.streak_id = self.streak_box = self.streak_start = None
        if observation is not None:
            self.last_observation = observation
        result = {**row, 'target_uid': self.target_uid, 'initial_native_track_id': self.initial_id,
                  'active_native_track_id': self.active_id, 'state': self.state,
                  'target_observed_this_frame': observation is not None, 'position_known': observation is not None,
                  'current_target_bbox_xyxy': observation['bbox_xyxy'] if observation else None,
                  'last_observed_target': self.last_observation, 'active_track_evidence': active_evidence,
                  'pending_loss': not self.lost and self.missing_count > 0,
                  'consecutive_missing_frames': self.missing_count, 'first_missing_frame': self.first_missing_frame,
                  'confirmed_lost_frame': self.confirmed_lost_frame, 'loss_latched': self.lost,
                  'reference_bank': self.bank.summary(), 'recovery_candidates': judgments,
                  'recovery_confirmed': accepted_now, 'recovery_confirmed_meaning': 'program accepted by appearance rules on this frame only',
                  'verification_basis': 'appearance_heuristic' if self.accepts else 'manual_initialization',
                  'physical_identity_evaluation': 'NOT_EVALUATED', 'loss_episode_id': self.loss_episodes}
        if previous != self.state:
            events.append({'event_type': 'STATE_TRANSITION', 'from_state': previous, 'to_state': self.state})
        common = {key: result[key] for key in ('frame_index', 'timestamp_seconds', 'source_pos_msec_seconds', 'target_uid')}
        return result, [{**common, **event} for event in events]

    def make_observation(self, row, detection):
        return {'frame_index': row['frame_index'], 'bbox_xyxy': list(detection['bbox_xyxy']),
                'native_track_id': detection['track_id'], 'detection_index': detection['detection_index'],
                'detection_score': detection['detection_score']}
