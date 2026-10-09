"""Experiment-only source binding/routing, no agent or application implementation."""
import copy,hashlib,re

def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def occurrences(text,q):return [m.start() for m in re.finditer(re.escape(q),text)] if q else []
def blocked(inp,gaps):
 return dict(schema_version=inp['schema_version'],task=inp['task'],status='USER_INPUT_REQUIRED',artifact=dict(missing_information=gaps,partial_artifact=None),trace=dict(selected_requirement_ids=[],selected_evidence_ids=[],excluded_evidence_ids=[],principle_ids=['TRUTH03'],decisions=[dict(code='REQUEST_FACT',reference_ids=[])]))
def gap(field,reason='ABSENT'):
 label=field.replace('_',' ')
 question=f'Please provide the {label}.' if reason=='ABSENT' else f'Please clarify the correct {label}; the supplied values conflict.' if reason=='CONFLICTING' else f'Please provide an authoritative source for the {label}.'
 return dict(field=field,reason=reason,question=question,requirement_ids=[])
def route(row,origins=None):
 inp=row['input'];task=inp['task'];facts=inp['profile']['facts'];spec=copy.deepcopy(row['task_spec']['required_fields']);gaps=[]
 if task=='ANALYZE_JOB' and not inp['job']['text'].strip():gaps.append(gap('job posting'))
 if task in ['MAP_JOB_TO_CANDIDATE','IDENTIFY_MISSING_INFORMATION']:return None
 if task in ['GENERATE_RESUME','GENERATE_RESUME_SECTION']:
  projects=inp['request']['section']=='PROJECTS' or 'PROJECTS' in inp['constraints']['required_sections']
  if projects:
   events=sorted({f['event_id'] for f in facts if f['field']=='title'})
   for e in events:spec.append(dict(event_id=e,field='origin',require_retrieved_source=False))
  if task=='GENERATE_RESUME':spec.append(dict(event_id=inp['profile']['candidate_id'].rsplit('.',1)[0]+'.profile',field='name',require_retrieved_source=False))
 for r in spec:
  if r['field']=='origin' and origins is not None:
   s=origins.get(r['event_id'],{})
   if s.get('contradictory'):gaps.append(gap('origin','CONFLICTING'))
   elif not s.get('support'):gaps.append(gap('origin','EXACT_VALUE_REQUIRED' if s.get('found') else 'ABSENT'))
   elif r['require_retrieved_source'] and not any(x.get('evidence_id') for x in s['support']):gaps.append(gap('origin source','EXACT_VALUE_REQUIRED'))
   continue
  found=[f for f in facts if f['event_id']==r['event_id'] and f['field']==r['field']]
  values={f['value'] for f in found}
  if not values:gaps.append(gap(r['field']));continue
  if len(values)>1:gaps.append(gap(r['field'],'CONFLICTING'));continue
  if r['require_retrieved_source']:
   supported=any(e['event_id']==r['event_id'] and any(f['value'] in e['content'] for f in found) for e in inp['rag'])
   if not supported:gaps.append(gap(r['field']+' source','EXACT_VALUE_REQUIRED'))
 # Diagnostic exception is deliberate: missing facts are its deliverable.
 return blocked(inp,gaps) if gaps else None

def build_registry(row):
 inp=row['input'];cid=row['id'];registry={};sources=copy.deepcopy(row['canonical_sources']);spans={};fact_links={};extra=[]
 def add(identity,sid,start,end,event,kind):
  assert identity not in registry,'duplicate identity'
  doc=sources[sid];assert 0<=start<end<=len(doc['text'])
  registry[identity]=dict(identity=identity,source_id=sid,source_version=doc['version'],source_sha256=digest(doc['text']),start=start,end=end,quote=doc['text'][start:end],event_id=event,kind=kind)
 for e in inp['rag']:
  sid=e['source_id'];assert sid in sources,'missing canonical source'
  a,b=e['citation_handle']['span'];assert sources[sid]['version']==e['citation_handle']['source_version'],'stale source version'
  assert sources[sid]['text'][a:b]==e['content'],'retrieved text does not match canonical span'
  add(e['evidence_id'],sid,a,b,e['event_id'],'retrieved_evidence')
 for f in inp['profile']['facts']:
  eid=row['fact_bindings'].get(f['fact_id'])
  if eid:
   assert eid in registry and registry[eid]['event_id']==f['event_id']
   rec=registry[eid];q=f['value'];pos=occurrences(rec['quote'],q);assert len(pos)==1,'ambiguous fact binding'
   add(f['fact_id'],rec['source_id'],rec['start']+pos[0],rec['start']+pos[0]+len(q),f['event_id'],'profile_fact')
   fact_links[f['fact_id']]=eid
  else:
   sid='profile/'+f['fact_id'];sources[sid]=dict(version=1,text=f['value']);add(f['fact_id'],sid,0,len(f['value']),f['event_id'],'profile_fact')
 # Source identities for already-visible request/job text, no new factual content.
 sid=f'{cid}.request.source';sources[sid]=dict(version=1,text=inp['request']['instruction']);eid=f'{cid}.request';add(eid,sid,0,len(sources[sid]['text']),f'{cid}.request','request_statement');extra.append(eid)
 sid=f'{cid}.job.source';sources[sid]=dict(version=1,text=inp['job']['text'])
 for r in inp['job']['requirements']:
  q=r['source_quote'];pos=occurrences(inp['job']['text'],q);binding=row.get('requirement_bindings',{}).get(r['requirement_id'])
  if binding:
   a,b=binding['start'],binding['end'];assert inp['job']['text'][a:b]==q,'invalid requirement metadata'
  else:
   assert len(pos)==1,'ambiguous/absent requirement span requires canonical occurrence metadata'
   a=pos[0];b=a+len(q)
  eid=r['requirement_id']+'.source';add(eid,sid,a,b,inp['job']['job_id'],'job_statement');extra.append(eid)
  spanid=r['requirement_id']+'.span';spans[spanid]=copy.deepcopy(registry[eid]);spans[spanid]['identity']=spanid
  # Token-level numerical phrase boundaries are coordinates only; comparator/unit semantics stay with model.
  for j,m in enumerate(re.finditer(r'\b\d+(?:\.\d+)?\s+(?:years?|months?|hours?|days?|weeks?|percent|%)\b',q),1):
   ni=r['requirement_id']+f'.numeric{j}';spans[ni]=dict(identity=ni,source_id=sid,source_version=1,source_sha256=digest(sources[sid]['text']),start=a+m.start(),end=a+m.end(),quote=m.group(),event_id=inp['job']['job_id'],kind='numeric_span')
 return dict(identities=registry,span_identities=spans,sources=sources,fact_links=fact_links,extra_evidence_ids=extra)
def interface_schema(schema,catalog):
 s=copy.deepcopy(schema)
 if s.get('$defs',{}).get('span'):
  s['$defs']['span']=dict(type='object',properties=dict(span_id=dict(type='string',enum=list(catalog['span_identities']) or ['unavailable.span'])),required=['span_id'],additionalProperties=False)
 return s
INTERFACE='''Source-bound interface: The catalog contains authoritative identities for already-visible sources. Select known evidence_ids/fact_ids for factual claims, including request motivation and job interest when relevant. A known ID is not proof of entailment: select only sources supporting the attached claim, at the same event/action/scope. Request/posting records do not establish candidate experience or role identity. For source_span fields return only the selected span_id, never coordinates. The system will bind it to canonical Unicode start/end/quote, source version and hash. Numeric spans must select the specific numeric identity. All non-citation schema semantics and the existing contract remain in effect. Do not put input-availability notes in recipient prose.'''
def model_input(row,cat):
 return dict(input=row['input'],source_catalog=list(cat['identities'].values()),span_catalog=list(cat['span_identities'].values()))
def resolve(obj,cat):
 obj=copy.deepcopy(obj);bindings=[];errors=[]
 def visit(x,path='$'):
  if isinstance(x,dict):
   if set(x)=={'span_id'}:
    rec=cat['span_identities'].get(x['span_id'])
    if rec is None:errors.append(dict(path=path,error='unknown span identity'));return
    bindings.append(dict(path=path,selected_identity=x['span_id'],authoritative=rec));x.clear();x.update({k:rec[k] for k in ['start','end','quote']});return
   for key in ['evidence_ids','fact_ids']:
    for identity in x.get(key,[]):
     rec=cat['identities'].get(identity)
     if rec is None:errors.append(dict(path=path+'.'+key,identity=identity,error='unknown source identity'))
     else:bindings.append(dict(path=path+'.'+key,selected_identity=identity,authoritative=rec))
   for k,v in x.items():visit(v,path+'.'+k)
  elif isinstance(x,list):
   for i,v in enumerate(x):visit(v,f'{path}[{i}]')
 visit(obj)
 return obj,dict(bindings=bindings,errors=errors,canonical_sources_sha256={k:digest(v['text']) for k,v in cat['sources'].items()})
