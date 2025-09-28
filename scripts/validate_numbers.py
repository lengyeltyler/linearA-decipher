#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from collections import Counter
from scipy.stats import chisquare

def main(in_csv="out/tables/annotated_ledger.csv", out_csv="out/tables/number_validation.csv"):
    df = pd.read_csv(in_csv)

    results = []
    grouped = df.groupby(["stem","ending"])
    for (stem, ending), group in grouped:
        numbers = list(group["number"])
        if len(numbers) < 2:
            continue  # too few data points

        # Count occurrences of each number
        counts = Counter(numbers)
        observed = list(counts.values())

        # Expected = flat distribution across range of observed numbers
        expected = [sum(observed)/len(observed)] * len(observed)

        chi2, pval = chisquare(observed, expected)

        results.append({
            "stem": stem,
            "ending": ending,
            "n_obs": len(numbers),
            "unique_numbers": len(counts),
            "chi2": round(chi2, 3),
            "pval": round(pval, 4),
            "numbers": " ".join(str(n) for n in numbers)
        })

    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(out_path, index=False)
    print(f"Wrote validation results to {out_path}")

if __name__ == "__main__":
    main()