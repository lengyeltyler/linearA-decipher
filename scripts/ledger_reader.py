#!/usr/bin/env python3
import re
import glob
from pathlib import Path
import pandas as pd

# ---- helpers ----
def load_glossary(path):
    df = pd.read_csv(path, sep="\t")
    gloss = {}
    for _, r in df.iterrows():
        gloss[r["token"]] = {
            "role": r["role"],
            "hyp": r["hypothesis"],
            "conf": r["confidence"]
        }
    return gloss

def extract_pairs(tokens):
    """Return list of consecutive ABxx ABxx pairs as stems/links/units."""
    pairs = []
    for i in range(len(tokens)-1):
        if tokens[i].startswith("AB") and tokens[i+1].startswith("AB"):
            pairs.append(f"{tokens[i]} {tokens[i+1]}")
    return pairs

def extract_numbers(tokens):
    return [t for t in tokens if re.fullmatch(r"\d+", t)]

def classify(items, gloss):
    """Map items to (role, hyp, conf) if known."""
    out = []
    for it in items:
        g = gloss.get(it)
        if g:
            out.append((it, g["role"], g["hyp"], g["conf"]))
        else:
            out.append((it, "unknown", "", ""))
    return out

def line_interpretation(pairs, nums, gloss):
    parts = classify(pairs, gloss)
    commodities = [p for p in parts if p[1] == "commodity"]
    units       = [p for p in parts if p[1] == "unit"]
    process     = [p for p in parts if p[1] == "process"]
    links       = [p for p in parts if p[1] == "link"]
    unknowns    = [p for p in parts if p[1] == "unknown"]

    interp = []

    # Try commodity + unit + number patterns first
    if commodities and units and nums:
        for c in commodities:
            for u in units:
                interp.append(f"{c[0]} ≈ {c[2]} [{c[3]}]  —  {u[0]} ≈ {u[2]} [{u[3]}]  —  number(s): {'/'.join(nums)}")

    # If only commodity + number
    if commodities and not interp and nums:
        for c in commodities:
            interp.append(f"{c[0]} ≈ {c[2]} [{c[3]}]  —  number(s): {'/'.join(nums)}")

    # Processing chains
    if process:
        chain = " → ".join(p[0] for p in process)
        interp.append(f"processing chain: {chain}")

    # Links / unknowns (context)
    if links:
        interp.append("links: " + ", ".join(p[0] for p in links))
    if unknowns:
        interp.append("unknown: " + ", ".join(p[0] for p in unknowns))

    if not interp:
        interp.append("no interpretation (insufficient anchors)")

    return " | ".join(interp)

# ---- main ----
def main(clean_dir="data/clean", out_dir="out/readable", glossary="out/tables/glossary_hypothesis.tsv"):
    gloss = load_glossary(glossary)
    out_path = Path(out_dir); out_path.mkdir(parents=True, exist_ok=True)

    for f in glob.glob(f"{clean_dir}/*.txt"):
        lines = Path(f).read_text().splitlines()
        out_lines = []
        for i, line in enumerate(lines, start=1):
            toks = line.strip().split()
            pairs = extract_pairs(toks)
            nums = extract_numbers(toks)
            gloss_line = line_interpretation(pairs, nums, gloss)
            out_lines.append(f"Line {i}: {line}\n  → {gloss_line}\n")

        Path(out_path, Path(f).name.replace(".txt", "_readable.txt")).write_text("\n".join(out_lines))

    print(f"Wrote interpreted files to {out_path}")

if __name__ == "__main__":
    main()