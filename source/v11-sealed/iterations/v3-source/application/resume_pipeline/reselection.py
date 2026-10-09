"""Bounded reselection from the already retrieved, candidate-scoped pool.

No new facts, rewritten quotations, relaxed licenses, or benchmark identities.
Rejected assertions stay unavailable; link-only rejection is scoped to its
requirement. Every newly selected quote must traverse the original license gate.
"""
import hashlib,json
from dataclasses import asdict
from .context_units import prepare_units
from .licensing import procedural

MAX_ROUNDS=2
MAX_CONTEXT_UNITS=5
MAX_POOL_UNITS=128

def quote_key(text):return ' '.join(text.split()).casefold()

def exclusions(reviews,approved):
    texts={quote_key(q['quote']) for q in approved};links=set()
    for review in reviews:
        q=review.get('quote')
        if not q or review.get('accepted'):continue
        key=quote_key(q['quote'])
        # Factual weakness/conflict and non-achievement cannot be cured by a
        # different job link or a duplicate source. Never soften that decision.
        if (review.get('support') in {'CONTRADICTED','UNSUPPORTED','PARTIALLY_SUPPORTED'}
            or review.get('eligibility') in {'B','C','D','E','F'}
            or review.get('counterevidence_ids') or review.get('relation_veto')):
            texts.add(key)
        else:links.update((key,rid) for rid in q['requirement_ids'])
    return texts,links

def retrieved_pool(retrieval,ledger):
    raw={};members={};order={}
    def descendants(out):
        yield out
        for child in out.get('fragment_outputs',[]):yield from descendants(child)
    def add(parent,p,rid):
        ref=p['reference'];e=ledger.evidence(ref['evidence_id'])
        if ref['scope']!=asdict(ledger.scope) or e.scope!=ledger.scope:raise ValueError('foreign fallback provenance')
        if e.source_id!=ref['source_id'] or e.version!=ref['source_version']:raise ValueError('stale fallback provenance')
        source=ledger.content(e.normalized_ref).decode()
        if hashlib.sha256(source.encode()).hexdigest()!=e.normalized_hash:raise ValueError('fallback source hash mismatch')
        a,b=ref['start'],ref['end']
        if type(a) is not int or type(b) is not int or not 0<=a<b<=len(source):raise ValueError('fallback source span')
        if p.get('content',source[a:b])!=source[a:b]:raise ValueError('fallback noncanonical content')
        checked=dict(reference=ref,content=source[a:b],attestations=p.get('attestations',[]))
        if parent in raw and raw[parent]['reference']!=ref:raise ValueError('fallback citation collision')
        raw[parent]=checked;members.setdefault(rid,set()).add(parent)
        if parent not in order.setdefault(rid,[]):order[rid].append(parent)
    for row in retrieval:
        rid=row['requirement_id']
        for out in descendants(row['output']):
            for parent,p in out.get('context',{}).get('provenance',{}).items():add(parent,p,rid)
            for hit in out.get('selector_trace',[]):
                ref=hit['provenance_handle']
                # Preserve the existing semantic plausibility floor. Pool
                # inclusion is still not factual support or eligibility.
                if hit.get('semantic_score',0)<out.get('config',{}).get('minimum_score',.2):continue
                identity=((ref['scope']['tenant_id'],ref['scope']['candidate_id']),ref['source_id'],ref['evidence_id'],ref['source_version'],ref['chunk_id'],ref['start'],ref['end'])
                parent='cite_'+hashlib.sha256(json.dumps(identity,separators=(',',':')).encode()).hexdigest()[:24]
                add(parent,dict(reference=ref),rid)
    units=prepare_units(raw,ledger);by_req={rid:{eid for eid,p in units.items() if set(p['parent_citation_ids'])&parents} for rid,parents in members.items()}
    parent_units={parent:[eid for eid,p in units.items() if parent in p['parent_citation_ids']] for parent in raw}
    ranked=[]
    for depth in range(max(map(len,order.values()),default=0)):
        for parents in order.values():
            if depth<len(parents):
                for eid in parent_units[parents[depth]]:
                    if eid not in ranked:ranked.append(eid)
    return units,by_req,ranked

def alternatives(units,by_req,ordered,requirements,reviews,approved,seen_units):
    denied,links=exclusions(reviews,approved);pending={r['requirement_id'] for r in requirements}
    candidates=[]
    for eid in ordered[:MAX_POOL_UNITS]:
        if eid in seen_units:continue
        p=units[eid];members=[rid for rid in pending if eid in by_req.get(rid,set())]
        quotes=[u for u in p['allowed_quotes'] if quote_key(u['text']) not in denied and not procedural(u['text']) and any((quote_key(u['text']),rid) not in links for rid in members)]
        if quotes:candidates.append((eid,{**p,'allowed_quotes':quotes}))
    return candidates,links
