# Stage 3E completion report — candidate-scoped evidence retrieval

**Stage 3E complete. Stage 3F has not begun.** Project: `~/scratch/resume-ai` on WPI Turing.

The measured recommendation is semantic candidate generation with MiniLM-L6-v2 + title/section context. Equal-weight RRF is implemented and evaluated but does not beat the semantic baseline. Retrieval scores and exact terms never become support or verification labels.

## 1–9. Architecture, query model, ranking, filtering and diversity

The additive provider-independent `EvidenceRetriever` protocol returns immutable `RetrievalResponse` / `RetrievalResult` objects, not raw storage rows. Results include rank, score, strategy, query identity, both scope IDs, exact embedding/chunk/revision/evidence/source/version pointers, native locator and offsets, source type, origin/trust, support and claim relationships, provenance event IDs, semantic space, lifecycle and component diagnostics. Large source text stays in the canonical ledger. See [architecture](stage3e_architecture.md) for the full contract.

`InformationNeed` covers job requirement, skill, experience, project, credential, accomplishment, technology, domain knowledge and question. One focused requirement and its ID form a request; whole-JD parsing is not implemented. `focused-v1` preserves wording with whitespace normalization. Optional inspectable expansion adds a few fixed aliases/container concepts. Need type participates in identity but does not apply unvalidated ranking boosts.

Semantic search invokes the Stage 3C query encoder and Stage 3D exact cosine search in one compatible space. BM25 uses technical tokens, k1=1.2 and b=0.75; C++/C#/QLoRA remain distinct. Lexical retrieval searches only records admitted by the same bound vector store. Hybrid uses equal-weight RRF with constant 60, never raw-score addition. Default branch budgets are 20; normal output is 5, API maximum 100. Default strategy is semantic with exact duplicate grouping, selected from the measured comparison.

Scope is mandatory at construction and request time. Default lifecycle is active. Source/evidence identity and type, origin, trust, chunk policy and verification-resolution marker are filterable. Historical evidence requires an explicit lifecycle filter. Date-range filtering is deferred because source time and ingestion time have different semantics. Assertions remain eligible. `resolve_supports` never means verified.

Optional exact grouping normalizes whitespace only and retains independent full references for grouped sources. No semantic near-duplicate merging is performed: similar wording can conceal different actions or qualifications. Optional per-source caps follow grouping. Both mechanisms are evaluated, not treated as universally beneficial.

## 10–13. Controlled quality comparison

The compatible set reuses 22 frozen Stage 3C needs, 44 chunks, query vectors and document vectors. All semantic scores and evidence rankings using the old tie policy reproduce exactly. The runtime breaks score ties by embedding ID; the original evaluation breaks evidence ties by fixture ID. The headline semantic metrics agree. All three strategies use the same corpus/needs; compatible branch budgets are 100 to expose the full ranking.

The extended synthetic set has 28 needs and 67 chunks, including multiple source categories, synthetic candidate/observed origins, identical evidence, a crowded source, stale/current resume versions, irrelevant text, and malicious instructions. Original singleton judgments are retained; equivalent unjudged siblings can make some misses benign. New exact-term needs have explicitly multiple relevant items. No fixture label creates an actual verified credential.

| Set / strategy | Recall@1 | Recall@3 | Recall@5 | MRR | nDCG@5 | Hard-negative wins | Dangerous top-1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| compatible-semantic | 0.6818 | 0.9091 | 1.0000 | 0.8030 | 0.8525 | 0.8636 | 0.0909 |
| compatible-lexical | 0.3636 | 0.7273 | 0.7273 | 0.5227 | 0.5752 | 0.5000 | 0.0909 |
| compatible-hybrid | 0.4091 | 0.8636 | 0.9545 | 0.6288 | 0.7053 | 0.8182 | 0.1364 |
| extended-semantic | 0.6607 | 0.8622 | 0.9439 | 0.7842 | 0.8239 | 0.8571 | 0.0714 |
| extended-lexical | 0.4158 | 0.6837 | 0.7296 | 0.5786 | 0.6081 | 0.5714 | 0.0714 |
| extended-hybrid | 0.4464 | 0.7551 | 0.9439 | 0.6560 | 0.7250 | 0.8929 | 0.1071 |

Recall is macro-average evidence recall at chunk-result positions, counting each evidence only once. MRR is first judged relevant position within the budget. nDCG uses binary relevance and counts repeated chunks of the same evidence once. Hard-negative win requires a strictly higher retrieval score; ties do not win, and absent positives lose. For bounded branches this is candidate-ranking behavior, not exhaustive semantic separation. Dangerous-neighbor labels come from explicit fixture judgments, not runtime inference.

| Extended configuration | R@5 | Grouped R@5 | MRR | Duplicate rate@5 | Unique sources@5 | Dangerous queries@3 | Grouped dangerous queries@3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| semantic | 0.9439 | 0.9439 | 0.7842 | 0.1214 | 5.0000 | 0.5714 | 0.5714 |
| lexical | 0.7296 | 0.7296 | 0.5786 | 0.0946 | 3.7143 | 0.2500 | 0.2500 |
| hybrid | 0.9439 | 0.9439 | 0.6560 | 0.1214 | 5.0000 | 0.3929 | 0.3929 |
| semantic-dedup | 0.9388 | 1.0000 | 0.7887 | 0.0000 | 4.9286 | 0.5714 | 0.6429 |
| semantic-diverse | 0.9388 | 1.0000 | 0.7887 | 0.0000 | 4.9643 | 0.5714 | 0.6429 |
| hybrid-expanded | 0.9796 | 0.9796 | 0.7018 | 0.1286 | 5.0000 | 0.3929 | 0.3929 |
| hybrid-dedup | 0.9388 | 1.0000 | 0.6583 | 0.0000 | 4.9286 | 0.4643 | 0.5357 |
| hybrid-diverse | 0.9388 | 1.0000 | 0.6583 | 0.0000 | 5.0000 | 0.4643 | 0.5357 |
| hybrid-budget-5 | 0.9439 | 0.9439 | 0.7065 | 0.0857 | 5.0000 | 0.3571 | 0.3571 |
| hybrid-budget-10 | 0.9439 | 0.9439 | 0.6815 | 0.1214 | 5.0000 | 0.3929 | 0.3929 |
| hybrid-budget-40 | 0.9082 | 0.9082 | 0.6548 | 0.1214 | 5.0000 | 0.3929 | 0.3929 |

Grouped recall credits a relevant evidence reference retained under a representative. Representative-only recall does not. Standard rank, hard-negative and danger metrics describe representatives; grouped danger separately counts retained hard-negative source references so grouping cannot hide them. A grouped source never inherits trust or support status from the representative. Grouping can expose more dangerous neighbors after removing repeats, and source caps can discard useful chunks. Source diversity counts source IDs, not independent corroboration. Budget probes 5/10/20/40 change candidate fusion; they are not fitted to individual answers. Expansion remains opt-in despite gains on this small synthetic set.

## 14. Important failures and non-regressions

Every need has machine-readable top-five results, expected evidence, semantic score/rank, lexical score/rank, hybrid score/rank and provenance in `results/stage3e/failure_analysis.json`. Missing branch candidates have null diagnostics. Full bounded rankings and query plans remain in each experiment JSON.

| Need | Semantic top 3 | Lexical top 3 | Hybrid top 3 | Interpretation |
|---|---|---|---|---|
| python_api | python_api_negative, fastapi_negative, python_api_positive | python_api_negative, kube_interest, python_api_positive | python_api_negative, python_api_positive, cpp_negative | Wrong action: consuming an API does not establish implementing one. |
| docker | docker_positive, docker_negative, kubernetes_negative | python_api_positive, cpp_negative, cpp | cpp, cpp_negative, docker_positive | Adjacent technology: Kubernetes is not Docker packaging evidence. |
| rag | built_negative, rag_positive, rag_negative | kube_interest, built_positive, built_negative | built_negative, built_positive, kube_interest | Adjacent task: fine-tuning does not establish retrieval-augmented generation. |
| aws | aws_positive, aws_negative, injection_negative | designed_negative, metadata_verification_positive, metadata_verification_negative | metadata_verification_positive, injection_negative, metadata_verification_negative | Adjacent cloud: Azure does not establish AWS experience; aliases may be missed by lexical retrieval. |
| fastapi | fastapi_positive, python_api_positive, observed_negative | python_api_positive, fastapi_positive, rag_positive | python_api_positive, fastapi_positive, metadata_origin_positive | Adjacent framework: Flask and FastAPI are not interchangeable. |
| pytorch | pytorch_positive, pytorch_negative, inference_negative | deep_learning_positive, pytorch_positive, pytorch_negative | pytorch_positive, deep_learning_positive, pytorch_negative | Adjacent framework: TensorFlow does not establish PyTorch experience. |
| qlora | lora_negative, qlora_positive, lora_positive | qlora_positive, lora_negative, rag_negative | lora_negative, qlora_positive, qlora_negative | Quantization distinction: LoRA alone does not establish QLoRA. |
| postgres | postgres_positive, postgres_negative, designed_positive | postgres_positive, duplicate_3, duplicate_4 | postgres_positive, duplicate_3, duplicate_4 | Inspect exact action and evidence scope; semantic similarity is candidate discovery only. |
| deep_learning | deep_learning_positive, pytorch_negative, pytorch_positive | kube_interest | kube_interest, deep_learning_positive, pytorch_negative | Inspect exact action and evidence scope; semantic similarity is candidate discovery only. |
| inference | inference_positive, inference_negative, docker_positive | deep_learning_negative, designed_negative, cpp_negative | cpp_negative, deep_learning_negative, cpp | Wrong lifecycle: training does not establish deployed inference. |
| built | built_positive, built_negative, rag_positive | built_positive, built_negative, rag_positive | built_positive, built_negative, rag_positive | Wrong action: using a library does not establish building it. |
| deployed | deployed_positive, deployed_negative, aws_positive | deployed_negative, deployed_positive, designed_negative | deployed_negative, deployed_positive, designed_negative | Wrong action: use or implementation alone does not establish deployment. |
| designed | designed_positive, designed_negative, docker_negative | designed_positive, designed_negative, injection_negative | designed_positive, designed_negative, rag_positive | Inspect exact action and evidence scope; semantic similarity is candidate discovery only. |
| observed | observed_positive, observed_negative, metadata_origin_positive | observed_positive | observed_positive, observed_negative, metadata_origin_positive | Text about observation is not authenticated external collection or verification. |
| certificate | certificate_positive, injection_positive, certificate_negative | injection_positive, certificate_positive, deployed_negative | injection_positive, certificate_positive, certificate_negative | Mentioning a credential is not issuer verification. |
| kubernetes | duplicate_3, duplicate_4, duplicate_1 | designed_negative, duplicate_3, duplicate_4 | duplicate_3, duplicate_4, duplicate_1 | Duplicate crowding plus experience-level distinction: tutorial familiarity is not production deployment. |
| latency | latency_positive, latency_negative, lora_negative | latency_positive | latency_positive, latency_negative, lora_negative | Unquantified improvement does not establish a 40 percent latency reduction. |
| lora | lora_positive, qlora_negative, qlora_positive | lora_positive, qlora_negative, inference_negative | lora_positive, qlora_negative, inference_negative | Quantization distinction: QLoRA and full-precision LoRA differ. |
| training | inference_positive, inference_negative, deep_learning_negative | kube_interest, deep_learning_negative, inference_negative | deep_learning_negative, inference_negative, kube_interest | Wrong lifecycle: inference does not establish weight training. |
| injection | metadata_verification_positive, metadata_verification_negative, injection_positive | metadata_verification_positive, metadata_verification_negative, injection_positive | metadata_verification_positive, metadata_verification_negative, injection_positive | Prompt-like text is untrusted data even when it contains the exact certification term. |
| metadata_origin | metadata_origin_positive, metadata_origin_negative, current_v2 | observed_positive, current_v2, metadata_origin_positive | metadata_origin_positive, observed_positive, current_v2 | Identical text cannot distinguish trust. Frozen labels are evaluation-only; origin must be resolved from metadata. |
| metadata_verification | certificate_positive, certificate_negative, metadata_verification_positive | metadata_verification_positive, certificate_negative, metadata_verification_negative | metadata_verification_positive, certificate_negative, certificate_positive | Identical credential text cannot establish verification. No actual verified credential is created. |
| exact_cpp | cpp, cpp_negative, lora_negative | cpp | cpp, cpp_negative, lora_negative | Technical punctuation must retain C++ distinctly from C. |
| exact_qlora | lora_negative, qlora_positive, python_api_positive | lora_negative, qlora_positive | lora_negative, qlora_positive, python_api_positive | Exact tokens preserve QLoRA versus LoRA; still no entailment decision. |
| exact_kube | kubernetes_negative, kube_interest, docker_negative | docker_negative, kubernetes_negative, kube_interest | kubernetes_negative, docker_negative, kube_interest | Exact occurrence can retrieve learning-only text. It does not establish experience; multiple genuine matching sources are relevant. |
| paraphrase | rag_positive, built_negative, built_positive | rag_positive | rag_positive, built_negative, built_positive | Benign lexical mismatch can miss a concept expressed without shared words. |
| current_version | current_v2, metadata_origin_positive, metadata_origin_negative | current_v2, kubernetes_negative, built_negative | current_v2, metadata_origin_positive, kubernetes_negative | Superseded perfect-match text must remain excluded; only current evidence competes. |
| container_expansion | kubernetes_negative, duplicate_3, duplicate_4 | python_api_positive, aws_positive | python_api_positive, kubernetes_negative, duplicate_3 | Container concepts can aid discovery, but Docker/Kubernetes are not equivalent experience. |

Adjacent-tech, action-level and trust mistakes remain visible; semantic similarity is not entailment. Lexical outperformance is visible on QLoRA and the exact Kubernetes need, while Docker paraphrases/deep learning/inference demonstrate lexical failures. Singleton judgments sometimes penalize genuinely related or duplicate evidence, so the report preserves the actual texts/IDs and grouped recall rather than claiming every miss is dangerous. Stale evidence and foreign-candidate leakage are separate correctness checks, not ranking metrics.

## 15–17. Security, lifecycle, provenance and trust

All three retrieval paths pass adversarial tests with a perfect answer stored under another tenant or another candidate while the authorized candidate has weaker Docker evidence. Forged scope requests and foreign catalogue IDs are rejected. Missing tenant/candidate scope fails. Space mismatch fails at construction. Catalogue omissions fail closed against the scoped store count. Source deletion and vector purge after preparation disappear on the next request.

The versioned fixture ingests resume v1 with production Kubernetes text, then v2 with local Docker tutorial text. Every normal result in every extended experiment is asserted to match the active evidence ID. Explicit superseded retrieval returns v1. Exact response and origin counts are in `lifecycle-and-provenance.json`. All 67 extended embedding records resolve through Stage 3C → Stage 3B → Stage 3A to their native source pointers. Assertions and simulated observed origins remain visible; all content remains untrusted. No credential is actually verified.

## 18. Local synthetic CPU microbenchmarks

Slurm job 2328559, four CPUs requested, 8 GiB RAM, no GPU. Live SQLite is node-local and archived only after close. Constant 384-dimensional synthetic vectors isolate engineering costs; these timings exclude real encoding and do not represent production or internet-scale performance. Each cell is a median of five samples at output k=5. Per-request timing includes lifecycle checks and BM25 preparation. Separate k=1/3/5 samples and min/max values are in `performance.json`.

| Records | Strategy | Retrieval median ms | Catalogue preparation ms | Vector registration/upsert s |
|---:|---|---:|---:|---:|
| 100 | semantic | 43.78 | 22.40 | 0.062 |
| 100 | lexical | 13.32 | 22.06 | 0.062 |
| 100 | hybrid | 44.66 | 21.96 | 0.062 |
| 1000 | semantic | 431.26 | 253.99 | 0.728 |
| 1000 | lexical | 134.01 | 254.06 | 0.728 |
| 1000 | hybrid | 443.87 | 253.42 | 0.728 |

Real model load: 3.875 s. Extended chunking/document encoding: 0.317 s. Vector preparation: 0.044 s. End-to-end query medians (including real query embedding for semantic/hybrid) are in `comparison.json`. Exact reference search and catalogue scans scale linearly and need backend work for larger interactive workloads.

## 19. Tests and preservation

**205/205 tests pass**, including 41 new retrieval/evaluation tests and all 164 prior tests unchanged. Independent saved-vector replay reproduces all 28 responses for semantic, lexical, hybrid and the recommended semantic-grouped configuration (112 exact response comparisons). Frozen Stage 2 replay and Stage 3A/3B demos pass. All 362 protected preexisting files and 22 pinned model assets remain byte-identical. No Stage 1/2 generation or GPU benchmark was rerun; historical outputs remain intact.

Coverage includes semantic/lexical/hybrid, deterministic fusion/order, typed queries and budgets, exact tokens, query mode, provider drift, paraphrase path, hard-negative non-entailment, scopes/spaces, lifecycle/history, source/evidence/origin filters, provenance, duplicate grouping, source caps, empty corpora, k edge cases, malicious data, deletion/purge, stale catalogues and metric correctness. Real MiniLM paraphrase and hard-negative behavior is additionally measured in the benchmark.

The full quality/performance run (2328559) completed in 51 seconds with batch MaxRSS 496,092 KiB. Final validation/replay (2328565) completed in 7 seconds. An earlier replay check (2328564) failed on Python tuple versus JSON list representation; the serialized responses already matched, and the harness was corrected to compare serialized structures. The failed log is preserved. Nodes were GPU-capable, but no GPU was requested or used.

## 20. Recommended configuration for the future Stage 3F

`RetrievalConfig(strategy="semantic", semantic_budget=20, lexical_budget=20, expansion=False, deduplicate=True, per_source_cap=None)` with requested `top_k=5` is the measured default. Exact grouping reduced duplicate rate to zero and retained all judged relevant references within five groups on this extended fixture; this is not a production recall guarantee. Keep the full 20-candidate semantic budget available for a future controlled reranker experiment rather than claiming top-five is sufficient for every need. Lexical and RRF remain explicit alternatives and diagnostics; do not silently fuse them into the default. Downstream consumers must resolve all grouped references; report grouped recall and preserve individual trust/source identities. No blanket source cap is recommended from this small set.

## 21. Limitations

Small synthetic judgments are not production validation. Some frozen judgments designate one evidence although other evidence is useful. No real verified credential, human relevance labeling, calibrated relevance probabilities, production backend, concurrent read snapshot, persistent BM25 index, date-range policy or safe semantic near-duplicate classifier is implemented. The trusted caller serializes mutation with retrieval and rebuilds catalogues after ingestion. Lexical retrieval requires embeddings in the selected space. Exact cosine and full lifecycle scans have linear costs. The local OS account remains the authority boundary inherited from Stage 3D.

## 22. Exact proposed Stage 3F boundary

A separately authorized Stage 3F may consume these bounded scoped candidate references and compare reranking methods/configurations against the same frozen retrieval inputs, retaining component ranks, provenance, lifecycle and trust. It may evaluate candidate ordering and budgets. It must not turn retrieval scores into support labels or run Qwen answer generation, credential verification, QLoRA, fine-tuning, browser automation, applications or outreach. Those remain outside Stage 3E and are not started here.

## Files and reproduction

No preexisting project file was modified. Additions:

- `rag/retrieval/`: `__init__.py`, `models.py`, `query.py`, `lexical.py`, `fusion.py`, `service.py`, `evaluator.py`, `benchmark.py`, `performance.py`, `validate.py`, `report.py`, `replay.py`, `evaluate.slurm`, `final_check.slurm`.
- `tests/rag/test_retrieval.py` (41 tests).
- `fixtures/rag/retrieval_eval/stage3e_v1.json`.
- `docs/stage3e_architecture.md`, `docs/stage3e_report.md`.
- `results/stage3e/`: frozen compatibility checks, all strategy/ablation JSON, document/query vectors, failure diagnostics, lifecycle/provenance checks, performance, regression logs, closed database archives, scheduler accounting and final artifact hash audit. Earlier Stage 3E trial results are retained in `initial-run/` and `corrected-run/`; top-level outputs are final. Initial-run metric handling was corrected and is not authoritative.

Run `sbatch rag/retrieval/evaluate.slurm` after loading `slurm/current`, after it completes successfully run `sbatch rag/retrieval/final_check.slurm` for saved-vector replay and report generation. All model, test and benchmark computation runs in Slurm. No later-stage model or workflow is invoked.
