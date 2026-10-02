"""M3 开发预演的公共输入、代码来源和待冻结清单；不改 M2 核心。"""

import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

try:
    from .evaluation_sources import read_json, read_rows
    from .run_target_state import load_baseline, sha256, write_json
except ImportError:
    from evaluation_sources import read_json, read_rows
    from run_target_state import load_baseline, sha256, write_json


GROUPS = ('A', 'B', 'C')
EXECUTION_FILES = ('scripts/run_comparison.py', 'scripts/evaluate_comparison.py',
                   'scripts/m3_common.py', 'scripts/run_recovery.py',
                   'scripts/appearance_recovery.py', 'scripts/run_target_state.py',
                   'scripts/evaluate_offline.py', 'scripts/evaluation_sources.py',
                   'scripts/review_recovery.py', 'scripts/validate_wrong_bottle.py')


def empty_output(path):
    path = Path(path)
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise ValueError('输出目录须为空；保留旧结果，换新路径')


def checked_file(item):
    path = Path(item['path'])
    if sha256(path) != item['sha256']:
        raise ValueError(f'来源 SHA 不匹配: {path}')
    return path


def committed_code():
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    hashes = {}
    for name in EXECUTION_FILES:
        blob = subprocess.check_output(['git', 'show', f'{revision}:{name}'])
        digest = hashlib.sha256(blob).hexdigest()
        if digest != sha256(Path(name)):
            raise ValueError(f'先提交实际执行代码，再运行: {name}')
        hashes[name] = digest
    return revision, hashes


def load_protocol(path):
    protocol = read_json(path)
    if (protocol.get('schema_version') != 1 or protocol.get('stage') != 'DEVELOPMENT_PREFLIGHT'
            or protocol.get('freeze_status') != 'PENDING_REVIEW_NOT_FROZEN'
            or protocol.get('groups') != list(GROUPS)):
        raise ValueError('本入口仅执行三组开发预演；协议尚未正式冻结')
    if (type(protocol['missing_frames']) is not int or protocol['missing_frames'] < 1
            or not 0 < protocol['match_iou_min'] <= 1
            or type(protocol['fixed_sample_stride']) is not int or protocol['fixed_sample_stride'] < 1):
        raise ValueError('缺失/IoU/抽样参数无效')
    config = checked_file(protocol['recovery_configuration'])
    selected = checked_file(protocol['selected_configuration_source'])
    if config.read_bytes() != selected.read_bytes():
        raise ValueError('M3 配置须与00选定对齐配置完全一致')
    checked_file(protocol['original_configuration'])
    cases, episodes = set(), set()
    for case in protocol['cases']:
        if case['case_id'] in cases or case['split'] != 'development':
            raise ValueError('开发片ID重复或混入独立测试')
        cases.add(case['case_id'])
        for event in case['events']:
            if not event['episode_id'] or event['episode_id'] in episodes:
                raise ValueError('共同人工事件ID重复')
            episodes.add(event['episode_id'])
            if event['expected_return'] is not None and type(event['expected_return']) is not bool:
                raise ValueError('返回机会只允许true/false/null')
    if not cases:
        raise ValueError('缺少开发输入')
    return protocol


def load_case(case):
    info, rows = load_baseline(Path(case['baseline']['path']), Path(case['source']))
    if info['source_sha256'] != case['source_sha256']:
        raise ValueError('公共原视频校验不一致')
    for name, digest in case['baseline']['sha256'].items():
        if sha256(Path(case['baseline']['path']) / name) != digest:
            raise ValueError('公共缓存校验不一致')
    start, end = case['initialization']['frame_index'], case['end_frame_exclusive']
    if not 0 <= start < end <= len(rows):
        raise ValueError('公共处理区间无效')
    box = case['initialization']['bbox_xyxy']
    if len(box) != 4 or not (0 <= box[0] < box[2] <= info['width'] and 0 <= box[1] < box[3] <= info['height']):
        raise ValueError('公共人工初始化框无效')
    return info, rows


def shared_inputs(info):
    return {k: info[k] for k in ('source_sha256', 'baseline_sha256', 'initialization',
                                'baseline_conditions', 'nominal_fps', 'width', 'height')} | {
        'config': {k: info['config'][k] for k in ('init_frame', 'init_box', 'init_iou',
                                                'missing_frames', 'end_frame_exclusive', 'target_uid')}}


def verify_shared(infos):
    if set(infos) != set(GROUPS):
        raise ValueError('须同时有A/B/C三组')
    common = shared_inputs(infos['A'])
    for group, info in infos.items():
        if shared_inputs(info) != common or info['comparison_group'] != group:
            raise ValueError('三组缓存/初始化/区间/时间或组别不一致')
        if info['recovery_enabled'] is not (True if group == 'C' else False if group == 'B' else None):
            raise ValueError('三组机制开关不符合A/B/C定义')
    if infos['B']['config_sha256'] != infos['C']['config_sha256']:
        raise ValueError('B/C共同配置校验不一致')
    return common


def freeze_checklist(protocol, protocol_path, runs_root):
    revision, code = committed_code()
    config = checked_file(protocol['recovery_configuration'])
    requirements = {str(p): sha256(p) for p in (Path('requirements.txt'), Path('requirements-baseline.txt'))}
    dependencies = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True)
    dependency_path = runs_root / 'dependencies_snapshot.txt'
    dependency_path.write_text(dependencies, encoding='utf-8')
    cases = []
    for case in protocol['cases']:
        info, _ = load_case(case)
        model = Path(info['model'])
        yaml = Path(case['baseline']['path']) / 'bytetrack.yaml'
        if sha256(model) != info['model_sha256'] or sha256(yaml) != info['tracker_config_sha256']:
            raise ValueError('权重或原生YAML校验不一致')
        cases.append({'case_id': case['case_id'], 'split': case['split'],
                      'source': {'path': case['source'], 'sha256': case['source_sha256']}, 'baseline': case['baseline'],
                      'initialization': case['initialization'], 'end_frame_exclusive': case['end_frame_exclusive'],
                      'model': {'path': str(model), 'sha256': sha256(model)},
                      'bytetrack_yaml': {'path': str(yaml), 'sha256': sha256(yaml)},
                      'detection_conditions': {k: info[k] for k in ('inference', 'tracker', 'tracker_config',
                                              'versions', 'tracker_constructor_frame_rate', 'effective_max_time_lost_frames')},
                      'identity_evidence': case['physical_identity_annotation'],
                      'supplemental_labels': case['evaluation_labels']})
    return {'status': 'PENDING_REVIEW_NOT_FROZEN', 'git_revision': revision,
            'executed_code_sha256': code, 'protocol': {'path': str(protocol_path), 'sha256': sha256(protocol_path)},
            'recovery_configuration': protocol['recovery_configuration'],
            'selected_configuration_source': protocol['selected_configuration_source'],
            'original_configuration': protocol['original_configuration'],
            'all_recovery_parameters': read_json(config), 'requirements_sha256': requirements,
            'installed_dependencies': {'path': str(dependency_path), 'sha256': sha256(dependency_path)},
            'runtime': {'python': platform.python_version(), 'opencv': importlib.metadata.version('opencv-python'),
                        'platform': platform.platform(), 'hardware': platform.machine()},
            'cases': cases, 'missing_frames': protocol['missing_frames'],
            'initialization_rule': protocol['initialization_rule'],
            'reference_rule': protocol['reference_rule'], 'sampling_rule': protocol['sampling_rule'],
            'metrics': protocol['metrics'], 'timing': protocol['timing'],
            'independent_test_design': protocol['independent_test_design'],
            'review_needed': '00核对开发预演后再记录冻结；新测试片只用早期画面指定初始化，不按后段结果重选。'}


def check_freeze_manifest(path):
    manifest = read_json(path)
    for name, digest in manifest['executed_code_sha256'].items():
        blob = subprocess.check_output(['git','show',f"{manifest['git_revision']}:{name}"])
        if sha256(Path(name)) != digest or hashlib.sha256(blob).hexdigest() != digest:
            raise ValueError('待冻结执行代码已改变')
    for key in ('protocol', 'recovery_configuration', 'selected_configuration_source',
                'original_configuration', 'installed_dependencies'):
        checked_file(manifest[key])
    for name, digest in manifest['requirements_sha256'].items():
        if sha256(Path(name)) != digest:
            raise ValueError('依赖清单已改变')
    for case in manifest['cases']:
        for key in ('source', 'model', 'bytetrack_yaml', 'identity_evidence', 'supplemental_labels'):
            checked_file(case[key])
        for name, digest in case['baseline']['sha256'].items():
            if sha256(Path(case['baseline']['path']) / name) != digest:
                raise ValueError('待冻结缓存已改变')
    return {'checks_passed': True, 'status': manifest['status'], 'frozen': False,
            'note': '校验通过仅表示准备内容未改变，不表示已正式冻结。'}


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-freeze',type=Path,required=True)
    args=parser.parse_args()
    try: result=check_freeze_manifest(args.check_freeze)
    except (ValueError,OSError,KeyError,subprocess.CalledProcessError) as exc:
        parser.exit(1,f'待冻结清单核查失败: {exc}\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
