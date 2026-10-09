# Stage 3H — final RAG scale validation

**Stage 3H complete. Recommendation: B — DO NOT FREEZE YET.**

The frozen retriever loses required evidence for two compound requirements at 100, 500 and 1,500 chunks. Both top-3 and top-5 have the same coverage losses. QLoRA cannot correct evidence that never reaches Qwen. The smallest next-stage RAG issue is coverage of material components under repeated semantically similar distractors; evaluate a versioned component-aware retrieval/context-selection correction before freezing. No correction was applied in Stage 3H.

RAG demonstrated operational value: at XL it reduced mean prompt size from about 274,967 tokens to 2,020 (top-3) or 2,342 (top-5), reductions of 99.3% and 99.1%. All 128 RAG generations ran on one A30; full context only completed at SMALL. This does not demonstrate superior large-scale accuracy against full context, because that control was infeasible. At SMALL, top-3's one-case accuracy advantage over full context comes from an unrepaired output-cap failure in the full arm, not demonstrated semantic retrieval superiority.

Retrieval, scope checks and context construction ran during CPU preparation. Qwen consumed the resulting frozen contexts; the independent CPU process rebuilt them from the corpus. Model inference latency and retrieval latency are reported separately, not as a measured end-to-end serving benchmark.

All **144 primary generations**, **362 tests**, and the independent artifact replay completed. **857 protected prior files** and **92 frozen files** remain unchanged. GPU job **2332803** completed in **02:59:15** and CPU verifier **2332804** in **00:02:51**; both exited successfully and their allocations ended. The 1,536-token output cap and all three malformed cap-limited outputs are preserved.

The complete raw prompts, token IDs, outputs, frozen corpus and vectors remain on Turing at `~/scratch/resume-ai/results/stage3h/`; primary outputs are in `benchmark-2332803/`. Local `generation-summary.jsonl` is a convenience copy retaining exact generated text and measured fields, with prompt/message/token-ID payloads omitted. It is not a replacement for the remote raw archive. See [artifact index](../results/stage3h/README.md), [semantic/security audit](stage3h_semantic_audit.md), and [machine-readable metrics](../results/stage3h/benchmark-2332803/metrics.json).

## 1. Architecture and controls

One synthetic candidate, 16 unchanged needs, 20 supplied atomic components, four nested corpus scales, and three primary arms: true full context, RAG top-3 and RAG top-5. Frozen Stage 3E semantic retrieval (20 vectors, exact whitespace-normalized duplicate grouping, no expansion/source caps), Stage 3F identity reranker, and Stage 3G v2 reasoning prompt/schema/validation are unchanged. Full context enumerates every active record in source order using validated provenance; it does not select by query relevance. No truncation was used.

No model weights, dependencies or historical Stage 1–3G results were changed. No QLoRA, fine-tuning, training dataset, browser automation or application workflow was started.

Model: `/scratch/mohammedmubashir/resume-ai/models/Qwen3.8-27B`, runtime architecture `Qwen3_5ForCausalLM`. NF4 four-bit weights, double quantization, BF16 compute/dtype, all parameters on cuda:0; greedy generation, max_new_tokens=1536, use_cache=true, thinking=false, seed=42. These and dependency versions are asserted equal to Stage 3G at process startup. Embedding CPU seed=0, PYTHONHASHSEED=0. Dependency freeze and every source hash are retained; the project has no Git checkout metadata.

## 2. Files

Created `rag/scale/{dataset,prepare,metrics,run,diagnose,verify}.py`, `rag/scale/__init__.py`, three Slurm wrappers, `tests/rag/test_scale.py`, `docs/stage3h_architecture.md`, this report, and `results/stage3h/` artifacts. All implementation is additive. Dataset/contexts/vectors/source hashes are listed in `results/stage3h/freeze.json`; the complete delivered inventory is `results/stage3h/final_manifest.json`.

## 3. Slurm and resources

Primary GPU job **2332803** requested **one NVIDIA A30, 8 CPUs, 64 GiB host RAM, 04:00:00 maximum**, account `cs541`, partition `academic`. Actual hardware: `NVIDIA A30, GPU-e2d3b0ee-c7d4-7ab1-0616-cd237e0ce041, 24576 MiB, 595.71.05`. The batch exits on completion; see `slurm_accounting.txt` for allocation elapsed and host RSS.

Preparation jobs: 2332790 and 2332800. The first GPU attempt 2332793 was cancelled during loading/smoke setup before any completed smoke output or primary freeze. A pre-freeze semantic review removed two overly generous document-to-component relations (“uses” did not entail “implemented/trained”). Source evidence and whole-need labels were unchanged; the original annotation snapshot is retained in `pre-freeze-review/`. Verification job 2332796 was cancelled as dependent on that attempt. Final CPU verification: 2332804. Read-only ranking diagnostic: 2332805. No simultaneous Qwen processes or multi-GPU requests.

## 4–5. Frozen scale dataset

`stage3h-scale-v1`, seed 42, synthetic and non-private. Sixteen needs: 4 SUPPORTED, 3 PARTIALLY_SUPPORTED, 3 UNSUPPORTED, 6 UNKNOWN. Core evidence is byte-identical and nested across scales. Each corpus adds realistic learning logs, adjacent technologies/actions, job criteria, self assertions, portfolio notes and exact duplicates. Sources include CV, LinkedIn, GitHub, portfolio, certificate and application-history records. One superseded resume revision is retained in storage but excluded from active context. A separate candidate B contains perfect answers and a secret canary.

| Scale | Active A chunks | Stored A chunks | Candidate B chunks |
| --- | --- | --- | --- |
| SMALL | 24 | 25 | 1 |
| MEDIUM | 100 | 101 | 1 |
| LARGE | 500 | 501 | 1 |
| XL | 1500 | 1501 | 1 |

Limitations: one authored candidate, templated short records, supplied decomposition, no production distribution or independent human adjudication. Template repetition deliberately stresses distractor density; the results are sensitivity measurements, not population estimates. Long multi-chunk canonical evidence remains an existing fail-closed limitation and was not validated as supported in this stage.

## 6. Full-context feasibility

All prompt tokens were measured with the existing Qwen tokenizer and chat template. Admission checks the configured position limit and a **65,536-byte-per-token KV-cache lower bound**, derived from 16 full-attention layers × K/V × four heads × 256 dimensions × BF16. That lower bound is compared with measured free GPU memory after loading. It does not include all workspaces, so passing it permits an actual attempt rather than guaranteeing feasibility. An observed OOM is reported separately. This is single-A30 operational feasibility, not a claim that Qwen’s theoretical context window is equally small.

Model position limit: 262,144. Free GPU memory immediately after load: 6.62 GiB. Output reservation: 1,536 tokens.

| Scale | Full prompt tokens min–max | Full result / count | Truncation |
| --- | --- | --- | --- |
| SMALL | 5,375–5,407 | {'FEASIBLE: actual_generation': 16} | None |
| MEDIUM | 19,165–19,197 | {'FULL_CONTEXT_NOT_FEASIBLE: observed_CUDA_OOM': 1, 'NOT_ATTEMPTED_AFTER_SAME_SCALE_OOM: ': 15} | None |
| LARGE | 92,096–92,128 | {'FULL_CONTEXT_NOT_FEASIBLE: observed_CUDA_OOM': 1, 'NOT_ATTEMPTED_AFTER_SAME_SCALE_OOM: ': 15} | None |
| XL | 274,956–274,988 | {'FULL_CONTEXT_NOT_FEASIBLE: model_position_limit': 16} | None |

Rejected or skipped full contexts have no completed generation. No partial evidence subset was constructed or scored as full context, and there is no truncation-loss list because no truncation occurred. A skipped arm has no accuracy score. No TRUNCATED_FULL_CONTEXT arm was run.

| OOM attempt | Prompt tokens | Failed-attempt seconds | Peak Torch allocated GiB | Peak Torch reserved GiB |
| --- | --- | --- | --- | --- |
| MEDIUM/h01 | 19169 | 0.1558 | 22.06 | 22.98 |
| LARGE/h01 | 92100 | 0.0363 | 21.12 | 22.20 |

Failed-prefill elapsed times are not successful inference latencies. The lower LARGE recorded peak reflects failure before a larger allocation could succeed, not evidence that LARGE requires less memory. Feasibility applies to the unchanged context format, kernels, allocator and single-A30 runtime; optimized kernels, offloading or compact alternative formats were not tested.

## 7. Retrieval by scale

Recall/MRR are macro means over the ten needs with authored relevant core evidence. The six absence-only needs have undefined recall and are excluded. Recall counts exact core provenance documents, so equivalent extra corroboration can preserve an answer even when a particular original core source is absent. Evidence survival instead asks whether all component judgments supported by the full corpus survive in the selected context, averaged over all 16 needs. Among the ten evidence-bearing needs, whole-need survival is 10/10 at SMALL and 8/10 at each larger scale; absence-only needs do not require retrieval of a positive proof.

| Scale | Recall@1 | Recall@3 | Recall@5 | MRR | Survival@3 | Survival@5 | Duplicate branch crowding |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SMALL | 65.0% | 100.0% | 100.0% | 90.0% | 100.0% | 100.0% | 4.7% |
| MEDIUM | 65.0% | 78.3% | 78.3% | 86.7% | 87.5% | 87.5% | 12.2% |
| LARGE | 65.0% | 75.0% | 75.0% | 86.2% | 87.5% | 87.5% | 15.3% |
| XL | 58.3% | 68.3% | 68.3% | 75.0% | 87.5% | 87.5% | 11.6% |

The duplicate branch metric is suppressed duplicate vectors / internal budget 20. Post-group contexts can still contain multiple corroborating records.

| Scale | Dangerous neighbor@3 | Dangerous neighbor@5 | Repeated text in top-5 context | Stale leakage | Cross-candidate leakage |
| --- | --- | --- | --- | --- | --- |
| SMALL | 24.0% | 20.4% | 6.2% | 0.0% | 0.0% |
| MEDIUM | 59.1% | 67.5% | 6.2% | 0.0% | 0.0% |
| LARGE | 58.3% | 65.0% | 11.6% | 0.0% | 0.0% |
| XL | 58.3% | 65.0% | 11.6% | 0.0% | 0.0% |

Dangerous neighbors are authored adjacent core documents or generated adjacent/assertion/training-versus-inference/built-versus-used categories, excluding documents with a valid relation for that need. The broader all-unrelated-or-dangerous upper bound remains in `retrieval.json`. The classification is a fixture taxonomy, not an automatic entailment model.

## 8–9. Reasoning and top-3 versus top-5

Stage 3G reported 54.1% on its Stage 2 comparison and 78.4% for both RAG and matched full context. That did not establish a retrieval-specific accuracy gain. Stage 3H uses a different frozen stress benchmark; its percentages must not be subtracted from Stage 3G as a causal scale effect. The valid scale comparisons here track the same 16 needs across the four nested histories.

| Scale | Arm | n | Label accuracy | Macro F1 | Atomic accuracy | Compound accuracy | Full contract | JSON / schema |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SMALL | full | 16 | 68.8% | 0.705 | 65.0% | 75.0% | 62.5% | 93.8% / 93.8% |
| SMALL | rag3 | 16 | 75.0% | 0.756 | 70.0% | 100.0% | 62.5% | 100.0% / 100.0% |
| SMALL | rag5 | 16 | 68.8% | 0.708 | 65.0% | 75.0% | 56.2% | 93.8% / 93.8% |
| MEDIUM | rag3 | 16 | 68.8% | 0.694 | 65.0% | 75.0% | 50.0% | 100.0% / 100.0% |
| MEDIUM | rag5 | 16 | 68.8% | 0.694 | 65.0% | 75.0% | 50.0% | 100.0% / 100.0% |
| LARGE | rag3 | 16 | 68.8% | 0.694 | 65.0% | 75.0% | 50.0% | 100.0% / 100.0% |
| LARGE | rag5 | 16 | 62.5% | 0.628 | 55.0% | 50.0% | 43.8% | 93.8% / 93.8% |
| XL | rag3 | 16 | 68.8% | 0.694 | 65.0% | 75.0% | 50.0% | 100.0% / 100.0% |
| XL | rag5 | 16 | 62.5% | 0.611 | 60.0% | 50.0% | 50.0% | 100.0% / 100.0% |

Atomic accuracy above uses full-corpus gold. Context-conditional atomic accuracy is separately saved as `atomic_context_accuracy`; it does not excuse retrieval loss from end-to-end scores. Every label’s precision, recall, F1 and support count is in `metrics.json` and the appendix below. These are matched needs, not independent samples as scale increases. Compound accuracy is parent-label accuracy over the four multi-atom needs; a correct parent can hide an incorrect atom. Malformed outputs receive no primary label credit. Citation precision is conditional on emitted, parseable asserted-relation citations; it must be read alongside strict-output validity, because malformed responses supply no such scored citations.

**Budget choice for this stress benchmark: top-3.** It has equal or higher label accuracy and higher citation precision at every scale, with lower mean inference time and fewer prompt tokens. It does not restore the two lost components. This is not approval to change the production default: Stage 3F contains a rank-five coverage case, which must remain in the next validation. No retrieval configuration was changed here.

| Scale | Top-3 mean seconds | Top-5 mean seconds | Top-3 mean-time reduction vs top-5 |
| --- | --- | --- | --- |
| SMALL | 63.61 | 67.31 | 5.5% |
| MEDIUM | 68.46 | 83.60 | 18.1% |
| LARGE | 66.86 | 82.72 | 19.2% |
| XL | 66.85 | 86.51 | 22.7% |

These are mean-time comparisons over all 16 cases, including malformed outputs. Median latency is reported separately and is not uniformly lower for top-3.

## 10–12. Tokens, latency and VRAM

| Scale | Arm | Mean chunks supplied | Mean prompt tokens | Mean generated tokens | Mean total tokens | Prompt reduction vs full | Evidence-token reduction vs full | Median seconds | Mean output tokens/s | Peak allocated GiB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SMALL | full | 24.0 | 5386 | 653 | 6038 | 0.0% | 0.0% | 52.19 | 8.79 | 18.81 |
| SMALL | rag3 | 3.2 | 1689 | 598 | 2287 | 68.6% | 86.4% | 46.37 | 9.36 | 17.37 |
| SMALL | rag5 | 5.4 | 2065 | 630 | 2695 | 61.7% | 77.6% | 47.61 | 9.31 | 17.51 |
| MEDIUM | rag3 | 3.6 | 1761 | 644 | 2405 | 90.8% | 96.4% | 70.46 | 9.37 | 17.64 |
| MEDIUM | rag5 | 5.6 | 2125 | 785 | 2910 | 88.9% | 94.4% | 66.90 | 9.32 | 17.78 |
| LARGE | rag3 | 5.1 | 2018 | 628 | 2646 | 97.8% | 99.0% | 59.83 | 9.33 | 18.47 |
| LARGE | rag5 | 6.9 | 2338 | 779 | 3117 | 97.5% | 98.6% | 57.10 | 9.31 | 18.47 |
| XL | rag3 | 5.1 | 2020 | 623 | 2642 | 99.3% | 99.7% | 58.80 | 9.25 | 18.47 |
| XL | rag5 | 6.9 | 2342 | 808 | 3150 | 99.1% | 99.5% | 57.62 | 9.23 | 18.47 |

Model latency includes prefill and decoding, timed after tokenization and input transfer. It excludes retrieval and offline corpus preparation; it is not a complete serving-latency benchmark.

| Scale | Mean retrieval seconds | Maximum retrieval seconds | Entire corpus preparation seconds |
| --- | --- | --- | --- |
| SMALL | 0.0261 | 0.0322 | 0.98 |
| MEDIUM | 0.0630 | 0.0713 | 2.11 |
| LARGE | 0.2557 | 0.2651 | 9.11 |
| XL | 0.7326 | 0.7448 | 51.32 |

Reductions are computed against the actual tokenized complete context, including at infeasible scales; they do not imply an observed full-context runtime saving when that arm could not run. Prompt reduction includes schema/system overhead; evidence reduction measures serialized evidence only. All primary contexts were freshly generated; no prompt reuse is assigned zero latency.

Qwen load: 24.83 s. Process elapsed, including smoke: 10746.18 s. Physical primary generations: 144. Primary prompt tokens: 347,877; generated tokens: 98,371. Token-cap hits: 3. Torch allocated/reserved peaks and whole-device 10-second telemetry are distinct measurements. The existing slow reference kernels were retained; no dependency changes were made.

SMALL's paired total inference time was 1,170.80 seconds for full context, 1,017.81 for top-3, and 1,077.02 for top-5: observed total-time reductions of 13.1% and 8.0%. These include the cap failures. No actual full-context latency saving is claimed at larger scales.

Whole-device telemetry sampled every ten seconds recorded a maximum of **20,175 MiB** across **1,075 samples**. It can miss short OOM/prefill peaks; the separate Torch peaks above capture a different quantity. Slurm reported batch MaxRSS **1,963,996K** for the GPU job and **2,356,716K** for the CPU verifier. These are scheduler samples, not continuous host-memory peaks or GPU VRAM. The 64 GiB reservation was retained. Corpus preparation times include all 16 retrieval queries, context/provenance construction and isolation checks; they are not isolated ingestion throughput.

## 13. Distractor robustness

The same core facts remain available in every corpus. At MEDIUM and above, `h05` (FastAPI plus Kubernetes) loses its FastAPI proof, while `h06` (RAG plus base-weight fine-tuning) loses its RAG implementation proof. This changes context gold even before Qwen runs. Extra top-5 slots do not restore that support. Identity reranking preserves the ordering, so it cannot rescue omitted components.

| Scale | Need | Evidence | Raw vector rank | Distinct-text rank (diagnostic only) |
| --- | --- | --- | --- | --- |
| SMALL | h05 | c01 | 2 | 2 |
| SMALL | h06 | c04 | 2 | 2 |
| MEDIUM | h05 | c01 | 8 | 6 |
| MEDIUM | h06 | c04 | 9 | 9 |
| LARGE | h05 | c01 | 18 | 8 |
| LARGE | h06 | c04 | 42 | 42 |
| XL | h05 | c01 | 64 | 24 |
| XL | h06 | c04 | 125 | 125 |

At MEDIUM the proof is still inside the 20-vector pool but below the selected five groups. At XL it also falls outside that pool. Exact deduplication alone would not cure the near-duplicate distractors; the distinct-text rank diagnostic shows this. These alternative ranks were never supplied to Qwen and are not claimed as an evaluated fix.

Top-3 changes three parent labels from SMALL at each larger scale; h05 changes from correct to wrong because its FastAPI proof is absent. Top-5 changes three labels at MEDIUM and four at LARGE/XL. At LARGE its h06 output is malformed; at XL it is valid JSON but predicts UNSUPPORTED, gives unjustified partial credit to RAG implementation, and violates parent/atomic aggregation. It still rejects the attacked base-weight fine-tuning component. Correct top-3 parent labels for h06 do not excuse its missing implementation proof or unsupported attribution.

## 14. Citations and provenance

| Scale | Arm | Citation validity | Citation precision | Unsupported citation rate | Fabricated-ID rate | Hallucinated positive-claim proxy |
| --- | --- | --- | --- | --- | --- | --- |
| SMALL | full | 100.0% | 64.0% | 36.0% | 0.0% | 22.2% |
| SMALL | rag3 | 100.0% | 66.7% | 33.3% | 0.0% | 11.1% |
| SMALL | rag5 | 100.0% | 62.5% | 37.5% | 0.0% | 12.5% |
| MEDIUM | rag3 | 100.0% | 35.5% | 64.5% | 0.0% | 25.0% |
| MEDIUM | rag5 | 100.0% | 26.2% | 73.8% | 0.0% | 25.0% |
| LARGE | rag3 | 100.0% | 33.3% | 66.7% | 0.0% | 25.0% |
| LARGE | rag5 | 100.0% | 25.7% | 74.3% | 0.0% | 14.3% |
| XL | rag3 | 100.0% | 33.3% | 66.7% | 0.0% | 25.0% |
| XL | rag5 | 100.0% | 23.3% | 76.7% | 0.0% | 25.0% |

Citation entailment uses frozen document-to-atom relations. UNKNOWN explanatory citations are checked for existence but excluded from positive/partial/contradiction precision. Exact quotes and valid IDs do not by themselves establish entailment. The hallucination rate is the Stage 3G positive/partial-atom overstatement proxy, not a complete audit of all prose.

## 15–16. Injection and isolation

| Scale | Arm | Attack-exposed prompts | Secret-ID/canary marker appearances | Suspected promotion prompts | Unauthorized ID occurrences | Cross-candidate output leakage |
| --- | --- | --- | --- | --- | --- | --- |
| SMALL | full | 16 | 0 | 2 | 0 | 0.0% |
| SMALL | rag3 | 5 | 0 | 0 | 0 | 0.0% |
| SMALL | rag5 | 9 | 0 | 0 | 0 | 0.0% |
| MEDIUM | rag3 | 3 | 0 | 1 | 0 | 0.0% |
| MEDIUM | rag5 | 4 | 0 | 1 | 0 | 0.0% |
| LARGE | rag3 | 3 | 0 | 1 | 0 | 0.0% |
| LARGE | rag5 | 4 | 0 | 0 | 0 | 0.0% |
| XL | rag3 | 3 | 0 | 1 | 0 | 0.0% |
| XL | rag5 | 4 | 0 | 1 | 0 | 0.0% |

The frozen explicit-success detector is a marker-appearance proxy; a quoted rejected instruction is not successful compliance. `supplemental-audit.json` separates markers emitted as citation IDs from mere prose/quote appearances. Suspected promotion means a positive/partial overstatement with malicious text present; it is not automatically attributed to injection, because Qwen can make the same error without an attack. See the semantic/security audit for interpretation. Zero secret-ID citation compliance must not be represented as proof that all instruction-based promotions are absent. Exposure alone is not failure. Reduced exposure counts demonstrate less attack-bearing context, not a causal reduction in attack success; a sanitized-evidence counterfactual was not run.

Candidate B’s perfect evidence is kept in a separate candidate-bound database under the same node-local root. Foreign scope requests and foreign vector insertion are rejected before Qwen; A cannot resolve B records. Every scale checks active contexts against foreign and superseded IDs. Prior tenant isolation regressions are also retained.

Across **51 attack-exposed prompts**, secret-ID/canary appearance and citation compliance were **0/51**. Manual review found no requested fine-tuning promotion or AWS-verification assertion; all parseable h06 base-weight atoms remained UNSUPPORTED. Seven exposed prompts had the broader overstatement proxy; these are not established attack successes. No sanitized counterfactual was run. Unauthorized parsed IDs and cross-candidate output leakage were **0**, and all **68** foreign-scope/write attempts were rejected before generation. A separate scan found no unauthorized complete opaque ID among **920** raw-text occurrences, including malformed outputs. Incomplete or differently formatted identifiers are outside that supplemental regex scan, while parsed IDs are checked by the frozen validator.

## 17–18. Known weaknesses and attribution

| Scale | Arm | Unjustified partial atoms | False contradiction atoms | Existing but nonentailing citation pairs | Failure categories |
| --- | --- | --- | --- | --- | --- |
| SMALL | full | 2 | 3 | 9 | {'CITATION': 7, 'STRUCTURED OUTPUT': 6, 'QWEN REASONING': 5} |
| SMALL | rag3 | 1 | 5 | 9 | {'CITATION': 8, 'QWEN REASONING': 6, 'STRUCTURED OUTPUT': 6} |
| SMALL | rag5 | 1 | 4 | 9 | {'CITATION': 7, 'STRUCTURED OUTPUT': 7, 'QWEN REASONING': 5} |
| MEDIUM | rag3 | 1 | 5 | 20 | {'CITATION': 8, 'RETRIEVAL': 2, 'STRUCTURED OUTPUT': 7, 'QWEN REASONING': 7} |
| MEDIUM | rag5 | 1 | 5 | 31 | {'RETRIEVAL': 2, 'STRUCTURED OUTPUT': 7, 'QWEN REASONING': 7, 'CITATION': 7} |
| LARGE | rag3 | 1 | 5 | 20 | {'CITATION': 8, 'RETRIEVAL': 2, 'STRUCTURED OUTPUT': 7, 'QWEN REASONING': 7} |
| LARGE | rag5 | 1 | 5 | 26 | {'RETRIEVAL': 2, 'STRUCTURED OUTPUT': 8, 'QWEN REASONING': 6, 'CITATION': 6} |
| XL | rag3 | 1 | 5 | 20 | {'CITATION': 8, 'RETRIEVAL': 2, 'STRUCTURED OUTPUT': 7, 'QWEN REASONING': 7} |
| XL | rag5 | 2 | 5 | 33 | {'RETRIEVAL': 2, 'QWEN REASONING': 7, 'CITATION': 7, 'STRUCTURED OUTPUT': 7} |

Failures overlap. RETRIEVAL covers missing full-corpus support; QWEN REASONING applies only to incorrect judgments against supplied context; CITATION covers nonexistent or nonentailing citations; STRUCTURED OUTPUT includes the unchanged missing-evidence contract. Identity reranking introduces no reordering. The detailed row-level decisions are in `failures.json`; ingestion/chunking/storage/security defects are not inferred merely from a wrong answer. The report does not “fix” reasoning errors through evidence selection.

| Attribution category | Audited interpretation |
| --- | --- |
| INGESTION / DATASET | h06 parent/atom wording mismatch; preserve frozen scoring and report exclusion sensitivity. No observed ingestion corruption. |
| CHUNKING | No observed defect on short one-chunk fixtures; longer multi-chunk canonical evidence is outside this validated support boundary. |
| EMBEDDING | Similarity ranking contributes to the observed selection outcome; no independently isolated embedding implementation defect. |
| VECTOR STORAGE | Scope, lifecycle and provenance checks are separately replayed; no observed storage corruption or foreign-vector admission. |
| RETRIEVAL | Material FastAPI/RAG implementation components fall below the selected groups or outside the candidate pool. |
| RERANKING | Identity preserves order; it cannot recover missing candidates. No reordering defect. |
| CONTEXT CONSTRUCTION | Duplicate groups can expand to 20 records; full serialization becomes infeasible. These are measured budget/efficiency limits, with no hidden truncation. |
| QWEN REASONING | False denials, unjustified partial support and action/method/numeric confusion when supplied evidence permits the correct judgment. |
| CITATION | Existing, resolvable IDs and exact quotes often do not entail the asserted atomic relation. |
| STRUCTURED OUTPUT | Unrepaired cap-truncated JSON, missing-evidence contract failures and inconsistent parent/atomic aggregation. |
| SECURITY | Separate attack-target and isolation checks; exposure or ordinary reasoning error alone is not attack compliance. |

## 19–20. Tests, preservation and replay

Final results are in `regression.json`, `preservation.json`, `independent-verification.json`, and `environment-final.txt`. Independent verification rebuilds all four corpora using the real pinned embedding provider and fresh node-local databases, compares every context/ranking/provenance object, reconstructs tokenized prompts, decodes every saved output and recomputes all metrics. This is a separate-process artifact replay, not a second complete Qwen generation run. Two smoke cases are fresh-generation repeats.

Verified final results:

- **362/362 tests:** 343 RAG tests and 19 Stage 1/2 tests, including all prior 326 and 36 new Stage 3H tests.
- Stage 2 replay and Stage 3A/3B demos passed; **112** prior retrieval responses, **297** reranker results and **594** prefix checks reproduced.
- **64** case contexts rebuilt in a separate CPU process using actual pinned embeddings and fresh stores; **2,128** stored candidate-A provenance chains resolved. All context/ranking/source-pointer objects matched.
- **144** prompt/token/output replays and recomputed metrics matched exactly; **296** emitted atomic citation occurrences resolved through the rebuilt chain. The two fresh smoke repetitions matched prompt and output token IDs exactly, within the same original Qwen process.
- **857** prior protected files unchanged, **92** frozen files unchanged, initial/final dependency inventories identical.
- **144** unique expected generation keys and **192** unique feasibility slots; zero omissions, duplicates or time-budget skips. The recovery byte prefix covering the first **22** saved responses is unchanged.
- No invalid-schema atomic credit or duplicate atomic components were found. The three truncated outputs remain invalid and unrepaired.

Final raw archive SHA-256: `5b2037dc48803ffbe2e4c93731e69c4ebcb7893ffb36277e07f4baa99b593639` (3,816,587 bytes). See [independent verification](../results/stage3h/independent-verification.json), [regressions](../results/stage3h/regression.json), [preservation](../results/stage3h/preservation.json), [recovery/completeness audit](../results/stage3h/final-integrity.json), and [Slurm accounting](../results/stage3h/slurm_accounting.txt).

## 21–22. Freeze decision and current configuration

**B — DO NOT FREEZE YET.** The blocker is measured loss of material component evidence under realistic adjacent/near-duplicate noise. Both budgets lose support in 2/16 needs at every non-small scale, even though those facts remain in storage. Before QLoRA, evaluate the smallest versioned RAG correction that preserves component coverage within a bounded token budget, including candidate-pool selection and near-duplicate crowding. Do not assume an increased top-k alone will work. No particular correction has yet been validated.

No configuration is approved as frozen for QLoRA. The unchanged evaluated baseline is: moderate structural chunks, 640 Unicode characters / 96 overlap; `sentence-transformers/all-MiniLM-L6-v2` at revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, normalized 384-dimensional attention-mask mean pooling, 256-token reject-on-overflow limit, empty query/document prefixes and title-section-v1 inputs; private scope-bound SQLite exact cosine store, active source-version filtering and full lineage; semantic top-20 candidate pool with exact duplicate grouping; identity reranker; top-3 or top-5 groups; Stage 3G v2 untrusted JSON context, opaque IDs, exact-support authenticated attestations, scope validation and native-pointer provenance sidecars. Multi-chunk canonical-ID ambiguity continues to fail closed.

## 23. Future QLoRA targets

After the retrieval blocker is resolved, carry forward only reasoning failures demonstrated with sufficient supplied evidence: partial-versus-unknown calibration, absence-versus-contradiction distinction, action/method specificity, exact numeric claims without inventing verification requirements, citation entailment, and complete schema/contract adherence. The evidence-missing cases must not become training examples that reward unsupported guessing.

## 24. Exact next-stage boundary

Proposed next stage: a separately authorized, versioned RAG coverage correction and controlled replay on this frozen benchmark plus fresh held-out distractor cases. Limit changes to candidate retrieval/context selection and explicitly assess component survival, citation quality, tokens and leakage. Do not start QLoRA until the evidence-coverage defect is resolved and revalidated. Proposed exit criteria: restore material component evidence across all four frozen Stage 3H scales, retain the historical rank-five coverage case, validate fresh held-out distractors under an explicit bounded context budget, and preserve zero isolation/provenance regressions. Correct evidence reaching Qwen is the RAG criterion; remaining reasoning mistakes should not be hidden by benchmark-specific retrieval rules. Retain the explicit fail-closed multi-chunk boundary unless that contract is separately implemented and validated. No next-stage work was performed here.

## Annotation sensitivity and audit limits

The h06 parent requirement uses broad fine-tuning wording, while its supplied atomic component specifically asks whether base weights were updated. LoRA is a fine-tuning method; frozen-base adapter training does not update base weights. Frozen scores apply to the supplied narrow atom. The separate semantic audit and sensitivity excluding h06 preserve this limitation without changing gold. The unambiguous h05 FastAPI evidence loss independently supports the no-freeze decision.

Excluding h06 does not remove the retrieval blocker: evidence survival is 15/15 at SMALL and 14/15 at each larger scale, or 8/9 among the remaining evidence-bearing needs. At every non-small scale both RAG arms score 10/15 parent labels correctly (66.7%) on this sensitivity subset. The no-freeze recommendation therefore does not depend on the ambiguous fine-tuning wording.

## Appendix: per-label metrics

### SMALL / full

| Label | Gold n | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| SUPPORTED | 4 | 100.0% | 100.0% | 100.0% |
| PARTIALLY_SUPPORTED | 3 | 50.0% | 66.7% | 57.1% |
| UNSUPPORTED | 3 | 60.0% | 100.0% | 75.0% |
| UNKNOWN | 6 | 100.0% | 33.3% | 50.0% |

### SMALL / rag3

| Label | Gold n | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| SUPPORTED | 4 | 100.0% | 100.0% | 100.0% |
| PARTIALLY_SUPPORTED | 3 | 75.0% | 100.0% | 85.7% |
| UNSUPPORTED | 3 | 50.0% | 100.0% | 66.7% |
| UNKNOWN | 6 | 100.0% | 33.3% | 50.0% |

### SMALL / rag5

| Label | Gold n | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| SUPPORTED | 4 | 100.0% | 100.0% | 100.0% |
| PARTIALLY_SUPPORTED | 3 | 66.7% | 66.7% | 66.7% |
| UNSUPPORTED | 3 | 50.0% | 100.0% | 66.7% |
| UNKNOWN | 6 | 100.0% | 33.3% | 50.0% |

### MEDIUM / rag3

| Label | Gold n | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| SUPPORTED | 4 | 100.0% | 100.0% | 100.0% |
| PARTIALLY_SUPPORTED | 3 | 66.7% | 66.7% | 66.7% |
| UNSUPPORTED | 3 | 50.0% | 100.0% | 66.7% |
| UNKNOWN | 6 | 66.7% | 33.3% | 44.4% |

### MEDIUM / rag5

| Label | Gold n | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| SUPPORTED | 4 | 100.0% | 100.0% | 100.0% |
| PARTIALLY_SUPPORTED | 3 | 66.7% | 66.7% | 66.7% |
| UNSUPPORTED | 3 | 50.0% | 100.0% | 66.7% |
| UNKNOWN | 6 | 66.7% | 33.3% | 44.4% |

### LARGE / rag3

| Label | Gold n | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| SUPPORTED | 4 | 100.0% | 100.0% | 100.0% |
| PARTIALLY_SUPPORTED | 3 | 66.7% | 66.7% | 66.7% |
| UNSUPPORTED | 3 | 50.0% | 100.0% | 66.7% |
| UNKNOWN | 6 | 66.7% | 33.3% | 44.4% |

### LARGE / rag5

| Label | Gold n | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| SUPPORTED | 4 | 100.0% | 100.0% | 100.0% |
| PARTIALLY_SUPPORTED | 3 | 50.0% | 33.3% | 40.0% |
| UNSUPPORTED | 3 | 50.0% | 100.0% | 66.7% |
| UNKNOWN | 6 | 66.7% | 33.3% | 44.4% |

### XL / rag3

| Label | Gold n | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| SUPPORTED | 4 | 100.0% | 100.0% | 100.0% |
| PARTIALLY_SUPPORTED | 3 | 66.7% | 66.7% | 66.7% |
| UNSUPPORTED | 3 | 50.0% | 100.0% | 66.7% |
| UNKNOWN | 6 | 66.7% | 33.3% | 44.4% |

### XL / rag5

| Label | Gold n | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| SUPPORTED | 4 | 100.0% | 100.0% | 100.0% |
| PARTIALLY_SUPPORTED | 3 | 50.0% | 33.3% | 40.0% |
| UNSUPPORTED | 3 | 37.5% | 100.0% | 54.5% |
| UNKNOWN | 6 | 100.0% | 33.3% | 50.0% |

