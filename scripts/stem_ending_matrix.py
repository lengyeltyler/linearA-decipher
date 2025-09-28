#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

def main(in_csv="out/tables/annotated_ledger.csv", out_csv="out/tables/stem_ending_matrix.csv"):
    df = pd.read_csv(in_csv)

    # Pivot table: stems as rows, endings as columns, counts as values
    matrix = df.pivot_table(
        index="stem",
        columns="ending",
        values="number",
        aggfunc="count",
        fill_value=0
    )

    # Reset index to make stem a column
    matrix = matrix.reset_index()

    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(out_path, index=False)
    print(f"Wrote matrix to {out_path}")

if __name__ == "__main__":
    main()