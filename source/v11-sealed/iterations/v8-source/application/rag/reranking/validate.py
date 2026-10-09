"""Regression and preservation checks; writes only Stage 3F outputs."""
import json
import re
import subprocess
import sys
from .prepare import ROOT, OUT, sha

def main(audit=True):
    checks={}; counts={}
    commands={'stage3_tests':['-m','unittest','discover','-s','tests/rag','-v'],
              'stage1_stage2_tests':['-m','unittest','discover','-s','eval/tests','-v'],
              'frozen_stage2_replay':['eval/runners/verify_stage2_run.py','results/prompt_engineered/grounded-v3-benchmark-2325384-1'],
              'stage3a_demo':['-m','rag.demo'], 'stage3b_demo':['-m','rag.chunking.demo']}
    for name,args in commands.items():
        p=subprocess.run([sys.executable,'-B',*args],cwd=ROOT,capture_output=True,text=True)
        (OUT/(name+'.log')).write_text(p.stdout+p.stderr); checks[name]=p.returncode==0
        if name.endswith('_tests'):
            m=re.search(r'Ran (\d+) tests?',p.stderr); counts[name]=int(m[1]) if m else 0
        if name.endswith('_demo') and p.returncode==0:
            checks[name]=json.loads(p.stdout)==json.loads((ROOT/('results/'+name.split('_')[0]+'/demo.json')).read_text())
    report={'checks':checks,'tests':counts,'total_tests':sum(counts.values())}
    if audit:
        manifest=json.loads((OUT/'preexisting_manifest.json').read_text())
        changed=[path for path,digest in manifest.items() if not (ROOT/path).is_file() or sha(ROOT/path)!=digest]
        assets=[path for path in manifest if path.startswith(('models/','hf-cache/'))]
        model_checks=[]
        for spec in json.loads((OUT/'models.lock.json').read_text()):
            folder=ROOT/'models/stage3f'/('models--'+spec['model'].replace('/','--'))/'snapshots'/spec['revision']
            model_checks.extend(sha(folder/name)==digest for name,digest in spec['files_sha256'].items())
        report.update(protected_files=len(manifest),protected_model_paths=len(assets),changed_or_missing=changed,
                      new_model_assets_unchanged=all(model_checks))
        checks['preservation']=not changed and all(model_checks)
    report['passed']=all(checks.values())
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    if not report['passed']: raise SystemExit(1)

if __name__=='__main__': main('--no-audit' not in sys.argv)
