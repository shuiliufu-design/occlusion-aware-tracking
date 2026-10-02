"""三组初始化/当前框及人工返回口径边界；构造记录不作为真实效果证据。"""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.evaluate_comparison import (evaluate_group, evaluate_return, position_verdict)
from scripts.m3_common import POLICY_KEYS, load_case, load_protocol, verify_shared
from scripts.run_comparison import NativeTarget, run
from scripts.run_target_state import TargetState,sha256
from test_target_state import BOX, row


def event(expected=True):
    return {'episode_id':'manual_gap_1','expected_return':expected,
            'recognizable_reappearance_frame':1 if expected is True else None,
            'evaluation_interval':{'start_frame':0,'end_frame_exclusive':4},
            'target_absent_intervals':[],'visible_controls':[]}


def replay(group='A', ids=(42,None,42,None), threshold=10):
    machine=NativeTarget(row(0,[42]),BOX) if group=='A' else TargetState(row(0,[42]),BOX,threshold)
    rows,events=[],[]
    for i,native in enumerate(ids):
        result,changes=machine.step(row(i,[native] if native is not None else []))
        if group=='B':
            result.update({'active_native_track_id':machine.native_id if not machine.loss_latched else None})
            changes=[{**changes,'event_type':'STATE_TRANSITION'}] if changes else []
        rows.append(result); events.extend(changes)
    return rows,events


LABEL={2:{'frame_index':2,'identity':'T1','bbox_xyxy':BOX}}


class NativeAdapterTests(unittest.TestCase):
    def test_only_current_detection_not_filter_prediction(self):
        data=row(0,[42]); data['tracks'][0]['bbox_xyxy']=[100,100,150,200]
        result,_=NativeTarget(data,BOX).step(data)
        self.assertEqual(result['current_target_bbox_xyxy'],BOX)
        self.assertIsNone(result['state'])
        self.assertIsNone(result['recovery_confirmed'])

    def test_no_history_box_on_missing_and_no_fake_loss(self):
        rows,events=replay()
        self.assertIsNone(rows[1]['current_target_bbox_xyxy'])
        self.assertIsNone(rows[1]['confirmed_lost_frame'])
        self.assertFalse(any(e['event_type'] in ('RECOVERY_ACCEPTED','STATE_TRANSITION') for e in events))
        self.assertEqual(events[1]['event_type'],'NATIVE_OBSERVATION_RESUMED')

    def test_new_id_does_not_replace_selected_id(self):
        for group in ('A','B'):
            rows,_=replay(group,ids=(42,None,99,None))
            self.assertFalse(rows[2]['position_known'])

    def test_native_can_return_after_long_gap_while_latched_B_cannot(self):
        a,_=replay('A',threshold=1); b,_=replay('B',threshold=1)
        self.assertTrue(a[2]['position_known'])
        self.assertFalse(b[2]['position_known'])

    def test_ambiguous_initialization_and_unassigned_rejected(self):
        for data in [row(0,[42,99]),row(0,unassigned=True)]:
            with self.assertRaises(ValueError):NativeTarget(data,BOX)

    def test_inputs_preserved_and_noncontiguous_cache_rejected(self):
        data=row(0,[1234]); before=deepcopy(data); m=NativeTarget(data,BOX)
        m.step(data); self.assertEqual(data,before)
        with self.assertRaises(ValueError):m.step(row(2))

    def test_unmatched_detection_cannot_supply_prediction(self):
        data=row(0,[42]); m=NativeTarget(data,BOX)
        data['detections'][0]['track_id']=99
        with self.assertRaises(ValueError):m.step(data)


class CommonReturnTests(unittest.TestCase):
    def result(self,group='A',labels=None,expected=True,ids=(42,None,42,None)):
        rows,events=replay(group,ids)
        return evaluate_return(group,rows,events,event(expected),LABEL if labels is None else labels,set(),30)

    def test_native_short_return_without_acceptance_counts_for_A_and_B(self):
        for group in ('A','B'):
            result=self.result(group)
            self.assertEqual(result['correct_return_events'],1)
            self.assertEqual(result['mechanism'],'NATIVE_REASSOCIATION')
            self.assertEqual(result['latency_frames'],1)
            self.assertAlmostEqual(result['latency_seconds_source_time'],1/30)

    def test_custom_acceptance_separate_from_native_return(self):
        rows,events=replay(); rows[2]['active_native_track_id']=99
        result=evaluate_return('C',rows,[{'event_type':'RECOVERY_ACCEPTED','frame_index':2}],event(),LABEL,set(),30)
        self.assertEqual(result['mechanism'],'CUSTOM_RECOVERY_ACCEPTANCE')
        self.assertEqual(result['correct_return_frame'],2)

    def test_same_id_wrong_physical_entity_is_not_correct(self):
        result=self.result(labels={2:{'identity':'OTHER_BOTTLE','bbox_xyxy':BOX}})
        self.assertEqual(result['correct_return_events'],0)
        self.assertEqual(result['unreturned_events'],1)
        self.assertEqual(result['evaluated_observations'][0]['verdict'],'INCORRECT')

    def test_same_entity_wrong_current_box_is_not_return(self):
        result=self.result(labels={2:{'identity':'T1','bbox_xyxy':[200,200,250,300]}})
        self.assertEqual(result['status'],'FAIL')
        self.assertIsNone(result['latency_frames'])

    def test_unknown_identity_has_no_fake_success_or_zero_latency(self):
        for labels in [{},{2:{'identity':'UNCERTAIN','bbox_xyxy':BOX}}]:
            result=self.result(labels=labels)
            self.assertEqual(result['status'],'UNEVALUATED')
            self.assertEqual(result['unreturned_events'],0)
            self.assertIsNone(result['latency_frames'])

    def test_negative_no_return_opportunity_not_failure(self):
        result=self.result(expected=False)
        self.assertEqual(result['expected_return_opportunities'],0)
        self.assertEqual(result['status'],'NOT_APPLICABLE')
        self.assertEqual(result['unreturned_events'],0)
        self.assertIsNone(result['latency_frames'])

    def test_unknown_opportunity_remains_unverified(self):
        result=self.result(expected=None)
        self.assertEqual(result['status'],'UNVERIFIED')
        self.assertIsNone(result['expected_return_opportunities'])

    def test_no_current_position_after_reappearance_is_missed(self):
        result=self.result(ids=(42,None,99,None))
        self.assertEqual(result['status'],'FAIL')
        self.assertEqual(result['unreturned_events'],1)

    def test_new_id_cannot_be_smuggled_as_A_target(self):
        rows,_=replay(); rows[2]['active_native_track_id']=99
        with self.assertRaises(ValueError):evaluate_return('A',rows,[],event(),LABEL,set(),30)

    def test_earlier_unlabelled_observation_prevents_exact_latency(self):
        rows,events=replay(ids=(42,42,42,None))
        result=evaluate_return('A',rows,events,event(),LABEL,set(),30)
        self.assertEqual(result['correct_return_events'],1)
        self.assertEqual(result['latency_status'],'UNEVALUATED')
        self.assertIsNone(result['latency_frames'])

    def test_positions_before_manual_reappearance_do_not_count(self):
        rows,_=replay(ids=(42,42,None,None)); labels={1:{'identity':'T1','bbox_xyxy':BOX}}
        ev=event(); ev['recognizable_reappearance_frame']=2
        result=evaluate_return('A',rows,[],ev,labels,set(),30)
        self.assertEqual(result['unreturned_events'],1)

    def test_absent_identity_overrides_same_id_and_high_score(self):
        rows,_=replay()
        result=position_verdict(rows[2],LABEL,{2})
        self.assertEqual(result['verdict'],'INCORRECT')

    def test_inconsistent_or_nonfinite_position_is_rejected(self):
        rows,_=replay(); bad=deepcopy(rows[2]); bad['position_known']=False
        with self.assertRaises(ValueError):position_verdict(bad,LABEL,set())
        bad=deepcopy(rows[2]); bad['current_target_bbox_xyxy']=[1,2,float('nan'),4]
        with self.assertRaises(ValueError):position_verdict(bad,LABEL,set())


class ComparisonProtocolTests(unittest.TestCase):
    def test_mutated_shared_initialization_is_rejected(self):
        common={'source_sha256':'source','baseline_sha256':{'frames.jsonl':'cache'},
                'initialization':{'initial_native_track_id':42},'baseline_conditions':{},
                'nominal_fps':30,'width':720,'height':1280,
                'config':{'init_frame':0,'init_box':BOX,'init_iou':.5,'missing_frames':10,
                          'end_frame_exclusive':4,'target_uid':'T1'},'config_sha256':'cfg'}
        infos={g:{**deepcopy(common),'comparison_group':g,'recovery_enabled':True if g=='C' else False if g=='B' else None} for g in 'ABC'}
        verify_shared(infos)
        infos['B']['config']['init_frame']=1
        with self.assertRaises(ValueError):verify_shared(infos)

    def test_nonempty_output_rejected_before_reading_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory); sentinel=output/'old.txt'; sentinel.write_text('keep')
            with self.assertRaises(ValueError):run(Path('absent_protocol.json'),output)
            self.assertEqual(sentinel.read_text(),'keep')

    def test_duplicate_manual_event_cannot_expand_denominator(self):
        protocol=json.loads(Path('configs/m3_protocol_v1.json').read_text())
        protocol['cases'][1]['events'][0]['episode_id']=protocol['cases'][0]['events'][0]['episode_id']
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'protocol.json'; p.write_text(json.dumps(protocol))
            with self.assertRaises(ValueError):load_protocol(p)

    def test_return_keyframe_excluded_from_fixed_sample_rate_and_AB_appearance_NA(self):
        rows,events=replay('B')
        for r in rows:r['recovery_candidates']=[]
        case={'case_id':'fixture','split':'development','initialization':{'frame_index':0},'end_frame_exclusive':4,'events':[event()]}
        supplement={'frames':[{'frame_index':0,'identity':'T1','visibility':'CLEAR','origin':'FIXED_SAMPLE'},
                              {'frame_index':2,'identity':'T1','visibility':'CLEAR','origin':'RETURN_KEYFRAME'}]}
        labels={0:{'identity':'T1','bbox_xyxy':BOX},**LABEL}
        result=evaluate_group('B',{'nominal_fps':30},rows,events,case,{},supplement,labels,
                              {'match_iou_min':.5,'fixed_sample_stride':10})
        self.assertEqual(result['fixed_sample_visibility']['clear_T1_samples'],1)
        self.assertEqual(result['wrong_candidate_appearance_rejection']['status'],'NOT_APPLICABLE')
        self.assertIsNone(result['custom_acceptance']['correct_accepts'])
        self.assertIsNone(result['fixed_sample_visibility']['whole_video_false_alarm_rate'])

    def test_holdout_cannot_use_pending_freeze(self):
        protocol=json.loads(Path('configs/m3_protocol_v1.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            manifest=Path(directory)/'pending.json'; manifest.write_text('{}')
            protocol.update(stage='HOLDOUT',freeze_status='FROZEN',
                            frozen_manifest={'path':str(manifest),'sha256':sha256(manifest)})
            p=Path(directory)/'protocol.json'; p.write_text(json.dumps(protocol))
            with patch('scripts.m3_common.check_freeze_manifest',return_value={'frozen':False}):
                with self.assertRaises(ValueError):load_protocol(p)

    def test_holdout_cannot_change_frozen_shared_policy(self):
        protocol=json.loads(Path('configs/m3_protocol_v1.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            manifest=Path(directory)/'frozen_fixture.json'
            manifest.write_text(json.dumps({'shared_policy':{k:protocol[k] for k in POLICY_KEYS}}))
            protocol.update(stage='HOLDOUT',freeze_status='FROZEN',match_iou_min=.7,
                            frozen_manifest={'path':str(manifest),'sha256':sha256(manifest)})
            p=Path(directory)/'protocol.json';p.write_text(json.dumps(protocol))
            with patch('scripts.m3_common.check_freeze_manifest',return_value={'frozen':True}):
                with self.assertRaises(ValueError):load_protocol(p)

    def test_holdout_cannot_relabel_used_development_video(self):
        protocol=json.loads(Path('configs/m3_protocol_v1.json').read_text())
        case=protocol['cases'][0]
        info=json.loads((Path(case['baseline']['path'])/'run_info.json').read_text())
        condition_keys=['inference','tracker','tracker_config','versions','tracker_constructor_frame_rate','effective_max_time_lost_frames']
        record={'source':{'sha256':case['source_sha256']},'detection_conditions':{k:info[k] for k in condition_keys},
                'model':{'sha256':info['model_sha256']},'bytetrack_yaml':{'sha256':sha256(Path(case['baseline']['path'])/'bytetrack.yaml')}}
        with tempfile.TemporaryDirectory() as directory:
            manifest=Path(directory)/'frozen_fixture.json';manifest.write_text(json.dumps({'cases':[record]}))
            protocol.update(stage='HOLDOUT',frozen_manifest={'path':str(manifest),'sha256':sha256(manifest)})
            with self.assertRaises(ValueError):load_case(case,protocol)


if __name__=='__main__':unittest.main()
