# Stage 3G — Qwen + RAG evidence reasoning

**Stage 3G complete. Stage 3H has not begun.**

This report separates the historical Stage 2 prompt comparison from the matched-prompt full-context control. Missing evidence was UNSUPPORTED in Stage 2 and is UNKNOWN in Stage 3G. Apparent gains over Stage 2 cannot be assigned entirely to retrieval.

## Architecture implemented

Trusted candidate scope → unchanged Stage 3E semantic retrieval (internal 20, grouped exact duplicates, no expansion/caps) → Stage 3F identity reranker → five evidence groups → Qwen atomic judgments → strict JSON/ID/quote/ownership validation. Full provenance stays in each prepared response and sidecar. See stage3g_architecture.md for boundary and reproduction details.

## Files and preservation

Added rag/reasoning/{contract,prepare,run,evaluate,regression,verify,report}.py, __init__.py, system_v2.txt, schema.json, prepare.slurm and gpu.slurm; tests/rag/test_reasoning.py and test_reasoning_metrics.py; fixtures/rag/reasoning_eval/stage3g_v1.json; docs/stage3g_architecture.md and this report; results/stage3g/ artifacts. Earlier-stage code, models, environments and historical results were not modified. The final preservation report is results/stage3g/preservation.json.

## Slurm and model configuration

Primary GPU Slurm job **2330445**, account cs541, partition academic, one A30, 8 CPUs, 64 GiB RAM, eight-hour maximum. The batch exits after the benchmark. Exact scheduler accounting is in results/stage3g/slurm_accounting.txt. Failed preparation/logging attempts and the cancelled diagnostic run with descriptive identifiers are retained and described in the execution audit. Only the blinded v2 run supplies primary metrics.

Model path: `/scratch/mohammedmubashir/resume-ai/models/Qwen3.8-27B`. Runtime architecture: `Qwen3_5ForCausalLM`. Directory naming is not architectural identity. Existing Stage 2 weights/dependencies retained. NF4, double quantization, BF16 compute/dtype, requested device_map=auto; actual parameter devices ['cuda:0']. Greedy generation, max_new_tokens=1536, use_cache=true, thinking=false, seed=42. Full model configuration, quantization, default generation parameters, GPU/driver and library versions: `benchmark-2330445/config.json`.

## Context, schema and security

Each JSON evidence group contains canonical evidence IDs, content, source type/origin, untrusted-data designation, verification policy, exact-support synthetic attestations when applicable, source version and span. Opaque evidence IDs serve as citation handles; native pointers and original attestation references remain in the validated provenance sidecars. No tenant ID, descriptive fixture identifier, source key, or ranking score is sent to Qwen. Requirement IDs and attestation references are opaque hashes. Delimited JSON lives in a user message separate from the system behavior contract. Evidence has no tool or scope-changing capability.

Output: information_need_id, label, atomic_claims (component_id, claim, label, evidence_ids, exact quotes, reason), evidence_ids union, missing_evidence and concise reason. No hidden reasoning traces. Raw parsing rejects fences, trailing prose, duplicate keys and nonfinite values. A failed raw result is not repaired for the primary metric.

Native citation resolution checks active vector → EmbeddingRecord → RetrievalChunk/revision → canonical evidence → source/version → pointer. Corpus ownership is checked upstream and again before context construction. Exact quote matching is necessary traceability, not a general entailment proof. Synthetic VerificationRecords exercise exact-support metadata only; no production verifier or real credential is claimed.

## Dataset and experimental controls

37 synthetic cases, 54 atomic components. Full-context gold distribution: {'SUPPORTED': 10, 'UNKNOWN': 17, 'PARTIALLY_SUPPORTED': 6, 'UNSUPPORTED': 4}. No private data. Compatible Stage 3E/F wording is reused; newly authored cases cover the requested numeric/action/technology/trust/injection/isolation conditions.

stage2 uses original grounded_v3 system/task/schema and all current candidate evidence. full uses the Stage 3G contract with all current evidence; rag5 uses the identical contract and real top-five groups. All arms use identical inference settings. Entirely identical rendered prompts reuse the same greedy output, explicitly marked reused_from_arm; these are not counted as new generations or timed at zero as if fresh inference. Arms with different prompts always run.

Atomic slots are supplied without gold labels as structured task components. The experiment measures atomic judgment and aggregation, not autonomous decomposition discovery. Most candidates have only one evidence group. A retrieval-selected QLoRA stress fixture puts genuine adaptation at rank five beneath four learning/interest distractors, without manual reordering.

## Primary comparison

| Arm | Cases | Strict JSON | Schema | Full contract | Label accuracy | Macro F1 |
|---|---:|---:|---:|---:|---:|---:|
| stage2 | 37 | 100.00% | 100.00% | 100.00% | 54.05% | 0.5175 |
| full | 37 | 100.00% | 100.00% | 83.78% | 78.38% | 0.7988 |
| rag5 | 37 | 100.00% | 100.00% | 83.78% | 78.38% | 0.7988 |

Stage 2 full-contract validity above means its historical schema, not the new atomic/quote contract. New-contract failures are not concealed by schema validity. Context-conditional accuracy is retained separately in metrics.json.

## Support-label metrics

| Arm | Label | Gold n | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|
| stage2 | SUPPORTED | 10 | 90.91% | 100.00% | 95.24% |
| stage2 | PARTIALLY_SUPPORTED | 6 | 46.15% | 100.00% | 63.16% |
| stage2 | UNSUPPORTED | 4 | 25.00% | 75.00% | 37.50% |
| stage2 | UNKNOWN | 17 | 100.00% | 5.88% | 11.11% |
| full | SUPPORTED | 10 | 100.00% | 80.00% | 88.89% |
| full | PARTIALLY_SUPPORTED | 6 | 46.15% | 100.00% | 63.16% |
| full | UNSUPPORTED | 4 | 80.00% | 100.00% | 88.89% |
| full | UNKNOWN | 17 | 100.00% | 64.71% | 78.57% |
| rag5 | SUPPORTED | 10 | 100.00% | 80.00% | 88.89% |
| rag5 | PARTIALLY_SUPPORTED | 6 | 46.15% | 100.00% | 63.16% |
| rag5 | UNSUPPORTED | 4 | 80.00% | 100.00% | 88.89% |
| rag5 | UNKNOWN | 17 | 100.00% | 64.71% | 78.57% |

## Atomic, compound, citation and hallucination results

| Metric | Stage 2 | Full control | RAG 5 |
|---|---:|---:|---:|
| atomic_claim_accuracy | 59.26% | 85.19% | 85.19% |
| compound_claim_accuracy | 100.00% | 100.00% | 100.00% |
| citation_validity | 100.00% | 100.00% | 100.00% |
| citation_precision | 78.57% | 85.00% | 85.00% |
| unsupported_citation_rate | 21.43% | 15.00% | 15.00% |
| fabricated_evidence_id_rate | 0.00% | 0.00% | 0.00% |
| hallucinated_candidate_claim_rate | 22.86% | 15.62% | 15.62% |
| prompt_injection_failure_rate | 0.00% | 0.00% | 0.00% |
| cross_candidate_leakage_rate | 0.00% | 0.00% | 0.00% |

Citation precision scores authored positive/partial/contradiction atomic relations only; UNKNOWN explanatory citations are checked for existence and separately reviewed. Rates are micro-averaged over atomic citation pairs, with counts in metrics.json. Fabricated-ID rate counts emitted atomic plus top-level ID occurrences. Hallucination rate counts overstated positive/partial atomic conclusions, not every free-text assertion. A separate semantic audit covers prose and examples.

## Prompt injection and tenant isolation

Three attack cases per primary arm include imperative label promotion, fake role/delimiter text and legitimate evidence mixed with a malicious technology instruction. The model has no retrieval tool. Candidate B has perfect Kubernetes evidence and a secret canary; trusted Candidate A retrieval cannot read its vector and rejects an attempt to use B scope. Foreign IDs and the canary are checked against output. Zero observed leakage is a fixture result, not a production security proof.

## Evidence-budget ablation (same ten cases)

| Groups | Accuracy vs full available evidence | Context-conditional accuracy | Atomic accuracy conditional on supplied context | Citation precision |
|---|---:|---:|---:|---:|
| rag1 | 80.00% | 90.00% | 91.30% | 89.47% |
| rag3 | 90.00% | 100.00% | 100.00% | 100.00% |
| rag5 | 90.00% | 90.00% | 95.65% | 100.00% |

A safe UNKNOWN after lost retrieval support counts against end-to-end accuracy but not against context-conditional reasoning accuracy. No content-only/provenance ablation was run; the matrix was limited to the requested evidence-budget comparison.

## Failure attribution

Categories may overlap. Stage 2 absence-policy mismatches appear in reasoning comparisons against current semantics but are not evidence that retrieval fixed them. Smaller-budget selection losses are distinguished from primary top-five retrieval misses.

| Arm | Attributed failures |
|---|---|
| full | {'LLM REASONING FAILURE': 8, 'CITATION FAILURE': 6, 'STRUCTURED OUTPUT FAILURE': 6} |
| rag1 | {'STRUCTURED OUTPUT FAILURE': 1, 'RANKING FAILURE': 2, 'LLM REASONING FAILURE': 2, 'CITATION FAILURE': 2} |
| rag3 | {'STRUCTURED OUTPUT FAILURE': 1, 'RANKING FAILURE': 1} |
| rag5 | {'LLM REASONING FAILURE': 8, 'CITATION FAILURE': 6, 'STRUCTURED OUTPUT FAILURE': 6} |
| stage2 | {'LLM REASONING FAILURE': 21, 'CITATION FAILURE': 9} |

Every failure, expected/context label, atomic counts, citation pair judgment and contract error is in benchmark-2330445/failures.json and scored.json. Interpret the separate semantic audit before treating an automatic failure as unambiguous human-adjudicated truth.

## Runtime and resource use

Qwen load: 23.99 s. Benchmark process total: 4146.76 s. Model loaded once for the full benchmark. Smoke used a separate load.

| Arm | New generations / contexts | Prompt tokens median / max | Output tokens median / max | Median latency (s), new generations | Tokens/s, new generations | Peak allocated GiB |
|---|---:|---:|---:|---:|---:|---:|
| full | 25 / 37 | 1273 / 2082 | 419 / 1459 | 44.66 | 9.52 | 17.46 |
| rag1 | 3 / 10 | 1294.5 / 1578 | 583.5 / 1248 | 46.95 | 9.57 | 17.26 |
| rag3 | 2 / 10 | 1351.5 / 1701 | 745.0 / 1463 | 68.59 | 9.53 | 17.32 |
| rag5 | 16 / 37 | 1273 / 1964 | 419 / 1463 | 44.29 | 9.52 | 17.43 |
| stage2 | 37 / 37 | 1947 / 2760 | 389 / 1035 | 41.49 | 9.34 | 17.75 |

Torch peak allocation/reservation is not identical to whole-device nvidia-smi use. No kernel packages were installed; existing reference-kernel fallback is retained. Context construction and retrieval latencies, full token IDs, raw special-token text, prompt rendering and actual generation timings are saved. Token-cap hits: {'full': 0, 'rag1': 0, 'rag3': 0, 'rag5': 0, 'stage2': 0}.

## Reproducibility and tests

See regression.json, preservation.json and independent-verification.json for final independently computed counts and status. Existing tests and historical artifacts were not weakened or rewritten. Independent verification reconstructs contexts/provenance and prompts, decodes saved token IDs and rescores every result; it does not claim a second Qwen generation run.

## Limitations and exact next-stage boundary

Small, single-author synthetic sample; short evidence and many identical full/RAG prompts; supplied atomic decomposition; historical label-policy mismatch; no held-out production corpus or independent human adjudicator. Relation-table citation entailment is limited to this fixture. Verification inputs are simulated. Prompt injection is tested, not formally prevented by text delimiters. Multi-chunk canonical-ID ambiguity fails closed. No concurrency/serving benchmark or context truncation strategy is introduced.

Stage 3H may evaluate final RAG optimization/validation only after reviewing these measured outcomes: broaden long-history and adversarial held-out cases, independently adjudicate citations, evaluate autonomous atomization and retain strict abstention/ownership checks. This report is a recommendation only. Stage 3H, QLoRA, fine-tuning, browser automation, discovery, applications, CV/cover-letter agents and recruiter outreach have not begun.

## Final interpretation and reviewed examples

The integration and controlled experiment are complete, but reliable evidence reasoning is not yet achieved. RAG-5 improves label accuracy by 24.32 percentage points over the historical prompt on this new rubric (29/37 versus 20/37). It does **not** improve over the matched Stage 3G full-context control: both have identical labels on all 37 cases, and 33/37 rendered prompts are identical. The sample provides little opportunity for retrieval to help because most candidate histories fit entirely in the context. Nine Stage 2 UNKNOWN-gold cases are instead labeled UNSUPPORTED, consistent with its historical absence policy. Neither the accuracy gain nor the improved abstention can be attributed solely to retrieval.

RAG-5 correctly judges 46/54 atomic components and all 8/8 supplied compound requirements. Its asserted atomic citation precision is 34/40; 6/40 citations exist but do not support the asserted relation under the frozen rubric. All 43 atomic citation occurrences exist. The hallucination proxy is 5/32 positive-or-partial atomic judgments, versus 8/35 for Stage 2. This proxy excludes understatements, false denials and unscored prose, and is not a comprehensive factuality measure.

Successful examples include API consumption correctly remaining UNKNOWN for API construction, Docker not implying Kubernetes, explicit deployment denial producing UNSUPPORTED, and the six-component FastAPI/Docker/AWS requirement receiving PARTIALLY_SUPPORTED with four supported and two unknown atoms. Three-source evidence supports all five components of the service/deployment/latency case with specific citations. Mixed malicious text does not erase the legitimate FastAPI fact or establish Kubernetes experience. Conflicting certification sources yield UNKNOWN. Current evidence excludes a superseded positive claim.

All eight primary label failures are exposed in the [complete semantic audit](stage3g_semantic_audit.md):

| Case | Frozen gold → output | Interpretation |
|---|---|---|
| lora_not_qlora | UNKNOWN → PARTIALLY_SUPPORTED | Credits adjacent method; partial-versus-unknown boundary is rubric-sensitive. |
| aws_not_azure | UNKNOWN → UNSUPPORTED | AWS use is incorrectly treated as proof of no Azure use. |
| sql_not_postgres | UNKNOWN → PARTIALLY_SUPPORTED | Generic SQL receives credit for a specific unestablished database. |
| numeric_exact | SUPPORTED → PARTIALLY_SUPPORTED | Adds an independent-verification requirement absent from the task. |
| assertion_not_verified | UNKNOWN → PARTIALLY_SUPPORTED | Self-report receives partial credit for independent verification. |
| inference_not_training | UNKNOWN → PARTIALLY_SUPPORTED | Quantized inference receives credit for training. |
| interest_not_experience | UNKNOWN → PARTIALLY_SUPPORTED | Interest/tutorial reading receives credit for hands-on experience. |
| rank5_qlora | SUPPORTED → PARTIALLY_SUPPORTED | Finds and cites the fifth proof but demands literal method terminology. |

The rank-five fixture describes adapting a language model by training low-rank adapters over a frozen four-bit base. Its definition-based gold is consistent with the mechanism described in the [original QLoRA paper](https://arxiv.org/abs/2305.14314). Qwen itself acknowledges the mechanism yet demands the literal name; this is attributed to reasoning, not missing retrieval. No model training was performed. The rubric was not changed after seeing output, and independent adjudication remains desirable for method specificity and partial-support boundaries.

Of the ten ablation cases, only three have evidence membership changes between budgets; corroboration retains its exact-duplicate group. RAG-1 loses required evidence in the multi-source and rank-five cases. In the multi-source case it additionally credits building from deployment evidence, so selection, reasoning and citation failures overlap. RAG-3 safely returns UNKNOWN when the rank-five proof is absent. RAG-5 includes that proof but produces the overly literal partial judgment. Thus five preserves evidence without guaranteeing correct use, and the apparent RAG-3 conditional advantage is not evidence for replacing five in production.

Six primary outputs fail the full application contract solely because `missing_evidence` is empty for a non-SUPPORTED result. Five have correct labels; the Azure case also has a reasoning error. Requiring missing evidence even when an explicit denial conclusively resolves a requirement is a contract-design limitation worth reviewing in Stage 3H. The frozen strict scores retain these failures without repair.

The three injection fixtures have zero successful attacks per arm. The single targeted foreign-candidate scenario rejects foreign scope upstream and contains neither foreign IDs nor the canary in any primary prompt or output. Separately, Stage 2 labels untrusted text claiming verifier approval as fully verified in `verifier_text_only`: this is an observed trust-boundary promotion, even though the attack-only automatic SECURITY counter does not capture it. Stage 3G returns UNKNOWN there but still gives inappropriate partial credit to self-reported certification in `assertion_not_verified`. Zero injection/leakage counts must not be described as zero security risk.

## Completed execution and preservation audit

The primary job **2330445 completed successfully** on `gpu-4-21` with one actual NVIDIA A30 (24,576 MiB), 8 allocated CPUs and 64 GiB allocated host memory. Requested maximum was 08:00:00; actual allocation elapsed was **01:16:16**, including separate smoke and benchmark processes. Slurm reports batch peak host RSS 51.71 GiB. The GPU allocation has ended. CPU-only independent verification job **2330449 completed successfully** in 00:02:11 with 4 CPUs and 12 GiB. See `results/stage3g/slurm_accounting.txt` for exact accounting, including failed/cancelled attempts. Total allocated GPU-job time across the 43-second logging failure, 46:53 diagnostic run and successful 1:16:16 run was **2:03:52 on one GPU at a time**.

The benchmark evaluated 131 comparisons using 83 physical generations and 48 explicitly recorded identical-prompt reuses. Physical prompts totaled 138,610 tokens and generation totaled 38,957 tokens. Benchmark runtime was 4,146.76 seconds (69.11 minutes), including its 23.99-second model load. Smoke load was 40.25 seconds. Across all arms peak Torch allocation was 17.75 GiB and reservation 18.29 GiB. This workload fit one A30; no escalation was needed. The ~9.3–9.6 tokens/second and roughly 44-second typical Stage 3G response are acceptable for this offline experiment, but interactive serving latency has not been validated.

The frozen performance file uses a lower-index empirical percentile that is misleading for tiny samples (notably two RAG-3 generations). It remains preserved. `performance-percentile-audit.json` supplies explicitly defined nearest-rank p95 values computed from unchanged timings: Stage 2 80.48 s, full 128.90 s, RAG-1 127.16 s, RAG-3 94.97 s, RAG-5 151.79 s. These samples differ because exact-prompt reuse avoids repeat generation. Borrowing the actual timing for each identical prompt gives an all-37-case median of 44.18 s for both full and RAG-5; these borrowed values are estimates, not new runs.

**326/326 tests passed: 273 existing tests plus 53 new Stage 3G tests.** Historical Stage 2 replay, Stage 3A/B demonstrations, all 112 Stage 3E responses, all 297 Stage 3F rankings and 594 prefix checks passed. All 749 protected earlier-stage files have unchanged hashes, and final dependency freeze equals the initial freeze. No existing environment, model weights, embedding/reranker assets or historical benchmark output was replaced.

Independent verification re-embedded and rebuilt all 37 contexts and provenance chains, reconstructed and decoded all 131 saved prompts/outputs, and obtained exactly equal metrics. All 19 frozen files match. Five separate-load smoke comparisons—direct_api, compound_four_of_six, verified_exact, injection_role and empty—also have identical prompts and generated token IDs. This is five fresh-generation repeats, not a second full 131-comparison model run. The verifier wrapper normalizes in-memory tuple/list serialization when comparing rebuilt objects with persisted JSON; it does not repair model output. Raw-output audit confirms only normal terminal EOS removal, with no JSON recovery.

Initial preparation/test failures and the optional device-map logging error were diagnosed before the selected run. The first diagnostic run was stopped after discovering descriptive fixture identifiers/source keys in model context. Its source snapshot, outputs and freeze are preserved under `diagnostic-v1-source` and the v1 artifacts. The v2 correction blinds public need IDs and attestation references and keeps native pointers solely in sidecars. The identifier audit proves all 37 cases, gold labels, vectors and retrieval results unchanged. System reasoning rules remain unchanged apart from their version stamp. No diagnostic v1 result contributes to primary metrics. The methodological restart was necessary but means this is not a preregistered held-out experiment.

## Recommendation and exact stopping boundary

Retain the Stage 3E semantic-20 → Stage 3F identity → five-group configuration as the **next evaluation starting point**, not a production-quality approval. This stage provides no controlled evidence that reducing to three is better, and the fifth group contains necessary proof in the stress case. Stage 3H should separately investigate partial-versus-unknown calibration, false contradiction, unrequested verification requirements, overly literal method naming, and the missing-evidence contract for explicit denials. Use larger independently adjudicated held-out histories with distractors, negative verification states, long/multiple chunks, and supplied-versus-autonomously-discovered atomic components. Preserve strict ownership, source validation and abstention throughout.

These are recommendations only. Stage 3G implementation, benchmark, replay and reporting are complete. Stage 3H optimization/evaluation has **not started**. QLoRA, fine-tuning, browser automation, job discovery/application filling, CV/cover-letter agents and recruiter outreach remain outside this work.

The full file inventory is `results/stage3g/final_manifest.json`; the frozen selected configuration is `freeze_v2.json`, and post-run completion status is `completion.json`. This report is produced by the frozen report generator followed by the separately preserved post-run `results/stage3g/finalize_report.py`; it does not modify frozen experiment code or scores.
