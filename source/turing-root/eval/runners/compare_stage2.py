"""Read-only baseline comparison; writes solely to a new candidate-run subdirectory."""
import argparse,hashlib,importlib.util,json,pathlib,re,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'metrics'))
from promotions_v1 import promotion_metrics
sys.dont_write_bytecode=True  # Frozen baseline must remain strictly read-only, including cache files.

def load_run(run):
    cfg=json.loads((run/'config.json').read_text())
    if cfg['status']!='complete':raise ValueError('Incomplete run')
    snapshot=run/'eval_snapshot'
    spec=importlib.util.spec_from_file_location('frozen_score',snapshot/'metrics/score.py');scorer=importlib.util.module_from_spec(spec);spec.loader.exec_module(scorer)
    data=json.loads((snapshot/'datasets/resume_v1.json').read_text());schema=json.loads((snapshot/'schemas/analysis_v1.json').read_text())
    records=[json.loads(line) for line in (run/'raw_outputs.jsonl').read_text().splitlines()]
    if len(records)!=len(data['cases']) or {r['id'] for r in records}!={c['id'] for c in data['cases']}:raise ValueError('Case coverage mismatch')
    lookup={r['id']:r for r in records};results={}
    for mode in ['strict','fence_diagnostic']:
        rows=[];predictions={};fences=0
        for c in data['cases']:
            text=lookup[c['id']]['text']
            if mode=='fence_diagnostic':
                m=re.fullmatch(r'```(?:json)?\s*\n(.*)\n```',text.strip(),re.S)
                if m:text=m.group(1);fences+=1
            try:p=json.loads(text);ok=True
            except json.JSONDecodeError:p=None;ok=False
            predictions[c['id']]=p
            row=scorer.score(c,p,schema);row.update(id=c['id'],json_valid=ok);rows.append(row)
        metrics=scorer.aggregate(rows)
        if mode=='strict' and metrics!=json.loads((run/'metrics.json').read_text()):raise AssertionError('Saved and recomputed strict metrics differ')
        results[mode]={'metrics':metrics,'promotions':promotion_metrics(data['cases'],predictions,schema,scorer.valid),'fences_removed':fences}
    results['performance']={'input_tokens_total':sum(r['input_tokens'] for r in records),'output_tokens_total':sum(r['output_tokens'] for r in records),'generation_seconds':sum(r['seconds'] for r in records),'output_tokens_per_second':sum(r['output_tokens'] for r in records)/sum(r['seconds'] for r in records),'load_seconds':cfg['load_seconds'],'peak_allocated_gpu_gib':max(max(r['peak_gpu_bytes']) for r in records)/2**30,'token_limit_cases':sum(r['hit_token_limit'] for r in records)}
    return cfg,results

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=pathlib.Path,required=True);ap.add_argument('--candidate',type=pathlib.Path,required=True);a=ap.parse_args()
    if a.candidate.resolve()==a.baseline.resolve() or 'baseline' in a.candidate.parts:raise ValueError('Candidate must not be a baseline directory')
    bc,b=load_run(a.baseline);cc,c=load_run(a.candidate)
    fixed=['model_path','quantization','generation_overrides','seed','thinking','dependencies','model_metadata_hashes','weight_manifest','model_class','generation_defaults']
    checks={k:bc[k]==cc[k] for k in fixed}
    for rel in ['datasets/resume_v1.json','schemas/analysis_v1.json','metrics/score.py']:
        digest=lambda d:hashlib.sha256((d/'eval_snapshot'/rel).read_bytes()).hexdigest()
        checks[rel]=digest(a.baseline)==digest(a.candidate)
    if not all(checks.values()):raise AssertionError(checks)
    out=a.candidate/'comparison';out.mkdir(exist_ok=False)
    result={'baseline_run':str(a.baseline),'candidate_run':str(a.candidate),'control_checks':checks,'baseline':b,'prompt_engineered':c,'notes':['Strict mode parses the decoded response exactly as generated, without fence stripping or repair.','Baseline diagnostics are comparison context, not primary scores.','Supplementary promotion rates are undefined when no schema-valid predictions exist.','Grounded-bullet and unsupported-claim rates in metrics are citation/claim-ID proxies; semantic audits are separate.']}
    (out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    columns=[b['strict']['metrics']['deterministic'],b['fence_diagnostic']['metrics']['deterministic'],c['strict']['metrics']['deterministic'],c['fence_diagnostic']['metrics']['deterministic']]
    lines=['# Stage 2 metric comparison','', '| Metric | Base strict | Base fence diagnostic | Prompt strict | Prompt fence diagnostic |','|---|---:|---:|---:|---:|']
    def fmt(v):return 'N/A' if v is None else f'{v:.4f}' if isinstance(v,float) else str(v)
    for key in ['json_valid_rate','schema_valid_rate','matches_label_accuracy','claims_label_accuracy','matches_attribution_accuracy','claims_attribution_accuracy','bullet_count','grounded_bullet_count','grounded_bullet_rate','unsupported_claim_count','unsupported_claim_rate','job_requirement_coverage_proxy']:
        lines.append('| '+key+' | '+' | '.join(fmt(x[key]) for x in columns)+' |')
    for key in ['requirements','skills','missing_requirements','bullet_claim_selection','refusal']:
        for metric in ['precision','recall','f1']:lines.append('| '+key+'.'+metric+' | '+' | '.join(fmt(x[key][metric]) for x in columns)+' |')
    lines+=['','## Supplementary promotion metrics','', 'Gold-label and skill-list proxy counts/rates, denominators and missing-output coverage are in comparison.json. Baseline strict promotion rates are undefined, not zero.','',json.dumps({'baseline_diagnostic':b['fence_diagnostic']['promotions'],'prompt_strict':c['strict']['promotions']},indent=2)]
    (out/'metrics_table.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'controls':checks,'prompt_strict':c['strict']['metrics']['deterministic'],'baseline_diagnostic_promotions':b['fence_diagnostic']['promotions'],'prompt_strict_promotions':c['strict']['promotions']},indent=2))
if __name__=='__main__':main()
