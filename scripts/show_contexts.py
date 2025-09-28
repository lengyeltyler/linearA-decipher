#!/usr/bin/env python3
import re, argparse
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

if __name__=="__main__":
    ap=argparse.ArgumentParser(description="Show lines containing a sign or a space-separated stem tuple.")
    ap.add_argument("-d","--dir", required=True, help="data/clean")
    ap.add_argument("--query", required=True, help='e.g., "AB81" or "AB81 AB02"')
    a=ap.parse_args()

    q = [t.strip().upper() for t in a.query.split()]
    files = sorted(Path(a.dir).glob("*.txt"))

    for f in files:
        lines = f.read_text(encoding="utf-8").splitlines()
        for raw in lines:
            toks = tokenize_line(raw)
            if not toks: continue
            toks_up = [t.upper() for t in toks]
            # exact subsequence match
            for i in range(0, len(toks_up)-len(q)+1):
                if toks_up[i:i+len(q)] == q:
                    print(f"[{f.name}] {raw.strip()}")
                    break