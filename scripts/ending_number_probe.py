#!/usr/bin/env python3
import re, csv, argparse
from pathlib import Path
from collections import defaultdict

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

def segments_with_numbers(indir: Path):
    segs=[]
    for f in sorted(indir.glob("*.txt")):
        cur=[]
        for raw in f.read_text(encoding="utf-8").splitlines():
            toks = tokenize_line(raw)
            if not toks: continue
            # find numbers at end of line
            num = None
            if NUM.fullmatch(toks[-1]):
                num = int(toks[-1])
                toks = toks[:-1]
            # store full token list + number
            segs.append((f.name, toks, num))
    return segs

if __name__=="__main__":
    ap=argparse.ArgumentParser(description="Correlate AB22 endings with following numbers.")
    ap.add_argument("-d","--dir", required=True, help="data/clean")
    ap.add_argument("-o","--out", default="out/tables/ending_number_stats.csv")
    a=ap.parse_args()

    segs = segments_with_numbers(Path(a.dir))

    # Collect numbers by ending sign after AB22
    ending_to_nums = defaultdict(list)

    for fname, toks, num in segs:
        for i,tok in enumerate(toks):
            if tok=="AB22" and i+1 < len(toks):
                ending = toks[i+1]
                if num is not None:
                    ending_to_nums[ending].append(num)

    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["ending_sign","count","avg_number","numbers"])
        for end, nums in ending_to_nums.items():
            if not nums: continue
            avg = sum(nums)/len(nums)
            w.writerow([end, len(nums), round(avg,2), " ".join(map(str,nums))])

    print(f"Wrote {a.out}")