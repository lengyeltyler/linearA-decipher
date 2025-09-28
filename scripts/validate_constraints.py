#!/usr/bin/env python3
import os, json, pandas as pd
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(__file__))
OUT  = os.path.join(BASE, "outputs")
PHRASES = os.path.join(OUT, "phrase_templates.csv")

# Canonical commodity→unit constraints (JSON-safe: use lists, not sets)
# (Units are in the "nice" forms used by phrase mining: spaces, not underscores.)
CANON = {
    "grain":     ["big jar", "large measure"],      # HT31 shows "large measure" ×7
    "oil":       ["small jar"],
    "wineA":     ["amphoraA"],
    "wineB":     ["amphoraB"],
    "prestige?": ["big jar", "measure tag"],
    "commodity?":["amphoraA", "unit?"],
}

# Map any legacy underscore unit names to the nice versions seen in phrase_templates.csv
REN = {
    "big_jar":"big jar",
    "small_jar":"small jar",
    "amphoraA":"amphoraA",
    "amphoraB":"amphoraB",
    "unit?":"unit?",
    "large_measure":"large measure",
    "measure_tag":"measure tag",
}

OUT_CONSTRAINTS = os.path.join(OUT, "constraint_violations.csv")
OUT_DICTIONARY  = os.path.join(OUT, "lexicon_frozen.json")

def main():
    if not os.path.exists(PHRASES):
        raise FileNotFoundError(f"Missing {PHRASES}. Run scripts/mine_templates.py first.")
    df = pd.read_csv(PHRASES)

    # normalize units to friendly form if underscores slipped through
    df["unit"] = df["unit"].astype(str).map(lambda u: REN.get(u, u))

    # find violations
    viol_rows = []
    seen = defaultdict(set)   # commodity -> units actually observed

    for r in df.itertuples(index=False):
        c = str(r.commodity)
        u = str(r.unit)
        seen[c].add(u)
        allowed = set(CANON.get(c, []))
        if allowed and u not in allowed:
            viol_rows.append({
                "file": r.file,
                "line": r.line,
                "commodity": c,
                "unit": u,
                "allowed_units": ", ".join(sorted(allowed))
            })

    pd.DataFrame(viol_rows).to_csv(OUT_CONSTRAINTS, index=False)
    print(f"Wrote {OUT_CONSTRAINTS} (rows={len(viol_rows)})")

    # freeze first-pass dictionary (JSON-safe: lists only, no sets)
    lexicon = {
        "stems": {
            "AB81 AB02": "grain",
            "AB54 AB67": "oil",
            "AB51 AB24": "wineA",
            "AB51 AB45": "wineB",
            "AB04 AB69": "prestige?",
            "AB27 AB17": "prestige?",
            "AB54 AB28": "commodity?",
            "AB28 AB67": "commodity?",
        },
        "endings": {
            "AB22 AB67": "big_jar",
            "AB22 AB03": "small_jar",
            "AB22 AB09": "amphoraA",
            "AB22 AB59": "amphoraB",
            "AB22 AB54": "unit?",
            "AB22 AB28": "large_measure",
            "AB22 AB40": "measure_tag"
        },
        "constraints": CANON  # already lists
    }

    with open(OUT_DICTIONARY, "w", encoding="utf-8") as f:
        json.dump(lexicon, f, indent=2, ensure_ascii=False)
    print(f"Froze dictionary → {OUT_DICTIONARY}")

if __name__ == "__main__":
    main()