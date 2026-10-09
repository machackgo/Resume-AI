"""CPU counterfactual replay: contract vetoes only, never fresh model evidence."""
import sys,json
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D/'application'));sys.dont_write_bytecode=True
from resume_pipeline.runtime import CaptureAdapter
from resume_pipeline.semantic_contracts import *
from resume_pipeline.component_review import component_requirement
from rag.domain import Scope
from rag.ingestion import MemoryLedger
from rag.component.decompose import RequirementDecomposer
from rag.retrieval import InformationNeed,NeedType
canonical=json.loads((D/'inputs/canonical-evidence.json').read_text());ledger=MemoryLedger().for_candidate(Scope(**canonical[0]['scope']));ledger.review_evidence=[]
for source in json.loads((D/'inputs/candidate_sources.json').read_text()):ledger.review_evidence.append(ledger.ingest(CaptureAdapter(source)).evidence)
catalog=entity_catalog(ledger);rows=[]
for f in sorted((D/'forensics').glob('*.json')):
 saved=json.loads(f.read_text());r=saved['execution'];provenance=dict(r.get('bounded_context',{}).get('provenance',{}))
 for fallback in r.get('fallback_attempts',[]):provenance.update(fallback.get('bounded_context',{}).get('provenance',{}))
 reqs={x['requirement_id']:x for x in r['requirements']};proposals=[]
 for review in r.get('claim_reviews',[]):
  q=review.get('quote',{});p=provenance.get(q.get('evidence_id'))
  if not p:continue
  unit=next((u for u in p['allowed_quotes'] if u['text']==q.get('quote')),None)
  if not unit:continue
  i=identity(p['reference'],unit,ledger.evidence(p['reference']['evidence_id']))
  links=[]
  for rid in q['requirement_ids']:
   req=reqs[rid];component=component_requirement(req,q['quote'])
   links.append(dict(requirement_id=rid,identity=identity_compatible(req['text'],i,catalog),original_relationship=relationship(req['text'],rid),component=component,capability_compatible=compatible(capability_types(component['text']),i['capability_types'])))
  proposals.append(dict(quote=q,identity=i,achievement=achievement(q['quote']),links=links,prior_accepted=review.get('accepted')))
 decompositions=[__import__('dataclasses').asdict(RequirementDecomposer().decompose(InformationNeed(NeedType.JOB_REQUIREMENT,q['text'],q['requirement_id']))) for q in reqs.values()]
 rows.append(dict(case=r['id'],proposals=proposals,new_decomposition=decompositions))
(D/'historical-contract-replay.json').write_text(json.dumps(dict(kind='CPU counterfactual, not fresh inference',cases=rows),indent=2))
(D/'derived-entity-catalog.json').write_text(json.dumps(dict(source='Approved canonical source metadata and headings',names=catalog),indent=2))
for row in rows:
 bad=[p for p in row['proposals'] if p['prior_accepted'] and (p['achievement']['standalone'] is False or any(not l['identity']['compatible'] or not l['capability_compatible'] for l in p['links']))]
 print(row['case'],'prior accepted assertions with new vetoes',len(bad))
