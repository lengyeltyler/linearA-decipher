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
                    if cur: segs.append(cur); cur=[]
                elif AB.fullmatch(t):
                    cur.append(t.upper())
        if cur: segs.append(cur)
    return segs

if __name__=="__main__":
    ap=argparse.ArgumentParser(description="Mine prefix/suffix patterns inside segments.")
    ap.add_argument("-d","--dir", required=True, help="data/clean")
    ap.add_argument("-o","--outdir", default="out/tables")
    ap.add_argument("--minlen", type=int, default=2, help="min AB tokens per segment")
    a=ap.parse_args()

    segs=[s for s in segments_from_dir(Path(a.dir)) if len(s)>=a.minlen]

    pref1=Counter(); pref2=Counter(); suff1=Counter(); suff2=Counter(); lengths=Counter()
    for s in segs:
        lengths.update([len(s)])
        pref1.update([s[0]])
        suff1.update([s[-1]])
        if len(s)>=2:
            pref2.update([(s[0], s[1])])
            suff2.update([(s[-2], s[-1])])

    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)

    def dump_ctr(name, ctr, headers):
        with (out/name).open("w", newline="", encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(headers)
            for k,v in ctr.most_common():
                if isinstance(k, tuple): k=" ".join(k)
                w.writerow([k,v])

    dump_ctr("prefix1.csv", pref1, ["prefix1","count"])
    dump_ctr("prefix2.csv", pref2, ["prefix2","count"])
    dump_ctr("suffix1.csv", suff1, ["suffix1","count"])
    dump_ctr("suffix2.csv", suff2, ["suffix2","count"])
    dump_ctr("segment_lengths.csv", lengths, ["len_tokens","count"])

    print("Wrote:",
          "out/tables/prefix1.csv, prefix2.csv, suffix1.csv, suffix2.csv, segment_lengths.csv")