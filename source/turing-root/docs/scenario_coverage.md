# Ground-truth-first scenario factory

Version: `stage4c0-scenarios-v1`; authored 2026-09-29; deterministic seed 430000. This catalog contains inputs and hidden audit facts only. It does not contain accepted professional targets or establish curriculum readiness.

`stage4c0/scenarios.py` exports `generate_pilot()`, `generate_pool()`, `generate_challenge()` and `write_scenarios(destination)`. The scenario record has `scenario_id`, `split`, `metadata`, `input` and `oracle`. Teacher requests must use only `input`. The paired `*_inputs.jsonl` files omit all oracle predicates. `ANALYZE_JOB` receives raw text with no extracted requirements and no candidate facts. The hidden expected extraction remains available only to validators.

The 18-record development pilot covers all ten tasks. It emphasizes four whole resumes and includes exact 31% metrics, Docker/Kubernetes, API consumption/construction, LoRA/QLoRA, explicit denial, unresolved numeric conflict, an injected instruction, an unverified credential, missing legal/tenure facts, and independent corroboration. Its seven source families stay outside final train/validation/test/challenge. No pilot target was inspected while authoring these facts.

The initial full pool has 112 records from 28 candidate variants and 21 substantive family groups. Seven families contain two controlled counterfactual variants; counting those variants as independent families would overstate diversity. Both variants stay in one split and share whole-resume and mapping tasks. The pairs cover containers, clouds, adapter methods, RAG study/implementation, API consumption/construction, exact versus unmeasured improvement, and asserted versus authenticated credentials.

| Task | Initial pool records |
|---|---:|
| GENERATE_RESUME | 28 |
| MAP_JOB_TO_CANDIDATE | 28 |
| ANALYZE_JOB | 8 |
| ANSWER_APPLICATION_QUESTION | 8 |
| GENERATE_COVER_LETTER | 8 |
| GENERATE_RESUME_SECTION | 8 |
| IDENTIFY_MISSING_INFORMATION | 8 |
| SELECT_RESUME_CONTENT | 7 |
| REWRITE_BULLET_FOR_JOB | 7 |
| DRAFT_OUTREACH | 2 |

This is an initial candidate pool, not a recommended final dataset size. Four tasks per candidate are useful because the same evidence supports observably different transformations. They are kept together to prevent task-level split leakage. The budget prioritizes complete resumes and evidence mapping while limiting outreach. Acceptance, measured token cost and uncovered behaviors determine whether the release should include this pool or expand it; count alone cannot demonstrate saturation.

The initial split is 92 train, 8 validation and 12 test records. Validation has two independent candidate families and test has three. The external challenge has ten input records from five separate archetypes, including safety-review transfer, a speech benchmark without live robot deployment, API consumption during migration, an internal note without peer-reviewed publication, and missing personal preferences. The challenge is not part of teacher training and must not be used to tune prompts or the catalog.

All ten requested role families occur in the initial pool. Seniority counts are 12 student/new-graduate, 16 entry, 40 early-career, 32 mid-level and 12 senior records. Fit counts are 48 strong, 40 moderate, 8 weak and 16 mixed. These labels are audit metadata, not teacher-visible claims. Detailed technology, action, trust, role and split counts are in `scenarios/coverage.json`; technology coverage is counted by candidate rather than multiplying every repeated source fact by its task count.

Candidate facts precede targets. Every fact has an owner, event, source provenance and stable ID. RAG excerpts are bounded to five exact-text groups and 640 characters each; the observed maximum excerpt is 154 characters. Profile history has explicit organization/title/start/end fields, separate project origins, and education entries. Senior candidates can contain prior and current roles; students retain project and education context without becoming senior professionals. Synthetic display names exist solely to satisfy the required header schema; phone numbers and emails are omitted.

`context_company` and `context_contact` are separate event scopes inside the stable input schema. They license relevant correspondence context, never candidate biography. The contact is a supplied synthetic recruiter role, not a discovered real person. User preferences and eligibility fields are absent unless explicitly authored. Assertions do not become authenticated facts. Exact authenticated attestations list fact IDs and source identity. Corroboration retains separate lineage. Instruction-bearing evidence stays untrusted and is marked as an instruction in the hidden oracle.

The input audit passes schema validation, owner/reference checks, unique scenario and candidate/job/task identity, exact source-quote membership, RAG bounds, deterministic replay, and declared group split isolation. It does not measure historical Stage 3/4A overlap or teacher quality; the main audit must do that.

Declared style-template groups are disjoint across held-out partitions, and held-out job body renderers use distinct structures. However, titles, field scaffolding, profile chronology skeletons and some generic connective text are shared. There is no claim of zero shared formatting or zero lexical template similarity. Substantive family isolation is the established property. A lexical similarity audit is still required; it should distinguish shared machine-readable schema from near-identical factual scenarios.

Coverage gaps found before full target generation include professional training examples with conflict/injection/corroboration, exact versus absent preferences, portfolio routing, one-sentence and character constraints, and full section-type representation. An additive expansion is authorized to address those gaps. It must create new families with independently authored truth and preserve this original pool and pilot byte-for-byte. No expansion may rescue a failed teacher answer by changing its source facts.

Other limitations remain: mostly US English technical scenarios, limited senior-professional narrative variation, a narrow synthetic credential universe, short bounded evidence contexts, and shared profile scaffolding. Zero real public jobs are redistributed. Real-world transfer, long-context content selection and international conventions remain later evaluation risks.

## Additive coverage expansion

`stage4c0/scenario_expansion.py` exports `generate_expansion()` and `write_expansion(destination)`. The independently authored expansion has 21 records in seven new train families. Its reason was logged before full teacher generation and without inspecting pilot outputs. It adds unresolved same-event metrics, malicious retrieved instructions, separately sourced corroboration, stored salary/start/relocation preferences, missing preferences, exact trusted portfolio lookup, explicit sentence/character bounds, a behavioral answer without an invented positive result, truthful REST terminology, and summary/skills/education/certification section tasks.

The combined candidate pool is 133 records: 113 train, 8 validation, 12 test. It now contains 31 whole resumes, 29 mappings, 8 analyses, 9 content plans, 12 application answers, 10 cover letters, 12 section tasks, 9 rewrites, 10 missing-information tasks and 3 outreach drafts. Section tasks cover all six retained section types. Original pilot, initial pool and challenge checksums were rechecked and remain identical. The full target pool is still conditional on the pilot gate; no teacher targets are generated by either source module.

The expansion deliberately adds only train records because it follows a coverage audit; it does not redesign held-out families after viewing their targets. This leaves small validation/test samples for some functions. Any broader future release should author additional held-out families before training decisions rather than repeatedly evaluating and repairing against this challenge set.

## Preregistered held-out task-coverage expansion

The final input-coverage audit found that several tasks lacked validation or test examples. Before any final teacher targets, `stage4c0/scenario_heldout.py` added ten original records from five new archetypes: six validation and four test. The active immutable input file is **`scenarios/heldout-coverage-v1.2.jsonl`**, with its input-only projection, manifest and coverage audit. Use v1.2 only; earlier held-out snapshots are quarantined, excluded artifacts retained for lineage.

An input consistency review caught different employer names in independently written job descriptions and generic supplied company context. The first correction exposed a duplicated suffix in one generated company name. These were renderer/consistency defects found without teacher targets. The corrected version sets the supplied company label explicitly and validates exact membership in the job text before freezing. Candidate experience facts were not revised to justify an artifact. Both prior JSONL snapshots and manifests remain byte-identical, with archived source and quarantine reasons.

The complete planned candidate pool is now **143 records: 113 train, 14 validation and 16 test**. Every retained task appears in train, validation and test; validation includes both a semantic application answer and a missing eligibility answer. The held-out additions include evidence selection, cover letters, grounded recruiter drafts, noisy/ambiguous analysis and absent relocation/start preferences. External challenge inputs are unchanged and were not used to tune this expansion.

These samples support task-level failure inspection. One or a few held-out examples per task do not support narrow confidence intervals, robust population accuracy estimates or a claim of saturation. Report per-task counts and each failure rather than hiding them inside an aggregate rate. The shared structured-profile scaffolding limitation remains.
