#!/usr/bin/env python3
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT  = ROOT / "outputs"; OUT.mkdir(parents=True, exist_ok=True)
LEDGER = OUT / "ht_syllabic_ledger.csv"
MAP    = ROOT / "data" / "syllabic_mapping.json"
SUBS   = OUT / "tablets_substituted.csv"

def main():
    mapping = json.loads(MAP.read_text(encoding="utf-8"))
    rows = []
    with LEDGER.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            item = row["item"].strip()
            m = mapping.get(item, {"commodity":"commodity?","unit":"unit?","confidence":"low"})
            rows.append({
                "file": row["file"],
                "line": "Line ?",
                "stem": item,                 # keep original syllabic item as 'stem' for traceability
                "ending": m["unit"],          # reuse 'ending' as unit class
                "number": row["number"],
                "raw_span": row["raw"],
                "stem_label": m["commodity"], # commodity label
                "ending_label": m["unit"]
            })
    header = ["file","line","stem","ending","number","raw_span","stem_label","ending_label"]
    mode = "a" if SUBS.exists() else "w"
    with SUBS.open(mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if mode == "w": w.writeheader()
        w.writerows(rows)
    print(f"Appended {len(rows)} rows to {SUBS}")

if __name__ == "__main__":
    main()