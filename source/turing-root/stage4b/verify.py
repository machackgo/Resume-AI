"""Independent read-only audit; no model load, optimizer or dataset rewrite."""
import json,math,os
from pathlib import Path
from safetensors import safe_open
from stage4b.prepare import sha
R=Path.cwd();O=R/'results/stage4b/smoke';A=R/'adapters/stage4b_smoke'
def read(p):return json.loads((O/p).read_text())
def lines(p):return [json.loads(l) for l in (O/p).read_text().splitlines()]
checks={}
def check(name,condition):
 checks[name]=bool(condition)
 if not condition:print('FAILED',name,flush=True)
m=read('protected-manifest.json')
for historical in ['results/stage4a/protected-manifest.json','results/stage4a/final-manifest.json']:
 for path,digest in json.loads((R/historical).read_text()).items():
  assert path not in m or m[path]==digest
  m[path]=digest
bad=[p for p,h in m.items() if not (R/p).is_file() or sha(R/p)!=h]
check('historical_byte_identity',not bad)
(O/'protected-verification.json').write_text(json.dumps(dict(files=len(m),changed=bad,passed=not bad),indent=2)+'\n')
for line in (R/'datasets/stage4a/v1/checksums.sha256').read_text().splitlines():
 h,p=line.split('  ',1);check('release_'+p,sha(R/'datasets/stage4a/v1'/p)==h)
loaded=read('loaded-architecture.json')
check('actual_loaded_architecture',loaded['class_name']=='Qwen3_5ForCausalLM' and loaded['parameters_reported']==26895998464)
check('single_gpu_placement',loaded['device_map']==['cuda:0'])
check('reload_record_exists',(O/'reload-verification.json').exists())
check('posttrain_record_exists',(O/'inmemory-verification.json').exists())
check('chunked_loss_equivalence',read('chunked-loss-equivalence.json')['passed'])
if A.exists():
 saved=json.loads((A/'checksums.json').read_text())
 for p,d in saved.items():check('adapter_hash_'+p,sha(A/p)==d['sha256'] and (A/p).stat().st_size==d['size'])
 with safe_open(A/'adapter_model.safetensors',framework='pt',device='cpu') as f:
  keys=list(f.keys());check('only_lora_saved',all('.lora_A.weight' in n or '.lora_B.weight' in n for n in keys));check('saved_adapter_count',sum(f.get_tensor(n).numel() for n in keys)==5242880)
 check('no_merged_model',not (A/'model.safetensors').exists())
 if (O/'reload-verification.json').exists():
  for k,v in read('reload-verification.json').items():check(k,v)
 if (O/'inmemory-verification.json').exists():
  for k,v in read('inmemory-verification.json').items():check(k,v)
 metrics=lines('training_metrics.jsonl');check('multiple_bounded_steps',2<=len(metrics)<=20)
 check('finite_losses',all(math.isfinite(x['loss']) for x in metrics));check('finite_positive_grad_norms',all(math.isfinite(x['gradient_norm']) and x['gradient_norm']>0 for x in metrics));check('every_step_updates',all(x['before_sha256']!=x['after_sha256'] for x in metrics))
 check('checksum_chain',all(a['after_sha256']==b['before_sha256'] for a,b in zip(metrics,metrics[1:])))
 p=read('optimization-proof.json');check('fixed_example_loss_response',p['final_loss']<p['initial_loss']);check('base_gradients_absent',p['base_gradients_absent'])
 check('trainable_parameter_count',read('trainable-parameters.json')['count']==5242880)
 check('memory_within_device',all(x['peak_reserved']<read('environment-train.json')['total_memory'] for x in lines('memory_metrics.jsonl')))
 check('complete_length_probe',all(x.get('forward') and x.get('backward') for x in lines('sequence-probes.jsonl')))
else:check('adapter_exists',False)
check('historical_regressions',read('regression.json')['passed'])
from rag.reasoning.contract import strict_parse,schema_valid
schema=json.loads((R/'datasets/stage4a/v1/target-schema.json').read_text())
for name in ['original_base_pretrain_probe.json','pretrain_probe.json','posttrain_probe.json','posttrain_base_probe.json','original_base_reload_probe.json','reload_probe.json','reload_base_probe.json']:
 if (O/name).exists():
  obj,error=strict_parse(read(name)['raw']);check('raw_schema_'+name,error is None and schema_valid(obj,schema))
 else:check('probe_exists_'+name,False)
if (O/'original_base_reload_probe.json').exists():check('original_base_recovered',read('original_base_reload_probe.json')['tokens']==read('original_base_pretrain_probe.json')['tokens'])
if (O/'training_metrics.jsonl').exists():
 metrics=lines('training_metrics.jsonl');manifest=read('subset_manifest.json');audit=read('loss-mask-audit.json')['examples']
 check('expected_step_count',len(metrics)==(len(manifest['ids'])+1)//2)
 check('exact_token_volume',sum(m['tokens'] for m in metrics)==sum(a['total'] for a in audit))
 check('exact_supervised_volume',sum(m['supervised_tokens'] for m in metrics)==sum(a['supervised'] for a in audit))

check('stage4a_tests',(O/'stage4a-tests.log').read_text().rstrip().endswith('OK'))
check('stage4b_tests',(O/'stage4b-tests.log').read_text().rstrip().endswith('OK'))
report=dict(passed=all(checks.values()),checks=checks,job=os.environ.get('SLURM_JOB_ID'))
(O/'independent-verification.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(report),flush=True)
if not report['passed']:raise SystemExit(1)
