import pandas as pd
import os

DATA_PATH = "outputs/tablet_volumes.csv"
OUT_TOTALS = "outputs/economy_totals.csv"
OUT_TXT = "outputs/economy_totals.txt"

df = pd.read_csv(DATA_PATH)

# Aggregate by commodity
totals = df.groupby("commodity")["liters"].sum().reset_index()
totals = totals.sort_values("liters", ascending=False)

# Normalize (percentage of total economy)
grand_total = totals["liters"].sum()
totals["percent"] = totals["liters"] / grand_total * 100

# Save to CSV
os.makedirs("outputs", exist_ok=True)
totals.to_csv(OUT_TOTALS, index=False)

# Save text summary
with open(OUT_TXT, "w") as f:
    f.write("=== Linear A Economic Totals ===\n\n")
    for _, row in totals.iterrows():
        f.write(f"{row['commodity']:12s} {row['liters']:8.1f} L  ({row['percent']:.2f}%)\n")
    f.write(f"\nTOTAL economy: {grand_total:.1f} L\n")

print(f"Saved {OUT_TOTALS} and {OUT_TXT}")