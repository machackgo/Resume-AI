"""Report measured results, denominators and limitations, without model calls."""
import json,statistics,sys
from pathlib import Path
from collections import Counter
from .prepare import ROOT,OUT,dump
from .evaluate import aggregate

def pct(v):return 'n/a' if v is None else f'{100*v:.2f}%'
def main(name):
    run=OUT/name;metric=json.loads((run/'metrics.json').read_text());scored=json.loads((run/'scored.json').read_text());cfg=json.loads((run/'config.json').read_text());raw=[json.loads(x) for x in (run/'raw.jsonl').read_text().splitlines()]
    prepared=json.loads((OUT/'prepared.json').read_text());lookup={r['case']['id']:r for r in prepared}
    perf={}
    for arm in metric:
        rows=[r for r in raw if r['arm']==arm];generated=[r for r in rows if not r.get('reused_from_arm')]
        perf[arm]={'evaluated_contexts':len(rows),'actual_generations':len(generated),'exact_prompt_reuses':len(rows)-len(generated),
            'prompt_tokens_min':min(r['input_tokens'] for r in rows),'prompt_tokens_median':statistics.median(r['input_tokens'] for r in rows),'prompt_tokens_max':max(r['input_tokens'] for r in rows),
            'generated_tokens_median':statistics.median(r['output_tokens'] for r in rows),'generated_tokens_max':max(r['output_tokens'] for r in rows),
            'latency_median_seconds_actual_generations':statistics.median(r['seconds'] for r in generated) if generated else None,
            'latency_p95_seconds_actual_generations':sorted(r['seconds'] for r in generated)[int(.95*(len(generated)-1))] if generated else None,
            'tokens_per_second_actual_generations':sum(r['output_tokens'] for r in generated)/sum(r['seconds'] for r in generated) if generated else None,
            'peak_gpu_allocated_gib':max(r['peak_gpu_allocated_bytes'] for r in rows)/2**30,
            'peak_gpu_reserved_gib':max(r['peak_gpu_reserved_bytes'] for r in rows)/2**30,
            'token_limit_hits':sum(r['hit_token_limit'] for r in rows)}
    dump(run/'performance.json',perf)
    ids={r['id'] for r in scored if r['arm']=='rag1'}
    ablation={a:aggregate([r for r in scored if r['arm']==a and r['id'] in ids]) for a in ('rag1','rag3','rag5')}
    dump(run/'ablation.json',ablation)
    failures=[r for r in scored if r['failures']];dump(run/'failures.json',failures)
    lines=['# Stage 3G — Qwen + RAG evidence reasoning','',
        '**Stage 3G complete. Stage 3H has not begun.**','',
        'This report separates the historical Stage 2 prompt comparison from the matched-prompt full-context control. Missing evidence was UNSUPPORTED in Stage 2 and is UNKNOWN in Stage 3G. Apparent gains over Stage 2 cannot be assigned entirely to retrieval.','',
        '## Architecture implemented','',
        'Trusted candidate scope → unchanged Stage 3E semantic retrieval (internal 20, grouped exact duplicates, no expansion/caps) → Stage 3F identity reranker → five evidence groups → Qwen atomic judgments → strict JSON/ID/quote/ownership validation. Full provenance stays in each prepared response and sidecar. See stage3g_architecture.md for boundary and reproduction details.','',
        '## Files and preservation','',
        'Added rag/reasoning/{contract,prepare,run,evaluate,regression,verify,report}.py, __init__.py, system_v2.txt, schema.json, prepare.slurm and gpu.slurm; tests/rag/test_reasoning.py and test_reasoning_metrics.py; fixtures/rag/reasoning_eval/stage3g_v1.json; docs/stage3g_architecture.md and this report; results/stage3g/ artifacts. Earlier-stage code, models, environments and historical results were not modified. The final preservation report is results/stage3g/preservation.json.','',
        '## Slurm and model configuration','',
        f'Primary GPU Slurm job **{cfg["slurm_job_id"]}**, account cs541, partition academic, one A30, 8 CPUs, 64 GiB RAM, eight-hour maximum. The batch exits after the benchmark. Exact scheduler accounting is in results/stage3g/slurm_accounting.txt. Failed preparation/logging attempts and the cancelled diagnostic run with descriptive identifiers are retained and described in the execution audit. Only the blinded v2 run supplies primary metrics.','',
        f'Model path: `{cfg["model_path"]}`. Runtime architecture: `{cfg["architecture"]}`. Directory naming is not architectural identity. Existing Stage 2 weights/dependencies retained. NF4, double quantization, BF16 compute/dtype, requested device_map=auto; actual parameter devices {cfg["parameter_devices"]}. Greedy generation, max_new_tokens=1536, use_cache=true, thinking=false, seed=42. Full model configuration, quantization, default generation parameters, GPU/driver and library versions: `{name}/config.json`.','',
        '## Context, schema and security','',
        'Each JSON evidence group contains canonical evidence IDs, content, source type/origin, untrusted-data designation, verification policy, exact-support synthetic attestations when applicable, source version and span. Opaque evidence IDs serve as citation handles; native pointers and original attestation references remain in the validated provenance sidecars. No tenant ID, descriptive fixture identifier, source key, or ranking score is sent to Qwen. Requirement IDs and attestation references are opaque hashes. Delimited JSON lives in a user message separate from the system behavior contract. Evidence has no tool or scope-changing capability.','',
        'Output: information_need_id, label, atomic_claims (component_id, claim, label, evidence_ids, exact quotes, reason), evidence_ids union, missing_evidence and concise reason. No hidden reasoning traces. Raw parsing rejects fences, trailing prose, duplicate keys and nonfinite values. A failed raw result is not repaired for the primary metric.','',
        'Native citation resolution checks active vector → EmbeddingRecord → RetrievalChunk/revision → canonical evidence → source/version → pointer. Corpus ownership is checked upstream and again before context construction. Exact quote matching is necessary traceability, not a general entailment proof. Synthetic VerificationRecords exercise exact-support metadata only; no production verifier or real credential is claimed.','',
        '## Dataset and experimental controls','',
        f'{len(prepared)} synthetic cases, {sum(len(r["case"]["components"]) for r in prepared)} atomic components. Full-context gold distribution: '+str(dict(Counter(r['gold']['full']['label'] for r in prepared)))+'. No private data. Compatible Stage 3E/F wording is reused; newly authored cases cover the requested numeric/action/technology/trust/injection/isolation conditions.','',
        'stage2 uses original grounded_v3 system/task/schema and all current candidate evidence. full uses the Stage 3G contract with all current evidence; rag5 uses the identical contract and real top-five groups. All arms use identical inference settings. Entirely identical rendered prompts reuse the same greedy output, explicitly marked reused_from_arm; these are not counted as new generations or timed at zero as if fresh inference. Arms with different prompts always run.','',
        'Atomic slots are supplied without gold labels as structured task components. The experiment measures atomic judgment and aggregation, not autonomous decomposition discovery. Most candidates have only one evidence group. A retrieval-selected QLoRA stress fixture puts genuine adaptation at rank five beneath four learning/interest distractors, without manual reordering.','',
        '## Primary comparison','',
        '| Arm | Cases | Strict JSON | Schema | Full contract | Label accuracy | Macro F1 |','|---|---:|---:|---:|---:|---:|---:|']
    for a in ('stage2','full','rag5'):
        m=metric[a];lines.append(f'| {a} | {m["cases"]} | {pct(m["strict_json_validity"])} | {pct(m["schema_validity"])} | {pct(m["contract_validity"])} | {pct(m["label_accuracy"])} | {m["macro_f1"]:.4f} |')
    lines+=['','Stage 2 full-contract validity above means its historical schema, not the new atomic/quote contract. New-contract failures are not concealed by schema validity. Context-conditional accuracy is retained separately in metrics.json.','','## Support-label metrics','','| Arm | Label | Gold n | Precision | Recall | F1 |','|---|---|---:|---:|---:|---:|']
    for a in ('stage2','full','rag5'):
        for label,v in metric[a]['labels'].items():lines.append(f'| {a} | {label} | {v["support"]} | {pct(v["precision"])} | {pct(v["recall"])} | {pct(v["f1"])} |')
    lines+=['','## Atomic, compound, citation and hallucination results','','| Metric | Stage 2 | Full control | RAG 5 |','|---|---:|---:|---:|']
    for k in ('atomic_claim_accuracy','compound_claim_accuracy','citation_validity','citation_precision','unsupported_citation_rate','fabricated_evidence_id_rate','hallucinated_candidate_claim_rate','prompt_injection_failure_rate','cross_candidate_leakage_rate'):
        lines.append('| '+k+' | '+' | '.join(pct(metric[a][k]) for a in ('stage2','full','rag5'))+' |')
    lines+=['','Citation precision scores authored positive/partial/contradiction atomic relations only; UNKNOWN explanatory citations are checked for existence and separately reviewed. Rates are micro-averaged over atomic citation pairs, with counts in metrics.json. Fabricated-ID rate counts emitted atomic plus top-level ID occurrences. Hallucination rate counts overstated positive/partial atomic conclusions, not every free-text assertion. A separate semantic audit covers prose and examples.','','## Prompt injection and tenant isolation','',
        'Three attack cases per primary arm include imperative label promotion, fake role/delimiter text and legitimate evidence mixed with a malicious technology instruction. The model has no retrieval tool. Candidate B has perfect Kubernetes evidence and a secret canary; trusted Candidate A retrieval cannot read its vector and rejects an attempt to use B scope. Foreign IDs and the canary are checked against output. Zero observed leakage is a fixture result, not a production security proof.','','## Evidence-budget ablation (same ten cases)','','| Groups | Accuracy vs full available evidence | Context-conditional accuracy | Atomic accuracy conditional on supplied context | Citation precision |','|---|---:|---:|---:|---:|']
    for a,m in ablation.items():lines.append(f'| {a} | {pct(m["label_accuracy"])} | {pct(m["context_label_accuracy"])} | {pct(m["atomic_claim_accuracy"])} | {pct(m["citation_precision"])} |')
    lines+=['','A safe UNKNOWN after lost retrieval support counts against end-to-end accuracy but not against context-conditional reasoning accuracy. No content-only/provenance ablation was run; the matrix was limited to the requested evidence-budget comparison.','','## Failure attribution','',
        'Categories may overlap. Stage 2 absence-policy mismatches appear in reasoning comparisons against current semantics but are not evidence that retrieval fixed them. Smaller-budget selection losses are distinguished from primary top-five retrieval misses.','', '| Arm | Attributed failures |','|---|---|']
    for a,m in metric.items():lines.append(f'| {a} | {m["failure_attribution"]} |')
    lines+=['','Every failure, expected/context label, atomic counts, citation pair judgment and contract error is in '+name+'/failures.json and scored.json. Interpret the separate semantic audit before treating an automatic failure as unambiguous human-adjudicated truth.','','## Runtime and resource use','',
        f'Qwen load: {cfg["load_seconds"]:.2f} s. Benchmark process total: {cfg["total_seconds"]:.2f} s. Model loaded once for the full benchmark. Smoke used a separate load.','',
        '| Arm | New generations / contexts | Prompt tokens median / max | Output tokens median / max | Median latency (s), new generations | Tokens/s, new generations | Peak allocated GiB |','|---|---:|---:|---:|---:|---:|---:|']
    for a,p in perf.items():
        latency=p['latency_median_seconds_actual_generations'];speed=p['tokens_per_second_actual_generations']
        lines.append(f'| {a} | {p["actual_generations"]} / {p["evaluated_contexts"]} | {p["prompt_tokens_median"]} / {p["prompt_tokens_max"]} | {p["generated_tokens_median"]} / {p["generated_tokens_max"]} | {latency:.2f} | {speed:.2f} | {p["peak_gpu_allocated_gib"]:.2f} |' if latency is not None else f'| {a} | all exact-prompt reuses | — | — | n/a | n/a | — |')
    lines+=['','Torch peak allocation/reservation is not identical to whole-device nvidia-smi use. No kernel packages were installed; existing reference-kernel fallback is retained. Context construction and retrieval latencies, full token IDs, raw special-token text, prompt rendering and actual generation timings are saved. Token-cap hits: '+str({a:p['token_limit_hits'] for a,p in perf.items()})+'.','','## Reproducibility and tests','',
        'See regression.json, preservation.json and independent-verification.json for final independently computed counts and status. Existing tests and historical artifacts were not weakened or rewritten. Independent verification reconstructs contexts/provenance and prompts, decodes saved token IDs and rescores every result; it does not claim a second Qwen generation run.','',
        '## Limitations and exact next-stage boundary','',
        'Small, single-author synthetic sample; short evidence and many identical full/RAG prompts; supplied atomic decomposition; historical label-policy mismatch; no held-out production corpus or independent human adjudicator. Relation-table citation entailment is limited to this fixture. Verification inputs are simulated. Prompt injection is tested, not formally prevented by text delimiters. Multi-chunk canonical-ID ambiguity fails closed. No concurrency/serving benchmark or context truncation strategy is introduced.','',
        'Stage 3H may evaluate final RAG optimization/validation only after reviewing these measured outcomes: broaden long-history and adversarial held-out cases, independently adjudicate citations, evaluate autonomous atomization and retain strict abstention/ownership checks. This report is a recommendation only. Stage 3H, QLoRA, fine-tuning, browser automation, discovery, applications, CV/cover-letter agents and recruiter outreach have not begun.']
    (ROOT/'docs/stage3g_report.md').write_text('\n'.join(lines)+'\n')
    print('Report written',flush=True)
if __name__=='__main__':main(sys.argv[1])
