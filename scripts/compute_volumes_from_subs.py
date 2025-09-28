#!/usr/bin/env python3
import csv, json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

SUBS = OUT / "tablets_substituted.csv"
VOL_JSON = ROOT / "data" / "volumes.json"

# Aliases: map raw endings → unit names
UNIT_ALIASES = {
    "AB22 AB67": "big_jar",
    "AB22 AB03": "small_jar",
    "AB22 AB09": "amphoraA",
    "AB22 AB59": "amphoraB",
    "AB22 AB28": "large_measure",
    "AB22 AB40": "measure_tag",
    "AB22 AB54": "unit?",
    "AB22 AB69": "big_jar",   # guess
}

# Default volumes if data/volumes.json not found
DEFAULT_VOLUMES = {
    "small_jar": 5.0,
    "big_jar": 50.0,
    "amphoraA": 30.0,
    "amphoraB": 30.0,
    "large_measure": 10.0,
    "measure_tag": 1.0,
    "unit?": 0.0,
}

def resolve_unit(row):
    """Resolve ending → human-readable unit name"""
    # prefer ending_label if it already matches a known unit
    ending_label = (row.get("ending_label") or "").strip()
    if ending_label in DEFAULT_VOLUMES:
        return ending_label
    # otherwise map the raw ending through aliases
    raw_ending = (row.get("ending") or "").strip()
    if raw_ending in UNIT_ALIASES:
        return UNIT_ALIASES[raw_ending]
    # fallback
    return "unit?"

def main():
    if not SUBS.exists():
        raise SystemExit(f"Missing {SUBS}. Run the earlier steps first.")

    if VOL_JSON.exists():
        volumes = json.loads(VOL_JSON.read_text(encoding="utf-8"))
    else:
        volumes = DEFAULT_VOLUMES

    rows = []
    with SUBS.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)

    # Aggregate per (file, commodity, resolved_unit)
    agg = defaultdict(lambda: {"count": 0, "unit_name": None})
    for row in rows:
        file = row["file"]
        commodity = (row.get("stem_label") or "").strip() or "commodity?"
        unit_name = resolve_unit(row)
        n = int(row["number"])
        agg[(file, commodity, unit_name)]["count"] += n
        agg[(file, commodity, unit_name)]["unit_name"] = unit_name

    # Write tablet_volumes.csv
    out_csv = OUT / "tablet_volumes.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file","commodity","unit","count","liters"])
        for (file, commodity, unit), data in sorted(agg.items()):
            count = data["count"]
            liters = count * float(volumes.get(unit, 0.0))
            w.writerow([file, commodity, unit, count, liters])
    print(f"✔ wrote {out_csv}")

    # Pretty per-tablet text report (tablet_volumes.txt)
    totals = defaultdict(lambda: defaultdict(float))
    for (file, commodity, unit), data in agg.items():
        count = data["count"]
        liters = count * float(volumes.get(unit, 0.0))
        totals[file][commodity] += liters

    out_txt = OUT / "tablet_volumes.txt"
    with out_txt.open("w", encoding="utf-8") as f:
        for file in sorted(totals):
            f.write(f"Tablet {file} — volume totals:\n")
            for commodity, L in sorted(totals[file].items(), key=lambda x: -x[1]):
                f.write(f"  • {commodity:10s} {L:.1f} L\n")
            f.write("\n")
    print(f"✔ wrote {out_txt}")

if __name__ == "__main__":
    main()