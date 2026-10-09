import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'results/stage3e'
def main():
    os.chdir(ROOT); checks={}; counts={}
    commands={'stage3_tests':['-m','unittest','discover','-s','tests/rag','-v'],
      'stage1_stage2_tests':['-m','unittest','discover','-s','eval/tests','-v'],
      'frozen_stage2_replay':['eval/runners/verify_stage2_run.py','results/prompt_engineered/grounded-v3-benchmark-2325384-1'],
      'stage3a_demo':['-m','rag.demo'],'stage3b_demo':['-m','rag.chunking.demo']}
    for name,args in commands.items():
        p=subprocess.run([sys.executable,'-B',*args],capture_output=True,text=True)
        (OUT/(name+'.log')).write_text(p.stdout+p.stderr); checks[name]=p.returncode==0
        if name.endswith('_tests'):
            m=re.search(r'Ran (\d+) tests?',p.stderr); counts[name]=int(m[1]) if m else 0
        if name.endswith('_demo'): checks[name]=checks[name] and json.loads(p.stdout)==json.loads((ROOT/('results/'+name.split('_')[0]+'/demo.json')).read_text())
    manifest=json.loads((OUT/'preexisting_manifest.json').read_text())
    changed=[k for k,v in manifest.items() if not (ROOT/k).is_file() or hashlib.sha256((ROOT/k).read_bytes()).hexdigest()!=v]
    assets=0
    for spec in json.loads((ROOT/'results/stage3c/models.lock.json').read_text()):
        folder=ROOT/'models/stage3c'/('models--'+spec['model'].replace('/','--'))/'snapshots'/spec['revision']
        for name,sha in spec['files_sha256'].items():
            assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==sha; assets+=1
    out={'passed':all(checks.values()) and not changed,'checks':checks,'tests':counts,'total_tests':sum(counts.values()),'protected_files':len(manifest),'changed_or_missing':changed,'pinned_model_assets':assets}
    (OUT/'validation.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
    if not out['passed']: raise SystemExit(1)
if __name__=='__main__': main()
