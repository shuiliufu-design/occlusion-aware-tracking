"""评价分母、身份不确定性、覆盖及历史来源边界；不测试或改变恢复核心。"""

from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.evaluate_offline import coverage, evaluate, evaluate_episode, interval_indices
from scripts.evaluation_sources import check_counts, verify_code


BOX = [10, 10, 30, 70]


def detection():
    return {'detection_index': 0, 'bbox_xyxy': BOX, 'class_name': 'bottle', 'track_id': 8}


def row(index, known=False, candidates=None, detected=True):
    return {'frame_index': index, 'source_pos_msec_seconds': index * .051,
            'state': 'TRACKING' if known else 'RECOVERY_CANDIDATE', 'position_known': known,
            'current_target_bbox_xyxy': BOX if known else None,
            'detections': [detection()] if detected else [], 'recovery_candidates': candidates or [],
            'recovery_confirmed': False, 'confirmed_lost_frame': 0}


def candidate(decision='REJECTED_APPEARANCE', quality=True):
    return {**detection(), 'decision': decision, 'bound_to_target': False,
            'quality': {'valid': quality},
            'best_reference': {'appearance_passed': False, 'gates': {'label_color': False}} if quality else None}


def accept(index):
    return {'frame_index': index, 'event_type': 'RECOVERY_ACCEPTED', 'candidate': detection(), 'active_native_track_id': 8}


class EventEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.info = {'recovery_enabled': True, 'nominal_fps': 20}
        self.rows = [row(i) for i in range(4)]
        self.case = {'episode_id': 'physical_event_1', 'event_type': 'ORIGINAL_RETURN', 'expected_return': True,
                     'physical_identity': 'T1', 'evaluation_interval': {'start_frame': 0, 'end_frame_exclusive': 4},
                     'interval_basis': '人工完整评价窗', 'recognizable_reappearance_frame': 1,
                     'target_absent_intervals': [], 'visible_controls': []}
        self.annotation = {'target_uid': 'T1', 'confirmation_basis': '拍摄者及画面', 'operator_confirmation': '未替换',
                           'timing_annotator': '人工', 'reappearance_criterion': '标签可见',
                           'keyframes': [{'frame_index': 2, 'identity': 'T1', 'bbox_xyxy': BOX}]}

    def result(self, events=None):
        return evaluate_episode(self.info, self.rows, events or [], self.case, self.annotation)

    def test_return_correct_and_both_time_scales(self):
        result = self.result([accept(2)])
        self.assertEqual(result['return_evaluation']['correctly_recovered_events'], 1)
        self.assertEqual(result['return_evaluation']['unrecovered_events'], 0)
        delay = result['return_evaluation']['latencies'][0]
        self.assertEqual(delay['latency_frames'], 1)
        self.assertAlmostEqual(delay['latency_seconds_frame_fps'], .05)
        self.assertAlmostEqual(delay['latency_seconds_source_time'], .051)

    def test_positive_disabled_is_one_miss_and_no_latency(self):
        self.info['recovery_enabled'] = False
        result = self.result()
        self.assertEqual(result['return_evaluation']['status'], 'FAIL')
        self.assertEqual(result['return_evaluation']['expected_return_opportunities'], 1)
        self.assertEqual(result['return_evaluation']['unrecovered_events'], 1)
        self.assertIsNone(result['return_evaluation']['latencies'])

    def test_algorithm_losses_cannot_create_opportunities(self):
        self.info['loss_episodes'] = 999
        result = self.result()
        self.assertEqual(result['return_evaluation']['expected_return_opportunities'], 1)
        self.assertEqual(result['return_evaluation']['unrecovered_events'], 1)

    def make_negative(self):
        self.case.update(expected_return=False, recognizable_reappearance_frame=None,
                         event_type='DIFFERENT_BOTTLE_REPLACEMENT',
                         target_absent_intervals=[{'start_frame': 1, 'end_frame_exclusive': 4}])
        self.annotation['negative_interval'] = {'start_frame': 1, 'end_frame_exclusive': 4,
                                               'bbox_xyxy': BOX, 'match_iou_min': .5, 'identity': 'OTHER_BOTTLE'}
        for r in self.rows:
            r['recovery_candidates'] = [candidate()]

    def test_no_return_is_not_a_failed_recovery(self):
        self.make_negative()
        result = self.result()
        self.assertEqual(result['return_evaluation']['status'], 'NOT_APPLICABLE')
        self.assertEqual(result['return_evaluation']['expected_return_opportunities'], 0)
        self.assertEqual(result['return_evaluation']['unrecovered_events'], 0)
        self.assertIsNone(result['return_evaluation']['success_rate'])
        self.assertIsNone(result['return_evaluation']['latencies'])
        self.assertEqual(result['wrong_candidate_appearance_rejection']['status'], 'PASS')

    def test_negative_frames_are_one_event_and_whole_candidates_separate(self):
        self.make_negative()
        rejection = self.result()['wrong_candidate_appearance_rejection']
        self.assertEqual(rejection['replacement_events'], 1)
        self.assertEqual(rejection['coverage']['appearance_rejected_observations'], 3)
        self.assertEqual(coverage(self.rows, True)['candidate_observations'], 4)

    def test_disabled_never_earns_appearance_pass(self):
        self.make_negative()
        self.info['recovery_enabled'] = False
        result = self.result()
        self.assertEqual(result['no_wrong_binding']['status'], 'PASS')
        self.assertEqual(result['wrong_candidate_appearance_rejection']['status'], 'NOT_APPLICABLE')
        self.assertIsNone(result['wrong_candidate_appearance_rejection']['coverage']['appearance_rejected_observations'])
        self.assertIsNone(result['wrong_candidate_appearance_rejection']['coverage']['qualified_candidate_observations'])

    def test_absent_target_accept_is_wrong_even_without_accept_keyframe(self):
        self.make_negative()
        self.annotation['keyframes'] = []
        result = self.result([accept(2)])
        self.assertEqual(result['acceptance_evaluation']['incorrect_accepts'], 1)
        self.assertEqual(result['wrong_candidate_appearance_rejection']['status'], 'FAIL')
        self.assertEqual(result['return_evaluation']['unrecovered_events'], 0)

    def test_uncertain_and_unlabelled_accepts_are_not_correct_or_known_misses(self):
        for labels in [[], [{'frame_index': 2, 'identity': 'UNCERTAIN', 'bbox_xyxy': BOX}]]:
            with self.subTest(labels=labels):
                self.annotation['keyframes'] = labels
                result = self.result([accept(2)])
                self.assertEqual(result['acceptance_evaluation']['unevaluated_accepts'], 1)
                self.assertEqual(result['return_evaluation']['status'], 'UNEVALUATED')
                self.assertEqual(result['return_evaluation']['unevaluated_return_events'], 1)
                self.assertEqual(result['return_evaluation']['unrecovered_events'], 0)
                self.assertIsNone(result['return_evaluation']['success_rate'])

    def test_wrong_identity_and_bad_localization_are_incorrect(self):
        for identity, box in [('OTHER_BOTTLE', BOX), ('T1', [100, 100, 120, 160])]:
            with self.subTest(identity=identity):
                self.annotation['keyframes'] = [{'frame_index': 2, 'identity': identity, 'bbox_xyxy': box}]
                result = self.result([accept(2)])
                self.assertEqual(result['acceptance_evaluation']['incorrect_accepts'], 1)
                self.assertEqual(result['return_evaluation']['status'], 'FAIL')

    def test_unknown_expectation_is_unverified_not_failed(self):
        self.case['expected_return'] = None
        result = self.result()
        self.assertEqual(result['return_evaluation']['status'], 'UNVERIFIED')
        self.assertEqual(result['return_evaluation']['unrecovered_events'], 0)

    def test_tracking_state_does_not_hide_visible_unknown_or_invent_whole_rate(self):
        self.rows[2]['state'] = 'TRACKING'
        self.case['visible_controls'] = [{'start_frame': 2, 'end_frame_exclusive': 3}]
        result = self.result()['visible_target_unknown']
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['unknown_frames'], [2])
        self.assertEqual(result['incorrect_lost_frames'], [])
        self.assertIsNone(result['whole_video_false_alarm_rate'])
        self.assertEqual(result['whole_video_status'], 'UNEVALUATED')

    def test_no_visibility_annotations_does_not_report_zero_false_alarms(self):
        result = self.result()['visible_target_unknown']
        self.assertEqual(result['status'], 'UNEVALUATED')
        self.assertIsNone(result['unknown_count'])


class CoverageAndSourceTests(unittest.TestCase):
    def test_half_open_endpoints_and_missing_frames(self):
        interval = {'start_frame': 1, 'end_frame_exclusive': 3, 'bbox_xyxy': BOX, 'match_iou_min': .5}
        rows = [row(i, candidates=[candidate()]) for i in range(4)]
        self.assertEqual([r['frame_index'] for r in coverage(rows, True, interval)['frames']], [1, 2])
        with self.assertRaises(ValueError):
            coverage(rows[:2], True, interval)
        with self.assertRaises(ValueError):
            interval_indices({'start_frame': 2, 'end_frame_exclusive': 2})

    def test_no_detection_low_quality_and_rejection_have_separate_counts(self):
        rows = [row(0, detected=False), row(1, candidates=[candidate('DEFERRED_QUALITY', False)]),
                row(2, candidates=[candidate()])]
        data = coverage(rows, True)
        self.assertEqual(data['frame_counts']['NO_MATCHED_DETECTION'], 1)
        self.assertEqual(data['frame_counts']['QUALITY_DEFERRED'], 1)
        self.assertEqual(data['qualified_candidate_observations'], 1)
        self.assertEqual(data['appearance_rejected_observations'], 1)

    def test_no_detected_substitute_does_not_pass_appearance(self):
        data = coverage([row(0, detected=False)], True)
        self.assertEqual(data['qualified_candidate_observations'], 0)
        self.assertEqual(data['appearance_rejected_observations'], 0)

    def test_rejection_label_requires_actual_evidence(self):
        with self.assertRaises(ValueError):
            coverage([row(0, candidates=[candidate(quality=False)])], True)
        with self.assertRaises(ValueError):
            coverage([row(0, candidates=[candidate('DEFERRED_QUALITY', True)])], True)

    def test_counts_must_match_rows_events_and_cannot_import_bad_loss_count(self):
        rows = [row(0)]
        info = {'config': {'init_frame': 0, 'end_frame_exclusive': 1}, 'frames_processed': 1,
                'state_frame_counts': {'RECOVERY_CANDIDATE': 1}, 'loss_episodes': 1, 'program_accepts': 0,
                'recovery_attempts': 0, 'events': 0, 'recovery_enabled': False}
        self.assertEqual(check_counts(info, rows, [])['algorithm_confirmed_losses'], 1)
        info['loss_episodes'] = 0
        with self.assertRaisesRegex(ValueError, '次数不一致'):
            check_counts(info, rows, [])

    def test_historical_code_sha_is_enforced(self):
        blob = b'historical runner'
        info = {'code_sha256': {'run_recovery.py': hashlib.sha256(blob).hexdigest()}}
        with patch('scripts.evaluation_sources.subprocess.check_output', side_effect=['commit\n', blob]):
            self.assertEqual(verify_code(info, 'revision')['resolved_revision'], 'commit')
        info['code_sha256']['run_recovery.py'] = '0' * 64
        with patch('scripts.evaluation_sources.subprocess.check_output', side_effect=['commit\n', blob]):
            with self.assertRaisesRegex(ValueError, '历史运行代码 SHA'):
                verify_code(info, 'revision')

    def test_output_refuses_overwrite_before_reading_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            sentinel = output / 'old.json'
            sentinel.write_text('evidence')
            with self.assertRaisesRegex(ValueError, '输出目录须为空'):
                evaluate(Path('nonexistent_protocol.json'), output)
            self.assertEqual(sentinel.read_text(), 'evidence')


if __name__ == '__main__':
    unittest.main()
