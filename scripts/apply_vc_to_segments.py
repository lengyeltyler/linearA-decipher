#!/usr/bin/env python3
import re, csv, argparse
from pathlib import Path

AB   = re.compile(r"\bAB\d{1,3}\b", re.I)
IDEO = re.compile(r"\*\d+[A-Z]+", re.I)
NUM  = re.compile(r"^\d+$")
LABEL= re.compile(r"^(?:\.?\d+[a-z]?|line\s+\d+)", re.I)

def tokenize_line(s: str):
    s = s.strip()
    if not s: return []
    if LABEL.match(s):
        parts = s.split(":", 1)
        if len(parts) == 2: s = parts[1].strip()
        else: return []
    s = s.replace(",", " ")
    return [t for t in s.split() if t]

def segments_from_dir(indir: Path):
    segs=[]
    for f in sorted(indir.glob("*.txt")):
        cur=[]
        for raw in f.read_text(encoding="utf-8").splitlines():
            for t in tokenize_line(raw):
                if IDEO.fullmatch(t) or NUM.fullmatch(t):
                    if cur: segs.append(cur); cur=[]
                elif AB.fullmatch(t):
                    cur.append(t.upper())
        if cur: segs.append(cur)
    return segs

def read_best_vowels(tsv_path: Path):
    vowels=set()
    if not tsv_path.exists(): return vowels
    for line in tsv_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("vowels"):
            _, val = line.split("\t",1)
            for s in val.strip().split():
                vowels.add(s.strip())
    return vowels

if __name__=="__main__":
    ap=argparse.ArgumentParser(description="Annotate segments with V/C patterns from best vowel set.")
    ap.add_argument("-d","--dir", required=True, help="data/clean")
    ap.add_argument("--best", default="out/tables/vc_best.tsv")
    ap.add_argument("-o","--out", default="out/tables/segment_vc_patterns.csv")
    a=ap.parse_args()

    vowels = read_best_vowels(Path(a.best))
    segs   = segments_from_dir(Path(a.dir))

    with open(a.out,"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["segment_tokens","pattern","len"])
        for s in segs:
            pats = "".join("V" if tok in vowels else "C" for tok in s)
            w.writerow([" ".join(s), pats, len(s)])

    print(f"Wrote {a.out}")