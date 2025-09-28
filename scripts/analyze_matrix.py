#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

def main(matrix_csv="out/tables/stem_ending_matrix.csv", out_png="out/plots/stem_clusters.png"):
    df = pd.read_csv(matrix_csv)

    # Keep stem column separate
    stems = df["stem"]
    X = df.drop(columns=["stem"])

    # Apply PCA (2D)
    pca = PCA(n_components=2)
    coords = pca.fit_transform(X)

    # Make plot
    plt.figure(figsize=(8,6))
    plt.scatter(coords[:,0], coords[:,1], c="blue")

    for i, label in enumerate(stems):
        plt.text(coords[i,0]+0.02, coords[i,1]+0.02, label, fontsize=8)

    plt.title("Linear A Stems (PCA projection)")
    plt.xlabel("PC1")
    plt.ylabel("PC2")

    out_path = Path(out_png)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Wrote PCA plot to {out_path}")

if __name__ == "__main__":
    main()