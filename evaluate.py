"""
Compare 3 systems on test.jsonl: Regex, Base model (no training), Fine-tuned (LoRA).
Run:  python evaluate.py          (add  --n 50  for a quicker test)
Creates: results.json and errors.jsonl (mistakes of the fine-tuned model, for error analysis)
"""
import argparse
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from common import build_prompt, load_jsonl, parse_json, score, print_table, wrong_fields
from regex_baseline import extract
 
MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=200)
args = ap.parse_args()
 
device = "cuda" if torch.cuda.is_available() else "cpu"
rows = load_jsonl("test.jsonl")[:args.n]
golds = [r["output"] for r in rows]
 
tok = AutoTokenizer.from_pretrained(MODEL)
tok.padding_side = "left"
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float32).to(device).eval()
 
 
def run(m, label):
    preds, raws = [], []
    for i in range(0, len(rows), 8):
        prompts = [build_prompt(r["email"]) for r in rows[i:i + 8]]
        enc = tok(prompts, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            out = m.generate(**enc, max_new_tokens=160, do_sample=False,
                             pad_token_id=tok.pad_token_id)
        for o in out:
            text = tok.decode(o[enc["input_ids"].shape[1]:], skip_special_tokens=True)
            raws.append(text)
            preds.append(parse_json(text))
        print(f"{label}: {min(i + 8, len(rows))}/{len(rows)}")
    return preds, raws
 
 
regex_preds = [extract(r["email"]) for r in rows]
base_preds, _ = run(model, "base model")
 
model = PeftModel.from_pretrained(model, "lora_out").eval()
ft_preds, ft_raws = run(model, "fine-tuned")
 
results = {
    "Regex": score(regex_preds, golds),
    "Base model": score(base_preds, golds),
    "Fine-tuned": score(ft_preds, golds),
}
print_table(results)
 
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
 
with open("errors.jsonl", "w", encoding="utf-8") as f:
    for r, p, raw in zip(rows, ft_preds, ft_raws):
        bad = wrong_fields(p, r["output"])
        if bad:
            f.write(json.dumps({"email": r["email"], "expected": r["output"],
                                "model_output": raw, "wrong_fields": bad},
                               ensure_ascii=False) + "\n")
print("\nSaved results.json and errors.jsonl (read errors.jsonl for your error analysis)")
 