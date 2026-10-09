# Stage 4B engineering smoke

This directory is isolated from frozen Stage 1–4A. It does not authorize full training.

- `prepare.py`: read-only integrity checks, additional protected manifest, deterministic TRAIN subset, tokenizer/masking audit and meta architecture inspection.
- `test_cpu.py`: 35 CPU tests, including exact FP32 loss/gradient equivalence.
- `engine.py train`: one-A30 NF4 base; 64 full-attention rank-8 LoRA modules; staged forward/backward probes; nine bounded updates on 17 TRAIN records; save separate adapter and raw probes. It refuses to repeat optimization if training metrics or the adapter already exist.
- `engine.py reload`: fresh-process local base + saved adapter load, hash validation, enabled inference and disabled-base recovery.
- `diagnose.py`: no-update comparisons of repeated reference backward and chunked loss, plus isolated frozen-head comparison. This diagnosed BF16/native backward variability, not a quality experiment.
- `regression.py`: runs all historical tests/replays with new output destinations, including Stage 4A tests.
- `verify.py`: independent saved artifact, raw schema, token-volume and protected-byte verification.
- `report.py`: creates the final report only after verification passes.
- `ROADMAP.md`: future curriculum and architecture requirements, documentation only.

All execution uses the existing Turing `.venv`, offline local model/tokenizer access, and Slurm. GPU script requests one A30, 8 CPUs, 64 GB RAM and two hours. Its sequential train/reload Python processes release the allocation on success or failure. No dependency installation is needed. Do not rerun preparation on a completed release: the baseline manifests are immutable evidence of the original state.

The required low-memory loss uses the model's unchanged text backbone with PEFT-injected projections and its unchanged frozen BF16 vocabulary head. It predicts assistant targets from predecessor hidden states and checkpoints 64-position head/FP32-cross-entropy chunks. Backbone saved tensors use PyTorch pinned-CPU storage and return to CUDA for backward; all parameters, gradients and computation stay on the A30. No prompt/evidence truncation, sequence packing, new kernel, merged model, or generated training data is used.

The recorded configuration is reproducible, but repeated same-seed backward runs in the existing native stack are not bitwise identical. Loss and isolated-head comparisons, actual adapter gradients, full parameter checksums, and exact saved/reloaded greedy probes are separate acceptance checks. Historical tests were not weakened.

For a future authorized rerun, use new Stage-specific artifact destinations and preserve the entire completed release. Do not reuse this runner as a Stage 4C full-training script without a separately reviewed configuration and scope.
