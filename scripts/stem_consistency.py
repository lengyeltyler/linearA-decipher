#!/usr/bin/env python3
import pandas as pd

df = pd.read_csv("out/tables/annotated_ledger.csv")

# Count how many endings each stem occurs with
consistency = df.groupby("stem")["ending"].nunique().reset_index()
consistency = consistency.rename(columns={"ending": "unique_endings"})

# Merge back counts
stem_counts = df.groupby("stem").size().reset_index(name="total_attestations")
result = pd.merge(consistency, stem_counts, on="stem")

# Example endings for quick reference
examples = df.groupby("stem")["ending"].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
result = pd.merge(result, examples, on="stem")

result.to_csv("out/tables/stem_consistency.csv", index=False)
print("Wrote out/tables/stem_consistency.csv")