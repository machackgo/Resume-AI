"""Conservative content filtering and bounded assertion-level recovery ranking.

Scores choose review order only. They cannot license a claim. No case IDs,
benchmark annotations, new evidence, or inferred project identities.
"""
import re
from .licensing import tokens,procedural,event_identity
from .reselection import quote_key,exclusions
MAX_ATTEMPTS=12
MAX_POOL_UNITS=128

def content_eligibility(unit,reference):
    text=unit['text'];heading=(unit.get('source_context') or {}).get('text','')
    if procedural(text):return dict(eligibility='C',reason='Procedure or prospective work is not an achieved activity')
    minor=r'^(?:Epoch\s+\d|(?:The\s+)?best validation (?:performance|accuracy) occurs|(?:Loss(?: function)?|Learning rate|Weight decay|Batch size|Number of epochs|Random seed|Figure\s+\d|Flatten layer|Fully connected layer|Output layer|Classification head|Accuracy|Precision|F1-Score)\s*[:–-]|Best checkpoint is saved|Scope:)'
    if re.search(minor,text,re.I):return dict(eligibility='C',reason='Isolated metric, configuration or implementation detail lacks standalone achievement significance')
    if re.search(r'\b(?:must finish|experimental boundary|historical stage|new code lives|diagnostic benchmark|deterministic selector|final report must)\b',text,re.I):return dict(eligibility='C',reason='Internal evaluation mechanics or policy is supporting context only')
    from .semantic_contracts import achievement
    value=achievement(text)
    if value['standalone'] is False:return dict(eligibility='C',reason=value['reason'],content_class=value['classification'],dimensions=value['dimensions'])
    return dict(eligibility='REVIEW_REQUIRED',reason='Truth, event, relevance, significance and strength require independent review')

def metric_resolution(measurements):
    """Never infer scope from numeric differences. Unknown scope => no metric.

    Each scope dimension must be explicitly established by provenance upstream.
    This helper only returns policy, never fabricates a reconciled value.
    """
    dims=('entity','quantity','population','stage','period','qualifiers')
    if len(measurements)<2:return {'action':'REVIEW_SINGLE','values':measurements}
    if any(not m.get('provenance_verified') or any(k not in m or m[k] is None for k in dims) for m in measurements):
        return {'action':'OMIT_METRIC','reason':'Unresolved measurement scope; seek separately licensed nonnumeric evidence'}
    groups={}
    for m in measurements:groups.setdefault(tuple(str(m[k]) for k in dims),set()).add(str(m['value']))
    if any(len(v)>1 for v in groups.values()):return {'action':'OMIT_METRIC','reason':'Same-scope conflict; never average or guess'}
    return {'action':'PRESERVE_SCOPED','values':measurements,'reason':'Distinct proven populations/stages retain their own labels'}

def ranked_candidates(units,by_req,ordered,reqs,reviews,approved,attempted):
    out=[];dedup=set()
    reqmap={r['requirement_id']:r['text'] for r in reqs}
    risky_events={r.get('event_id') for r in reviews if not r.get('accepted') and re.search(r'\b(?:count|records|metric|number|dataset|trained on)\b',r.get('reason',''),re.I)}
    for rank,eid in enumerate(ordered[:MAX_POOL_UNITS],1):
        p=units[eid];ref=p['reference']
        for unit in p['allowed_quotes']:
            text=unit['text'];key=quote_key(text);event=event_identity(ref,unit)
            # Rejection attaches to this assertion/event, not the words alone.
            # A different project's identical wording needs its own license.
            scoped=[r for r in reviews if r.get('event_id')==event or r.get('quote',{}).get('evidence_id')==eid]
            selected=[q for q in approved if q.get('event_id')==event or q.get('evidence_id')==eid]
            denied,links=exclusions(scoped,selected)
            identity=(ref['source_id'],ref['source_version'],unit['start'],unit['end'])
            rids=[rid for rid in reqmap if eid in by_req.get(rid,set()) and (key,rid) not in links]
            candidate_id=(eid,unit['start'],unit['end'])
            if key in denied or not rids or candidate_id in attempted or identity in dedup:continue
            dedup.add(identity)
            gate=content_eligibility(unit,ref)
            context=text+' '+(unit.get('source_context') or {}).get('text','')
            similarity=max((len(tokens(context)&tokens(reqmap[r]))/max(1,len(tokens(reqmap[r]))) for r in rids))
            strength=bool(re.search(r'\b(?:built|implemented|developed|trained|deployed|designed|achieves|achieved|contributed|architected)\b',text,re.I))
            numeric=bool(re.search(r'\d',text));ambiguity=numeric and event in risky_events
            factors=dict(semantic_relevance=similarity,component_coverage=len(rids)/max(1,len(reqs)),event_identity=int(bool(unit.get('source_context'))),evidence_strength=int(strength),source_reliability=int(ref.get('origin')=='candidate_supplied'),resume_eligibility=0 if gate['eligibility']=='C' else 1,duplication_penalty=0,ambiguity_penalty=int(ambiguity),contradiction_risk=int(event in risky_events),retrieval_rank=rank)
            score=6*similarity+strength+.25*factors['component_coverage']+.25*factors['event_identity']+.1*factors['source_reliability']-2*ambiguity-.5*factors['contradiction_risk']-rank/10000
            out.append(dict(candidate_id=candidate_id,evidence_id=eid,unit=unit,requirement_ids=rids,rank=rank,score=score,score_factors=factors,eligibility=gate))
    return sorted(out,key=lambda c:(c['eligibility']['eligibility']=='C',-c['score'],c['candidate_id']))
