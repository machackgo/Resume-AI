# Stage 4A (dataset and objective only)

Frozen release: `datasets/stage4a/v1/`. Final report: `docs/stage4a_report.md`.
Only `messages` belongs in future model inputs. Never pass `oracle` or `metadata` to Qwen.
Development candidates are superseded and must not be trained on.

Within the existing Turing project and a CPU allocation, validate without regeneration:

```sh
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false .venv/bin/python -B -m stage4a.validate datasets/stage4a/v1
```

Reproduce into a NEW directory (the generator refuses an existing destination):

```sh
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false .venv/bin/python -B -m stage4a.build datasets/stage4a/reproduced-v1
```

The three JSONL files and generation configuration must reproduce byte-for-byte.
Generation/freeze timestamps are audit metadata and naturally differ. The builder requires
this repository's frozen message builder, tokenizer and historical exclusion artifacts.
No weights are loaded by the dataset builder or validator.

Run Stage4A tests against the frozen release:

```sh
STAGE4A_DATASET=datasets/stage4a/v1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m unittest discover -s tests/stage4a -v
```

Use the inherited historical regression unchanged. Exact learned-reranker scores were
hardware-sensitive on compute-3-04; CPU-only replay on gpu-4-23 matched the original
bitwise results. A GPU allocation is neither requested nor necessary for that replay.

`proposed-stage4b-config.json` is documentation, not an executable training configuration.
The A30 training memory envelope is unproven. Stage4A has no training entry point,
optimizer step, adapter creation or downstream workflow.
