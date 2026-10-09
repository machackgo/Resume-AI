"""Freeze reviewed factory inputs before full generation, never freeze a dataset."""
import argparse,datetime,json
from pathlib import Path
from .io import read_json,read_jsonl,sha_file,write_json,strict_json
from . import contracts

def freeze(root,records,audit,paths,out):
    rows=read_jsonl(records);report=read_json(audit)
    if not report.get('passed') or report.get('records_file_sha256')!=sha_file(records):raise ValueError('complete bound pilot validation required')
    if not report.get('tokenizer_fingerprint',{}).get('files'):raise ValueError('real tokenizer fingerprint required')
    if not report.get('historical_exclusion',{}).get('passed') or not report.get('provenance_validation_executed'):raise ValueError('pilot provenance and exclusion required')
    tasks={r['metadata']['task'] for r in rows}
    if tasks!=set(contracts.TASKS):raise ValueError('pilot task coverage incomplete')
    if not any(r['metadata']['task']=='GENERATE_RESUME' and strict_json(r['messages'][-1]['content'])['status']=='COMPLETE' for r in rows):raise ValueError('complete whole resume pilot required')
    snapshots={}
    for directory in ['stage4c0','research/stage4c0','contracts']:
        for p in sorted((root/directory).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.json','.jsonl','.txt','.md','.slurm']:
                snapshots[str(p.relative_to(root))]=sha_file(p)
    for p in paths:snapshots[str(p.relative_to(root))]=sha_file(p)
    result={'version':'stage4c0-data-factory-v2','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'factory_frozen':True,'dataset_frozen':False,'teacher_prompt_version':'teacher.v2','critic_prompt_version':'critic.v1','schema_rubric_version':contracts.VERSION,'pilot_records_sha256':sha_file(records),'pilot_validation_sha256':sha_file(audit),'pilot_accepted_unique':len(rows),'pilot_tasks':sorted(tasks),'sha256':snapshots,'scope':'Freeze of generator/contracts/validators and input snapshot before prospective full generation; not a training authorization.','training_allowed':False,'supersedes_factory_v1':True,'prior_snapshot_sha256':sha_file(root/'work/factory-freeze-v1.json'),'prior_source_archive_sha256':sha_file(root/'work/factory-v1-archived-source.tar.gz'),'change_scope':'Validator education credential field compatibility, bounded instrument/education-noun action disambiguation, compositional nonfactual invitation grammar, exact-message-bound token preflight, and synthetic-history origin projection. Teacher/critic contracts, groundtruth, research and quality thresholds unchanged. Saved targets revalidated.'}
    write_json(out,result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--records',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('inputs',type=Path,nargs='+');a=p.parse_args()
    x=freeze(a.root.resolve(),a.records,a.audit,[x.resolve() for x in a.inputs],a.out);print(json.dumps({'files':len(x['sha256']),'pilot':x['pilot_accepted_unique']}))
