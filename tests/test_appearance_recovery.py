"""用可控图像/候选检查身份门控与状态边界；不计为真实瓶子拒绝率。"""

import copy
import unittest
from unittest.mock import patch

import numpy as np

from scripts.appearance_recovery import (RecoveryState, compare_feature, extract_feature,
                                        judge_candidates, load_config)

BOX = [30, 20, 90, 200]


def image(wrong=False, second=False):
    frame = np.full((240, 240, 3), 170, np.uint8)
    crop = np.full((180, 60, 3), 180, np.uint8)
    crop[:35] = (220, 40, 30) if wrong else (25, 35, 220)
    for y in range(75, 150):
        crop[y] = ((230, 70, 35) if y % 12 < 6 else (160, 30, 20)) if wrong else ((30, 150, 50) if y % 12 < 6 else (40, 40, 210))
    frame[20:200, 30:90] = crop
    if second:
        frame[20:200, 130:190] = crop
    return frame


def row(index, ids=(17,), score=0.95, second=False, unassigned=False, jump=False):
    detections, tracks = [], []
    boxes = [BOX, [130, 20, 190, 200]] if second else ([130, 20, 190, 200] if jump else BOX,)
    for offset, native_id in enumerate(ids):
        detection = {'detection_index': offset, 'bbox_xyxy': list(boxes[min(offset, len(boxes) - 1)]),
                     'class_id': 39, 'class_name': 'bottle', 'detection_score': score,
                     'track_id': None if unassigned else native_id}
        detections.append(detection)
        if detection['track_id'] is not None:
            tracks.append(dict(detection))
    return {'frame_index': index, 'timestamp_seconds': index / 30,
            'source_pos_msec_seconds': index / 30, 'detections': detections, 'tracks': tracks}


class AppearanceRecoveryTests(unittest.TestCase):
    def test_reference_window_expiry_prevents_later_fill(self):
        config = load_config()
        config['reference_wait_frames'] = 10
        machine = RecoveryState(row(0), BOX, 100, config)
        for index in range(10):
            machine.step(row(index, score=0.95 if index < 4 else 0.49), image())
        self.assertEqual(machine.bank.summary()['status'], 'INSUFFICIENT_REFERENCE')
        self.assertEqual(machine.bank.freeze_reason, 'REFERENCE_WINDOW_EXPIRED')
        digest = machine.bank.digest()
        for index in range(10, 20):
            machine.step(row(index), image())
        self.assertEqual(machine.bank.digest(), digest)

    def test_inclusive_color_texture_and_shape_gate_boundaries(self):
        machine = self.lost()
        feature = extract_feature(image(), row(7)['detections'][0], machine.config)
        for cap, label, ncc, ratio in ((0.55, 0, 1, 0.65), (0, 0.35, 1, 1.5), (0, 0, 0.55, 1)):
            feature['aspect_ratio'] = machine.bank.samples[0]['feature']['aspect_ratio'] * ratio
            with patch('scripts.appearance_recovery.cv2.compareHist', side_effect=[cap, label]), patch('scripts.appearance_recovery.cv2.matchTemplate', return_value=np.array([[ncc]])):
                best, _ = compare_feature(feature, machine.bank.samples[:1], machine.config)
            self.assertTrue(best['appearance_passed'])
        with patch('scripts.appearance_recovery.cv2.compareHist', side_effect=[0, 0]), patch('scripts.appearance_recovery.cv2.matchTemplate', return_value=np.array([[0.5499]])):
            best, _ = compare_feature(feature, machine.bank.samples[:1], machine.config)
        self.assertFalse(best['gates']['label_texture'])

    def test_reference_skips_low_quality_then_collects_earliest_qualified_frames(self):
        config = load_config()
        machine = RecoveryState(row(0, score=0.49), BOX, 2, config)
        machine.step(row(0, score=0.49), image())
        self.assertFalse(machine.bank.frozen)
        self.assertEqual(len(machine.bank.samples), 0)
        for index in range(1, 11):
            machine.step(row(index), image())
        self.assertEqual(machine.bank.summary()['sample_frames'], list(range(1, 11)))
        self.assertTrue(machine.bank.frozen)

    def make(self, target_samples=5):
        config = load_config()
        config['reference_target_samples'] = target_samples
        machine = RecoveryState(row(0), BOX, 2, config)
        for index in range(5):
            machine.step(row(index), image())
        return machine

    def lost(self):
        machine = self.make()
        machine.step(row(5, ()), image())
        result, _ = machine.step(row(6, ()), image())
        self.assertEqual(result['state'], 'LOST')
        return machine

    def test_reference_freezes_on_absence_and_never_uses_future(self):
        machine = self.make(10)
        digest = machine.bank.digest()
        machine.step(row(5, ()), image())
        self.assertTrue(machine.bank.frozen)
        self.assertEqual(machine.bank.summary()['sample_frames'], list(range(5)))
        for index in range(6, 20):
            machine.step(row(index, (29,)), image())
        self.assertEqual(machine.bank.digest(), digest)

    def test_five_frames_required_no_hidden_positions_and_native_ids_preserved(self):
        machine = self.lost()
        digest = machine.bank.digest()
        for index in range(7, 12):
            source = row(index, (29,))
            before = copy.deepcopy(source)
            result, events = machine.step(source, image())
            self.assertEqual(source, before)
            if index < 11:
                self.assertEqual(result['state'], 'RECOVERY_CANDIDATE')
                self.assertIsNone(result['current_target_bbox_xyxy'])
            else:
                self.assertTrue(result['recovery_confirmed'])
                self.assertEqual(result['target_uid'], 'T1')
                self.assertEqual(result['initial_native_track_id'], 17)
                self.assertEqual(result['active_native_track_id'], 29)
                accepted = [event for event in events if event['event_type'] == 'RECOVERY_ACCEPTED']
                self.assertEqual(accepted[0]['candidate']['confirmation_count'], 5)
        self.assertEqual(machine.bank.digest(), digest)

    def test_high_score_same_initial_id_wrong_appearance_cannot_restore(self):
        machine = self.lost()
        for index in range(7, 14):
            result, _ = machine.step(row(index, score=1.0), image(wrong=True))
            self.assertEqual(result['recovery_candidates'][0]['decision'], 'REJECTED_APPEARANCE')
            self.assertIsNone(result['current_target_bbox_xyxy'])
        self.assertEqual(machine.accepts, 0)

    def test_partial_low_score_and_unassigned_do_not_accumulate(self):
        machine = self.lost()
        for index in range(7, 11):
            result, _ = machine.step(row(index, (29,), unassigned=True), image())
            candidate = result['recovery_candidates'][0]
            self.assertEqual(candidate['decision'], 'ACCEPTABLE')
            self.assertEqual(candidate['confirmation_count'], 0)
        result, _ = machine.step(row(11, (29,), score=0.49), image())
        self.assertEqual(result['recovery_candidates'][0]['decision'], 'DEFERRED_QUALITY')
        self.assertEqual(machine.accepts, 0)

    def test_candidate_switch_disappearance_and_spatial_jump_reset(self):
        machine = self.lost()
        machine.step(row(7, (29,)), image())
        machine.step(row(8, (29,)), image())
        result, _ = machine.step(row(9, (30,)), image())
        self.assertEqual(result['recovery_candidates'][0]['confirmation_count'], 1)
        machine.step(row(10, ()), image())
        result, _ = machine.step(row(11, (30,)), image())
        self.assertEqual(result['recovery_candidates'][0]['confirmation_count'], 1)
        result, _ = machine.step(row(12, (30,), jump=True), image(second=True))
        self.assertEqual(result['recovery_candidates'][0]['confirmation_count'], 1)
        self.assertEqual(machine.accepts, 0)

    def test_competition_tie_and_duplicate_id_defer(self):
        for ids in ((29, 30), (29, 29)):
            machine = self.lost()
            for index in range(7, 14):
                result, _ = machine.step(row(index, ids, second=True), image(second=True))
                self.assertTrue(all(c['decision'] in ('AMBIGUOUS', 'DEFERRED_QUALITY') for c in result['recovery_candidates']))
            self.assertEqual(machine.accepts, 0)

    def test_gate_failed_competitor_is_not_removed_and_top_failure_has_no_fallback(self):
        machine = self.lost()
        data = row(7, (29, 30), second=True)['detections']
        features = [extract_feature(image(second=True), d, machine.config) for d in data]
        def evidence(score, passed):
            return {'score': score, 'appearance_passed': passed, 'gates': {'cap_color': passed}}, []
        with patch('scripts.appearance_recovery.compare_feature', side_effect=[evidence(0.85, True), evidence(0.83, False)]):
            judgments, winner = judge_candidates(data, features, machine.bank, machine.config)
            self.assertIsNone(winner)
            self.assertEqual(judgments[0]['decision'], 'AMBIGUOUS')
        with patch('scripts.appearance_recovery.compare_feature', side_effect=[evidence(0.9, False), evidence(0.85, True)]):
            _, winner = judge_candidates(data, features, machine.bank, machine.config)
            self.assertIsNone(winner)
        with patch('scripts.appearance_recovery.compare_feature', side_effect=[evidence(0.9, True), evidence(0.8, True)]):
            _, winner = judge_candidates(data, features, machine.bank, machine.config)
            self.assertEqual(winner['track_id'], 29)  # 差值恰为 0.10，允许数值舍入误差。

    def test_best_reference_must_pass_all_gates_no_reference_cherry_picking(self):
        machine = self.lost()
        feature = extract_feature(image(), row(7)['detections'][0], machine.config)
        with patch('scripts.appearance_recovery.cv2.compareHist', side_effect=[0.6, 0.0, 0.3, 0.2]), patch('scripts.appearance_recovery.cv2.matchTemplate', side_effect=[np.array([[1.0]]), np.array([[0.6]])]):
            best, comparisons = compare_feature(feature, machine.bank.samples[:2], machine.config)
        self.assertEqual(best['reference_frame_index'], 0)
        self.assertFalse(best['appearance_passed'])
        self.assertEqual(len(comparisons), 2)

    def test_invalid_image_constant_texture_colorless_region_and_insufficient_reference(self):
        config = load_config()
        for frame in (None, np.zeros((240, 240, 3), np.uint8), np.full((240, 240, 3), (20, 30, 220), np.uint8)):
            feature = extract_feature(frame, row(0)['detections'][0], config)
            self.assertFalse(feature['valid'])
        machine = RecoveryState(row(0), BOX, 1, config)
        machine.step(row(0), image())
        machine.step(row(1, ()), image())
        for index in range(2, 10):
            result, _ = machine.step(row(index, (29,)), image())
            self.assertEqual(result['reference_bank']['status'], 'INSUFFICIENT_REFERENCE')
            self.assertIsNone(result['current_target_bbox_xyxy'])
        self.assertEqual(machine.accepts, 0)

    def test_after_recovery_quality_failure_loses_again_and_new_confirmation_restarts(self):
        machine = self.lost()
        for index in range(7, 12):
            machine.step(row(index, (29,)), image())
        result, _ = machine.step(row(12, (29,), score=0.49), image())
        self.assertIsNone(result['current_target_bbox_xyxy'])
        machine.step(row(13, ()), image())
        for index in range(14, 19):
            result, events = machine.step(row(index, (29,)), image())
        accepted = [e for e in events if e['event_type'] == 'RECOVERY_ACCEPTED'][0]
        self.assertEqual(accepted['confirmation_start_frame'], 14)
        self.assertEqual(machine.accepts, 2)
        self.assertEqual(machine.attempts, 2)

    def test_visually_identical_replacement_is_known_failure_boundary(self):
        machine = self.lost()
        for index in range(7, 12):
            machine.step(row(index, (999,)), image())
        self.assertEqual(machine.accepts, 1)  # 同图像代表另一实体时，这些特征无法分辨。

    def test_quality_threshold_and_aspect_ratio(self):
        config = load_config()
        detection = row(0, score=0.5)['detections'][0]
        feature = extract_feature(image(), detection, config)
        self.assertTrue(feature['valid'])
        detection['bbox_xyxy'] = [-1, 20, 90, 200]
        self.assertIn('BOX_NOT_FULLY_IN_IMAGE', extract_feature(image(), detection, config)['reasons'])
        machine = self.lost()
        feature['aspect_ratio'] *= 2
        best, _ = compare_feature(feature, machine.bank.samples, config)
        self.assertFalse(best['gates']['aspect_ratio'])


if __name__ == '__main__':
    unittest.main()
