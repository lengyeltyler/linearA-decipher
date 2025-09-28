#!/usr/bin/env python3
import os
import pandas as pd

# -------- Paths (project-root aware) --------
BASE = os.path.dirname(os.path.dirname(__file__))          # .../linearA-decipher
OUT_DIR = os.path.join(BASE, "outputs")
IN_CSV  = os.path.join(OUT_DIR, "tablets_substituted.csv")
TRANS_DIR = os.path.join(OUT_DIR, "proto_translations")
MASTER_CSV = os.path.join(OUT_DIR, "proto_translations.csv")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TRANS_DIR, exist_ok=True)

# -------- Ending (container/unit) dictionary --------
ENDING_MAP = {
    "AB22 AB67": "big_jar",
    "AB22 AB03": "small_jar",
    "AB22 AB09": "amphoraA",
    "AB22 AB59": "amphoraB",
    "AB22 AB54": "unit?",
    "AB22 AB28": "large_measure",
    "AB22 AB40": "measure_tag",
}

# -------- Stem confidence tiers --------
HIGH = {"grain", "oil", "wineA", "wineB"}
MED  = {"prestige?", "commodity?"}
# all others => low

def confidence_for(stem_label: str, ending_label: str) -> str:
    stem_label = (stem_label or "").strip()
    ending_label = (ending_label or "").strip()

    if stem_label in HIGH:
        stem_conf = "high"
    elif stem_label in MED:
        stem_conf = "medium"
    else:
        stem_conf = "low"

    end_word = ENDING_MAP.get(ending_label)
    if end_word in {"big_jar","small_jar","amphoraA","amphoraB"}:
        end_conf = "high"
    elif end_word is not None:
        end_conf = "medium"
    else:
        end_conf = "low"

    order = {"low":0, "medium":1, "high":2}
    return {0:"low", 1:"medium", 2:"high"}[min(order[stem_conf], order[end_conf])]

def line_to_text(stem_label: str, ending_label: str, number, raw_span: str) -> str:
    # fallbacks
    stem_label = stem_label if isinstance(stem_label, str) and stem_label else None
    ending_label = ending_label if isinstance(ending_label, str) and ending_label else None
    number = int(number) if pd.notna(number) else 0

    # choose commodity word
    if stem_label and stem_label != "link?":
        commodity = stem_label
    else:
        # fallback: first token in raw span
        commodity = (raw_span or "").split()[0] if isinstance(raw_span, str) else "UNKNOWN"

    # choose unit word
    unit = ENDING_MAP.get(ending_label, ending_label if ending_label else "UNKNOWN_UNIT")

    return f"{commodity.replace('_',' ')} in {str(unit).replace('_',' ')} ×{number}"

def main():
    if not os.path.exists(IN_CSV):
        raise FileNotFoundError(f"Missing input: {IN_CSV}. Ensure tablets_substituted.csv is in outputs/")

    df = pd.read_csv(IN_CSV)

    # sanity: required columns
    required = {"file","line","translation","confidence","raw","stem_label","ending_label","number"}
    # we’ll build translation/confidence below if not present
    have = set(df.columns)

    # If translation not present, compose it now from stem/ending/number/raw
    if "translation" not in df.columns:
        if not {"stem_label","ending_label","number","raw_span"}.issubset(have):
            raise ValueError("Input is missing columns needed to compose translations: "
                             "expected stem_label, ending_label, number, raw_span")
        df["translation"] = [
            line_to_text(r.stem_label, r.ending_label, r.number, r.raw_span)
            for r in df.itertuples(index=False)
        ]
        # keep a 'raw' column for output continuity
        if "raw" not in df.columns:
            df["raw"] = df["raw_span"]

    # If confidence not present, compute it
    if "confidence" not in df.columns:
        if not {"stem_label","ending_label"}.issubset(set(df.columns)):
            raise ValueError("Input is missing stem_label/ending_label needed for confidence scoring.")
        df["confidence"] = [
            confidence_for(r.stem_label, r.ending_label) for r in df.itertuples(index=False)
        ]

    # Normalize types for sorting: handle numeric or string 'line'
    if "line" not in df.columns:
        raise ValueError("Input is missing required column: line")

    # robust line number extraction
    if pd.api.types.is_numeric_dtype(df["line"]):
        line_n = df["line"].astype(int)
    else:
        extracted = df["line"].astype(str).str.extract(r'(\d+)', expand=False)
        line_n = pd.to_numeric(extracted, errors="coerce").fillna(0).astype(int)

    out = df.copy()
    out["line_n"] = line_n
    out = out.sort_values(["file","line_n"]).drop(columns=["line_n"])

    # Minimal output schema
    cols = ["file","line","translation","confidence"]
    if "raw" in out.columns:
        cols.append("raw")
    out = out[cols]

    # Write master CSV
    out.to_csv(MASTER_CSV, index=False)

    # Write per-tablet txt files
    for file_name, g in out.groupby("file"):
        lines = [
            f"{row.translation}   [{row.confidence}]" + (f"   (raw: {row.raw})" if 'raw' in g.columns else "")
            for row in g.itertuples(index=False)
        ]
        txt_path = os.path.join(TRANS_DIR, f"{file_name.replace('.txt','')}_translated.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Proto-translations for {file_name}\n\n")
            f.write("\n".join(lines))
        print(f"✔ wrote {txt_path}")

    print(f"✔ wrote {MASTER_CSV}")

if __name__ == "__main__":
    main()