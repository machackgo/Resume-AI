"""Manifest only this new remediation. Never alter prior evidence."""
import hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent;P=D.parent/'resume-ai-final-remediation-20261007'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8388608),b''):h.update(block)
 return h.hexdigest()
changed=[]
for p in sorted((D/'application').rglob('*')):
 if not p.is_file() or '__pycache__' in p.parts:continue
 rel=p.relative_to(D);old=P/rel
 if not old.exists() or sha(p)!=sha(old):changed.append(dict(path=str(rel),before_sha256=sha(old) if old.exists() else None,after_sha256=sha(p)))
(D/'changed-file-manifest.json').write_text(json.dumps(changed,indent=2))
inputs={str(p.relative_to(D/'inputs')):dict(sha256=sha(p),unchanged=sha(p)==sha(P/'inputs'/p.relative_to(D/'inputs'))) for p in (D/'inputs').rglob('*') if p.is_file()}
assert all(x['unchanged'] for x in inputs.values())
(D/'input-integrity.json').write_text(json.dumps(inputs,indent=2))
print('Changed files:',len(changed),'unchanged input files:',len(inputs))
