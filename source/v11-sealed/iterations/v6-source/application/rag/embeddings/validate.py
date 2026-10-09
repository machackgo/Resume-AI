"""CPU-only acceptance and frozen-vector replay; writes only Stage 3C outputs."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from .evaluation import evaluate
from .similarity import cosine

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/stage3c'


def main():
    os.chdir(ROOT)
    report={'checks':{},'test_counts':{},'preservation':{}}
    commands={
        'stage3c_tests':['-m','unittest','discover','-s','tests/rag','-p','test_embedding*.py','-v'],
        'stage3b_tests':['-m','unittest','discover','-s','tests/rag','-p','test_chunking.py','-v'],
        'stage3a_tests':['-m','unittest','discover','-s','tests/rag','-p','test_ingestion.py','-v'],
        'stage1_stage2_tests':['-m','unittest','discover','-s','eval/tests','-v'],
        'frozen_stage2_replay':['eval/runners/verify_stage2_run.py','results/prompt_engineered/grounded-v3-benchmark-2325384-1'],
        'stage3a_demo':['-m','rag.demo'],'stage3b_demo':['-m','rag.chunking.demo']}
    for name,args in commands.items():
        command=[sys.executable,'-B',*args]
        run=subprocess.run(command,capture_output=True,text=True)
        (OUT/(name+'.log')).write_text(run.stdout+run.stderr)
        report['checks'][name]={'command':command,'exit_code':run.returncode}
        if name.endswith('_tests'):
            count=re.search(r'Ran (\d+) tests?',run.stderr)
            report['test_counts'][name]=int(count[1]) if count else 0
        if name.endswith('_demo'):
            stage=name.split('_')[0]
            report['checks'][name]['frozen_equal']=run.returncode==0 and json.loads(run.stdout)==json.loads((ROOT/f'results/{stage}/demo.json').read_text())
    for stage in ('stage3a','stage3b','stage3c'):
        manifest=json.loads((ROOT/f'results/{stage}/preexisting_manifest.json').read_text())
        changed=[key for key,value in manifest.items() if not (ROOT/key).is_file() or hashlib.sha256((ROOT/key).read_bytes()).hexdigest()!=value]
        report['preservation'][stage]={'protected_files':len(manifest),'changed_or_missing':changed}
    replay=[]
    for model in (0,1):
        result=json.loads((OUT/f'model{model}-evaluation.json').read_text())
        for experiment in result['experiments']:
            path=OUT/experiment['artifact']; payload=json.loads(path.read_text())
            assert hashlib.sha256(path.read_bytes()).hexdigest()==experiment['artifact_sha256']
            owner={c['chunk_id']:c['source_fixture_id'] for c in payload['chunk_manifest']}
            for q,qv,expected in zip(payload['queries'],payload['query_vectors'],experiment['queries']):
                best={}
                for rec in payload['records']:
                    key=owner[rec['chunk_id']]; score=cosine(qv,rec['vector'])
                    if key not in best or (-score,rec['chunk_id'])<(-best[key][0],best[key][1]['chunk_id']): best[key]=(score,rec)
                actual=evaluate([q],[qv],[(key,pair[1]['vector']) for key,pair in best.items()])['queries'][0]
                for field in ('recall_at_1','recall_at_3','mrr','hard_negative_win_rate','positive_similarity','hard_negative_similarity','margin'):
                    assert actual[field]==expected[field],field
                assert [r['id'] for r in actual['ranking']]==[r['id'] for r in expected['ranking']]
            replay.append(experiment['artifact'])
    report['frozen_vector_replay']={'experiments':len(replay),'queries':len(replay)*22,'passed':True}
    report['test_counts']['total']=sum(report['test_counts'].values())
    report['passed']=(all(c['exit_code']==0 and c.get('frozen_equal',True) for c in report['checks'].values())
        and all(not p['changed_or_missing'] for p in report['preservation'].values())
        and all(report['test_counts'].values()))
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__': raise SystemExit(main())
