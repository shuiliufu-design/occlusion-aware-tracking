import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_holdout_annotations import (validate_event, validate_frame_labels,
                                          validate_visibility_intervals)


def label(index, origin='FIXED_SAMPLE', identity='T1', visibility='CLEAR'):
    return {'frame_index': index, 'origin': origin, 'identity': identity,
            'visibility': visibility, 'bbox_xyxy': [10, 20, 30, 70] if visibility == 'CLEAR' else None,
            'timestamp_seconds': index / 30, 'source_pos_msec_seconds': index / 30}


class HoldoutAnnotationTests(unittest.TestCase):
    def setUp(self):
        self.frames = [label(0), label(10), label(3, 'EVENT_KEYFRAME', 'UNCERTAIN', 'UNCERTAIN')]

    def check(self, frames=None):
        return validate_frame_labels(self.frames if frames is None else frames, 0, 20, 10, 100, 100)

    def test_fixed_grid_complete_keyframe_not_denominator(self):
        result = self.check()
        self.assertEqual(result['fixed_samples_checked'], 2)
        self.assertEqual(result['additional_keyframes'], 1)
        self.assertEqual(result['uncertain_frames'], [3])

    def test_missing_fixed_sample_rejected(self):
        with self.assertRaisesRegex(ValueError, '缺帧'):
            self.check([self.frames[0], self.frames[2]])

    def test_duplicate_frame_rejected(self):
        with self.assertRaisesRegex(ValueError, '重复'):
            self.check(self.frames + [label(0)])

    def test_keyframe_cannot_be_fixed_sample(self):
        frames = copy.deepcopy(self.frames); frames[2]['origin'] = 'FIXED_SAMPLE'
        with self.assertRaisesRegex(ValueError, '关键帧'):
            self.check(frames)

    def test_manual_box_outside_pixels_rejected(self):
        frames = copy.deepcopy(self.frames); frames[0]['bbox_xyxy'] = [-1, 20, 30, 70]
        with self.assertRaisesRegex(ValueError, '超出原图'):
            self.check(frames)

    def test_nonfinite_manual_box_rejected(self):
        frames = copy.deepcopy(self.frames); frames[0]['bbox_xyxy'][0] = float('nan')
        with self.assertRaisesRegex(ValueError, '无效'):
            self.check(frames)

    def test_partial_identity_does_not_imply_complete_geometry(self):
        frames = [label(0), label(10, identity='OTHER_BOTTLE', visibility='PARTIAL')]
        self.assertEqual(self.check(frames)['fixed_partial_or_uncertain_geometry'], [10])
        frames[1]['bbox_xyxy'] = [10, 20, 30, 70]
        with self.assertRaisesRegex(ValueError, '补完整框'):
            self.check(frames)

    def test_uncertain_cannot_claim_target_identity(self):
        frames = copy.deepcopy(self.frames); frames[2]['identity'] = 'T1'
        with self.assertRaisesRegex(ValueError, '强判身份'):
            self.check(frames)

    def test_visibility_intervals_no_gaps_or_overlap(self):
        for spans in ([{'start_frame': 0, 'end_frame_exclusive': 10},
                       {'start_frame': 11, 'end_frame_exclusive': 20}],
                      [{'start_frame': 0, 'end_frame_exclusive': 11},
                       {'start_frame': 10, 'end_frame_exclusive': 20}]):
            with self.assertRaisesRegex(ValueError, '空隙/重叠'):
                validate_visibility_intervals(spans, [], 0, 20)

    def test_negative_zero_opportunity_cannot_have_return_frame(self):
        event = {'expected_return': False, 'recognizable_reappearance_frame': None}
        physical = {'original_target_removed': True, 'original_target_reappears': False}
        validate_event(event, physical, {}, False)
        event['recognizable_reappearance_frame'] = 10
        with self.assertRaisesRegex(ValueError, '零返回机会'):
            validate_event(event, physical, {}, False)

    def test_positive_return_needs_original_pixel_identity(self):
        event = {'expected_return': True, 'recognizable_reappearance_frame': 10}
        with self.assertRaisesRegex(ValueError, '可辨认T1'):
            validate_event(event, {}, {10: label(10, identity='OTHER_BOTTLE')}, True)

    def test_timestamp_must_be_finite_original_time(self):
        frames = copy.deepcopy(self.frames); frames[0]['source_pos_msec_seconds'] = float('inf')
        with self.assertRaisesRegex(ValueError, '原帧时间'):
            self.check(frames)


if __name__ == '__main__':
    unittest.main()
