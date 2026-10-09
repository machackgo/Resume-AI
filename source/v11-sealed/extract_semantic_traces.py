"""Index actual execution traces without changing judgments or model evidence."""
import hashlib,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
run=D/sys.argv[1]
out=D/(sys.argv[1]+'-semantic-traces');out.mkdir(exist_ok=True)
for path in sorted([*run.glob('case-J*.json'),*run.glob('stress-S*.json')]):
 r=json.loads(path.read_text());batches=r.get('batches',[r])
 record={'case':r['id'],'source_artifact':str(path.relative_to(D)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'raw_job_sha256':r['raw_job_sha256'],'requirements':r['requirements'],'coverage':r.get('requirement_coverage'),'batches':[],'final_resume':r.get('resume')}
 for b in batches:
  record['batches'].append({k:b.get(k) for k in ['requirements','retrieval','bounded_context','model_messages','inference','initial_selection_valid','requirement_results','claim_reviews','fallback_pool','fallback_attempts','fallback_selection_trace','fallback_retrieval_expansions','safe_omissions','failure_stage','error']})
 target=out/(r['id']+'.json')
 data=json.dumps(record,indent=2)
 if target.exists():assert target.read_text()==data,'Attempted to change an existing trace'
 else:target.write_text(data)
print('Indexed',len(list(out.glob('*.json'))),'case traces')
