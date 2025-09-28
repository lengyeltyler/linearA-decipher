#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from itertools import combinations
import re
import glob

def extract_stems(tokens):
    """Simple heuristic: group tokens into pairs like ABxx AByy."""
    stems = []
    for i in range(len(tokens)-1):
        if tokens[i].startswith("AB") and tokens[i+1].startswith("AB"):
            stems.append(f"{tokens[i]} {tokens[i+1]}")
    return stems

def main(clean_dir="data/clean", out_csv="out/tables/cooccurrence_full.csv"):
    results = []
    for filepath in glob.glob(f"{clean_dir}/*.txt"):
        with open(filepath, "r") as f:
            lines = f.readlines()

        for li, line in enumerate(lines, start=1):
            tokens = line.strip().split()
            stems = extract_stems(tokens)
            if len(stems) < 2:
                continue

            for a, b in combinations(sorted(set(stems)), 2):
                results.append({
                    "file": Path(filepath).name,
                    "line": li,
                    "pair": f"{a} + {b}",
                    "stems": ", ".join(stems)
                })

    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(out_path, index=False)
    print(f"Wrote co-occurrence table to {out_path}")

if __name__ == "__main__":
    main()