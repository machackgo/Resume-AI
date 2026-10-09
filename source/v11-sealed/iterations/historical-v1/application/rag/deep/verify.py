"""Separate-process replay of retrieval, raw generations, metrics and protection."""
import os,json,re,subprocess,sys
from pathlib import Path
from dataclasses import asdict
from .prepare import ROOT,H,OUT,provider_new,corpus,Scope,MemoryLedger,CLOCK,at_scale,record_from_dict,populate,EmbeddingSpace,RetrievalConfig,CitationTextResolver,InformationNeed,NeedType,dump,sha
from .retrieve import DeepConfig,DeepRetriever,QueryRetriever,key
from .run import check_freeze,load_rows,build_messages
from .score import compute
from rag.scale.metrics import score_record

def main(run,folder):
    assert os.getenv('SLURM_JOB_ID');frozen=check_freeze();cfg=DeepConfig(**json.loads((OUT/'config.json').read_text())['selected']);data=json.loads((H/'dataset.json').read_text())
    p,_=provider_new();queries=json.loads((OUT/'query-vectors.json').read_text());embed=p.embed_queries;deltas=[]
    # Fresh query encoding for new alias texts; inherited exact historical vectors
    # are independently ranked and historical model identity remains protected.
    historical=json.loads((ROOT/'results/stage3i/query-vectors.json').read_text())
    for text,v in queries.items():
        if text not in historical:deltas.append(max(abs(x-y) for x,y in zip(embed([text])[0],v)))
    assert max(deltas,default=0)<1e-5
    p.embed_queries=lambda texts:tuple(tuple(queries[t]) for t in texts)
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(ROOT/'models/Qwen3.8-27B',local_files_only=True)
    raw=[json.loads(s) for s in (run/'raw.jsonl').read_text().splitlines()];expected={(s,'h%02d'%i) for s in ('LARGE','XL') for i in range(1,17)}
    prior=[json.loads(l) for l in (ROOT/'results/stage3i/benchmark-2333661/raw.jsonl').read_text().splitlines()]
    for r in raw:
        if r.get('reused_historical'):
            assert sha(ROOT/r['reuse_source'])==r['reuse_source_sha256']
            source=next(x for x in prior if x['run_id']==r['reuse_run_id'])
            for field in ('messages','rendered_prompt','text','raw_text','token_ids','input_tokens','output_tokens'):assert r[field]==source[field]
    assert len(raw)==32 and len({r['run_id'] for r in raw})==32 and {(r['scale'],r['id']) for r in raw}==expected
    counts=dict(contexts=0,provenance_roundtrips=0,citation_pairs=0,invalid_citation_pairs=0,output_tokens_replayed=0,selector_items=0,forensic_rank_checks=0);invalid=[]
    from rag.vectorstore.models import VectorQuery
    for scale in ('SMALL','MEDIUM','LARGE','XL'):
        scope=Scope('synthetic-stage3h','candidate-A');ledger=MemoryLedger(clock=CLOCK);svc,chunks,owners,rebuilt,attest=corpus({'id':'corpus-A','documents':at_scale(data,scale)},scope,p,ledger)
        hist=json.loads((H/f'{scale}-corpus.json').read_text())['records'];records=[record_from_dict(r) for r in hist]
        assert all({k:v for k,v in asdict(a).items() if k!='vector'}=={k:v for k,v in asdict(b).items() if k!='vector'} for a,b in zip(rebuilt,records))
        store=populate(folder/scale,svc,chunks,records);space=EmbeddingSpace(p.config,'title-section-v1');resolver=CitationTextResolver(store,svc);retriever=QueryRetriever(store,p,space,svc,[r.record_id for r in records],RetrievalConfig(semantic_budget=cfg.internal_k),normalize=cfg.normalize);engine=DeepRetriever(retriever,resolver,cfg)
        lookup={r['case']['id']:r for r in load_rows(scale)}
        for row in lookup.values():
            q=row['case'];out=engine.retrieve(*scope.key,InformationNeed(NeedType.JOB_REQUIREMENT,q['requirement'],q['id']),attest);out=json.loads(json.dumps(out))
            for field in ('context','traces','mapping','selector_trace','decomposition','config'):assert out[field]==row['component'][field],(scale,q['id'],field)
            counts['contexts']+=1;counts['selector_items']+=len(out['selector_trace'])
            for eid,v in out['context']['provenance'].items():
                ref=v['reference'];record=store.get_embedding(ref['embedding_id']).record;citation=svc.cite(record.chunk_id,record.chunk_revision_id)
                assert record.evidence_id==eid and citation.chunk.evidence.evidence_id==eid and citation.source.source_id==ref['source_id']
                assert ref['scope']==asdict(scope) and ref['trust']=='untrusted_data' and ref['lifecycle']=='active' and ref['semantic_space_id']==space.space_id
                assert citation.chunk.text==v['content'] and citation.chunk.start==ref['start'] and citation.chunk.end==ref['end'];counts['provenance_roundtrips']+=1
        trace=next(t for t in json.loads((OUT/'h06-forensic-traces.json').read_text()) if t['scale']==scale)
        for comp in trace['components']:
            hits=store.search_vectors(VectorQuery(space,tuple(queries[comp['query_plan']['text']]),len(records)));gold=trace['gold_chains'][0]['embedding']['record_id'];rank=next(i for i,h in enumerate(hits,1) if h.embedding_id==gold);assert rank==comp['gold_rank'];counts['forensic_rank_checks']+=1
        for r in (r for r in raw if r['scale']==scale):
            row=lookup[r['id']];msg=build_messages(row);assert msg==r['messages'];render=tok.apply_chat_template(msg,tokenize=False,add_generation_prompt=True,enable_thinking=False)
            assert render==r['rendered_prompt'] and len(tok(render,add_special_tokens=False)['input_ids'])==r['input_tokens']
            assert len(r['token_ids'])==r['output_tokens'] and r['total_tokens']==r['input_tokens']+r['output_tokens']
            assert tok.decode(r['token_ids'],skip_special_tokens=True)==r['text'] and tok.decode(r['token_ids'],skip_special_tokens=False)==r['raw_text']
            assert r['evidence_tokens']==len(tok(json.dumps(row['contexts']['component']['groups'],ensure_ascii=True),add_special_tokens=False)['input_ids'])
            counts['output_tokens_replayed']+=r['output_tokens'];s=score_record(row,r)
            for pair in s['citation_pairs']:
                counts['citation_pairs']+=1
                if pair['evidence_id'] not in row['contexts']['component']['provenance']:
                    counts['invalid_citation_pairs']+=1;assert not pair['exists'] and not pair['entailed'];invalid.append(dict(run_id=r['run_id'],**pair))
            allowed=row["contexts"]["component"]["provenance"]
            for eid in re.findall(r"evidence_[a-f0-9]{64}",r["text"]):
                if eid not in allowed:invalid.append(dict(run_id=r["run_id"],evidence_id=eid,raw_identifier_audit=True,accepted=False))
            assert not s['cross_candidate_leakage']
        store.close();print('VERIFIED',scale,flush=True)
    metrics=compute(run)
    for name,value in metrics.items():assert value==json.loads((run/(name+'.json')).read_text()),name
    # Replay prior stages without mutating their output directories or source.
    from rag.reasoning import regression
    regression.OUT=OUT;regression.main(folder/'legacy')
    protected=json.loads((OUT/'protected-manifest.json').read_text());changed=[name for name,h in protected.items() if not (ROOT/name).is_file() or sha(ROOT/name)!=h];assert not changed,changed
    check_freeze();config=json.loads((run/'config.json').read_text())
    for path,h in config['source_files'].items():assert sha(ROOT/path)==h
    dump(OUT/'independent-verification.json',dict(passed=True,slurm_job=os.environ['SLURM_JOB_ID'],expected_run_count=32,unique_runs=32,metrics_replayed_equal=True,query_max_delta=max(deltas,default=0),frozen_files=len(frozen),protected_files=len(protected),changed_or_missing=changed,invalid_citations=invalid,**counts))
    print('ALL VERIFIED',flush=True)
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
