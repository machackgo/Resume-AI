# Resume AI baseline v1

Eight synthetic, deterministic, English cases. All ten requested capabilities are exercised through one structured analysis per case: requirement/skill extraction; evidence citations; requirement matching and missing detection; claim labels; bullet generation and job tailoring; structured JSON; refusal of fabricated claims. No real candidate data. The fixed vocabulary makes extraction measurable but limits this to closed-vocabulary extraction. Proposed claims constrain claim-selection evaluation; open-ended generation needs the separate semantic audit. Do not interpret this small development set as production validation.

The neutral base prompt defines the task/schema/label semantics, without few-shot examples, retrieval, adapters, or iterative prompt optimization. Weights untouched; existing NF4 loading retained. Thinking disabled explicitly, greedy decoding, seed 42, 1536 output tokens. Later stages must retain dataset/schema/scorer and inference budgets, recording prompt or architecture changes. Compare thinking-enabled inference as a separate experiment, not as this baseline.

Ground truth uses UNKNOWN for explicit ambiguity/conflict; mere absence is UNSUPPORTED. Adjacency is not equivalence. Partial compound claims are PARTIALLY_SUPPORTED. Tutorial-only AWS familiarity is partial evidence for AWS, not hands-on expertise. Missing means not fully supported, including preferred requirements; known gaps and unresolved evidence can be separated using labels. Contradictory five-vs-one years supports Python usage but not five years. Citation sets are exact; acceptable alternate attributions can lower strict accuracy and should be reviewed explicitly.

Metrics: strict final-text JSON parsing (no fence stripping or repair); restricted JSON Schema validation; micro extraction/missing/refusal/claim-selection precision, recall and F1; macro exact-label and exact-evidence-set accuracy; unsupported claim assertion rate over cited proposed claims; citation-grounded bullet rate; evidence-overlap job coverage proxy over ALL requirements. Failed schema cases score as empty predictions, remain in denominators, and have undefined bullet rates when no bullets exist. No single aggregate score. Citation-grounded rates do not prove the prose is entailed. Free-text hallucination rate, factual entailment, relevance, clarity, and usefulness require separate human audit. Empty output cannot earn perfect grounding. Model-judged metrics are not used.

Reproduce on Turing:

```
cd ~/scratch/resume-ai
.venv/bin/python -m unittest discover -s eval/tests -v
mkdir -p results/baseline
/cm/shared/apps/slurm/current/bin/sbatch eval/runners/baseline.slurm
```

Each new job uses an exclusive run directory keyed by Slurm ID (never overwrites a prior run). config records hashes of all eval source/data/prompt/schema files and local model metadata; shard sizes/timestamps and local download revision provide weight provenance without rehashing 52G. Raw records include exact rendered prompt, token IDs, text, timings, token cap flags, and GPU memory. No network downloads or environment rebuild. Python dependencies already installed. Bitwise reproducibility across hardware/library versions is not promised.

Review free-text bullets against every cited fact and record unsupported additions, invented metrics/employers/projects/credentials, ambiguity handling, and job relevance in a separate audit artifact. Treat missing/invalid output as a task failure, not a hallucination-free success.


Completed baseline: `results/baseline/base-v1-2325384-eval3/summary.md`.
Safe allocation reuse was verified for this session: one GPU on existing job 2325384, via `bash eval/runners/reuse_allocation.sh JOB_ID UNIQUE_RUN_ID`. Check GPU idleness and remaining allocation time before any future reuse; a pending standalone job can hit per-user GPU quota.

CPU-only verification and diagnostics:

```
.venv/bin/python eval/runners/rescore.py results/baseline/base-v1-2325384-eval3
.venv/bin/python eval/runners/diagnose_format.py results/baseline/base-v1-2325384-eval3
```

The diagnostic is secondary and removes only a complete Markdown JSON fence. It never replaces strict metrics. `semantic_audit.json` is an explicitly qualitative review by the engineering assistant, not an independent human judgment. Postprocessing scripts are saved alongside the run. Gold labels and inference prompt were not changed after observing results. For future exact source reproduction, use the saved eval snapshot in a separate project checkout retaining the same model path; preserve this run directory.
