# Inspection before implementation — 2026-09-26

Project resolves to `/scratch/mohammedmubashir/resume-ai` from `~/scratch/resume-ai`. Original top level: `.venv/`, `models/`, `hf-cache/`, `baseline_test.py`, `reasoning_benchmark.py`, `test_qwen_4bit.py`. No AGENTS.md found under scratch. No benchmark outputs or project Git directory found. Approximate disk use: weights directory 52G, environment 6.0G, cache 1.3M. No weights or original scripts changed.

Local identity: README references `Qwen/Qwen3.8-27B`; directory `models/Qwen3.8-27B`. Download metadata config commit: `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`. This is local artifact provenance, not independent remote repository verification. Config architecture is `Qwen3_5ForConditionalGeneration`, model_type `qwen3_5`, language_model_only false. Existing loader is AutoModelForCausalLM; actual runtime class is recorded in run config. Dense advertised 27B; safetensors headers contain 27,781,427,952 tensor elements including vision/auxiliary tensors (not an assertion of active text parameter count). 18 weight shards. 64 text layers, hidden size 5120, intermediate 17408; three linear-attention layers then one full-attention layer per group.

Tokenizer config: Qwen2Tokenizer, vocabulary 248320 in model config, context 262144, add_bos_token false, no BOS/UNK string, EOS `<|im_end|>`, padding `<|endoftext|>`, no cleanup or prefix space. Chat template uses ChatML role delimiters and think tags. Thinking defaults on; reasoning_effort allows low, medium, xhigh (default). Low/xhigh insert instructions, medium inserts none. Disabling thinking prefills empty closed think tags. preserve_thinking defaults true. Template hash and tokenizer metadata hashes saved per run.

All existing scripts load local-only, 4-bit BitsAndBytes NF4, double quantization enabled, compute BF16, model dtype BF16, low_cpu_mem_usage true, device_map auto. Actual GPU distribution depends on allocation; cannot infer it from source. Existing generation is greedy, with max_new_tokens 120 / 512 per effort / 150 for baseline_test / reasoning_benchmark / test_qwen_4bit. Checkpoint sampling defaults are do_sample true, temperature 1, top_k 20, top_p .95, overridden by greedy mode. First script uses medium thinking; second compares low/medium/xhigh; third uses template default xhigh. All ask for a short QLoRA explanation. Short token budgets may consume the entire output on thinking. Historical speed and warnings unavailable because no saved outputs exist in the project.

Python 3.11.12, PyTorch 2.14.0, Transformers 5.17.0, Accelerate 1.15.0, BitsAndBytes 0.50.2, tokenizers 0.23.2. jsonschema absent; evaluator uses a tested validator for its deliberately restricted schema subset, requiring no install. CUDA runtime availability, GPU memory, actual model class/map, speed and load warnings are measured inside Slurm, not by running inference on the login node.

Slurm binaries are not on non-login SSH PATH: `/cm/shared/apps/slurm/current/bin`. academic has eight A30 GPU nodes, four 24G GPUs each; most idle during inspection. User job 2325384 was an active bash allocation on gpu-4-21, left untouched. New baseline requests one A30, four CPUs, 64G host RAM, one hour. A single NF4 27B replica is expected to fit with bounded generation; the job will provide evidence.

Original SHA256:
- baseline_test.py: af1c5f91955c5c8c0fd7722215c881df1d6258bafe909af38cf13ed88d1617c6
- reasoning_benchmark.py: a6b13b6c53aca769daf8eb9d43d881ade7a811aed64f601b6bc625351b01b5b5
- test_qwen_4bit.py: 6cc6132deb4f0f445153c49aff25deb6aab18d76b24dc2a6d62eed3ec3049cfa

## Runtime confirmation

Completed run base-v1-2325384-eval3: Qwen3_5ForCausalLM; all parameters cuda:0; hf_device_map absent. CUDA 13.0 available on one A30 24G, driver 595.71.05; 16.99 GiB peak allocated; 9.46 output tokens/sec including prefill. Optional causal_conv1d and flash-linear-attention absent; reference kernel warnings recorded. See baseline_report.md for failures, Slurm reuse, metrics and audit.
