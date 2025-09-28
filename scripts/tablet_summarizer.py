#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd
import re
from collections import defaultdict

# -------- helpers --------

def load_glossary(path="out/tables/glossary_hypothesis.tsv"):
    """
    Returns two dicts:
      stem_map[token] -> normalized commodity label (e.g., 'grain', 'oil', 'wineA', 'prestige?')
      unit_map[token] -> normalized unit label (e.g., 'big_jar', 'small_jar', 'amphoraA', 'amphoraB')
    Falls back to hypothesis text if no explicit mapping is found.
    """
    df = pd.read_csv(path, sep="\t")
    stem_map, unit_map = {}, {}

    # Manual normalizations (you can extend these easily)
    COMMODITY_LABELS = {
        "AB81 AB02": "grain",
        "AB54 AB67": "oil",
        "AB51 AB24": "wineA",
        "AB51 AB45": "wineB",
        "AB04 AB40": "oil_or_unguent?",   # rare; keep cautious
        "AB04 AB69": "prestige?",
        "AB27 AB17": "prestige?",
        "AB28 AB67": "vessel_large?",
        "AB54 AB28": "vessel_small?",
        "AB30 AB22": "livestock?",
        "AB79 AB30": "livestock_class?",
        "AB81 AB79": "herd_or_owner?",
    }
    UNIT_LABELS = {
        "AB22 AB67": "big_jar",
        "AB22 AB03": "small_jar",
        "AB22 AB09": "amphoraA",
        "AB22 AB59": "amphoraB",
        "AB22 AB40": "measure_tag",
        "AB22 AB41": "small_measure",
        "AB22 AB54": "large_measure",
        "AB22 AB28": "vessel_link",
    }

    for _, r in df.iterrows():
        token, role, hyp = r["token"], str(r["role"]), str(r["hypothesis"])
        if role == "commodity":
            label = COMMODITY_LABELS.get(token)
            if not label:
                # derive short label from hypothesis, e.g., "grain/cereal (bulk)" -> "grain"
                m = re.match(r"([A-Za-z?]+)", hyp)
                label = (m.group(1).lower() if m else hyp.lower() or "commodity?")
            stem_map[token] = label
        elif role == "unit":
            label = UNIT_LABELS.get(token)
            if not label:
                m = re.match(r"([A-Za-z?]+)", hyp)
                label = (m.group(1).lower() if m else hyp.lower() or "unit?")
            unit_map[token] = label
        # ignore process/link here; summarizer is commodity/unit focused

    return stem_map, unit_map

def normalize_int(x):
    try:
        return int(x)
    except Exception:
        return None

# -------- main summarizer --------

def main(seq_csv="out/tables/structured_sequences.csv",
         glossary="out/tables/glossary_hypothesis.tsv",
         out_summary="out/tables/tablet_summary.csv",
         out_totals="out/tables/tablet_totals.csv",
         out_triads="out/tables/triads_detected.csv",
         out_readable_dir="out/readable"):

    stem_map, unit_map = load_glossary(glossary)
    df = pd.read_csv(seq_csv)

    # Normalize labels
    df["commodity"] = df["stem"].map(stem_map).fillna("commodity?")
    df["unit"] = df["ending"].map(unit_map).fillna("unit?")
    df["n"] = df["number"].apply(normalize_int)

    # Output 1: detailed summary (line-level)
    out1 = Path(out_summary); out1.parent.mkdir(parents=True, exist_ok=True)
    df_out = df[["file","line","stem","ending","n","commodity","unit","raw_span"]].sort_values(["file","line"])
    df_out.to_csv(out1, index=False)

    # Output 2: totals per (tablet, commodity, unit)
    totals = (
        df_out.groupby(["file","commodity","unit"], dropna=False)["n"]
              .sum(min_count=1)
              .reset_index()
              .sort_values(["file","commodity","unit"])
    )
    out2 = Path(out_totals)
    totals.to_csv(out2, index=False)

    # Output 3: detect multi-sequence lines and triads (grain+oil+wine)
    # We use commodity label membership on the same (file,line)
    triad_rows = []
    for (f, ln), g in df_out.groupby(["file","line"]):
        commodities = list(g["commodity"])
        uniq = set(commodities)
        is_pair = len(uniq) >= 2
        is_triad = {"grain","oil","wineA"}.issubset(uniq) or {"grain","oil","wineB"}.issubset(uniq)
        triad_rows.append({
            "file": f,
            "line": ln,
            "commodities": ", ".join(commodities),
            "triad_grain_oil_wine": bool(is_triad),
            "num_sequences": len(g)
        })
    triads = pd.DataFrame(triad_rows).sort_values(["file","line"])
    out3 = Path(out_triads); triads.to_csv(out3, index=False)

    # Output 4: readable per-tablet summaries
    out_dir = Path(out_readable_dir); out_dir.mkdir(parents=True, exist_ok=True)
    for f, g in totals.groupby("file"):
        lines = [f"Tablet {f} — commodity totals:\n"]
        for _, r in g.iterrows():
            qty = "?" if pd.isna(r["n"]) else int(r["n"])
            lines.append(f"  • {r['commodity']:<10}  {qty} × {r['unit']}")
        # add triad note
        tri_g = triads[(triads["file"]==f) & (triads["triad_grain_oil_wine"]==True)]
        if not tri_g.empty:
            lines.append("\n  Triad lines (grain+oil+wine): " +
                         ", ".join(str(int(x)) for x in tri_g["line"].tolist()))
        Path(out_dir, f.replace(".txt","_summary.txt")).write_text("\n".join(lines) + "\n")

    print(f"Wrote line-level summary: {out1}")
    print(f"Wrote totals: {out2}")
    print(f"Wrote triad detection: {out3}")
    print(f"Wrote readable summaries to: {out_dir}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seq_csv", default="out/tables/structured_sequences.csv")
    ap.add_argument("--glossary", default="out/tables/glossary_hypothesis.tsv")
    ap.add_argument("--out_summary", default="out/tables/tablet_summary.csv")
    ap.add_argument("--out_totals", default="out/tables/tablet_totals.csv")
    ap.add_argument("--out_triads", default="out/tables/triads_detected.csv")
    ap.add_argument("--out_readable_dir", default="out/readable")
    args = ap.parse_args()
    main(args.seq_csv, args.glossary, args.out_summary, args.out_totals, args.out_triads, args.out_readable_dir)