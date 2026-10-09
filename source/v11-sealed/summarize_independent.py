"""Validate independent claim decisions against complete raw cohorts; no inferred labels."""
import json,hashlib,sys,collections
from pathlib import Path
D=Path(__file__).resolve().parent;cohort=sys.argv[1]
manifest=json.loads((D/cohort/'cohort-manifest.json').read_text())
decisions=json.loads((D/(cohort+'-independent-decisions.json')).read_text())
assert set(decisions)=={r['case'] for r in manifest['cases']}
counts={k:collections.Counter() for k in ['factual_class','content_class','identity_class','capability_class']};rows=[]
for entry in manifest['cases']:
 p=D/cohort/Path(entry['source']).name;r=json.loads(p.read_text());d=decisions[r['id']]
 assert d['raw_sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
 claims={c['claim_id']:c for s in (r.get('resume') or {}).get('sections',[]) for c in s['claims']}
 assert set(claims)=={c['claim_id'] for c in d['claims']}
 assert d.get('rationale') and 'case_passed' in d
 for c in d['claims']:
  assert c.get('rationale')
  for dim in counts:counts[dim][c[dim]]+=1
 rows.append(dict(case=r['id'],status=r['status'],claims=len(claims),passed=d['case_passed'],rationale=d['rationale']))
result=dict(cohort=cohort,cases=rows,dimensions={k:dict(v) for k,v in counts.items()},all_cases_passed=all(x['passed'] for x in rows),independent_audit_complete=True,method='Assistant independently reviewed canonical source spans, full requirement/component lineage, contrary evidence, and actual license trace; no labels copied from model self-assessment.')
with (D/(cohort+'-independent-audit.json')).open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
