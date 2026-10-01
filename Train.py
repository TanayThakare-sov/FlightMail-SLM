"""
Fine-tune a small language model with LoRA on train.jsonl.
Run:  python train.py        (use a GPU, e.g. free Google Colab T4)
Output: folder 'lora_out' (the small trained adapter)
"""
import random
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model
from common import build_prompt, target_text, load_jsonl
 
MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
EPOCHS = 2
BATCH = 4
LR = 2e-4
MAX_LEN = 384
 
device = "cuda" if torch.cuda.is_available() else "cpu"
if device == "cpu":
    print("WARNING: no GPU found. Training will be very slow. Use Google Colab (GPU).")
 
random.seed(0)
torch.manual_seed(0)
 
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32).to(device)
 
lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                  target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                  task_type="CAUSAL_LM")
model = get_peft_model(model, lora)
model.print_trainable_parameters()   # shows how few parameters LoRA trains
 
rows = load_jsonl("train.jsonl")
 
 
def encode(row):
    prompt_ids = tok(build_prompt(row["email"]), add_special_tokens=False)["input_ids"]
    answer_ids = tok(target_text(row["output"]) + tok.eos_token, add_special_tokens=False)["input_ids"]
    ids = (prompt_ids + answer_ids)[:MAX_LEN]
    labels = ([-100] * len(prompt_ids) + answer_ids)[:MAX_LEN]   # learn only from the answer part
    return ids, labels
 
 
data = [encode(r) for r in rows]
optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=LR)
 
model.train()
step = 0
for epoch in range(EPOCHS):
    random.shuffle(data)
    for i in range(0, len(data), BATCH):
        batch = data[i:i + BATCH]
        longest = max(len(ids) for ids, _ in batch)
        input_ids, labels, mask = [], [], []
        for ids, lab in batch:
            pad = longest - len(ids)
            input_ids.append(ids + [tok.pad_token_id] * pad)
            labels.append(lab + [-100] * pad)
            mask.append([1] * len(ids) + [0] * pad)
        out = model(input_ids=torch.tensor(input_ids).to(device),
                    attention_mask=torch.tensor(mask).to(device),
                    labels=torch.tensor(labels).to(device))
        out.loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        step += 1
        if step % 20 == 0:
            print(f"epoch {epoch + 1}  step {step}  loss {out.loss.item():.4f}")
 
model.save_pretrained("lora_out")
tok.save_pretrained("lora_out")
print("Saved adapter to lora_out/")
 