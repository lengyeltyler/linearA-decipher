#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

def main(in_csv="out/tables/bundles.csv",
         wide_csv="out/tables/bundle_item_matrix.csv",
         wide_wt_csv="out/tables/bundle_item_matrix_weighted.csv"):
    df = pd.read_csv(in_csv)
    # Split bundle string "A + B + C" into list
    df["items"] = df["bundle"].str.split(r"\s*\+\s*")

    # All unique items
    vocab = sorted({itm for items in df["items"] for itm in items})

    # Build binary matrix
    rows = []
    for _, r in df.iterrows():
        vec = {itm: 0 for itm in vocab}
        for itm in r["items"]:
            vec[itm] = 1
        vec["bundle"] = r["bundle"]
        vec["count"] = r["count"]
        rows.append(vec)
    mat = pd.DataFrame(rows).set_index("bundle")

    # Save binary (one row per bundle instance)
    out1 = Path(wide_csv)
    out1.parent.mkdir(parents=True, exist_ok=True)
    mat.drop(columns=["count"]).to_csv(out1)

    # Save frequency-weighted (so frequent bundles matter more)
    weighted = mat.copy()
    for col in [c for c in weighted.columns if c != "count"]:
        weighted[col] = weighted[col] * weighted["count"]
    weighted = weighted.drop(columns=["count"])
    weighted.to_csv(wide_wt_csv)

    print(f"Wrote {out1} and {wide_wt_csv}")

if __name__ == "__main__":
    main()