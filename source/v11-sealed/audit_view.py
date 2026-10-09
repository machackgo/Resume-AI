"""Human review view of final substantive claims and accepted licenses."""
import json,sys,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
sources={s['id']:s for s in json.loads((D/'inputs/candidate_sources.json').read_text())}
evidence={e['source_id']:e for e in json.loads((D/'inputs/canonical-evidence.json').read_text())}
for arg in sys.argv[1:]:
 p=D/arg;r=json.loads(p.read_text());print('\nCASE',r['id'],'STATUS',r['status'],'RAW SHA',hashlib.sha256(p.read_bytes()).hexdigest())
 print('REQUIREMENTS',json.dumps(r['requirements']))
 claims=[c for s in (r.get('resume') or {}).get('sections',[]) for c in s['claims']]
 for c in claims:
  print('\nCLAIM',json.dumps(c,indent=2))
  e=evidence[c['source_id']];s=sources[json.loads(e['metadata_json'])['id']]['text'].replace('\r\n','\n').replace('\r','\n');a,b=c['span']
  print('SOURCE WINDOW',repr(s[max(0,a-500):min(len(s),b+500)]))
  for batch in r.get('batches',[r]):
   for v in batch.get('claim_reviews',[]):
    if v.get('quote',{}).get('quote')==c['text'] and v.get('accepted'):
     print('ACCEPTED REVIEW',json.dumps({k:v.get(k) for k in ['support','eligibility','reason','links','semantic_license','semantic_identity','component_requirements','relationship_licenses','identity_checks']},indent=2))
 print('OMISSIONS',json.dumps(r.get('requirement_coverage')))
 if not claims:print('ERROR',r.get('error'))
 for batch in r.get('batches',[r]):
  print('FALLBACK POOL',batch.get('fallback_pool'))
  for v in batch.get('claim_reviews',[]):
   print('REVIEW SUMMARY',json.dumps({k:v.get(k) for k in ['accepted','quote','support','eligibility','reason','semantic_identity','link_only_rejection']},default=str))
