#!/usr/bin/env python3
import re, csv, argparse
from pathlib import Path
from collections import Counter, defaultdict

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

if __name__=="__main__":
    ap=argparse.ArgumentParser(description="Analyze templates around AB22: [stem] AB22 [ending].")
    ap.add_argument("-d","--dir", required=True, help="data/clean")
    ap.add_argument("-o","--outdir", default="out/tables")
    ap.add_argument("--min-stem-len", type=int, default=1)
    a=ap.parse_args()

    segs = segments_from_dir(Path(a.dir))

    # Collect all occurrences of ... AB22 ...
    endings = Counter()
    stems   = Counter()
    pairs   = Counter()   # (stem_tuple, ending_sign)
    examples= {}          # (stem_tuple, ending_sign) -> "file: segment"

    for fname, s in segs:
        for i, tok in enumerate(s):
            if tok == "AB22":
                # left stem: everything before AB22 in this segment
                stem = tuple(s[:i]) if i>=a.min_stem_len else None
                # right ending: the sign immediately after AB22 (if any)
                ending = s[i+1] if i+1 < len(s) else None
                if stem and ending:
                    stems.update([stem])
                    endings.update([ending])
                    pairs.update([(stem, ending)])
                    key = (stem, ending)
                    if key not in examples:
                        # format an example snippet
                        left = " ".join(stem)
                        ex = f"{left} AB22 {ending}"
                        examples[key] = f"{fname}: {ex}"
                # continue scanning the segment (there could be multiple AB22s)

    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)

    # Write top stems (by how often they appear before AB22)
    with (out/"ab22_top_stems.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["stem_tokens","count"])
        for stem,c in stems.most_common():
            w.writerow([" ".join(stem), c])

    # Write top endings (signs that follow AB22)
    with (out/"ab22_top_endings.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["ending_sign","count"])
        for end,c in endings.most_common():
            w.writerow([end, c])

    # Write stem→ending distribution
    with (out/"ab22_stem_ending_pairs.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["stem_tokens","ending_sign","count","example"])
        for (stem,end),c in pairs.most_common():
            w.writerow([" ".join(stem), end, c, examples.get((stem,end), "")])

    print("Wrote:",
          "out/tables/ab22_top_stems.csv,",
          "out/tables/ab22_top_endings.csv,",
          "out/tables/ab22_stem_ending_pairs.csv")