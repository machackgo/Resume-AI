"""CPU-only read-only verification of a smoke or benchmark run's frozen scorer."""
import argparse,hashlib,importlib.util,json,pathlib,sys
sys.dont_write_bytecode=True

def main():
 ap=argparse.ArgumentParser();ap.add_argument('run',type=pathlib.Path);a=ap.parse_args();run=a.run
 cfg=json.loads((run/'config.json').read_text());assert cfg['status']=='complete'
 snap=run/'eval_snapshot'
 for name,digest in cfg['files'].items():assert hashlib.sha256((snap/pathlib.Path(name).relative_to('eval')).read_bytes()).hexdigest()==digest,name
 dataset=pathlib.Path(cfg.get('dataset_path','eval/datasets/resume_v1.json')).relative_to('eval')
 data=json.loads((snap/dataset).read_text());schema=json.loads((snap/'schemas/analysis_v1.json').read_text())
 spec=importlib.util.spec_from_file_location('frozen_scorer',snap/'metrics/score.py');scorer=importlib.util.module_from_spec(spec);spec.loader.exec_module(scorer)
 raw=[json.loads(x) for x in (run/'raw_outputs.jsonl').read_text().splitlines()];saved=[json.loads(x) for x in (run/'predictions.jsonl').read_text().splitlines()]
 assert len(raw)==len(saved)==len(data['cases']);assert [x['id'] for x in raw]==[c['id'] for c in data['cases']]==[x['id'] for x in saved]
 rows=[]
 for c,r,s in zip(data['cases'],raw,saved):
  try:p=json.loads(r['text']);error=None
  except json.JSONDecodeError as e:p=None;error=str(e)
  assert p==s['prediction'] and error==s['parse_error']
  row=scorer.score(c,p,schema);row.update(id=c['id'],json_valid=error is None);rows.append(row)
 assert scorer.aggregate(rows)==json.loads((run/'metrics.json').read_text())
 print(json.dumps({'run':str(run),'cases':len(rows),'source_hashes_match':True,'strict_predictions_match_raw':True,'strict_metrics_reproduced':True}))
if __name__=='__main__':main()
