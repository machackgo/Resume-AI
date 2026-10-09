# Resume AI Stage 2 engineering report

**Completed: prompt engineering and structured output only.** Final prompt: `grounded_v3`. Final run: `results/prompt_engineered/grounded-v3-benchmark-2325384-1`. Base run: `results/baseline/base-v1-2325384-eval3`.

The same untouched Qwen model now returns raw schema-valid JSON on all eight cases and produces no unsupported text in nine qualitatively reviewed bullets. Requirement, skill and gap extraction reach 100% F1 on this small set. However, support-label accuracy worsens, and one fully supported accomplishment is incorrectly refused. Prompting improved output reliability and conservatism, but it did not solve evidence understanding.

## 1. Baseline recap and failure taxonomy

Baseline strict JSON/schema validity was 0/8 because every response contained Markdown fences. After diagnostic fence removal, requirement F1 was 97.56%, skill F1 91.43%, missing-requirement F1 100%. A qualitative assistant review found unsupported additions in 2/11 bullets.

Failure classes: raw formatting noncompliance; UNKNOWN facts or tutorial-only familiarity appearing as candidate skills; ambiguous distinction between partial support, absent support and uncertainty; compound claims treated as indivisible; citations appearing correct while generated prose adds unsupported activities or outcomes. The existing citation scorer cannot verify prose entailment.

## 2. Controls, schema and strategy

Dataset, expected answers, schema, base prompt and deterministic scorer were preserved byte-for-byte. All original baseline artifacts were protected by a pre-stage manifest. Same local model `/scratch/mohammedmubashir/resume-ai/models/Qwen3.8-27B`, text runtime `Qwen3_5ForCausalLM`, NF4 4-bit double quantization, BF16 compute/model dtype, device_map auto, local-only loading, seed 42, thinking disabled, greedy generation, use_cache true and max_new_tokens 1536. Same installed environment: Python 3.11.12, torch 2.14.0, transformers 5.17.0, accelerate 1.15.0, bitsandbytes 0.50.2, tokenizers 0.23.2. No weights changed or downloaded, no installations, no adapters, RAG or fine-tuning.

Prompt architecture: versioned `system.txt` behavior contract; `task.txt` task instructions; separately named JSON input sections for candidate evidence, job description, candidate request, proposed claims, vocabulary, and the unchanged schema. No case IDs, gold labels, gold citation sets, or benchmark answers enter the assembled prompts. The vocabulary remains the same global closed vocabulary used by the baseline. Input serialization changes are part of the prompt intervention.

Rules require exactly one JSON object, supported skills only, no adjacent-technology substitution, classification of each atomic component, minimal evidence-entailing bullets, refusal of all non-fully-supported proposed claims, and original stated quantities in generated bullets. Exact arithmetic can still entail an already proposed claim for classification; generation preserves original quantities to satisfy the stricter metric instruction. This is an intentional wording constraint, not a gold-label change.

No schema change: skills still lacks a support/proficiency field, atomic claim alignment is not structurally exposed, exact negative citation sets can be debatable, and IDs are only weakly typed. Those limitations are documented before implementation in `eval/experiments/stage2/design.md`.

Installed Transformers exposes token-filter/logits-processor hooks but no ready JSON-schema generation interface in the inspected generation module; outlines/xgrammar/lm-format-enforcer are absent. The simplest instruction-only approach was tried first and passed formatting. No fence stripping, JSON repair, prefill, grammar decoding or retries were used for primary metrics. Tokenizer special-token handling is identical to baseline.

## 3. Development loop and freeze

One separate synthetic R/reporting smoke case was used; it is not part of the eight-case benchmark. v1 passed formatting and avoided invented metrics, but classified a supported-plus-denied compound as wholly UNSUPPORTED. v2 clarified atomic precedence but the same failure remained; the actual rendered v2 prompt was verified, ruling out a stale-prompt error. v3 added a general symbolic A-AND-B decision table and an UNSUPPORTED-label audit, without answer-specific facts. The compound became PARTIALLY_SUPPORTED while its unsafe complete claim remained refused.

All three prompt versions and smoke results are retained. The standalone deployment smoke requirement still disagrees with its partial-support gold label; given explicit non-deployment, UNSUPPORTED is defensible. That rubric issue was documented, not relabeled. v3 was frozen with source hashes, smoke provenance and review before the full benchmark. The unchanged benchmark was run once. No full-benchmark failure was used to revise the prompt.

## 4. Side-by-side metrics

Primary strict metrics parse the model's decoded response as generated. Base fence diagnostics are context only; all base strict task scores remain zero and parsed bullet rates undefined. Prompt diagnostics equal prompt strict metrics because no fences were present. Extraction metrics are micro-averaged; label/citation accuracy and coverage retain the original macro definitions.

| Metric | Base strict | Base fence diagnostic | Prompt strict |
|---|---:|---:|---:|
| JSON validity | 0.00% | 100.00% | 100.00% |
| Schema validity | 0.00% | 100.00% | 100.00% |
| Requirement precision | 0.00% | 100.00% | 100.00% |
| Requirement recall | 0.00% | 95.24% | 100.00% |
| Requirement f1 | 0.00% | 97.56% | 100.00% |
| Skill precision | 0.00% | 84.21% | 100.00% |
| Skill recall | 0.00% | 100.00% | 100.00% |
| Skill f1 | 0.00% | 91.43% | 100.00% |
| Missing requirement precision | 0.00% | 100.00% | 100.00% |
| Missing requirement recall | 0.00% | 100.00% | 100.00% |
| Missing requirement f1 | 0.00% | 100.00% | 100.00% |
| Requirement label accuracy (macro) | 0.00% | 85.42% | 77.08% |
| Claim label accuracy (macro) | 0.00% | 95.83% | 91.67% |
| Requirement evidence attribution (macro) | 0.00% | 95.83% | 100.00% |
| Claim evidence attribution (macro) | 0.00% | 95.83% | 95.83% |
| Citation/claim-ID grounded bullet rate | N/A | 90.91% | 100.00% |
| Non-fully-supported cited claim rate | N/A | 9.09% | 0.00% |
| Job coverage proxy (macro) | 0.00% | 39.58% | 31.25% |
| Parsed bullet count | 0 | 11 | 9 |
| Citation/claim-ID grounded bullet count | 0 | 10 | 9 |
| Non-fully-supported cited claim count | 0 | 1 | 0 |
| Bullet claim selection precision | 0.00% | 90.91% | 100.00% |
| Bullet claim selection recall | 0.00% | 100.00% | 90.00% |
| Bullet claim selection f1 | 0.00% | 95.24% | 94.74% |
| Refusal precision | 0.00% | 100.00% | 93.33% |
| Refusal recall | 0.00% | 92.86% | 100.00% |
| Refusal f1 | 0.00% | 96.30% | 96.55% |

Strict base parsed unsupported count 0 is not evidence of zero hallucination: there were no schema-valid parsed bullets. The base diagnostic non-fully-supported claim-ID count of 1 concerns a partial compound citation, not necessarily unsafe prose.

Supplementary promotion metrics were defined separately without changing the scorer:

| Promotion measure | Base strict | Base diagnostic | Prompt strict |
|---|---:|---:|---:|
| Gold UNKNOWN match/claim labels promoted to SUPPORTED | N/A | 0/6 (0%) | 0/6 (0%) |
| Gold PARTIALLY_SUPPORTED labels promoted to SUPPORTED | N/A | 0/5 (0%) | 0/5 (0%) |
| UNKNOWN requirement IDs asserted in skills | N/A | 2/3 (66.67%) | 0/3 (0%) |
| PARTIALLY_SUPPORTED requirement IDs asserted in skills | N/A | 1/3 (33.33%) | 0/3 (0%) |

These skill measures are exact-ID proxies over gold non-fully-supported requirements absent from gold skills, not universal semantic promotion rates. All eight diagnostic/base and strict/prompt cases are evaluable; no required match/claim predictions are missing or duplicated. Incorrect transitions to other non-supported labels remain errors even when SUPPORTED-promotion rates are zero.

## 5. Atomic semantic audit and fixes

The same qualitative material-addition standard was applied by the primary engineering assistant, not an independent human or calibrated judge. Baseline: 9 grounded / 11 bullets, 2 unsupported / 11 (18.18%). Prompt: 9 grounded / 9 bullets, **0 unsupported / 9 (0%)**. Every new bullet has an explicit atomic breakdown, cited IDs, and actual evidence text in `semantic_audit.json`. There are no remaining unsupported generated bullets to enumerate. The smaller output count and lost supported claim must be considered alongside the zero rate.

**Fixed by a weaker grounded statement:** baseline “Utilized Python for data processing and analysis tasks.” cited E1 and E2, which only reported conflicting five-year versus one-year Python tenure. Python experience was supported; data-processing and analysis activities were not. Stage 2 says “Has Python experience.” with E1/E2, avoiding both invented tasks and a resolved tenure claim.

**Removed rather than safely rewritten:** baseline “Analyzed 12,000 synthetic transactions using Python and SQL to extract insights and validate data integrity.” cited E1: “Used Python and SQL to analyze 12000 synthetic transactions in a personal project.” Analysis, quantity, and tools were supported; data-integrity validation was not. Stage 2 emits no bullet for this case. It wrongly downgrades the supported core claim to PARTIALLY_SUPPORTED, so the unsupported validation disappears at the cost of losing valid content.

Other fixes: unknown Python and certification details no longer appear in skills; tutorial-only AWS is excluded from skills; automation is no longer omitted as a requirement; a partial Azure-and-AWS claim is refused and no longer used as a bullet citation. Fabricated credentials, employment and unmeasured savings remain rejected. The supported 5-to-2-hour evidence is retained literally rather than converted into a new percentage.

## 6. Remaining failures and regressions

- Requirement support-label accuracy falls **85.42% to 77.08%**. Team leadership changes from correct PARTIALLY_SUPPORTED to UNSUPPORTED; ambiguous Python changes from correct UNKNOWN to UNSUPPORTED. Production ML and tutorial AWS remain UNSUPPORTED rather than gold PARTIALLY_SUPPORTED.
- Claim label accuracy falls **95.83% to 91.67%**. The trained-and-deployed compound is fixed, but ambiguous Python backend work changes from UNKNOWN to PARTIALLY_SUPPORTED, and the supported transaction-analysis claim changes to PARTIALLY_SUPPORTED.
- Supported bullet selection recall falls **100% to 90%**, F1 **95.24% to 94.74%**. Refusal precision falls **100% to 93.33%** because a supported claim is refused; refusal recall improves to 100%.
- Job coverage proxy falls **39.58% to 31.25%**, driven by the missing supported analysis bullet. More refusals cannot be treated as unconditional improvement.
- Claim evidence attribution remains 95.83%: citing E1 for the unmeasured savings claim differs from the empty gold set, though E1 is a defensible explanation of non-support. Gold was not revised.
- Atomic checking exists only in instructions, not as an enforceable output structure. Apparent correct citations still require semantic review. The hypothesis that the symbolic audit increases conservatism is consistent with the results, but no component ablation establishes causality.

All per-case differences are recorded in `comparison/independent_verification.json`.

## 7. Tests and independent verification

Nineteen CPU tests pass locally and remotely: all nine original tests retained plus strict plain-JSON acceptance, fenced/preamble/trailing-prose rejection, unsupported/partial/unknown bullet detection, promotion denominators, invalid-output handling, no gold leakage, original file hash preservation, exclusive run writing, separate smoke data, prompt template checks, and read-only comparison tests. A test-development false positive initially treated the ordinary word “adjacent” as a leaked case ID; the check was corrected to detect structured ID references, while full evidence-string and gold-mutation leakage tests remain. No evaluator test was weakened.

All smoke runs and the full benchmark were independently replayed from raw response text with their frozen scorer/source snapshots; parsed predictions and strict metrics reproduced exactly. A second implementation independently checked JSON/schema counts, micro precision/recall/F1, and citation/claim-ID bullet counts for both models in strict and diagnostic modes. Comparison control assertions all passed. The login-node guard rejects before importing Torch or creating an output directory. Final preservation checks cover every previously protected file, the entire baseline file inventory, frozen source hashes and unchanged model shard sizes/timestamps. Weight contents were not redundantly hashed or copied.

## 8. Slurm and performance

Reused valid, idle allocation 2325384 on gpu-4-21, account cs541, partition academic; original bash step .0 left running. Each inference step used one NVIDIA A30 24 GB and four CPUs, with the allocation's existing 64 GB host memory. No login-node model execution. Completed steps: .9 v1 smoke (1m29s), .11 v2 smoke (1m31s), .13 v3 smoke (2m20s), .15 full benchmark (6m17s), all exit 0. Read-only nvidia-smi steps checked allocation idleness; no unrelated job was terminated.

| Performance | Base | Prompt v3 |
|---|---:|---:|
| Input tokens, all 8 cases | 6,798 | 15,312 |
| Output tokens | 3,336 | 3,199 |
| Generation seconds, including prefill | 352.49 | 345.24 |
| Output tokens/sec | 9.46 | 9.27 |
| Model load seconds | 24.14 | 24.19 |
| Peak allocated GPU GiB | 16.99 | 17.42 |
| Output token-limit hits | 0 | 0 |

The larger prompt costs more input tokens and slightly reduces output throughput; total generation time is lower because fewer tokens are generated. This is not a repeated performance study. The existing optional causal_conv1d and flash-linear-attention kernel warnings persist; reference implementations were retained. Slurm accounting also recorded a higher transient host MaxRSS in v3 smoke (~53.6 GiB); that recorded peak was below the 64 GB allocation, and all inference steps completed successfully. All parameters remained on cuda:0.

## 9. Files and reproduction

No pre-Stage-2 project file or baseline artifact was modified. New evaluation files:

- `eval/prompts/grounded_v1/{system.txt,task.txt}`
- `eval/prompts/grounded_v2/{system.txt,task.txt}`
- `eval/prompts/grounded_v3/{system.txt,task.txt}`
- `eval/experiments/stage2/design.md`, `smoke_v1.json`, `smoke_review_v1.md`, `smoke_review_v2.md`, `smoke_review_v3.md`, `freeze_grounded_v3.json`, and `report.md`
- `eval/metrics/promotions_v1.py`
- `eval/runners/prompt_contract.py`, `run_prompt_engineered.py`, `prompt_engineered.slurm`, `reuse_prompt_allocation.sh`, `compare_stage2.py`, `verify_stage2_run.py`, `freeze_prompt.py`
- `eval/tests/test_stage2.py`, `test_stage2_comparison.py`

New results live only under `results/prompt_engineered/`: the pre-stage control manifest, initial source transfer archive, three smoke run directories/logs, and the final benchmark directory/log. Each run has config, raw_outputs.jsonl, predictions.jsonl, metrics.json, summary.md, source snapshot, and control manifest. Final comparison adds machine-readable comparisons, metrics table, independent verification, semantic audit, engineering report, Slurm accounting, preservation/test verification, and postprocessing source. The full exact file inventory is `verification.json`; runtime bytecode caches are excluded from that inventory. Stage-2-only runner files evolved to support prompt versions; their earlier contents remain in each smoke snapshot.

From the existing remote project, CPU-only checks:

```
.venv/bin/python -m unittest discover -s eval/tests -v
.venv/bin/python eval/runners/verify_stage2_run.py results/prompt_engineered/grounded-v3-benchmark-2325384-1
```

For a future reproduction, use a new run ID and a valid idle Slurm allocation:

```
bash eval/runners/reuse_prompt_allocation.sh JOB_ID benchmark NEW_UNIQUE_RUN_ID grounded_v3
```

Or submit `sbatch eval/runners/prompt_engineered.slurm benchmark grounded_v3` using the cluster's full Slurm binary path. The runner checks the frozen prompt/source and unchanged controls; it refuses existing run directories. The reuse script refuses existing log files. Do not rerun the freeze command or overwrite the recorded run. `compare_stage2.py` writes only to a new candidate comparison directory and verifies baseline controls. Raw outputs, token IDs, complete rendered prompts, metadata, hashes, GPU information and timing remain available for reproduction.

## 10. Conclusions and next experiment candidates — not started

**Structured output:** instruction-only prompting was sufficient for 8/8 raw valid objects in this run, with no repair or decoding constraints. This establishes observed success, not a format guarantee on unseen inputs. Grammar-constrained decoding is a candidate if a hard API guarantee is needed.

**Evidence grounding:** prompting eliminated observed unsupported bullet additions and unsafe skill promotions on this small dataset, but was not sufficient for accurate end-to-end evidence reasoning. It traded unsupported additions for over-refusal and inconsistent support labels. It is not ready to be trusted as a production grounding mechanism based on these results alone.

Next candidates: first adjudicate the support taxonomy on atomic compound claims, contradictory evidence, weaker experience, and tutorial familiarity; evaluate the frozen prompt on a new, independently authored held-out set; then test an explicit atomic evidence ledger or verifier that preserves supported content without allowing unsupported clauses. Treat any schema/scorer revision as a separately versioned comparison rather than rewriting these results. A grammar-decoding ablation can isolate formatting guarantees from grounding. Optional kernel acceleration should be evaluated separately under identical model/prompt settings. These findings do not yet identify missing knowledge as the dominant failure, so neither RAG nor QLoRA is justified as an automatic next step.

**Stopped after Stage 2. No RAG, embeddings, vector database, training, or application-agent work was started.**
