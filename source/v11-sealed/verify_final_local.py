"""Read-only verification of every prior sealed local package and archive."""
import json,hashlib,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent;P=D.parent/'resume-ai-final-remediation-20261007'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8388608),b''):h.update(b)
 return h.hexdigest()
m=json.loads((P/'SHA256SUMS.json').read_text())['files']
if isinstance(m,list):m={x['path']:x['sha256'] for x in m}
else:m={k:(v['sha256'] if isinstance(v,dict) else v) for k,v in m.items()}
bad=[k for k,v in m.items() if not (P/k).exists() or sha(P/k)!=v]
archive=P.with_name(P.name+'-full-v7-final.zip');before=json.loads((D/'integrity-local-before.json').read_text())
def call(path):return json.loads(subprocess.run([sys.executable,str(path)],capture_output=True,text=True,check=True).stdout)
frozen=call(D.parent/'resume-ai-remediation-20261007/verify_local.py');history=call(P/'verify_local_history.py')
result=dict(prior_package_files=len(m),mismatches=bad,archive_sha256=sha(archive),archive_matches=sha(archive)==before['archive_sha256'],local_frozen=frozen,prior_history=history)
print(json.dumps(result,indent=2))
assert not bad and result['archive_matches'] and all(not v['mismatches'] for v in frozen.values()) and all(not v['mismatches'] for v in history)
