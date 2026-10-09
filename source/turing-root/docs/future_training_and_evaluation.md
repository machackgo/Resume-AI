# Future experiment design — no training executed

This document specifies a proposed, separately authorized experiment. It is not authorization to train, and a dataset failing the Stage 4C-0 release gates must not enter it. The existing Stage 4B adapter is an engineering smoke artifact, not an evidence-trained scientific baseline.

## Minimal comparison

Keep Base Qwen plus the frozen Stage 3J RAG as an unchanged control. Compare two newly trained, separately authorized adapters from the same frozen base: an evidence-only Stage 4A arm, and an interleaved Stage 4A plus professional arm. Keep optimizer, seed, effective batch, supervised-token budget, evaluation inputs and decoding constant where technically possible. Do not merge adapters. A professional-only arm or staged curriculum is a later ablation, not required for the first experiment.

Use immutable Stage 4A v1 paths by reference, never rewrite its files. For the interleaved arm, begin with 50% Stage 4A and 50% professional assistant-target tokens. This is a conservative experimental choice, not an empirically established optimum. Sample by supervised-token mass rather than concatenating rows, because professional responses are longer. Within professional tokens propose: whole resume 20%, semantic application answers 15%, candidate mapping 15%, job analysis 10%, content selection 10%, section generation 10%, cover letters 8%, missing-information routing 7%, bullet rewriting 3%, outreach 2%. Retain all six section variants under one section discriminator. Never train on validation, test, challenge, critique, oracle, rejected targets or generation receipts.

Interleave throughout to reduce the risk that a final prose-only phase erodes grounding. Do not repeatedly replay a tiny seed curriculum to meet an arbitrary large step count. After the actual accepted pool and token report are available, cap the first experiment at one pass-equivalent over its professional training targets; match the evidence-only arm's supervised-token budget. Use validation for checkpoint selection. Run sealed test and external challenge evaluations once for the chosen checkpoint, and report uncertainty rather than tuning against them.

## Sequence and supervision

Use the real local Qwen tokenizer and unchanged Stage 4A chat serialization, with `enable_thinking=False`. Mask every system, user and RAG token from loss. Supervise only the assistant JSON and its end marker. Keep concise observable trace fields, final content and application-level claim citations; exclude hidden reasoning and critic explanations. Grounding citations remain outside user-visible rendered content.

The engineering history establishes complete optimizer steps at 4,233 tokens and forward/backward at a 4,608-token tensor envelope. It does not establish all-active 4,608-token optimization. Use 4,233 as the conservative complete-example ceiling until a separate engineering experiment establishes otherwise. No silent truncation is permitted. Oversize examples require coherent task decomposition and fresh generation/critique: content selection, section output, or a bounded whole artifact. Retain whole-resume examples for chronology, allocation and redundancy; isolated bullets cannot substitute for them.

## Catastrophic regression gate

Reject any professional checkpoint with an observed critical violation on the registered adversarial suite: invented metric, technology substitution, action inflation, employer/degree/credential fabrication, cross-candidate evidence, unsupported authorization/preference, injection obedience or fabricated tool execution. Require 100% schema validity, exact numeric and technology fidelity on that finite suite. Zero observed violations is a finite-sample finding, not a universal guarantee.

On the untouched Stage 4A test set and historical evidence benchmarks report macro label accuracy, UNKNOWN/UNSUPPORTED confusion, citation entailment, numeric fidelity, technology fidelity and isolation separately. Pre-register a maximum two percentage-point paired macro-accuracy loss versus the evidence-only arm. Report paired bootstrap confidence intervals and discordant cases; if uncertainty cannot exclude a material five-point loss, expand a separately authored evidence evaluation set before acceptance. Do not relax thresholds after seeing test results. Professional improvement cannot compensate for a critical truth failure.

## Professional evaluation

Report task-specific denominators and confidence intervals for grounding, hallucinated-claim rate, numeric fidelity, technology fidelity, schema validity, supported requirement coverage, supported keyword alignment, evidence utilization, content selection, professional writing, concision, redundancy, cover-letter specificity, application-answer grounding, correct abstention and outreach personalization. Distinguish available supported requirements from unsupported JD requirements: omission of unsupported skills is correct, not failed coverage.

Use deterministic checks plus blinded independent rubric judgments. Randomize model labels; do not give judges hidden generator reasoning. Score professional prose only after truth gates pass. The small evaluation splits provide diagnostic evidence, not precise production-quality estimates. Audit sample disagreements and report judge limitations; model confidence is not evidence of correctness.

ATS evaluation here is structured-output parsability, conventional headings, complete text fields, predictable dates, supported skills, no decorative or hidden keywords, and future deterministic-template compatibility. No universal ATS score, parser guarantee or hiring-outcome claim is valid. Future PDF/DOCX rendering needs its own text-extraction, reading-order and accessibility evaluation.

## Application boundary

Future flow: discovered job → analyze job → map evidence → select content → generate resume → optional letter and application answers → deterministic File Generator → Browser Agent → stop/review before submission → optional contact selection by Outreach Agent → grounded outreach draft → review/send policy → persist application state.

Qwen does not discover contacts, browse, click, upload, submit, send messages, persist preferences or maintain a continuous loop. The future orchestrator owns run modes of one, ten, twenty, thirty or continuous-until-stopped applications, cancellation, retry and review policy. Exact profile fields are filled deterministically; missing personal or legal facts require user input. Contact context is supplied, never hallucinated. This stage implements none of those agents or rendering tools.
