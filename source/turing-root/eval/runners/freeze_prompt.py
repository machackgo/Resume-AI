"""Freeze prompt and experiment code after smoke review, before benchmark."""
import argparse,datetime,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--version',choices=['grounded_v1','grounded_v2','grounded_v3'],required=True);ap.add_argument('--smoke-run',required=True);ap.add_argument('--review',required=True);a=ap.parse_args()
 run=ROOT/'results/prompt_engineered'/a.smoke_run;c=json.loads((run/'config.json').read_text());assert c['status']=='complete' and c['phase']=='smoke' and c['prompt_version']==a.version.replace('_','-')
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 for p in (ROOT/'eval/prompts'/a.version).glob('*.txt'):assert sha(p)==c['files'][str(p.relative_to(ROOT))]
 paths=[p for p in (ROOT/'eval').rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.suffix in ['.py','.txt','.json','.slurm','.sh'] and not p.name.startswith('freeze_')]
 out=ROOT/'eval/experiments/stage2'/('freeze_'+a.version+'.json')
 record={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prompt_version':a.version,'smoke_run':a.smoke_run,'smoke_raw_sha256':sha(run/'raw_outputs.jsonl'),'smoke_review':a.review,'smoke_review_sha256':sha(ROOT/a.review),'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'policy':'One full unchanged benchmark run; do not revise this prompt based on its outcomes.'}
 with out.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
 print(out)
if __name__=='__main__':main()
