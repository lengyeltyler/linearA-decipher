#!/usr/bin/env python3
import re, csv, argparse
from pathlib import Path
from collections import Counter

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
                    if cur: segs.append((f.name, cur)); cur=[]
                elif AB.fullmatch(t):
                    cur.append(t.upper())
        if cur: segs.append((f.name, cur))
    return segs

def strip_suffix_prefix(seg, suffix2, prefix2):
    s = seg[:]
    # strip suffix2 if present
    for a,b in suffix2:
        if len(s)>=2 and s[-2]==a and s[-1]==b:
            s = s[:-2]
            break
    # strip prefix2 if present
    for a,b in prefix2:
        if len(s)>=2 and s[0]==a and s[1]==b:
            s = s[2:]
            break
    return s

if __name__=="__main__":
    ap=argparse.ArgumentParser(description="Mask common suffix/prefix pairs and recount stems.")
    ap.add_argument("-d","--dir", required=True, help="data/clean")
    ap.add_argument("-o","--outdir", default="out/tables")
    ap.add_argument("--suffix2", action="append", default=[], help='Ending pair, e.g. "AB22 AB67" (repeatable)')
    ap.add_argument("--prefix2", action="append", default=[], help='Opening pair, e.g. "AB54 AB22" (repeatable)')
    ap.add_argument("--minlen", type=int, default=2, help="min tokens after stripping to keep as a stem")
    a=ap.parse_args()

    # parse pairs
    suf_pairs = []
    for s in a.suffix2:
        parts=s.strip().split()
        if len(parts)==2: suf_pairs.append((parts[0].upper(), parts[1].upper()))
    pre_pairs = []
    for s in a.prefix2:
        parts=s.strip().split()
        if len(parts)==2: pre_pairs.append((parts[0].upper(), parts[1].upper()))

    segs = segments_from_dir(Path(a.dir))

    stem_counter = Counter()
    stem_bigr = Counter()
    examples = {}  # stem tuple -> one example (file)

    for fname, seg in segs:
        stem = strip_suffix_prefix(seg, suf_pairs, pre_pairs)
        if len(stem) < a.minlen:
            continue
        t = tuple(stem)
        stem_counter.update([t])
        if t not in examples:
            examples[t] = fname
        for i in range(len(stem)-1):
            stem_bigr.update([(stem[i], stem[i+1])])

    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    with (out/"stems.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["stem_tokens","count","example_file"])
        for stem,c in stem_counter.most_common():
            w.writerow([" ".join(stem), c, examples.get(stem,"")])

    with (out/"stem_bigrams.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["s1","s2","count"])
        for (a1,a2),c in stem_bigr.most_common():
            w.writerow([a1,a2,c])

    print("Wrote: out/tables/stems.csv and out/tables/stem_bigrams.csv")