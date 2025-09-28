#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def main(matrix_csv="out/tables/bundle_item_matrix_weighted.csv",
         out_clusters="out/tables/bundle_clusters.csv",
         out_plot="out/plots/bundle_clusters.png",
         k=3):
    df = pd.read_csv(matrix_csv, index_col=0)

    # Standardize
    X = StandardScaler(with_mean=True, with_std=True).fit_transform(df.values)

    # PCA to 2D
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X)

    # KMeans clusters on PCA space (stable & interpretable)
    km = KMeans(n_clusters=k, n_init="auto", random_state=42)
    labels = km.fit_predict(coords)

    # Save cluster membership
    out_path = Path(out_clusters); out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "bundle": df.index,
        "cluster": labels,
        "pc1": coords[:,0],
        "pc2": coords[:,1]
    }).sort_values(["cluster","bundle"]).to_csv(out_path, index=False)

    # Plot
    plt.figure(figsize=(10,8))
    plt.scatter(coords[:,0], coords[:,1], c=labels, s=80)
    for i, b in enumerate(df.index):
        plt.text(coords[i,0]+0.02, coords[i,1]+0.02, b, fontsize=7)
    plt.title("Linear A Bundles — PCA + KMeans")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    Path(out_plot).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_plot, dpi=300, bbox_inches="tight")
    print(f"Wrote {out_clusters} and {out_plot}")
    print(f"PCA explained variance ratio: {pca.explained_variance_ratio_}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", default="out/tables/bundle_item_matrix_weighted.csv")
    ap.add_argument("--out_clusters", default="out/tables/bundle_clusters.csv")
    ap.add_argument("--out_plot", default="out/plots/bundle_clusters.png")
    ap.add_argument("--k", type=int, default=3)
    args = ap.parse_args()
    main(args.matrix, args.out_clusters, args.out_plot, args.k)