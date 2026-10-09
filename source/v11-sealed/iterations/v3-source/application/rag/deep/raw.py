"""Lossless bounded query construction for raw, potentially long requirements."""
from dataclasses import asdict
from ..domain import stable_id
from ..retrieval import InformationNeed, NeedType
from .retrieve import normalize_query


def focused_spans(text, provider, max_characters=1800):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('nonempty text required')
    if len(text) > 262144:
        raise ValueError('raw input exceeds configured 262144-character limit')
    offset = 0
    while offset < len(text):
        if not text[offset:].strip():
            break
        end = min(len(text), offset + max_characters)
        def fits(end):
            value = provider.config.query_prefix + normalize_query(text[offset:end])
            return len(provider.tokenizer(value, add_special_tokens=True)['input_ids']) <= provider.max_tokens
        while end > offset and not fits(end):
            end = offset + max(0, (end-offset)*3//4)
        if end <= offset:
            raise ValueError('query metadata exceeds embedding budget')
        if end < len(text):
            boundary = max(text.rfind('\n',offset,end),text.rfind('. ',offset,end),text.rfind(' ',offset,end))
            if boundary > offset + (end-offset)//2:
                end = boundary + 1
        yield offset,end
        offset=end


def retrieve_text(engine, tenant_id, candidate_id, text, requirement_id):
    # Validate authenticated scope before tokenization/search, including empty input.
    if (tenant_id,candidate_id) != engine.retriever.store.scope.key:
        raise ValueError('unauthorized scope')
    spans=list(focused_spans(text,engine.retriever.provider))
    if len(spans)==1:
        return engine.retrieve(tenant_id,candidate_id,InformationNeed(NeedType.JOB_REQUIREMENT,text,requirement_id))
    outputs=[]
    for a,b in spans:
        nid=stable_id('need_fragment',requirement_id,a,b,text[a:b])
        outputs.append(engine.retrieve(tenant_id,candidate_id,InformationNeed(NeedType.JOB_REQUIREMENT,text[a:b],nid)))
    # Round-robin bounded groups; duplicate groups union all citation provenance.
    grouped={};order=[]
    for depth in range(max((len(o['context']['groups']) for o in outputs),default=0)):
        for output in outputs:
            groups=output['context']['groups']
            if depth>=len(groups):continue
            g=groups[depth]; key=' '.join(g['evidence'][0]['content'].split())
            if key not in grouped:
                grouped[key]={'evidence':{},'retrieval_membership':{}};order.append(key)
            for e in g['evidence']:grouped[key]['evidence'][e['evidence_id']]=e
            grouped[key]['retrieval_membership'].update(g['retrieval_membership'])
    groups=[dict(evidence=list(grouped[k]['evidence'].values()),retrieval_membership=grouped[k]['retrieval_membership']) for k in order[:engine.config.global_budget]]
    ids={e['evidence_id'] for g in groups for e in g['evidence']}
    provenance={k:v for o in outputs for k,v in o['context']['provenance'].items() if k in ids}
    components=[c for o in outputs for c in o['decomposition']['components']]
    retrieval=[{**c,'evidence_ids':[e for e in c['evidence_ids'] if e in ids]} for o in outputs for c in o['context']['component_retrieval']]
    return dict(context=dict(version='chunk-citations-v3',groups=groups,provenance=provenance,component_retrieval=retrieval,component_notice='Fragment retrieval is not support; all original text retained in query_spans.'),decomposition=dict(requirement_id=requirement_id,original_text=text,components=components,status='bounded_exact_fragments'),query_spans=[dict(start=a,end=b,text=text[a:b]) for a,b in spans],fragment_outputs=outputs,config=asdict(engine.config))
