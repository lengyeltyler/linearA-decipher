#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(__file__))          # project root
OUT = os.path.join(BASE, "outputs")
VOL_CSV = os.path.join(OUT, "tablet_volumes.csv")
CLUST_CSV = os.path.join(OUT, "volume_clusters.csv")

os.makedirs(OUT, exist_ok=True)

# --- helpers ---
def classify_tablet(row):
    """Rule-of-thumb type label using liters."""
    grain = row.get("grain", 0.0)
    oil   = row.get("oil", 0.0)
    wine  = row.get("wineA", 0.0) + row.get("wineB", 0.0)

    if grain > 0 and oil > 0 and wine > 0:
        # check how close to a 10:1:~10 style (tolerant)
        g, o, w = grain, oil, wine
        base = min(v for v in [g, o, w] if v > 0)
        ratio = (g/base, o/base, w/base)
        # Very loose acceptance for “triadic-like”
        if ratio[0] >= 8 and ratio[1] >= 1 and ratio[2] >= 6:
            return "triadic_ledger"
        return "mixed_ledger"
    if grain > 0 and wine == 0:
        return "grain_dominant"
    return "other"

def sum_by_commodity(vol_df):
    sums = (vol_df
            .pivot_table(index="file", columns="commodity",
                         values="liters", aggfunc="sum", fill_value=0)
            .reset_index())
    for col in ["grain","oil","wineA","wineB"]:
        if col not in sums.columns:
            sums[col] = 0.0
    return sums

def write_text_report(sums, clusters_path, out_txt):
    # read cluster assignments if available
    clusters = None
    if os.path.exists(clusters_path):
        clusters = pd.read_csv(clusters_path).set_index("file")["cluster"].to_dict()

    lines = []
    for _, r in sums.iterrows():
        file = r["file"]
        grain = float(r["grain"])
        oil   = float(r["oil"])
        wine  = float(r["wineA"] + r["wineB"])
        total = grain + oil + wine
        label = classify_tablet(r)
        cl = clusters.get(file, "NA") if clusters else "NA"

        # normalized ratios (avoid div by zero)
        base = min([v for v in [grain,oil,wine] if v > 0], default=1.0)
        ratio = (round(grain/base,1) if grain>0 else 0,
                 round(oil/base,1)   if oil>0   else 0,
                 round(wine/base,1)  if wine>0  else 0)

        lines.append(f"Tablet {file}  [cluster {cl}]  → type: {label}")
        lines.append(f"  Grain {grain:.1f} L | Oil {oil:.1f} L | Wine {wine:.1f} L | Total {total:.1f} L")
        lines.append(f"  Ratio (G:O:W) ≈ {ratio}\n")

    with open(out_txt, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote report: {out_txt}")

def make_bar_charts(sums, out_png):
    # stacked bars per tablet: grain, oil, wine
    tablets = sums["file"].tolist()
    grain = sums["grain"].tolist()
    oil   = sums["oil"].tolist()
    wine  = (sums["wineA"] + sums["wineB"]).tolist()

    plt.figure(figsize=(10,6))
    x = range(len(tablets))
    plt.bar(x, grain, label="Grain (L)")
    plt.bar(x, oil, bottom=grain, label="Oil (L)")
    plt.bar(x, wine, bottom=[g+o for g,o in zip(grain, oil)], label="Wine (L)")
    plt.xticks(list(x), tablets, rotation=45, ha="right")
    plt.ylabel("Liters")
    plt.title("Commodity volumes per tablet (stacked)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png)
    plt.close()
    print(f"Wrote chart: {out_png}")

def main():
    vol = pd.read_csv(VOL_CSV)  # requires outputs/tablet_volumes.csv
    sums = sum_by_commodity(vol)
    # write text report
    write_text_report(sums, CLUST_CSV, os.path.join(OUT, "volume_report.txt"))
    # write stacked bar chart
    make_bar_charts(sums, os.path.join(OUT, "volume_bars.png"))

if __name__ == "__main__":
    main()