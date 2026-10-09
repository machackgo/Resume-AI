"""Create immutable messages-only sampling plans after frozen data validation."""
import json,random,collections,hashlib
from pathlib import Path
from transformers import AutoTokenizer
from stage4a.data import tokenized,pad_batch
R=Path.cwd(); O=R/'results/stage4c1/plan'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v): (O/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def main():
 assert json.loads((R/'results/stage4c1/preflight/integrity.json').read_text())['passed']
 assert not O.exists(),'refuse to overwrite sampling plan'
 O.mkdir(parents=True)
 tok=AutoTokenizer.from_pretrained(R/'models/Qwen3.8-27B',local_files_only=True)
 pools={};enc={};excluded=set();source={}
 for d,splits in [('stage4a',['train','validation','test']),('stage4c0',['train','validation','test','challenge'])]:
  for split in splits:
   p=R/f'datasets/{d}/v1/{split}.jsonl';source[str(p.relative_to(R))]=sha(p)
   rows=[json.loads(l) for l in p.read_text().splitlines()]
   assert all(r['metadata']['split']==split for r in rows)
   if split!='train':excluded.update(r['metadata']['example_id'] for r in rows);continue
   pools[d]=rows
   for r in rows:
    eid=r['metadata']['example_id'];e=tokenized(r,tok);assert e['total_tokens']<=4233
    enc[eid]=e
 assert len(pools['stage4a'])==1600 and len(pools['stage4c0'])==119
 assert not excluded.intersection(enc)
 rng=random.Random(430001);a=pools['stage4a'][:];rng.shuffle(a)
 weights=json.loads((R/'datasets/stage4c0/v1/future_curriculum_experiment.v1.json').read_text())['professional_task_order_weights']
 queues=collections.defaultdict(list)
 for r in pools['stage4c0']:queues[r['metadata']['task']].append(r)
 for q in queues.values():rng.shuffle(q)
 c=[]
 while any(queues.values()):
  tasks=sorted(t for t,q in queues.items() if q);t=rng.choices(tasks,weights=[weights[t] for t in tasks])[0];c.append(queues[t].pop())
 def mass(rows):return sum(enc[r['metadata']['example_id']]['target_tokens'] for r in rows)
 def closest(pool,budget):
  out=[];total=0
  for r in pool:
   n=enc[r['metadata']['example_id']]['target_tokens']
   if total+n>=budget:
    if abs(total+n-budget)<abs(total-budget):out.append(r)
    break
   out.append(r);total+=n
  return out
 P=mass(c);replay=closest(a,P);control=closest(a,P+mass(replay))
 inter=[];ar=iter(replay);cr=iter(c);am=cm=0
 while True:
  if am<=cm:
   r=next(ar,None)
   if r is None:inter.extend(cr);break
   am+=enc[r['metadata']['example_id']]['target_tokens']
  else:
   r=next(cr,None)
   if r is None:inter.extend(ar);break
   cm+=enc[r['metadata']['example_id']]['target_tokens']
  inter.append(r)
 for name,rows in [('evidence_only',control),('interleaved',inter)]:
  entries=[]
  for r in rows:
   m=r['metadata'];eid=m['example_id'];e=enc[eid]
   entries.append({'id':eid,'dataset':'stage4c0' if eid.startswith('s4c0_') else 'stage4a','task':m.get('task','EVIDENCE_REASONING'),'label':m.get('expected_label'),'target_tokens':e['target_tokens'],'total_tokens':e['total_tokens']})
  out={'seed':430001,'source_sha256':source,'entries':entries,'unique_examples':len({x['id'] for x in entries}),'effective_exposures':len(entries),'target_tokens':mass(rows),'steps':(len(entries)+1)//2,'checkpoints':sorted(set([max(1,((len(entries)+1)//2)//2),(len(entries)+1)//2])),'task_exposures':dict(collections.Counter(x['task'] for x in entries)),'dataset_exposures':dict(collections.Counter(x['dataset'] for x in entries)),'dataset_target_tokens':{d:sum(x['target_tokens'] for x in entries if x['dataset']==d) for d in ['stage4a','stage4c0']},'max_exposures_per_record':1}
  dump(name+'.json',out)
 chosen=[pools['stage4a'][0]]+[next(r for r in pools['stage4c0'] if r['metadata']['task']==t) for t in ['ANALYZE_JOB','GENERATE_RESUME','GENERATE_COVER_LETTER','ANSWER_APPLICATION_QUESTION']]
 audit=[]
 for r in chosen:
  e=enc[r['metadata']['example_id']];n=e['input_tokens']
  assert e['labels'][:n]==[-100]*n and e['labels'][n:]==e['input_ids'][n:]
  assert tok.decode(e['input_ids'][n:-1])==r['messages'][2]['content']
  assert e['labels'][-1]==tok.convert_tokens_to_ids('<|im_end|>')
  audit.append({'id':r['metadata']['example_id'],'task':r['metadata'].get('task','EVIDENCE_REASONING'),'prompt_tokens':n,'assistant_tokens':e['target_tokens'],'total_tokens':e['total_tokens'],'boundary':[{'position':i,'token':tok.convert_ids_to_tokens(e['input_ids'][i]),'label':e['labels'][i]} for i in range(n-4,n+4)]})
 padded=pad_batch([enc[r['metadata']['example_id']] for r in chosen],tok)
 assert all(l==-100 for e in padded for l,a in zip(e['labels'],e['attention_mask']) if a==0)
 dump('loss-mask-audit.json',{'passed':True,'examples':audit,'padding_tokens':sum(e['attention_mask'].count(0) for e in padded),'model_weights_loaded':False})
 dump('train-token-distribution.json',{d:{k:sorted(enc[r['metadata']['example_id']][k] for r in rows) for k in ['input_tokens','target_tokens','total_tokens']} for d,rows in pools.items()})
 print(json.dumps({'passed':True,'professional_target_tokens':P,'interleaved_examples':len(inter),'evidence_only_examples':len(control)}))
if __name__=='__main__':main()
