"""Preserve completed run logs/harnesses; never overwrite changed evidence."""
import json,hashlib,subprocess,re,sys
from pathlib import Path
from transport import SSH_OPTIONS
D=Path(__file__).resolve().parent;name=sys.argv[1]
assert re.fullmatch(r'(?:historical|full)-v[0-9]+(?:-shard-[0-9]+)?',name)
remote='/scratch/mohammedmubashir/resume-ai/work/semantic-contracts-20261008/'+name
ssh=['ssh',*SSH_OPTIONS,'mohammedmubashir@turing.wpi.edu']
script=f'''import pathlib,hashlib,json
D=pathlib.Path({remote!r});out={{}}
for p in sorted(D.iterdir()):
 if p.is_file() and (p.suffix in ['.log','.sbatch','.py'] or p.name in ['case-results.json','stress-results.json','cpu-gate.json','historical-gate.json']):out[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
print(json.dumps(out))
'''
m=json.loads(subprocess.run(ssh+['python3'],input=script,text=True,capture_output=True,check=True,timeout=60).stdout)
local=D/'remote-run-auxiliary'/name;local.mkdir(parents=True,exist_ok=True)
for f,h in m.items():
 p=local/f
 if not p.exists():subprocess.run(['scp','-q',*SSH_OPTIONS,'mohammedmubashir@turing.wpi.edu:'+remote+'/'+f,str(p)],check=True,timeout=60)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==h,('Changed or incomplete auxiliary evidence',name,f)
target=local/'transfer-verification.json';data=json.dumps(dict(remote=remote,files=m,verified=True),indent=2)
if target.exists():assert target.read_text()==data
else:target.write_text(data)
print(name,len(m),'verified auxiliary files')
