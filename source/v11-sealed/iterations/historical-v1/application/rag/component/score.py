"""Primary scoring from untouched raw outputs; no cap repair or gold edits."""
import json,statistics
from collections import Counter
from .prepare import OUT,H,ROOT,dump,coverage
from .run import load_rows
from ..scale.metrics import score_record,aggregate_scored

def attribution(row,score):
    failures=[f+' FAILURE' for f in score['failures'] if f!='RETRIEVAL']
    if score['retrieval_loss']:
        q=row['case'];out=row['component'];selected=set(row['contexts']['component']['provenance']);ids=row['id_to_doc'];candidate=set()
        for trace in out['traces'].values():
            for r in trace['results']:
                candidate.update(ref['evidence_id'] for ref in [r['reference']]+r['corroborating_references'])
        required=[set(g['relations']) for g in q['gold'] if g['relations']]
        lost=[s for s in required if not s&{ids[e] for e in selected}]
        if all(s&{ids[e] for e in candidate} for s in lost):failures.append('MERGE/BUDGET FAILURE')
        elif out['decomposition']['status'].startswith('unresolved') or len(out['decomposition']['components'])<len(q['components']):failures.append('DECOMPOSITION FAILURE')
        else:failures.append('RETRIEVAL FAILURE')
    return sorted(set(failures))
def compute(run):
    raws=[json.loads(s) for s in (run/'raw.jsonl').read_text().splitlines()];scores=[];metrics={};performance={};comparisons={}
    legacy=json.loads((H/'benchmark-2332803/scored.json').read_text())
    for scale in ('SMALL','MEDIUM','LARGE','XL'):
        lookup={r['case']['id']:r for r in load_rows(scale)};sc=[]
        for raw in (r for r in raws if r['scale']==scale):
            row=lookup[raw['id']];s=score_record(row,raw);s['failures']=attribution(row,s);s['run_id']=raw['run_id'];sc.append(s)
        if not sc:continue
        metrics[scale]=aggregate_scored(sc);scores+=sc
        metrics[scale]['excluding_ambiguous_h06']=aggregate_scored([s for s in sc if s['id']!='h06'])
        comparisons[scale]={a:aggregate_scored([r for r in legacy if r['scale']==scale and r['arm']==a]) for a in ('rag3','rag5')}
        comparisons[scale]['component']=metrics[scale]
        for a in ('rag3','rag5'):comparisons[scale][a]['excluding_ambiguous_h06']=aggregate_scored([r for r in legacy if r['scale']==scale and r['arm']==a and r['id']!='h06'])
        rr=[r for r in raws if r['scale']==scale]
        performance[scale]={k:{'mean':statistics.mean(r[k] for r in rr),'median':statistics.median(r[k] for r in rr),'max':max(r[k] for r in rr)} for k in ('input_tokens','output_tokens','total_tokens','evidence_groups','evidence_chunks','seconds','tokens_per_second','peak_gpu_allocated_bytes','peak_gpu_reserved_bytes','prompt_reduction_vs_full','prompt_change_vs_rag3','prompt_change_vs_rag5')}
    return dict(scored=scores,metrics=metrics,performance=performance,comparison=comparisons,failures=[s for s in scores if s['failures']])
def main(run):
    result=compute(run)
    for k,v in result.items():dump(run/(k+'.json'),v)
    print(json.dumps(result['metrics'],indent=2))
if __name__=='__main__':
    import sys
    from pathlib import Path
    main(Path(sys.argv[1]))
