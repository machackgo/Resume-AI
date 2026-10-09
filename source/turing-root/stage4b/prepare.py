import os,json,hashlib,inspect,importlib.metadata,subprocess
from pathlib import Path
ROOT=Path.cwd(); OUT=ROOT/'results/stage4b/smoke'; OUT.mkdir(parents=True,exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(name,x): (OUT/name).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
def verify():
 checks={}
 for mf in ['results/stage4a/protected-manifest.json','results/stage4a/final-manifest.json']:
  m=json.loads((ROOT/mf).read_text());bad=[p for p,h in m.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h];checks[mf]={'files':len(m),'changed':bad};assert not bad,bad
 release=ROOT/'datasets/stage4a/v1'
 for line in (release/'checksums.sha256').read_text().splitlines():
  h,p=line.split('  ',1);assert sha(release/p)==h,p
 archive=ROOT/'results/stage4a-release-v1.tar.gz';h=(archive.with_suffix(archive.suffix+'.sha256')).read_text().split()[0];assert sha(archive)==h
 checks['archive_sha256']=h;checks['release_checksums_valid']=True;dump('release-integrity.json',checks)
 # Protect all existing project artifacts, excluding mutable environment/cache and our new stage.
 paths=[]
 for d in ['datasets','docs','eval','fixtures','migrations','models','rag','results','stage4a','tests']:
  paths.extend(p for p in (ROOT/d).rglob('*') if p.is_file() and 'stage4b' not in p.parts and '__pycache__' not in p.parts)
 dump('protected-manifest.json',{str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))})
def select(rows):
 chosen=[]
 for family in ['adaptation','api','numeric','verified']:
  for label,variant in [('SUPPORTED',2),('PARTIALLY_SUPPORTED',6),('UNKNOWN',3),('UNSUPPORTED',1)]:
   chosen.append(sorted([r for r in rows if r['metadata']['template_family']==family and r['metadata']['expected_label']==label and r['metadata']['variant']==variant],key=lambda r:r['metadata']['example_id'])[0])
 return chosen
if __name__=='__main__':
 verify();print('INTEGRITY PASSED',flush=True)
 import torch
 from transformers import AutoTokenizer,AutoConfig,AutoModelForCausalLM
 from accelerate import init_empty_weights
 from peft import prepare_model_for_kbit_training
 model=ROOT/'models/Qwen3.8-27B';tok=AutoTokenizer.from_pretrained(model,local_files_only=True)
 from stage4a.validate import validate_release
 dump('dataset-validation.json',validate_release(ROOT/'datasets/stage4a/v1',tok))
 from stage4a.data import tokenized,pad_batch
 rows=[json.loads(l) for l in (ROOT/'datasets/stage4a/v1/train.jsonl').read_text().splitlines()];chosen=select(rows)
 encoded={r['metadata']['example_id']:tokenized(r,tok) for r in rows}
 longest=max(rows,key=lambda r:encoded[r['metadata']['example_id']]['total_tokens'])
 if longest not in chosen:chosen.append(longest)
 ids=[r['metadata']['example_id'] for r in chosen]
 for split in ['validation','test']:
  other={json.loads(l)['metadata']['example_id'] for l in (ROOT/f'datasets/stage4a/v1/{split}.jsonl').read_text().splitlines()};assert not set(ids)&other
 assert all(r['metadata']['split']=='train' for r in chosen)
 dump('subset_manifest.json',dict(selection='Lexicographic IDs within four fixed families, four labels, fixed variants; plus longest TRAIN record; no inference-based selection',ids=ids,examples=[dict(**r['metadata'],total_tokens=encoded[r['metadata']['example_id']]['total_tokens']) for r in chosen],train_sha256=sha(ROOT/'datasets/stage4a/v1/train.jsonl')))
 audits=[]
 for r in chosen:
  e=encoded[r['metadata']['example_id']];n=e['input_tokens'];assert e['labels'][:n]==[-100]*n;assert e['labels'][n:]==e['input_ids'][n:];assert e['labels'][-1]==tok.convert_tokens_to_ids('<|im_end|>');assert tok.decode(e['input_ids'][n:-1])==r['messages'][2]['content'];assert e['total_tokens']<=4608
  audits.append(dict(id=r['metadata']['example_id'],total=e['total_tokens'],masked=n,supervised=e['target_tokens'],padding=0,boundary=[dict(position=i,token_id=e['input_ids'][i],token=tok.convert_ids_to_tokens(e['input_ids'][i]),label=e['labels'][i]) for i in range(n-8,n+8)],eos=e['labels'][-1]))
 batch=pad_batch([encoded[ids[0]],encoded[ids[-1]]],tok)
 for b in batch:
  assert all(l==-100 for l,a in zip(b['labels'],b['attention_mask']) if a==0)
 dump('loss-mask-audit.json',dict(examples=audits,padding_tokens=[b['attention_mask'].count(0) for b in batch],chat_template=tok.chat_template,tokenizer_class=type(tok).__name__,pad_token_id=tok.pad_token_id,eos_token_id=tok.eos_token_id,enable_thinking=False,supervise='assistant JSON and exactly one im_end; formatting newline excluded'))
 config=AutoConfig.from_pretrained(model,local_files_only=True)
 with init_empty_weights(): meta=AutoModelForCausalLM.from_config(config)
 modules={n:dict(type=type(m).__name__,shape=list(m.weight.shape)) for n,m in meta.named_modules() if isinstance(m,torch.nn.Linear)}
 dump('architecture.json',dict(model_path=str(model.resolve()),class_name=type(meta).__name__,parameters=sum(p.numel() for p in meta.parameters()),config=config.to_dict(),modules=modules))
 import transformers.models.qwen3_5.modeling_qwen3_5 as implementation
 dump('environment-cpu.json',dict(versions={p:importlib.metadata.version(p) for p in ['torch','transformers','peft','bitsandbytes','accelerate','datasets','trl','tokenizers']},cuda=torch.version.cuda,job=os.environ.get('SLURM_JOB_ID'),model_source=inspect.getfile(implementation),model_source_sha256=sha(inspect.getfile(implementation))))
 (OUT/'peft-preparation-source.txt').write_text(inspect.getsource(prepare_model_for_kbit_training))
 (OUT/'model-implementation.py.txt').write_text(inspect.getsource(implementation))
 print('CPU PREPARATION PASSED',len(ids),flush=True)
