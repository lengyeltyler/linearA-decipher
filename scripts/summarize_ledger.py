#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
import argparse

def main(ledger_csv, out_csv):
    df = pd.read_csv(ledger_csv)

    # Group by stem + ending
    grouped = df.groupby(["stem","ending"]).agg(
        pair_count = ("number","count"),
        total_number = ("number","sum"),
        avg_number = ("number","mean"),
        min_number = ("number","min"),
        max_number = ("number","max"),
        examples = ("example", lambda x: "; ".join(x.head(3)))
    ).reset_index()

    grouped = grouped.sort_values(["stem","ending"])
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    grouped.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Summarize annotated ledger by stem + ending")
    ap.add_argument("-i","--infile", default="out/tables/annotated_ledger.csv")
    ap.add_argument("-o","--outfile", default="out/tables/ledger_summary.csv")
    args = ap.parse_args()
    main(args.infile, args.outfile)