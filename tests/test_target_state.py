"""状态边界与错误绑定的回归检查；合成记录不作模型效果证据。"""

import copy
import unittest

from scripts.run_target_state import TargetState


BOX = [10, 20, 50, 100]


def row(index, ids=(), unassigned=False):
    detections, tracks = [], []
    for d_index, track_id in enumerate(ids):
        detection = {'detection_index': d_index, 'bbox_xyxy': list(BOX), 'class_id': 39,
                     'class_name': 'bottle', 'detection_score': 0.9, 'track_id': track_id}
        detections.append(detection)
        tracks.append({key: detection[key] for key in ('detection_index', 'bbox_xyxy', 'class_id', 'class_name', 'detection_score', 'track_id')})
    if unassigned:
        detections.append({'detection_index': len(detections), 'bbox_xyxy': list(BOX), 'class_id': 39,
                           'class_name': 'bottle', 'detection_score': 0.15, 'track_id': None})
    return {'frame_index': index, 'timestamp_seconds': index / 30, 'source_pos_msec_seconds': index / 30,
            'detections': detections, 'tracks': tracks}


class TargetStateTests(unittest.TestCase):
    def make(self, threshold=2, native_id=42):
        first = row(100, [native_id])
        machine = TargetState(first, BOX, threshold)
        machine.step(first)
        return machine

    def test_missing_threshold_and_unknown_position_during_grace(self):
        machine = self.make(3)
        for index in (101, 102):
            result, event = machine.step(row(index))
            self.assertEqual(result['state'], 'TRACKING')
            self.assertTrue(result['pending_loss'])
            self.assertIsNone(result['current_target_bbox_xyxy'])
            self.assertFalse(result['position_known'])
            self.assertEqual(result['last_observed_target']['frame_index'], 100)
            self.assertIsNone(event)
        result, event = machine.step(row(103))
        self.assertEqual(result['state'], 'LOST')
        self.assertEqual(result['first_missing_frame'], 101)
        self.assertEqual(result['confirmed_lost_frame'], 103)
        self.assertEqual(event['from_state'], 'TRACKING')
        self.assertEqual(result['consecutive_missing_frames'], 3)

    def test_unrelated_track_does_not_reset_missing(self):
        machine = self.make()
        machine.step(row(101, [98]))
        result, _ = machine.step(row(102, [98]))
        self.assertEqual(result['state'], 'RECOVERY_CANDIDATE')
        self.assertTrue(result['loss_latched'])
        self.assertEqual(result['recovery_candidates'][0]['track_id'], 98)
        self.assertIsNone(result['current_target_bbox_xyxy'])

    def test_native_short_gap_resets_before_confirmed_loss(self):
        machine = self.make()
        machine.step(row(101))
        result, _ = machine.step(row(102, [42]))
        self.assertEqual(result['state'], 'TRACKING')
        self.assertEqual(result['consecutive_missing_frames'], 0)
        self.assertTrue(result['position_known'])
        self.assertFalse(result['loss_latched'])

    def test_same_id_is_only_candidate_after_loss_and_candidate_can_disappear(self):
        machine = self.make(1)
        machine.step(row(101))
        for index, data in ((102, row(102, [42])), (103, row(103, unassigned=True))):
            result, _ = machine.step(data)
            self.assertEqual(result['state'], 'RECOVERY_CANDIDATE')
            self.assertFalse(result['recovery_confirmed'])
            self.assertFalse(result['recovery_candidates'][0]['bound_to_target'])
            self.assertEqual(result['recovery_candidates'][0]['identity_check']['status'], 'UNVERIFIED')
            self.assertIsNone(result['current_target_bbox_xyxy'])
            self.assertEqual(result['last_observed_target']['frame_index'], 100)
        result, event = machine.step(row(104))
        self.assertEqual(result['state'], 'LOST')
        self.assertEqual(event['from_state'], 'RECOVERY_CANDIDATE')

    def test_multiple_candidates_remain_unbound(self):
        machine = self.make(1)
        machine.step(row(101))
        result, _ = machine.step(row(102, [42, 98]))
        self.assertEqual(len(result['recovery_candidates']), 2)
        self.assertTrue(all(not c['bound_to_target'] for c in result['recovery_candidates']))
        self.assertEqual(result['initial_native_track_id'], 42)

    def test_initialization_rejects_ambiguity_no_match_and_unassigned(self):
        for data, box in ((row(0, [42, 98]), BOX), (row(0, [42]), [200, 200, 300, 300]),
                          (row(0, unassigned=True), BOX)):
            with self.assertRaises(ValueError):
                TargetState(data, box, 2)

    def test_arbitrary_id_initialization_and_inputs_unchanged(self):
        first = row(71, [9876])
        before = copy.deepcopy(first)
        machine = TargetState(first, BOX, 1)
        result, _ = machine.step(first)
        self.assertEqual(result['initial_native_track_id'], 9876)
        self.assertEqual(first, before)
        with self.assertRaises(ValueError):
            machine.step(row(73))

    def test_invalid_threshold_and_box(self):
        for threshold, box in ((0, BOX), (1, [10, 20, float('nan'), 100]), (1, [10, 20, 5, 100])):
            with self.assertRaises(ValueError):
                TargetState(row(0, [42]), box, threshold)


if __name__ == '__main__':
    unittest.main()
