"""Conservative truth checks independent of teacher citations and scores.

This is a synthetic-data validator, not a general-purpose entailment engine.
Public evidence is the only factual authority. Hidden oracle annotations restrict
scope and expose contradictions; they may never add facts absent from the input.
An independent hash-bound semantic critic remains mandatory.
"""
import re
from .io import digest, norm

VERSION = 'grounding-v2'
TECHNOLOGIES = ['Python','PyTorch','TensorFlow','transformers','LLMs','RAG','LoRA','QLoRA','FastAPI','Flask','REST APIs','Docker','Kubernetes','AWS','Azure','GCP','SQL','PostgreSQL','vector databases','CI/CD','MLOps','Java','C++','Rust','Go','React','Spark','JAX','MLflow','Git','GitHub','Redis','MongoDB','OpenAI','Qwen','Hugging Face','scikit-learn','BERT','CUDA','Linux','Terraform','Airflow','SageMaker','Lambda','Vertex AI']
TECH_ALIASES = {'rest api':'REST APIs','rest apis':'REST APIs','retrieval-augmented generation':'RAG','retrieval augmented generation':'RAG','large language model':'LLMs','large language models':'LLMs','llm':'LLMs','llms':'LLMs','continuous integration':'CI/CD','continuous delivery':'CI/CD','amazon web services':'AWS','google cloud':'GCP','google cloud platform':'GCP','vector database':'vector databases'}
ACTION_GROUPS = {
 'studied':['studied','study','studying','learned about','read about'],
 'used':['used','use','using','utilized'], 'consumed':['consumed','consume','consuming','called'],
 'built':['built','build','building','implemented','implement','implementing','developed','develop','developing','created','create','creating','wrote'],
 'designed':['designed','design','designing','architected'], 'trained':['trained','train','training'],
 'fine-tuned':['fine-tuned','fine-tune','fine-tuning','finetuned'], 'evaluated':['evaluated','evaluate','evaluating','assessed','benchmarked','measured'],
 'optimized':['optimized','optimize','optimizing','reduced','improved','accelerated'],
 'deployed':['deployed','deploy','deploying','launched'], 'operated':['operated','operate','operating','maintained','monitored'],
 'led':['led','lead','leading','managed','directed','supervised'], 'collaborated':['collaborated','collaborate','collaborating','contributed','partnered','coauthored'],
}
EXACT_FIELDS = {
 'organization': {'organization','institution','issuer'},
 'role': {'role','title'},
 'title': {'role','title','name','project_name','degree','credential','certification'},
 'start_date': {'start_date'}, 'end_date': {'end_date'},
 'degree': {'degree'}, 'institution': {'institution'},
 'certification': {'certification','credential'}, 'credential': {'credential','certification'},
 'location': {'location'}, 'name': {'name'}, 'url': {'url'},
}
_RESUME_TASKS = {'GENERATE_RESUME','GENERATE_RESUME_SECTION','REWRITE_BULLET_FOR_JOB','SELECT_RESUME_CONTENT'}


def contains(text, term):
    return re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', text, re.I) is not None


def technologies(text):
    return {x for x in TECHNOLOGIES if contains(text, x)} | {v for k,v in TECH_ALIASES.items() if contains(text,k)}


def actions(text):
    return {k for k,vs in ACTION_GROUPS.items() if any(contains(text,v) for v in vs)}


def action_mismatches(clause, supported_facts):
    """Disambiguate two bounded grammatical cases; no general action promotion."""
    support=' '.join(f['value'] for f in supported_facts)
    detected=actions(clause);allowed=actions(support)
    # Instrument adjunct: 'fine-tuned ... using QLoRA' is supported by the
    # same primary action explicitly 'with QLoRA', not by merely studying it.
    instrument=re.search(r'\busing\s+([\w+.-]+)',clause,re.I)
    if instrument and 'used' in detected and instrument.group(1).lower() not in {'a','an','the'}:
        for f in supported_facts:
            for sentence in re.split(r'[.;]',f['value']):
                if re.search(r'\bwith\s+'+re.escape(instrument.group(1).rstrip('.'))+r'(?!\w)',sentence,re.I) and (detected-{'used'}) & actions(sentence):
                    allowed.add('used')
    # Education 'training in statistics' is not an assertion of model training.
    phrase=re.search(r'\btraining in ([A-Za-z ,&-]+)[.!]?$',clause,re.I)
    education=' '.join(f['value'] for f in supported_facts if f['field'] in {'degree','credential'})
    if phrase and education:
        stop={'and','in','of','the','a','an'}
        domain=set(re.findall(r'[a-z]+',phrase.group(1).lower()))-stop
        if domain and domain<=set(re.findall(r'[a-z]+',education.lower())):
            detected=actions(clause[:phrase.start()])
    if re.search(r'\b(?:client-side )?API use\b',clause,re.I) and any(re.search(r'\b(?:consumed|called)\b[^.;]*\bAPI\b',f['value'],re.I) for f in supported_facts):
        allowed.add('used')
    return detected-allowed


def numbers(text):
    return set(re.findall(r'(?<![\w])(?:[$€£])?\d+(?:,\d{3})*(?:\.\d+)?(?:%|\+)?(?![\w])', text))


def claims(value, p=''):
    if isinstance(value,dict):
        if set(value)=={'text','evidence_ids','fact_ids'}:
            yield p,value
        else:
            for k,v in value.items():
                yield from claims(v,p+'/'+str(k).replace('~','~0').replace('/','~1'))
    elif isinstance(value,list):
        for k,v in enumerate(value):
            yield from claims(v,p+'/'+str(k))


def claim_context(output, path):
    """Read immutable structural scope around a claim, independently of refs."""
    node=output; event=None; section=None
    for part in path.split('/')[1:]:
        if isinstance(node,dict):
            if isinstance(node.get('event_id'),str):event=node['event_id']
            if isinstance(node.get('section'),str):section=node['section']
        key=part.replace('~1','/').replace('~0','~')
        node=node[int(key)] if isinstance(node,list) else node[key]
    return event,section


def nonfactual_safe(text):
    """Conservative empty-reference courtesy/performative allowlist.

    Not an entailment verdict. All other text needs references and semantic
    inspection even when a teacher or critic calls it nonfactual.
    """
    t=' '.join(text.split()).strip()
    sentences=[x.strip() for x in re.split(r'(?<=[.!?])\s+',t) if x.strip()]
    if len(sentences)>1:
        return len(sentences)<=4 and len(t)<=1000 and all(nonfactual_safe(sentence) for sentence in sentences)
    if re.fullmatch(r'(?:Dear (?:Hiring (?:Team|Manager)|Recruiting Team)|Hello|Hi|Sincerely|Regards|Best regards|Kind regards|Thank you)[,!.]?',t,re.I):return True
    if re.fullmatch(r'Thank you for (?:your time|your consideration|your time and consideration|considering my application)[,.!]?',t,re.I):return True
    if re.fullmatch(r'I (?:would welcome|welcome) (?:the|an) opportunity to discuss (?:the role|this role|my application|how I could contribute)[.!]?',t,re.I):return True
    if re.fullmatch(r'I would welcome a conversation about how (?:this experience|I) could contribute to (?:the|this) role[.!]?',t,re.I):return True
    if re.fullmatch(r'(?:Would you be open to|Would you be available for|Could we arrange) (?:a brief conversation|a short conversation|a brief informational conversation|a short informational conversation)(?: about (?:the role|this role|your work))?\??',t,re.I):return True
    # Bounded deictic courtesy grammar: no new named entities, experience
    # adjectives, numbers, past relationships or asserted qualifications.
    ref=r'(?:this (?:background|experience)|these (?:contributions|implementation examples))'
    role=r'(?:the|this) role'
    if re.fullmatch(r'I would welcome (?:the|an) opportunity to discuss '+ref+r' and '+role+r'[.!]?',t,re.I):return True
    if re.fullmatch(r'I would welcome a conversation about '+role+r' and how '+ref+r' could contribute[.!]?',t,re.I):return True
    topic=r'(?:'+ref+r' and '+role+r'|whether '+ref+r' fits '+role+r'|how '+ref+r' might fit (?:the|this) team[’\x27]s needs)'
    if re.fullmatch(r'Would you be (?:open to|available for) a brief conversation about '+topic+r'\??',t,re.I):return True
    return False


def preserves_explicit_negative(text, source):
    """Permit a narrow explicit denial, never affirmative reuse of its tokens.

    A sentence copied faithfully or a short single-clause denial still receives
    full semantic review. Conjunctions/parentheticals are not lexically certified.
    """
    if not re.search(r'\b(?:no|not|never|without)\b',source,re.I):return False
    if norm(text)==norm(source):return True
    t=' '.join(text.split()).strip()
    if re.fullmatch(r'No[.!]?',t,re.I):return True
    if len(t.split())>35 or re.search(r'\b(?:but|and|while|although|however)\b|[;:()\n]',t,re.I):return False
    return re.fullmatch(r'(?:No,?\s+)?I\s+(?:(?:have|had)\s+(?:not|never)|(?:do|did)\s+not|never)\s+[^.!?]+[.!]?',t,re.I) is not None


def entity_phrases(text):
    """Detect explicit organization/institution-like names for independent checks.

    The hidden entity inventory supplements this extractor for known names;
    arbitrary unknown names and implicit entities still need the semantic critic.
    """
    endings=r'(?:Corp(?:oration)?|Inc|LLC|Ltd|Company|University|College|Institute|Lab|Laboratory|Works|Research Unit)'
    pattern=r'\b(?:[A-Z][\w&+.-]*[ \t]+){1,7}'+endings+r'\b'
    return {re.sub(r'^(?:At|In|For|With|From)\s+','',name) for name in re.findall(pattern,text)}


def _attested(fact, evidence):
    for e in evidence.values():
        if e['evidence_id'] not in fact['evidence_ids']:continue
        for a in e.get('authenticated_attestations',[]):
            if (a.get('policy')=='exact_fact_ids_only' and a.get('source_id')==e['source_id']
                and fact['fact_id'] in a.get('fact_ids',[]) and fact['event_id']==e['event_id']):
                return True
    return False


def validate_scenario(s):
    errors=[];inp=s['input'];o=s['oracle'];owner=inp['profile']['candidate_id']
    if o['candidate_id']!=owner:errors.append('CANDIDATE_OWNERSHIP')
    fs=inp['profile']['facts'];byid={f['fact_id']:f for f in fs}
    if len(byid)!=len(fs):errors.append('DUPLICATE_FACT_ID')
    es=inp['rag'];byev={e['evidence_id']:e for e in es}
    if len(byev)!=len(es):errors.append('DUPLICATE_EVIDENCE_ID')
    if len({e['content'] for e in es})>5:errors.append('RAG_GROUP_BUDGET')
    for e in es:
        if len(e['content'])>640:errors.append('RAG_CHUNK_BOUND')
        if e['trust']!='untrusted_data':errors.append('RAG_TRUST_PROMOTION')
        if e['citation_handle']!={'source_version':1,'span':[0,len(e['content'])]}:errors.append('RAG_CITATION_SPAN')
        for a in e.get('authenticated_attestations',[]):
            if a.get('source_id')!=e['source_id'] or a.get('policy')!='exact_fact_ids_only':errors.append('INVALID_AUTHENTICATED_ATTESTATION')
            for fid in a.get('fact_ids',[]):
                if fid not in byid or byid[fid]['event_id']!=e['event_id']:errors.append('ATTESTATION_FACT_SCOPE')
    for f in o['facts']:
        if f['owner']!=owner:errors.append('CROSS_CANDIDATE_FACT')
        if f['fact_id'] not in byid:errors.append('UNKNOWN_ORACLE_FACT')
        if set(f['evidence_ids'])-set(byev):errors.append('UNKNOWN_ORACLE_EVIDENCE')
        if f['fact_id'] in byid:
            if f['event_id']!=byid[f['fact_id']]['event_id']:errors.append('FACT_EVENT_MISMATCH')
            if f['provenance']!=byid[f['fact_id']]['provenance']:errors.append('FACT_PROVENANCE_MISMATCH')
        for eid in f['evidence_ids']:
            if eid in byev and byev[eid]['event_id']!=f['event_id']:errors.append('EVIDENCE_FACT_EVENT_MISMATCH')
    if len({f['fact_id'] for f in o['facts']})!=len(o['facts']):errors.append('DUPLICATE_ORACLE_FACT')
    if {f['fact_id'] for f in o['facts']} != set(byid):errors.append('INCOMPLETE_ORACLE_FACT_INVENTORY')
    return sorted(set(errors))


def _source_spans(output, job_text):
    errors=[]
    def walk(value,path=''):
        if isinstance(value,dict):
            if set(value)=={'start','end','quote'}:
                start,end=value['start'],value['end']
                if not (type(start) is int and type(end) is int and 0<=start<end<=len(job_text)) or job_text[start:end]!=value['quote']:
                    errors.append('JOB_SOURCE_SPAN:'+path)
            for k,v in value.items():walk(v,path+'/'+str(k))
        elif isinstance(value,list):
            for i,v in enumerate(value):walk(v,path+'/'+str(i))
    walk(output)
    return errors


def validate_claims(s,output):
    errors=validate_scenario(s);soft=[];inp=s['input'];o=s['oracle']
    fs={f['fact_id']:f for f in o['facts']};visible={f['fact_id']:f for f in inp['profile']['facts']};es={e['evidence_id']:e for e in inp['rag']}
    excluded=set(inp['constraints']['excluded_fact_ids'])
    all_entities={entity for f in fs.values() for entity in f.get('entities',[]) if entity}
    texts=[];audit=[]
    errors.extend(_source_spans(output,inp.get('job',{}).get('text','')))
    for path,c in claims(output):
        ids=c['evidence_ids'];fids=c['fact_ids'];text=c['text'];texts.append(text)
        event,section=claim_context(output,path)
        if len(set(ids))!=len(ids) or len(set(fids))!=len(fids):errors.append('DUPLICATE_CLAIM_REFERENCE:'+path)
        if set(ids)-set(es):errors.append('UNKNOWN_EVIDENCE_ID:'+path)
        if set(fids)-set(fs):errors.append('UNKNOWN_FACT_ID:'+path)
        referenced=[fs[f] for f in fids if f in fs]
        evidence_facts=[f for f in fs.values() if set(f['evidence_ids'])&set(ids)]
        supporting={f['fact_id']:f for f in referenced+evidence_facts}.values()
        if any(f['owner']!=o['candidate_id'] for f in supporting):errors.append('CROSS_CANDIDATE_EVIDENCE:'+path)
        if set(fids)&excluded:errors.append('EXCLUDED_USER_FACT:'+path)
        if event and any(f['event_id']!=event for f in referenced):errors.append('WRONG_EVENT_REFERENCE:'+path)
        clauses=[x.strip() for x in re.split(r'[;\n]|(?<=[.!?])\s+',text) if x.strip()]
        positive=[f for f in supporting if f['polarity']=='positive' or (f['polarity']=='negative' and any(preserves_explicit_negative(clause,visible[f['fact_id']]['value']) for clause in clauses))]
        eligible=[f for f in positive if f['fact_id'] not in excluded and (event is None or f['event_id']==event)]
        if event and positive and not eligible:errors.append('WRONG_EVENT_SUPPORT:'+path)
        if supporting and not positive:errors.append('NO_POSITIVE_FACT_SUPPORT:'+path)
        if not ids and not fids and not nonfactual_safe(text):errors.append('MISSING_FACTUAL_REFERENCE:'+path)
        if output.get('task') in _RESUME_TASKS and any(f['event_id'].startswith('context_') for f in eligible):
            errors.append('CONTEXT_TO_CANDIDATE_TRANSFER:'+path)
            eligible=[f for f in eligible if not f['event_id'].startswith('context_')]
        # Profile and RAG references form a union, not a Cartesian join. An
        # independently supplied identity fact need not have its own RAG entry
        # simply because the paragraph also cites action evidence.
        for eid in ids:
            if eid in es and not any(eid in f['evidence_ids'] for f in eligible):
                errors.append('NONENTAILING_CITATION:'+path)
        # The hidden oracle never supplies missing technology or metric values.
        support_text=' '.join(visible[f['fact_id']]['value'] for f in eligible if f['fact_id'] in visible)
        allowed_tech=technologies(support_text);detected_tech=technologies(text)
        # Explicit negative facts support only the particular denial sentence.
        # They must never license an affirmative clause elsewhere in a paragraph.
        for clause in clauses:
            clause_support=' '.join(visible[f['fact_id']]['value'] for f in eligible if f['polarity']=='positive' or preserves_explicit_negative(clause,visible[f['fact_id']]['value']))
            if technologies(clause)-technologies(clause_support):errors.append('TECHNOLOGY_MISMATCH:'+path+':'+','.join(sorted(technologies(clause)-technologies(clause_support))))
            if numbers(clause)-numbers(clause_support):errors.append('NUMERIC_MISMATCH:'+path+':'+','.join(sorted(numbers(clause)-numbers(clause_support))))
            clause_facts=[visible[f['fact_id']] for f in eligible if f['polarity']=='positive' or preserves_explicit_negative(clause,visible[f['fact_id']]['value'])]
            mismatches=action_mismatches(clause,clause_facts)
            if mismatches:errors.append('ACTION_STRENGTH_INFLATION:'+path+':'+','.join(sorted(mismatches)))
        detected_entities={entity for entity in all_entities if contains(text,entity)}|entity_phrases(text)
        if any(not contains(support_text,entity) for entity in detected_entities):errors.append('ENTITY_MISMATCH:'+path)
        # Candidate identity/date/title leaves require matching field kinds and event.
        leaf=path.rsplit('/',1)[-1]
        if leaf in EXACT_FIELDS:
            accepted_kinds=set(EXACT_FIELDS[leaf])
            if leaf=='title':
                if section=='EXPERIENCE':accepted_kinds={'role','title'}
                elif section=='PROJECTS':accepted_kinds={'name','project_name','title'}
                elif section=='EDUCATION':accepted_kinds={'degree','credential'}
                elif section=='CERTIFICATIONS':accepted_kinds={'credential','certification'}
            compatible=[visible[f['fact_id']]['value'] for f in eligible if visible[f['fact_id']]['field'] in accepted_kinds]
            if text not in compatible:errors.append('STRUCTURED_FACT_MISMATCH:'+path)
        if re.search(r'\b(?:verified|authenticated|independently confirmed)\b',text,re.I):
            if not eligible or any(f['provenance']!='AUTHENTICATED' or not _attested(f,es) for f in eligible):
                errors.append('UNAUTHENTICATED_VERIFICATION:'+path)
        # A metric and its action/technology cannot be pooled across events.
        byevent={}
        for f in eligible:byevent.setdefault(f['event_id'],[]).append(visible[f['fact_id']]['value'])
        if len(byevent)>1:
            for clause in clauses:
                ns,ts,acts=numbers(clause),technologies(clause),actions(clause)
                if not ns or not (ts or acts):continue
                if not any(ns<=numbers(' '.join(v)) and ts<=technologies(' '.join(v)) and acts<=actions(' '.join(v)) for v in byevent.values()):
                    errors.append('CROSS_EVENT_FACT_FUSION:'+path)
        # An excluded fact cannot be reintroduced just by citing its evidence.
        excluded_support=[f for f in supporting if f['fact_id'] in excluded]
        for f in excluded_support:
            value=visible[f['fact_id']]['value']
            if contains(text,value) or (numbers(text)&numbers(value))-numbers(support_text) or (technologies(text)&technologies(value))-allowed_tech:
                errors.append('EXCLUDED_USER_FACT:'+path)
        if any(contains(text,x) for x in ['world-class','industry-leading','revolutionary','millions of requests']):soft.append('INFLATED_LANGUAGE:'+path)
        if len(text.split())>45 and '/bullets/' in path:soft.append('LONG_BULLET:'+path)
        if '/bullets/' in path and re.search(r'\b(I|my|we|our)\b',text):soft.append('FIRST_PERSON_RESUME:'+path)
        audit.append(dict(pointer=path,text_sha256=digest(text),evidence_ids=ids,fact_ids=fids,event_id=event,detected_technologies=sorted(detected_tech),detected_numbers=sorted(numbers(text)),detected_actions=sorted(actions(text)),detected_entities=sorted(detected_entities),semantic_status='REQUIRES_INDEPENDENT_CRITIC'))
    bs=[norm(c['text']) for p,c in claims(output) if '/bullets/' in p]
    if len(bs)!=len(set(bs)):errors.append('DUPLICATE_BULLET')
    return dict(hard_errors=sorted(set(errors)),soft_findings=sorted(set(soft)),claims=audit)
