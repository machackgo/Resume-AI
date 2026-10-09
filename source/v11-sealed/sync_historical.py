"""Download only complete parseable JSON artifacts; verify remote hashes."""
import subprocess,json,hashlib,sys,re
from pathlib import Path
from transport import SSH_OPTIONS
D=Path(__file__).resolve().parent;name=sys.argv[1]
assert re.fullmatch(r'(?:historical|full)-v[0-9]+(?:-shard-[0-9]+)?',name)
remote='/scratch/mohammedmubashir/resume-ai/work/semantic-contracts-20261008/'+name
script='''import pathlib,json,hashlib
D=pathlib.Path(%s);out={}
for p in sorted(D.glob('*.json')):
 if not (p.name.startswith(('case-J','stress-S','control-')) or p.name in ['controlled-review-results.json','production-model-configuration.json','e2e-error.json','e2e-execution.json','assigned-cases.json','reused-case-verification.json']):continue
 data=p.read_bytes()
 try:json.loads(data)
 except json.JSONDecodeError:continue
 out[p.name]=hashlib.sha256(data).hexdigest()
print(json.dumps(out))
'''%repr(remote)
m=json.loads(subprocess.run(['ssh',*SSH_OPTIONS,'mohammedmubashir@turing.wpi.edu','python3'],input=script,text=True,capture_output=True,check=True,timeout=60).stdout)
local=D/name;local.mkdir(exist_ok=True)
for f,h in m.items():
 target=local/f
 if not target.exists():subprocess.run(['scp','-q',*SSH_OPTIONS,'mohammedmubashir@turing.wpi.edu:'+remote+'/'+f,str(target)],check=True,timeout=60)
 assert hashlib.sha256(target.read_bytes()).hexdigest()==h,('download hash mismatch',f)
print(json.dumps({'verified_files':len(m),'cases':[f for f in m if f.startswith(('case-J','stress-S'))],'controls':{f:json.loads((local/f).read_text())['passed'] for f in m if f.startswith('control-')}},indent=2))
(D/(name+'-download-manifest.json')).write_text(json.dumps(m,indent=2))
