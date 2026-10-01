"""微型视频和已知检测记录验证关闭汇总；不作为模型效果证据。"""

import argparse
import json
from pathlib import Path
import tempfile
import unittest

import cv2
import numpy as np

from scripts.review_recovery import review
from scripts.run_recovery import DEFAULT_CONFIG_PATH, run
from scripts.run_target_state import sha256, write_json


class DisabledRunStatisticsTests(unittest.TestCase):
    def run_fixture(self, root, native_ids):
        source, baseline, output = root / 'source.avi', root / 'baseline', root / 'output'
        writer = cv2.VideoWriter(str(source), cv2.VideoWriter_fourcc(*'MJPG'), 10, (120, 160))
        self.assertTrue(writer.isOpened())
        try:
            for _ in native_ids:
                writer.write(np.full((160, 120, 3), 160, np.uint8))
        finally:
            writer.release()
        baseline.mkdir()
        rows = []
        for index, native_id in enumerate(native_ids):
            detection = {'detection_index': 0, 'bbox_xyxy': [10, 20, 50, 100],
                         'class_id': 39, 'class_name': 'bottle', 'detection_score': 0.9,
                         'track_id': native_id}
            rows.append({'frame_index': index, 'timestamp_seconds': index / 10,
                         'source_pos_msec_seconds': index / 10,
                         'detections': [detection] if native_id is not None else [],
                         'tracks': [detection.copy()] if native_id is not None else []})
        (baseline / 'frames.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
        (baseline / 'bytetrack.yaml').write_text('{}\n')
        write_json(baseline / 'run_info.json', {
            'completed': True, 'custom_recovery_enabled': False, 'source_sha256': sha256(source),
            'frames_processed': len(rows), 'tracker_updates': len(rows), 'nominal_fps': 10,
            'width': 120, 'height': 160, 'model_sha256': 'synthetic-record-fixture',
            'tracker': 'fixture', 'tracker_config': {}, 'inference': {}, 'versions': {}})
        args = argparse.Namespace(source=source, baseline=baseline, output=output,
                                  config=DEFAULT_CONFIG_PATH, end_frame=None, init_frame=0,
                                  init_box=[10, 20, 50, 100], missing_frames=2, init_iou=0.5,
                                  target_uid='T1', disable_recovery=True, step1_output=None)
        info = run(args)
        records = [json.loads(line) for line in (output / 'frames.jsonl').read_text().splitlines()]
        review(output, [])
        return info, records, output

    def test_loss_and_candidate_oscillation_count_as_one_episode(self):
        with tempfile.TemporaryDirectory() as directory:
            info, rows, _ = self.run_fixture(Path(directory), [17, 17, None, None, 33, None, 33])
            self.assertEqual(info['loss_episodes'], 1)
            self.assertEqual([row['state'] for row in rows][3:],
                             ['LOST', 'RECOVERY_CANDIDATE', 'LOST', 'RECOVERY_CANDIDATE'])
            self.assertEqual(info['program_accepts'], 0)
            self.assertEqual(info['recovery_attempts'], 0)

    def test_confirmed_loss_with_only_candidate_state_is_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            info, rows, _ = self.run_fixture(Path(directory), [17, 17, 33, 33, 33])
            self.assertEqual(info['loss_episodes'], 1)
            self.assertNotIn('LOST', [row['state'] for row in rows])
            self.assertEqual(rows[3]['confirmed_lost_frame'], 3)

    def test_short_gap_reobserved_before_threshold_has_no_loss(self):
        with tempfile.TemporaryDirectory() as directory:
            info, _, _ = self.run_fixture(Path(directory), [17, 17, None, 17, 17])
            self.assertEqual(info['loss_episodes'], 0)

    def test_reviewer_rejects_the_previous_zero_count_bug(self):
        with tempfile.TemporaryDirectory() as directory:
            info, _, output = self.run_fixture(Path(directory), [17, 17, None, None, None])
            info['loss_episodes'] = 0
            write_json(output / 'run_info.json', info)
            with self.assertRaisesRegex(ValueError, '关闭分支丢失次数'):
                review(output, [])


if __name__ == '__main__':
    unittest.main()
