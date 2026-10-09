"""CPU-only rescore from saved outputs using the run's frozen data and scorer.
Writes metrics.recomputed.json; refuses partial or duplicate case sets.
"""
import argparse,importlib.util,json,pathlib

def main():
 ap=argparse.ArgumentParser();ap.add_argument('run_dir',type=pathlib.Path);a=ap.parse_args();d=a.run_dir
 snapshot=d/'eval_snapshot'
 spec=importlib.util.spec_from_file_location('frozen_scorer',snapshot/'metrics/score.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 data=json.loads((snapshot/'datasets/resume_v1.json').read_text());schema=json.loads((snapshot/'schemas/analysis_v1.json').read_text())
 raw=[json.loads(x) for x in (d/'raw_outputs.jsonl').read_text().splitlines()]
 assert len(raw)==len(data['cases']) and {r['id'] for r in raw}=={c['id'] for c in data['cases']},'Missing, duplicate, or unexpected case IDs'
 lookup={r['id']:r for r in raw};rows=[]
 for c in data['cases']:
  try:p=json.loads(lookup[c['id']]['text']);ok=True
  except json.JSONDecodeError:p=None;ok=False
  r=module.score(c,p,schema);r.update(id=c['id'],json_valid=ok);rows.append(r)
 metrics=module.aggregate(rows)
 (d/'metrics.recomputed.json').write_text(json.dumps(metrics,indent=2)+'\n')
 original=json.loads((d/'metrics.json').read_text());assert metrics==original,'Recomputed metrics differ'
 print('Recomputed all cases; metrics exactly match saved metrics.')
if __name__=='__main__':main()
