"""Create blinded professional VALIDATION packets; no final targets."""
import json,sys,hashlib,random
from pathlib import Path
from stage4c1.evaluate import write,sha
R=Path.cwd()
def main(source,destination,split='validation'):
 assert split in ('validation','test','challenge')
 if split!='validation':assert (R/'results/stage4c1/development_frozen.json').exists()
 src=Path(source).resolve();out=Path(destination).resolve();assert not out.exists()
 generation=src.parent if src.name=='scoring_v2' else src
 scores=json.loads((src/'scores.json').read_text())['stage4c0'];rows={r['metadata']['example_id']:r for r in map(json.loads,(R/f'datasets/stage4c0/v1/{split}.jsonl').read_text().splitlines())}
 assert len(scores)==len(rows)=={'validation':14,'test':16,'challenge':6}[split] and {s['id'] for s in scores}==set(rows)
 cases=[]
 for s in scores:
  row=rows[s['id']];p=generation/'stage4c0'/(s['id']+'.json');obj=json.loads(p.read_text());assert obj['split']==split
  cases.append({'id':s['id'],'task':row['metadata']['task'],'visible_messages':row['messages'][:2],'student_output':obj['raw'],'output_sha256':sha(p),'automatic_errors':s['errors'],'schema_valid':s['schema_valid'],'generation_complete':obj['termination']=='eos'})
 random.Random(430001).shuffle(cases)
 rubric=R/'contracts/rubric.v1.json';rubrics={p.name:json.loads(p.read_text()) for p in sorted((R/'contracts/task_rubrics').glob('*.json'))}
 write(out/'packet.json',{'version':'stage4c1-blinded-professional-v1','split':split,'model_label':'ANONYMOUS_MODEL','cases':cases,'rubric':json.loads(rubric.read_text()),'task_rubrics':rubrics,'primary_rubric_dimensions':['task_completion','job_relevance','specificity','writing','structure_coherence','uncertainty_handling','downstream_usability'],'grounding_is_separate_hard_gate':True,'invalid_output_rule':'Missing/schema-invalid/length-terminated responses score0 on all seven professional dimensions; do not count unassessable factual claims as safe. Review every packet output, including deterministic passes.','assessment_boundary':'Visible task/evidence/profile only; no hidden reasoning requested. Brief externally meaningful assessments and factual-atom source support only.'})
 write(out/'mapping.json',{'source':str(src.relative_to(R)),'raw_outputs':{c['id']:c['output_sha256'] for c in cases},'rubric_sha256':sha(rubric),'requested_model':'gpt-6-astra','requested_reasoning':'ultra'})
if __name__=='__main__':main(*sys.argv[1:])
