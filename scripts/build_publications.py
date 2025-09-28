#!/usr/bin/env python3
"""
Build per-tablet publication-style reports with parallel text.

Outputs (per tablet) to: outputs/publication/<TABLET>_publication.md

Data sources:
- outputs/tablets_substituted.csv   (raw spans + labels + numbers)
- outputs/tablet_volumes.csv        (liters per commodity/unit)
- outputs/proto_translations.csv    (optional; we derive from substituted if missing)

No external deps beyond pandas.
"""

from pathlib import Path
import pandas as pd
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
PUB = OUT / "publication"
PUB.mkdir(parents=True, exist_ok=True)

SUBS_CSV = OUT / "tablets_substituted.csv"
VOL_CSV  = OUT / "tablet_volumes.csv"
PROTO_CSV = OUT / "proto_translations.csv"  # optional; we won’t fail if absent

# --- Confidence rules (simple & consistent) -----------------------------------
HIGH_STEMS  = {"grain", "oil", "wine", "winea", "wineb"}
KNOWN_UNITS = {"small_jar", "big_jar", "amphoraa", "amphorab", "large_measure", "measure_tag"}

def infer_confidence(stem_label: str, unit_label: str) -> str:
    s = (stem_label or "").strip().lower()
    u = (unit_label or "").strip().lower()

    if s in HIGH_STEMS and u in KNOWN_UNITS:
        return "high"
    if s in HIGH_STEMS or u in KNOWN_UNITS:
        return "medium"
    return "low"

def fmt_qty_line(stem_label, unit_label, number, confidence, raw_span):
    stem_label = stem_label or "commodity?"
    unit_label = unit_label or "unit?"
    conf_tag = {"high":"[high]","medium":"[medium]","low":"[low]"}[confidence]
    return f"{stem_label} in {unit_label} ×{int(number)}   {conf_tag}   (raw: {raw_span})"

def build_parallel_table(rows):
    """
    rows: list of dicts with keys:
      - raw_span
      - translation_line  (already formatted)
      - confidence
    Returns a GitHub-flavored Markdown table string.
    """
    lines = []
    lines.append("| Linear A (raw line) | Our hypothesis translation | Confidence |")
    lines.append("|---|---|---|")
    for r in rows:
        raw = r["raw_span"].replace("|", "\\|")
        tr  = r["translation_line"].replace("|", "\\|")
        conf = r["confidence"].capitalize()
        lines.append(f"| {raw} | {tr} | {conf} |")
    return "\n".join(lines)

def build_per_tablet_summary(vol_df, tablet_file):
    """Returns markdown block with liters by commodity + percent for this tablet."""
    df = vol_df[vol_df["file"] == tablet_file].copy()
    if df.empty:
        return "_No volume data available for this tablet._\n"

    # Sum liters by commodity
    g = df.groupby("commodity", as_index=False)["liters"].sum()
    g = g.sort_values("liters", ascending=False)
    total = g["liters"].sum()
    g["percent"] = g["liters"].pipe(lambda s: (s / total * 100).round(2))

    # Build a table
    md = []
    md.append("**Tablet volume summary**\n")
    md.append("")
    md.append("| commodity | liters | share (%) |")
    md.append("|---|---:|---:|")
    for _, r in g.iterrows():
        md.append(f"| {r['commodity']} | {r['liters']:.1f} | {r['percent']:.2f} |")
    md.append("")
    md.append(f"_Total: {total:.1f} L_")
    md.append("")
    return "\n".join(md)

def build_mini_lexicon(subs_df, tablet_file):
    """List the stems/units used on this tablet (what the reader needs)."""
    d = subs_df[subs_df["file"] == tablet_file].copy()
    if d.empty:
        return "_No lexicon items found on this tablet._\n"

    d["stem_label"] = d["stem_label"].fillna("commodity?")
    d["ending_label"] = d["ending_label"].fillna("unit?")
    stems = sorted(set(d["stem_label"]))
    units = sorted(set(d["ending_label"]))

    md = []
    md.append("**Mini lexicon used on this tablet**\n")
    md.append("")
    md.append("**Stems → commodity (hypothesis):**")
    for s in stems:
        md.append(f"- {s}")
    md.append("")
    md.append("**Endings → unit/measure (hypothesis):**")
    for u in units:
        md.append(f"- {u}")
    md.append("")
    return "\n".join(md)

def main():
    if not SUBS_CSV.exists():
        raise SystemExit(f"Missing {SUBS_CSV}. Run the pipeline to create it.")

    subs = pd.read_csv(SUBS_CSV)
    # Ensure required columns exist, and fill/normalize
    for col in ["file","raw_span","stem_label","ending_label","number"]:
        if col not in subs.columns:
            raise SystemExit(f"{SUBS_CSV} missing column: {col}")
    subs["stem_label"] = subs["stem_label"].fillna("commodity?")
    subs["ending_label"] = subs["ending_label"].fillna("unit?")
    subs["number"] = subs["number"].astype(int)

    # Optional proto translations (not strictly needed)
    if PROTO_CSV.exists():
        proto = pd.read_csv(PROTO_CSV)
    else:
        proto = pd.DataFrame(columns=["file","line","translation"])

    # Volume data
    if VOL_CSV.exists():
        vol = pd.read_csv(VOL_CSV)
    else:
        vol = pd.DataFrame(columns=["file","commodity","unit","count","liters"])

    # Tablets present
    tablets = sorted(subs["file"].unique())

    index_lines = ["# Linear A — Proto-decipherment Publication",
                   "",
                   "_Per-tablet, parallel-text edition generated by `scripts/build_publications.py`._",
                   ""]
    for tablet in tablets:
        base = tablet.replace(".txt","")
        out_md = PUB / f"{base}_publication.md"

        # Build parallel rows for this tablet
        tdf = subs[subs["file"] == tablet].copy()
        tdf["confidence"] = tdf.apply(
            lambda r: infer_confidence(str(r["stem_label"]), str(r["ending_label"])), axis=1
        )
        tdf["translation_line"] = tdf.apply(
            lambda r: fmt_qty_line(r["stem_label"], r["ending_label"], r["number"], r["confidence"], r["raw_span"]),
            axis=1
        )

        # Order by line number if present in raw_span
        # Try to extract trailing integer from raw_span, else keep csv order
        import re
        def line_key(s):
            if not isinstance(s,str): return 1e9
            # catch common forms: "... 7"  or "Line 3: ..." etc.
            m = re.search(r"(?:Line\s*)?(\d+)\b", s)
            if m:
                try:
                    return int(m.group(1))
                except:
                    return 1e9
            return 1e9
        tdf = tdf.sort_values(by="raw_span", key=lambda s: s.map(line_key))

        rows = [{"raw_span": rs["raw_span"],
                 "translation_line": rs["translation_line"],
                 "confidence": rs["confidence"]} for _, rs in tdf.iterrows()]

        # Build markdown
        md = []
        md.append(f"# {base} — Parallel Text Publication\n")
        md.append("_Exploratory hypothesis of commodities/units aligned with the original transcription._\n")
        md.append("## Parallel text\n")
        md.append(build_parallel_table(rows))
        md.append("\n")
        md.append("## Tablet summary\n")
        md.append(build_per_tablet_summary(vol, tablet))
        md.append("\n")
        md.append("## Mini lexicon (this tablet)\n")
        md.append(build_mini_lexicon(subs, tablet))
        md.append("\n")
        md.append("## Notes on confidence\n")
        md.append(textwrap.dedent("""\
            - **High**: both stem (commodity) and unit match anchor patterns recurring across tablets.
            - **Medium**: only the stem *or* the unit is on solid footing.
            - **Low**: neither side has strong recurrence; treat as tentative.
        """).strip())
        md.append("")

        out_md.write_text("\n".join(md), encoding="utf-8")
        print(f"✔ wrote {out_md}")

        index_lines.append(f"- [{base}]({out_md.relative_to(PUB)})")

    # Small index
    (PUB / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"✔ wrote {PUB/'index.md'}")

if __name__ == "__main__":
    main()