#!/usr/bin/env python3
import re, argparse
from pathlib import Path

AB = re.compile(r"\bAB\d{1,3}\b", re.I)
IDEO = re.compile(r"\*\d+[A-Z]+", re.I)     # e.g. *201VAS
NUM = re.compile(r"\b\d+\b")
LABEL = re.compile(r"^(?:\.?\d+[a-z]?|line\s+\d+|ht|kh|za|pk)\b", re.I)
STRIP = re.compile(r"[,\[\]•·;]")

def normalize_file(src: Path, dst: Path):
    out = []
    for raw in src.read_text(encoding="utf-8").splitlines():
        s = STRIP.sub(" ", raw).strip()
        if not s:
            out.append("")
            continue
        if s.lower().startswith(("line ", ".")) or LABEL.match(s):
            out.append(s)
            continue
        toks = s.split()
        kept = []
        for t in toks:
            if IDEO.fullmatch(t) or AB.fullmatch(t) or NUM.fullmatch(t):
                kept.append(t.upper())
        out.append(" ".join(kept))
    dst.write_text("\n".join(out), encoding="utf-8")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-i","--in-dir", required=True)
    ap.add_argument("-o","--out-dir", required=True)
    args = ap.parse_args()
    in_dir, out_dir = Path(args.in_dir), Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in sorted(in_dir.glob("*.txt")):
        normalize_file(p, out_dir / p.name)
    print(f"Normalized files → {out_dir}")