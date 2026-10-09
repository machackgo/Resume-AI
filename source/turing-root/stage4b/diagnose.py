import json,torch
from stage4b.engine import load,attach,seed,batch,reference_loss,loss,OUT,MODEL
from stage4a.data import tokenized
from transformers import AutoTokenizer
import stage4b.engine as engine
engine.OUT=OUT/'diagnosis';engine.OUT.mkdir(exist_ok=True)
seed();tok=AutoTokenizer.from_pretrained(MODEL,local_files_only=True)
ids=json.loads((OUT/'subset_manifest.json').read_text())['ids'];rows=[json.loads(l) for l in open('datasets/stage4a/v1/train.jsonl')];es=[tokenized(r,tok) for r in rows if r['metadata']['example_id'] in ids];b=batch(min(es,key=lambda x:len(x['input_ids'])))
m,q=load();m,train,lc=attach(m);m.train();results=[];grad=[]
for fun in [reference_loss,reference_loss,loss]:
 m.zero_grad(set_to_none=True);seed();v=fun(m,b);v.backward();results.append(v.item());grad.append({n:p.grad.detach().float().cpu().clone() for n,p in train.items()});del v
stats={}
for i in [1,2]:
 a=torch.cat([v.flatten() for v in grad[0].values()]).double();b=torch.cat([v.flatten() for v in grad[i].values()]).double();stats[str(i)]=dict(max_abs=(a-b).abs().max().item(),reference_norm=a.norm().item(),candidate_norm=b.norm().item(),relative_l2=((a-b).norm()/a.norm()).item(),cosine=torch.nn.functional.cosine_similarity(a,b,dim=0).item(),nonzero_reference=int((a!=0).sum()))
# Isolate the proposed change: same detached hidden states, same frozen vocabulary head.
from stage4b.engine import chunked_cross_entropy
m.eval();data=batch(min(es,key=lambda x:len(x['input_ids'])))
with torch.no_grad():
 hidden=m.get_base_model().model(input_ids=data['input_ids'],attention_mask=data['attention_mask'],use_cache=False).last_hidden_state
pos=torch.nonzero(data['labels'][0,1:]!=-100).flatten();h=hidden[0,pos].detach().requires_grad_(True);targets=data['labels'][0,pos+1];head=m.get_output_embeddings()
a_loss=torch.nn.functional.cross_entropy(head(h).float(),targets);ga=torch.autograd.grad(a_loss,h)[0].double()
b_loss=chunked_cross_entropy(h,head,targets);gb=torch.autograd.grad(b_loss,h)[0].double()
head_check=dict(reference_loss=a_loss.item(),chunked_loss=b_loss.item(),max_abs=(ga-gb).abs().max().item(),relative_l2=((ga-gb).norm()/ga.norm()).item(),cosine=torch.nn.functional.cosine_similarity(ga.flatten(),gb.flatten(),dim=0).item())
r=dict(isolated_head=head_check,losses=results,comparisons=stats,description='0 original selected-logit loss; 1 repeated original; 2 checkpointed 64-position loss; identical RNG seed')
(OUT/'loss-diagnosis.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
