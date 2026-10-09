"""Independent raw-output scoring, with explicit per-failure attribution."""
import json,statistics
from pathlib import Path
from .prepare import ROOT,H,OUT,dump
from .run import load_rows
from rag.scale.metrics import score_record,aggregate_scored
from rag.reasoning.contract import strict_parse
LAYERS={'INGESTION','CHUNKING','DECOMPOSITION','QUERY_CONSTRUCTION','EMBEDDING','VECTOR_INDEX','INITIAL_RETRIEVAL','TOP_K_CUTOFF','DEDUPLICATION','COMPONENT_MERGE','BOUNDED_SELECTION','CONTEXT_CONSTRUCTION','QWEN_REASONING','CITATION','STRUCTURED_OUTPUT','SECURITY'}
def classify(row,score):
    events=[]
    def add(layer,detail,uncertainty=None):
        assert layer in LAYERS;events.append(dict(layer=layer,detail=detail,uncertainty=uncertainty))
    if not score.get('json_valid',True) or not score.get('schema_valid',True):add('STRUCTURED_OUTPUT','Unrepaired raw JSON or schema failure.')
    if score.get('retrieval_loss'):
        selected={row['id_to_doc'][e] for e in row['contexts']['component']['provenance']};pool={row['id_to_doc'][ref['evidence_id']] for t in row['component']['traces'].values() for r in t['results'] for ref in [r['reference']]+r['corroborating_references']}
        lost=[set(a['relations']) for a in row['case']['gold'] if a['relations'] and not set(a['relations'])&selected]
        add('BOUNDED_SELECTION' if lost and all(s&pool for s in lost) else 'INITIAL_RETRIEVAL','Full-corpus gold differs from delivered-context gold.','Pool absence alone cannot distinguish semantic rank from other upstream causes; consult forensic rank trace.')
    for f in score['failures']:
        if f=='QWEN REASONING':add('QWEN_REASONING','Model reasoning differs from the evidence delivered to it.')
        elif f=='CITATION':add('CITATION','Citation membership, exact quote, or authored entailment relation failed.')
        elif f=='STRUCTURED OUTPUT' and not any(e['layer']=='STRUCTURED_OUTPUT' for e in events):add('STRUCTURED_OUTPUT','Output contract violation.')
        elif f=='SECURITY':add('SECURITY','Measured unauthorized identifier or scope violation; inspect raw output.')
    return events

def compute(run):
    raw=[json.loads(s) for s in (run/'raw.jsonl').read_text().splitlines()];scores=[];metrics={};performance={};comparison={};events=[];parsed=[]
    h=json.loads((H/'benchmark-2332803/scored.json').read_text());i=json.loads((ROOT/'results/stage3i/benchmark-2333661/scored.json').read_text());iraw=[json.loads(s) for s in (ROOT/'results/stage3i/benchmark-2333661/raw.jsonl').read_text().splitlines()]
    for scale in ('LARGE','XL'):
        lookup={r['case']['id']:r for r in load_rows(scale)};ss=[];rr=[r for r in raw if r['scale']==scale]
        for r in rr:
            row=lookup[r['id']];s=score_record(row,r);s['run_id']=r['run_id'];ss.append(s);events.extend(dict(run_id=r['run_id'],id=r['id'],scale=scale,**e) for e in classify(row,s));p,error=strict_parse(r['text']);parsed.append(dict(run_id=r['run_id'],prediction=p,parse_error=error))
        scores+=ss;metrics[scale]=aggregate_scored(ss)
        comparison[scale]={'stage3h_top3':aggregate_scored([s for s in h if s['scale']==scale and s['arm']=='rag3']),'stage3i':aggregate_scored([s for s in i if s['scale']==scale]),'stage3j':metrics[scale]}
        comparison[scale]['excluding_h06']={a:aggregate_scored([s for s in src if s['scale']==scale and s['id']!='h06' and (a!='stage3h_top3' or s['arm']=='rag3')]) for a,src in [('stage3h_top3',h),('stage3i',i),('stage3j',ss)]}
        for r in rr:r['prompt_change_vs_stage3i']=r['input_tokens']/next(x['input_tokens'] for x in iraw if x['scale']==scale and x['id']==r['id'])-1
        performance[scale]={k:dict(mean=statistics.mean(r[k] for r in rr),min=min(r[k] for r in rr),max=max(r[k] for r in rr),sum=sum(r[k] for r in rr)) for k in ('input_tokens','output_tokens','total_tokens','evidence_groups','evidence_chunks','seconds','tokens_per_second','peak_gpu_allocated_bytes','peak_gpu_reserved_bytes','prompt_reduction_vs_full','prompt_change_vs_stage3i')}
    return dict(scored=scores,metrics=metrics,overall_metrics=aggregate_scored(scores),performance=performance,comparison=comparison,failure_attributions=events,parsed_predictions=parsed)
def main(run):
    for name,value in compute(run).items():dump(run/(name+'.json'),value)
if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]))
