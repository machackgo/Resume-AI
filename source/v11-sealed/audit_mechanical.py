"""Independent mechanical checks. Semantic judgments must be supplied separately."""
import sys,json,hashlib
from pathlib import Path
from jsonschema import Draft202012Validator
D=Path(__file__).resolve().parent;run=D/sys.argv[1]
def sha(text):return hashlib.sha256(text.encode()).hexdigest()
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
sources={s['id']:s for s in json.loads((D/'inputs/candidate_sources.json').read_text())}
evidence={e['source_id']:e for e in json.loads((D/'inputs/canonical-evidence.json').read_text())}
inputs={c['id']:c for c in json.loads((D/'inputs/benchmark.json').read_text())['cases']+json.loads((D/'inputs/stress-inputs.json').read_text())}
validator=Draft202012Validator(json.loads((D/'application/resume_pipeline/output.schema.json').read_text()))
rows=[]
for p in sorted(list(run.glob('case-J*.json'))+list(run.glob('stress-S*.json'))):
 r=json.loads(p.read_text());issues=[];final=r.get('resume');claims=[c for s in (final or {}).get('sections',[]) for c in s['claims']]
 if r.get('raw_job_sha256')!=sha(inputs[r['id']]['job_text']):issues.append('benchmark job hash mismatch')
 if final:issues += ['schema: '+e.message for e in validator.iter_errors(final)]
 for c in claims:
  e=evidence[c['source_id']];text=sources[json.loads(e['metadata_json'])['id']]['text'].replace('\r\n','\n').replace('\r','\n');a,b=c['span'];heading=c.get('source_context')
  checks={'span':text[a:b]==c['text'],'canonical_hash':sha(text)==e['normalized_hash'],'version':c['source_version']==e['version'],'candidate':final['candidate_id']==e['scope']['candidate_id']}
  if heading:
   checks['heading_span']=text[heading['start']:heading['end']]==heading['text']
   checks['scope_spans']=all(text[h['start']:h['end']]==h['text'] for h in heading.get('document_scope',[]))
  expected='event_'+sha(json.dumps([e['scope'],c['source_id'],c['source_version'],heading['start'] if heading else 0],sort_keys=True))[:24]
  checks['event']=c['event_id']==expected
  identity=c.get('semantic_identity',{})
  checks['typed_candidate']=identity.get('candidate_id')==final['candidate_id']
  checks['typed_evidence']=identity.get('canonical_evidence_id')==e['evidence_id']
  checks['typed_source']=identity.get('source_id')==c['source_id']
  checks['typed_span']=identity.get('provenance',{}).get('start')==a and identity.get('provenance',{}).get('end')==b
  for cid in c['evidence_ids']:
   ref=final['provenance'].get(cid,{}).get('reference',{})
   checks['citation:'+cid]=ref.get('source_id')==c['source_id'] and ref.get('scope')==e['scope'] and ref.get('evidence_id')==e['evidence_id'] and ref.get('source_version')==c['source_version']
  for link in c.get('licensed_relationships',[]):
   for support in link.get('supporting_technology_evidence',[]):
    se=evidence[support['source_id']];st=sources[json.loads(se['metadata_json'])['id']]['text'].replace('\r\n','\n').replace('\r','\n');sa,sb=support['span'];typed=support['semantic_identity']
    if st[sa:sb]!=support['text'] or support['source_version']!=se['version'] or support['canonical_evidence_id']!=se['evidence_id']:issues.append('noncanonical final supporting technology evidence')
    if typed.get('candidate_id')!=final['candidate_id'] or typed.get('canonical_evidence_id')!=se['evidence_id'] or typed.get('source_id')!=support['source_id']:issues.append('final supporting technology identity mismatch')
    if typed.get('provenance',{}).get('start')!=sa or typed.get('provenance',{}).get('end')!=sb:issues.append('final supporting technology typed span mismatch')
  issues.extend(c['claim_id']+': '+k for k,v in checks.items() if not v)
 declared_windows={}
 for item in walk(r):
  if 'reference' in item and 'content' in item and 'context_span' in item:
   key=json.dumps([item['reference'],item['content']],sort_keys=True)
   declared_windows.setdefault(key,set()).add(tuple(item['context_span']))
 batches=r.get('batches',[r]);ids={};inferences={};span_checks=0;source_windows=0;reused_context_spans=0
 for x in walk(r):
  if 'assertion_anchor' in x:
   anchor=x['assertion_anchor'];ref=x.get('reference',{});sid=x.get('source_id',ref.get('source_id'))
   e=evidence[sid];text=sources[json.loads(e['metadata_json'])['id']]['text'].replace('\r\n','\n').replace('\r','\n')
   if text[anchor['start']:anchor['end']]!=anchor['text']:issues.append('noncanonical assertion anchor span')
   typed=x.get('semantic_identity',{})
   if typed.get('candidate_id')!=e['scope']['candidate_id'] or typed.get('canonical_evidence_id')!=e['evidence_id']:issues.append('assertion anchor identity mismatch')
   if typed.get('provenance',{}).get('start')!=anchor['start'] or typed.get('provenance',{}).get('end')!=anchor['end']:issues.append('assertion anchor typed span mismatch')
  if 'generated_tokens' in x and 'arm' in x:inferences[json.dumps(x,sort_keys=True)]=x
  if 'canonical_evidence_id' in x and 'content' in x and 'source_hash' in x:
   e=evidence[x['source_id']];text=sources[json.loads(e['metadata_json'])['id']]['text'].replace('\r\n','\n').replace('\r','\n');source_windows+=1
   if text[x['start']:x['end']]!=x['content'] or sha(text)!=x['source_hash'] or x['source_version']!=e['version']:issues.append('noncanonical secondary review window')
  if 'reference' in x and 'content' in x and isinstance(x['reference'],dict):
   ref=x['reference'];e=evidence.get(ref.get('source_id'))
   if e is None or ref.get('scope')!=e['scope']:issues.append('foreign context provenance');continue
   text=sources[json.loads(e['metadata_json'])['id']]['text'].replace('\r\n','\n').replace('\r','\n');a,b=x.get('context_span',[ref['start'],ref['end']]);span_checks+=1
   if 'context_span' not in x and text[a:b]!=x['content']:
    # Review envelopes reference an already-declared canonical expanded window;
    # the citation reference still identifies the original retrieved chunk.
    declared=declared_windows.get(json.dumps([ref,x['content']],sort_keys=True),set())
    if len(declared)==1:
     a,b=next(iter(declared));reused_context_spans+=1
     if not (a<=ref['start'] and b>=ref['end']):issues.append('expanded context does not contain cited chunk')
    else:issues.append('missing/ambiguous declared review window span')
   if text[a:b]!=x['content']:issues.append('noncanonical bounded context span')
 for b in batches:
  attempts=b.get('fallback_attempts',[]);pool=b.get('fallback_pool',{});seen=set();vetoed=set()
  if pool.get('review_calls',0)>12:issues.append('fallback review bound')
  if pool.get('unit_count',0)>128:issues.append('fallback pool bound')
  trace=b.get('fallback_selection_trace',[])
  for i,a in enumerate(attempts):
   key=tuple(a['selected_candidate'])
   if key in seen:issues.append('repeated fallback candidate')
   seen.add(key)
   if trace[i]['candidate_id']!=list(key):issues.append('fallback trace mismatch')
   next_id=attempts[i+1]['selected_candidate'] if i+1<len(attempts) else None
   if trace[i].get('next_candidate_chosen')!=next_id:issues.append('fallback successor mismatch')
  for v in b.get('claim_reviews',[]):
   key=(v.get('event_id'),v.get('quote',{}).get('quote'))
   if v.get('accepted') and key in vetoed:issues.append('same-event contradiction revival')
   if v.get('support')=='CONTRADICTED' or v.get('relation_veto'):vetoed.add(key)
 model=list(inferences.values())
 for m in model:
  if m['arm']!='BASE' or m.get('trainable_parameters') or m.get('gradients_present'):issues.append('unapproved model/training state')
  if m['input_tokens']>8192 or m['generated_tokens']>1536 or m.get('termination')=='length':issues.append('token/termination regression')
 rows.append(dict(case=r['id'],status=r['status'],claims=len(claims),issues=issues,model_calls=len(model),maximum_input_tokens=max([m['input_tokens'] for m in model],default=0),canonical_context_checks=span_checks,reused_declared_review_spans=reused_context_spans,canonical_secondary_windows=source_windows))
output=dict(cases=rows,ordinary_failures=sum(bool(r['issues']) for r in rows),limitations='Mechanical correctness is separate from independent factual, content, identity and capability audits.')
with (D/(sys.argv[1]+'-mechanical-audit'+('-'+sys.argv[2] if len(sys.argv)>2 else '')+'.json')).open('x') as f:json.dump(output,f,indent=2)
print(json.dumps(output,indent=2))
