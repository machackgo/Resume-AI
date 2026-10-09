"""Unrepaired deterministic generation; validation-only during development."""
import json,time,os,hashlib,collections
from pathlib import Path
R=Path.cwd()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2,sort_keys=True,default=lambda x: sorted(x) if isinstance(x,set) else str(x))+'\n');tmp.replace(p)
def score_evidence(row,raw):
 from rag.reasoning.contract import strict_parse,schema_valid,validate
 from rag.retrieval import InformationNeed,NeedType
 p,err=strict_parse(raw);gold=json.loads(row['messages'][2]['content']);inp=json.loads(row['messages'][1]['content'])
 schema=json.loads((R/'datasets/stage4a/v1/target-schema.json').read_text());valid=err is None and schema_valid(p,schema)
 out={'id':row['metadata']['example_id'],'expected':gold['label'],'predicted':'INVALID','raw_predicted':p.get('label','INVALID') if isinstance(p,dict) else 'INVALID','schema_valid':valid,'contract_valid':False,'compound':row['metadata']['compound'],'numeric':row['metadata']['numeric'],'family':row['metadata']['template_family'],'atomic_total':len(gold['atomic_claims']),'atomic_correct':0,'citations':0,'valid_citations':0,'entailed_citations':0,'top_level_citations':0,'valid_top_level_citations':0,'fabricated_ids':0,'unsupported_positive_atoms':0,'overclaimed_atoms':0,'positive_atoms':0,'errors':[]}
 if not valid:out['errors']=['SCHEMA'];return out
 allowed={e['evidence_id']:e for g in inp['UNTRUSTED_RETRIEVED_EVIDENCE'] for e in g['evidence']}
 need=InformationNeed(NeedType.JOB_REQUIREMENT,inp['task']['requirement'],row['metadata']['example_id'])
 _,contract=validate(raw,need,inp['task']['components'],{'provenance':allowed})
 out['errors']=contract['errors'];out['contract_valid']=not contract['errors'];out['predicted']=p['label'] if out['contract_valid'] else 'INVALID';expected={a['component_id']:a for a in gold['atomic_claims']}
 seen_atoms=set()
 for a in p['atomic_claims']:
  g=expected.get(a['component_id']);out['atomic_correct']+=bool(out['contract_valid'] and g and a['component_id'] not in seen_atoms and a['label']==g['label'] and a['claim']==g['claim']);seen_atoms.add(a['component_id'])
  out['unsupported_positive_atoms']+=bool(a['label'] in ['SUPPORTED','PARTIALLY_SUPPORTED'] and (g is None or g['label'] not in ['SUPPORTED','PARTIALLY_SUPPORTED']))
  out['positive_atoms']+=a['label'] in ['SUPPORTED','PARTIALLY_SUPPORTED']
  out['overclaimed_atoms']+=bool(a['label'] in ['SUPPORTED','PARTIALLY_SUPPORTED'] and (g is None or g['label'] in ['UNKNOWN','UNSUPPORTED'] or (a['label']=='SUPPORTED' and g['label']=='PARTIALLY_SUPPORTED')))
  for eid in a['evidence_ids']:
   out['citations']+=1;out['valid_citations']+=eid in allowed;out['fabricated_ids']+=eid not in allowed;out['entailed_citations']+=bool(g and eid in g['evidence_ids'])
 out['top_level_citations']=len(p['evidence_ids']);out['valid_top_level_citations']=sum(eid in allowed for eid in p['evidence_ids']);out['fabricated_ids']+=sum(eid not in allowed for eid in p['evidence_ids'])
 return out

def score_professional(row,raw):
 from stage4c0.io import strict_json
 from stage4c0.validate import validate_target
 from stage4c0 import contracts
 out={'id':row['metadata']['example_id'],'task':row['metadata']['task'],'schema_valid':False,'errors':[],'semantic_critic_pending':True}
 try:p=strict_json(raw)
 except Exception:out['errors']=['SCHEMA:INVALID_JSON'];return out
 errs=contracts.validate_output(p,row['metadata']['task']);out['schema_valid']=not errs
 if errs:out['errors']=['SCHEMA:'+e for e in errs];return out
 result=validate_target(row['scenario'],p,None)
 out['errors']=[e for e in result['hard_errors'] if e!='INDEPENDENT_CRITIC_REQUIRED'];out['soft_findings']=result['soft_findings'];out['claims']=result['claims'];out['status']=p['status'];out['expected_status']=row['scenario']['oracle'].get('expected_status');out['visible_words']=result.get('visible_words');out['visible_characters']=result.get('visible_characters')
 return out

def summarize(scores):
 labels=['SUPPORTED','PARTIALLY_SUPPORTED','UNKNOWN','UNSUPPORTED'];ev=scores['stage4a'];pro=scores['stage4c0'];n=len(ev)
 def ratio(x,y):return x/y if y else None
 per={}
 for lab in labels:
  tp=sum(x['expected']==lab and x['predicted']==lab for x in ev);p=ratio(tp,sum(x['predicted']==lab for x in ev)) or 0;r=ratio(tp,sum(x['expected']==lab for x in ev)) or 0
  per[lab]={'precision':p,'recall':r,'f1':2*p*r/(p+r) if p+r else 0,'support':sum(x['expected']==lab for x in ev)}
 def group(k,v):
  xs=[x for x in ev if x[k]==v];return {'correct':sum(x['predicted']==x['expected'] for x in xs),'n':len(xs)}
 return {'stage4a':{'n':n,'accuracy':ratio(sum(x['predicted']==x['expected'] for x in ev),n),'raw_label_accuracy_before_contract_gate':ratio(sum(x['raw_predicted']==x['expected'] for x in ev),n),'macro_f1':sum(x['f1'] for x in per.values())/4,'per_label':per,'atomic_accuracy':ratio(sum(x['atomic_correct'] for x in ev),sum(x['atomic_total'] for x in ev)),'compound_accuracy':group('compound',True),'atomic_case_accuracy':group('compound',False),'numeric_case_accuracy':group('numeric',True),'schema_valid':sum(x['schema_valid'] for x in ev),'contract_valid':sum(x['contract_valid'] for x in ev),'contract_error_counts':dict(collections.Counter(e for x in ev for e in x['errors'])),'citation_validity':ratio(sum(x['valid_citations'] for x in ev),sum(x['citations'] for x in ev)),'top_level_citation_validity':ratio(sum(x['valid_top_level_citations'] for x in ev),sum(x['top_level_citations'] for x in ev)),'citation_reference_precision':ratio(sum(x['entailed_citations'] for x in ev),sum(x['citations'] for x in ev)),'fabricated_ids':sum(x['fabricated_ids'] for x in ev),'overclaimed_atoms':sum(x['overclaimed_atoms'] for x in ev),'positive_atoms':sum(x['positive_atoms'] for x in ev),'overclaimed_positive_atom_rate_proxy':ratio(sum(x['overclaimed_atoms'] for x in ev),sum(x['positive_atoms'] for x in ev)),'unsupported_positive_atoms':sum(x['unsupported_positive_atoms'] for x in ev),'unsupported_positive_atom_rate_proxy':ratio(sum(x['unsupported_positive_atoms'] for x in ev),sum(x['atomic_total'] for x in ev)),'unknown_unsupported_to_supported':sum(x['expected'] in ['UNKNOWN','UNSUPPORTED'] and x['raw_predicted']=='SUPPORTED' for x in ev)},'stage4c0':{'n':len(pro),'schema_valid':sum(x['schema_valid'] for x in pro),'deterministic_pass':sum(not x['errors'] for x in pro),'error_counts':dict(collections.Counter(e.split(':')[0] for x in pro for e in x['errors'])),'by_task':{t:{'n':sum(x['task']==t for x in pro),'schema_valid':sum(x['task']==t and x['schema_valid'] for x in pro),'deterministic_pass':sum(x['task']==t and not x['errors'] for x in pro)} for t in sorted({x['task'] for x in pro})},'semantic_critic_pending':True},'limitations':['Deterministic checks are not a semantic entailment proof.','Evidence numeric-case accuracy is not independent prose numeric fidelity.','Professional rubric and semantic claim judging require Astra review.']}

def evaluate(model,tok,out,split='validation',identity=None,datasets=('stage4a','stage4c0')):
 import torch
 assert split in ['validation','test','challenge']
 assert datasets in [('stage4a','stage4c0'),('stage4c0',)]
 if split=='validation':assert datasets==('stage4a','stage4c0')
 if split!='validation':
  lock=R/'results/stage4c1/development_frozen.json';assert lock.exists(),'final exam locked until development freezes'
  assert identity is not None and identity.get('development_freeze_sha256')==sha(lock)
 assert identity is not None,'immutable model/decode identity required'
 identity_hash=__import__('hashlib').sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
 if (out/'evaluation_identity.json').exists():assert json.loads((out/'evaluation_identity.json').read_text())==identity
 else:write(out/'evaluation_identity.json',identity)
 model.eval();scores={}
 for d in ['stage4a','stage4c0']:
  if d not in datasets:scores[d]=[];continue
  if split=='challenge' and d=='stage4a':scores[d]=[];continue
  p=R/f'datasets/{d}/v1/{split}.jsonl';rows=[json.loads(l) for l in p.read_text().splitlines()];scores[d]=[]
  if split=='validation' and d=='stage4a':
   subset_path=R/'results/stage4c1/plan/validation_subset.json';assert identity['validation_subset_sha256']==sha(subset_path)
   subset=json.loads(subset_path.read_text());assert subset['source_sha256']==sha(p);allowed=set(subset['stage4a_ids']);rows=[r for r in rows if r['metadata']['example_id'] in allowed];assert len(rows)==len(allowed)==80
  for i,row in enumerate(rows):
   eid=row['metadata']['example_id'];dst=out/d/(eid+'.json')
   prompt=tok.apply_chat_template(row['messages'][:2],tokenize=False,add_generation_prompt=True,enable_thinking=False)
   prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()
   if dst.exists():
    item=json.loads(dst.read_text());assert item['prompt_sha256']==prompt_hash and item['input_file_sha256']==sha(p) and item['identity_sha256']==identity_hash
   else:
    ids=tok(prompt,add_special_tokens=False,return_tensors='pt').to('cuda');start=time.monotonic()
    with torch.inference_mode():
     generated=model.generate(**ids,do_sample=False,max_new_tokens=2048 if d=='stage4a' else 3072,use_cache=True,pad_token_id=tok.pad_token_id,eos_token_id=[tok.eos_token_id,tok.convert_tokens_to_ids('<|im_end|>')])
    tokens=generated[0,ids['input_ids'].shape[1]:].tolist();raw=tok.decode(tokens,skip_special_tokens=True)
    item={'identity_sha256':identity_hash,'id':eid,'split':split,'dataset':d,'prompt_sha256':prompt_hash,'input_file_sha256':sha(p),'raw':raw,'tokens':tokens,'seconds':time.monotonic()-start,'termination':'eos' if tokens and tokens[-1] in [tok.eos_token_id,tok.convert_tokens_to_ids('<|im_end|>')] else 'length','decoding':{'do_sample':False,'max_new_tokens':2048 if d=='stage4a' else 3072,'enable_thinking':False}}
    write(dst,item);del ids,generated
   scored=(score_evidence if d=='stage4a' else score_professional)(row,item['raw']);scores[d].append(scored)
   if 'teacher_forced_loss' not in item:
    from stage4a.data import tokenized
    from stage4b.engine import chunked_cross_entropy
    e=tokenized(row,tok);b={k:torch.tensor([e[k]],dtype=torch.long,device='cuda') for k in ['input_ids','attention_mask','labels']}
    base=model.get_base_model() if hasattr(model,'get_base_model') else model
    with torch.inference_mode():
     pos=torch.nonzero(b['labels'][0,1:]!=-100).flatten();hidden=base.model(input_ids=b['input_ids'],attention_mask=b['attention_mask'],use_cache=False).last_hidden_state
     item['teacher_forced_loss']=chunked_cross_entropy(hidden[0,pos],base.get_output_embeddings(),b['labels'][0,pos+1]).item();assert __import__('math').isfinite(item['teacher_forced_loss']),'nonfinite validation loss'
    item['supervised_tokens']=e['target_tokens'];write(dst,item);del b,hidden,pos
   scored['teacher_forced_loss']=item['teacher_forced_loss'];scored['termination']=item['termination'];scored['generation_complete']=item['termination']=='eos'
   if not scored['generation_complete']:
    scored['errors'].append('GENERATION_LENGTH_LIMIT')
    if d=='stage4a':scored['predicted']='INVALID';scored['contract_valid']=False;scored['atomic_correct']=0
   write(out/'progress.json',{'dataset':d,'done':i+1,'total':len(rows),'last_id':eid,'time':time.time()})
   print(json.dumps({'event':'validation','dataset':d,'done':i+1,'total':len(rows),'id':eid,'seconds':item['seconds']}),flush=True)
 write(out/'scores.json',scores);summary=summarize(scores)
 for d,xs in scores.items():
  if not xs:summary.pop(d,None);continue
  summary[d]['length_terminated']=sum(x['termination']=='length' for x in xs);summary[d]['mean_example_validation_loss']=sum(x['teacher_forced_loss'] for x in xs)/len(xs)
 write(out/'summary.json',summary)

def base_identity(quantization):
 model=R/'models/Qwen3.8-27B'
 return {'model_manifest_sha256':sha(R/'results/stage4c0/protected-manifest.json'),'quantization':quantization,'attention':'sdpa','validation_subset_sha256':sha(R/'results/stage4c1/plan/validation_subset.json'),'tokenizer':{p.name:sha(p) for p in model.iterdir() if p.is_file() and ('token' in p.name or p.name in ['vocab.json','merges.txt','chat_template.jinja'])},'decoding':{'do_sample':False,'stage4a_max_new_tokens':2048,'stage4c0_max_new_tokens':3072,'enable_thinking':False},'adapter':None}

def main():
 import torch,subprocess
 assert os.environ.get('SLURM_JOB_ID') and torch.cuda.device_count()==1
 assert json.loads((R/'results/stage4c1/preflight/integrity.json').read_text())['passed']
 from stage4b import engine as eng
 out=R/'results/stage4c1/base_validation';out.mkdir(parents=True,exist_ok=True);eng.OUT=out
 eng.seed();model,q=eng.load()
 from transformers import AutoTokenizer
 tok=AutoTokenizer.from_pretrained(eng.MODEL,local_files_only=True)
 write(out/f'environment_{os.environ["SLURM_JOB_ID"]}.json',{'job':os.environ['SLURM_JOB_ID'],'quantization':q.to_dict(),'gpu':torch.cuda.get_device_name(),'nvidia_smi':subprocess.check_output(['nvidia-smi'],text=True),'model':str(eng.MODEL),'adapter':None,'prepared_for_training':False})
 identity=base_identity(q.to_dict())
 evaluate(model,tok,out,identity=identity)
if __name__=='__main__':main()
