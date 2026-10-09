# Stage 3I — atomic requirement decomposition and component-aware retrieval

**Stage 3I complete. Decision: B — DO NOT FREEZE RAG YET.**

The bounded correction restores h05’s FastAPI proof at LARGE/XL, but h06 still loses the RAG implementation proof. At each primary scale, evidence-bearing whole-requirement coverage improves from 8/10 to 9/10; material-component survival improves from 10/12 to 11/12. This is a measured partial fix. The evidence does not support freezing RAG or starting QLoRA.

## 1. Stage 3H defect diagnosis

Stage 3H’s whole-requirement search lost c01/c12/c21 construction evidence for h05 and c04 RAG implementation evidence for h06. At XL, c01 and c04 were at raw ranks 64 and 125, beyond the unchanged 20-vector pool. Top-5 therefore could not recover them. Stale/foreign evidence was not the cause. The original 144 outputs, including three malformed capped outputs, are unchanged and are reused as controls.

h06’s parent says fine-tuning while its supplied scoring atom narrows that to base-model weights. This pre-existing annotation limitation is preserved, not endorsed or silently corrected. The RAG implementation atom is distinct from that ambiguity. Comparisons excluding h06 are reported below.

## 2. Architecture and implementation files

New code is in `rag/component/{decompose,retrieve,benchmark,prepare,supplement,run,score,verify,verify_v2}.py`, with `__init__.py` and Slurm wrappers. New tests: `tests/rag/test_component.py`. New documentation: `docs/stage3i_architecture.md` and this report. New artifacts: `results/stage3i/`. No historical implementation/result/prompt/config/test file was modified. The final manifest lists every delivered Stage 3I file.

Pipeline: typed original requirement → conservative structural decomposition → existing Stage 3E retrieval per component → existing identity-reranker validation → deterministic round-robin distinct-group selection → existing Stage 3G provenance/context and support contract with retrieval membership metadata. MiniLM, VectorStore, source/chunk/claim models and trust boundaries are retained.

## 3. Slurm resources and lifecycle

GPU job **2333661** requested one A30, 8 CPUs, 64 GB RAM, 10:00:00 maximum, account cs541, partition academic. Actual device: `NVIDIA A30, GPU-bc81b1b7-ed75-37d3-110a-b9fb1d0bdca5, 24576 MiB, 595.71.05`. See `slurm-accounting.txt` and `gpu-job.txt` for actual CPU/RAM and elapsed allocation. The allocation completed and released after **1:32:49** (Slurm COMPLETED); CPU verification job **2333886** performs the independent replay. No Qwen inference ran on a login node and no second GPU was requested.

CPU preparation: 2333644 and 2333645 caught floating-point vector differences; 2333647 was cancelled before freeze while preserving atomic Top-5 compatibility; final preparation 2333649 completed. Supplemental CPU job 2333655 passed. Historical replay 2333674 exposed cross-CPU bitwise learned-score differences; matching CPU-family replay 2333675 reran the unchanged checks without requesting a GPU. All attempt logs are retained.

## 4. Decomposition design, safety and benchmark

Version `structural-extractive-v1`; no decomposition model, candidate evidence, external service or model-weight change. IDs hash version, original requirement ID/text, component order and component text. Exact original text and conjunct relationships remain attached. Recognized coordinated actions/shared objects and explicit “both” predicates split; negation, disjunction, conditions and unsupported syntax remain intact with a fallback status. Numeric and credential phrases remain relationally attached where splitting would weaken meaning.

The frozen benchmark has 34 synthetic cases, 46 authored expected components and 43 predicted components. Exact normalized matching yields 40 matches. Three deliberately difficult under-splits remain: Docker/deployment modifiers, shared FastAPI/Flask construction, and credential/experience conjunction. No semantic expansion was observed in the authored audit. Token-subset validation is an additional safety check, not a general proof of entailment. There was no independent human adjudication.

| Metric | Result |
| --- | --- |
| component_precision | 93.02% |
| component_recall | 86.96% |
| invented_component_rate | 0.00% |
| missed_component_rate | 13.04% |
| exact_entity_preservation | 100.00% |
| numeric_preservation | 100.00% |
| action_preservation | 100.00% |
| exact_decomposition_rate | 91.18% |

The smoke gate was declared before retrieval: precision ≥85%, recall ≥80%, exact entity/numeric/action preservation 100%, no invented tokens. It passed. These are measured synthetic results, not a universal guarantee of grammatical coverage. Primary under-splits are retained in `decomposition-failures.json`.

Granularity sensitivity: frozen case d12 retains “Maintained C++ and C# libraries” as one activity. A stricter per-technology interpretation requires two components and reveals one additional under-split. That post-freeze audit leaves the primary benchmark untouched and yields precision 39/43 = 90.70%, recall 39/47 = 82.98%, missed components 8/47 = 17.02%, and exact decomposition 30/34 = 88.24%; preservation and invented-component results are unchanged. It still passes the predeclared smoke thresholds. This sensitivity, saved separately, reinforces the limited grammar coverage rather than changing frozen gold after model outputs.

## 5. Retrieval budgets, merging and context contract

Retrieval-only selection chose **Top-2 per decomposed component; Top-5 for unsplit requirements; five final distinct-text groups**. The tested alternatives were per-component 1/2/3/5 and global limits 5/6. Larger tested budgets did not restore h06. Atomic Top-5 retains Stage 3F’s rank-five evidence case. The fixed 0.20 cosine floor is a plausibility heuristic, not a support/entailment score or a production-calibrated cutoff.

Each query keeps the Stage 3E 20-vector pool, focused-v1 construction without expansion, active filters and authenticated tenant/candidate scope. Selection visits each component’s first group before second groups. Duplicate groups merge before budget selection; all retrieved component rank/score/query metadata and authenticated corroborating source references survive. Five groups may contain more than five independently sourced records; source counts and duplicate overhead are measured rather than hidden.

Context states distinguish selected candidates, budget-excluded candidates, and no plausible candidate retrieved. A semantically adjacent candidate can still be returned for a component with no supporting evidence; membership explicitly does not prove support. Empty-corpus tests validate the missing-candidate signal. Component metadata is trusted application output; evidence text remains untrusted JSON data. Group-level memberships include exact-text corroboration; full traces preserve exact per-reference membership.

Stage 3G support schema/system/label semantics are unchanged. Qwen scores the original Stage 3H atomic claims while generated retrieval components are exposed separately. Thus this experiment isolates component-query retrieval/context selection; it does not claim validated end-to-end automatic authoring of Qwen’s scored atoms.

## 6. Required-evidence survival and scale comparison

| Scale | Arm | Material components surviving | All required components covered | Mean groups | Mean records |
| --- | --- | --- | --- | --- | --- |
| SMALL | rag3 | 12/12 (100.00%) | 10/10 (100.00%) | 3.00 | 3.25 |
| SMALL | rag5 | 12/12 (100.00%) | 10/10 (100.00%) | 5.00 | 5.38 |
| SMALL | component | 12/12 (100.00%) | 10/10 (100.00%) | 4.38 | 4.69 |
| MEDIUM | rag3 | 10/12 (83.33%) | 8/10 (80.00%) | 3.00 | 3.62 |
| MEDIUM | rag5 | 10/12 (83.33%) | 8/10 (80.00%) | 5.00 | 5.62 |
| MEDIUM | component | 11/12 (91.67%) | 9/10 (90.00%) | 4.62 | 5.56 |
| LARGE | rag3 | 10/12 (83.33%) | 8/10 (80.00%) | 2.81 | 5.12 |
| LARGE | rag5 | 10/12 (83.33%) | 8/10 (80.00%) | 4.56 | 6.88 |
| LARGE | component | 11/12 (91.67%) | 9/10 (90.00%) | 4.19 | 7.69 |
| XL | rag3 | 10/12 (83.33%) | 8/10 (80.00%) | 2.81 | 5.12 |
| XL | rag5 | 10/12 (83.33%) | 8/10 (80.00%) | 4.56 | 6.88 |
| XL | component | 11/12 (91.67%) | 9/10 (90.00%) | 4.19 | 7.69 |

Coverage denominators exclude six absence-only requirements; they do not receive vacuous retrieval-success credit. The earlier preparation summary also reports a requirement-weighted mean of per-requirement component fractions (85%→95% at LARGE/XL); the table above reports the more direct component micro-average (83.33%→91.67%). Relevant-evidence document recall, proof-hit@1/2/3/5 and final component survival are separate metrics. See `per-component-recall.json`, `final-retrieval-metrics.json`, and the frozen ablation traces.

| Scale | Candidate k | Mean component document recall | Component proof-hit rate |
| --- | --- | --- | --- |
| LARGE | 1 | 69.29% | 83.33% |
| LARGE | 2 | 77.62% | 91.67% |
| LARGE | 3 | 77.62% | 91.67% |
| LARGE | 5 | 77.62% | 91.67% |
| XL | 1 | 61.27% | 83.33% |
| XL | 2 | 69.61% | 91.67% |
| XL | 3 | 69.61% | 91.67% |
| XL | 5 | 69.61% | 91.67% |

The Recall@k table uses the saved per-component candidate rankings before the final merge. Ordered gold atoms are aligned to generated queries where cardinality matches; unsplit requirements share their single query. Exact-document recall counts all authored relevant copies, while proof-hit requires any valid source for that component. It is therefore possible to preserve a proposition while omitting some corroborating copies.

h05 is restored at every scale; h06 remains a retrieval loss at MEDIUM/LARGE/XL. All other evidence-bearing requirements preserve their full-corpus judgment. Excluding h06, all nine evidence-bearing requirements are covered in Stage 3I at LARGE/XL versus eight under either historical global arm.

## 7. Dangerous neighbors, duplication, isolation and injection

| Scale | Arm | Dangerous-neighbor rate | Repeated-text record fraction | Stale leakage | Cross-candidate leakage |
| --- | --- | --- | --- | --- | --- |
| LARGE | rag3 | 58.33% | 11.56% | 0% | 0% |
| LARGE | rag5 | 65.00% | 11.56% | 0% | 0% |
| LARGE | component | 57.65% | 16.96% | 0% | 0% |
| XL | rag3 | 58.33% | 11.56% | 0% | 0% |
| XL | rag5 | 65.00% | 11.56% | 0% | 0% |
| XL | component | 57.65% | 16.96% | 0% | 0% |

The final dangerous-neighbor table uses the exact Stage 3H per-need hard-core taxonomy and generated distractor categories, recalculated for all arms. Preparation’s broader conservative core-neighbor diagnostic remains separately saved and is not substituted for this matched metric. Context duplicate overhead reflects independently sourced exact copies; no evidence ID or text group is selected twice.

Supplemental CPU fixtures: 7 passed, covering held-out actions, exact numbers, missing/several-missing components, LoRA/QLoRA/RAG neighbors, malicious scope instructions, perfect evidence in candidate B, deterministic replay, and the historical rank-five case. Three entirely absent components produce explicit no-candidate states. Supporting evidence is not fabricated for missing components.

| Scale | Attack-exposed Qwen prompts | Explicit foreign ID/canary success | Suspected promotion proxy | Output candidate leakage |
| --- | --- | --- | --- | --- |
| SMALL | 9 | 0 | 0 | 0.00% |
| MEDIUM | 4 | 0 | 1 | 0.00% |
| LARGE | 4 | 0 | 1 | 0.00% |
| XL | 4 | 0 | 1 | 0.00% |

Exposure is not instruction compliance. The suspected-promotion measure is an overstatement proxy and does not establish attack causality without a sanitized counterfactual. No production-wide injection robustness claim is made from these authored fixtures.

## 8. Qwen labels, atoms, compound conclusions and contract

| Scale | Arm | n | Label accuracy | Macro F1 | Atomic accuracy | Compound accuracy | JSON | Schema | Full contract |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SMALL | rag3 | 16 | 75.00% | 0.756 | 70.00% | 100.00% | 100.00% | 100.00% | 62.50% |
| SMALL | rag5 | 16 | 68.75% | 0.708 | 65.00% | 75.00% | 93.75% | 93.75% | 56.25% |
| SMALL | component | 16 | 75.00% | 0.756 | 70.00% | 100.00% | 100.00% | 100.00% | 62.50% |
| MEDIUM | rag3 | 16 | 68.75% | 0.694 | 65.00% | 75.00% | 100.00% | 100.00% | 50.00% |
| MEDIUM | rag5 | 16 | 68.75% | 0.694 | 65.00% | 75.00% | 100.00% | 100.00% | 50.00% |
| MEDIUM | component | 16 | 68.75% | 0.693 | 65.00% | 75.00% | 100.00% | 100.00% | 50.00% |
| LARGE | rag3 | 16 | 68.75% | 0.694 | 65.00% | 75.00% | 100.00% | 100.00% | 50.00% |
| LARGE | rag5 | 16 | 62.50% | 0.628 | 55.00% | 50.00% | 93.75% | 93.75% | 43.75% |
| LARGE | component | 16 | 62.50% | 0.642 | 60.00% | 50.00% | 100.00% | 100.00% | 43.75% |
| XL | rag3 | 16 | 68.75% | 0.694 | 65.00% | 75.00% | 100.00% | 100.00% | 50.00% |
| XL | rag5 | 16 | 62.50% | 0.611 | 60.00% | 50.00% | 100.00% | 100.00% | 50.00% |
| XL | component | 16 | 62.50% | 0.642 | 60.00% | 50.00% | 100.00% | 100.00% | 43.75% |

Metrics use unchanged full-corpus gold. Context-conditional atomic metrics remain separately available. A correct compound label does not excuse an incorrect atom. Full-contract validity includes the inherited rule requiring nonempty missing_evidence for every non-SUPPORTED label, even conclusive denials; that contract-design limitation was not changed. Full per-label precision/recall/F1/support and confusion counts are saved in `comparison.json` and `metrics.json`. Historical outputs are reused, not regenerated.

Across the 32 primary LARGE/XL generations, label accuracy is 62.50% and atomic accuracy is 60.00%. Across all 64 scale/regression generations, label accuracy is 67.19%. These repeat the same 16 needs across nested corpora and are not 64 independent population samples.

| Scale | Arm | Label | Precision | Recall | F1 | Gold support |
| --- | --- | --- | --- | --- | --- | --- |
| LARGE | rag3 | SUPPORTED | 100.00% | 100.00% | 100.00% | 4 |
| LARGE | rag3 | PARTIALLY_SUPPORTED | 66.67% | 66.67% | 66.67% | 3 |
| LARGE | rag3 | UNSUPPORTED | 50.00% | 100.00% | 66.67% | 3 |
| LARGE | rag3 | UNKNOWN | 66.67% | 33.33% | 44.44% | 6 |
| LARGE | rag5 | SUPPORTED | 100.00% | 100.00% | 100.00% | 4 |
| LARGE | rag5 | PARTIALLY_SUPPORTED | 50.00% | 33.33% | 40.00% | 3 |
| LARGE | rag5 | UNSUPPORTED | 50.00% | 100.00% | 66.67% | 3 |
| LARGE | rag5 | UNKNOWN | 66.67% | 33.33% | 44.44% | 6 |
| LARGE | component | SUPPORTED | 100.00% | 75.00% | 85.71% | 4 |
| LARGE | component | PARTIALLY_SUPPORTED | 66.67% | 66.67% | 66.67% | 3 |
| LARGE | component | UNSUPPORTED | 37.50% | 100.00% | 54.55% | 3 |
| LARGE | component | UNKNOWN | 100.00% | 33.33% | 50.00% | 6 |
| XL | rag3 | SUPPORTED | 100.00% | 100.00% | 100.00% | 4 |
| XL | rag3 | PARTIALLY_SUPPORTED | 66.67% | 66.67% | 66.67% | 3 |
| XL | rag3 | UNSUPPORTED | 50.00% | 100.00% | 66.67% | 3 |
| XL | rag3 | UNKNOWN | 66.67% | 33.33% | 44.44% | 6 |
| XL | rag5 | SUPPORTED | 100.00% | 100.00% | 100.00% | 4 |
| XL | rag5 | PARTIALLY_SUPPORTED | 50.00% | 33.33% | 40.00% | 3 |
| XL | rag5 | UNSUPPORTED | 37.50% | 100.00% | 54.55% | 3 |
| XL | rag5 | UNKNOWN | 100.00% | 33.33% | 50.00% | 6 |
| XL | component | SUPPORTED | 100.00% | 75.00% | 85.71% | 4 |
| XL | component | PARTIALLY_SUPPORTED | 66.67% | 66.67% | 66.67% | 3 |
| XL | component | UNSUPPORTED | 37.50% | 100.00% | 54.55% | 3 |
| XL | component | UNKNOWN | 100.00% | 33.33% | 50.00% | 6 |

| Scale | Arm | Label accuracy excluding h06 | Atomic accuracy excluding h06 |
| --- | --- | --- | --- |
| LARGE | rag3 | 66.67% | 61.11% |
| LARGE | rag5 | 66.67% | 61.11% |
| LARGE | component | 66.67% | 61.11% |
| XL | rag3 | 66.67% | 61.11% |
| XL | rag5 | 66.67% | 61.11% |
| XL | component | 66.67% | 61.11% |

Six smoke outputs were saved before primary inference: strict JSON/schema valid counts 6/6 and 6/6. Smoke errors, including contract errors, are retained in `smoke.json`; smoke is not part of primary accuracy. Primary output-cap hits: 0. Exact cases: `[]`. Malformed primary text remains invalid; it is not repaired, retried with a larger cap, or replaced.

## 9. Citation and candidate-claim grounding

| Scale | Arm | Citation validity | Citation precision | Unsupported citation rate | Fabricated ID rate | Hallucinated positive-claim proxy |
| --- | --- | --- | --- | --- | --- | --- |
| LARGE | rag3 | 100.00% | 33.33% | 66.67% | 0.00% | 25.00% |
| LARGE | rag5 | 100.00% | 25.71% | 74.29% | 0.00% | 14.29% |
| LARGE | component | 97.50% | 28.21% | 69.23% | 2.60% | 12.50% |
| XL | rag3 | 100.00% | 33.33% | 66.67% | 0.00% | 25.00% |
| XL | rag5 | 100.00% | 23.26% | 76.74% | 0.00% | 25.00% |
| XL | component | 100.00% | 28.21% | 71.79% | 0.00% | 12.50% |

Validity checks ID membership/provenance; precision uses the frozen authored document-to-atom entailment relations. Existing IDs and exact quotes can still fail entailment. Citation precision is conditional on parseable asserted-relation citations and must be read alongside output validity. The hallucination statistic is the established positive/partial-atom overstatement proxy, not a complete prose audit.

## 10. Context and performance

| Scale | Arm | Mean input tokens | Mean generated tokens | Mean total tokens | Mean Qwen seconds | Mean output tokens/s |
| --- | --- | --- | --- | --- | --- | --- |
| LARGE | rag3 | 2018 | 628 | 2646 | 66.86 | 9.33 |
| LARGE | rag5 | 2338 | 779 | 3117 | 82.72 | 9.31 |
| LARGE | component | 3538 | 748 | 4286 | 80.23 | 9.21 |
| XL | rag3 | 2020 | 623 | 2642 | 66.85 | 9.25 |
| XL | rag5 | 2342 | 808 | 3150 | 86.51 | 9.23 |
| XL | component | 3544 | 754 | 4299 | 80.99 | 9.19 |

| Scale | Mean prompt tokens | Mean generated tokens | Mean total tokens | Reduction vs full | Change vs Top-3 | Change vs Top-5 | Mean Qwen seconds | Mean tokens/s | Peak allocated GiB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SMALL | 2874 | 608 | 3482 | 46.63% | 70.10% | 39.19% | 65.24 | 9.24 | 17.93 |
| MEDIUM | 3110 | 825 | 3934 | 83.78% | 76.54% | 46.35% | 88.10 | 9.25 | 18.30 |
| LARGE | 3538 | 748 | 4286 | 96.16% | 75.36% | 51.33% | 80.23 | 9.21 | 19.34 |
| XL | 3544 | 754 | 4299 | 98.71% | 75.49% | 51.37% | 80.99 | 9.19 | 19.36 |

| Scale | Mean decomposition seconds | Mean retrieval seconds | Mean merge seconds |
| --- | --- | --- | --- |
| SMALL | 0.000040 | 0.018013 | 0.002195 |
| MEDIUM | 0.000046 | 0.058819 | 0.002512 |
| LARGE | 0.000050 | 0.275044 | 0.002982 |
| XL | 0.000055 | 0.854962 | 0.003599 |

Qwen model load: 42.60s. Timed run interval after imports, including load, smoke and primary inference: 5545.86s. Primary inference latency sum: 5032.95s. Primary input/generated/total tokens: 209,051 / 46,970 / 256,021. Evidence groups, source records, per-case latency, tokens/s and Torch allocated/reserved peaks are saved. Ten-second whole-device telemetry is separately recorded in `gpu-telemetry-2333661.csv`; it can miss short peaks.

The whole-device telemetry sampled 557 memory values and observed a maximum of 21147 MiB. This is distinct from Torch allocation/reservation peaks and can miss short peaks.

Changes versus Top-3/Top-5 in this table use ratios of total/mean prompt tokens across matched cases. The raw performance JSON also retains the distinct mean of per-case relative changes. Full-context denominators are Stage 3H’s actual tokenizer counts, including infeasible LARGE/XL full contexts. No full-context inference speedup is inferred where that arm could not run. Retrieval preparation and Qwen generation are timed separately; this is not a production end-to-end throughput benchmark. The study retains single-candidate/template-distribution limits.

## 11. Failure attribution and remaining Qwen errors

| Scale | Attribution counts |
| --- | --- |
| SMALL | {"CITATION FAILURE": 8, "QWEN REASONING FAILURE": 6, "STRUCTURED OUTPUT FAILURE": 6} |
| MEDIUM | {"CITATION FAILURE": 8, "QWEN REASONING FAILURE": 8, "RETRIEVAL FAILURE": 1, "STRUCTURED OUTPUT FAILURE": 7} |
| LARGE | {"CITATION FAILURE": 8, "QWEN REASONING FAILURE": 8, "RETRIEVAL FAILURE": 1, "STRUCTURED OUTPUT FAILURE": 8} |
| XL | {"CITATION FAILURE": 8, "QWEN REASONING FAILURE": 8, "RETRIEVAL FAILURE": 1, "STRUCTURED OUTPUT FAILURE": 8} |

The schema records only the required categories: DECOMPOSITION FAILURE, COMPONENT QUERY FAILURE, EMBEDDING FAILURE, RETRIEVAL FAILURE, MERGE/BUDGET FAILURE, CONTEXT CONSTRUCTION FAILURE, QWEN REASONING FAILURE, CITATION FAILURE, STRUCTURED OUTPUT FAILURE, SECURITY FAILURE. Multiple categories may apply to one case. No category is assigned merely to make counts exhaustive; decomposition benchmark misses are separate from Qwen cases. Wrong answers with intact full-corpus judgments are reasoning/citation errors; absent required evidence remains retrieval loss even if the parent label happens to be correct.

Residual h06 is conservatively classified RETRIEVAL FAILURE in primary scoring. A separately labelled, post-freeze CPU diagnostic changed only the query acronym RAG to its exact expanded name. c04 moved from rank 42 to 1 at LARGE and 125 to 1 at XL (MEDIUM 9 to 1). This demonstrates component-query representation sensitivity with the unchanged MiniLM model; it does not establish a general alias policy or an evaluated end-to-end fix. Those alternate queries were never supplied to the primary Qwen run. See alias-diagnostic.json. The narrower diagnostic category is COMPONENT QUERY FAILURE; no model replacement or primary synonym expansion was silently introduced.

Observed Qwen errors with no measured retrieval loss are enumerated in `qwen-errors-without-retrieval-loss.json`. Counts below use only those cases and preserve distinctions between insufficient evidence and explicit contradiction. They are diagnostic observations, not a training handoff.

Concrete LARGE examples: h02 receives byte-equal ordered factual evidence to the historical Top-5 context, including explicit Docker/AWS deployment proof, but Qwen downgrades deployment to PARTIALLY_SUPPORTED because unrelated planning notes supposedly create ambiguity. h05 now correctly supports FastAPI construction but converts a Kubernetes documentation review with no recorded deployment into UNSUPPORTED rather than UNKNOWN. h07 correctly supports PyTorch training while treating TensorFlow learning goals as a categorical denial; it also emits a non-exact quotation. These are preserved reasoning/citation failures, not reasons to remove correctly retrieved evidence. Added metadata distinguishes the new prompt from the historical prompt, so this is not an identical-prompt repeat.

| Scale | Unjustified PARTIALLY_SUPPORTED | False contradiction for UNKNOWN | Existing non-entailing citations |
| --- | --- | --- | --- |
| SMALL | 1 | 5 | 11 |
| MEDIUM | 1 | 5 | 25 |
| LARGE | 0 | 6 | 24 |
| XL | 0 | 6 | 25 |

## 12. Tests, replay, preservation and reproducibility

Final unit/regression tests: 429 passed ({"stage3-tests": 410, "stage1-stage2-tests": 19}). Historical Stage 3E 112-case and Stage 3F 297-result replays passed on the matching CPU family, with unchanged assertions. The initial heterogeneous-CPU bitwise learned-score failure is preserved in the attempt log; it was not fixed by weakening comparisons or editing old artifacts.

Independent CPU replay reconstructed 64 contexts, resolved 2128 stored provenance chains, checked 154 emitted citation pairs and 447 raw opaque-ID occurrences, replayed 46970 generated tokens, checked 64 unique expected run IDs, and reproduced all saved metrics. Prompt rendering and tokenizer counts, scope, active versions and untrusted flags matched. This is an independent process, not independent human adjudication or a second Qwen run.

Initial verifier 2333662 correctly stopped on an invalid model citation in LARGE h12. Its raw output and failed verification log are preserved. The versioned verifier v2 measures invalid IDs as scored model failures, verifies that the scorer rejects them, and still enforces candidate ownership for real context evidence. Invalid citation audit: `[{"scale": "LARGE", "id": "h12", "component_id": "a1", "evidence_id": "evidence_8072d308e7c73bbdd57eea1aa02d964331c76be9cc1aabd78915d874836600", "exists": false, "entailed": false, "asserted_relation": true}]`. This changes verification handling, not inference, scoring, gold, retrieval or historical tests.

Protected files: 705 newly inventoried non-model historical files, plus the pre-existing 857-file Stage 1–3G protection mechanism and 92 Stage 3H freeze entries; these sets overlap and must not be summed. All remain byte-identical. Corpus vectors/input identities remain the frozen Stage 3H values. New query embeddings were frozen; CPU re-embedding max absolute delta was 1.42e-07, and exact saved vectors were used for reproducible context replay.

The consolidated `reproducibility.json` records experiment stage3i-v1, decomposition dataset stage3i-decomposition-v1, unchanged control corpus stage3h-scale-v1, and the complete runtime/configuration. MiniLM is sentence-transformers/all-MiniLM-L6-v2 at revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41, using normalized 384-dimensional attention-mask mean pooling, float32 CPU and title-section-v1 inputs. Reproduction records include dataset versions/hashes, original corpus and scope, decomposition/ID/query/merge/dedup/global/per-component strategies, pinned MiniLM model/revision and title-section-v1 input, moderate chunk policy and semantic-space references, identity configuration, original Stage 3G system/schema hashes, Stage 3I source snapshots, Qwen model path/architecture/quantization/BF16/generation/seed/thinking/output cap, dependency freeze, Slurm/GPU/resources, raw text and token IDs, parsed predictions, traces, component mappings, metrics and failures. No model was downloaded or changed.

## 13. Decision, smallest remaining defect and next-stage boundary

**B — DO NOT FREEZE RAG YET.**

The smallest remaining demonstrated RAG-layer defect is component-query representation for acronym-bearing RAG implementation: the literal RAG query loses c04 behind architectural/learning references at scale. The exact-name diagnostic restores c04 to rank 1 without increasing the evidence budget, isolating a promising small correction for separate validation. It was not incorporated after the primary configuration froze, and is not claimed as a completed fix. Increasing the tested per-component/global budgets did not fix the frozen primary retrieval. Separately, the conservative decomposition grammar misses three benchmark constructions and is not ready to serve as a universal atomic analyzer.

The experimental retrieval configuration is frozen for reproducibility, **not** approved as a production RAG freeze. Because the decision is B, no QLoRA-ready configuration or training-target handoff is declared. The observed Qwen error inventory is retained for later consideration only after the retrieval gate passes.

Next authorized boundary: NONE in this session. A future separately authorized corrective stage could isolate component-query wording/alias representation versus embedding ranking under the same bounded evidence budget, and validate the three under-split grammar forms. Do not train adapters, generate training datasets, modify Qwen weights, perform browser/job/application workflows, generate CVs/letters, conduct outreach or deploy production changes. Stage 3I ends here.

## Artifact index

- `docs/stage3i_architecture.md`: architecture and boundaries.
- `results/stage3i/config.json`, `retrieval-freeze.json`: pre-Qwen retrieval choice and hashes.
- `decomposition-dataset.json`, `decomposition-results.json`, `decomposition-failures.json`: frozen decomposition evaluation.
- `*-retrieval.json`, `*-prepared.json`, `query-vectors.json`: all ablations, final contexts and query vectors.
- `supplement-dataset.json`, `supplement-results.json`: held-out and security regression fixtures.
- `benchmark-2333661/`: raw/smoke outputs, token IDs, parsed predictions, model config, comparisons, performance and failures.
- `final-retrieval-metrics.json`, `per-component-recall.json`, `retrieval-failure-diagnostic.json`: coverage and residual-rank diagnosis.
- `independent-verification.json`, `regression.json`, protection manifests, test logs and Slurm accounting: replay and preservation evidence.
