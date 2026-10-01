"""离线评价的来源检查：使用对应 Git 快照核查历史结果，不改旧输出。"""

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

try:
    from .run_target_state import sha256, write_json
except ImportError:
    from run_target_state import sha256, write_json


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines()]


def historical_blob(revision, name):
    # 固定取 Git 对象，不用当前工作区代码代替运行版本。
    return subprocess.check_output(['git', 'show', f'{revision}:scripts/{name}'])


def verify_code(info, revision):
    resolved = subprocess.check_output(['git', 'rev-parse', '--verify', f'{revision}^{{commit}}'], text=True).strip()
    checks = {}
    for name, expected in info['code_sha256'].items():
        if Path(name).name != name or not name.endswith('.py'):
            raise ValueError('非法历史脚本名')
        actual = hashlib.sha256(historical_blob(resolved, name)).hexdigest()
        if actual != expected:
            raise ValueError(f'历史运行代码 SHA 不匹配: {name}')
        checks[name] = actual
    return {'resolved_revision': resolved, 'recorded_code_sha256_verified': checks}


def check_counts(info, rows, events):
    """从记录重算诊断计数；这些数字不作人工返回机会分母。"""
    start, end = info['config']['init_frame'], info['config']['end_frame_exclusive']
    if [r['frame_index'] for r in rows] != list(range(start, end)) or len(rows) != info['frames_processed']:
        raise ValueError('逐帧区间或次数不一致')
    states = dict(Counter(r['state'] for r in rows))
    losses = sorted({r['confirmed_lost_frame'] for r in rows if r['confirmed_lost_frame'] is not None})
    accepts = [e for e in events if e['event_type'] == 'RECOVERY_ACCEPTED']
    attempts = [e for e in events if e['event_type'] == 'RECOVERY_ATTEMPT_STARTED']
    actual = (states, len(losses), len(accepts), len(attempts), len(events))
    recorded = (info['state_frame_counts'], info['loss_episodes'], info['program_accepts'], info['recovery_attempts'], info['events'])
    if actual != recorded or sum(r['recovery_confirmed'] for r in rows) != len(accepts):
        raise ValueError('运行汇总与逐帧/事件次数不一致')
    if not info['recovery_enabled'] and (accepts or any(c['bound_to_target'] for r in rows for c in r['recovery_candidates'])):
        raise ValueError('关闭组出现绑定')
    return {'confirmed_loss_frames': losses, 'algorithm_confirmed_losses': len(losses),
            'program_accepts': len(accepts), 'confirmation_attempts': len(attempts), 'state_frame_counts': states}


def snapshot(paths):
    files = set()
    for path in paths:
        path = Path(path)
        if path.is_dir():
            files.update(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
        elif path.is_file():
            files.add(path)
    return {str(p): sha256(p) for p in sorted(files)}


def verify_snapshot(before):
    for path, expected in before.items():
        if sha256(path) != expected:
            raise ValueError(f'旧证据变化: {path}')


def run_historical_checks(run, destination, annotations=None):
    """历史核查脚本在临时副本写新报告；旧结果只读链接，绝不覆盖。"""
    output = Path(run['output'])
    info = read_json(output / 'run_info.json')
    provenance = verify_code(info, run['code_revision'])
    revision = provenance['resolved_revision']
    with tempfile.TemporaryDirectory(prefix='offline_evaluation_') as directory:
        root = Path(directory)
        scripts, review_output = root / 'scripts', root / 'run'
        scripts.mkdir()
        review_output.mkdir()
        names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision, 'scripts'], text=True).splitlines()
        scripts_sha = {}
        for path in names:
            if not path.endswith('.py'):
                continue
            blob = historical_blob(revision, Path(path).name)
            (scripts / Path(path).name).write_bytes(blob)
            scripts_sha[path] = hashlib.sha256(blob).hexdigest()
        # review([], ...) 只写 review/evaluation；其余数据均指向原始只读输入。
        for entry in output.iterdir():
            if entry.name not in ('review.json', 'evaluation.json'):
                (review_output / entry.name).symlink_to(entry.resolve(), target_is_directory=entry.is_dir())
        command = [sys.executable, str(scripts / 'review_recovery.py'), '--output', str(review_output)]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        review = read_json(review_output / 'review.json')
        keys = ('record_checks_passed', 'output_decoded_frames', 'original_output_files_preserved',
                'state_frame_counts', 'program_accepts', 'reference_frozen', 'disabled_matches_step1')
        checks = {key: review[key] for key in keys}
        # 关闭结果重新由当时 TargetState 回放，负例也不依赖旧 PASS 或空对照。
        if not info['recovery_enabled']:
            replay_code = '''
import json, sys
from pathlib import Path
from run_target_state import TargetState
p=Path(sys.argv[1]); info=json.loads((p/'run_info.json').read_text())
rows=[json.loads(l) for l in (p/'frames.jsonl').read_text().splitlines()]
base=[json.loads(l) for l in (Path(info['baseline'])/'frames.jsonl').read_text().splitlines()]
c=info['config']; machine=TargetState(base[c['init_frame']], c['init_box'], c['missing_frames'], c['init_iou'])
events=[]
for row in rows:
    expected,event=machine.step(base[row['frame_index']])
    if any(row[k]!=v for k,v in expected.items()): raise ValueError('关闭组未退回当时 TargetState')
    if event: events.append(dict(event,event_type='STATE_TRANSITION'))
actual=[json.loads(l) for l in (p/'events.jsonl').read_text().splitlines()]
if events!=actual: raise ValueError('关闭组事件不一致')
print(len(rows))
'''
            driver = scripts / 'replay_disabled.py'
            driver.write_text(replay_code, encoding='utf-8')
            replay = subprocess.run([sys.executable, str(driver), str(output)], capture_output=True, text=True, check=True)
            checks['historical_target_state_replayed_frames'] = int(replay.stdout.strip())
        if annotations is not None:
            report_path = destination / f"{run['run_id']}_raw_negative.json"
            validator = [sys.executable, str(scripts / 'validate_wrong_bottle.py'), '--output', str(output),
                         '--annotations', str(annotations), '--report', str(report_path)]
            subprocess.run(validator, capture_output=True, text=True, check=True)
            raw = read_json(report_path)
            checks['raw_pixel_recomputed_frames'] = raw['raw_pixel_evidence_recomputed_frames']
            checks['source_redecoded_frames'] = raw['source_redecoded_frames']
            checks['raw_report'] = str(report_path)
        provenance.update({'historical_scripts_sha256': scripts_sha, 'record_checks': checks,
                           'method': 'Git snapshot; unmodified recorded SHA; temporary review output; no legacy identity metrics imported'})
        write_json(destination / f"{run['run_id']}_source_checks.json", provenance)
    return provenance
