"""Concise independent-review material; never assigns support labels."""
import json,hashlib,sys
from pathlib import Path
D=Path(__file__).resolve().parent
sources={s['id']:s for s in json.loads((D/'inputs/candidate_sources.json').read_text())}
evidence={e['source_id']:e for e in json.loads((D/'inputs/canonical-evidence.json').read_text())}
for arg in sys.argv[1:]:
 p=D/arg;r=json.loads(p.read_text());print('\nCASE',r['id'],'STATUS',r['status'],'SHA',hashlib.sha256(p.read_bytes()).hexdigest(),'ERROR',r.get('error'))
 print('REQUIREMENTS',[(q['requirement_id'],q['text']) for q in r['requirements']])
 claims=[c for s in (r.get('resume') or {}).get('sections',[]) for c in s['claims']]
 for c in claims:
  print('CLAIM',c['claim_id'],c['text']);print('IDENTITY',c['semantic_identity']);print('SPAN',c['source_id'],c['span'],'ATTRIBUTION',c['attribution'])
  e=evidence[c['source_id']];t=sources[json.loads(e['metadata_json'])['id']]['text'].replace('\r\n','\n').replace('\r','\n');a,b=c['span'];print('CANONICAL_CONTEXT',repr(t[max(0,a-250):min(len(t),b+250)]))
  print('LICENSES',c.get('licensed_relationships'))
 for b in r.get('batches',[r]):
  print('FALLBACK',b.get('fallback_pool'))
  for v in b.get('claim_reviews',[]):
   if v.get('accepted') or v.get('support') in ['CONTRADICTED','PARTIALLY_SUPPORTED']:
    print('REVIEW',v.get('accepted'),v.get('support'),v.get('quote',{}).get('quote'),v.get('reason'),v.get('links'))
 print('COVERAGE',[(x['requirement_id'],x['status'],x.get('omitted')) for x in r.get('requirement_coverage',[])])
