"""Seal completed matched baseline with provenance and protected-base verification."""
import json,hashlib,importlib.metadata
from pathlib import Path
from stage4c1.evaluate import sha,write,score_evidence,score_professional,summarize
R=Path.cwd();B=R/'results/stage4c1/base_validation';O=B/'scoring_v2'
def main():
 assert (B/'summary.json').exists() and not O.exists()
 identity=json.loads((B/'evaluation_identity.json').read_text());assert identity['adapter'] is None
 digest=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
 protected=json.loads((R/'results/stage4c0/protected-manifest.json').read_text());base={p:h for p,h in protected.items() if p.startswith('models/Qwen3.8-27B/')}
 assert base and all(sha(R/p)==h for p,h in base.items())
 subset=json.loads((R/'results/stage4c1/plan/validation_subset.json').read_text());scores={'stage4a':[],'stage4c0':[]};binding={}
 for d in ('stage4a','stage4c0'):
  expected=set(subset['stage4a_ids']) if d=='stage4a' else {json.loads(l)['metadata']['example_id'] for l in (R/'datasets/stage4c0/v1/validation.jsonl').read_text().splitlines()}
  rows={r['metadata']['example_id']:r for r in map(json.loads,(R/f'datasets/{d}/v1/validation.jsonl').read_text().splitlines())}
  assert {p.stem for p in (B/d).glob('*.json')}==expected
  for p in (B/d).glob('*.json'):
   item=json.loads(p.read_text());assert item['identity_sha256']==digest and item['split']=='validation'
   scored=(score_evidence if d=='stage4a' else score_professional)(rows[item['id']],item['raw'])
   scored.update(teacher_forced_loss=item['teacher_forced_loss'],termination=item['termination'],generation_complete=item['termination']=='eos')
   if not scored['generation_complete']:
    scored['errors'].append('GENERATION_LENGTH_LIMIT')
    if d=='stage4a':scored.update(predicted='INVALID',contract_valid=False,atomic_correct=0)
   scores[d].append(scored)
   binding[str(p.relative_to(R))]=sha(p)
  assert len(scores[d])==len(expected) and {s['id'] for s in scores[d]}==expected
 summary=summarize(scores)
 for d,xs in scores.items():
  summary[d]['length_terminated']=sum(x['termination']=='length' for x in xs)
  summary[d]['mean_example_validation_loss']=sum(x['teacher_forced_loss'] for x in xs)/len(xs)
 for name,x in [('scores',scores),('summary',summary),('selection80_scores',scores),('selection80_summary',summary),('identity',identity),('generated_artifact_checksums',binding)]:write(O/(name+'.json'),x)
 write(O/'completion.json',{'passed':True,'generation_complete':True,'optimizer_steps':0,'base_files_unchanged':True,'cache_migration_sha256':sha(B/'cache_migration.json'),'scoring_source_sha256':sha(R/'stage4c1/evaluate.py'),'versions':{p:importlib.metadata.version(p) for p in ['torch','transformers','peft','bitsandbytes','accelerate','tokenizers']}})
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
