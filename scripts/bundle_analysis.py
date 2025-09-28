#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from itertools import combinations
import glob

def extract_stems(tokens):
    """Heuristic: stems are pairs of ABxx tokens in sequence."""
    stems = []
    for i in range(len(tokens)-1):
        if tokens[i].startswith("AB") and tokens[i+1].startswith("AB"):
            stems.append(f"{tokens[i]} {tokens[i+1]}")
    return stems

def main(clean_dir="data/clean", out_csv="out/tables/bundles.csv"):
    bundle_counts = {}

    for filepath in glob.glob(f"{clean_dir}/*.txt"):
        with open(filepath, "r") as f:
            lines = f.readlines()

        for li, line in enumerate(lines, start=1):
            tokens = line.strip().split()
            stems = extract_stems(tokens)
            stems = sorted(set(stems))  # unique stems per line

            if len(stems) >= 2:
                for r in [2, 3]:  # pairs and triples
                    for combo in combinations(stems, r):
                        key = " + ".join(combo)
                        bundle_counts.setdefault(key, {"count":0, "examples":[]})
                        bundle_counts[key]["count"] += 1
                        if len(bundle_counts[key]["examples"]) < 3:
                            bundle_counts[key]["examples"].append(
                                f"{Path(filepath).name}: Line {li} => {', '.join(stems)}"
                            )

    # Flatten into DataFrame
    rows = []
    for bundle, data in sorted(bundle_counts.items(), key=lambda x: -x[1]["count"]):
        rows.append({
            "bundle": bundle,
            "count": data["count"],
            "examples": " | ".join(data["examples"])
        })

    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Wrote bundle data to {out_path}")

if __name__ == "__main__":
    main()