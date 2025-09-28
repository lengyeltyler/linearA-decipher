#!/usr/bin/env python3
import re, csv, argparse
from pathlib import Path
from collections import Counter

AB   = re.compile(r"\bAB\d{1,3}\b", re.I)
IDEO = re.compile(r"\*\d+[A-Z]+", re.I)   # e.g. *201VAS
NUM  = re.compile(r"^\d+$")
LABEL= re.compile(r"^(?:\.?\d+[a-z]?|line\s+\d+)", re.I)

def tokenize_line(s: str):
    """Return tokens from a line, including the tail after 'Label:' if present."""
    s = s.strip()
    if not s:
        return []
    # If it's a label line, try to parse the tail after a colon (e.g., "Line 1: AB54 AB08 ... 3")
    if LABEL.match(s):
        parts = s.split(":", 1)
        if len(parts) == 2:
            s = parts[1].strip()  # keep only the tail after ':'
        else:
            return []  # pure label with no tokens
    # normalize separators
    s = s.replace(",", " ")
    return [t for t in s.split() if t]

def read_segments(p: Path):
    segs = []
    cur = []
    for raw in p.read_text(encoding="utf-8").splitlines():
        toks = tokenize_line(raw)
        if not toks:
            continue
        for t in toks:
            if IDEO.fullmatch(t) or NUM.fullmatch(t):
                if cur:
                    segs.append(cur)
                    cur = []
            elif AB.fullmatch(t):
                cur.append(t.upper())
            # else ignore
    if cur:
        segs.append(cur)
    return segs

def main():
    ap = argparse.ArgumentParser(description="Segment by ideograms/numbers; list recurring chunks.")
    ap.add_argument("-d","--dir", required=True, help="data/clean")
    ap.add_argument("-o","--out-prefix", default="out/tables/segments")
    ap.add_argument("--min-len", type=int, default=2, help="minimum AB tokens per segment")
    a = ap.parse_args()

    files = sorted(Path(a.dir).glob("*.txt"))
    segs_all = []
    for f in files:
        segs = read_segments(f)
        segs_all.extend([s for s in segs if len(s) >= a.min_len])

    # whole-segment frequency
    seg_counter = Counter(tuple(s) for s in segs_all)

    # internal n-grams (within segments)
    bigr = Counter()
    trigr = Counter()
    for s in segs_all:
        for i in range(len(s)-1):
            bigr.update([(s[i], s[i+1])])
        for i in range(len(s)-2):
            trigr.update([(s[i], s[i+1], s[i+2])])

    out_dir = Path(a.out_prefix).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir/"segment_list.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["segment_tokens","count"])
        for seg, c in seg_counter.most_common():
            w.writerow([" ".join(seg), c])

    with (out_dir/"segment_bigrams.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["s1","s2","count"])
        for (a1, a2), c in bigr.most_common():
            w.writerow([a1, a2, c])

    with (out_dir/"segment_trigrams.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["s1","s2","s3","count"])
        for (a1, a2, a3), n in trigr.most_common():
            w.writerow([a1, a2, a3, n])

    print("Wrote: out/tables/segment_list.csv, segment_bigrams.csv, segment_trigrams.csv")

if __name__ == "__main__":
    main()