import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

MODEL = "/scratch/mohammedmubashir/resume-ai/models/Qwen3.8-27B"

print("CUDA available:", torch.cuda.is_available())
print("GPU count:", torch.cuda.device_count())

for i in range(torch.cuda.device_count()):
    print(f"GPU {i}: {torch.cuda.get_device_name(i)}")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

print("\nLoading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)

print("Loading Qwen in 4-bit...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    local_files_only=True,
)

print("\nMODEL LOADED SUCCESSFULLY")
print("Device map:")
print(model.hf_device_map)

messages = [
    {
        "role": "user",
        "content": "In three concise sentences, explain what QLoRA is and why it is useful for fine-tuning large language models."
    }
]

text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

inputs = tokenizer(text, return_tensors="pt").to(model.device)

print("\nGenerating...")

with torch.inference_mode():
    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        do_sample=False,
    )

generated = outputs[0][inputs.input_ids.shape[1]:]

print("\n===== QWEN OUTPUT =====")
print(tokenizer.decode(generated, skip_special_tokens=True))
print("=======================")

for i in range(torch.cuda.device_count()):
    used = torch.cuda.memory_allocated(i) / 1024**3
    reserved = torch.cuda.memory_reserved(i) / 1024**3
    print(f"GPU {i}: allocated={used:.2f} GB, reserved={reserved:.2f} GB")
