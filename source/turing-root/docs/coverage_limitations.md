# Empirical input coverage and limitations

Audit scope: the active input-only candidate catalog as authored on 2026-09-29. Files are `pool.jsonl`, `pool-expansion-v1.jsonl` and `heldout-coverage-v1.2.jsonl`. No teacher, critic, test-reference or challenge-target artifacts were opened for this report. Inputs and hidden synthetic truth were inspected; all figures below describe scenario coverage, not model quality or accepted data.

The candidate catalog has **143 records, 40 candidate variants and 33 substantive candidate/job families**. Reusing a candidate for different tasks is deliberate; it does not create another independent background. Train/validation/test counts are **113/14/16**. The 18 development-pilot and 10 external-challenge inputs are separate. Every task appears in each main split, but most held-out task cells contain only one or two records.

| Task | Candidate records |
|---|---:|
| Whole resume | 31 |
| Candidate mapping | 29 |
| Job analysis | 10 |
| Content selection | 11 |
| Application answer | 14 |
| Cover letter | 11 |
| Resume section | 12 |
| Bullet rewrite | 9 |
| Missing information | 11 |
| Outreach draft | 5 |

All ten role families, five seniority categories and four fit categories are represented. Section tasks cover Experience and Projects four times each, and Summary, Skills, Education and Certifications once each. This establishes basic breadth; it does not establish that each behavior has enough independent demonstrations.

## Genuine repetition

All 40 candidate variants contain the exact degree value **Bachelor of Science in Computer Science**; four additionally contain a master's degree in that subject. The most common profile field multiset occurs in **15 of 40 candidates**: three claim facts plus name, one employment entry and one education entry. Dates are drawn from a small seniority-based chronology scaffold. These are substantial synthetic-template limitations, despite different technical experiences.

The same candidate facts appear in multiple tasks within a split. Seven controlled counterfactual families intentionally share almost all their source material. Job text includes repeated requirement markers and conventional location wording. Profile organization, institution and identity labels use recognizable synthetic naming patterns. Task instructions are also shared. Therefore zero declared family overlap must not be described as zero template repetition.

A surface comparison of the **33 unique job texts** used lowercased Unicode word tokens and sets of contiguous four-token shingles. Across **255 cross-split job pairs**, median Jaccard similarity was **0.01064** and maximum **0.07937**. No pair reached 0.50. These numbers exclude JSON schema scaffolding and candidate profiles. They are descriptive only: they do not prove semantic independence, detect all paraphrases, or establish an externally validated leakage threshold. Generic formatting and education patterns remain shared even when four-gram overlap is low.

## Uneven domain depth

By candidate, Python occurs in the explicit technology/domain tags for 23 variants, SQL for 15, Docker for 8 and PyTorch for 7. QLoRA and vector databases each occur in only one variant. Exact technology tags intentionally omit technologies not established by visible source text. A generic transformer model must not silently become evidence of a particular library. Counts describe exposure, not skill proficiency or factual support for every job requirement.

Every candidate has externally observed facts and authenticated structured fields, but only **two candidate variants** contain explicitly candidate-asserted facts. In the active pool, unresolved conflict and malicious-instruction content each appear in **three records from one family**. Independent corroboration also has limited family breadth. The final pool has no oracle facts labeled explicit negative; the pilot does. Stage 4A remains the separate source of broad evidence-label discrimination, but professional-task transfer of explicit contradiction needs further evaluation.

Of the 14 application-answer records, ten are classified BEHAVIORAL, two PREFERENCE, one FACTUAL and one ELIGIBILITY. Trusted salary, start date, relocation and portfolio cases supplement missing-data cases. There is no dedicated MOTIVATION-class record, and many requested form subtypes have little or no independent representation. Sensitive and preference fields must continue to route to trusted data or user input regardless of these counts.

Evidence contexts are short: among 133 non-analysis records, 94 have three distinct RAG content groups, 37 have four, and only two have five. This pool does not establish competence at selecting content from a large candidate history. Locale is consistently US English. International conventions, non-CS education, career changes, degree-free paths, richer research credentials and several senior technical backgrounds remain underrepresented.

## Evaluation limits and freeze implications

The input tests cover schema, provenance, immutable snapshots, deterministic replay, counterfactual grouping, raw-job analysis isolation, fact ownership, RAG bounds, declared split isolation, privacy markers, prompt contracts and coverage axes. They do not certify professional writing, target entailment, historical Stage 3/4A leakage, Qwen token compatibility, teacher quality or full release readiness. Those require the separate target, historical and tokenizer audits.

No coverage-saturation claim is justified. The pool is a small, controlled candidate curriculum for a measured pilot and possible controlled experiment. Per-task held-out counts must accompany later metrics; report every hard failure and use wide uncertainty bounds. Additional coverage should be preregistered and independently authored before training or test-driven tuning. Neither the candidate count nor passing these input tests is sufficient to declare the professional curriculum ready.
