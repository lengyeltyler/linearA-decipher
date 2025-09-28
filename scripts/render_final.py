#!/usr/bin/env python3
import os, json, pandas as pd

BASE = os.path.dirname(os.path.dirname(__file__))
OUT  = os.path.join(BASE, "outputs")
SUB  = os.path.join(OUT, "tablets_substituted.csv")
LEXJ = os.path.join(OUT, "lexicon_frozen.json")
FINAL_DIR = os.path.join(OUT, "final_translations")
MASTER = os.path.join(OUT, "final_translations.csv")

os.makedirs(FINAL_DIR, exist_ok=True)

ENDING_MAP_NICE = {
    "big_jar":"big jar",
    "small_jar":"small jar",
    "amphoraA":"amphoraA",
    "amphoraB":"amphoraB",
    "unit?":"unit?",
    "large_measure":"large measure",
    "measure_tag":"measure tag",
}

def main():
    if not os.path.exists(SUB):
        raise FileNotFoundError("Run scripts/substitute_dictionary.py first.")
    if not os.path.exists(LEXJ):
        raise FileNotFoundError("Run scripts/validate_constraints.py first to produce lexicon_frozen.json")

    df = pd.read_csv(SUB)
    lex = json.load(open(LEXJ, "r", encoding="utf-8"))
    # (we could validate again here if needed)

    rows = []
    for r in df.itertuples(index=False):
        stem = str(r.stem_label)
        ending = str(r.ending_label)
        num = int(r.number)

        # map ending to nice words
        end_key = lex["endings"].get(ending, ending)
        end_nice = ENDING_MAP_NICE.get(end_key, end_key)

        # commodity is already stem_label; keep as-is
        comm = stem.replace("_"," ")

        text = f"{comm} in {end_nice} ×{num}"
        rows.append({"file": r.file, "line": r.line, "translation": text})

    out = pd.DataFrame(rows)
    if "line" in out.columns and not pd.api.types.is_numeric_dtype(out["line"]):
        ln = pd.to_numeric(out["line"].astype(str).str.extract(r'(\d+)', expand=False), errors="coerce").fillna(0).astype(int)
        out = out.assign(_ln=ln).sort_values(["file","_ln"]).drop(columns=["_ln"])
    else:
        out = out.sort_values(["file","line"])

    out.to_csv(MASTER, index=False)

    for file_name, g in out.groupby("file"):
        txt = os.path.join(FINAL_DIR, f"{file_name.replace('.txt','')}_final.txt")
        with open(txt, "w", encoding="utf-8") as f:
            f.write(f"Linear A proto-decipherment — {file_name}\n\n")
            for row in g.itertuples(index=False):
                f.write(f"- {row.translation}\n")
        print("✔ wrote", txt)

    print("✔ wrote", MASTER)

if __name__ == "__main__":
    main()