import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from scipy.cluster.hierarchy import linkage, dendrogram
import os

# === Paths ===
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "outputs", "tablet_volumes.csv")
OUT_DIR = os.path.join(BASE_DIR, "outputs")

# === Step 1: Load data ===
df = pd.read_csv(DATA_PATH)

# Keep only grain, oil, wine rows
triad_df = df[df["commodity"].isin(["grain", "oil", "wineA", "wineB"])].copy()
triad_df["commodity"] = triad_df["commodity"].replace({"wineA": "wine", "wineB": "wine"})

# === Step 2: Pivot into wide format ===
pivot = triad_df.pivot_table(
    index="file",
    columns="commodity",
    values="liters",
    aggfunc="sum",
    fill_value=0
).reset_index()

# Ensure consistent columns
for col in ["grain", "oil", "wine"]:
    if col not in pivot.columns:
        pivot[col] = 0

# === Step 3: Normalize ratios ===
ratio_df = pivot.copy()
totals = ratio_df[["grain", "oil", "wine"]].sum(axis=1)
for col in ["grain", "oil", "wine"]:
    ratio_df[col] = ratio_df[col] / totals

# === Step 4: KMeans clustering ===
X = ratio_df[["grain", "oil", "wine"]].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
ratio_df["cluster"] = kmeans.fit_predict(X_scaled)

# === Step 5: Save CSV ===
ratio_df[["file", "grain", "oil", "wine", "cluster"]].to_csv(
    os.path.join(OUT_DIR, "volume_clusters.csv"), index=False
)

# === Step 6: Scatter plot ===
plt.figure(figsize=(8,6))
for c in ratio_df["cluster"].unique():
    subset = ratio_df[ratio_df["cluster"] == c]
    plt.scatter(subset["grain"], subset["wine"], s=100, label=f"Cluster {c}")
plt.xlabel("Grain (normalized ratio)")
plt.ylabel("Wine (normalized ratio)")
plt.title("Tablet Clusters by Grain–Wine Ratio")
plt.legend()
plt.savefig(os.path.join(OUT_DIR, "volume_clusters_scatter.png"))
plt.close()

# === Step 7: Dendrogram ===
linked = linkage(X_scaled, method="ward")
plt.figure(figsize=(8,6))
dendrogram(linked, labels=ratio_df["file"].values, leaf_rotation=90)
plt.title("Hierarchical Clustering of Tablets (Grain/Oil/Wine Ratios)")
plt.savefig(os.path.join(OUT_DIR, "volume_clusters_dendrogram.png"))
plt.close()

print("✅ Analysis complete. Files written to outputs/:")
print(" - volume_clusters.csv")
print(" - volume_clusters_scatter.png")
print(" - volume_clusters_dendrogram.png")