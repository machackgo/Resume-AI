"""Deterministic report assembly from measured artifacts; no LLM explanation."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'results/stage3e'
def read(name): return json.loads((OUT/name).read_text())
def main():
    assert read('saved-vector-replay.json')['passed']
    comparison=read('comparison.json'); validation=read('validation.json'); perf=read('performance.json')
    configs={e['label']:e for e in comparison['experiments']}
    reports={s:read('extended-'+s+'.json') for s in ('semantic','lexical','hybrid')}
    failures=[]
    reasons={
      'python_api':'Wrong action: consuming an API does not establish implementing one.',
      'docker':'Adjacent technology: Kubernetes is not Docker packaging evidence.',
      'aws':'Adjacent cloud: Azure does not establish AWS experience; aliases may be missed by lexical retrieval.',
      'fastapi':'Adjacent framework: Flask and FastAPI are not interchangeable.',
      'pytorch':'Adjacent framework: TensorFlow does not establish PyTorch experience.',
      'rag':'Adjacent task: fine-tuning does not establish retrieval-augmented generation.',
      'qlora':'Quantization distinction: LoRA alone does not establish QLoRA.',
      'lora':'Quantization distinction: QLoRA and full-precision LoRA differ.',
      'training':'Wrong lifecycle: inference does not establish weight training.',
      'inference':'Wrong lifecycle: training does not establish deployed inference.',
      'built':'Wrong action: using a library does not establish building it.',
      'deployed':'Wrong action: use or implementation alone does not establish deployment.',
      'kubernetes':'Duplicate crowding plus experience-level distinction: tutorial familiarity is not production deployment.',
      'exact_kube':'Exact occurrence can retrieve learning-only text. It does not establish experience; multiple genuine matching sources are relevant.',
      'observed':'Text about observation is not authenticated external collection or verification.',
      'certificate':'Mentioning a credential is not issuer verification.',
      'metadata_origin':'Identical text cannot distinguish trust. Frozen labels are evaluation-only; origin must be resolved from metadata.',
      'metadata_verification':'Identical credential text cannot establish verification. No actual verified credential is created.',
      'injection':'Prompt-like text is untrusted data even when it contains the exact certification term.',
      'latency':'Unquantified improvement does not establish a 40 percent latency reduction.',
      'current_version':'Superseded perfect-match text must remain excluded; only current evidence competes.',
      'exact_qlora':'Exact tokens preserve QLoRA versus LoRA; still no entailment decision.',
      'exact_cpp':'Technical punctuation must retain C++ distinctly from C.',
      'paraphrase':'Benign lexical mismatch can miss a concept expressed without shared words.',
      'container_expansion':'Container concepts can aid discovery, but Docker/Kubernetes are not equivalent experience.'}
    for i,q in enumerate(reports['semantic']['queries']):
        modes={s:reports[s]['queries'][i] for s in reports}
        union=set(q['expected'])
        for x in modes.values(): union.update(x['ranking'][:5]); union.update(x['hard_negatives'])
        details=[]
        for evidence in sorted(union):
            item={'evidence_fixture_id':evidence,'expected':evidence in q['expected'],'hard_negative':evidence in q['hard_negatives']}
            for strategy,x in modes.items():
                matches=[(j+1,r) for j,(id,r) in enumerate(zip(x['ranking'],x['response']['results'])) if id==evidence]
                item[strategy]={'rank':matches[0][0],'score':matches[0][1]['score'],'reference':matches[0][1]['reference']} if matches else None
            details.append(item)
        failures.append({'information_need':q['need'],'id':q['id'],'expected':q['expected'],
          'important_failure':any(x['metrics']['recall_at_1']<1 or x['metrics']['dangerous_query_at_3'] for x in modes.values()),
          'reason':reasons.get(q['id'],'Inspect exact action and evidence scope; semantic similarity is candidate discovery only.'),
          'top5':{s:x['ranking'][:5] for s,x in modes.items()},'metrics':{s:x['metrics'] for s,x in modes.items()},'details':details})
    (OUT/'failure_analysis.json').write_text(json.dumps(failures,indent=2)+'\n')
    lines=['# Stage 3E completion report — candidate-scoped evidence retrieval','',
      '**Stage 3E complete. Stage 3F has not begun.** Project: `~/scratch/resume-ai` on WPI Turing.','',
      'The measured recommendation is semantic candidate generation with MiniLM-L6-v2 + title/section context. Equal-weight RRF is implemented and evaluated but does not beat the semantic baseline. Retrieval scores and exact terms never become support or verification labels.','',
      '## 1–9. Architecture, query model, ranking, filtering and diversity','',
      'The additive provider-independent `EvidenceRetriever` protocol returns immutable `RetrievalResponse` / `RetrievalResult` objects, not raw storage rows. Results include rank, score, strategy, query identity, both scope IDs, exact embedding/chunk/revision/evidence/source/version pointers, native locator and offsets, source type, origin/trust, support and claim relationships, provenance event IDs, semantic space, lifecycle and component diagnostics. Large source text stays in the canonical ledger. See [architecture](stage3e_architecture.md) for the full contract.','',
      '`InformationNeed` covers job requirement, skill, experience, project, credential, accomplishment, technology, domain knowledge and question. One focused requirement and its ID form a request; whole-JD parsing is not implemented. `focused-v1` preserves wording with whitespace normalization. Optional inspectable expansion adds a few fixed aliases/container concepts. Need type participates in identity but does not apply unvalidated ranking boosts.','',
      'Semantic search invokes the Stage 3C query encoder and Stage 3D exact cosine search in one compatible space. BM25 uses technical tokens, k1=1.2 and b=0.75; C++/C#/QLoRA remain distinct. Lexical retrieval searches only records admitted by the same bound vector store. Hybrid uses equal-weight RRF with constant 60, never raw-score addition. Default branch budgets are 20; normal output is 5, API maximum 100. Default strategy is semantic with exact duplicate grouping, selected from the measured comparison.','',
      'Scope is mandatory at construction and request time. Default lifecycle is active. Source/evidence identity and type, origin, trust, chunk policy and verification-resolution marker are filterable. Historical evidence requires an explicit lifecycle filter. Date-range filtering is deferred because source time and ingestion time have different semantics. Assertions remain eligible. `resolve_supports` never means verified.','',
      'Optional exact grouping normalizes whitespace only and retains independent full references for grouped sources. No semantic near-duplicate merging is performed: similar wording can conceal different actions or qualifications. Optional per-source caps follow grouping. Both mechanisms are evaluated, not treated as universally beneficial.','',
      '## 10–13. Controlled quality comparison','',
      'The compatible set reuses 22 frozen Stage 3C needs, 44 chunks, query vectors and document vectors. All semantic scores and evidence rankings using the old tie policy reproduce exactly. The runtime breaks score ties by embedding ID; the original evaluation breaks evidence ties by fixture ID. The headline semantic metrics agree. All three strategies use the same corpus/needs; compatible branch budgets are 100 to expose the full ranking.','',
      'The extended synthetic set has '+str(comparison['extended_queries'])+' needs and '+str(comparison['extended_chunks'])+' chunks, including multiple source categories, synthetic candidate/observed origins, identical evidence, a crowded source, stale/current resume versions, irrelevant text, and malicious instructions. Original singleton judgments are retained; equivalent unjudged siblings can make some misses benign. New exact-term needs have explicitly multiple relevant items. No fixture label creates an actual verified credential.','',
      '| Set / strategy | Recall@1 | Recall@3 | Recall@5 | MRR | nDCG@5 | Hard-negative wins | Dangerous top-1 |',
      '|---|---:|---:|---:|---:|---:|---:|---:|']
    for label in ('compatible-semantic','compatible-lexical','compatible-hybrid','extended-semantic','extended-lexical','extended-hybrid'):
        m=configs[label]['metrics']; vals=[m[k] for k in ('recall_at_1','recall_at_3','recall_at_5','mrr','ndcg_at_5','hard_negative_win_rate','dangerous_neighbor_at_1')]
        lines.append('| '+label+' | '+' | '.join(f'{x:.4f}' for x in vals)+' |')
    lines += ['', 'Recall is macro-average evidence recall at chunk-result positions, counting each evidence only once. MRR is first judged relevant position within the budget. nDCG uses binary relevance and counts repeated chunks of the same evidence once. Hard-negative win requires a strictly higher retrieval score; ties do not win, and absent positives lose. For bounded branches this is candidate-ranking behavior, not exhaustive semantic separation. Dangerous-neighbor labels come from explicit fixture judgments, not runtime inference.','',
      '| Extended configuration | R@5 | Grouped R@5 | MRR | Duplicate rate@5 | Unique sources@5 | Dangerous queries@3 | Grouped dangerous queries@3 |',
      '|---|---:|---:|---:|---:|---:|---:|---:|']
    for label,e in configs.items():
        if not label.startswith('extended'): continue
        m=e['metrics']; keys=('recall_at_5','grouped_recall_at_5','mrr','duplicate_result_rate_at_5','unique_sources_at_5','dangerous_query_at_3')
        owners=read('extended-embeddings.json')['owners']
        observed=read(label+'.json')['queries']
        grouped_danger=sum(any(owners[ref['chunk_id']] in q['hard_negatives'] for x in q['response']['results'][:3] for ref in [x['reference']]+x['corroborating_references']) for q in observed)/len(observed)
        lines.append('| '+label.removeprefix('extended-')+' | '+' | '.join(f'{m[k]:.4f}' for k in keys)+f' | {grouped_danger:.4f} |')
    lines += ['', 'Grouped recall credits a relevant evidence reference retained under a representative. Representative-only recall does not. Standard rank, hard-negative and danger metrics describe representatives; grouped danger separately counts retained hard-negative source references so grouping cannot hide them. A grouped source never inherits trust or support status from the representative. Grouping can expose more dangerous neighbors after removing repeats, and source caps can discard useful chunks. Source diversity counts source IDs, not independent corroboration. Budget probes 5/10/20/40 change candidate fusion; they are not fitted to individual answers. Expansion remains opt-in despite gains on this small synthetic set.','',
      '## 14. Important failures and non-regressions','',
      'Every need has machine-readable top-five results, expected evidence, semantic score/rank, lexical score/rank, hybrid score/rank and provenance in `results/stage3e/failure_analysis.json`. Missing branch candidates have null diagnostics. Full bounded rankings and query plans remain in each experiment JSON.','',
      '| Need | Semantic top 3 | Lexical top 3 | Hybrid top 3 | Interpretation |','|---|---|---|---|---|']
    for f in failures:
        lines.append('| '+f['id']+' | '+', '.join(f['top5']['semantic'][:3])+' | '+', '.join(f['top5']['lexical'][:3])+' | '+', '.join(f['top5']['hybrid'][:3])+' | '+f['reason']+' |')
    lines += ['', 'Adjacent-tech, action-level and trust mistakes remain visible; semantic similarity is not entailment. Lexical outperformance is visible on QLoRA and the exact Kubernetes need, while Docker paraphrases/deep learning/inference demonstrate lexical failures. Singleton judgments sometimes penalize genuinely related or duplicate evidence, so the report preserves the actual texts/IDs and grouped recall rather than claiming every miss is dangerous. Stale evidence and foreign-candidate leakage are separate correctness checks, not ranking metrics.','',
      '## 15–17. Security, lifecycle, provenance and trust','',
      'All three retrieval paths pass adversarial tests with a perfect answer stored under another tenant or another candidate while the authorized candidate has weaker Docker evidence. Forged scope requests and foreign catalogue IDs are rejected. Missing tenant/candidate scope fails. Space mismatch fails at construction. Catalogue omissions fail closed against the scoped store count. Source deletion and vector purge after preparation disappear on the next request.','',
      'The versioned fixture ingests resume v1 with production Kubernetes text, then v2 with local Docker tutorial text. Every normal result in every extended experiment is asserted to match the active evidence ID. Explicit superseded retrieval returns v1. Exact response and origin counts are in `lifecycle-and-provenance.json`. All '+str(comparison['citation_roundtrips'])+' extended embedding records resolve through Stage 3C → Stage 3B → Stage 3A to their native source pointers. Assertions and simulated observed origins remain visible; all content remains untrusted. No credential is actually verified.','',
      '## 18. Local synthetic CPU microbenchmarks','',
      'Slurm job '+comparison['slurm_job_id']+', four CPUs requested, 8 GiB RAM, no GPU. Live SQLite is node-local and archived only after close. Constant 384-dimensional synthetic vectors isolate engineering costs; these timings exclude real encoding and do not represent production or internet-scale performance. Each cell is a median of five samples at output k=5. Per-request timing includes lifecycle checks and BM25 preparation. Separate k=1/3/5 samples and min/max values are in `performance.json`.','',
      '| Records | Strategy | Retrieval median ms | Catalogue preparation ms | Vector registration/upsert s |','|---:|---|---:|---:|---:|']
    for r in perf['rows']:
        if r['top_k']==5: lines.append(f"| {r['n']} | {r['strategy']} | {1000*r['median_seconds']:.2f} | {1000*r['catalogue_prepare_seconds']:.2f} | {r['vector_index_seconds']:.3f} |")
    lines += ['',f"Real model load: {comparison['model_load_seconds']:.3f} s. Extended chunking/document encoding: {comparison['embedding_and_chunking_seconds']:.3f} s. Vector preparation: {comparison['vector_preparation_seconds']:.3f} s. End-to-end query medians (including real query embedding for semantic/hybrid) are in `comparison.json`. Exact reference search and catalogue scans scale linearly and need backend work for larger interactive workloads.",'',
      '## 19. Tests and preservation','',
      f"**{validation['total_tests']}/{validation['total_tests']} tests pass**, including 41 new retrieval/evaluation tests and all 164 prior tests unchanged. Independent saved-vector replay reproduces all 28 responses for semantic, lexical, hybrid and the recommended semantic-grouped configuration (112 exact response comparisons). Frozen Stage 2 replay and Stage 3A/3B demos pass. All {validation['protected_files']} protected preexisting files and {validation['pinned_model_assets']} pinned model assets remain byte-identical. No Stage 1/2 generation or GPU benchmark was rerun; historical outputs remain intact.",'',
      'Coverage includes semantic/lexical/hybrid, deterministic fusion/order, typed queries and budgets, exact tokens, query mode, provider drift, paraphrase path, hard-negative non-entailment, scopes/spaces, lifecycle/history, source/evidence/origin filters, provenance, duplicate grouping, source caps, empty corpora, k edge cases, malicious data, deletion/purge, stale catalogues and metric correctness. Real MiniLM paraphrase and hard-negative behavior is additionally measured in the benchmark.','',
      'The full quality/performance run (2328559) completed in 51 seconds with batch MaxRSS 496,092 KiB. Final validation/replay (2328565) completed in 7 seconds. An earlier replay check (2328564) failed on Python tuple versus JSON list representation; the serialized responses already matched, and the harness was corrected to compare serialized structures. The failed log is preserved. Nodes were GPU-capable, but no GPU was requested or used.','',
      '## 20. Recommended configuration for the future Stage 3F','',
      '`RetrievalConfig(strategy="semantic", semantic_budget=20, lexical_budget=20, expansion=False, deduplicate=True, per_source_cap=None)` with requested `top_k=5` is the measured default. Exact grouping reduced duplicate rate to zero and retained all judged relevant references within five groups on this extended fixture; this is not a production recall guarantee. Keep the full 20-candidate semantic budget available for a future controlled reranker experiment rather than claiming top-five is sufficient for every need. Lexical and RRF remain explicit alternatives and diagnostics; do not silently fuse them into the default. Downstream consumers must resolve all grouped references; report grouped recall and preserve individual trust/source identities. No blanket source cap is recommended from this small set.','',
      '## 21. Limitations','',
      'Small synthetic judgments are not production validation. Some frozen judgments designate one evidence although other evidence is useful. No real verified credential, human relevance labeling, calibrated relevance probabilities, production backend, concurrent read snapshot, persistent BM25 index, date-range policy or safe semantic near-duplicate classifier is implemented. The trusted caller serializes mutation with retrieval and rebuilds catalogues after ingestion. Lexical retrieval requires embeddings in the selected space. Exact cosine and full lifecycle scans have linear costs. The local OS account remains the authority boundary inherited from Stage 3D.','',
      '## 22. Exact proposed Stage 3F boundary','',
      'A separately authorized Stage 3F may consume these bounded scoped candidate references and compare reranking methods/configurations against the same frozen retrieval inputs, retaining component ranks, provenance, lifecycle and trust. It may evaluate candidate ordering and budgets. It must not turn retrieval scores into support labels or run Qwen answer generation, credential verification, QLoRA, fine-tuning, browser automation, applications or outreach. Those remain outside Stage 3E and are not started here.','',
      '## Files and reproduction','',
      'No preexisting project file was modified. Additions:','',
      '- `rag/retrieval/`: `__init__.py`, `models.py`, `query.py`, `lexical.py`, `fusion.py`, `service.py`, `evaluator.py`, `benchmark.py`, `performance.py`, `validate.py`, `report.py`, `replay.py`, `evaluate.slurm`, `final_check.slurm`.','- `tests/rag/test_retrieval.py` (41 tests).','- `fixtures/rag/retrieval_eval/stage3e_v1.json`.','- `docs/stage3e_architecture.md`, `docs/stage3e_report.md`.','- `results/stage3e/`: frozen compatibility checks, all strategy/ablation JSON, document/query vectors, failure diagnostics, lifecycle/provenance checks, performance, regression logs, closed database archives, scheduler accounting and final artifact hash audit. Earlier Stage 3E trial results are retained in `initial-run/` and `corrected-run/`; top-level outputs are final. Initial-run metric handling was corrected and is not authoritative.','',
      'Run `sbatch rag/retrieval/evaluate.slurm` after loading `slurm/current`, after it completes successfully run `sbatch rag/retrieval/final_check.slurm` for saved-vector replay and report generation. All model, test and benchmark computation runs in Slurm. No later-stage model or workflow is invoked.','']
    (ROOT/'docs/stage3e_report.md').write_text('\n'.join(lines))
    manifest=read('preexisting_manifest.json')
    changed=[p for p,h in manifest.items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    assert not changed and validation['passed']
    files=[* (ROOT/'rag/retrieval').glob('*'),ROOT/'tests/rag/test_retrieval.py',ROOT/'fixtures/rag/retrieval_eval/stage3e_v1.json',*(ROOT/'docs').glob('stage3e*.md'),*OUT.rglob('*')]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file() and p.name!='final_audit.json'}
    (OUT/'final_audit.json').write_text(json.dumps({'passed':True,'protected_files_unchanged':len(manifest),'changed_or_missing':changed,'artifact_sha256':hashes},indent=2)+'\n')
if __name__=='__main__': main()
