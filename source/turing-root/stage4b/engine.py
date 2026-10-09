"""Stage4B only: bounded QLoRA engineering probes. Never merge or save base."""
import os,json,time,hashlib,random,sys,traceback,gc,contextlib,subprocess
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig
from peft import LoraConfig,get_peft_model,PeftModel
from stage4a.data import tokenized,pad_batch
from stage4b.prepare import sha
ROOT=Path.cwd();OUT=ROOT/'results/stage4b/smoke';MODEL=ROOT/'models/Qwen3.8-27B';ADAPTER=ROOT/'adapters/stage4b_smoke'
def dump(name,x): (OUT/name).write_text(json.dumps(x,sort_keys=True,indent=2,default=lambda v: sorted(v) if isinstance(v,set) else str(v))+'\n')
def emit(name,x):
 with (OUT/name).open('a') as f:f.write(json.dumps(x,sort_keys=True)+'\n')
 print(name,json.dumps(x),flush=True)
def memory(tag):
 torch.cuda.synchronize();d=dict(tag=tag,allocated=torch.cuda.memory_allocated(),reserved=torch.cuda.memory_reserved(),peak_allocated=torch.cuda.max_memory_allocated(),peak_reserved=torch.cuda.max_memory_reserved());emit('memory_metrics.jsonl',d);return d
def seed():random.seed(410042);torch.manual_seed(410042);torch.cuda.manual_seed_all(410042)
def load():
 assert torch.cuda.device_count()==1 and 'A30' in torch.cuda.get_device_name(0)
 assert torch.cuda.is_bf16_supported()
 memory('before_load')
 q=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.bfloat16)
 m=AutoModelForCausalLM.from_pretrained(MODEL,local_files_only=True,quantization_config=q,device_map={'':0},dtype=torch.bfloat16,attn_implementation='sdpa')
 assert m.is_loaded_in_4bit;assert all(p.device.type=='cuda' and p.device.index==0 for p in m.parameters())
 memory('after_base_load');dump('loaded-architecture.json',dict(class_name=type(m).__name__,device_map={str(p.device) for p in m.parameters()},parameters_reported=m.num_parameters(),modules={n:dict(type=type(x).__name__,in_features=x.in_features,out_features=x.out_features) for n,x in m.named_modules() if hasattr(x,'in_features') and hasattr(x,'out_features')}));return m,q
def attach(m):
 # Audited PEFT preparation equivalent, except retain existing BF16 large embeddings/head.
 # Avoid ~4.74GiB FP32 expansion of two frozen 248320x5120 matrices.
 for n,p in m.named_parameters():
  p.requires_grad_(False)
  if p.__class__.__name__!='Params4bit' and p.ndim==1 and p.dtype==torch.bfloat16:p.data=p.data.float()
 m.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});m.config.use_cache=False
 targets=[n for n,x in m.named_modules() if n.split('.')[-1] in ['q_proj','k_proj','v_proj','o_proj']]
 assert len(targets)==64,targets
 lc=LoraConfig(r=8,lora_alpha=16,lora_dropout=0.05,bias='none',task_type='CAUSAL_LM',target_modules=targets)
 m=get_peft_model(m,lc)
 train={n:p for n,p in m.named_parameters() if p.requires_grad}
 assert sum(p.numel() for p in train.values())==5242880
 assert all(('lora_A.default.weight' in n or 'lora_B.default.weight' in n) and p.device==torch.device('cuda:0') for n,p in train.items())
 dump('trainable-parameters.json',dict(names={n:list(p.shape) for n,p in train.items()},count=sum(p.numel() for p in train.values()),base_count=26895998464,percentage=100*5242880/26895998464,targets=targets,base_frozen=True,device_map={str(p.device) for p in m.parameters()},preparation='freeze all; 1D nonquantized parameters FP32; embeddings/head retain BF16; nonreentrant gradient checkpointing; no input-grad hook needed',dtypes={n:str(p.dtype) for n,p in m.named_parameters() if 'embed_tokens' in n or 'lm_head' in n}))
 memory('after_lora');return m,train,lc

def validate_encoded(e):
 n=len(e['input_ids']);assert 1<n<=4608,'invalid sequence length'
 assert len(e['labels'])==len(e['attention_mask'])==n
 assert any(l!=-100 for l in e['labels'][1:]),'empty supervised region'
 assert all(l==-100 or l==i for i,l in zip(e['input_ids'],e['labels'])),'invalid labels'
 assert all(a in (0,1) for a in e['attention_mask'])
 assert all(l==-100 for a,l in zip(e['attention_mask'],e['labels']) if not a),'padding supervised'
def batch(e):
 validate_encoded(e)
 return {k:torch.tensor([e[k]],dtype=torch.long,device='cuda') for k in ['input_ids','attention_mask','labels']}
def chunked_cross_entropy(hidden,head,targets,chunk_size=64):
 from torch.utils.checkpoint import checkpoint
 def part(h,t):return torch.nn.functional.cross_entropy(head(h).float(),t,reduction='sum')
 total=hidden.new_zeros((),dtype=torch.float32)
 for start in range(0,len(targets),chunk_size):
  h=hidden[start:start+chunk_size];t=targets[start:start+chunk_size]
  total=total+(checkpoint(part,h,t,use_reentrant=False) if torch.is_grad_enabled() else part(h,t))
 return total/len(targets)
def reference_loss(m,b):
 pos=torch.nonzero(b['labels'][0,1:]!=-100).flatten()
 logits=m(input_ids=b['input_ids'],attention_mask=b['attention_mask'],use_cache=False,logits_to_keep=pos).logits
 return torch.nn.functional.cross_entropy(logits[0].float(),b['labels'][0,pos+1])
def loss(m,b):
 pos=torch.nonzero(b['labels'][0,1:]!=-100).flatten();assert len(pos)>0
 base=m.get_base_model()
 with torch.autograd.graph.save_on_cpu(pin_memory=True) if torch.is_grad_enabled() else contextlib.nullcontext():
  hidden=base.model(input_ids=b['input_ids'],attention_mask=b['attention_mask'],use_cache=False).last_hidden_state
 result=chunked_cross_entropy(hidden[0,pos],base.get_output_embeddings(),b['labels'][0,pos+1])
 assert torch.isfinite(result)
 return result

def grads(m,train):
 assert all(p.device==torch.device('cuda:0') for p in m.parameters())
 assert all(p.grad is not None and p.grad.device==torch.device('cuda:0') for p in train.values())
 assert all(p.grad is None for n,p in m.named_parameters() if not p.requires_grad)
 assert all(p.grad is not None for p in train.values())
 assert all(torch.isfinite(p.grad).all().item() for p in train.values())
 norm=torch.nn.utils.clip_grad_norm_(list(train.values()),1.0,error_if_nonfinite=True)
 assert norm.item()>0;return norm.item()
def fingerprint(train):
 h=hashlib.sha256()
 for n,p in train.items():h.update(n.encode());h.update(p.detach().cpu().float().numpy().tobytes())
 return h.hexdigest()
def probe(m,tok,row,name):
 m.eval();e=tokenized(row,tok);ids=torch.tensor([e['input_ids'][:e['input_tokens']]],device='cuda');start=time.monotonic()
 with torch.inference_mode():
  logits=m(input_ids=ids,attention_mask=torch.ones_like(ids),use_cache=False,logits_to_keep=1).logits[0,-1].float()
  # Sparse deterministic score signature demonstrates effects even if greedy text stays identical.
  scores=torch.topk(logits,20);signature=dict(ids=scores.indices.tolist(),logits=scores.values.tolist())
  result=m.generate(input_ids=ids,attention_mask=torch.ones_like(ids),do_sample=False,max_new_tokens=1536,use_cache=True,pad_token_id=tok.pad_token_id,eos_token_id=[tok.eos_token_id,tok.convert_tokens_to_ids('<|im_end|>')])
 raw=tok.decode(result[0,ids.shape[1]:],skip_special_tokens=True);valid=False;error=None
 try:
  from rag.reasoning.contract import strict_parse,schema_valid
  obj,error=strict_parse(raw);valid=error is None and schema_valid(obj,json.loads((ROOT/'datasets/stage4a/v1/target-schema.json').read_text()))
  if not valid:error=error or 'frozen schema validation failed'
 except Exception as ex:error=str(ex)
 d=dict(example_id=row['metadata']['example_id'],raw=raw,tokens=result[0,ids.shape[1]:].tolist(),signature=signature,schema_valid=valid,schema_error=error,seconds=time.monotonic()-start)
 dump(name,d);return d

def main(mode):
 if mode=='train':assert not ADAPTER.exists() and not (OUT/'training_metrics.jsonl').exists(),'refuse to repeat/overwrite completed optimization'
 seed();tok=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
 manifest=json.loads((OUT/'subset_manifest.json').read_text());byid={r['metadata']['example_id']:r for r in map(json.loads,(ROOT/'datasets/stage4a/v1/train.jsonl').read_text().splitlines())};rows=[byid[i] for i in manifest['ids']];encoded=[tokenized(r,tok) for r in rows]
 probe_row=rows[0]
 m,q=load()
 dump('environment-'+mode+'.json',dict(job=os.environ['SLURM_JOB_ID'],gpu=torch.cuda.get_device_name(),total_memory=torch.cuda.get_device_properties(0).total_memory,cuda=torch.version.cuda,torch=torch.__version__,nvidia_smi=subprocess.check_output(['nvidia-smi'],text=True)))
 if mode=='reload':
  original=probe(m,tok,probe_row,'original_base_reload_probe.json')
  assert original['tokens']==json.loads((OUT/'original_base_pretrain_probe.json').read_text())['tokens']
  expected=json.loads((ADAPTER/'checksums.json').read_text())
  assert all(sha(ADAPTER/p)==v['sha256'] for p,v in expected.items())
  # Identical precision preparation to saved training model; frozen base remains on disk unchanged.
  for p in m.parameters():
   p.requires_grad_(False)
   if p.__class__.__name__!='Params4bit' and p.ndim==1 and p.dtype==torch.bfloat16:p.data=p.data.float()
  m=PeftModel.from_pretrained(m,ADAPTER,is_trainable=False)
  reloaded=probe(m,tok,probe_row,'reload_probe.json')
  with m.disable_adapter():base=probe(m,tok,probe_row,'reload_base_probe.json')
  pre=json.loads((OUT/'pretrain_probe.json').read_text());post=json.loads((OUT/'posttrain_probe.json').read_text())
  checks=dict(reload_tokens_equal=post['tokens']==reloaded['tokens'],reload_scores_equal=post['signature']==reloaded['signature'],base_tokens_equal=pre['tokens']==base['tokens'],base_scores_equal=pre['signature']==base['signature'],schema_valid=all(x['schema_valid'] for x in [pre,post,reloaded,base]))
  dump('reload-verification.json',checks);assert all(checks.values()),checks;return
 probe(m,tok,probe_row,'original_base_pretrain_probe.json')
 m,train,lc=attach(m)
 import bitsandbytes as bnb
 optimizer=bnb.optim.PagedAdamW8bit(list(train.values()),lr=5e-5,weight_decay=0.01,betas=(0.9,0.999),eps=1e-8)
 assert {id(p) for g in optimizer.param_groups for p in g['params']}=={id(p) for p in train.values()}
 memory('after_optimizer')
 dump('config.json',dict(stage='4B ONLY',seed=410042,model=str(MODEL.resolve()),quantization=q.to_dict(),lora=lc.to_dict(),batch_size=1,gradient_accumulation=2,max_length=4608,packing=False,truncation=False,optimizer='bitsandbytes.optim.PagedAdamW8bit',lr=5e-5,weight_decay=0.01,betas=[0.9,0.999],eps=1e-8,scheduler='constant',gradient_checkpointing=True,use_reentrant=False,activation_offload='torch.autograd.graph.save_on_cpu(pin_memory=True) for backbone saved tensors; GPU computation and parameters',device_map={'':0},attention='sdpa',steps=(len(rows)+1)//2,loss='checkpointed frozen vocabulary projection and FP32 CE; 64 supervised positions per chunk; exact causal assistant-only loss',subset_manifest_sha256=sha(OUT/'subset_manifest.json')))
 # Verify actual-model loss and adapter gradients against native selected-logit reference.
 m.train();e=min(encoded,key=lambda e:len(e['input_ids']));b=batch(e)
 seed();optimizer.zero_grad(set_to_none=True);reference=reference_loss(m,b);reference.backward()
 saved_grad={n:p.grad.detach().cpu().clone() for n,p in train.items()};ref_value=reference.item();del reference
 optimizer.zero_grad(set_to_none=True);torch.cuda.empty_cache();seed();candidate=loss(m,b);candidate.backward()
 differences={n:float((p.grad.detach().cpu()-saved_grad[n]).abs().max()) for n,p in train.items()}
 reference_vector=torch.cat([v.flatten() for v in saved_grad.values()]).double()
 candidate_vector=torch.cat([p.grad.detach().cpu().flatten() for p in train.values()]).double()
 relative_l2=((candidate_vector-reference_vector).norm()/reference_vector.norm()).item()
 cosine=torch.nn.functional.cosine_similarity(reference_vector,candidate_vector,dim=0).item()
 # Diagnosed same-seed reference/reference backward variability ~1.9–2.0%.
 # Near-zero elementwise relative comparisons are not a reliable BF16 equivalence gate.
 diagnosis=json.loads((OUT/'loss-diagnosis.json').read_text());head=diagnosis['isolated_head']
 assert head['relative_l2']<0.005 and head['cosine']>0.99999 and abs(head['reference_loss']-head['chunked_loss'])<2e-5
 assert relative_l2<0.03 and cosine>0.9995
 assert abs(candidate.item()-ref_value)<2e-5
 dump('chunked-loss-equivalence.json',dict(passed=True,reference_loss=ref_value,chunked_loss=candidate.item(),max_gradient_absolute_error=max(differences.values()),relative_gradient_l2=relative_l2,gradient_cosine=cosine,relative_l2_limit=0.03,cosine_minimum=0.9995,loss_absolute_tolerance=2e-5,diagnosis_sha256=sha(OUT/'loss-diagnosis.json'),sequence_length=len(e['input_ids']),example_id=rows[encoded.index(e)]['metadata']['example_id'],chunk_size=64))
 del candidate,b,saved_grad,reference_vector,candidate_vector;optimizer.zero_grad(set_to_none=True)
 # Fresh adapters: memory probes do backward but NO optimization. Synthetic lengths below
 # dataset minimum are explicitly engineering tensors, never optimization examples.
 for length in [1024,2048,3072,4096,4608]:
  m.train();optimizer.zero_grad(set_to_none=True);gc.collect();torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();start=time.monotonic()
  eligible=[e for e in encoded if len(e['input_ids'])<=length]
  if eligible:
   e=max(eligible,key=lambda x:len(x['input_ids']));k=length-len(e['input_ids']);e={key:e[key]+([tok.pad_token_id] if key=='input_ids' else [-100] if key=='labels' else [0])*k for key in ['input_ids','labels','attention_mask']};kind='complete TRAIN example plus masked padding'
  else:
   e=dict(input_ids=[tok.eos_token_id]*length,labels=[-100]*(length-16)+[tok.eos_token_id]*16,attention_mask=[1]*length);kind='synthetic shape-only; no optimizer update'
  try:
   b=batch(e);v=loss(m,b);memory('probe_'+str(length)+'_forward');v.backward();norm=grads(m,train);mem=memory('probe_'+str(length)+'_backward');emit('sequence-probes.jsonl',dict(sequence_length=length,batch=1,gradient_accumulation=2,gradient_checkpointing=True,forward=True,backward=True,optimizer_step='not performed; reserved for frozen subset training',loss=v.item(),gradient_norm=norm,seconds=time.monotonic()-start,kind=kind,**mem));del v,b
  except torch.cuda.OutOfMemoryError as ex:
   emit('sequence-probes.jsonl',dict(sequence_length=length,oom=True,error=str(ex),seconds=time.monotonic()-start));raise
 optimizer.zero_grad(set_to_none=True);gc.collect();torch.cuda.empty_cache()
 with m.disable_adapter():pre=probe(m,tok,probe_row,'pretrain_probe.json')
 # Same-example deterministic teacher-forced loss before/after distinguishes optimization
 # response from changes in example difficulty. No probe outputs select training data.
 m.eval()
 with torch.no_grad():initial=loss(m,batch(encoded[0])).item()
 initial_hash=fingerprint(train);step=0
 for offset in range(0,len(encoded),2):
  group=encoded[offset:offset+2];m.train();optimizer.zero_grad(set_to_none=True);torch.cuda.reset_peak_memory_stats();start=time.monotonic();values=[]
  before=fingerprint(train)
  for e in group:
   b=batch(e);v=loss(m,b);values.append(v.item());(v/len(group)).backward();del v,b
  norm=grads(m,train);memory('step_'+str(step+1)+'_backward');optimizer.step();torch.cuda.synchronize();after=fingerprint(train);assert after!=before
  step+=1;mem=memory('step_'+str(step)+'_optimizer');emit('training_metrics.jsonl',dict(step=step,loss=sum(values)/len(values),example_losses=values,lr=5e-5,gradient_norm=norm,tokens=sum(len(e['input_ids']) for e in group),supervised_tokens=sum(sum(l!=-100 for l in e['labels']) for e in group),seconds=time.monotonic()-start,before_sha256=before,after_sha256=after,**mem))
 optimizer.zero_grad(set_to_none=True);m.eval()
 with torch.no_grad():final=loss(m,batch(encoded[0])).item()
 dump('optimization-proof.json',dict(initial_loss=initial,final_loss=final,initial_sha256=initial_hash,final_sha256=fingerprint(train),finite=True,base_gradients_absent=True,steps=step))
 assert not ADAPTER.exists(),'refuse to overwrite adapter';ADAPTER.mkdir(parents=True)
 m.save_pretrained(ADAPTER,safe_serialization=True,save_embedding_layers=False)
 import shutil
 for name in ['config.json','subset_manifest.json','environment-cpu.json','environment-train.json']:shutil.copy2(OUT/name,ADAPTER/name)
 (ADAPTER/'checksums.json').write_text(json.dumps({p.name:dict(size=p.stat().st_size,sha256=sha(p)) for p in sorted(ADAPTER.iterdir()) if p.is_file()},sort_keys=True,indent=2)+'\n')
 post=probe(m,tok,probe_row,'posttrain_probe.json')
 with m.disable_adapter():base=probe(m,tok,probe_row,'posttrain_base_probe.json')
 checks=dict(base_tokens_equal=pre['tokens']==base['tokens'],base_scores_equal=pre['signature']==base['signature'],adapter_affects_scores=pre['signature']!=post['signature'],schema_valid=all(x['schema_valid'] for x in [pre,post,base]))
 dump('inmemory-verification.json',checks);assert all(checks.values()),checks
if __name__=='__main__':
 try:main(sys.argv[1])
 except Exception as ex:
  dump('failure-'+sys.argv[1]+'.json',dict(error=repr(ex),traceback=traceback.format_exc()));raise
