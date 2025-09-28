# tablet_volumes.py
import pandas as pd
import os

# --- Define unit volume assumptions (liters) ---
UNIT_TO_LITERS = {
    "amphoraA": 30,       # type A amphora
    "amphoraB": 30,       # type B amphora
    "big_jar": 20,        # large pithos
    "small_jar": 5,       # small container
    "measure_tag": 1,     # placeholder / conversion
    "large_measure": 10,  # uncertain unit, guess 10 L
    "unit?": 1            # unknown, keep minimal
}

# --- Known target triad ratios (grain:oil:wine) ---
KNOWN_TRIADS = [
    (12, 1, 6),   # storage/offering ratio
    (10, 1, 5),   # ration variant
]

def load_data(file="tablet_totals.csv"):
    return pd.read_csv(file)

def compute_volumes(df):
    records = []
    summaries = {}

    for _, row in df.iterrows():
        tablet = row["file"]
        commodity = row["commodity"]
        unit = row["unit"]
        n = row["n"]

        liters = n * UNIT_TO_LITERS.get(unit, 1)

        records.append({
            "file": tablet,
            "commodity": commodity,
            "unit": unit,
            "count": n,
            "liters": liters
        })

        if tablet not in summaries:
            summaries[tablet] = {}
        summaries[tablet].setdefault(commodity, 0)
        summaries[tablet][commodity] += liters

    return pd.DataFrame(records), summaries

def normalize_ratio(values, precision=1):
    """Normalize commodity liters into ratios (integers)."""
    if not values or sum(values) == 0:
        return None
    base = min([v for v in values if v > 0])
    return tuple(round(v / base, precision) for v in values)

def detect_triad(grain, oil, wine):
    """Check if ratio matches a known triad (approx)."""
    if not (grain and oil and wine):
        return None
    ratio = normalize_ratio([grain, oil, wine])
    for triad in KNOWN_TRIADS:
        if all(abs(r - t) <= 1 for r, t in zip(ratio, triad)):
            return triad
    return None

def write_outputs(df, summaries, outdir="out"):
    os.makedirs(outdir, exist_ok=True)

    # --- CSV with per-line volumes ---
    df.to_csv(os.path.join(outdir, "tablet_volumes.csv"), index=False)

    # --- Human-readable summaries ---
    with open(os.path.join(outdir, "tablet_volumes.txt"), "w") as f:
        for tablet, commodities in summaries.items():
            f.write(f"Tablet {tablet} — volume totals:\n")
            for comm, liters in commodities.items():
                f.write(f"  • {comm:10s} {liters:.1f} L\n")

            # Check triad ratios
            grain = commodities.get("grain", 0)
            oil = commodities.get("oil", 0)
            wine = commodities.get("wineA", 0) + commodities.get("wineB", 0)

            if grain > 0 and oil > 0 and wine > 0:
                triad = detect_triad(grain, oil, wine)
                if triad:
                    f.write(f"    → Matches triad ratio {triad}\n")
                else:
                    norm = normalize_ratio([grain, oil, wine])
                    f.write(f"    → Grain:Oil:Wine ratio ≈ {norm}\n")
            f.write("\n")

def main():
    df = load_data("tablet_totals.csv")
    vol_df, summaries = compute_volumes(df)
    write_outputs(vol_df, summaries)

if __name__ == "__main__":
    main()