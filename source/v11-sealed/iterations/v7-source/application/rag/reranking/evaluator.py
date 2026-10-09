"""Stage 3E candidate generation and controlled Stage 3F comparisons on Slurm.

Outputs only Stage 3F artifacts. No query/document expected answer reaches a
provider. Judgments are read solely by the evaluation routines.
"""
from dataclasses import asdict
import gc
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import time

from ..retrieval.benchmark import extended_corpus, populate
from ..retrieval.replay import SavedProvider
from ..retrieval import CandidateEvidenceRetriever, RetrievalConfig, InformationNeed, NeedType
from ..retrieval.evaluator import metrics as legacy_metrics, aggregate as legacy_aggregate
from ..vectorstore.models import record_from_dict, EmbeddingSpace
from ..embeddings.local import LocalTransformerProvider
from .base import ScopedReranker, CitationTextResolver, IdentityProvider
from .cross_encoder import LocalCrossEncoder
from .metrics import evaluate, aggregate

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/stage3f'

def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def fingerprint(text):
    return hashlib.sha256(' '.join(text.split()).encode()).hexdigest()

def rss_kib():
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith('VmRSS:'): return int(line.split()[1])


def load_legacy(folder):
    original = ROOT / 'results/stage3e'
    artifact = json.loads((original / 'extended-embeddings.json').read_text())
    records = tuple(record_from_dict(x) for x in artifact['records'])
    provider = SavedProvider(records, json.loads((original / 'query-vectors.json').read_text()))
    data = json.loads((ROOT / 'fixtures/rag/retrieval_eval/stage3e_v1.json').read_text())
    service, chunks, owners, recovered, latest = extended_corpus(data, provider)
    assert recovered == records
    store = populate(folder / 'legacy', service, chunks, records)
    resolver = CitationTextResolver(store, service)
    replays = []
    responses = []
    for label in ('semantic', 'lexical', 'hybrid', 'semantic-dedup'):
        expected = json.loads((original / ('extended-' + label + '.json')).read_text())
        retriever = CandidateEvidenceRetriever(store, provider,
            EmbeddingSpace(records[0].config, records[0].input_strategy), service,
            [r.record_id for r in records], RetrievalConfig(**expected['config']))
        for query, old in zip(data['queries'], expected['queries']):
            need = InformationNeed(NeedType(query.get('kind', 'job_requirement')), query['query'], query['id'])
            response = retriever.retrieve(*service.scope.key, need, top_k=100)
            assert json.loads(json.dumps(asdict(response))) == old['response']
            replays.append({'strategy':label, 'query':query['id'], 'exact_response_equal':True})
            if label == 'semantic-dedup': responses.append((query, response))
    for r in records:
        # Includes superseded records in the canonical round trip, active only in results.
        from ..embeddings.cache import ChunkEmbedder
        ChunkEmbedder(service.scope, None).resolve(store.get_embedding(r.record_id).record, service)
    dump('stage3e_replay.json', {'comparisons': len(replays), 'records_equal': len(records), 'checks': replays})
    return data, service, store, owners, resolver, responses


def load_extended(folder):
    data = json.loads((ROOT / 'fixtures/rag/reranking_eval/stage3f_v1.json').read_text())
    spec = json.loads((ROOT / 'results/stage3c/models.lock.json').read_text())[0]
    provider = LocalTransformerProvider(spec, str(ROOT / 'models/stage3c'))
    query_vectors = {}
    raw_embed = provider.embed_queries
    def audited(texts):
        vectors = raw_embed(texts)
        query_vectors.update(dict(zip(texts, vectors)))
        return vectors
    provider.embed_queries = audited
    service, chunks, owners, records, latest = extended_corpus(data, provider)
    store = populate(folder / 'extended', service, chunks, records)
    retriever = CandidateEvidenceRetriever(store, provider,
        EmbeddingSpace(records[0].config, records[0].input_strategy), service,
        [r.record_id for r in records], RetrievalConfig())
    resolver = CitationTextResolver(store, service)
    responses = []
    for q in data['queries']:
        need = InformationNeed(NeedType.JOB_REQUIREMENT, q['query'], q['id'])
        response = retriever.retrieve(*service.scope.key, need, top_k=20)
        assert all(x.reference.evidence_id == latest[x.reference.source_id] for x in response.results)
        # Requesting top five is exactly a prefix, including its corroboration references.
        prefix = retriever.retrieve(*service.scope.key, need, top_k=5)
        assert prefix.results == response.results[:5]
        responses.append((q, response))
    from ..embeddings.cache import ChunkEmbedder
    for r in records:
        ChunkEmbedder(service.scope, None).resolve(store.get_embedding(r.record_id).record, service)
    dump('extended-embeddings.json', {'records':[asdict(r) for r in records], 'owners':owners})
    dump('query-vectors.json', query_vectors)
    dump('candidate-sets.json', {'dataset_sha256': hashlib.sha256((ROOT/'fixtures/rag/reranking_eval/stage3f_v1.json').read_bytes()).hexdigest(),
        'retrieval_config':asdict(retriever.config), 'queries':[{'id':q['id'], 'response':asdict(r)} for q,r in responses],
        'active_version_checks':True, 'resolved_records':len(records), 'top5_is_exact_prefix':True})
    # Map individual chunks to exact-text groups; all source members remain available.
    group_by_chunk = {c.chunk_id:fingerprint(c.text) for c in chunks}
    group_docs = {}
    for c in chunks:
        if c.evidence.evidence_id != latest[c.evidence.source_id]: continue
        group_docs.setdefault(group_by_chunk[c.chunk_id], set()).add(owners[c.chunk_id])
    del provider; gc.collect()
    return data, service, store, owners, resolver, responses, group_by_chunk, group_docs


def judgments(query, group_docs):
    grades = {group:max(query['grades'][doc] for doc in docs) for group,docs in group_docs.items()}
    doc_groups = {}
    for group, docs in group_docs.items():
        for doc in docs: doc_groups.setdefault(doc, set()).add(group)
    hard = {g for doc in query['hard_negatives'] for g in doc_groups.get(doc, ())}
    pairs = sorted({(a,b) for x,y in query['dangerous_pairs'] for a in doc_groups.get(x,()) for b in doc_groups.get(y,()) if a!=b and grades[a]>grades[b]})
    return grades, hard, pairs


def run_extended(label, provider, loaded):
    data, service, store, owners, resolver, responses, group_by_chunk, group_docs = loaded
    rows = []; exact_replays = 0
    # Warmup outside latency sample. No label enters the model input.
    first_q, first_response = responses[0]
    ScopedReranker(service.scope, first_response, provider, resolver).rerank(first_response.query.need, first_response.results[:5], 5)
    for budget in (5,10,20):
        for query, response in responses:
            candidates = response.results[:budget]
            wrapper = ScopedReranker(service.scope, response, provider, resolver)
            timings=[]; result=None
            for repetition in range(3):
                started=time.perf_counter()
                actual=wrapper.rerank(response.query.need, candidates, budget)
                timings.append(time.perf_counter()-started)
                if result is not None:
                    assert actual == result, 'same-input deterministic replay mismatch'
                    exact_replays += 1
                result=actual
            if label == 'identity': assert tuple(x.original for x in result) == candidates
            ranking=[group_by_chunk[x.reference.chunk_id] for x in result]
            grades, hard, pairs = judgments(query,group_docs)
            m=evaluate(ranking,grades,hard,pairs)
            # Strict-score wins expose ties hidden by deterministic retrieval tie-breaking.
            scoremap={group_by_chunk[x.reference.chunk_id]:x.rerank_score for x in result}
            available=[(a,b) for a,b in pairs if a in scoremap and b in scoremap]
            m['strict_hard_negative_win_rate']=sum(scoremap[a]>scoremap[b] for a,b in available)/len(available) if available else None
            m['hard_negative_score_ties']=sum(scoremap[a]==scoremap[b] for a,b in available)
            positions={key:i for i,key in enumerate(ranking)}
            failures=[{'stronger_docs':sorted(group_docs[a]),'weaker_docs':sorted(group_docs[b]),
                       'stronger_rank':positions[a]+1,'weaker_rank':positions[b]+1,
                       'stronger_score':scoremap[a],'weaker_score':scoremap[b]}
                      for a,b in pairs if a in positions and b in positions and positions[b]<positions[a]]
            # Diversity diagnostic: only reorder exactly tied scores; never boost weaker score.
            diverse=[]; pending=list(result); sources=set()
            while pending:
                score=pending[0].rerank_score
                tier=[x for x in pending if x.rerank_score==score]
                while tier:
                    index=next((i for i,x in enumerate(tier) if x.reference.source_id not in sources),0)
                    item=tier.pop(index); diverse.append(item); sources.add(item.reference.source_id); pending.remove(item)
            diverse_metrics=evaluate([group_by_chunk[x.reference.chunk_id] for x in diverse], grades,hard,pairs)
            rows.append({'id':query['id'],'category':query['category'],'need':query['query'],
                'requested_candidate_budget':budget,'actual_candidate_count':len(candidates),'metrics':m,
                'latency_seconds':timings,'dangerous_failures':failures,
                'ranking':[owners[x.reference.chunk_id] for x in result],
                'results':[asdict(x) for x in result],
                'diversity_ties_only':{'changed_order':diverse!=list(result),'metrics':diverse_metrics,
                    'unique_sources_top3':len({r.source_id for x in diverse[:3] for r in (x.reference,)+x.corroborating_references})}})
    summaries=[]
    for budget in (5,10,20):
        part=[x for x in rows if x['requested_candidate_budget']==budget]
        times=[t for x in part for t in x['latency_seconds']]
        summaries.append({'candidate_budget':budget,'queries':len(part),'metrics':aggregate([x['metrics'] for x in part]),
            'latency_median_ms':statistics.median(times)*1000,
            'latency_p95_ms':sorted(times)[int(.95*(len(times)-1))]*1000,
            'documents_per_second':sum(x['actual_candidate_count']*len(x['latency_seconds']) for x in part)/sum(times),
            'categories':{c:aggregate([x['metrics'] for x in part if x['category']==c]) for c in sorted({x['category'] for x in part})},
            'diversity_ties_only_changed_queries':sum(x['diversity_ties_only']['changed_order'] for x in part),
            'diversity_ties_only_metrics':aggregate([x['diversity_ties_only']['metrics'] for x in part])})
    report={'label':label,'config':asdict(provider.config),'summary':summaries,'queries':rows,
            'exact_replays':exact_replays,'max_observed_pair_tokens':getattr(provider,'max_observed_tokens',None),
            'resource':{'model_load_seconds':getattr(provider,'load_seconds',0),
                'parameters':getattr(provider,'parameter_count',0),'resident_kib_after_run':rss_kib(),
                'process_cumulative_peak_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
            'slurm_job_id':os.environ['SLURM_JOB_ID']}
    dump(label+'.json',report)
    print(label, json.dumps(summaries),flush=True)
    return report


def run_legacy(label, provider, loaded):
    data, service, store, owners, resolver, responses=loaded
    rows=[]
    for budget in (5,10,20):
        for q,response in responses:
            result=ScopedReranker(service.scope,response,provider,resolver).rerank(response.query.need,response.results[:budget],budget)
            ids=[owners[x.reference.chunk_id] for x in result]
            texts=[resolver(x.reference) for x in result]
            scores={owners[x.reference.chunk_id]:x.rerank_score for x in result}
            m=legacy_metrics(ids,q['relevant'],q['hard_negatives'],texts,[x.reference.source_id for x in result],scores=scores)
            for k in (1,2,3,5):
                credited={owners[ref.chunk_id] for x in result[:k] for ref in (x.reference,)+x.corroborating_references}
                m['grouped_recall_at_'+str(k)]=len(credited & set(q['relevant']))/len(set(q['relevant']))
            rows.append({'id':q['id'],'candidate_budget':budget,'ranking':ids,'metrics':m,'results':[asdict(x) for x in result]})
    dump('legacy-'+label+'.json',{'label':label,'summary':[
        {'candidate_budget':b,'metrics':legacy_aggregate([x['metrics'] for x in rows if x['candidate_budget']==b])}
        for b in (5,10,20)],'queries':rows,
        'note':'Frozen Stage 3E singleton/binary labels retained. Representative metrics can penalize equivalent siblings; grouped recall is also reported.'})


def main(folder, model_index=None):
    if not os.environ.get('SLURM_JOB_ID'): raise RuntimeError('Slurm allocation required')
    folder.mkdir(parents=True,exist_ok=True)
    legacy=load_legacy(folder)
    extended=load_extended(folder)
    if model_index is None:
        provider=IdentityProvider(); label='identity'
    else:
        specs=json.loads((OUT/'models.lock.json').read_text())
        provider=LocalCrossEncoder(specs[model_index],ROOT/'models/stage3f')
        label='minilm' if model_index==0 else 'tinybert'
    run_extended(label,provider,extended)
    run_legacy(label,provider,legacy)
    legacy[2].close(); extended[2].close()

if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv)>2 else None)
