"""Non-model probe: canonical candidates reaching semantic review, not licenses."""
import sys,json,os
from pathlib import Path
D=Path(os.environ['RESUME_REPAIR_RUN_DIR']);ROOT=Path('/scratch/mohammedmubashir/resume-ai')
sys.path.insert(0,str(D/'application'));sys.dont_write_bytecode=True
def guard(event,args):
 if event=='open' and isinstance(args[0],(str,bytes)):
  p=Path(os.fsdecode(args[0])).resolve()
  if any(p==ROOT/n or ROOT/n in p.parents for n in ['datasets','eval','fixtures','scenarios','research']) or any('heldout' in x.lower() or 'holdout' in x.lower() or x=='eval_snapshot' for x in p.parts):raise PermissionError('Protected content prohibited')
sys.addaudithook(guard)
from resume_pipeline.runtime import load_kb
from resume_pipeline.pipeline import requirements
from resume_pipeline.reselection import retrieved_pool
from resume_pipeline.fallback_retrieval import expand_retrieval
from resume_pipeline.semantic_policy import ranked_candidates
from resume_pipeline.semantic_contracts import *
from resume_pipeline.component_review import component_requirement
from resume_pipeline.licensing import review_sources
from rag.deep.raw import retrieve_text
engine,ledger,store=load_kb(ROOT,D);catalog=entity_catalog(ledger);out=[]
for n,text in enumerate(['Implemented a project with FastAPI.','Implemented PostgreSQL connectivity.','Process images using OpenCV.']):
 _,reqs,_=requirements(text,engine.retriever.provider)
 initial=[dict(requirement_id=r['requirement_id'],output=retrieve_text(engine,*ledger.scope.key,r['text'],r['requirement_id'])) for r in reqs]
 extra=expand_retrieval(engine,ledger.scope,reqs)
 deeper=expand_retrieval(engine,ledger.scope,reqs,80)
 for depth,rows in [(20,initial),(40,initial+extra),(80,initial+extra+deeper)]:
  units,by_req,ordered=retrieved_pool(rows,ledger);candidates=ranked_candidates(units,by_req,ordered,reqs,[],[],set());eligible=[]
  for candidate in candidates:
   if candidate['eligibility']['eligibility']=='C':continue
   unit=candidate['unit'];ident=unit['semantic_identity'];sources=review_sources(ledger,units,unit['text'],unit,text)
   for source in sources:source['positive_support_allowed']=same_support_entity(ident,source['semantic_identity'],catalog)
   for req in reqs:
    comp=component_requirement(req,unit['text']);tech=technology_license(comp['text'],unit['text'],(unit.get('source_context') or {}).get('text',''),sources)
    okay=identity_compatible(req['text'],ident,catalog)['compatible'] and event_scope_compatible(comp['text'],ident) and action_strength_compatible(comp['text'],unit['text']) and compatible(capability_types(comp['text']),ident['capability_types']) and tech['compatible']
    from resume_pipeline.semantic_contracts import unresolved_negative
    if unresolved_negative(unit['text'],ident,sources,catalog):okay=False
    if okay:eligible.append(dict(rank=candidate['rank'],claim=unit['text'],identity=ident,component=comp,technology_support=tech,decision='REQUIRES_INDEPENDENT_BASE_FACTUAL_AND_CONTENT_REVIEW'))
  out.append(dict(query=text,depth=depth,discovered_units=len(units),necessary_gate_survivors=eligible))
  print('PROBE',n,depth,'survivors',len(eligible),flush=True)
with (D/'cpu-retrieval-license-probe.json').open('x') as f:json.dump(dict(model_inference=False,not_acceptance_evidence=True,queries=out),f,indent=2)
store.close()
