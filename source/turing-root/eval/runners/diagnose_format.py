"""Secondary formatting diagnostic. Never replaces strict baseline metrics.
Only remove a single complete Markdown JSON fence; do not repair JSON.
"""
import argparse,importlib.util,json,pathlib,re

def main():
 ap=argparse.ArgumentParser();ap.add_argument('run_dir',type=pathlib.Path);a=ap.parse_args();d=a.run_dir;snapshot=d/'eval_snapshot'
 spec=importlib.util.spec_from_file_location('scorer',snapshot/'metrics/score.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 data=json.loads((snapshot/'datasets/resume_v1.json').read_text());schema=json.loads((snapshot/'schemas/analysis_v1.json').read_text());cases={c['id']:c for c in data['cases']}
 records=[json.loads(x) for x in (d/'raw_outputs.jsonl').read_text().splitlines()];rows=[];predictions=[];confusion={};diffs=[]
 for r in records:
  text=r['text'].strip();match=re.fullmatch(r'```(?:json)?\s*\n(.*)\n```',text,re.S);recovered=bool(match)
  if recovered:text=match.group(1)
  try:p=json.loads(text);ok=True
  except json.JSONDecodeError:p=None;ok=False
  c=cases[r['id']];row=module.score(c,p,schema);row.update(id=r['id'],json_valid=ok);rows.append(row);predictions.append(dict(id=r['id'],fence_removed=recovered,prediction=p))
  if module.valid(p,schema):
   for field,key in [('claims','id'),('matches','requirement')]:
    actual={x[key]:x for x in p[field]}
    for expected in c['gold'][field]:
     pred=actual.get(expected[key],{});pair=expected['label']+' -> '+pred.get('label','MISSING');confusion[pair]=confusion.get(pair,0)+1
     if pred.get('label')!=expected['label'] or set(pred.get('evidence_ids',[]))!=set(expected['evidence_ids']):diffs.append(dict(case=r['id'],field=field,expected=expected,actual=pred))
 result=module.aggregate(rows);result.update(warning='SECONDARY diagnostic after fence removal. Strict original metrics remain authoritative.',confusion=confusion,differences=diffs)
 (d/'format_diagnostic_metrics.json').write_text(json.dumps(result,indent=2)+'\n');(d/'format_diagnostic_predictions.json').write_text(json.dumps(predictions,indent=2)+'\n');print(json.dumps(result['deterministic'],indent=2))
if __name__=='__main__':main()
