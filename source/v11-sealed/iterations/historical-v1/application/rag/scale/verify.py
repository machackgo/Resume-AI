"""Separate CPU process: actual re-embedding, provenance replay and raw-token audit."""
import json,os,sys,statistics
from pathlib import Path
from .prepare import ROOT,OUT,dump,sha,load_rows,build_scale
from .dataset import dataset,SCALES
from .metrics import score_record,aggregate_scored,retrieval_metrics
from ..reasoning.run import build_messages
from ..embeddings.local import LocalTransformerProvider

def normal(x):return json.loads(json.dumps(x))
def main(run,folder):
    assert os.getenv('SLURM_JOB_ID')
    frozen=json.loads((OUT/'freeze.json').read_text())['files']
    assert all(sha(ROOT/p)==h for p,h in frozen.items())
    data=json.loads((OUT/'dataset.json').read_text());assert dataset()==data
    provider=LocalTransformerProvider(json.loads((ROOT/'results/stage3c/models.lock.json').read_text())[0],str(ROOT/'models/stage3c'))
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(ROOT/'models/Qwen3.8-27B',local_files_only=True)
    raws=[json.loads(x) for x in (run/'raw.jsonl').read_text().splitlines()];scored=[];metrics={};retrieval={};count=0;citations=0;roundtrips=0
    for scale in SCALES:
        old=load_rows(scale);new,meta=build_scale(data,scale,provider,folder/scale);new=normal(new)
        for a,b in zip(old,new):
            for k in a:
                if k!='retrieval_seconds':assert a[k]==b[k],(scale,a['case']['id'],k)
            count+=1
        oldmeta=json.loads((OUT/(scale+'-corpus.json')).read_text())
        for k in oldmeta:
            if k!='seconds':assert oldmeta[k]==normal(meta[k]),(scale,k)
        roundtrips+=meta['provenance_roundtrips'];lookup={r['case']['id']:r for r in new}
        sr=[]
        for raw in [r for r in raws if r['scale']==scale]:
            row=lookup[raw['id']];msg=build_messages(row,raw['arm'])
            assert msg==raw['messages']
            rendered=tok.apply_chat_template(msg,tokenize=False,add_generation_prompt=True,enable_thinking=False)
            assert rendered==raw['rendered_prompt']
            assert len(tok(rendered,add_special_tokens=False)['input_ids'])==raw['input_tokens']
            assert tok.decode(raw['token_ids'],skip_special_tokens=True)==raw['text']
            assert tok.decode(raw['token_ids'],skip_special_tokens=False)==raw['raw_text']
            assert len(raw['token_ids'])==raw['output_tokens'];assert raw['total_tokens']==raw['input_tokens']+raw['output_tokens']
            s=score_record(row,raw);sr.append(s)
            # Every allowed citation resolves via freshly rebuilt stored vectors.
            citations+=sum(p['exists'] for p in s['citation_pairs'])
        scored+=sr
        metrics[scale]={arm:aggregate_scored([r for r in sr if r['arm']==arm]) for arm in ('full','rag3','rag5') if any(r['arm']==arm for r in sr)}
        rr=[dict(id=r['case']['id'],**retrieval_metrics(r)) for r in old]
        retrieval[scale]={'cases':rr,'mean':{k:statistics.mean([r[k] for r in rr if r[k] is not None]) if any(r[k] is not None for r in rr) else None for k in rr[0] if k!='id'}}
        print('Replay',scale,'passed',flush=True)
    assert scored==json.loads((run/'scored.json').read_text())
    assert metrics==json.loads((run/'metrics.json').read_text())
    assert retrieval==json.loads((run/'retrieval.json').read_text())
    smoke=json.loads((run/'smoke.json').read_text());repeat=[]
    for r in smoke:
        match=next(x for x in raws if x['scale']==r['scale'] and x['id']==r['id'] and x['arm']==r['arm'])
        repeat.append(dict(id=r['id'],prompt_equal=r['rendered_prompt']==match['rendered_prompt'],output_tokens_equal=r['token_ids']==match['token_ids']))
    dump(OUT/'independent-verification.json',dict(passed=True,contexts_rebuilt=count,stored_provenance_roundtrips=roundtrips,citation_occurrences_roundtripped=citations,prompt_token_and_raw_output_replays=len(raws),metrics_equal=True,retrieval_metrics_equal=True,smoke_fresh_generation_repeats=repeat,frozen_files=len(frozen),note='Separate CPU rebuild and rescore; not a second full Qwen generation run.'))
    from ..reasoning import regression
    regression.OUT=OUT
    regression.main(folder/'historical',audit=True)
    print('ALL VERIFIED',flush=True)
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]))
