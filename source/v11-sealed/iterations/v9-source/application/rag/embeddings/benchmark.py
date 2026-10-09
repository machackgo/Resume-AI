"""Reproducible Slurm CPU evaluation, including a deliberately limited policy probe."""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import time
from ..adapters import NormalizedFixtureAdapter
from ..domain import Scope, Locator, canonical, ClaimDraft
from ..ingestion import MemoryLedger, AnnotatedFixtureExtractor
from ..chunking.chunker import CandidateChunks
from ..chunking.policy import POLICY_A, POLICY_B
from .cache import ChunkEmbedder
from .evaluation import evaluate
from .input_builder import STRATEGIES, build_input
from .local import LocalTransformerProvider
from .similarity import cosine

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/stage3c'
FIXTURE=ROOT/'fixtures/rag/embedding_eval/resume_semantics_v1.json'
CLOCK=lambda:'2026-09-27T00:00:00+00:00'


def corpus(data, policy, long_form=False):
    ledger=MemoryLedger(clock=CLOCK).for_candidate(Scope('synthetic-eval','candidate'))
    service=CandidateChunks(ledger)
    chunks=[]; owners={}; targets={}
    for i,d in enumerate(data['documents']):
        text=d['text']
        if long_form:
            # Independently fixed filler and varied placement, not tuned to scores.
            before=('Recorded project dates, reviewed team notes, and maintained a changelog. ' * (3+i%4))
            text=before+'\n\n'+text+'\n\n'+('Discussed schedules and documented routine meeting outcomes. '*6)
        start=text.index(d['text']); end=start+len(d['text'])
        adapter=NormalizedFixtureAdapter('document.v1',d['id'],'https://example.invalid/'+d['id'],
            d['title'],text,Locator('document.v1',canonical({'document_id':d['id'],'section':d['section']})))
        r=ledger.ingest(adapter, AnnotatedFixtureExtractor((ClaimDraft(d['text'],start,end,d['text']),)))
        generated=service.generate(r.evidence.evidence_id,policy)
        for c in generated:
            owners[c.chunk_id]=d['id']
            targets[c.chunk_id]=c.start<=start and end<=c.end
        chunks.extend(generated)
    return service,tuple(chunks),owners,targets


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--model-index',type=int,required=True)
    args=parser.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('run model evaluation on a Slurm compute allocation')
    specs=json.loads((OUT/'models.lock.json').read_text()); spec=specs[args.model_index]
    data=json.loads(FIXTURE.read_text())
    start=time.perf_counter(); provider=LocalTransformerProvider(spec,str(ROOT/'models/stage3c'))
    load_seconds=time.perf_counter()-start
    # Warm both encoder paths before collecting steady-state timings.
    provider.embed_documents(['Synthetic warmup.']); provider.embed_queries(['Synthetic warmup.'])
    started=time.perf_counter()
    qvectors=provider.embed_queries([q['query'] for q in data['queries']])
    query_seconds=time.perf_counter()-started
    experiments=[]
    for variant in ('short','long-policy-probe'):
        for policy in (POLICY_A,POLICY_B):
            for strategy in STRATEGIES:
                service,chunks,owners,targets=corpus(data,policy,variant!='short')
                embedder=ChunkEmbedder(service.scope,provider,clock=CLOCK)
                started=time.perf_counter(); records=embedder.embed(chunks,strategy)
                elapsed=time.perf_counter()-started
                for r in records: embedder.resolve(r,service)
                rows=[]
                for q,qvector in zip(data['queries'],qvectors):
                    # Evidence-level ranking: max over its chunks. Retain winning
                    # chunk and exact target-span containment to audit false hits.
                    best={}
                    for r in records:
                        doc=owners[r.chunk_id]; score=cosine(qvector,r.vector)
                        if doc not in best or (-score,r.chunk_id)<(-best[doc][0],best[doc][1].chunk_id):
                            best[doc]=(score,r)
                    result=evaluate([q],[qvector],[(doc,pair[1].vector) for doc,pair in best.items()])['queries'][0]
                    for item in result['ranking']:
                        rec=best[item['id']][1]
                        item.update(winning_chunk_id=rec.chunk_id,target_fully_contained=targets[rec.chunk_id])
                    result['supported_recall_at_1']=float(result['ranking'][0]['relevant'] and result['ranking'][0]['target_fully_contained'])
                    rows.append(result)
                keys=('recall_at_1','recall_at_3','mrr','hard_negative_win_rate','supported_recall_at_1')
                summary={k:sum(r[k] for r in rows)/len(rows) for k in keys}
                content_rows=[r for r in rows if r['category']!='metadata_only']
                label=f'model{args.model_index}-{variant}-{policy.name}-{strategy}'
                payload={'records':[asdict(r) for r in records],
                         'inputs':[{'chunk_id':c.chunk_id,**asdict(build_input(c,strategy))} for c in chunks],
                         'query_vectors':qvectors,'queries':data['queries'],
                         'chunk_manifest':[{'chunk_id':c.chunk_id,'revision_id':c.revision_id,
                                            'source_fixture_id':owners[c.chunk_id],'start':c.start,'end':c.end,
                                            'target_fully_contained':targets[c.chunk_id]} for c in chunks]}
                artifact=OUT/(label+'-records.json'); artifact.write_text(json.dumps(payload,indent=2)+'\n')
                experiments.append({'variant':variant,'chunk_policy':asdict(policy),'policy_id':policy.policy_id,
                    'input_strategy':strategy,'chunk_count':len(chunks),'metrics':summary,
                    'content_only_metrics':{k:sum(r[k] for r in content_rows)/len(content_rows) for k in keys},
                    'document_seconds':elapsed,'documents_per_second':len(chunks)/elapsed,
                    'query_seconds':query_seconds,'queries_per_second':len(qvectors)/query_seconds,
                    'artifact':artifact.name,'artifact_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    'queries':rows})
                print(label,summary,flush=True)
    again=provider.embed_queries([q['query'] for q in data['queries']])
    repeat_delta=max(abs(x-y) for a,b in zip(qvectors,again) for x,y in zip(a,b))
    report={'dataset_version':data['version'],'dataset_sha256':hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        'config':asdict(provider.config),'model_metadata':spec,'parameter_count':provider.parameter_count,
        'model_load_seconds':load_seconds,'peak_rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        'max_observed_tokens':provider.max_observed_tokens,'repeat_query_max_abs_delta':repeat_delta,
        'environment':{'python':platform.python_version(),'platform':platform.platform(),'hostname':platform.node(),
                       'slurm_job_id':os.environ['SLURM_JOB_ID'],'cpu':subprocess.getoutput('lscpu'),
                       'pip_freeze':subprocess.getoutput(str(ROOT/'.venv/bin/pip')+' freeze')},
        'experiments':experiments}
    (OUT/f'model{args.model_index}-evaluation.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__': main()
