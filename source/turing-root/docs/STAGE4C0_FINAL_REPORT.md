# Resume AI — Stage 4C-0 final report

A. PROFESSIONAL CURRICULUM READY FOR QLORA TRAINING

Completed 2026-09-30 UTC. This is a research, data, audit and evaluation-design release. No QLoRA, optimizer updates, adapter creation/merge, model-weight modification, RAG changes, browser/job agents or deployment were performed.

## Decision and scope

Freeze the audited **149-example professional curriculum** (119 train, 14 validation, 16 test) plus **6 independently reviewed challenge references**. Preserve all ten original external challenge inputs separately; four references remain unscored and quarantined. The 18-example development pilot is separate and excluded from SFT. This is suitable for a small controlled experiment, not proof of professional competence or saturated coverage.

The smallest known factory defects are incomplete requirement-support whitelists and ambiguous expected completion statuses in ten excluded scenarios. They cannot override accepted-target truth checks. Six training mapping scenarios and four challenge references are excluded. Their raw outputs, oracle disagreement and reasons remain available; no disputed label was forced, no ground truth was retrofitted, and no excluded artifact is a training target.

## Research and domain design

See [methodology and limitations](final_methodology_and_limitations.md), [research report](../research/stage4c0/research_report.md), [source manifest](../research/stage4c0/sources.jsonl), [curriculum design](curriculum_design.md), and [factory change record](validator_v2_final_scope.md). These are substantive parts of this report. The research snapshot contains 30 primary sources and 65 normalized principles across ATS parsing, resumes, technical resumes, job interpretation, letters, applications, outreach, truthfulness, recruiting conventions and accessibility. Sources retain access/date/confidence/context/licensing provenance. Most verification used indexed page text; no complete copyrighted source corpus was collected.

Conservative defaults: conventional headings, linear machine-readable structured fields, consistent chronology and supported terminology. No universal ATS score or parser guarantee. Resume length and summaries depend on experience/context. PDF/DOCX rendering is future deterministic File Generator work; this release tests structured content, not actual ATS ingestion. Strong prose must preserve action strength, exact metrics, technologies, credentials and employment. Company culture, referrals and personal/legal answers cannot be guessed.

## Tasks, contracts and quality control

Ten stable task discriminators use versioned JSON schemas: ANALYZE_JOB, MAP_JOB_TO_CANDIDATE, SELECT_RESUME_CONTENT, GENERATE_RESUME, GENERATE_RESUME_SECTION, REWRITE_BULLET_FOR_JOB, GENERATE_COVER_LETTER, ANSWER_APPLICATION_QUESTION, IDENTIFY_MISSING_INFORMATION and DRAFT_OUTREACH. Six section variants cover Summary, Skills, Experience, Projects, Education and Certifications. Full schemas, rubrics and prompts are packaged in `contracts/`; task-specific externally meaningful decisions precede/ accompany artifacts in compact trace fields. No private chain-of-thought is generated or stored.

Ground truth is authored first. Typed synthetic profile facts, evidence IDs, source lineage, exact-support attestations and event scope constrain every target. The frozen-RAG bridge round-trips production-compatible typed messages and supports; it is a fixture resolver, not a new retrieval implementation or an end-to-end MiniLM/vector-store demonstration. Retrieved text remains untrusted, including injection fixtures.

Teacher configuration requested gpt-6-astra/ultra; independent critic invocations use the same requested model family with separate requests. Actual runtime model identity, provider token billing and cost were unavailable and remain null. Teacher v2, critic v1, schema/rubric v1 and validator v2 are versioned. Maximum two revision loops; this full pool used at most one. A critic cannot override deterministic rejection. Independent does not mean independent model-family errors.

Hard gates: schema, IDs/ownership, exact numeric/technology fidelity, event-scoped employer/title/date/degree/credential fidelity, claim citations, task/status consistency, user constraints, injection resistance, split/provenance/hash checks and complete-token ceiling. Every accepted target has an independent leaf/atom audit. Grounding must score 4/4; other rubric dimensions at least 3/4 and mean at least 3.5. Weak writing, generic phrasing, poor selection and redundancy trigger revision; factual failures are never averaged away.

## Pilot and version lineage

18 distinct pilot cases across all ten tasks; 25 generation attempts, 21 accepted attempts, four rejected attempts, four revision attempts and three superseded accepted versions. Final selection is 18. Original failures included UNKNOWN mapping support arrays and incomplete missing-information routing. Teacher v2 clarifies those interface rules. Pilot standalone validation, historical exclusion, assistant-only masking and real Qwen tokenization passed; maximum 2,729 tokens.

Factory v1 source and checksum snapshot are retained. During full validation, bounded validator repairs were explicitly versioned as factory/validator v2: education credential-field compatibility, synthetic-history origin projection, instrument/education-noun action disambiguation, conservative courtesy-language handling and exact-message-bound token preflight. Research, schemas, rubrics, scenario truth and immutable teacher outputs did not change. All selected targets were revalidated under v2; the v2 snapshot is a post-repair snapshot, not a claim that it predated original full generation.

## Full generation and rejection accounting

165 distinct inputs, **184 generation attempts**, **155 accepted targets**, **29 rejected attempts**, **19 revision attempts**. Attempt acceptance 84.24%; unique scenario acceptance 93.94%. Rejection counts include scenario/oracle disagreements, citation-scope defects, job-number representation, wording/grounding issues and one token overflow; they are not all fabricated claims.

| Task | Attempts | Accepted unique | Rejected attempts | Revisions |
|---|---:|---:|---:|---:|
| ANALYZE_JOB | 11 | 10 | 1 | 1 |
| ANSWER_APPLICATION_QUESTION | 22 | 19 | 3 | 0 |
| DRAFT_OUTREACH | 6 | 5 | 1 | 1 |
| GENERATE_COVER_LETTER | 15 | 12 | 3 | 3 |
| GENERATE_RESUME | 40 | 38 | 2 | 1 |
| GENERATE_RESUME_SECTION | 12 | 12 | 0 | 0 |
| IDENTIFY_MISSING_INFORMATION | 14 | 14 | 0 | 0 |
| MAP_JOB_TO_CANDIDATE | 42 | 24 | 18 | 12 |
| REWRITE_BULLET_FOR_JOB | 10 | 9 | 1 | 1 |
| SELECT_RESUME_CONTENT | 12 | 12 | 0 | 0 |

Accepted examples have zero known hard-grounding failures, numeric mismatches, technology substitutions or cross-candidate contamination. Schema validity and these finite accepted-set checks are 100%. This does not imply an unknown population failure rate is zero. Per-task critic dimensions and accepted fidelity rates are in [statistics](../datasets/stage4c0/v1/statistics.json); raw hard errors remain in `attempts.jsonl`. Initial/final attempt binding prevents hiding failed generations.

## Coverage, diversity and exclusions

The main prospectively authored input catalog contains 37 families and 45 candidate variants, with degree-free, non-CS, graduate and varied career histories. The final counts below include six scored external references. All ten role families, all ten tasks in each main split, all six section variants, five seniority groups and four fit levels are represented. This is breadth, not saturation. The dataset is intentionally a compact seed release; no learning curve proves that 119 training examples are sufficient for final product mastery. Future expansion should target documented sparse cells rather than duplicate successful templates.

| Role family | Accepted records |
|---|---:|
| AI Engineer | 18 |
| Applied Scientist | 12 |
| Backend / ML Platform Engineer | 18 |
| Data Scientist | 27 |
| Generative AI Engineer | 12 |
| MLOps Engineer | 16 |
| Machine Learning Engineer | 16 |
| NLP Engineer | 10 |
| Research Engineer | 11 |
| Software Engineer — AI | 15 |

**seniority:** early_career: 49; entry_level: 22; mid_level: 52; senior: 17; student_new_graduate: 15.

**fit_level:** mixed: 28; moderate: 49; strong: 66; weak: 12.

**difficulty:** hard: 120; standard: 35.

**technology_tags:** AWS: 7; Azure: 18; CI/CD: 20; Docker: 28; FastAPI: 19; Flask: 15; GCP: 11; Kubernetes: 15; LLMs: 12; LoRA: 8; PostgreSQL: 21; PyTorch: 29; Python: 85; QLoRA: 4; RAG: 17; REST APIs: 18; React: 2; SQL: 55; TensorFlow: 12; evaluation: 73; inference: 12; monitoring: 8; training: 8; vector databases: 3.

**action_tags:** built: 85; collaborated: 51; consumed: 6; credential: 10; deployed: 32; designed: 34; evaluated: 74; fine-tuned: 8; implemented: 77; instruction: 3; led: 8; operated: 30; optimized: 17; studied: 15; trained: 14; used: 55.

**trust_tags:** AUTHENTICATED: 155; CANDIDATE_ASSERTED: 9; EXTERNAL_OBSERVED: 155.

Detailed candidate/job/template distributions, lexical counts and exposure tags are in statistics.json. Tags are descriptors, not independent proof of claims. Same candidate facts intentionally recur across different tasks only within a split. One near-duplicate whole-resume/Experience-section pair is retained to teach distinct output scopes; same family and split. No cross-split near-artifact pair reached the registered 0.80 five-gram Jaccard review threshold. Exact and normalized input/output and candidate-job-task duplicate results are recorded.

Group isolation covers scenario family, candidate/job archetype, template family, counterfactual group, split group and actual candidate/job identity. Zero known prohibited leakage. Historical audit fingerprints 1,621 Stage 3 context strings and 380 Stage 4A test context strings; no exact/high-overlap matches. Historical outputs were never given to the teacher. Lexical checks cannot prove semantic independence. All original challenge inputs remain isolated. No real-public-job evaluation corpus was redistributed: rights were unclear, so original synthetic reconstructions were used.

## Token and sequence analysis

Real local Qwen tokenizer and unchanged chat template; thinking disabled; system/user/RAG tokens masked, assistant structured JSON plus completion terminator supervised. No truncation or model weights loaded. Each record binds token counts and tokenizer fingerprints to exact messages.

| Task | Median total | Mean total | p90 | p95 | p99 | Maximum |
|---|---:|---:|---:|---:|---:|---:|
| ANALYZE_JOB | 1021.5 | 1030.5 | 1170 | 1171 | 1171 | 1171 |
| ANSWER_APPLICATION_QUESTION | 1568 | 1622.7 | 1923 | 1973 | 1973 | 1973 |
| DRAFT_OUTREACH | 2165 | 2197.8 | 2666 | 2666 | 2666 | 2666 |
| GENERATE_COVER_LETTER | 2038.0 | 2047.4 | 2342 | 2433 | 2433 | 2433 |
| GENERATE_RESUME | 2098.0 | 2209.7 | 2775 | 2854 | 4157 | 4157 |
| GENERATE_RESUME_SECTION | 1909.5 | 1886.9 | 2140 | 2327 | 2327 | 2327 |
| IDENTIFY_MISSING_INFORMATION | 1527.5 | 1563.9 | 1711 | 1928 | 1928 | 1928 |
| MAP_JOB_TO_CANDIDATE | 1779.0 | 1797.3 | 2063 | 2115 | 2224 | 2224 |
| REWRITE_BULLET_FOR_JOB | 1682 | 1720.8 | 2189 | 2189 | 2189 | 2189 |
| SELECT_RESUME_CONTENT | 2101.5 | 2180.9 | 2578 | 3774 | 3774 | 3774 |

Overall median/p50 1859, mean 1870.92, p90 2374, p95 2578, p99 3774, max **4157**, total 289,992 tokens. Input and target means/medians/p90/p95/p99/max appear separately for every task in statistics.json. Assistant targets total 71,958 tokens; TRAIN targets total **55,115**.

Stage 4B demonstrated a 4,608-token tensor forward/backward envelope, but complete optimizer examples reached 4,233. This release uses the conservative 4,233 limit. One original resume was 4,261; bounded teacher revision reduced it to 4,157 while preserving required sections and exact facts, then an independent critic and real-token audit passed. All final examples fit; no multi-GPU allocation is proposed. Future longer cases should use content-selection/section decomposition or separately measured sequence engineering, never silent truncation. Full resumes remain essential for chronology, prioritization and cross-section coherence.

## Future experiment — design only

Preserve Base Qwen + frozen Stage 3J RAG as the untrained control. Compare two fresh adapter arms: Stage 4A evidence reasoning only, and interleaved Stage 4A plus this professional TRAIN split. The Stage 4B smoke adapter is not an evidence-trained baseline. Interleaving is the conservative first experiment; a staged arm and professional-only arm are deferred to avoid unnecessary compute.

Use 50/50 **assistant-target tokens**, with a professional exposure cap of one pass: P=55,115 professional tokens; target budget **110,230 supervised tokens per arm**, subject to complete-example granularity. Reference frozen Stage 4A v1, do not modify or concatenate it blindly. Task priorities guide ordering under the cap: resume20, application15, mapping15, job10, selection10, section10, letter8, missing-info7, rewriting3, outreach2. These are ordering priorities only. Each of the119 professional TRAIN records must occur exactly once; no replacement, no task-quota upsampling. Actual per-task target-token fractions are authoritative in datasets/stage4c0/v1/future_curriculum_experiment.v1.json, which resolves the draft sampling ambiguity.

If separately authorized: one A30; existing measured Stage 4B recipe; rank8/alpha16/dropout0.05 q/k/v/o adapters; NF4 double-quantization BF16, LR5e-5 PagedAdamW8bit, microbatch1/accumulation2, conservative4,233 maximum, no packing/truncation, measured CPU activation-offload/chunked-loss strategy, seed430001. Exact design and optimizer fields: [future experiment manifest](../contracts/future_curriculum_experiment.draft.json). No experiment was executed.

Reject any checkpoint with critical invented facts, numeric/technology substitution, cross-candidate leakage, injection obedience, false legal/preference answers or fabricated tool actions on the registered suite. Require 100% schema/numeric/technology checks there. Pre-register at most two percentage-point paired macro evidence-accuracy loss versus evidence-only; report UNKNOWN/UNSUPPORTED confusion and citation entailment separately. If uncertainty cannot exclude a material five-point loss, expand independent evaluation before acceptance. Never trade truth for prose quality. Blind model labels for professional judges; evaluate sealed test/challenge once after validation-based checkpoint selection.

Professional evaluation retains all 17 requested dimensions separately: grounding, hallucinated claims, numeric/technology fidelity, requirement coverage, supported terminology, evidence use, selection, writing, concision, redundancy, ATS structure, letter specificity, application grounding, correct USER_INPUT_REQUIRED, outreach personalization and schema validity. See [evaluation design](future_training_and_evaluation.md) for limitations and orchestration/run-mode boundaries.

## Tests, preservation and reproducibility

187 Stage 4C-0 tests passed locally and on CPU job2334389. Historical regression: 467 Stage 3 +19 Stage1/2 +55 Stage4A +35 Stage4B =576 tests passed, plus saved historical replays. No historical test was weakened. The final complete standalone audit validated all155 records, exact sidecar provenance, schema/truth, real tokenizer/chat/loss masks, group leakage, historical exclusion and hashes. Protected-history after verification passed against all1,456 Stage1–4B manifest entries, including recoverable base/frozen artifacts. Reports and checksums are packaged.

Human-quality packet contains 25 stratified/revised examples. It is an inspection aid; **no actual human review is claimed**. Every accepted example has independent Astra criticism; same-family bias and deterministic semantic incompleteness remain risks. Rejected raw artifacts and taxonomy are separate research material, never SFT. No DPO-ready preference dataset is certified; oracle-disputed cases are explicitly unsuitable as chosen/rejected preference pairs.

CPU-only Slurm jobs performed validation/tokenization/historical tests/protection. Frontier work was external teacher/critic inference. Generation attempts and actual receipt timing are preserved; provider input/output token billing, model runtime identity and cost remain unavailable. Qwen dataset-token totals are not Astra billing estimates.

## Release artifacts and next-stage boundary

Local release: `datasets/stage4c0/v1`. Remote project: `/home/mohammedmubashir/scratch/resume-ai`. `manifest.json`, `checksums.json`, `release_gate.json`, per-split JSONL, exact request/teacher/critic sidecars, rubrics, schemas, research and reports define the immutable release. Standalone validation: `.venv/bin/python -B -m stage4c0.validate datasets/stage4c0/v1/records.jsonl --tokenizer models/Qwen3.8-27B --report <new-report-path>`. Run from the remote repository so frozen Stage4A/Stage3 audit dependencies are available.

Archive path and SHA-256 are recorded in [release delivery metadata](../release/STAGE4C0_RELEASE.json). This report is outside the archive to avoid a circular archive-self-hash. Dataset/research/rubric/schema file checksums are separately listed. Archive includes source/lineage and failed attempts; it excludes base weights, adapters, private data and historical target corpora.

**STOP: Stage 4C-0 complete.** The next boundary is a separately authorized controlled QLoRA experiment following the design above. No Stage4C-1/4C-2, adapter merge, preference optimization, agent implementation or deployment is authorized or started.

## Requested 100-point audit index

Each item is addressed in the report narrative and the following primary evidence. Paths are relative to the project root.

| # | Requested item | Primary evidence |
|---:|---|---|
| 1 | Research methodology | research/stage4c0; docs/final_methodology_and_limitations.md |
| 2 | Research sources and provenance | research/stage4c0; docs/final_methodology_and_limitations.md |
| 3 | Source quality assessment | research/stage4c0; docs/final_methodology_and_limitations.md |
| 4 | ATS principles | research/stage4c0; docs/final_methodology_and_limitations.md |
| 5 | Resume principles | research/stage4c0; docs/final_methodology_and_limitations.md |
| 6 | Technical AI resume principles | research/stage4c0; docs/final_methodology_and_limitations.md |
| 7 | Job-analysis principles | research/stage4c0; docs/final_methodology_and_limitations.md |
| 8 | Cover-letter principles | research/stage4c0; docs/final_methodology_and_limitations.md |
| 9 | Application principles | research/stage4c0; docs/final_methodology_and_limitations.md |
| 10 | Outreach principles | research/stage4c0; docs/final_methodology_and_limitations.md |
| 11 | Conflicting advice | research/stage4c0; docs/final_methodology_and_limitations.md |
| 12 | Task vocabulary | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 13 | Task schemas | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 14 | Observable pipelines | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 15 | Quality rubrics | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 16 | Hard failures | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 17 | Soft failures | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 18 | Candidate factory | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 19 | Job factory | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 20 | Ground-truth provenance | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 21 | Frozen RAG integration | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 22 | Teacher architecture | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 23 | Teacher versions | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 24 | Critic architecture | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 25 | Critic versions | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 26 | Revision policy | contracts; docs/curriculum_design.md; docs/final_methodology_and_limitations.md |
| 27 | Validator architecture | stage4c0/validate.py; stage4c0/grounding.py; validator-report.json |
| 28 | Claim grounding | stage4c0/validate.py; stage4c0/grounding.py; validator-report.json |
| 29 | Numeric fidelity | stage4c0/validate.py; stage4c0/grounding.py; validator-report.json |
| 30 | Technology fidelity | stage4c0/validate.py; stage4c0/grounding.py; validator-report.json |
| 31 | Credential/date/employment fidelity | stage4c0/validate.py; stage4c0/grounding.py; validator-report.json |
| 32 | ATS structure validator | stage4c0/validate.py; stage4c0/grounding.py; validator-report.json |
| 33 | Bullet quality validator | stage4c0/validate.py; stage4c0/grounding.py; validator-report.json |
| 34 | Pilot size/composition | work/pilot-final; work/factory-freeze-v2.json; docs/validator_v2_final_scope.md |
| 35 | Pilot results | work/pilot-final; work/factory-freeze-v2.json; docs/validator_v2_final_scope.md |
| 36 | Pilot rejection reasons | work/pilot-final; work/factory-freeze-v2.json; docs/validator_v2_final_scope.md |
| 37 | Pilot systemic defects | work/pilot-final; work/factory-freeze-v2.json; docs/validator_v2_final_scope.md |
| 38 | Corrections before full generation | work/pilot-final; work/factory-freeze-v2.json; docs/validator_v2_final_scope.md |
| 39 | Frozen factory configuration and later versioned repairs | work/pilot-final; work/factory-freeze-v2.json; docs/validator_v2_final_scope.md |
| 40 | Full attempted count | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 41 | Accepted count | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 42 | Rejected count | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 43 | Revised count | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 44 | Acceptance rate | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 45 | Hard-grounding failure rate | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 46 | Numeric fidelity | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 47 | Technology fidelity | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 48 | Schema validity | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 49 | Task distribution | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 50 | Role distribution | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 51 | Seniority distribution | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 52 | Fit distribution | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 53 | Technology distribution | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 54 | Action distribution | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 55 | Trust distribution | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 56 | Difficulty distribution | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 57 | Diversity | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 58 | Duplicates | datasets/stage4c0/v1/generation_statistics.json; statistics.json; coverage_details.json |
| 59 | Train count | datasets/stage4c0/v1/manifest.json; validator-report.json; quarantine |
| 60 | Validation count | datasets/stage4c0/v1/manifest.json; validator-report.json; quarantine |
| 61 | Test count | datasets/stage4c0/v1/manifest.json; validator-report.json; quarantine |
| 62 | Challenge count | datasets/stage4c0/v1/manifest.json; validator-report.json; quarantine |
| 63 | Grouped split strategy | datasets/stage4c0/v1/manifest.json; validator-report.json; quarantine |
| 64 | Cross-split leakage | datasets/stage4c0/v1/manifest.json; validator-report.json; quarantine |
| 65 | Stage4A leakage | datasets/stage4c0/v1/manifest.json; validator-report.json; quarantine |
| 66 | Stage3 leakage | datasets/stage4c0/v1/manifest.json; validator-report.json; quarantine |
| 67 | Challenge isolation | datasets/stage4c0/v1/manifest.json; validator-report.json; quarantine |
| 68 | Real-world evaluation decision | datasets/stage4c0/v1/manifest.json; validator-report.json; quarantine |
| 69 | Qwen token statistics | datasets/stage4c0/v1/statistics.json; report Token and sequence analysis |
| 70 | Maximum sequence | datasets/stage4c0/v1/statistics.json; report Token and sequence analysis |
| 71 | Token percentiles | datasets/stage4c0/v1/statistics.json; report Token and sequence analysis |
| 72 | Stage4B comparison | datasets/stage4c0/v1/statistics.json; report Token and sequence analysis |
| 73 | Long examples | datasets/stage4c0/v1/statistics.json; report Token and sequence analysis |
| 74 | Whole/section mixture | datasets/stage4c0/v1/statistics.json; report Token and sequence analysis |
| 75 | Function traces | datasets/stage4c0/v1/statistics.json; report Token and sequence analysis |
| 76 | Assistant-only loss | datasets/stage4c0/v1/statistics.json; report Token and sequence analysis |
| 77 | Future curriculum mixture | contracts/future_curriculum_experiment.draft.json; docs/future_training_and_evaluation.md |
| 78 | Curriculum ordering | contracts/future_curriculum_experiment.draft.json; docs/future_training_and_evaluation.md |
| 79 | Task weights | contracts/future_curriculum_experiment.draft.json; docs/future_training_and_evaluation.md |
| 80 | Grounding regression gate | contracts/future_curriculum_experiment.draft.json; docs/future_training_and_evaluation.md |
| 81 | Three-model evaluation design | contracts/future_curriculum_experiment.draft.json; docs/future_training_and_evaluation.md |
| 82 | Professional metrics | contracts/future_curriculum_experiment.draft.json; docs/future_training_and_evaluation.md |
| 83 | ATS limits | contracts/future_curriculum_experiment.draft.json; docs/future_training_and_evaluation.md |
| 84 | Rejected/preference data | docs/final_methodology_and_limitations.md; rejected-attempts.jsonl; quarantine |
| 85 | Synthetic limitations | docs/final_methodology_and_limitations.md; rejected-attempts.jsonl; quarantine |
| 86 | Teacher limitations | docs/final_methodology_and_limitations.md; rejected-attempts.jsonl; quarantine |
| 87 | Remaining risks | docs/final_methodology_and_limitations.md; rejected-attempts.jsonl; quarantine |
| 88 | Stage4C0 tests | datasets/stage4c0/v1/audits; validator-report.json; release_gate.json |
| 89 | Historical tests | datasets/stage4c0/v1/audits; validator-report.json; release_gate.json |
| 90 | Protected artifacts | datasets/stage4c0/v1/audits; validator-report.json; release_gate.json |
| 91 | Manifest | datasets/stage4c0/v1/manifest.json; checksums.json |
| 92 | Dataset checksums | datasets/stage4c0/v1/manifest.json; checksums.json |
| 93 | Research/rubric/schema checksums | datasets/stage4c0/v1/manifest.json; checksums.json |
| 94 | Archive path/checksum | release/STAGE4C0_RELEASE.json |
| 95 | Usage/cost | generation_statistics.json; generation_config.json; immutable teacher/critic receipts; provider cost unavailable |
| 96 | A/B decision | report Decision and Future experiment; release_gate.json; docs/final_independent_readiness_review.json |
| 97 | Decision reason | report Decision and Future experiment; release_gate.json; docs/final_independent_readiness_review.json |
| 98 | Smallest remaining defect | report Decision and Future experiment; release_gate.json; docs/final_independent_readiness_review.json |
| 99 | Exact next experiment | report Decision and Future experiment; release_gate.json; docs/final_independent_readiness_review.json |
| 100 | Next-stage boundary | report Decision and Future experiment; release_gate.json; docs/final_independent_readiness_review.json |
