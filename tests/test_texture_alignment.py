"""有界平移的几何/退化边界和恢复安全；合成测试不代表真实身份准确率。"""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np

from scripts.appearance_recovery import (RecoveryState, align_texture, compare_feature,
                                        extract_feature, judge_candidates, load_config)
from scripts.review_recovery import check_appearance
from test_appearance_recovery import BOX, image, row


def shifted(reference, dx, dy):
    h, w = reference.shape
    result = np.full_like(reference, 123)
    x0, x1 = max(0, -dx), min(w, w-dx)
    y0, y1 = max(0, -dy), min(h, h-dy)
    result[y0:y1, x0:x1] = reference[y0+dy:y1+dy, x0+dx:x1+dx]
    return result


class TextureAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(Path('configs/recovery_f180_dev.json'))
        self.reference = np.random.default_rng(42).integers(0, 256, (96, 64), dtype=np.uint8)

    def test_small_translation_and_true_overlap_without_padding(self):
        candidate = shifted(self.reference, -2, 4)
        result = align_texture(candidate, self.reference, self.config)
        self.assertEqual(result['shift_xy'], [-2, 4])
        self.assertGreater(result['ncc'], .999)
        self.assertLess(result['zero_shift_ncc'], .1)
        self.assertEqual(result['candidate_region_xyxy'], [2, 0, 64, 92])
        self.assertEqual(result['reference_region_xyxy'], [0, 4, 62, 96])
        self.assertAlmostEqual(result['overlap_fraction'], 62*92/(64*96))

    def test_zero_shift_and_integer_bounds_included(self):
        zero = align_texture(self.reference, self.reference, self.config)
        self.assertEqual(zero['shift_xy'], [0, 0])
        self.assertEqual(zero['max_shift_xy'], [6, 9])
        self.assertEqual(zero['tested_shifts'], 13*19)
        result = align_texture(shifted(self.reference, 6, -9), self.reference, self.config)
        self.assertEqual(result['shift_xy'], [6, -9])
        self.assertGreater(result['ncc'], .999)

    def test_out_of_range_translation_cannot_be_searched(self):
        result = align_texture(shifted(self.reference, 9, 0), self.reference, self.config)
        self.assertLessEqual(abs(result['shift_xy'][0]), 6)
        self.assertLess(result['ncc'], .55)

    def test_overlap_limit_discards_small_regions(self):
        self.config['texture_min_overlap_fraction'] = .999
        result = align_texture(shifted(self.reference, 1, 1), self.reference, self.config)
        self.assertEqual(result['valid_shifts'], 1)
        self.assertEqual(result['shift_xy'], [0, 0])
        self.assertEqual(result['overlap_fraction'], 1)

    def test_constant_common_region_is_not_high_correlation_evidence(self):
        texture = np.zeros((96, 64), np.uint8)
        texture[:, 0] = np.arange(96) % 2 * 255
        result = align_texture(texture, texture, self.config)
        self.assertEqual(result['valid_shifts'], 19)
        self.assertEqual(result['shift_xy'], [0, 0])
        constant = np.full_like(texture, 100)
        self.assertIsNone(align_texture(texture, constant, self.config))
        self.assertIsNone(align_texture(constant, texture, self.config))

    def test_invalid_nonfinite_and_nonfinite_ncc_are_deferred(self):
        bad = self.reference.astype(np.float32)
        bad[0, 0] = np.nan
        self.assertIsNone(align_texture(bad, bad, self.config))
        self.assertIsNone(align_texture(self.reference[:10], self.reference, self.config))
        with patch('scripts.appearance_recovery.cv2.matchTemplate', return_value=np.array([[np.nan]])):
            self.assertIsNone(align_texture(self.reference, self.reference, self.config))

    def test_config_cannot_expand_bounds_or_shrink_overlap(self):
        for key, value in [('texture_max_shift_fraction_x', .11), ('texture_min_overlap_fraction', .79),
                           ('texture_alignment_enabled', 1)]:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                config = dict(self.config); config[key] = value
                path = Path(directory) / 'config.json'; path.write_text(json.dumps(config))
                with self.assertRaises(ValueError):
                    load_config(path)

    def test_disabled_mode_keeps_exact_original_components_and_fields(self):
        feature = extract_feature(image(), row(0)['detections'][0], self.config)
        refs = [{'frame_index': 0, 'feature': feature}]
        legacy = compare_feature(feature, refs, load_config())
        self.config['texture_alignment_enabled'] = False
        self.assertEqual(compare_feature(feature, refs, self.config), legacy)
        self.assertNotIn('texture_alignment', legacy[0])

    def test_best_reference_score_does_not_mix_other_reference_gates(self):
        feature = extract_feature(image(), row(0)['detections'][0], self.config)
        refs = [{'frame_index': 0, 'feature': feature}, {'frame_index': 1, 'feature': feature}]
        alignments = [{'ncc': 1}, {'ncc': .9}]
        with patch('scripts.appearance_recovery.cv2.compareHist', side_effect=[0, .36, .56, 0]), patch(
                'scripts.appearance_recovery.align_texture', side_effect=alignments):
            best, comparisons = compare_feature(feature, refs, self.config)
        self.assertEqual(best['reference_frame_index'], 0)
        self.assertEqual(best['label_distance'], .36)
        self.assertFalse(best['appearance_passed'])
        self.assertEqual(best['texture_ncc'], 1)
        self.assertEqual(len(comparisons), 2)

    def test_alignment_metadata_check_rejects_forged_shift_overlap_or_std(self):
        feature = extract_feature(image(), row(0)['detections'][0], self.config)
        best, comparisons = compare_feature(feature, [{'frame_index': 0, 'feature': feature}], self.config)
        original = {'best_reference': best, 'reference_comparisons': comparisons, 'confirmation_count': 0}
        check_appearance(original, self.config)
        for key, value in [('shift_xy', [7, 0]), ('overlap_fraction', .1), ('candidate_gray_std', 0)]:
            with self.subTest(key=key):
                bad = copy.deepcopy(original)
                bad['reference_comparisons'][0]['texture_alignment'][key] = value
                bad['best_reference']['texture_alignment'][key] = value
                with self.assertRaises(ValueError):
                    check_appearance(bad, self.config)


class AlignmentStateSafetyTests(unittest.TestCase):
    def machine(self):
        config = load_config(Path('configs/recovery_f180_dev.json'))
        config['reference_target_samples'] = 5
        machine = RecoveryState(row(0), BOX, 2, config)
        for index in range(5):
            machine.step(row(index), image())
        return machine

    def lost(self):
        machine = self.machine()
        machine.step(row(5, ()), image()); machine.step(row(6, ()), image())
        return machine

    def test_high_score_same_id_wrong_appearance_still_clears_position(self):
        machine = self.machine()
        digest = machine.bank.digest()
        result, _ = machine.step(row(5, score=1), image(wrong=True))
        self.assertFalse(result['position_known'])
        self.assertFalse(result['active_track_evidence']['best_reference']['appearance_passed'])
        result, _ = machine.step(row(6, score=1), image(wrong=True))
        self.assertEqual(result['recovery_candidates'][0]['decision'], 'REJECTED_APPEARANCE')
        self.assertEqual(machine.bank.digest(), digest)

    def test_quality_failure_is_not_rescued_by_alignment(self):
        machine = self.machine()
        with patch('scripts.appearance_recovery.align_texture', side_effect=AssertionError('低质不能进入对齐')):
            result, _ = machine.step(row(5, score=.49), image())
        self.assertFalse(result['position_known'])

    def test_no_valid_overlap_evidence_does_not_accumulate(self):
        machine = self.lost()
        with patch('scripts.appearance_recovery.align_texture', return_value=None):
            result, _ = machine.step(row(7, (29,)), image())
        candidate = result['recovery_candidates'][0]
        self.assertEqual(candidate['decision'], 'DEFERRED_QUALITY')
        self.assertEqual(candidate['confirmation_count'], 0)

    def test_equal_competition_remains_ambiguous_and_no_fallback(self):
        machine = self.lost()
        result, _ = machine.step(row(7, (29, 30), second=True), image(second=True))
        self.assertTrue(all(c['decision']=='AMBIGUOUS' for c in result['recovery_candidates']))
        self.assertEqual(machine.streak_count, 0)
        # 某项外观失败的高分候选仍参与差值；最高分失败不回退。
        features = [extract_feature(image(second=True), d, machine.config) for d in row(7, (29,30), second=True)['detections']]
        data = row(7, (29,30), second=True)['detections']
        with patch('scripts.appearance_recovery.compare_feature', side_effect=[
                ({'score':.85,'appearance_passed':False,'gates':{'cap_color':False}}, []),
                ({'score':.84,'appearance_passed':True,'gates':{'cap_color':True}}, [])]):
            judgments, winner = judge_candidates(data, features, machine.bank, machine.config)
        self.assertIsNone(winner)
        self.assertEqual(judgments[1]['decision'], 'AMBIGUOUS')

    def test_confirmation_reset_five_frames_and_after_recovery_loss(self):
        machine = self.lost(); digest = machine.bank.digest()
        machine.step(row(7, (29,)), image())
        result, _ = machine.step(row(8, (30,)), image())
        self.assertEqual(result['recovery_candidates'][0]['confirmation_count'], 1)
        machine.step(row(9, ()), image())
        for index in range(10, 15):
            result, _ = machine.step(row(index, (30,)), image())
            self.assertEqual(result['recovery_confirmed'], index==14)
        result, _ = machine.step(row(15, (30,), score=.49), image())
        self.assertFalse(result['position_known'])
        result, _ = machine.step(row(16, ()), image())
        self.assertEqual(result['state'], 'LOST')
        self.assertEqual(machine.bank.digest(), digest)


if __name__ == '__main__':
    unittest.main()
