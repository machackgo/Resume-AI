"""Frozen RAG serialization/attestation bridge audit over synthetic references.

Not vector retrieval, embedding generation or a canonical-store replay. Existing
historical tests cover those layers. No frozen module is changed by this adapter.
"""
import copy,json
from dataclasses import replace
from pathlib import Path
from .io import digest,canonical,read_jsonl,write_json

ORIGIN_TO_FROZEN={'synthetic_authored_fixture':'synthetic_fixture','synthetic_authored_history_record':'synthetic_fixture','synthetic_independent_lab_observation':'synthetic_fixture','synthetic_independent_maintainer_review':'synthetic_fixture','candidate_supplied':'candidate_supplied','externally_observed':'externally_observed'}

class FixtureResolver:
    def __init__(self,scope,refs,content):self.scope=scope;self.refs=refs;self.content=content
    def __call__(self,ref):
        if ref.scope!=self.scope or self.refs.get(ref.evidence_id)!=ref:raise ValueError('foreign/stale/modified synthetic reference')
        return self.content[ref.evidence_id]

def bridge(visible):
    from .contracts import validate_input
    if validate_input(visible):raise ValueError('invalid professional view schema')
    from rag.domain import Scope,Origin,Locator,Pointer,Claim,Support,ClaimKind,Relation,VerificationRecord,VerificationState
    from rag.retrieval.models import EvidenceReference,RetrievalResult
    from rag.reranking.models import RerankedEvidence,RerankerConfig
    from rag.reasoning.contract import from_ranked
    scope=Scope('stage4c0-synthetic-tenant',visible['profile']['candidate_id']);facts={f['fact_id']:f for f in visible['profile']['facts']}
    refs={};content={};inverse=[];origin_inverse=[];attestations=[];grouped={}
    for e in visible['rag']:
        if len(e['content'])>640 or e['citation_handle']!={'source_version':1,'span':[0,len(e['content'])]}:raise ValueError('invalid source version/span/bound')
        if e['origin'] not in ORIGIN_TO_FROZEN:raise ValueError('unknown origin alias')
        origin=Origin(ORIGIN_TO_FROZEN[e['origin']]).value
        origin_inverse.append({'scope':scope.key,'evidence_id':e['evidence_id'],'source_id':e['source_id'],'original_origin':e['origin'],'frozen_origin':origin})
        locator=Locator('text_input.v1',canonical({'input_id':e['source_id']}));support_ids=[]
        for a in e['authenticated_attestations']:
            if a['source_id']!=e['source_id'] or a['policy']!='exact_fact_ids_only':raise ValueError('attestation source/policy mismatch')
            for fid in a['fact_ids']:
                f=facts.get(fid)
                if f is None or f['event_id']!=e['event_id'] or f['provenance']!='AUTHENTICATED' or f['value'] not in e['content']:raise ValueError('attestation exact visible fact mismatch')
                cid='claim_'+digest({'scope':scope.key,'event':f['event_id'],'field':f['field'],'text':f['value']})
                start=e['content'].index(f['value']);end=start+len(f['value'])
                sid='support_'+digest({'scope':scope.key,'source':e['source_id'],'version':1,'evidence':e['evidence_id'],'span':[start,end],'claim':cid,'fact_id':fid,'text':f['value'],'event':f['event_id']})
                claim=Claim(scope,cid,f['value']);pointer=Pointer(e['evidence_id'],start,end,f['value'],locator)
                support=Support(scope,sid,cid,pointer,Relation.ASSERTS,ClaimKind.ASSERTION,None,'stage4c0-fixture-bridge-v1','Synthetic exact visible fact; no real-world credential verification')
                att=VerificationRecord(scope,sid,VerificationState.VERIFIED,'Synthetic exact-fact authority',a['attestation_id']+':'+fid,'stage4c0-synthetic-exact-fact-v1','2026-09-29T00:00:00+00:00','Synthetic attestation applies only to this source-version/span/fact')
                support_ids.append(sid);attestations.append(att)
                inverse.append({'evidence_id':e['evidence_id'],'source_id':e['source_id'],'source_version':1,'span':[start,end],'event_id':f['event_id'],'fact_id':fid,'claim_id':claim.claim_id,'support_id':support.support_id,'attestation_id':a['attestation_id']})
        ref=EvidenceReference(scope,'synthetic_embedding_'+digest(e['evidence_id']),'synthetic_chunk_'+digest(e['content']),'synthetic_revision_1',e['evidence_id'],e['source_id'],1,e['source_type'],None,locator,0,len(e['content']),origin,'untrusted_data','resolve_supports',tuple(support_ids),(),(),'synthetic-context-no-vectors','active')
        refs[e['evidence_id']]=ref;content[e['evidence_id']]=e['content'];grouped.setdefault(e['content'],[]).append(ref)
    if len(grouped)>5:raise ValueError('five-group bound')
    resolver=FixtureResolver(scope,refs,content);ranked=[]
    for i,rs in enumerate(grouped.values(),1):
        # Required typed numeric fields are declared fixture placeholders, never
        # measured retrieval scores; from_ranked does not expose them to Qwen.
        result=RetrievalResult(i,0.0,'synthetic_fixture','synthetic_query',rs[0],None,None,None,None,None,(),tuple(rs[1:]))
        ranked.append(RerankedEvidence(result,'synthetic_need',i,0.0,RerankerConfig('identity','synthetic','identity-v1','none',dtype='none',max_tokens=1),max(1,len(grouped)),5,'synthetic_fixture_hash'))
    ctx=from_ranked(scope,ranked,resolver,attestations)
    frozen={e['evidence_id']:e for g in ctx['groups'] for e in g['evidence']}
    for e in visible['rag']:
        x=frozen[e['evidence_id']]
        for key in ['content','source_type','trust','citation_handle']:
            if x[key]!=e[key]:raise ValueError('lossy frozen projection '+key)
        if x['origin']!=ORIGIN_TO_FROZEN[e['origin']]:raise ValueError('origin round trip')
        if len(x['authenticated_attestations'])!=sum(len(a['fact_ids']) for a in e['authenticated_attestations']):raise ValueError('lost exact attestation')
    return ctx,{'scope':scope,'refs':refs,'resolver':resolver,'ranked':ranked,'attestations':attestations,'inverse':inverse,'origin_inverse':origin_inverse}

def audit(scenarios):
    from rag.domain import Scope
    from rag.reasoning.contract import from_ranked
    from rag.component.retrieve import messages
    from rag.retrieval.models import InformationNeed,NeedType
    tests={'serialization_round_trips':0,'attestation_facts':0,'wrong_reference_rejected':0,'foreign_attestation_rejected':0,'unknown_support_unverified':0,'wrong_source_attestation_rejected':0,'unknown_origin_rejected':0,'wrong_fact_value_rejected':0,'modified_reference_rejected':0};inverse=[];origin_inverse=[]
    for s in scenarios:
        inp=s['input'];ctx,b=bridge(inp);ids=sorted(b['refs']);ctx['component_retrieval']=[];ctx['component_notice']='Synthetic bounded context; retrieval membership is not entailment. No vector search run.'
        need=InformationNeed(NeedType.JOB_REQUIREMENT,'Professional task evidence serialization check','stage4c0-compat')
        wire=json.loads(messages(need,[],ctx)[1]['content'])
        if wire['UNTRUSTED_RETRIEVED_EVIDENCE']!=ctx['groups']:raise ValueError('frozen message serialization changed evidence')
        tests['serialization_round_trips']+=1;tests['attestation_facts']+=len(b['inverse']);inverse+=b['inverse'];origin_inverse+=b['origin_inverse']
        if ids:
            ref=b['refs'][ids[0]]
            try:b['resolver'](replace(ref,source_version=2))
            except ValueError:tests['wrong_reference_rejected']+=1
            else:raise ValueError('stale reference accepted')
            for changed in [replace(ref,source_id='wrong-source'),replace(ref,end=ref.end+1)]:
                try:b['resolver'](changed)
                except ValueError:tests['modified_reference_rejected']+=1
                else:raise ValueError('modified reference accepted')
            bad=copy.deepcopy(inp);bad['rag'][0]['origin']='unknown_origin'
            try:bridge(bad)
            except ValueError:tests['unknown_origin_rejected']+=1
            else:raise ValueError('unknown origin accepted')
        if b['attestations']:
            a=b['attestations'][0]
            try:from_ranked(b['scope'],b['ranked'],b['resolver'],[replace(a,scope=Scope('foreign','foreign'))])
            except ValueError:tests['foreign_attestation_rejected']+=1
            else:raise ValueError('foreign attestation accepted')
            unverified=from_ranked(b['scope'],b['ranked'],b['resolver'],[replace(a,support_id='wrong-support')])
            if any(e['authenticated_attestations'] for g in unverified['groups'] for e in g['evidence']):raise ValueError('wrong support promoted')
            tests['unknown_support_unverified']+=1
            bad=copy.deepcopy(inp)
            next(e for e in bad['rag'] if e['authenticated_attestations'])['authenticated_attestations'][0]['source_id']='wrong-source'
            try:bridge(bad)
            except ValueError:tests['wrong_source_attestation_rejected']+=1
            else:raise ValueError('wrong source attestation accepted')
            bad=copy.deepcopy(inp);fid=next(e for e in bad['rag'] if e['authenticated_attestations'])['authenticated_attestations'][0]['fact_ids'][0]
            next(f for f in bad['profile']['facts'] if f['fact_id']==fid)['value']='unsupported changed fact'
            try:bridge(bad)
            except ValueError:tests['wrong_fact_value_rejected']+=1
            else:raise ValueError('wrong fact attestation accepted')
    if not tests['attestation_facts']:raise ValueError('no positive attestation coverage')
    return {'passed':True,'version':'stage4c0-frozen-context-bridge-v2','checks':tests,'inverse_fact_claim_support':inverse,'origin_aliases':ORIGIN_TO_FROZEN,'inverse_origins':origin_inverse,'origin_note':'Many-to-one synthetic origin projection; exact source origins retained in this inverse sidecar and immutable input.','vector_retrieval_run':False,'canonical_store_ingestion_run':False,'scope':'Typed frozen context and message helper CPU round-trip over immutable synthetic references; not frozen wire identity or production integration certification','limitations':['No real-world authentication claim; synthetic fixture authority only.','Professional task envelope is a new view over frozen evidence, not a change to Stage3J retrieval.','Historical regression suite separately replays canonical/provenance/vector components.']}

if __name__=='__main__':
    import sys
    rows=[]
    for name in sys.argv[2:]:rows+=read_jsonl(name)
    result=audit(rows);write_json(Path(sys.argv[1]),result);print(json.dumps(result['checks']))
