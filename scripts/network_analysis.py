#!/usr/bin/env python3
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path

def main(in_csv="out/tables/cooccurrence_full.csv",
         out_csv="out/tables/network_stats.csv",
         out_png="out/plots/commodity_network.png"):

    df = pd.read_csv(in_csv)

    # Build graph
    G = nx.Graph()
    for _, row in df.iterrows():
        a, b = row["pair"].split(" + ")
        G.add_edge(a.strip(), b.strip())

    # Compute stats
    stats = []
    for node in G.nodes():
        stats.append({
            "stem": node,
            "degree": G.degree(node),
            "neighbors": ", ".join(G.neighbors(node))
        })

    # Save stats
    out_path_csv = Path(out_csv)
    out_path_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(stats).to_csv(out_path_csv, index=False)

    # Draw graph
    plt.figure(figsize=(10,8))
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx_nodes(G, pos, node_size=800, node_color="lightblue")
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.6)
    nx.draw_networkx_labels(G, pos, font_size=8)
    plt.title("Linear A Commodity Network")
    plt.axis("off")

    out_path_png = Path(out_png)
    out_path_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path_png, dpi=300, bbox_inches="tight")
    print(f"Wrote network stats to {out_path_csv}")
    print(f"Wrote network graph to {out_path_png}")

if __name__ == "__main__":
    main()