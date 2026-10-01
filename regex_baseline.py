"""
Simple rule-based method (the 'old way').
Written by looking only at the TRAINING email styles, like a real developer would.
Run alone:  python regex_baseline.py
"""
import re
from common import FIELDS, load_jsonl, score, print_table
 
 
def extract(email):
    out = {f: None for f in FIELDS}
    out["event_type"] = "cancellation" if re.search(r"cancel", email, re.I) else "schedule_change"
 
    m = re.search(r"\b(?:6E|AI|UK|SG|QP)\d{3,4}\b", email)
    if m:
        out["flight_no"] = m.group(0)
 
    m = re.search(r"(?i:PNR|Booking ref|Ref|code is)[:\s]+([A-Z0-9]{6})\b", email)
    if m:
        out["pnr"] = m.group(1)
 
    m = re.search(r"\b([A-Z]{3})\s*(?:to|-)\s*([A-Z]{3})\b", email)
    if m:
        out["origin"], out["destination"] = m.group(1), m.group(2)
 
    m = re.search(r"\b\d{2} [A-Z][a-z]{2} 2026\b|\b\d{2}/\d{2}/2026\b|\b[A-Z][a-z]{2} \d{1,2}, 2026\b", email)
    if m:
        out["date"] = m.group(0)
 
    m = re.search(r"(?:Dear|Hi)\s+([A-Z][a-z]+ [A-Z][a-z]+)", email)
    if m:
        out["passenger"] = m.group(1)
    else:
        m = re.search(r"Pax:\s*([A-Z]+ [A-Z]+)", email)
        if m:
            out["passenger"] = m.group(1).title()
 
    times = re.findall(r"\b\d{2}:\d{2}\b", email)
    if out["event_type"] == "cancellation":
        out["old_time"] = times[0] if times else None
    elif len(times) >= 2:
        if "instead of" in email:          # style: "now leaves at NEW instead of OLD"
            out["new_time"], out["old_time"] = times[0], times[1]
        else:
            out["old_time"], out["new_time"] = times[0], times[1]
    return out
 
 
if __name__ == "__main__":
    rows = load_jsonl("test.jsonl")
    preds = [extract(r["email"]) for r in rows]
    print_table({"Regex": score(preds, [r["output"] for r in rows])})
 