#!/usr/bin/env python3
import os, re, pandas as pd
from collections import Counter

BASE = os.path.dirname(os.path.dirname(__file__))
OUT  = os.path.join(BASE, "outputs")
IN_CSV = os.path.join(OUT, "proto_translations.csv")

TEMPLATES_CSV = os.path.join(OUT, "phrase_templates.csv")
COMM_UNIT_CSV = os.path.join(OUT, "commodity_unit_counts.csv")
ANOMALIES_CSV = os.path.join(OUT, "translation_anomalies.csv")

LINE_RX = re.compile(r'^(?P<commodity>.+?)\s+in\s+(?P<unit>.+?)\s+×(?P<number>\d+)\s*$')

def main():
    if not os.path.exists(IN_CSV):
        raise FileNotFoundError(f"Missing {IN_CSV}. Run scripts/render_translations.py first.")
    df = pd.read_csv(IN_CSV)

    pattern_counts = Counter()
    comm_unit_counts = Counter()
    parsed_rows, anomalies = [], []

    for r in df.itertuples(index=False):
        text = str(r.translation)
        m = LINE_RX.match(text)
        if not m:
            anomalies.append({"file": r.file, "line": r.line, "translation": text, "reason": "no_match"})
            continue
        commodity = " ".join(m.group("commodity").split())
        unit      = " ".join(m.group("unit").split())
        number    = int(m.group("number"))

        template = "COMMODITY in UNIT ×N"
        pattern_counts[template] += 1
        comm_unit_counts[(commodity, unit)] += 1

        parsed_rows.append({
            "file": r.file, "line": r.line,
            "commodity": commodity, "unit": unit, "number": number,
            "template": template, "confidence": r.confidence
        })

    pd.DataFrame(parsed_rows).to_csv(TEMPLATES_CSV, index=False)
    pd.DataFrame(
        [{"commodity": c, "unit": u, "count": n} for (c,u), n in comm_unit_counts.items()]
    ).sort_values(["commodity","unit"]).to_csv(COMM_UNIT_CSV, index=False)
    pd.DataFrame(anomalies).to_csv(ANOMALIES_CSV, index=False)

    print("Wrote:")
    print(" -", TEMPLATES_CSV)
    print(" -", COMM_UNIT_CSV)
    print(" -", ANOMALIES_CSV)

if __name__ == "__main__":
    main()