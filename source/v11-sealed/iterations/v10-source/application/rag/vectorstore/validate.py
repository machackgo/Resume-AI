"""Stage 3D acceptance; never rewrites earlier-stage reports."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/stage3d'

def run():
    os.chdir(ROOT); commands={
        'stage3d_tests':['-m','unittest','discover','-s','tests/rag','-p','test_vectorstore*.py','-v'],
        'stage3c_tests':['-m','unittest','discover','-s','tests/rag','-p','test_embedding*.py','-v'],
        'stage3b_tests':['-m','unittest','discover','-s','tests/rag','-p','test_chunking.py','-v'],
        'stage3a_tests':['-m','unittest','discover','-s','tests/rag','-p','test_ingestion.py','-v'],
        'stage1_stage2_tests':['-m','unittest','discover','-s','eval/tests','-v'],
        'frozen_stage2_replay':['eval/runners/verify_stage2_run.py','results/prompt_engineered/grounded-v3-benchmark-2325384-1'],
        'stage3a_demo':['-m','rag.demo'],'stage3b_demo':['-m','rag.chunking.demo']}
    report={'checks':{},'test_counts':{}}
    for name,args in commands.items():
        proc=subprocess.run([sys.executable,'-B',*args],text=True,capture_output=True)
        (OUT/(name+'.log')).write_text(proc.stdout+proc.stderr)
        report['checks'][name]={'exit_code':proc.returncode,'command':[sys.executable,'-B',*args]}
        if name.endswith('_tests'):
            match=re.search(r'Ran (\d+) tests?',proc.stderr)
            report['test_counts'][name]=int(match[1]) if match else 0
        if name.endswith('_demo'):
            stage=name.split('_')[0]
            report['checks'][name]['frozen_equal']=proc.returncode==0 and json.loads(proc.stdout)==json.loads((ROOT/f'results/{stage}/demo.json').read_text())
    manifest=json.loads((OUT/'preexisting_manifest.json').read_text())
    changed=[k for k,v in manifest.items() if not (ROOT/k).is_file() or hashlib.sha256((ROOT/k).read_bytes()).hexdigest()!=v]
    report['preservation']={'files':len(manifest),'changed_or_missing':changed}
    # Include pinned model assets in the audit without re-running GPU or encoder benchmarks.
    locked=json.loads((ROOT/'results/stage3c/models.lock.json').read_text()); assets=0
    for spec in locked:
        folder=ROOT/'models/stage3c'/('models--'+spec['model'].replace('/','--'))/'snapshots'/spec['revision']
        for name,sha in spec['files_sha256'].items():
            assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==sha
            assets+=1
    report['pinned_model_assets_unchanged']=assets
    write=json.loads((OUT/'replay_write.json').read_text()); read=json.loads((OUT/'replay_read.json').read_text())
    report['persistence']={'writer_pid':write['process_id'],'reader_pid':read['process_id'],
        'separate_processes':write['process_id']!=read['process_id'],
        'experiments':len(read['experiments']),'queries':sum(x['queries'] for x in read['experiments']),
        'citation_roundtrips':sum(x['citation_roundtrips'] for x in read['experiments']),
        'maximum_score_delta':max(x['maximum_score_delta'] for x in read['experiments'])}
    report['test_counts']['total']=sum(report['test_counts'].values())
    report['passed']=not changed and all(v['exit_code']==0 and v.get('frozen_equal',True) for v in report['checks'].values()) and all(report['test_counts'].values()) and write['passed'] and read['passed'] and report['persistence']['separate_processes']
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
    if not report['passed']: raise SystemExit(1)

if __name__=='__main__': run()
