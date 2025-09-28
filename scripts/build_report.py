#!/usr/bin/env python3
import datetime
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

def main():
    md_path = OUT / "LinearA_report.md"

    # Header
    lines = []
    lines.append("# Linear A — Proto-decipherment Report\n\n")
    lines.append(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    lines.append("This document aggregates:\n")
    lines.append("- Proto-translations per tablet\n")
    lines.append("- Economy totals\n")
    lines.append("- Commodity ratios and cluster plots\n")
    lines.append("- Brief method and caveats\n\n")
    lines.append("> Repository: auto-generated from your `outputs/` by `scripts/build_report.py`\n")
    lines.append("\n---\n\n")

    # Method
    lines.append("## Method (in brief)\n\n")
    lines.append("This report is generated from a reproducible pipeline:\n\n")
    lines.append("1. **Input**: cleaned Linear A sign bigrams per line in `data/clean/*.txt`.\n")
    lines.append("2. **Structure detection**: extract frequent stems (likely commodities) and endings (likely units/measures).\n")
    lines.append("3. **Anchors**: map high-confidence pairs to provisional labels.\n")
    lines.append("4. **Substitution**: produce `outputs/tablets_substituted.csv`.\n")
    lines.append("5. **Volumes & ratios**: convert counts to liters, compute per-tablet shares.\n")
    lines.append("6. **Proto-translations**: render per-tablet readable summaries.\n\n")
    lines.append("**Caveats**:\n")
    lines.append("- This is a **proto-decipherment**: not phonetic values or full grammar.\n")
    lines.append("- Unknowns appear as `commodity?` and `unit?`.\n")
    lines.append("- Results are strongest where anchors recur consistently.\n\n")
    lines.append("\n---\n\n")

    # Proto-translations
    lines.append("## Tablet-by-tablet proto-translations\n\n")
    trans_dir = OUT / "proto_translations"
    if trans_dir.exists():
        for txt in sorted(trans_dir.glob("*_translated.txt")):
            name = txt.stem.replace("_translated", "")
            lines.append(f"### {name}\n\n")
            lines.append("```text\n")
            lines.append(txt.read_text(encoding="utf-8"))
            lines.append("\n```\n\n")

    # Economy totals
    eco_csv = OUT / "economy_totals.csv"
    if eco_csv.exists():
        lines.append("\n---\n\n")
        lines.append("## Economy totals\n\n")
        df = pd.read_csv(eco_csv)
        lines.append("**Totals table:**\n\n")
        lines.append(df.to_markdown(index=False, tablefmt="github"))
        lines.append("\n\n**Text summary:**\n\n```text\n")
        lines.append((OUT / "economy_totals.txt").read_text(encoding="utf-8"))
        lines.append("\n```\n\n")

    # Clusters
    clust_csv = OUT / "volume_clusters.csv"
    if clust_csv.exists():
        lines.append("\n---\n\n")
        lines.append("## Commodity ratios & clusters\n\n")
        df = pd.read_csv(clust_csv)
        labels = []
        for _, row in df.iterrows():
            if row["wine"] > 0.8:
                labels.append("wine cluster")
            else:
                labels.append("grain/oil cluster")
        df["cluster_label"] = labels
        lines.append("**Cluster assignments (by commodity share):**\n\n")
        lines.append(df.to_markdown(index=False, tablefmt="github"))
        lines.append("\n\n")
        scatter_path = OUT / "volume_clusters_scatter.png"
        if scatter_path.exists():
            lines.append(f"![Commodity share scatter](./{scatter_path.relative_to(ROOT)})\n")

    # Write Markdown
    md_path.write_text("".join(lines), encoding="utf-8")
    print(f"✔ wrote {md_path}")
    print("⚠ Skipped PDF export (disabled to avoid dependency issues).")

if __name__ == "__main__":
    main()