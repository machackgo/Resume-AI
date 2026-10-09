"""Versioned, resumable Stage 4C-1 training; one preregistered interval per job."""
import os,json,time,random,signal,sys,traceback,shutil,gc
from pathlib import Path
import torch
from stage4c1.evaluate import write,sha,evaluate
from stage4b import engine as eng
from stage4a.data import tokenized
R=Path.cwd(); STOP=False

def signal_stop(sig,frame):
 global STOP
 STOP=True

def assert_trainable(m,train):
 actual={n:p for n,p in m.named_parameters() if p.requires_grad}
 assert set(actual)==set(train) and all(actual[n] is p for n,p in train.items())
 assert sum(p.numel() for p in train.values())==5242880
 assert all('lora_' in n for n in actual)
 assert all(not p.requires_grad and p.grad is None for n,p in m.named_parameters() if n not in train)

def state_fingerprint(obj):
 import hashlib
 h=hashlib.sha256()
 def walk(x):
  if isinstance(x,torch.Tensor):
   t=x.detach().cpu().contiguous();h.update(str((str(t.dtype),tuple(t.shape))).encode());h.update(t.reshape(-1).view(torch.uint8).numpy().tobytes())
  elif isinstance(x,dict):
   for k in sorted(x,key=str):h.update(str(k).encode());walk(x[k])
  elif isinstance(x,(list,tuple)):
   for v in x:walk(v)
  else:h.update(repr(x).encode())
 walk(obj);return h.hexdigest()

def checkpoint(m,opt,scheduler,step,plan,config,path,trajectory):
 assert not path.exists(),'never overwrite checkpoint'
 tmp=path.with_name(path.name+'.incomplete');assert not tmp.exists(),'inspect incomplete checkpoint before retry'
 tmp.mkdir(parents=True);m.save_pretrained(tmp,safe_serialization=True,save_embedding_layers=False)
 torch.save({'adapter_fingerprint':eng.fingerprint({n:p for n,p in m.named_parameters() if p.requires_grad}),'optimizer_fingerprint':state_fingerprint(opt.state_dict()),'scheduler_fingerprint':state_fingerprint(scheduler.state_dict()),'step':step,'optimizer':opt.state_dict(),'scheduler':scheduler.state_dict(),'random':random.getstate(),'torch':torch.get_rng_state(),'cuda':torch.cuda.get_rng_state_all(),'plan_sha256':config['plan_sha256'],'config_sha256':config['config_sha256']},tmp/'training_state.pt')
 assert [x['step'] for x in trajectory]==list(range(1,step+1))
 assert [eid for x in trajectory for eid in x['ids']]==[x['id'] for x in plan['entries'][:2*step]]
 write(tmp/'training_config.json',config);write(tmp/'mixture.json',plan);write(tmp/'trajectory.json',trajectory)
 write(tmp/'checksums.json',{p.name:sha(p) for p in tmp.iterdir() if p.is_file()})
 tmp.rename(path)
 write(path.parent/'latest.json',{'step':step,'path':str(path),'checksums_sha256':sha(path/'checksums.json')})

def main(arm,until):
 assert arm in ['evidence_only','interleaved'] and os.environ.get('SLURM_JOB_ID')
 assert not (R/'results/stage4c1/development_frozen.json').exists(),'NO TRAINING AFTER FINAL-EXAM FREEZE'
 assert torch.cuda.device_count()==1 and 'A30' in torch.cuda.get_device_name()
 assert json.loads((R/'results/stage4c1/preflight/integrity.json').read_text())['passed']
 assert (R/'results/stage4c1/base_validation/scoring_v2/summary.json').exists(),'baseline must finish before optimization'
 out=R/'results/stage4c1'/arm;out.mkdir(parents=True,exist_ok=True);eng.OUT=out
 plan_path=R/f'results/stage4c1/plan/{arm}.json';plan=json.loads(plan_path.read_text());assert until in plan['checkpoints']
 cfg_path=R/'stage4c1/training_config.json';cfg=json.loads(cfg_path.read_text());cfg['config_sha256']=sha(cfg_path);cfg['plan_sha256']=sha(plan_path);cfg['arm']=arm;cfg['execution_sources']={str(p.relative_to(R)):sha(p) for p in sorted((R/'stage4c1').glob('*.py'))}
 assert sha(R/'docs/stage4c1_experiment_protocol.md')==cfg['protocol_sha256']
 for p,h in plan['source_sha256'].items():assert sha(R/p)==h,'source drift '+p
 approval=R/f'results/stage4c1/approvals/{arm}_{until}.json'
 assert approval.exists(),'teacher approval required for next registered phase'
 receipt=json.loads(approval.read_text());assert receipt['config_sha256']==sha(cfg_path)
 for reviewed,h in receipt['reviewed_artifacts'].items():assert sha(R/reviewed)==h,'stale teacher continuation decision'
 assert receipt['decision']=='CONTINUE' and receipt['plan_sha256']==sha(plan_path) and receipt['protocol_sha256']==cfg['protocol_sha256']
 adapterroot=R/f'adapters/stage4c1/run_430001/{arm}';adapterroot.mkdir(parents=True,exist_ok=True)
 random.seed(430001);torch.manual_seed(430001);torch.cuda.manual_seed_all(430001)
 tok=eng.AutoTokenizer.from_pretrained(eng.MODEL,local_files_only=True)
 rows={}
 for d in ['stage4a','stage4c0']:
  for l in (R/f'datasets/{d}/v1/train.jsonl').read_text().splitlines():
   r=json.loads(l);assert r['metadata']['split']=='train';rows[r['metadata']['example_id']]=r
 ordered=[rows[x['id']] for x in plan['entries']];encoded=[tokenized(r,tok) for r in ordered]
 assert all(e['total_tokens']<=4233 for e in encoded)
 m,q=eng.load();torch.manual_seed(430001);torch.cuda.manual_seed_all(430001);m,train,lc=eng.attach(m)
 import bitsandbytes as bnb
 optimizer=bnb.optim.PagedAdamW8bit(list(train.values()),lr=5e-5,weight_decay=.01,betas=(.9,.999),eps=1e-8)
 scheduler=torch.optim.lr_scheduler.LambdaLR(optimizer,lambda _:1.0)
 assert {id(p) for g in optimizer.param_groups for p in g['params']}=={id(p) for p in train.values()}
 step=0;trajectory=[]
 if (adapterroot/'latest.json').exists():
  last=json.loads((adapterroot/'latest.json').read_text());p=Path(last['path'])
  assert sha(p/'checksums.json')==last['checksums_sha256']
  assert all(sha(p/n)==h for n,h in json.loads((p/'checksums.json').read_text()).items())
  from safetensors.torch import load_file
  from peft import set_peft_model_state_dict
  loaded=set_peft_model_state_dict(m,load_file(str(p/'adapter_model.safetensors')));assert not loaded.unexpected_keys and not any('lora_' in k for k in loaded.missing_keys),'adapter state not fully restored'
  state=torch.load(p/'training_state.pt',map_location='cpu',weights_only=False)
  assert state['plan_sha256']==cfg['plan_sha256'] and state['config_sha256']==cfg['config_sha256']
  saved_cfg=json.loads((p/'training_config.json').read_text())
  assert saved_cfg['execution_sources']==cfg['execution_sources'],'execution source drift requires diagnosed/versioned restart, not silent resume'
  trajectory=json.loads((p/'trajectory.json').read_text());assert len(trajectory)==state['step']
  optimizer.load_state_dict(state['optimizer']);scheduler.load_state_dict(state['scheduler'])
  assert eng.fingerprint(train)==state['adapter_fingerprint'],'adapter restore fingerprint mismatch'
  assert state_fingerprint(optimizer.state_dict())==state['optimizer_fingerprint'],'optimizer state restore mismatch'
  assert state_fingerprint(scheduler.state_dict())==state['scheduler_fingerprint'],'scheduler state restore mismatch'
  write(out/f'resume_verified_{state["step"]:06d}_{os.environ["SLURM_JOB_ID"]}.json',{'passed':True,'step':state['step'],'adapter_fingerprint':state['adapter_fingerprint'],'optimizer_fingerprint':state['optimizer_fingerprint'],'scheduler_fingerprint':state['scheduler_fingerprint'],'checkpoint':str(p)})
  random.setstate(state['random']);torch.set_rng_state(state['torch']);torch.cuda.set_rng_state_all(state['cuda']);step=state['step']
 assert step<=until
 prior_reviews=[x for x in plan['checkpoints'] if x<until]
 if prior_reviews:
  assert str((adapterroot/f'checkpoint_{max(prior_reviews):06d}'/'checksums.json').relative_to(R)) in receipt['reviewed_artifacts'],'continuation must bind preceding reviewed checkpoint'
 assert_trainable(m,train)
 assert {id(p) for g in optimizer.param_groups for p in g['params']}=={id(p) for p in train.values()}
 if step==0:
  initial_fp=eng.fingerprint(train)
  if (out/'initial_adapter.json').exists():assert json.loads((out/'initial_adapter.json').read_text())['fingerprint']==initial_fp
  else:write(out/'initial_adapter.json',{'fingerprint':initial_fp,'seed':430001})
  other=R/'results/stage4c1'/('interleaved' if arm=='evidence_only' else 'evidence_only')/'initial_adapter.json'
  if other.exists():assert json.loads(other.read_text())['fingerprint']==initial_fp,'fresh arms must share identical initialization'
  if not (out/'prepared_base_train_probe.json').exists():
   with m.disable_adapter():eng.probe(m,tok,ordered[0],'prepared_base_train_probe.json')
  if not (adapterroot/'checkpoint_000000').exists():checkpoint(m,optimizer,scheduler,0,plan,cfg,adapterroot/'checkpoint_000000',trajectory)
 write(out/f'environment_{until}_from_{step}_{os.environ["SLURM_JOB_ID"]}.json',{'job':os.environ['SLURM_JOB_ID'],'gpu':torch.cuda.get_device_name(),'quantization':q.to_dict(),'lora':lc.to_dict(),'optimizer':'bitsandbytes.PagedAdamW8bit','scheduler':'constant','resume_step':step,'planned_stop_step':until,'configuration':cfg})
 signal.signal(signal.SIGUSR1,signal_stop);signal.signal(signal.SIGTERM,signal_stop)
 for index in range(step,until):
  assert not (R/'results/stage4c1/development_frozen.json').exists(),'development frozen while process active'
  group=encoded[2*index:2*index+2];assert group
  m.train();optimizer.zero_grad(set_to_none=True);assert_trainable(m,train);torch.cuda.reset_peak_memory_stats();start=time.monotonic();losses=[];before=eng.fingerprint(train)
  for e in group:
   b=eng.batch(e);v=eng.loss(m,b);assert torch.isfinite(v) and v.item()<30,'loss anomaly'
   losses.append(v.item());(v/len(group)).backward();del b,v
  norm=eng.grads(m,train);assert_trainable(m,train);assert norm<100,'gradient explosion'
  assert not (R/'results/stage4c1/development_frozen.json').exists(),'NO OPTIMIZER STEP AFTER FINAL-EXAM FREEZE'
  optimizer.step();scheduler.step();torch.cuda.synchronize();after=eng.fingerprint(train);assert before!=after
  assert all(torch.isfinite(p).all() for p in train.values());step=index+1
  optimizer.zero_grad(set_to_none=True)
  metric={'job':os.environ['SLURM_JOB_ID'],'step':step,'loss':sum(losses)/len(losses),'example_losses':losses,'gradient_norm':norm,'lr':optimizer.param_groups[0]['lr'],'seconds':time.monotonic()-start,'allocated':torch.cuda.memory_allocated(),'reserved':torch.cuda.memory_reserved(),'peak_allocated':torch.cuda.max_memory_allocated(),'peak_reserved':torch.cuda.max_memory_reserved(),'before_sha256':before,'after_sha256':after,'ids':[x['id'] for x in plan['entries'][2*index:2*index+2]],'supervised_tokens':sum(e['target_tokens'] for e in group),'base_frozen':True}
  eng.emit('training_metrics.jsonl',metric);trajectory.append(metric)
  if step%10==0 or step==until or STOP:
   checkpoint(m,optimizer,scheduler,step,plan,cfg,adapterroot/f'checkpoint_{step:06d}',trajectory)
  if step==10 and not any(out.glob('resume_verified_000010_*.json')):
   write(out/'engineering_restart_required.json',{'step':step,'reason':'Fresh-process optimizer/scheduler/adapter/RNG resume integration before remaining optimization'});return
  if STOP:write(out/'interrupted.json',{'safe_step':step,'time':time.time()});return
 assert_trainable(m,train);optimizer.zero_grad(set_to_none=True);del optimizer,scheduler;gc.collect();torch.cuda.empty_cache()
 if not (out/f'adapter_train_probe_{step:06d}.json').exists():eng.probe(m,tok,ordered[0],f'adapter_train_probe_{step:06d}.json')
 with m.disable_adapter():recovered=eng.probe(m,tok,ordered[0],f'recovered_base_train_probe_{step:06d}.json')
 original=json.loads((out/'prepared_base_train_probe.json').read_text());assert recovered['tokens']==original['tokens'] and recovered['signature']==original['signature'],'prepared base recovery failed'
 write(out/f'base_recovery_{step:06d}.json',{'passed':True,'probe_id':ordered[0]['metadata']['example_id']})
 identity={'validation_subset_sha256':sha(R/'results/stage4c1/plan/validation_subset.json'),'adapter_checksums_sha256':sha(adapterroot/f'checkpoint_{step:06d}'/'checksums.json'),'base_manifest_sha256':sha(R/'results/stage4c0/protected-manifest.json'),'training_config_sha256':cfg['config_sha256'],'decoding':{'do_sample':False,'stage4a_max_new_tokens':2048,'stage4c0_max_new_tokens':3072,'enable_thinking':False},'tokenizer':{p.name:sha(p) for p in eng.MODEL.iterdir() if p.is_file() and ('token' in p.name or p.name in ['vocab.json','merges.txt','chat_template.jinja'])}}
 evaluate(m,tok,out/f'validation_{step:06d}',identity=identity)
 write(out/f'needs_teacher_review_{step:06d}.json',{'step':step,'arm':arm,'validation_complete':True,'time':time.time(),'checkpoint':str(adapterroot/f'checkpoint_{step:06d}'),'next_action':'Teacher diagnosis and registered gate decision. No automatic continuation.'})

if __name__=='__main__':
 try:main(sys.argv[1],int(sys.argv[2]))
 except Exception as e:
  write(R/'results/stage4c1'/f'failure_{os.environ.get("SLURM_JOB_ID","nojob")}.json',{'error':repr(e),'traceback':traceback.format_exc(),'time':time.time()});raise
