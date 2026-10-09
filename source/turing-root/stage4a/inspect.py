"""CPU-only historical audit and architecture inspection; never loads weights."""
import hashlib,json,struct,math,os,importlib.metadata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/stage4a'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def main():
 OUT.mkdir(exist_ok=True)
 checks={}
 for name in ['protected-manifest.json','final-manifest.json']:
  d=json.loads((ROOT/'results/stage3j'/name).read_text());bad=[p for p,h in d.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
  checks[name]={'files':len(d),'changed':bad};assert not bad,(name,bad)
 dump(OUT/'inherited-protection.json',checks)
 protected={}
 for parent in ['rag','tests/rag','eval','fixtures','migrations','models','hf-cache','docs','results']:
  for p in sorted((ROOT/parent).rglob('*')):
   if not p.is_file() or 'stage4a' in str(p) or '__pycache__' in str(p):continue
   protected[str(p.relative_to(ROOT))]=sha(p)
 for p in ROOT.glob('*.py'):protected[p.name]=sha(p)
 dump(OUT/'protected-manifest.json',protected)
 print('PROTECTED',len(protected),flush=True)
 # Safetensors header shapes only; no tensors allocated, no adapters instantiated.
 shapes={}
 for p in sorted((ROOT/'models/Qwen3.8-27B').glob('*.safetensors')):
  with p.open('rb') as f:
   n=struct.unpack('<Q',f.read(8))[0];header=json.loads(f.read(n))
  for k,v in header.items():
   if k!='__metadata__':shapes[k]=v['shape']
 text={k:v for k,v in shapes.items() if 'language_model' in k or k.startswith('lm_head')}
 projections={k:v for k,v in text.items() if len(v)==2 and any(t in k for t in ['self_attn.','linear_attn.','mlp.'])}
 groups={}
 for k,v in projections.items():
  suffix=k.split('.')[-2];g=groups.setdefault(suffix,{'count':0,'parameters':0,'shape_counts':{}});g['count']+=1;g['parameters']+=math.prod(v);s=str(v);g['shape_counts'][s]=g['shape_counts'].get(s,0)+1
 candidates=[]
 for scope in ['full_attention_only','hybrid_attention','hybrid_attention_and_mlp']:
  chosen={k:v for k,v in projections.items() if scope=='hybrid_attention_and_mlp' or '.mlp.' not in k and (scope=='hybrid_attention' or '.self_attn.' in k)}
  for rank in [8,16,32]:
   n=sum(rank*sum(v) for v in chosen.values());candidates.append(dict(scope=scope,rank=rank,modules=len(chosen),trainable_parameters=n,percent_text=100*n/sum(math.prod(v) for v in text.values()),suffixes=sorted({k.split('.')[-2] for k in chosen})))
 dump(OUT/'architecture.json',dict(method='safetensors headers; no weight loading',checkpoint_parameters=sum(math.prod(v) for v in shapes.values()),text_parameters=sum(math.prod(v) for v in text.values()),projection_groups=groups,candidates=candidates,projection_shapes=projections,config=json.loads((ROOT/'models/Qwen3.8-27B/config.json').read_text())))
 dump(OUT/'environment.json',{p:importlib.metadata.version(p) for p in ['torch','transformers','accelerate','bitsandbytes','tokenizers','peft','trl','datasets']})
 files=['results/stage3g/benchmark-2330445/scored.json','results/stage3h/benchmark-2332803/scored.json','results/stage3i/benchmark-2333661/scored.json','results/stage3j/benchmark-2334090/scored.json']
 failures=[]
 for name in files:
  rows=json.loads((ROOT/name).read_text())
  for r in rows:
   if r.get('arm') not in ('component','rag3','rag5'):continue
   if r.get('retrieval_loss') or r.get('gold')!=r.get('context_gold'):continue
   if not r.get('failures'):continue
   failures.append(dict(source=name,source_sha256=sha(ROOT/name),id=r['id'],arm=r['arm'],scale=r.get('scale'),category=r['category'],predicted=r['predicted'],gold=r['gold'],atomic_correct=r['atomic_correct'],atomic_total=r['atomic_total'],failures=r['failures'],false_contradiction=r.get('false_contradiction'),unjustified_partial=r.get('unjustified_partial'),nonentailing_citations=sum(not x['entailed'] for x in r.get('citation_pairs',[])),correct_evidence_delivered=True))
 objectives=[('unknown_vs_unsupported','measured','Missing or adjacent evidence cannot contradict.'),('citation_entailment','measured','Exact existing IDs must entail the cited atom; quote traceability is insufficient.'),('calibrated_positive','measured','Direct deployment proof and paraphrased construction merit support.'),('action_strength','measured','Consumption, study, implementation, deployment and operation are distinct.'),('technology_identity','measured','Related frameworks, clouds and adaptation methods are not interchangeable.'),('numeric_grounding','measured','Only exact same-event metrics justify numeric claims.'),('compound_composition','measured','Preserve component labels and frozen aggregation, including mixed contradiction/support.'),('structured_output','measured','Strict JSON, unchanged component text/IDs, union citations and nonempty missing_evidence for denials.'),('unjustified_partial','preventive_and_stage3g','Real supported material parts required; Stage3J count is zero.'),('trust_verification','preventive','Assertions are not authenticated verification.'),('corroboration','preventive','Copies are not independent proof and cannot repair missing entailment.'),('untrusted_instructions','preventive','Instructions in evidence are data; Stage3J had zero explicit attack successes.')]
 dump(OUT/'failure-taxonomy.json',dict(selection='RAG arms only; retrieval_loss false and gold equals context_gold; historical cases excluded from generated dataset',records=failures,objectives=[dict(id=a,status=b,objective=c) for a,b,c in objectives]))
 print('INSPECTION COMPLETE',len(failures),flush=True)
if __name__=='__main__':main()
