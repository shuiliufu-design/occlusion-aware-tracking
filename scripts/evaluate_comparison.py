"""M3 三组共同人工事件评价；当前框决定正确返回，接受事件仅作机制诊断。"""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

import cv2
import numpy as np

try:
    from .evaluate_offline import STATUS_MEANINGS, coverage, interval_indices
    from .evaluation_sources import (check_counts, historical_blob, read_json, read_rows,
                                     run_historical_checks, snapshot, verify_code, verify_snapshot)
    from .m3_common import (GROUPS, checked_file, committed_code, empty_output, load_case,
                            load_protocol, verify_shared)
    from .run_target_state import box_iou, sha256, write_json
except ImportError:
    from evaluate_offline import STATUS_MEANINGS, coverage, interval_indices
    from evaluation_sources import (check_counts, historical_blob, read_json, read_rows,
                                    run_historical_checks, snapshot, verify_code, verify_snapshot)
    from m3_common import (GROUPS, checked_file, committed_code, empty_output, load_case,
                           load_protocol, verify_shared)
    from run_target_state import box_iou, sha256, write_json


def position_verdict(row, labels, absent, target_uid='T1', match_iou_min=0.5):
    """不读取跟踪ID/检测分数作为身份真值。"""
    known = row['position_known']
    box = row['current_target_bbox_xyxy']
    if known != (box is not None):
        raise ValueError('当前位置框与position_known矛盾')
    if not known:
        return {'verdict':'NO_CURRENT_POSITION','annotation_iou':None}
    if len(box)!=4 or not all(math.isfinite(v) for v in box) or not (box[0]<box[2] and box[1]<box[3]):
        raise ValueError('输出当前位置框无效')
    frame = row['frame_index']
    if frame in absent:
        return {'verdict':'INCORRECT','reason':'人工确认原目标不在画面','annotation_iou':None}
    label = labels.get(frame)
    if not label or label['identity'] in ('UNCERTAIN','UNKNOWN'):
        return {'verdict':'UNEVALUATED','reason':'缺少本帧独立身份/框','annotation_iou':None}
    if label['identity'] != target_uid:
        return {'verdict':'INCORRECT','reason':'本帧人工身份为另一物体','annotation_iou':None}
    if label.get('bbox_xyxy') is None:
        return {'verdict':'UNEVALUATED','reason':'同一实体有依据但缺少本帧人工框','annotation_iou':None}
    manual=label['bbox_xyxy']
    if len(manual)!=4 or not all(math.isfinite(v) for v in manual) or not (manual[0]<manual[2] and manual[1]<manual[3]):
        raise ValueError('人工评价框无效')
    iou = box_iou(box,manual)
    return {'verdict':'CORRECT' if iou >= match_iou_min else 'INCORRECT',
            'reason':'人工同一目标与本帧框核对' if iou >= match_iou_min else '当前框未达到人工IoU门槛',
            'annotation_iou':iou}


def evaluate_return(group, rows, events, event, labels, absent, fps, iou_min=0.5):
    indices = interval_indices(event['evaluation_interval'])
    by_frame = {r['frame_index']:r for r in rows}
    if any(i not in by_frame for i in indices):
        raise ValueError('共同事件评价窗不完整')
    expected = event['expected_return']
    base = {'expected_return_opportunities':int(expected is True) if expected is not None else None,
            'correct_return_events':0,'unreturned_events':0,'unevaluated_return_events':0,
            'correct_return_frame':None,'mechanism':None,'latency_frames':None,
            'latency_seconds_frame_fps':None,'latency_seconds_source_time':None,
            'latency_status':'NOT_APPLICABLE','success_rate':None,
            'unknown_observation_frames_before_verified_return':[], 'evaluated_observations':[]}
    if expected is not True:
        return base | {'status':'NOT_APPLICABLE' if expected is False else 'UNVERIFIED'}
    start = event['recognizable_reappearance_frame']
    if type(start) is not int or start not in indices:
        raise ValueError('人工可辨认重现帧无效')
    unknown, judgments, verified = [], [], None
    for i in range(start,indices.stop):
        row = by_frame[i]
        if not row['position_known']:
            if row['current_target_bbox_xyxy'] is not None:
                raise ValueError('未知位置却填入当前位置')
            continue
        judgment = position_verdict(row,labels,absent,match_iou_min=iou_min)
        if judgment['verdict']=='UNEVALUATED':
            unknown.append(i)
        else:
            judgments.append({'frame_index':i,**judgment})
        if judgment['verdict']=='CORRECT':
            verified=i; break
    base.update({'unknown_observation_frames_before_verified_return':unknown,
                 'evaluated_observations':judgments})
    if verified is None:
        base.update({'status':'UNEVALUATED' if unknown else 'FAIL',
                     'unreturned_events':int(not unknown),'unevaluated_return_events':int(bool(unknown)),
                     'success_rate':None if unknown else 0.0})
        return base
    accepted = any(e['event_type']=='RECOVERY_ACCEPTED' and e['frame_index']==verified for e in events)
    initial_id=by_frame[verified]['initial_native_track_id']
    active_id=by_frame[verified].get('active_native_track_id')
    if group=='C' and accepted:
        mechanism='CUSTOM_RECOVERY_ACCEPTANCE'
    elif active_id==initial_id:
        gap=any(not by_frame[i]['position_known'] for i in range(indices.start,verified))
        mechanism=('NATIVE_REASSOCIATION_WITH_APPEARANCE' if group=='C' else 'NATIVE_REASSOCIATION') if gap else 'NATIVE_CONTINUITY'
    else:
        if group in ('A','B'):
            raise ValueError('A/B不得把新ID自动当作初始化目标')
        mechanism='EXISTING_CUSTOM_BINDING_OBSERVED'
    base.update({'status':'PASS','correct_return_events':1,'correct_return_frame':verified,
                 'mechanism':mechanism,'success_rate':1.0})
    if unknown:
        # 返回存在已确认，但更早输出未标注，无法报告精确首次返回延迟。
        base['latency_status']='UNEVALUATED'
    else:
        base.update({'latency_status':'PASS','latency_frames':verified-start,
                     'latency_seconds_frame_fps':(verified-start)/fps,
                     'latency_seconds_source_time':by_frame[verified]['source_pos_msec_seconds']-by_frame[start]['source_pos_msec_seconds']})
    return base


def validate_labels(case, protocol):
    physical = read_json(checked_file(case['physical_identity_annotation']))
    supplemental = read_json(checked_file(case['evaluation_labels']))
    if (physical['source_sha256'] != case['source_sha256'] or physical['target_uid'] != 'T1'
            or not physical.get('operator_confirmation') or not physical.get('confirmation_basis')
            or supplemental['source_sha256'] != case['source_sha256']):
        raise ValueError('共同身份依据/视频来源不一致')
    start,end=case['initialization']['frame_index'],case['end_frame_exclusive']
    labels={k['frame_index']:k for k in physical.get('keyframes',[])}
    seen=set(); images={}
    for label in supplemental['frames']:
        i=label['frame_index']
        if i in seen or type(i) is not int or not start <= i < end or not label.get('annotator') or not label.get('basis'):
            raise ValueError('新增标注重复/越界或缺少人工依据')
        seen.add(i)
        if label['origin']=='FIXED_SAMPLE' and (i-start)%protocol['fixed_sample_stride']:
            raise ValueError('后补帧不得进入固定抽样分母')
        path=checked_file(label['raw_image'])
        images[i]=path; labels[i]=label
    cap=cv2.VideoCapture(case['source']); index=0; checked=0
    try:
        if not cap.isOpened(): raise ValueError('无法核对原始标注图')
        while index <= max(images,default=-1):
            ok,frame=cap.read()
            if not ok: raise ValueError('标注原视频提前结束')
            if index in images:
                if not np.array_equal(frame,cv2.imread(str(images[index]))):
                    raise ValueError('新增标注图与原像素不一致')
                checked+=1
            index+=1
    finally: cap.release()
    for event in case['events']:
        interval=interval_indices(event['evaluation_interval'])
        if interval.start < start or interval.stop > end:
            raise ValueError('人工事件越过共同处理范围')
        if event['expected_return'] is True and event['recognizable_reappearance_frame'] != physical.get('recognizable_reappearance_frame'):
            raise ValueError('可辨认重现时刻须与独立人工依据一致')
        if event['expected_return'] is False:
            if not physical.get('original_target_removed') or physical.get('original_target_reappears') is not False or event['recognizable_reappearance_frame'] is not None:
                raise ValueError('无返回机会缺少原目标取走确认')
        for sub in [*event['target_absent_intervals'],*event['visible_controls']]:
            points=interval_indices(sub)
            if points.start < interval.start or points.stop > interval.stop:
                raise ValueError('人工子区间越过共同事件')
            if 'evidence' in sub:
                checked_file({'path':sub['evidence'],'sha256':sub['evidence_sha256']})
        for control in event['visible_controls']:
            checked_file({'path':control['evidence'],'sha256':control['evidence_sha256']})
    return physical,supplemental,labels,{'raw_annotation_images_verified':checked,'sequential_decoded_frames':index}


def review_native(output, revision, destination):
    info=read_json(output/'run_info.json')
    provenance=verify_code(info,revision)
    with tempfile.TemporaryDirectory(prefix='m3_native_review_') as directory:
        root=Path(directory)
        names=subprocess.check_output(['git','ls-tree','-r','--name-only',revision,'scripts'],text=True).splitlines()
        for name in names:
            if name.endswith('.py'): (root/Path(name).name).write_bytes(historical_blob(revision,Path(name).name))
        driver=root/'replay_native.py'
        driver.write_text('''
import json,sys,cv2
from pathlib import Path
from run_comparison import NativeTarget
from evaluation_sources import read_json,read_rows
p=Path(sys.argv[1]); info=read_json(p/'run_info.json'); c=info['config']
base=read_rows(Path(info['baseline'])/'frames.jsonl'); rows=read_rows(p/'frames.jsonl')
m=NativeTarget(base[c['init_frame']],c['init_box'],c['init_iou'],c['target_uid']); events=[]
if len(rows)!=c['end_frame_exclusive']-c['init_frame']: raise ValueError('A区间不完整')
for n,row in enumerate(rows):
    expected,changes=m.step(base[c['init_frame']+n]); expected['output_frame_index']=n
    if row!=expected: raise ValueError('A只读选择回放不一致')
    events.extend(changes)
if read_rows(p/'events.jsonl')!=events: raise ValueError('A观察间断诊断不一致')
cap=cv2.VideoCapture(str(p/'status.mp4')); count=0
while True:
    ok,frame=cap.read()
    if not ok: break
    if frame.shape[:2]!=(info['height'],info['width']): raise ValueError('A视频尺寸不一致')
    count+=1
cap.release()
if count!=len(rows): raise ValueError('A视频帧数不一致')
print(count)
''',encoding='utf-8')
        result=subprocess.run([sys.executable,str(driver),str(output)],capture_output=True,text=True,check=True)
    provenance['record_checks']={'native_selection_replayed_frames':int(result.stdout.strip()),
                                 'output_decoded_frames':int(result.stdout.strip()),'custom_state_applicable':False}
    write_json(destination/'A_source_checks.json',provenance)
    return provenance


def evaluate_group(group, info, rows, events, case, physical, supplemental, labels, protocol):
    absent={i for e in case['events'] for sub in e['target_absent_intervals'] for i in interval_indices(sub)}
    by_frame={r['frame_index']:r for r in rows}
    iou_min=protocol['match_iou_min']
    audited=[]
    for i in sorted(absent | {i for i in labels if i in by_frame}):
        audited.append({'frame_index':i,**position_verdict(by_frame[i],labels,absent,match_iou_min=iou_min)})
    wrong=[item for item in audited if item['verdict']=='INCORRECT']
    fixed=[k for k in supplemental['frames'] if k['origin']=='FIXED_SAMPLE']
    visible=[k['frame_index'] for k in fixed if k['identity']=='T1' and k['visibility']=='CLEAR']
    unknown=[i for i in visible if not by_frame[i]['position_known']]
    plan=list(range(case['initialization']['frame_index'],case['end_frame_exclusive'],protocol['fixed_sample_stride']))
    known_samples={k['frame_index'] for k in fixed}
    accepted=[e for e in events if e['event_type']=='RECOVERY_ACCEPTED']
    if group!='C' and accepted:
        raise ValueError('A/B出现自定义恢复绑定事件')
    binding=[{'frame_index':e['frame_index'],**position_verdict(by_frame[e['frame_index']],labels,absent,match_iou_min=iou_min)} for e in accepted]
    counts=Counter(v['verdict'] for v in binding)
    whole=coverage(rows,group=='C')
    negative=coverage(rows,group=='C',physical['negative_interval']) if 'negative_interval' in physical else None
    rejection='NOT_APPLICABLE'
    if group=='C' and negative is not None:
        qualified=negative['qualified_candidate_observations']; rejected=negative['appearance_rejected_observations']
        rejection='FAIL' if wrong or counts['INCORRECT'] or qualified!=rejected else ('PASS' if qualified else 'UNVERIFIED')
    controls={i for event in case['events'] for control in event['visible_controls'] for i in interval_indices(control)}
    return {'case_id':case['case_id'],'group':group,'split':case['split'],
            'events':[{'episode_id':event['episode_id'],'expected_return':event['expected_return'],
                       'return_evaluation':evaluate_return(group,rows,events,event,labels,absent,info['nominal_fps'],iou_min)} for event in case['events']],
            'custom_acceptance':{'status':'APPLICABLE' if group=='C' else 'NOT_APPLICABLE',
                'program_accepts':len(accepted) if group=='C' else None,
                'correct_accepts':counts['CORRECT'] if group=='C' else None,
                'incorrect_accepts':counts['INCORRECT'] if group=='C' else None,
                'unevaluated_accepts':counts['UNEVALUATED'] if group=='C' else None,'results':binding},
            'incorrect_current_position':{'status':'FAIL' if wrong else 'PASS' if audited else 'UNEVALUATED',
                'annotated_absent_frames':len(absent),'incorrect_absent_frames':[i for i in sorted(absent) if by_frame[i]['position_known']],
                'incorrect_audited_frames':[v['frame_index'] for v in wrong],'whole_video_status':'UNEVALUATED'},
            'fixed_sample_visibility':{'status':'FAIL' if unknown else 'PASS' if visible else 'UNEVALUATED',
                'planned_samples':len(plan),'annotated_samples':len(fixed),'unreviewed_samples':[i for i in plan if i not in known_samples],
                'clear_T1_samples':len(visible),'unknown_clear_T1_samples':unknown,
                'sample_false_alarm_rate':len(unknown)/len(visible) if visible else None,
                'whole_video_false_alarm_rate':None,'whole_video_status':'UNEVALUATED'},
            'diagnostic_visible_controls':{'annotated_frames':len(controls),
                 'unknown_frames':[i for i in sorted(controls) if not by_frame[i]['position_known']],
                 'note':'旧诊断控制单列；后补关键帧不扩充固定抽样分母。'},
            'wrong_candidate_appearance_rejection':{'status':rejection,'replacement_events':int(negative is not None),
                'coverage':negative,'note':'A/B未执行外观核验；无绑定不能算拒绝通过。'},
            'whole_run_candidate_coverage':whole if group!='A' else {
                'status':'NOT_APPLICABLE','candidate_observations':None,
                'note':'A只有原生ID选择，没有M2候选机制；原检测仍完整保存。'},
            'native_reassociation_diagnostics':[e for e in events if e['event_type']=='NATIVE_OBSERVATION_RESUMED'] if group=='A' else {
                'status':'DIAGNOSED_BY_CURRENT_POSITION','note':'主返回指标不要求自定义接受事件。'},
            'position_audit':audited}


def evaluate(protocol_path, runs_root, output):
    empty_output(output)
    protocol=load_protocol(protocol_path)
    revision,code=committed_code()
    manifest=read_json(runs_root/'run_manifest.json')
    if manifest['protocol_sha256']!=sha256(protocol_path):
        raise ValueError('运行与评价协议不一致')
    protected=snapshot([runs_root,*[checked_file(c['evaluation_labels']) for c in protocol['cases']]])
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/'preservation_before.json',protected)
    common_events=[]; detailed=[]; source_checks=[]; label_checks=[]
    for case in protocol['cases']:
        load_case(case,protocol)
        physical,supplemental,labels,checks=validate_labels(case,protocol)
        label_checks.append({'case_id':case['case_id'],**checks,
                             'operator_confirmation':physical['operator_confirmation']})
        common_events.extend({'case_id':case['case_id'],'source_sha256':case['source_sha256'],
            'physical_identity_annotation':case['physical_identity_annotation'],'supplemental_labels':case['evaluation_labels'],**event} for event in case['events'])
        infos={g:read_json(runs_root/case['case_id']/g/'run_info.json') for g in GROUPS}
        verify_shared(infos)
        for group in GROUPS:
            directory=runs_root/case['case_id']/group; info=infos[group]
            if info['common_protocol_sha256']!=sha256(protocol_path) or info['execution_revision']!=manifest['code_revision']:
                raise ValueError('组别运行版本/协议来源不一致')
            if group!='A' and (info['config_sha256']!=protocol['recovery_configuration']['sha256'] or
                              info['appearance_config']!=read_json(checked_file(protocol['recovery_configuration']))):
                raise ValueError('B/C未使用00选定恢复配置')
            rows,events=read_rows(directory/'frames.jsonl'),read_rows(directory/'events.jsonl')
            destination=output/'source_checks'/case['case_id']/group
            destination.mkdir(parents=True)
            if group=='A':
                provenance=review_native(directory,info['execution_revision'],destination)
            else:
                check_counts(info,rows,events)
                provenance=run_historical_checks({'output':str(directory),'run_id':group,
                    'code_revision':info['execution_revision']},destination,
                    checked_file(case['physical_identity_annotation']) if group=='C' and 'negative_interval' in physical else None)
                old=case.get('regression_outputs',{}).get(group)
                if old:
                    if rows!=read_rows(Path(old)/'frames.jsonl') or events!=read_rows(Path(old)/'events.jsonl'):
                        raise ValueError('B/C改变了已验证核心行为；保留结果交00，不在预演中改核心')
                    if sha256(directory/'status.mp4')!=sha256(Path(old)/'status.mp4'):
                        raise ValueError('B/C状态视频回归不一致')
                    provenance['known_development_regression_identical']=True
            source_checks.append({'case_id':case['case_id'],'group':group,'output':str(directory),
                                  'input_sha256':{name:sha256(directory/name) for name in ('frames.jsonl','events.jsonl','run_info.json','status.mp4')},
                                  'provenance':provenance})
            detailed.append(evaluate_group(group,info,rows,events,case,physical,supplemental,labels,protocol))
    groups=[]
    for item in detailed:
        groups.append({k:item[k] for k in ('case_id','group','split','events','custom_acceptance','incorrect_current_position',
                                         'fixed_sample_visibility','diagnostic_visible_controls')} | {
            'appearance_rejection_status':item['wrong_candidate_appearance_rejection']['status'],
            'manual_negative_coverage':{k:v for k,v in item['wrong_candidate_appearance_rejection']['coverage'].items() if k!='frames'}
               if item['wrong_candidate_appearance_rejection']['coverage'] else None,
            'whole_run_candidate_observations':item['whole_run_candidate_coverage'].get('candidate_observations')})
    summary={'stage':protocol['stage'],'status_meanings':STATUS_MEANINGS,'groups':groups,
             'independent_manual_events':len(common_events),'independent_return_opportunities':sum(e['expected_return'] is True for e in common_events),
             'frozen':protocol['freeze_status']=='FROZEN','M3_holdout_started':protocol['stage']=='HOLDOUT','timing':protocol['timing'],
             'whole_video_false_alarm_rate':None,'whole_video_visibility_status':'UNEVALUATED',
             'unverified_scopes':protocol['unverified_scopes'],'annotation_limits':protocol['annotation_limits'],
             'note':'每组分别评价相同人工事件；不累加为三倍独立样本，不改变旧M2接受事件口径。'}
    write_json(output/'common_manual_events.json',common_events)
    write_json(output/'per_event_results.json',detailed)
    write_json(output/'annotation_checks.json',label_checks)
    write_json(output/'summary.json',summary)
    verify_snapshot(protected)
    write_json(output/'preservation_after.json',{p:sha256(Path(p)) for p in protected})
    write_json(output/'run_info.json',{'completed':True,'command':shlex.join(sys.orig_argv),
               'git_head_at_execution':revision,'execution_code_sha256':code,'protocol_sha256':sha256(protocol_path),
               'source_checks':source_checks,'files_preserved':len(protected)})
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol',type=Path,required=True)
    parser.add_argument('--runs',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try: result=evaluate(args.protocol,args.runs,args.output)
    except (ValueError,OSError,KeyError,IndexError,subprocess.CalledProcessError) as exc:
        parser.exit(1,f'三组评价失败: {getattr(exc,"stderr",None) or str(exc)}\n保留旧输出。\n')
    print(json.dumps({'completed':True,'groups':result['groups'],'frozen':result['frozen']},ensure_ascii=False,indent=2))
