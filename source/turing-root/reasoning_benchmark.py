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

print("Loading Qwen 27B ONCE...")
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
        "content": "Explain QLoRA in exactly three concise sentences."
    }
]

for effort in ["low", "medium", "xhigh"]:

    print("\n" + "=" * 70)
    print(f"REASONING MODE: {effort.upper()}")
    print("=" * 70)

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=True,
        reasoning_effort=effort,
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_tokens = inputs.input_ids.shape[1]

    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()

    start = time.time()

    with torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
        )

    torch.cuda.synchronize()
    elapsed = time.time() - start

    generated = output[0, input_tokens:]
    decoded = tokenizer.decode(generated, skip_special_tokens=False)

    print("\nRAW OUTPUT:")
    print(decoded)

    new_tokens = len(generated)

    print("\nMETRICS:")
    print(f"Input tokens:     {input_tokens}")
    print(f"Generated tokens: {new_tokens}")
    print(f"Time:             {elapsed:.2f} sec")
    print(f"Speed:            {new_tokens / elapsed:.2f} tok/sec")

print("\nAll reasoning benchmarks complete.")
