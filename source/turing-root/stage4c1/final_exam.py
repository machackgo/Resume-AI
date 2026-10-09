"""One sealed final examination per frozen model; never launches optimization."""
import json,os,sys,random
from pathlib import Path
import torch
from stage4b import engine as eng
from stage4c1.evaluate import evaluate,write,sha
R=Path.cwd()
def main(label):
 assert label in ['base','selected','evidence_only'] and os.environ.get('SLURM_JOB_ID')
 lock=R/'results/stage4c1/development_frozen.json';assert lock.exists()
 selected=json.loads(lock.read_text());assert selected['development_frozen'] is True and selected['further_training_forbidden'] is True
 out=R/'results/stage4c1/final_exam'/label;out.mkdir(parents=True,exist_ok=True);eng.OUT=out
 random.seed(430001);torch.manual_seed(430001);torch.cuda.manual_seed_all(430001)
 m,q=eng.load();tok=eng.AutoTokenizer.from_pretrained(eng.MODEL,local_files_only=True)
 identity={'development_freeze_sha256':sha(lock),'label':label,'base_manifest_sha256':sha(R/'results/stage4c0/protected-manifest.json'),'quantization':q.to_dict(),'tokenizer_files':{p.name:sha(p) for p in eng.MODEL.iterdir() if p.is_file() and ('token' in p.name or p.name in ['vocab.json','merges.txt','chat_template.jinja'])},'decoding':{'do_sample':False,'enable_thinking':False,'stage4a_max_new_tokens':2048,'stage4c0_max_new_tokens':3072}}
 if label!='base':
  chosen=selected if label=='selected' else selected['evidence_only_comparator']
  p=R/chosen['checkpoint'];assert sha(p/'checksums.json')==chosen['checkpoint_checksums_sha256']
  assert all(sha(p/n)==h for n,h in json.loads((p/'checksums.json').read_text()).items())
  for parameter in m.parameters():
   parameter.requires_grad_(False)
   if parameter.__class__.__name__!='Params4bit' and parameter.ndim==1 and parameter.dtype==torch.bfloat16:parameter.data=parameter.data.float()
  from peft import PeftModel
  m=PeftModel.from_pretrained(m,p,is_trainable=False)
  assert not any(p.requires_grad for p in m.parameters())
  state=torch.load(p/'training_state.pt',map_location='cpu',weights_only=False)
  assert eng.fingerprint({n:p for n,p in m.named_parameters() if 'lora_A.default.weight' in n or 'lora_B.default.weight' in n})==state['adapter_fingerprint']
  identity['adapter_checksums_sha256']=chosen['checkpoint_checksums_sha256']
  cfg=json.loads((p/'training_config.json').read_text());arm=cfg['arm'];step=state['step']
  plan=json.loads((p/'mixture.json').read_text());probe_id=plan['entries'][0]['id']
  row=next(r for r in map(json.loads,(R/'datasets/stage4a/v1/train.jsonl').read_text().splitlines()) if r['metadata']['example_id']==probe_id)
  reloaded=eng.probe(m,tok,row,'reload_train_probe.json')
  original=json.loads((R/f'results/stage4c1/{arm}/adapter_train_probe_{step:06d}.json').read_text())
  with m.disable_adapter():recovered=eng.probe(m,tok,row,'recovered_base_train_probe.json')
  base_probe=json.loads((R/f'results/stage4c1/{arm}/prepared_base_train_probe.json').read_text())
  checks={'adapter_tokens_equal':reloaded['tokens']==original['tokens'],'adapter_scores_equal':reloaded['signature']==original['signature'],
          'base_tokens_equal':recovered['tokens']==base_probe['tokens'],'base_scores_equal':recovered['signature']==base_probe['signature']}
  write(out/'adapter_reload_verified.json',{'passed':all(checks.values()),'checks':checks,'adapter_fingerprint':state['adapter_fingerprint'],'checkpoint':chosen['checkpoint'],'train_probe_id':probe_id})
  assert all(checks.values()),'reload or prepared-base recovery failure'
 else:identity['adapter']=None
 datasets=('stage4c0',) if label=='evidence_only' else ('stage4a','stage4c0')
 identity['exam_datasets']=list(datasets)
 for split in ['test','challenge']:
  evaluate(m,tok,out/split,split=split,identity=identity,datasets=datasets)
 if label!='evidence_only':
  from stage4c1.historical_exam import historical_exam
  historical_exam(m,tok,out/'historical',identity)
 write(out/'curriculum_exam_complete.json',{'passed':True,'identity':identity,'note':'Evaluation completion is not a promotion decision.'})
if __name__=='__main__':main(sys.argv[1])
