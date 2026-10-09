"""CPU-only remote acceptance runner; never rewrites previous-stage artifacts."""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/stage3b'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    os.chdir(ROOT)
    OUT.mkdir(exist_ok=True)
    if not (OUT/'preexisting_manifest.json').exists():
        raise RuntimeError('capture the pre-Stage-3B manifest before installation')
    report = {'python': sys.version, 'platform': platform.platform(), 'checks': {}, 'test_counts': {}}
    commands = {
        'stage3b_tests': ['-m','unittest','discover','-s','tests/rag','-p','test_chunking.py','-v'],
        'stage3a_tests': ['-m','unittest','discover','-s','tests/rag','-p','test_ingestion.py','-v'],
        'existing_tests': ['-m','unittest','discover','-s','eval/tests','-v'],
        'frozen_stage2_replay': ['eval/runners/verify_stage2_run.py',
                               'results/prompt_engineered/grounded-v3-benchmark-2325384-1'],
        'stage3a_demo_replay': ['-m','rag.demo'],
        'stage3b_demo': ['-m','rag.chunking.demo'],
    }
    for name,args in commands.items():
        command=[sys.executable,'-B',*args]
        run=subprocess.run(command,capture_output=True,text=True)
        (OUT/(name+'.log')).write_text(run.stdout+run.stderr)
        report['checks'][name]={'command':command,'exit_code':run.returncode}
        if name.endswith('_tests'):
            count = re.search(r'Ran (\d+) tests?', run.stderr)
            report['test_counts'][name.removesuffix('_tests')] = int(count[1]) if count else 0
        print(name,run.returncode,flush=True)
        if name=='stage3a_demo_replay' and run.returncode==0:
            report['stage3a_demo_equal']=json.loads(run.stdout)==json.loads((ROOT/'results/stage3a/demo.json').read_text())
        if name=='stage3b_demo' and run.returncode==0:
            demo=json.loads(run.stdout)
            (OUT/'demo.json').write_text(run.stdout)
            (OUT/'policy_comparison.json').write_text(json.dumps(demo['comparison'],indent=2)+'\n')
    # Different process hash seeds must reproduce every demo field, including IDs.
    hashes=[]
    for seed in ('0','713'):
        run=subprocess.run([sys.executable,'-B','-m','rag.chunking.demo'],capture_output=True,
                           env={**os.environ,'PYTHONHASHSEED':seed},check=True)
        hashes.append(hashlib.sha256(run.stdout).hexdigest())
    report['cross_process_demo_hashes']=hashes
    report['cross_process_deterministic']=len(set(hashes))==1
    report['preservation']={}
    for name,path in (('pre_stage3b',OUT/'preexisting_manifest.json'),
                      ('stage1_stage2',ROOT/'results/stage3a/preexisting_manifest.json')):
        manifest=json.loads(path.read_text())
        changed=[key for key,value in manifest.items() if not (ROOT/key).is_file() or sha(ROOT/key)!=value]
        report['preservation'][name]={'protected_files':len(manifest),'changed_or_missing':changed}
    report['test_counts']['total']=sum(report['test_counts'].values())
    report['artifact_hashes']={str(p.relative_to(ROOT)):sha(p) for p in
        sorted([* (ROOT/'rag/chunking').glob('*.py'), ROOT/'tests/rag/test_chunking.py',
                * (ROOT/'docs').glob('stage3b*.md'), OUT/'demo.json',OUT/'policy_comparison.json'])}
    report['passed']=(all(c['exit_code']==0 for c in report['checks'].values())
                      and all(report['test_counts'].values()) and report.get('stage3a_demo_equal',False) and report['cross_process_deterministic']
                      and all(not p['changed_or_missing'] for p in report['preservation'].values()))
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
