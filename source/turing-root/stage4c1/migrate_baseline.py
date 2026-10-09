"""One-time metadata-verified migration. Original raw outputs remain immutable."""
import json,hashlib,shutil
from pathlib import Path
from transformers import AutoTokenizer
from stage4c1.evaluate import sha,write,base_identity
R=Path.cwd();B=R/'results/stage4c1/base_validation';S=R/'results/stage4c1/source_snapshots/base_v1_job2335266_data'
def main():
 assert not (R/'adapters/stage4c1').exists(),'migration must precede optimization'
 assert not S.exists() and B.exists()
 env=json.loads((B/'environment.json').read_text());assert env['job']=='2335266' and env['adapter'] is None and env['prepared_for_training'] is False
 protected=json.loads((R/'results/stage4c0/protected-manifest.json').read_text());base={p:h for p,h in protected.items() if p.startswith('models/Qwen3.8-27B/')}
 assert base and all(sha(R/p)==h for p,h in base.items())
 subset=json.loads((R/'results/stage4c1/plan/validation_subset.json').read_text());allowed=set(subset['stage4a_ids'])
 tok=AutoTokenizer.from_pretrained(R/'models/Qwen3.8-27B',local_files_only=True)
 identity=base_identity(env['quantization']);binding=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
 old_hashes={str(p.relative_to(B)):sha(p) for p in B.rglob('*') if p.is_file()}
 B.rename(S);B.mkdir();write(B/'evaluation_identity.json',identity)
 migrated=[];excluded=[]
 for d in ('stage4a','stage4c0'):
  source=R/f'datasets/{d}/v1/validation.jsonl';rows={x['metadata']['example_id']:x for x in map(json.loads,source.read_text().splitlines())}
  for p in sorted((S/d).glob('*.json')):
   item=json.loads(p.read_text());eid=item['id'];assert eid in rows and item['split']=='validation' and item['dataset']==d
   # No output scoring or quality-based cache selection.
   prompt=tok.apply_chat_template(rows[eid]['messages'][:2],tokenize=False,add_generation_prompt=True,enable_thinking=False)
   assert item['prompt_sha256']==hashlib.sha256(prompt.encode()).hexdigest() and item['input_file_sha256']==sha(source)
   assert item['decoding']=={'do_sample':False,'enable_thinking':False,'max_new_tokens':2048 if d=='stage4a' else 3072}
   assert tok.decode(item['tokens'],skip_special_tokens=True)==item['raw']
   if d=='stage4a' and eid not in allowed:excluded.append({'path':str(p.relative_to(R)),'sha256':sha(p)});continue
   item['identity_sha256']=binding;item['migrated_from']={'path':str(p.relative_to(R)),'sha256':sha(p),'job':'2335266'}
   target=B/d/p.name;write(target,item);migrated.append({'id':eid,'source_sha256':sha(p),'target_sha256':sha(target),'source':str(p.relative_to(R)),'target':str(target.relative_to(R))})
 assert all(sha(S/p)==h for p,h in old_hashes.items())
 write(B/'cache_migration.json',{'passed':True,'original_files':old_hashes,'original_root':str(S.relative_to(R)),'original_environment_sha256':sha(S/'environment.json'),'original_source_sha256':sha(R/'results/stage4c1/source_snapshots/base_evaluate_v1.py'),'base_files_sha256':base,'stable_identity':identity,'migrated':migrated,'excluded_sealed':excluded,'optimizer_steps':0})
 print(json.dumps({'passed':True,'migrated':len(migrated),'sealed_excluded':len(excluded),'optimizer_steps':0}))
if __name__=='__main__':main()
