"""从公共缓存运行A原生选择/B状态候选/C外观恢复，并作开发预演评价。"""

import argparse
from collections import Counter
import json
from pathlib import Path
import shlex
import sys
from types import SimpleNamespace

import cv2

try:
    from .evaluation_sources import snapshot, verify_snapshot
    from .m3_common import (GROUPS, committed_code, empty_output, freeze_checklist, load_case,
                            load_protocol, verify_shared, write_json, sha256)
    from .run_target_state import TargetState
    from .run_recovery import run as run_recovery
except ImportError:
    from evaluation_sources import snapshot, verify_snapshot
    from m3_common import (GROUPS, committed_code, empty_output, freeze_checklist, load_case,
                           load_protocol, verify_shared, write_json, sha256)
    from run_target_state import TargetState
    from run_recovery import run as run_recovery


class NativeTarget:
    """只读选择初始化原生ID，不更改ByteTrack或添加丢失/恢复状态。"""

    def __init__(self, row, box, init_iou=0.5, target_uid='T1'):
        initialization = TargetState(row, box, 1, init_iou).initialization
        self.initialization = initialization
        self.native_id = initialization['initial_native_track_id']
        self.class_id = initialization['class_id']
        self.target_uid = target_uid
        self.next_frame = row['frame_index']
        self.previous_known = None

    def step(self, row):
        if row['frame_index'] != self.next_frame:
            raise ValueError('A组缓存帧必须连续')
        self.next_frame += 1
        tracks = [t for t in row['tracks'] if t['track_id'] == self.native_id and t['class_id'] == self.class_id]
        if len(tracks) > 1:
            raise ValueError('A组同一原生ID重复')
        detection = None
        if tracks:
            track = tracks[0]
            detection = row['detections'][track['detection_index']]
            if detection['track_id'] != self.native_id or detection['class_id'] != self.class_id:
                raise ValueError('A组轨迹没有本帧实际检测依据')
        known = detection is not None
        result = {**row, 'target_uid': self.target_uid, 'state': None,
                  'reason': 'NATIVE_DETECTION_PRESENT' if known else 'NATIVE_DETECTION_ABSENT',
                  'initial_native_track_id': self.native_id,
                  'active_native_track_id': self.native_id if known else None,
                  'target_observed_this_frame': known, 'position_known': known,
                  'current_target_bbox_xyxy': detection['bbox_xyxy'] if known else None,
                  'current_detection_index': detection['detection_index'] if known else None,
                  'observation_basis': 'current detection of initially selected native ID; physical identity evaluated separately',
                  'consecutive_missing_frames': None, 'confirmed_lost_frame': None,
                  'recovery_enabled': None, 'recovery_confirmed': None, 'recovery_candidates': [],
                  'mechanism_status': {'loss_state': 'NOT_APPLICABLE', 'appearance_rejection': 'NOT_APPLICABLE',
                                       'custom_acceptance': 'NOT_APPLICABLE'}}
        events = []
        if self.previous_known is not None and known != self.previous_known:
            events.append({'event_type': 'NATIVE_OBSERVATION_RESUMED' if known else 'NATIVE_OBSERVATION_MISSING',
                           'frame_index': row['frame_index'], 'timestamp_seconds': row['timestamp_seconds'],
                           'source_pos_msec_seconds': row['source_pos_msec_seconds'],
                           'selected_native_track_id': self.native_id,
                           'note': '只读观察间断诊断；不是自定义LOST或RECOVERY_ACCEPTED，也不证明物理身份。'})
        self.previous_known = known
        return result, events


def draw_native(frame, row):
    if row['position_known']:
        x1, y1, x2, y2 = map(round, row['current_target_bbox_xyxy'])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (50, 230, 80), 3)
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 130), (20, 20, 20), -1)
    lines = [f"A ByteTrack f{row['frame_index']} {row['timestamp_seconds']:.2f}s",
             f"selected native:{row['initial_native_track_id']} position:{'OBSERVED' if row['position_known'] else 'UNKNOWN'}",
             'NATIVE ID IS NOT PHYSICAL IDENTITY PROOF']
    for offset, line in enumerate(lines):
        cv2.putText(frame, line, (12, 28+36*offset), cv2.FONT_HERSHEY_SIMPLEX, .53, (255,255,255), 1)


def run_native(case, protocol, output):
    empty_output(output)
    info, rows = load_case(case)
    initial = case['initialization']
    machine = NativeTarget(rows[initial['frame_index']], initial['bbox_xyxy'], initial['match_iou_min'])
    output.mkdir(parents=True)
    cap = cv2.VideoCapture(case['source'])
    writer = cv2.VideoWriter(str(output/'status.mp4'), cv2.VideoWriter_fourcc(*'mp4v'),
                             info['nominal_fps'], (info['width'],info['height']))
    if not cap.isOpened() or not writer.isOpened():
        cap.release(); writer.release()
        raise ValueError('A组视频无法读取/保存')
    index, count, events = 0, 0, []
    try:
        with (output/'frames.jsonl').open('w',encoding='utf-8') as stream:
            while True:
                ok, frame = cap.read()
                if not ok: break
                if index >= len(rows) or frame.shape[:2] != (info['height'],info['width']):
                    raise ValueError('A组原视频与公共缓存不一致')
                if initial['frame_index'] <= index < case['end_frame_exclusive']:
                    result, changes = machine.step(rows[index])
                    result['output_frame_index'] = count
                    stream.write(json.dumps(result,ensure_ascii=False,allow_nan=False)+'\n')
                    events.extend(changes)
                    draw_native(frame,result); writer.write(frame)
                    if count == 0:
                        if not cv2.imwrite(str(output/'first_frame.jpg'),frame):
                            raise ValueError('A组预览保存失败')
                    count += 1
                index += 1
        if index != len(rows) or count != case['end_frame_exclusive']-initial['frame_index']:
            raise ValueError('A组解码或输出帧数不足')
    finally:
        cap.release(); writer.release()
    (output/'events.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in events),encoding='utf-8')
    result = {'completed':True,'command':shlex.join(sys.orig_argv), 'source':case['source'],
              'source_sha256':info['source_sha256'],'baseline':case['baseline']['path'],
              'baseline_sha256':case['baseline']['sha256'],'initialization':machine.initialization,
              'baseline_conditions':{k:info[k] for k in ('model_sha256','tracker','tracker_config','inference','versions')},
              'width':info['width'],'height':info['height'],'nominal_fps':info['nominal_fps'],
              'config':{'init_frame':initial['frame_index'],'init_box':initial['bbox_xyxy'],
                        'init_iou':initial['match_iou_min'],'missing_frames':protocol['missing_frames'],
                        'end_frame_exclusive':case['end_frame_exclusive'],'target_uid':'T1'},
              'frames_processed':count,'source_decoded_frames':index,'detections_reused':True,
              'recovery_enabled':None,'program_accepts':None,'loss_episodes':None,
              'native_observation_events':dict(Counter(e['event_type'] for e in events)),
              'output_video':'status.mp4','state_module_enabled':False,'identity_check_enabled':False}
    return result


def run(protocol_path, output):
    empty_output(output)
    protocol = load_protocol(protocol_path)
    revision, code = committed_code()
    protected = snapshot([Path('outputs'), Path('configs/recovery.json'),
                          Path('configs/recovery_f180_dev.json'),
                          *[Path(c['source']) for c in protocol['cases']]])
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/'protocol.json',protocol)
    write_json(output/'preservation_before.json',protected)
    manifest = {'stage':protocol['stage'],'frozen':False,'protocol_sha256':sha256(protocol_path),
                'code_revision':revision,'code_sha256':code,'cases':[]}
    for case in protocol['cases']:
        initial=case['initialization']; infos={}
        for group in GROUPS:
            destination=output/case['case_id']/group
            if group=='A':
                result=run_native(case,protocol,destination)
            else:
                result=run_recovery(SimpleNamespace(source=Path(case['source']),baseline=Path(case['baseline']['path']),
                       output=destination,step1_output=None,init_frame=initial['frame_index'],
                       init_box=initial['bbox_xyxy'],init_iou=initial['match_iou_min'],missing_frames=protocol['missing_frames'],
                       end_frame=case['end_frame_exclusive'],target_uid='T1',
                       config=Path(protocol['recovery_configuration']['path']),disable_recovery=group=='B'))
            result.update({'comparison_group':group,'execution_revision':revision,
                           'common_protocol_sha256':sha256(protocol_path)})
            result.setdefault('code_sha256',{})
            result['code_sha256'].update({Path(name).name:digest for name,digest in code.items()})
            write_json(destination/'run_info.json',result); infos[group]=result
        common=verify_shared(infos)
        manifest['cases'].append({'case_id':case['case_id'],'shared_inputs':common,
                                'runs':{g:str(output/case['case_id']/g) for g in GROUPS}})
    write_json(output/'run_manifest.json',manifest)
    try:
        from .evaluate_comparison import evaluate
    except ImportError:
        from evaluate_comparison import evaluate
    summary=evaluate(protocol_path,output,output/'evaluation')
    write_json(output/'freeze_checklist.json',freeze_checklist(protocol,protocol_path,output))
    verify_snapshot(protected)
    write_json(output/'preservation_after.json',{p:sha256(Path(p)) for p in protected})
    write_json(output/'run_info.json',{'completed':True,'command':shlex.join(sys.orig_argv),
               'stage':protocol['stage'],'frozen':False,'execution_revision':revision,'code_sha256':code,
               'protocol_sha256':sha256(protocol_path),'old_files_preserved':len(protected),
               'timing_status':'UNVERIFIED','note':'三组顺序解码同一原视频/缓存，未重跑检测；没有速度对照结论。'})
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try: result=run(args.protocol,args.output)
    except (ValueError,OSError,KeyError,IndexError) as exc:
        parser.exit(1,f'三组开发预演失败: {exc}\n保留部分输出，复跑换新路径。\n')
    print(json.dumps({'completed':True,'groups':result['groups'],'frozen':False},ensure_ascii=False,indent=2))
