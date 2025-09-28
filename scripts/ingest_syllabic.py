#!/usr/bin/env python3
import re, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT   = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

targets = ["HT7.txt","HT8.txt","HT9.txt","HT10.txt","HT12.txt"]
row_re = re.compile(r"^\s*Line\s*\d+\s*:\s*(.+?)\s+(-?\d+)\s*$", re.I)

def parse(p: Path):
    tablet = p.stem
    for line in p.read_text(encoding="utf-8").splitlines():
        m = row_re.match(line)
        if m:
            yield (tablet, m.group(1).strip(), int(m.group(2)), line.strip())

def main():
    rows = []
    for name in targets:
        fp = CLEAN / name
        if fp.exists():
            rows.extend(parse(fp))
    out_csv = OUT / "ht_syllabic_ledger.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["file","item","number","raw"]); w.writerows(rows)
    print(f"Wrote {out_csv} (rows={len(rows)})")

if __name__ == "__main__":
    main()