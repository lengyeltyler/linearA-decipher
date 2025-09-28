#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from itertools import combinations

def main(in_csv="out/tables/annotated_ledger.csv", out_csv="out/tables/cooccurrence.csv"):
    df = pd.read_csv(in_csv)

    results = []
    grouped = df.groupby(["file","line_label"])
    for (file, line), group in grouped:
        stems = list(group["stem"].unique())
        if len(stems) < 2:
            continue

        for a, b in combinations(sorted(stems), 2):
            results.append({
                "file": file,
                "line": line,
                "pair": f"{a} + {b}",
                "stems": ", ".join(stems)
            })

    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(out_path, index=False)
    print(f"Wrote cooccurrence table to {out_path}")

if __name__ == "__main__":
    main()