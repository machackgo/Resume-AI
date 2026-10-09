"""Prepare bounded VALIDATION teacher packets; never reads final exam files."""
import json,collections,sys
from pathlib import Path
from stage4c1.evaluate import write,sha
R=Path.cwd()
def taxonomy(s):
 cats=set()
 if not s['schema_valid']:cats.add('SCHEMA')
 for e in s.get('errors',[]):
  if 'NUMERIC' in e:cats.add('NUMERIC_GROUNDING')
  elif 'TECH' in e:cats.add('ADJACENT_TECHNOLOGY')
  elif 'ACTION' in e:cats.add('ACTION_STRENGTH')
  elif 'CITATION' in e or 'EVIDENCE_ID' in e or e in ['unknown_or_foreign_id','quote_not_exact','quote_coverage','citation_union','missing_citation']:cats.add('CITATION_ENTAILMENT')
  elif 'USER_INPUT' in e or 'STATUS' in e:cats.add('USER_INPUT_REQUIRED')
  elif 'SECTION' in e:cats.add('ATS_STRUCTURE')
  elif 'WORD_LIMIT' in e or 'CHARACTER_LIMIT' in e:cats.add('OVER_VERBOSITY')
  elif 'MAPPING' in e or 'LABEL' in e:cats.add('EVIDENCE_REASONING')
  elif 'JOB' in e:cats.add('REQUIREMENT_EXTRACTION')
  elif not e.startswith('SCHEMA'):cats.add('EVIDENCE_REASONING')
 if 'expected' in s and s['predicted']!=s['expected']:
  cats.add('UNKNOWN_VS_UNSUPPORTED' if {s['predicted'],s['expected']}=={'UNKNOWN','UNSUPPORTED'} else 'UNJUSTIFIED_PARTIAL' if s['predicted']=='PARTIALLY_SUPPORTED' else 'COMPOUND_REASONING' if s['compound'] else 'EVIDENCE_REASONING')
 if s.get('unsupported_positive_atoms'):cats.add('EVIDENCE_REASONING')
 return sorted(cats)
def main(directory):
 out=Path(directory);scores=json.loads((out/('selection80_scores.json' if (out/'selection80_scores.json').exists() else 'scores.json')).read_text());generation_root=out.parent if out.name=='scoring_v2' else out;index={}
 for d in ['stage4a','stage4c0']:
  index[d]={r['metadata']['example_id']:r for r in map(json.loads,(R/f'datasets/{d}/v1/validation.jsonl').read_text().splitlines())}
 failures=[];counts=collections.Counter()
 for d,xs in scores.items():
  for s in xs:
   cats=taxonomy(s)
   if cats:failures.append({'dataset':d,'id':s['id'],'categories':cats,'score':s});counts.update(cats)
 selected=[];seen=set()
 for cat in sorted(counts):
  candidates=sorted((f for f in failures if cat in f['categories']),key=lambda f:f['id'])
  for f in candidates:
   if f['id'] not in seen:selected.append(f);seen.add(f['id']);break
  if len(selected)>=8:break
 for f in sorted(failures,key=lambda f:f['id']):
  if len(selected)>=8:break
  if f['id'] not in seen:selected.append(f);seen.add(f['id'])
 def packet(d,eid):
  row=index[d][eid];p=generation_root/d/(eid+'.json');generated=json.loads(p.read_text())
  return {'id':eid,'dataset':d,'metadata':row['metadata'],'visible_messages':row['messages'][:2],'student_raw':generated['raw'],'output_sha256':sha(p)}
 write(out/'failure_taxonomy.json',{'counts':dict(counts),'cases':failures,'automatic_taxonomy_is_not_teacher_diagnosis':True})
 write(out/'teacher_failure_sample.json',{'boundary':'VALIDATION ONLY; diagnosis may guide novel TRAIN-family corrections; never paraphrase these cases','cases':[dict(packet(f['dataset'],f['id']),automatic_categories=f['categories'],score=f['score']) for f in selected],'max_sample':8})
 write(out/'professional_rubric_packet.json',{'boundary':'VALIDATION qualitative assessment; not training targets','cases':[packet('stage4c0',s['id']) for s in scores['stage4c0']],'rubric':'contracts/rubric.v1.json','task_rubrics':'contracts/task_rubrics'})
 print(json.dumps({'failure_counts':dict(counts),'teacher_sample':len(selected)}))
if __name__=='__main__':main(sys.argv[1])
