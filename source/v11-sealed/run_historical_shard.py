import os,sys,json,traceback
from pathlib import Path
ROOT=Path('/scratch/mohammedmubashir/resume-ai');D=Path(os.environ.get('RESUME_REPAIR_RUN_DIR',str(ROOT/'work/repair-acceptance-20261007')));sys.path.insert(0,str(D/'application'));sys.dont_write_bytecode=True
protected=[ROOT/p for p in ('datasets','eval','fixtures','scenarios','research')];denied=[]
def guard(event,args):
 if event=='open' and isinstance(args[0],(str,bytes)):
  p=Path(os.fsdecode(args[0])).resolve()
  if any(p==r or r in p.parents for r in protected) or any('heldout' in x.lower() or 'holdout' in x.lower() or x=='eval_snapshot' for x in p.parts):
   denied.append(str(p));raise PermissionError('Protected content prohibited')
sys.addaudithook(guard)
def put(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2,default=str)
try:
 from resume_pipeline.runtime import load_kb,BaseQwen
 from resume_pipeline.pipeline import ResumePipeline
 engine,ledger,store=load_kb(ROOT,D)
 model=BaseQwen(ROOT);put('production-model-configuration.json',model.configuration)
 from controlled_reviews import run as controls
 control_results=controls(model);put('controlled-review-results.json',control_results)
 if not all(r['passed'] for r in control_results):raise RuntimeError('Targeted semantic controls failed; full suite not started')
 profile={'candidate_id':engine.retriever.store.scope.candidate_id,'name':'Mohammed Mubashir Uddin Faraz'}
 pipeline=ResumePipeline(engine,ledger,model,profile)
 all_cases=[c for c in json.loads((D/'benchmark.json').read_text())['cases'] if c['id'] in {'J20','J08','J14','J09','J12','J15'}]
 all_stress=[c for c in json.loads((D/'stress-inputs.json').read_text()) if c['id'] in {'S07','S05'}]
 shard=int(os.environ['HISTORICAL_SHARD']);shards=2
 if shard not in (0,1):raise ValueError('Invalid historical shard')
 import hashlib
 put('assigned-cases.json',dict(shard=shard,shards=shards,cases=[dict(id=c['id'],raw_job_sha256=hashlib.sha256(c['job_text'].encode()).hexdigest()) for i,c in enumerate(all_cases+all_stress) if i%shards==shard]))
 cases=[c for i,c in enumerate(all_cases) if i%shards==shard];out=[]
 for case in cases:
  result=pipeline.run(case['job_text'],profile['candidate_id']);result.update(id=case['id'],title=case['title']);put('case-'+case['id']+'.json',result)
  out.append(result);print('CASE',case['id'],result['status'],result.get('failure_stage'),result.get('error'),flush=True)
 put('case-results.json',out)
 stress=[c for i,c in enumerate(all_stress,start=len(all_cases)) if i%shards==shard];out=[]
 for case in stress:
  result=pipeline.run(case['job_text'],profile['candidate_id']);result.update(id=case['id'],category=case['category']);put('stress-'+case['id']+'.json',result);out.append(result)
  print('STRESS',case['id'],result['status'],result.get('failure_stage'),flush=True)
 put('stress-results.json',out);put('e2e-execution.json',dict(job=os.environ.get('SLURM_JOB_ID'),denied_protected_opens=denied,training=False,adapter_promoted=False));store.close()
except Exception:
 put('e2e-error.json',dict(error=traceback.format_exc(),denied_protected_opens=denied));raise
