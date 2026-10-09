"""Standalone, fail-closed validation. Does not regenerate or silently repair data.
Run: python -B -m stage4a.validate datasets/stage4a/v1
"""
import json,re,sys,hashlib,statistics,math
from collections import Counter,defaultdict
from pathlib import Path
from .catalog import CATALOG,SPLITS,VERSION,NOTICE
from .data import ROOT,LABELS,canonical,digest,predicates,claim_text,fact_text,entry,oracle,tokenized,scenario,entity
from rag.reasoning.contract import strict_parse,validate as frozen_validate
from rag.retrieval import InformationNeed,NeedType
from rag.component.retrieve import messages
from rag.component.decompose import RequirementDecomposer

def ensure(b,msg):
 if not b:raise ValueError(msg)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def norm(s):return ' '.join(re.findall(r'\w+|%|\$',s.casefold()))
def stats(xs):
 s=sorted(xs)
 return dict(mean=statistics.mean(s),median=statistics.median(s),p90=s[math.ceil(len(s)*.9)-1],p95=s[math.ceil(len(s)*.95)-1],maximum=max(s),minimum=min(s),sum=sum(s))
def historical_index():
 files=[ROOT/'fixtures/rag/reasoning_eval/stage3g_v1.json']
 for stage in ['stage3g','stage3h','stage3i','stage3j']:
  for p in (ROOT/'results'/stage).glob('*.json'):
   if any(x in p.name for x in ['dataset','prepared','smoke_fixture']):files.append(p)
 strings=set()
 def walk(x):
  if isinstance(x,dict):
   for k,v in x.items():
    if k in ('requirement','claim','content','text') and isinstance(v,str) and len(v.split())>=5:strings.add(norm(v))
    else:walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 for p in files:walk(json.loads(p.read_text()))
 return dict(files={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(files))},normalized_fingerprints=sorted(digest(s) for s in strings),normalized_texts=sorted(strings),policy='all requirements, component claims and evidence strings from all top-level Stage3G-J datasets/prepared fixtures; no model answers used to generate examples')

def validate_row(row,tok=None,limit=4608):
 from .schema import schema,conforms
 ensure(conforms(row,schema()),'record JSON schema')
 ensure(set(row)=={'metadata','messages','oracle'},'row schema')
 m=row['metadata'];fid=m['scenario_family'];v=m['variant'];ensure(fid in CATALOG and type(v)==int and 0<=v<8,'catalog family/variant')
 ensure(m['template_family']==CATALOG[fid]['category'],'parent template family')
 ensure(m['domain_tags']==[CATALOG[fid]['domain']] and m['action_tags']==[CATALOG[fid]['action']],'domain/action tags')
 ensure(m['generator_version']==VERSION and m['split']==SPLITS[fid],'split/version')
 ensure(m['scenario_id']==scenario(fid,v),'scenario id')
 ensure(m['expected_label'] in LABELS,'label vocabulary')
 ensure(m['example_id']=='s4a_'+digest(m['scenario_id']+m['expected_label'])[:24],'stable example ID')
 ensure(m['candidate']=='synthetic_'+digest(m['scenario_id'])[:24],'synthetic owner')
 msg=row['messages'];ensure(len(msg)==3 and [x['role'] for x in msg]==['system','user','assistant'],'messages roles')
 ensure(all(set(x)=={'role','content'} and isinstance(x['content'],str) for x in msg),'message schema')
 ensure(msg[0]['content']==(ROOT/'rag/reasoning/system_v2.txt').read_text(),'frozen system')
 payload,err=strict_parse(msg[1]['content']);ensure(err is None,'user parse')
 target,err=strict_parse(msg[2]['content']);ensure(err is None,'assistant parse')
 ensure(msg[2]['content']==json.dumps(target,ensure_ascii=True,separators=(',',':')),'canonical strict JSON target')
 spec=row['oracle']['spec'];facts=row['oracle']['facts'];ensure(set(spec)=={'event','predicates'} and spec['event']==entity(fid,v),'event identity')
 ps=spec['predicates'];ensure(1<=len(ps)<=4 and ps==predicates(fid,v)[:len(ps)],'technology/action/numeric identity')
 ensure(m['compound']==(len(ps)>1) and m['numeric']==(CATALOG[fid]['category']=='numeric'),'structure tags')
 components=[dict(id='a'+str(i+1),claim=claim_text(p,spec['event'])) for i,p in enumerate(ps)]
 requirement='; '.join(c['claim'].rstrip('.') for c in components)+'.'
 ensure(payload['task']['components']==components and payload['task']['requirement']==requirement,'atomic component consistency')
 bykey={p['key']:p for p in ps};ids=set();entries={}
 for f in facts:
  ensure(set(f)=={'id','owner','predicate','kind','event','attested','source_type','origin','lineage','verbose'},'fact schema')
  ensure(f['owner']==m['candidate'],'candidate isolation')
  ensure(re.fullmatch('evidence_[0-9a-f]{64}',f['id']) and f['id'] not in ids,'evidence ID unique');ids.add(f['id'])
  ensure(f['predicate'] in bykey and f['kind'] in ['positive','adjacent','denial','noise','injection'],'fact identity')
  ensure(f['event'] in (spec['event'],spec['event']+'-previous'),'event isolation')
  ensure(f['source_type'] in ['resume','github','linkedin','veribridge'] and f['origin'] in ['candidate_supplied','externally_observed'],'source metadata')
  ensure(type(f['attested'])==bool and (not f['attested'] or f['kind'] in ['positive','denial']),'attestation scope')
  ensure(re.fullmatch('synthetic_source_[0-9a-f]{24}',f['lineage']),'source lineage')
  entries[f['id']]=entry(f,bykey[f['predicate']],v)
  ensure(len(entries[f['id']]['content'])<=640,'frozen chunk budget')
 actual=[e for g in payload['UNTRUSTED_RETRIEVED_EVIDENCE'] for e in g['evidence']]
 ensure(all(set(g)=={'evidence'} and g['evidence'] for g in payload['UNTRUSTED_RETRIEVED_EVIDENCE']),'group schema')
 ensure(len(payload['UNTRUSTED_RETRIEVED_EVIDENCE'])<=5,'frozen group budget')
 ensure(len(actual)==len(entries) and {e['evidence_id']:e for e in actual}==entries,'malformed content/trust/numeric/action/source or evidence ownership')
 # Content allowlist by structured authored renderer is stronger than regex PII scans.
 for e in actual:
  ensure(not re.search(r'@|https?://|mohammed|mubashir|linkedin.com|github.com',e['content'],re.I),'private data')
 ensure(len({g['evidence'][0]['content'] for g in payload['UNTRUSTED_RETRIEVED_EVIDENCE']})==len(payload['UNTRUSTED_RETRIEVED_EVIDENCE']),'duplicate groups')
 ensure(all(len({e['content'] for e in g['evidence']})==1 for g in payload['UNTRUSTED_RETRIEVED_EVIDENCE']),'group content equality')
 need=InformationNeed(NeedType.JOB_REQUIREMENT,requirement,m['example_id']);dec=RequirementDecomposer().decompose(need)
 ctx=dict(groups=payload['UNTRUSTED_RETRIEVED_EVIDENCE'],provenance={i:dict(content=e['content']) for i,e in entries.items()},component_notice=NOTICE,component_retrieval=[dict(component_id=c.component_id,text=c.text,evidence_ids=sorted(ids),status='selected_candidates' if ids else 'no_plausible_candidate_retrieved') for c in dec.components])
 ensure(msg[:2]==messages(need,components,ctx),'frozen message builder compatibility')
 parsed,valid=frozen_validate(msg[2]['content'],need,components,ctx);ensure(valid['schema_valid'] and not valid['errors'],'frozen output contract: '+str(valid))
 expected=oracle(spec,facts)
 for atom,(label,citations,reason) in zip(target['atomic_claims'],expected):
  ensure(atom['label']==label,'atomic entailment label')
  ensure(atom['evidence_ids']==citations,'citation entailment')
  ensure(atom['reason']==reason,'grounded concise atomic explanation')
 ensure(target['label']==m['expected_label'],'overall metadata')
 ensure((target['label']=='SUPPORTED')==(not target['missing_evidence']),'missing evidence semantics')
 expected_missing=[a['claim']+(' Resolve the explicit contradictory record.' if a['label']=='UNSUPPORTED' else ' Supply direct evidence or resolve uncertainty.') for a in target['atomic_claims'] if a['label']!='SUPPORTED']
 ensure(target['missing_evidence']==expected_missing,'grounded missing evidence')
 expected_reason={'SUPPORTED':'All material components have direct cited support.','PARTIALLY_SUPPORTED':'Direct evidence establishes some material components; the remaining components are unestablished or contradicted.','UNKNOWN':'The available evidence cannot establish support or a resolved contradiction.','UNSUPPORTED':'An explicit contradiction is established and no material component has direct support.'}[target['label']]
 ensure(target['reason']==expected_reason,'grounded overall explanation')
 ensure(len(target['reason'])<250 and all(len(a['reason'])<250 for a in target['atomic_claims']),'no hidden traces')
 if tok is not None:
  enc=tokenized(row,tok);ensure(enc['total_tokens']<=limit,'sequence length risk; no truncation permitted')
  ensure(enc['target_tokens']>0 and all(x==-100 for x in enc['labels'][:enc['input_tokens']]),'loss mask')
  return {k:enc[k] for k in ['input_tokens','target_tokens','total_tokens']}
 return None

def fingerprint(row):
 p=json.loads(row['messages'][1]['content'])
 return p['task']['requirement']+'\n'+'\n'.join(e['content'] for g in p['UNTRUSTED_RETRIEVED_EVIDENCE'] for e in g['evidence'])
def family_signature(fid):
 f=CATALOG[fid];return set(norm(f['claim']+' '+f['positive']+' '+f['adjacent']).split())
def leakage(rows,index):
 family=defaultdict(set);scenarios=defaultdict(set);owners=defaultdict(set);exact={};normalized={};hist=set(index['normalized_fingerprints']);collisions=[];allids=set()
 for row in rows:
  m=row['metadata'];s=m['split'];family[m['template_family']].add(s);scenarios[m['scenario_id']].add(s);owners[m['candidate']].add(s)
  ensure(m['example_id'] not in allids,'duplicate example ID');allids.add(m['example_id'])
  text=fingerprint(row)
  for table,value in [(exact,text),(normalized,norm(text))]:
   h=digest(value)
   if h in table:ensure(table[h]==s,'cross-split duplicate')
   table[h]=s
  payload=json.loads(row['messages'][1]['content'])
  texts=[payload['task']['requirement']]+[a['claim'] for a in payload['task']['components']]+[e['content'] for g in payload['UNTRUSTED_RETRIEVED_EVIDENCE'] for e in g['evidence']]
  for t in texts:
   if digest(norm(t)) in hist:collisions.append(m['example_id'])
 ensure(all(len(s)==1 for s in family.values()),'template-family split leakage')
 ensure(all(len(s)==1 for s in scenarios.values()),'scenario split leakage')
 ensure(all(len(s)==1 for s in owners.values()),'entity split leakage')
 ensure(not collisions,'historical benchmark exact/normalized leakage')
 # Semantic-family lexical overlap strips entities, IDs and shared JSON/schema.
 # Predicate identity is the grouping boundary, not a paraphrase ID.
 high=[];maximum=0
 semantic_splits={r['metadata']['scenario_family']:r['metadata']['split'] for r in rows}
 fids=sorted(semantic_splits)
 for i,a in enumerate(fids):
  for b in fids[i+1:]:
   if semantic_splits[a]==semantic_splits[b]:continue
   x,y=family_signature(a),family_signature(b);overlap=len(x&y)/len(x|y);maximum=max(maximum,overlap)
   if overlap>=.85:high.append([a,b,overlap])
 ensure(not high,'suspicious cross-split semantic-template overlap')
 # Historical approximate overlap on 5-word shingles, only content-bearing text.
 def shingles(s):
  w=norm(s).split();return {tuple(w[i:i+5]) for i in range(len(w)-4)}
 old=[shingles(t) for t in index['normalized_texts'] if len(t.split())>=12]
 new=[shingles(fingerprint(r)) for r in rows]
 inv=defaultdict(set)
 for j,ss in enumerate(old):
  for sh in ss:inv[sh].add(j)
 hist_max=0.;hist_hits=[]
 for i,ss in enumerate(new):
  candidate=set().union(*(inv.get(sh,set()) for sh in ss)) if ss else set()
  for j in candidate:
   if not old[j]:continue
   overlap=len(ss&old[j])/len(ss|old[j]);hist_max=max(hist_max,overlap)
   if overlap>=.85:hist_hits.append([rows[i]['metadata']['example_id'],j,overlap])
 ensure(not hist_hits,'historical near duplicate')
 return dict(known_leakage=0,exact_cross_split_duplicates=0,normalized_cross_split_duplicates=0,template_family_cross_split_overlap=0,scenario_cross_split_overlap=0,entity_cross_split_overlap=0,historical_collisions=0,historical_fingerprint_count=len(hist),near_overlap_threshold=.85,max_cross_split_family_token_jaccard=maximum,max_historical_fivegram_jaccard=hist_max,limitation='Lexical checks cannot prove absence of semantic contamination; shared reasoning categories and generic secondary predicates are intentional. No exact benchmark cases are reused.')

def validate_release(folder,tok,check_manifest=True):
 folder=Path(folder);rows=[];counts={}
 for split in ['train','validation','test']:
  rs=[]
  for line in (folder/(split+'.jsonl')).read_text().splitlines():
   r,e=strict_parse(line);ensure(e is None,'JSONL parse');ensure(r['metadata']['split']==split,'split membership');rs.append(r)
  counts[split]=len(rs);rows.extend(rs)
 tokens=[validate_row(r,tok) for r in rows]
 index=json.loads((folder/'historical-exclusion.json').read_text())
 for p,h in index['files'].items():ensure(sha(ROOT/p)==h,'historical fingerprint source changed')
 audit=leakage(rows,index)
 for split in counts:
  labels=Counter(r['metadata']['expected_label'] for r in rows if r['metadata']['split']==split)
  ensure(set(labels)==set(LABELS) and max(labels.values())==min(labels.values()),'label balance')
 result=dict(passed=True,examples=len(rows),split_counts=counts,label_counts=dict(Counter(r['metadata']['expected_label'] for r in rows)),token_statistics={k:stats([t[k] for t in tokens]) for k in tokens[0]},leakage=audit,truncation_count=0)
 ensure(result['token_statistics']==json.loads((folder/'statistics.json').read_text())['tokens'],'token statistics drift')
 if check_manifest:
  manifest=json.loads((folder/'manifest.json').read_text())
  ensure(manifest['counts']==counts and manifest['example_count']==len(rows),'manifest counts')
  for p,h in manifest['checksums'].items():ensure(sha(folder/p)==h,'release checksum '+p)
  for p,h in manifest['source_checksums'].items():ensure(sha(ROOT/p)==h,'source checksum '+p)
 return result

def main():
 from transformers import AutoTokenizer
 folder=Path(sys.argv[1]);tok=AutoTokenizer.from_pretrained(ROOT/'models/Qwen3.8-27B',local_files_only=True)
 print(json.dumps(validate_release(folder,tok),indent=2))
if __name__=='__main__':main()
