#!/usr/bin/env python3
import json, csv, argparse
from pathlib import Path

def readcsv(path):
    out=[]
    with open(path, encoding="utf-8") as f:
        next(f, None)
        for line in f:
            cells=[c.strip() for c in line.split(",")]
            if not cells or len(cells)<2: continue
            out.append((cells[0], int(cells[-1])))
    return dict(out)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--freq", required=True)
    ap.add_argument("--starts", required=True)
    ap.add_argument("--ends", required=True)
    ap.add_argument("--contexts", required=True)
    ap.add_argument("-o","--out", default="out/tables/vowel_candidates.csv")
    a=ap.parse_args()

    freq   = readcsv(a.freq)
    starts = readcsv(a.starts)
    ends   = readcsv(a.ends)
    ctx    = json.loads(Path(a.contexts).read_text(encoding="utf-8"))

    rows=[]
    for s,c in freq.items():
        neighbors=set(ctx.get(s,{}).keys())
        edge = starts.get(s,0)+ends.get(s,0)
        score = (len(neighbors)+1)/(c+1)*100 - 0.1*edge
        rows.append((s,c,len(neighbors),edge,round(score,3)))
    rows.sort(key=lambda r:r[-1], reverse=True)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out,"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["sign","freq","neighbor_types","edge_hits","vowelish_score"])
        w.writerows(rows)
    print(f"Wrote {a.out}")