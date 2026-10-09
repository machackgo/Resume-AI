"""Synthetic CPU storage measurements. No encoder, ANN or production claims."""
from dataclasses import replace
import json
import os
from pathlib import Path
import platform
import random
import statistics
import time
from ..domain import Scope, stable_id
from ..embeddings.models import EmbeddingRecord
from ..embeddings.similarity import normalize
from .config import StoreConfig
from .models import record_from_dict, ChunkReference, EmbeddingSpace, VectorQuery
from .sqlite_reference import SQLiteVectorStore

ROOT=Path(__file__).resolve().parents[2]

def main(root):
    if not os.environ.get('SLURM_JOB_ID'): raise RuntimeError('scale tests require a compute allocation')
    sample=record_from_dict(json.loads((ROOT/'results/stage3c/model0-short-moderate-title-section-v1-records.json').read_text())['records'][0])
    results=[]
    for size in (100,1000,10000):
        scope=Scope('synthetic-scale',str(size)); rng=random.Random(73); records=[]; refs=[]
        for i in range(size):
            # Synthetic references deliberately do not pretend to be real evidence.
            source=stable_id('synthetic_source',scope.key,i); evidence=stable_id('synthetic_evidence',source)
            chunk=stable_id('synthetic_chunk',evidence); revision=stable_id('synthetic_revision',chunk)
            ih=stable_id('synthetic_input',i)
            cache=stable_id('embedding_cache','stage3c-v1',scope.key,sample.input_strategy,ih,sample.config.identity,'document')
            identity=stable_id('embedding_record',scope.key,chunk,revision,cache)
            r=replace(sample,scope=scope,record_id=identity,cache_key=cache,source_id=source,evidence_id=evidence,
                      chunk_id=chunk,chunk_revision_id=revision,evidence_version=1,input_hash=ih,
                      vector=normalize([rng.uniform(-1,1) for _ in range(sample.config.dimension)]),
                      origin='synthetic_fixture',support_ids=(),provenance_event_ids=())
            records.append(r)
            refs.append(ChunkReference(scope,chunk,revision,evidence,source,1,r.policy_id,'synthetic','synthetic',
                                       r.origin,r.trust,(),(),((r.input_strategy,ih),)))
        for batch in (1,100):
            if batch==1 and size>100: continue  # avoid pointless fsync load
            config=StoreConfig(root/f'{size}-batch-{batch}')
            s=SQLiteVectorStore(config,scope); space=EmbeddingSpace(sample.config,sample.input_strategy)
            t=time.perf_counter(); s.register_chunks(refs); reference_seconds=time.perf_counter()-t
            t=time.perf_counter()
            for start in range(0,size,batch): s.upsert_embeddings(records[start:start+batch])
            elapsed=time.perf_counter()-t
            t=time.perf_counter(); s.upsert_embeddings(records); duplicate=time.perf_counter()-t
            # State filter explicitly includes staged data for a pure storage measurement.
            from .models import SearchFilter
            latencies=[]
            for r in records[:5]:
                t=time.perf_counter(); hits=s.search_vectors(VectorQuery(space,r.vector,10,SearchFilter(state='staged')))
                latencies.append(time.perf_counter()-t); assert hits[0].embedding_id==r.record_id
            plan=[tuple(r) for r in s._db.execute('EXPLAIN QUERY PLAN SELECT embedding_id FROM vector_records WHERE space_id=? AND tombstoned=0',(space.space_id,))]
            footprint=s.path.stat().st_size; s.close()
            t=time.perf_counter(); s=SQLiteVectorStore(config,scope); reopen=time.perf_counter()-t
            assert s.count(filters=SearchFilter(state='staged'))==size; s.close()
            results.append({'records':size,'dimension':sample.config.dimension,'batch':batch,'reference_seconds':reference_seconds,
                            'insert_seconds':elapsed,'insert_records_per_second':size/elapsed,
                            'duplicate_upsert_seconds':duplicate,'query_samples':len(latencies),'query_seconds':latencies,
                            'query_median_seconds':statistics.median(latencies),'query_max_seconds':max(latencies),
                            'reopen_seconds':reopen,'database_bytes':footprint,'metadata_index_plan':plan})
    report={'backend':'sqlite exact binary64 cosine','seed':73,'platform':platform.platform(),
            'hostname':platform.node(),'slurm_job_id':os.environ['SLURM_JOB_ID'],
            'filesystem':'node-local /tmp; final closed snapshot copied to project scratch',
            'results':results,'limitations':'Single run, warm queries, five samples, one CPU, synthetic independent vectors; not production SLOs.'}
    (ROOT/'results/stage3d/performance.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'sizes':[100,1000,10000],'passed':True}))

if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]))
