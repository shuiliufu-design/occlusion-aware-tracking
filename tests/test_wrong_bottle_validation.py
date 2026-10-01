"""负例评价须有真实合格候选，不能靠零检测/零接受得出通过。"""

import copy
import unittest

from scripts.validate_wrong_bottle import summarize_negative

BOX = [10, 20, 50, 100]
ANNOTATION = {'target_uid': 'T1', 'original_target_removed': True, 'original_target_reappears': False,
              'operator_confirmation': '已换成另一只瓶子', 'confirmation_basis': '拍摄者说明及原始画面',
              'negative_interval': {'start_frame': 2, 'end_frame_exclusive': 4,
                                    'identity': 'OTHER_BOTTLE', 'bbox_xyxy': BOX, 'match_iou_min': 0.5}}


def records(detected=True, valid=True):
    rows = []
    for index in range(2, 4):
        detection = {'detection_index': 0, 'bbox_xyxy': BOX, 'detection_score': 0.9, 'track_id': 7}
        candidate = {**detection, 'quality': {'valid': valid},
                     'best_reference': {'gates': {'label_color': False}, 'appearance_passed': False} if valid else None,
                     'decision': 'REJECTED_APPEARANCE' if valid else 'DEFERRED_QUALITY',
                     'confirmation_count': 0, 'bound_to_target': False}
        rows.append({'frame_index': index, 'timestamp_seconds': index / 30, 'source_pos_msec_seconds': index / 30,
                     'position_known': False, 'current_target_bbox_xyxy': None, 'target_observed_this_frame': False,
                     'detections': [detection] if detected else [], 'recovery_candidates': [candidate] if detected else []})
    return rows


class WrongBottleValidationTests(unittest.TestCase):
    def test_no_detection_does_not_prove_rejection(self):
        result = summarize_negative(records(detected=False), [], ANNOTATION)
        self.assertEqual(result['verdict'], 'UNVERIFIED')
        self.assertEqual(result['qualified_candidate_frames'], 0)

    def test_low_quality_is_deferred_not_rejected(self):
        result = summarize_negative(records(valid=False), [], ANNOTATION)
        self.assertEqual(result['verdict'], 'UNVERIFIED')
        self.assertEqual(result['candidate_decisions'], {'DEFERRED_QUALITY': 2})

    def test_qualified_rejected_candidates_pass(self):
        result = summarize_negative(records(), [], ANNOTATION)
        self.assertEqual(result['verdict'], 'PASS')
        self.assertEqual(result['qualified_candidate_frames'], 2)

    def test_high_quality_acceptable_without_binding_is_not_rejection(self):
        rows = records()
        rows[0]['recovery_candidates'][0]['decision'] = 'ACCEPTABLE'
        self.assertEqual(summarize_negative(rows, [], ANNOTATION)['verdict'], 'UNVERIFIED')

    def test_incorrect_position_or_acceptance_fails(self):
        rows = records()
        rows[0]['current_target_bbox_xyxy'] = BOX
        self.assertEqual(summarize_negative(rows, [], ANNOTATION)['verdict'], 'FAIL')
        events = [{'event_type': 'RECOVERY_ACCEPTED', 'frame_index': 3}]
        self.assertEqual(summarize_negative(records(), events, ANNOTATION)['verdict'], 'FAIL')

    def test_unmatched_object_or_confirmation_is_not_pass(self):
        rows = records()
        for row in rows:
            row['detections'][0]['bbox_xyxy'] = [100, 200, 150, 300]
        self.assertEqual(summarize_negative(rows, [], ANNOTATION)['verdict'], 'UNVERIFIED')
        rows = records()
        rows[0]['recovery_candidates'][0]['confirmation_count'] = 1
        self.assertEqual(summarize_negative(rows, [], ANNOTATION)['verdict'], 'FAIL')

    def test_incomplete_interval_or_missing_physical_basis_fails(self):
        with self.assertRaises(ValueError):
            summarize_negative(records()[:1], [], ANNOTATION)
        annotation = copy.deepcopy(ANNOTATION)
        annotation['original_target_removed'] = False
        with self.assertRaises(ValueError):
            summarize_negative(records(), [], annotation)

    def test_rejection_text_cannot_override_passed_appearance(self):
        rows = records()
        rows[0]['recovery_candidates'][0]['best_reference'] = {
            'gates': {'label_color': True}, 'appearance_passed': True}
        with self.assertRaises(ValueError):
            summarize_negative(rows, [], ANNOTATION)


if __name__ == '__main__':
    unittest.main()
