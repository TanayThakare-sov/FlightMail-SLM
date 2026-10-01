"""Shared helpers used by all other files."""
import json
import re
 
FIELDS = ["event_type", "pnr", "passenger", "flight_no", "origin",
          "destination", "date", "old_time", "new_time"]
 
INSTRUCTION = ("Extract the booking details from this airline email. "
               "Reply with JSON only, using keys: " + ", ".join(FIELDS) + ".")
 
 
def build_prompt(email):
    return f"{INSTRUCTION}\n\nEmail:\n{email}\n\nJSON:\n"
 
 
def target_text(output):
    return json.dumps({k: output.get(k) for k in FIELDS}, ensure_ascii=False)
 
 
def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
 
 
def parse_json(text):
    """Take the model's text and try to read a JSON object from it."""
    m = re.search(r"\{.*?\}", text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None
 
 
def _norm(x):
    return None if x is None else str(x).strip()
 
 
def wrong_fields(pred, gold):
    pred = pred or {}
    return [f for f in FIELDS if _norm(pred.get(f)) != _norm(gold.get(f))]
 
 
def score(preds, golds):
    n = len(golds)
    per_field = {f: 0 for f in FIELDS}
    exact = 0
    for p, g in zip(preds, golds):
        bad = wrong_fields(p, g)
        for f in FIELDS:
            if f not in bad:
                per_field[f] += 1
        exact += (len(bad) == 0)
    result = {"JSON valid": 100 * sum(p is not None for p in preds) / n}
    for f in FIELDS:
        result[f] = 100 * per_field[f] / n
    result["ALL fields correct"] = 100 * exact / n
    return result
 
 
def print_table(results):
    """results = {"Regex": {...}, "Base model": {...}, ...}"""
    names = list(results)
    keys = list(next(iter(results.values())))
    print("\n" + "Metric (%)".ljust(22) + "".join(n.rjust(16) for n in names))
    print("-" * (22 + 16 * len(names)))
    for k in keys:
        print(k.ljust(22) + "".join(f"{results[n][k]:16.1f}" for n in names))
 