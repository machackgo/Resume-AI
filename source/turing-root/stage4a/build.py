"""Generate a new release candidate, never overwrite a frozen dataset."""
import json,sys,datetime,collections
from pathlib import Path
from transformers import AutoTokenizer
from .data import ROOT,generate,write_json,tokenized,pad_batch
from .catalog import VERSION,SEED,CATALOG,SPLITS
from .validate import validate_row,leakage,historical_index,stats,sha

from .schema import schema
def main(folder):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
 tok=AutoTokenizer.from_pretrained(ROOT/'models/Qwen3.8-27B',local_files_only=True)
 rows=generate();tokens=[]
 for r in rows:tokens.append(validate_row(r,tok))
 index=historical_index();audit=leakage(rows,index)
 for split in ['train','validation','test']:
  with (folder/(split+'.jsonl')).open('x') as stream:
   for r in rows:
    if r['metadata']['split']==split:stream.write(json.dumps(r,ensure_ascii=True,separators=(',',':'))+'\n')
 counter=lambda k:dict(collections.Counter(str(r['metadata'][k]) for r in rows))
 statistics=dict(examples=len(rows),splits=counter('split'),labels=counter('expected_label'),scenario_families=counter('scenario_family'),template_families=counter('template_family'),difficulty=counter('difficulty'),compound=counter('compound'),numeric=counter('numeric'),hard_negative=counter('hard_negative'),security=counter('security'),domain=dict(collections.Counter(t for r in rows for t in r['metadata']['domain_tags'])),actions=dict(collections.Counter(t for r in rows for t in r['metadata']['action_tags'])),trust=dict(collections.Counter(t for r in rows for t in r['metadata']['trust_tags'])),tokens={k:stats([t[k] for t in tokens]) for k in tokens[0]},by_split={s:dict(labels=dict(collections.Counter(r['metadata']['expected_label'] for r in rows if r['metadata']['split']==s)),tokens={k:stats([t[k] for r,t in zip(rows,tokens) if r['metadata']['split']==s]) for k in tokens[0]}) for s in ['train','validation','test']},evidence_groups=dict(collections.Counter(len(json.loads(r['messages'][1]['content'])['UNTRUSTED_RETRIEVED_EVIDENCE']) for r in rows)),citation_atoms=dict(collections.Counter('cited' if a['evidence_ids'] else 'uncited' for r in rows for a in json.loads(r['messages'][2]['content'])['atomic_claims'])),sequence_length_risk={str(n):sum(t['total_tokens']>n for t in tokens) for n in [2048,4096,4608,6144,8192]},assistant_output_cap_risk=sum(t['target_tokens']>1536 for t in tokens))
 write_json(folder/'statistics.json',statistics);write_json(folder/'historical-exclusion.json',index);write_json(folder/'leakage.json',audit)
 write_json(folder/'schema.json',schema());(folder/'target-schema.json').write_bytes((ROOT/'rag/reasoning/schema.json').read_bytes())
 write_json(folder/'generation_config.json',dict(generator_version=VERSION,seed=SEED,families=CATALOG,split_assignment=SPLITS,variants_per_family=8,labels=['SUPPORTED','PARTIALLY_SUPPORTED','UNKNOWN','UNSUPPORTED'],example_count=1920,source_policy='authored synthetic templates only; historical records used solely for taxonomy and exclusion checks',grouping='parent template category (including all technology-substitution siblings), semantic predicate family, all counterfactual siblings and all synthetic entities; no random example split',maximum_groups=5,maximum_chunk_characters=640))
 samples=[rows[0],next(r for r in rows if r['metadata']['expected_label']=='PARTIALLY_SUPPORTED')]
 enc=[tokenized(r,tok) for r in samples];padded=pad_batch(enc,tok)
 write_json(folder/'loss-mask-audit.json',dict(passed=True,pad_token_id=tok.pad_token_id,eos_token_id=tok.eos_token_id,assistant_end_token_id=tok.convert_tokens_to_ids('<|im_end|>'),enable_thinking=False,add_generation_prompt_inference=True,add_generation_prompt_full_training=False,examples=[dict(example_id=r['metadata']['example_id'],prompt_tokens=e['input_tokens'],assistant_tokens=e['target_tokens'],boundary_tokens=tok.convert_ids_to_tokens(e['input_ids'][e['input_tokens']-12:e['input_tokens']+12]),boundary_labels=e['labels'][e['input_tokens']-12:e['input_tokens']+12],tail_tokens=tok.convert_ids_to_tokens(e['input_ids'][-8:]),padding=sum(i==0 for i in p['attention_mask']),padding_loss_masked=all(y==-100 for y,a in zip(p['labels'],p['attention_mask']) if a==0)) for r,e,p in zip(samples,enc,padded)]))
 # Artifact samples carry exact input/target, no invented summary labels.
 samples=[]
 for fid in ['container_orchestration','cloud_aws','api_rest','adaptation_qlora','adaptation_nf4','rag_finetuning','numeric_latency','verified_aws','asserted_aws','lifecycle_deploy']:
  for lab in ['SUPPORTED','UNKNOWN','UNSUPPORTED']:
   samples.append(next(r for r in rows if r['metadata']['scenario_family']==fid and r['metadata']['variant']==1 and r['metadata']['expected_label']==lab))
 samples.extend(next(r for r in rows if r['metadata']['scenario_family']=='api_rest' and r['metadata']['variant']==v and r['metadata']['expected_label']==lab) for v,lab in [(6,'PARTIALLY_SUPPORTED'),(7,'PARTIALLY_SUPPORTED'),(3,'UNKNOWN'),(7,'UNKNOWN'),(2,'SUPPORTED')])
 write_json(folder/'inspection-samples.json',samples)
 lines=['# Stage 4A representative inspection','Exact structured targets and evidence; this is a finite authored sample, not model-generated evaluation.']
 for r in samples:
  p=json.loads(r['messages'][1]['content']);lines+=['\n## '+r['metadata']['scenario_family']+' / '+str(r['metadata']['variant'])+' / '+r['metadata']['expected_label'],p['task']['requirement']]
  for g in p['UNTRUSTED_RETRIEVED_EVIDENCE']:
   for e in g['evidence']:lines+=['- '+e['evidence_id']+': '+e['content']+' [origin='+e['origin']+'; authenticated='+str(bool(e['authenticated_attestations']))+']']
  lines+=['```json',json.dumps(json.loads(r['messages'][2]['content']),indent=2),'```']
 (folder/'inspection.md').write_text('\n'.join(lines)+'\n')
 sourcefiles=list((ROOT/'stage4a').glob('*.py'))+[ROOT/'rag/reasoning/system_v2.txt',ROOT/'rag/reasoning/schema.json',ROOT/'rag/reasoning/contract.py',ROOT/'rag/component/retrieve.py',ROOT/'rag/component/decompose.py',ROOT/'results/stage3j/frozen-rag-configuration.json']
 model=ROOT/'models/Qwen3.8-27B'
 tokfiles=[model/x for x in ['tokenizer.json','tokenizer_config.json','chat_template.jinja','vocab.json','merges.txt','config.json']]
 write_json(folder/'manifest.json',dict(dataset_version='stage4a-v1',status='validated_candidate_pending_tests',generation_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),generator_version=VERSION,seed=SEED,schema_version='stage4a-record-v1 + frozen stage3g-v2 target',frozen_rag_contract='results/stage3j/frozen-rag-configuration.json',qwen_tokenizer=str(model.relative_to(ROOT)),qwen_chat_template_sha256=sha(model/'chat_template.jinja'),tokenizer_files={str(p.relative_to(ROOT)):sha(p) for p in tokfiles},counts=statistics['splits'],example_count=len(rows),label_distribution=statistics['labels'],scenario_distribution=statistics['scenario_families'],difficulty_distribution=statistics['difficulty'],token_statistics=statistics['tokens'],historical_benchmark_fingerprints_file='historical-exclusion.json',source_checksums={str(p.relative_to(ROOT)):sha(p) for p in sourcefiles},checksums={p.name:sha(p) for p in sorted(folder.iterdir()) if p.is_file()}))
 print(json.dumps(statistics,indent=2),flush=True)
if __name__=='__main__':main(sys.argv[1])
