#!/usr/bin/env python3
import re, csv, argparse
from pathlib import Path
from collections import Counter

AB = re.compile(r"\bAB\d{1,3}\b", re.I)
IDEO = re.compile(r"\*\d+[A-Z]+", re.I)
NUM = re.compile(r"^\d+$")
LABEL = re.compile(r"^(?:\.?\d+[a-z]?|line\s+\d+)", re.I)

def sequences(path: Path):
    seqs=[]; buf=[]
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or LABEL.match(s): continue
        for t in s.replace(",", " ").split():
            if IDEO.fullmatch(t) or NUM.fullmatch(t):
                if buf: seqs.append(buf); buf=[]
            elif AB.fullmatch(t): buf.append(t.upper())
    if buf: seqs.append(buf)
    return seqs

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("-d","--dir", required=True)
    ap.add_argument("-o","--out", default="out/tables/affixes.csv")
    a=ap.parse_args()

    left,right=Counter(),Counter()
    for f in sorted(Path(a.dir).glob("*.txt")):
        for seq in sequences(f):
            if len(seq)>=2:
                left.update([seq[0]])
                right.update([seq[-1]])

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out,"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["position","sign","count"])
        for s,c in left.most_common():  w.writerow(["LEFT",s,c])
        for s,c in right.most_common(): w.writerow(["RIGHT",s,c])
    print(f"Wrote {a.out}")