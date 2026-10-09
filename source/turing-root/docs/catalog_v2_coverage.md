# Prospective catalog v2: input diversity correction

Authored and frozen on 2026-09-29 before full-catalog teacher generation. This is an input-catalog freeze, not an accepted curriculum release or a training-readiness decision. No teacher outputs, critic outputs, final test targets or historical benchmark targets were read to create this version. No training was performed.

The earlier input audit found that all 40 candidate variants held the same computer-science bachelor's degree, with only two education-path shapes. Shared career timelines and missing project origins also limited the realism of prospective whole-resume inputs. The correction is implemented at the generator level in `stage4c0/scenario_catalog_v2.py`, through explicit, family-level qualifications and career histories. The original 143 input records remain preserved in their original files. Their technical evidence, job descriptions, requirement mappings and controlled technical counterfactuals are unchanged in v2; the new catalog records parent scenario IDs and hashes.

Use `scenarios/catalog-v2/catalog.jsonl` **instead of** the earlier full catalog. Never concatenate v1 and v2 as independent examples. The teacher projection is `catalog_inputs.jsonl`; it contains only scenario IDs and visible inputs, without the hidden oracle. `manifest.json` records source, output, parent, pilot and challenge checksums. Pilot and external challenge files were not modified.

## Scope and measured changes

| Measure | Original full catalog | Catalog v2 |
|---|---:|---:|
| Records | 143 | 155 |
| Train / validation / test | 113 / 14 / 16 | 125 / 14 / 16 |
| Candidate variants | 40 | 45 |
| Substantive candidate/job families | 33 | 37 |
| Distinct authored education paths | 2 | 37 |
| Degree-free candidate variants | 0 | 3 |
| Candidate variants with a graduate degree | 4 | 19 |
| Largest repeated profile event/field skeleton | 15 | 6 |

Education paths now include non-degree completion credentials, associate degrees, statistics, mathematics, electrical engineering, physics, linguistics, ecology and other non-CS disciplines, alongside graduate research qualifications. Degree-free cases explicitly state that no college degree is held and do not contain a degree field. A completion certificate is not represented as a degree or a professional license. These are authored diversity choices, not estimated frequencies in the applicant population. Unusual degree labels and the broad spread of disciplines remain synthetic-data limitations; variety of labels alone is not evidence of realistic career histories.

There are 31 distinct current-role/title/date patterns; the most repeated pattern belongs to two controlled candidate variants. Work dates and education dates are coherent. All project events in the new full catalog have explicit names and origins. Additional metadata never upgrades technical source assertions to verified experience. Candidate/profile ground truth and evidence provenance are authored before any target. Exact technical claims and their original trust levels remain unchanged for the retained 143 records.

The 12 new records address specific prospective gaps:

| New family | Records | Behavior |
|---|---:|---|
| Explicit contradiction | 3 | A candidate explicitly denies operating Kubernetes; mapping stays UNSUPPORTED, and professional artifacts must not convert the denial into a skill. |
| Supplied role motivation | 3 | A candidate's stated accessibility-related motivation can support a role-motivation answer and relevant correspondence. The model must not invent emotional attachment. |
| Trusted/missing personal fields | 4 | Controlled worlds supply or omit work authorization, availability and remote/hybrid preferences. Missing data requires user input. Stored fields are exact data, with deterministic routing preferred in production. |
| Larger history selection | 2 | Fifteen action propositions across five event-specific sources require prioritization and omission, including an irrelevant but true personal React project. |

The larger-history examples contain five RAG groups with a maximum source length of 246 characters, within the frozen five-group/640-character bounds. They exercise selecting among more facts; they do not demonstrate performance on an arbitrarily large candidate history. Selection from the full evidence store remains the frozen retrieval layer's responsibility.

## Distribution and evaluation limits

All ten retained tasks appear in each split. Across the 155 records, task counts are: resume 34; mapping 30; application answers 18; missing information 13; content selection 12; cover letter 12; resume section 12; job analysis 10; bullet rewrite 9; outreach 5. This input distribution preserves resume/mapping priority and a small outreach share. It is not a final token-weighted training mixture.

The catalog covers all ten requested role families and five seniority groups. Record counts by fit are strong 68, moderate 50, mixed 26 and weak 11. Those counts are repeated task views of 45 candidates, not 155 independent candidate backgrounds. The four new families are all in train; this deliberate small expansion does **not** supply independent held-out evaluation for every newly added behavior. The original held-out tasks and challenge are unchanged. A later evaluation design must report this limitation rather than treating task presence as behavioral saturation.

Application answers now include 10 behavioral, 2 preference, 2 factual, 3 eligibility and 1 motivation questions. Four candidate variants have a negative fact: three degree-free education statements and one explicit technology-experience denial. The technology denial is therefore still represented by only one substantive family. Conflict, malicious instructions and independent corroboration remain limited, intentional minority cases rather than broad coverage claims.

Validation and test sets are small: 14 and 16 records. Even zero failures in 16 independent trials would leave a one-sided 95% binomial upper failure bound of about 17%; these records are clustered by family, so independence should not be assumed. Per-task counts are still smaller. These splits support preliminary regression checks, not precise claims about deployment accuracy or generalization.

## Template and lexical audit

The audit compares all 295 cross-split pairs among 37 unique raw JD texts using lowercase Unicode word tokenization and four-token-shingle Jaccard similarity. Median similarity is 0.01064, maximum 0.09677, and no pair reaches 0.5. These measurements retain role words, formatting language and synthetic names. They are a lexical screen, not semantic leakage proof.

Actual renderer reuse is disclosed separately from metadata labels. Fourteen train families use the same default introduction/requirements/location renderer; several additional train families share narrative, checklist, question-led and requirements-first branches. The four new named style labels also use that default renderer. They must not be counted as four independent prose templates merely because their labels differ. Held-out branches are separate, but basic requirement vocabulary, profile fields and task schemas necessarily recur across splits. Zero substantive-family overlap does not mean zero shared language or formatting.

The largest exact event/field profile skeleton is shared by six candidate variants, improved from 15 but still repetitive. Most evidence remains short and clean. The catalog is original synthetic authored material, not a measured sample of real recruiting documents. No style-diversity or near-duplicate claims about **generated artifacts** can be made from this input-only audit.

## Verification and ownership release

`PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest stage4c0.test_catalog_v2 stage4c0.test_factory` passed all 41 tests (14 new catalog checks plus 27 existing research/factory checks). Checks cover reproducibility, source/output/parent hashes, input schemas, ground-truth hashes, candidate ownership, provenance, source spans, degree-free fidelity, explicit project origins, chronology, technical-fact preservation, controlled personal-field worlds, negative facts, bounded RAG, task coverage and substantive-group isolation. Cross-owner fact-ID collisions are zero.

Catalog SHA256: `97b88b6e04ebf1e19400046261d19fb12a44998deb58db2c12b95921573cd579`.

Source SHA256: `c4dad9409f41c36f64adec619a09ade06c79212853ed46107bfd0d045048a21e`.

Machine-readable measurements are in `docs/catalog_v2_input_audit.json`. The source and catalog are frozen; any material further change requires another version and parent notification. Teacher acceptance, independent criticism, real tokenizer statistics, historical benchmark leakage checks and final release eligibility belong to the downstream pipeline. No coverage-saturation claim is made.
