#!/usr/bin/env python3
import csv
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

VOL_CSV = OUT / "tablet_volumes.csv"
RATIO_CSV = OUT / "volume_clusters.csv"
SCATTER_PNG = OUT / "volume_clusters_scatter.png"
DENDRO_PNG = OUT / "volume_clusters_dendrogram.png"  # left in case you want to add linkage later

def main():
    if not VOL_CSV.exists():
        raise SystemExit(f"Missing {VOL_CSV}. Run compute_volumes_from_subs.py first.")

    df = pd.read_csv(VOL_CSV)

    # Keep only the three anchor commodities for ratios; everything else is ignored here
    df["commodity_norm"] = df["commodity"].str.lower()
    df["commodity_norm"] = df["commodity_norm"].replace({
        "winea": "wine",
        "wineb": "wine"
    })

    piv = (df[df["commodity_norm"].isin(["grain","oil","wine"])]
           .pivot_table(index="file", columns="commodity_norm", values="liters", aggfunc="sum"))

    # Ensure all three columns exist; fill missing with 0
    for col in ["grain","oil","wine"]:
        if col not in piv.columns:
            piv[col] = 0.0
    piv = piv[["grain","oil","wine"]].fillna(0.0)

    # Drop tablets with total liters == 0 (avoid 0/0 -> NaN)
    totals = piv.sum(axis=1)
    good = totals > 0
    clean = piv.loc[good].copy()

    if clean.empty or len(clean) < 2:
        # Not enough data to cluster; still write a simple CSV and quit gracefully
        ratio_df = clean.copy()
        ratio_df["total"] = ratio_df.sum(axis=1)
        for col in ["grain","oil","wine"]:
            ratio_df[col] = np.where(ratio_df["total"] > 0, ratio_df[col] / ratio_df["total"], 0.0)
        ratio_df = ratio_df.drop(columns=["total"]).reset_index()
        ratio_df["cluster"] = 0
        ratio_df.to_csv(RATIO_CSV, index=False)
        print(f"✔ wrote {RATIO_CSV} (no clustering: not enough tablets)")
        return

    # Ratios (safe: total > 0 by filter)
    ratio_df = clean.copy()
    ratio_df["total"] = ratio_df.sum(axis=1)
    for col in ["grain","oil","wine"]:
        ratio_df[col] = ratio_df[col] / ratio_df["total"]
    ratio_df = ratio_df.drop(columns=["total"]).reset_index()  # columns: file, grain, oil, wine

    # KMeans on standardized ratios; k=2 (triadic vs grain-dominant previously worked)
    X = ratio_df[["grain","oil","wine"]].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    k = 2 if len(ratio_df) >= 2 else 1
    kmeans = KMeans(n_clusters=k, n_init="auto", random_state=42)
    ratio_df["cluster"] = kmeans.fit_predict(X_scaled) if k > 1 else 0

    # Write CSV
    ratio_df.to_csv(RATIO_CSV, index=False)
    print(f"✔ wrote {RATIO_CSV}")

    # Scatter (grain vs wine; point size ~ oil share)
    plt.figure(figsize=(6,5))
    plt.scatter(ratio_df["grain"], ratio_df["wine"], s=200*ratio_df["oil"]+30, alpha=0.8)
    for _, row in ratio_df.iterrows():
        plt.annotate(row["file"].replace(".txt",""), (row["grain"], row["wine"]), xytext=(3,3), textcoords="offset points")
    plt.xlabel("Grain share")
    plt.ylabel("Wine share")
    plt.title("Tablet commodity share (size = Oil share)")
    plt.grid(True, linestyle=":")
    plt.tight_layout()
    plt.savefig(SCATTER_PNG, dpi=150)
    plt.close()
    print(f"✔ saved {SCATTER_PNG}")

    # (Optional) Dendrogram placeholder: not computing linkage here; keep file absent by default.

if __name__ == "__main__":
    main()