"""Independent process: reembed/retrieve/rerank, reconstruct prompts, decode raw IDs,
rescore and compare without mutating benchmark outputs or loading Qwen weights.
"""
import json,sys,hashlib
from pathlib import Path
from .prepare import ROOT,OUT,build,dump
from .evaluate import measure,aggregate
from .run import build_messages
from ..embeddings.local import LocalTransformerProvider

def main(run,folder):
    frozen=json.loads((OUT/'freeze_v2.json').read_text())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in frozen.items())
    original=json.loads((OUT/'prepared.json').read_text())
    provider=LocalTransformerProvider(json.loads((ROOT/'results/stage3c/models.lock.json').read_text())[0],str(ROOT/'models/stage3c'))
    count=0
    for old in original:
        new=build(old['case'],provider,folder/old['case']['id'])
        for key in old:
            if key!='retrieval_seconds':assert new[key]==old[key],(old['case']['id'],key)
        count+=1
    rows={r['case']['id']:r for r in original}
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(ROOT/'models/Qwen3.8-27B',local_files_only=True)
    raw=[json.loads(x) for x in (run/'raw.jsonl').read_text().splitlines()];scored=[]
    for r in raw:
        msg=build_messages(rows[r['id']],r['arm']);assert msg==r['messages']
        assert tok.apply_chat_template(msg,tokenize=False,add_generation_prompt=True,enable_thinking=False)==r['rendered_prompt']
        assert tok.decode(r['token_ids'],skip_special_tokens=True)==r['text']
        assert tok.decode(r['token_ids'],skip_special_tokens=False)==r['raw_text']
        scored.append(measure(rows[r['id']],r['arm'],r['text']))
    assert scored==json.loads((run/'scored.json').read_text())
    metrics={a:aggregate([r for r in scored if r['arm']==a]) for a in sorted({r['arm'] for r in scored})}
    assert metrics==json.loads((run/'metrics.json').read_text())
    dump(OUT/'independent-verification.json',{'passed':True,'exact_context_and_provenance_replays':count,'raw_token_decodes_and_prompt_replays':len(raw),'metrics_exactly_equal':True,'frozen_files':len(frozen),'note':'Qwen generation not rerun; independently replayed token decoding, scoring, real embeddings, retrieval, identity reranking and provenance.'})
    print('Independent verification passed',count,len(raw),flush=True)
if __name__=='__main__':main(OUT/sys.argv[1],Path(sys.argv[2]))
