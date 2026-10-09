"""Prepare (never submit) identical full acceptance shards after historical gate."""
import json,subprocess,hashlib
from pathlib import Path
from transport import SSH_OPTIONS
D=Path(__file__).resolve().parent
supplement=D/'final-regression-gate.json'
if supplement.exists():
 assert json.loads(supplement.read_text())['passed'],'Post-validation contract regression is unresolved; no new inference staging authorized'
G=json.loads((D/'historical-gate.json').read_text())
assert G['passed'] and len(G['cases'])==8
gate=json.loads((D/'cpu-gate.json').read_text());assert gate['passed']
assert gate['application']=={str(p.relative_to(D/'application')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (D/'application').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
remote='/scratch/mohammedmubashir/resume-ai/work/semantic-contracts-20261008'
ssh=['ssh',*SSH_OPTIONS,'mohammedmubashir@turing.wpi.edu']
for i in range(3):
 name=f'full-v1-shard-{i}';target=remote+'/'+name
 script=f'''import pathlib,shutil
D=pathlib.Path({target!r});S=pathlib.Path({(remote+'/'+G['source_run'])!r})
D.mkdir()
for name in ['application','benchmark.json','stress-inputs.json','candidate_sources.json','embedding-records.json','candidate-vector-store','cpu-gate.json','controlled_reviews.py']:
 p=S/name
 if p.is_dir():shutil.copytree(p,D/name)
 else:shutil.copy2(p,D/name)
'''
 subprocess.run(ssh+['python3'],input=script,text=True,check=True)
 batch=(D/'historical-v7-shard-0.sbatch').read_text().replace('semantic-contracts-history','semantic-contracts-full').replace('historical-v7-shard-0',name).replace('historical-%j.log','full-%j.log').replace('export HISTORICAL_SHARD=0',f'export ACCEPTANCE_SHARD={i} ACCEPTANCE_SHARDS=3').replace('run_historical_shard.py','run_full_shard.py')
 batch=batch.replace('.venv/bin/python -B "$RESUME_REPAIR_RUN_DIR/run_full_shard.py"', '.venv/bin/python -B -c \'import json,pathlib,os; assert json.loads((pathlib.Path(os.environ["RESUME_REPAIR_RUN_DIR"])/"historical-gate.json").read_text())["passed"]\'\n.venv/bin/python -B "$RESUME_REPAIR_RUN_DIR/run_full_shard.py"')
 (D/(name+'.sbatch')).write_text(batch)
 subprocess.run(['scp','-q',*SSH_OPTIONS,str(D/'run_full_shard.py'),str(D/'historical-gate.json'),str(D/'completed-case-manifest.json'),str(D/(name+'.sbatch')),'mohammedmubashir@turing.wpi.edu:'+target+'/'],check=True)
 verify=(D/'verify_historical-v7-shard-0.py').read_text().replace('historical-v7-shard-0',name)
 (D/('verify_'+name+'.py')).write_text(verify)
 result=subprocess.run(ssh+['python3'],input=verify,text=True,capture_output=True,check=True)
 m=json.loads(result.stdout);local={str(p.relative_to(D/'application')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (D/'application').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 assert m['application']==local
 (D/(name+'-pre-manifest.json')).write_text(json.dumps(m,indent=2))
 print(name,'VERIFIED, NOT SUBMITTED',flush=True)
