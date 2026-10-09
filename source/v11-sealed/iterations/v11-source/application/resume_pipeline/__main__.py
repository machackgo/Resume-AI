"""Single non-agent command, including structured initialization failures."""
import argparse,json,time
from pathlib import Path
from .runtime import load_kb,BaseQwen
from .pipeline import ResumePipeline,normalize_job

def main(argv=None):
    p=argparse.ArgumentParser(description='Non-agent grounded resume generation using approved frozen BASE Qwen')
    for name in ('root','kb','job-file','profile-file','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(argv)
    # Reserve a fresh result before expensive inference; never replace an artifact.
    try:destination=a.output.open('x')
    except OSError as error:p.error('cannot create fresh output: '+str(error))
    started=time.monotonic();stage='input';store=None
    try:
        profile=json.loads(a.profile_file.read_text());job=a.job_file.read_text()
        if not isinstance(profile,dict) or any(not isinstance(profile.get(k),str) or not profile[k].strip() for k in ('candidate_id','name')):
            raise ValueError('profile requires nonempty candidate_id and name')
        normalize_job(job)
        stage='knowledge_base';engine,ledger,store=load_kb(a.root,a.kb)
        stage='candidate_scope'
        if profile['candidate_id']!=store.scope.candidate_id:raise ValueError('foreign profile')
        stage='model_initialization';model=BaseQwen(a.root)
        stage='pipeline';result=ResumePipeline(engine,ledger,model,profile).run(job,profile['candidate_id'])
    except Exception as error:
        result=dict(status='FAILED',resume=None,model_called=False,compiler_valid=False,schema_valid=False,failure_stage=stage,error={'type':type(error).__name__,'message':str(error)},seconds=time.monotonic()-started)
    finally:
        if store is not None:store.close()
    with destination:json.dump(result,destination,indent=2)
    print(result['status'])
    return 0 if result['status']=='COMPLETE' else 1

if __name__=='__main__':raise SystemExit(main())
