"""Separate CPU replay of vectors, scope, contexts, tokens, predictions, history."""
import os,json,re,statistics,subprocess,sys
from pathlib import Path
from dataclasses import asdict
from .prepare import ROOT,OUT,H,dump,sha,corpus,Scope,MemoryLedger,CLOCK,populate,CandidateEvidenceRetriever,EmbeddingSpace,RetrievalConfig,CitationTextResolver,InformationNeed,NeedType,LocalTransformerProvider,record_from_dict,at_scale
from .retrieve import ComponentConfig,ComponentRetriever
from .run import check_freeze,load_rows,build_messages
from .score import compute
from ..scale.metrics import score_record
from ..reasoning.contract import strict_parse

def main(run,folder):
    assert os.getenv('SLURM_JOB_ID');frozen=check_freeze();cfg=ComponentConfig(**json.loads((OUT/'config.json').read_text())['selected']);data=json.loads((H/'dataset.json').read_text())
    source=json.loads((run/'config.json').read_text())['source_files']
    for p,h in source.items():assert sha(ROOT/p)==h,p
    provider=LocalTransformerProvider(json.loads((ROOT/'results/stage3c/models.lock.json').read_text())[0],str(ROOT/'models/stage3c'));queries=json.loads((OUT/'query-vectors.json').read_text());embed=provider.embed_queries
    deltas=[]
    for q,v in queries.items():
        actual=embed([q])[0];delta=max(abs(x-y) for x,y in zip(v,actual));assert delta<1e-5;deltas.append(delta)
    provider.embed_queries=lambda texts:tuple(tuple(queries[t]) for t in texts)
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(ROOT/'models/Qwen3.8-27B',local_files_only=True)
    raw=[json.loads(s) for s in (run/'raw.jsonl').read_text().splitlines()];assert len(raw)==64;assert len({r['run_id'] for r in raw})==64;assert {(r['scale'],r['id']) for r in raw}=={(s,'h%02d'%n) for s in ('SMALL','MEDIUM','LARGE','XL') for n in range(1,17)}
    counts={'contexts':0,'stored_provenance_roundtrips':0,'citation_pairs':0,'output_id_occurrences':0,'output_tokens_replayed':0};diagnostic=[];lookups={}
    for scale in ('SMALL','MEDIUM','LARGE','XL'):
        scope=Scope('synthetic-stage3h','candidate-A');ledger=MemoryLedger(clock=CLOCK);svc,chunks,owners,records,attest=corpus({'id':'corpus-A','documents':at_scale(data,scale)},scope,provider,ledger)
        hist=json.loads((H/(scale+'-corpus.json')).read_text())['records'];assert len(records)==len(hist)
        for a,b in zip(records,hist):assert {k:v for k,v in json.loads(json.dumps(asdict(a))).items() if k!='vector'}=={k:v for k,v in b.items() if k!='vector'}
        records=[record_from_dict(r) for r in hist];store=populate(folder/scale,svc,chunks,records);retriever=CandidateEvidenceRetriever(store,provider,EmbeddingSpace(provider.config,'title-section-v1'),svc,[r.record_id for r in records],RetrievalConfig());resolver=CitationTextResolver(store,svc);cr=ComponentRetriever(retriever,resolver,cfg)
        lookup={r['case']['id']:r for r in load_rows(scale)};lookups[scale]=lookup
        for row in lookup.values():
            q=row['case'];need=InformationNeed(NeedType.JOB_REQUIREMENT,q['requirement'],q['id']);actual=cr.retrieve(*scope.key,need,attest);actual=json.loads(json.dumps(actual))
            for k in ('context','decomposition','traces','mapping','config'):assert actual[k]==row['component'][k],(scale,q['id'],k)
            counts['contexts']+=1
            for e,v in actual['context']['provenance'].items():
                assert v['reference']['scope']==asdict(scope) and v['reference']['lifecycle']=='active' and v['reference']['trust']=='untrusted_data'
            if row['gold']['component']!=row['gold']['full']:
                # Read-only diagnostic: raw vector rank of required core proofs.
                from ..vectorstore.models import VectorQuery,SearchFilter
                ranks={}
                for comp in actual['decomposition']['components']:
                    hits=store.search_vectors(VectorQuery(retriever.space,tuple(queries[comp['text']]),min(10000,len(records)),SearchFilter()))
                    core={}
                    for i,hit in enumerate(hits,1):
                        r=store.get_embedding(hit.embedding_id).record;d=owners[r.chunk_id]
                        if d in q['relevant']:core[d]={'raw_rank':i,'score':hit.score}
                    ranks[comp['text']]=core
                diagnostic.append(dict(scale=scale,id=q['id'],required_core_vector_ranks=ranks,full_gold=row['gold']['full'],context_gold=row['gold']['component']))
        counts['stored_provenance_roundtrips']+=len(records)
        for r in (r for r in raw if r['scale']==scale):
            row=lookup[r['id']];msg=build_messages(row);assert msg==r['messages'];render=tok.apply_chat_template(msg,tokenize=False,add_generation_prompt=True,enable_thinking=False);assert render==r['rendered_prompt'];assert len(tok(render,add_special_tokens=False)['input_ids'])==r['input_tokens'];assert len(r['token_ids'])==r['output_tokens'];assert tok.decode(r['token_ids'],skip_special_tokens=True)==r['text'];assert tok.decode(r['token_ids'],skip_special_tokens=False)==r['raw_text'];assert r['total_tokens']==r['input_tokens']+r['output_tokens'];counts['output_tokens_replayed']+=r['output_tokens']
            assert r['evidence_tokens']==len(tok(json.dumps(row['contexts']['component']['groups'],ensure_ascii=True),add_special_tokens=False)['input_ids'])
            allowed=row['contexts']['component']['provenance'];s=score_record(row,r)
            for pair in s['citation_pairs']:
                assert pair['evidence_id'] in allowed;counts['citation_pairs']+=1
            # Include malformed raw outputs in unauthorized opaque-ID audit.
            for eid in re.findall(r'evidence_[a-f0-9]{64}',r['text']):assert eid in allowed;counts['output_id_occurrences']+=1
            assert 'CANARY_B_7391' not in r['text'] and 'EV-SECRET' not in r['text']
        store.close();print('REPLAY',scale,'passed',flush=True)
    metrics=compute(run)
    for k,v in metrics.items():assert v==json.loads((run/(k+'.json')).read_text()),k
    protected=json.loads((OUT/'protected-manifest.json').read_text());changed=[p for p,h in protected.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h];assert not changed,changed
    # Existing historical model/cache and earlier-stage protection mechanisms.
    prior=json.loads((H/'preexisting_manifest.json').read_text());priorchanged=[p for p,h in prior.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h];assert not priorchanged,priorchanged
    stageh=json.loads((H/'freeze.json').read_text())['files'];assert all(sha(ROOT/p)==h for p,h in stageh.items())
    checks={};testcounts={}
    commands={'stage3-tests':['-m','unittest','discover','-s','tests/rag','-v'],'stage1-stage2-tests':['-m','unittest','discover','-s','eval/tests','-v'],'stage2-replay':['eval/runners/verify_stage2_run.py','results/prompt_engineered/grounded-v3-benchmark-2325384-1']}
    for name,args in commands.items():
        p=subprocess.run([sys.executable,'-B',*args],capture_output=True,text=True);(OUT/(name+'.log')).write_text(p.stdout+p.stderr);checks[name]=p.returncode==0
        m=re.search(r'Ran (\d+) tests?',p.stderr)
        if m:testcounts[name]=int(m[1])
    assert all(checks.values()),checks
    dump(OUT/'retrieval-failure-diagnostic.json',diagnostic)
    dump(OUT/'independent-verification.json',dict(passed=True,slurm_job_id=os.environ['SLURM_JOB_ID'],**counts,metrics_equal=True,unique_primary_run_ids=64,expected_primary_cases=64,frozen_files=len(frozen),query_reembedding_max_absolute_delta=max(deltas),replay_uses_exact_frozen_vectors=True,protected_files=len(protected),protected_stage1_3g_files=len(prior),stage3h_frozen_files=len(stageh),changed_or_missing=changed+priorchanged,tests=testcounts,checks=checks))
    print('ALL VERIFIED',flush=True)
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
