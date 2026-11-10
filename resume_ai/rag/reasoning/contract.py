"""Versioned context/strict output contract; no model dependencies."""
import json
import hashlib
from dataclasses import asdict
from pathlib import Path
from ..reranking.base import ScopedReranker, IdentityProvider

VERSION='chunk-citations-v3'

def citation_id(ref):
    # Model-facing citation is a chunk identity, not a document or embedding ID.
    identity = (ref.scope.key, ref.source_id, ref.evidence_id, ref.source_version,
                ref.chunk_id, ref.start, ref.end)
    return 'cite_' + hashlib.sha256(json.dumps(identity,separators=(',',':')).encode()).hexdigest()[:24]

LABELS=('SUPPORTED','PARTIALLY_SUPPORTED','UNSUPPORTED','UNKNOWN')
ROOT=Path(__file__).resolve().parent  # adapted: schema/prompt files live next to this module

def public_need_id(need):
    return 'need_'+hashlib.sha256(need.requirement_id.encode()).hexdigest()[:24]

def aggregate_labels(labels):
    if not labels: return 'UNKNOWN'
    if all(x=='SUPPORTED' for x in labels): return 'SUPPORTED'
    if any(x in ('SUPPORTED','PARTIALLY_SUPPORTED') for x in labels): return 'PARTIALLY_SUPPORTED'
    if any(x=='UNSUPPORTED' for x in labels): return 'UNSUPPORTED'
    return 'UNKNOWN'

def strict_parse(raw):
    def pairs(xs):
        d={}
        for k,v in xs:
            if k in d: raise ValueError('duplicate JSON key')
            d[k]=v
        return d
    try:
        return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON'))),None
    except (ValueError,TypeError) as e: return None,str(e)

def context(scope,response,resolver,budget=5,attestations=()):
    """Trusted scope, authentic response, exact version attestations; fail closed.
    An attestation is trusted application state, never parsed from source content.
    The benchmark supplies synthetic VerificationRecords, not real credentials.
    """
    if type(budget) is not int or not 0<=budget<=5: raise ValueError('budget')
    ranked=ScopedReranker(scope,response,IdentityProvider(),resolver).rerank(response.query.need,response.results,budget)
    return from_ranked(scope,ranked,resolver,attestations),ranked

def from_ranked(scope,ranked,resolver,attestations=()):
    if resolver.scope!=scope: raise ValueError('scope mismatch')
    groups=[]; provenance={}
    for row in ranked:
        refs=(row.reference,)+row.corroborating_references
        entries=[]
        for ref in refs:
            if ref.scope!=scope: raise ValueError('foreign evidence')
            content=resolver(ref)
            eid = citation_id(ref)
            if eid in provenance and (provenance[eid]['content'] != content or
                    provenance[eid]['reference']['chunk_id'] != ref.chunk_id):
                raise ValueError('citation identity conflict')
            verified=[]
            for a in attestations:
                if a.scope!=scope: raise ValueError('foreign attestation')
                if a.support_id in ref.support_ids:
                    if a.state.value=='verified': verified.append({'state':a.state.value,'issuer':a.issuer,'attestation_ref':'attestation_'+hashlib.sha256(a.attestation_ref.encode()).hexdigest()[:24],'policy':a.policy_version})
            entry={'evidence_id':eid,'source_type':ref.source_type,'origin':ref.origin,
                   'trust':ref.trust,'verification':{'reference_policy':ref.verification,'meaning':'No authenticated verification unless exact-support attestation is supplied below'},'authenticated_attestations':verified,
                   'content':content,'citation_handle':{'source_version':ref.source_version,'span':[ref.start,ref.end]}}
            entries.append(entry)
            provenance[eid]={'reference':asdict(ref),'content':content,'attestations':[asdict(a) for a in attestations if a.scope==scope and a.support_id in ref.support_ids]}
        groups.append({'evidence':entries})
    return {'version':VERSION,'groups':groups,'provenance':provenance}

def messages(need,components,ctx):
    payload={'task':{'information_need_id':public_need_id(need),'requirement':need.text,
                    'components':components},
             'UNTRUSTED_RETRIEVED_EVIDENCE':ctx['groups'],
             'END_UNTRUSTED_RETRIEVED_EVIDENCE':True,
             'output_schema':json.loads((ROOT/'schema.json').read_text())}
    # JSON escaping prevents evidence from creating message roles or structural delimiters.
    return [{'role':'system','content':(ROOT/'system_v2.txt').read_text()},
            {'role':'user','content':json.dumps(payload,ensure_ascii=True)}]

def schema_valid(x,s):
    """Exact supported JSON Schema subset; no dependency installation."""
    if 'enum' in s and x not in s['enum']: return False
    t=s.get('type')
    if t=='object':
        return isinstance(x,dict) and set(x)==set(s['required']) and all(schema_valid(x[k],v) for k,v in s['properties'].items())
    if t=='array':
        return isinstance(x,list) and len(x)>=s.get('minItems',0) and (not s.get('uniqueItems') or len({json.dumps(v,sort_keys=True) for v in x})==len(x)) and all(schema_valid(v,s['items']) for v in x)
    if t=='string':return isinstance(x,str) and len(x)>=s.get('minLength',0)
    return 'enum' in s

def validate(raw,need,components,ctx):
    p,error=strict_parse(raw)
    out={'json_valid':error is None,'schema_valid':False,'errors':[]}
    if error: out['errors'].append('json:'+error); return p,out
    out['schema_valid']=schema_valid(p,json.loads((ROOT/'schema.json').read_text()))
    if not out['schema_valid']:out['errors'].append('schema');return p,out
    expected={x['id']:x['claim'] for x in components}; atoms=p['atomic_claims']
    if p['information_need_id']!=public_need_id(need): out['errors'].append('need_id')
    if len(atoms)!=len(expected) or {x['component_id']:x['claim'] for x in atoms}!=expected: out['errors'].append('atomic_coverage')
    allowed=ctx['provenance']; used=set()
    for a in atoms:
        ids=a['evidence_ids']; used.update(ids)
        if a['label'] in ('SUPPORTED','PARTIALLY_SUPPORTED','UNSUPPORTED') and not ids: out['errors'].append('missing_citation')
        if any(i not in allowed for i in ids): out['errors'].append('unknown_or_foreign_id')
        if set(q['evidence_id'] for q in a['quotes'])!=set(ids): out['errors'].append('quote_coverage')
        for q in a['quotes']:
            if q['evidence_id'] not in allowed or q['quote'] not in allowed[q['evidence_id']]['content']: out['errors'].append('quote_not_exact')
    if used!=set(p['evidence_ids']): out['errors'].append('citation_union')
    if any(i not in allowed for i in p['evidence_ids']): out['errors'].append('unknown_or_foreign_id')
    if aggregate_labels([a['label'] for a in atoms])!=p['label']: out['errors'].append('label_aggregation')
    if p['label']!='SUPPORTED' and not p['missing_evidence']: out['errors'].append('missing_evidence_required')
    out['errors']=sorted(set(out['errors']))
    return p,out
