"""Stage a new historical revision, preserving all prior run directories."""
import json,subprocess,hashlib,sys,re
from pathlib import Path
D=Path(__file__).resolve().parent;rev=sys.argv[1]
supplement=D/'final-regression-gate.json'
if supplement.exists():
 assert json.loads(supplement.read_text())['passed'],'Post-validation contract regression is unresolved; no new inference staging authorized'
assert re.fullmatch(r'v[0-9]+',rev)
gate=json.loads((D/'cpu-gate.json').read_text());assert gate['passed']
assert gate['application']=={str(p.relative_to(D/'application')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (D/'application').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
remote='/scratch/mohammedmubashir/resume-ai/work/semantic-contracts-20261008'
ssh=['ssh','-o','BatchMode=yes','mohammedmubashir@turing.wpi.edu']
for i in range(2):
 name=f'historical-{rev}-shard-{i}';target=remote+'/'+name
 script=f'''import pathlib,shutil
D=pathlib.Path({target!r});S=pathlib.Path({(remote+'/historical-v7-shard-0')!r})
D.mkdir()
for name in ['benchmark.json','stress-inputs.json','candidate_sources.json','embedding-records.json','candidate-vector-store']:
 p=S/name
 if p.is_dir():shutil.copytree(p,D/name)
 else:shutil.copy2(p,D/name)
'''
 subprocess.run(ssh+['python3'],input=script,text=True,check=True)
 subprocess.run(['rsync','-a','--exclude=__pycache__','-e','ssh -o BatchMode=yes',str(D/'application')+'/','mohammedmubashir@turing.wpi.edu:'+target+'/application/'],check=True)
 batch=(D/f'historical-v7-shard-{i}.sbatch').read_text().replace(f'historical-v7-shard-{i}',name)
 (D/(name+'.sbatch')).write_text(batch)
 subprocess.run(['scp','-q','-o','BatchMode=yes',str(D/'run_historical_shard.py'),str(D/'controlled_reviews.py'),str(D/'cpu-gate.json'),str(D/(name+'.sbatch')),'mohammedmubashir@turing.wpi.edu:'+target+'/'],check=True)
 verify=(D/'verify_historical-v7-shard-0.py').read_text().replace('historical-v7-shard-0',name)
 (D/('verify_'+name+'.py')).write_text(verify)
 result=subprocess.run(ssh+['python3'],input=verify,text=True,capture_output=True,check=True)
 m=json.loads(result.stdout);local={str(p.relative_to(D/'application')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (D/'application').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 assert m['application']==local
 (D/(name+'-pre-manifest.json')).write_text(json.dumps(m,indent=2))
 print(name,'VERIFIED, NOT SUBMITTED',flush=True)
