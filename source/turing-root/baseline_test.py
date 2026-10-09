import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

MODEL = "/scratch/mohammedmubashir/resume-ai/models/Qwen3.8-27B"

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)

print("Loading Qwen 27B...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    quantization_config=bnb,
    device_map="auto",
    dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    local_files_only=True,
)

messages = [
    {
        "role": "system",
        "content": "You are a concise AI assistant. Return only the final answer."
    },
    {
        "role": "user",
        "content": "Explain QLoRA in exactly three concise sentences. Do not show reasoning or analysis."
    },
]

prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=True,
    reasoning_effort="medium",
)

print("\n========== CHAT TEMPLATE ==========")
print(prompt)
print("===================================\n")

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
input_tokens = inputs.input_ids.shape[1]

torch.cuda.reset_peak_memory_stats()
torch.cuda.synchronize()
start = time.time()

with torch.inference_mode():
    output = model.generate(
        **inputs,
        max_new_tokens=120,
        do_sample=False,
    )

torch.cuda.synchronize()
elapsed = time.time() - start

new_tokens = output.shape[1] - input_tokens
generated_ids = output[0, input_tokens:]

print("\n========== RAW GENERATION ==========")
print(tokenizer.decode(generated_ids, skip_special_tokens=False))
print("====================================")

print("\n========== BENCHMARK ==========")
print(f"Input tokens:     {input_tokens}")
print(f"Generated tokens: {new_tokens}")
print(f"Generation time:  {elapsed:.2f} sec")
print(f"Tokens/sec:       {new_tokens / elapsed:.2f}")

for i in range(torch.cuda.device_count()):
    allocated = torch.cuda.memory_allocated(i) / 1024**3
    reserved = torch.cuda.memory_reserved(i) / 1024**3
    peak = torch.cuda.max_memory_allocated(i) / 1024**3

    print(
        f"GPU {i}: allocated={allocated:.2f} GB | "
        f"reserved={reserved:.2f} GB | "
        f"peak={peak:.2f} GB"
    )

print("===============================")
