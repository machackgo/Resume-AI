"""Validate a blinded review; preserve factual/constraint distinctions."""
import json,sys,hashlib
from pathlib import Path
from stage4c1.selection import professional_review
packet_path,review_path,out_path=map(Path,sys.argv[1:4])
packet=json.loads(packet_path.read_text());review=json.loads(review_path.read_text())
assert all(isinstance(x.get('constraint_violations'),list) and all(isinstance(v,str) and v.strip() for v in x['constraint_violations']) for x in review['cases']), 'explicit constraint review required'
s=professional_review(packet,review)
s['hard_constraint_violation_cases']=sum(bool(x.get('constraint_violations',[])) for x in review['cases'])
s['factual_critical_violation_cases']=s['critical_violation_cases']
# User constraints are second in the authorized truth hierarchy. This supplements
# automatic artifact checks without relabeling a pure constraint failure as fact.
if s['hard_constraint_violation_cases']:s['grounding_safe']=False
s['source_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (packet_path,review_path)}
assert not out_path.exists();out_path.write_text(json.dumps(s,indent=2)+'\n')
print(json.dumps({k:s[k] for k in ('n','quality_mean','grounding_safe','factual_critical_violation_cases','hard_constraint_violation_cases')}))
