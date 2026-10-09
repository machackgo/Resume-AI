# Final smoke review and freeze decision

Run grounded-v3-smoke-2325384-1, Slurm step 2325384.13. Raw response is a JSON object without fences or external prose; strict schema passed. 533 output tokens in 59.336 seconds. Compound claim S2 is now PARTIALLY_SUPPORTED, not UNSUPPORTED. Unknown credential remains UNKNOWN and absent from skills. Invented 25% metric remains UNSUPPORTED and refused. One minimal grounded R/CSV bullet, no added activity or metric. General atomic-label correction worked.

The indivisible production_deployment requirement remains UNSUPPORTED versus the smoke gold PARTIALLY_SUPPORTED. This is defensible given explicit non-deployment and the absence of any deployment evidence; the smoke gold was intentionally preserved. This taxonomy disagreement is not a formatting or hallucination failure and is not fixed by answer-specific rules.

Freeze grounded_v3 without further prompt edits. Evaluate the full original eight-case dataset exactly once, with original labels/scorer/model/generation controls. Report every regression. The repeated smoke is a development test, not a held-out generalization estimate. v1/v2 prompts, raw outputs and failed compound classifications remain preserved.
