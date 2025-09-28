#!/usr/bin/env python3
import re, csv, argparse
from pathlib import Path

# --- Patterns (same conventions as your other scripts) ---
AB    = re.compile(r"\bAB\d{1,3}\b", re.I)
IDEO  = re.compile(r"\*\d+[A-Z]+", re.I)      # e.g., *201VAS
NUM   = re.compile(r"^\d+$")
LABEL = re.compile(r"^(?:\.?\d+[a-z]?|line\s+\d+)", re.I)  # ".1", ".2a", "Line 3", etc.

def split_label_and_tail(raw: str):
    """
    Returns (label, tail_text_for_tokens).
    Accepts lines like 'Line 4: AB81 AB02 AB22 AB67 12' or just tokens.
    """
    s = raw.strip()
    if not s:
        return ("", "")
    if LABEL.match(s):
        # If there's a colon, everything after it is token content
        parts = s.split(":", 1)
        if len(parts) == 2:
            return (parts[0].strip(), parts[1].strip())
        else:
            # Label only (no tokens on same line)
            return (s, "")
    return ("", s)

def tokenize_tail(tail: str):
    """Tokenize the non-label tail; keep AB###, ideograms, and numbers."""
    if not tail:
        return []
    tail = tail.replace(",", " ")
    toks = [t for t in tail.split() if t]
    return toks

def parse_line_to_segments(tokens):
    """
    Split a line's token stream into 'segments' by ideograms and numbers.
    We keep numbers separately (trailing num for the line is returned by caller).
    """
    seg = []
    segments = []
    for t in tokens:
        if IDEO.fullmatch(t):
            if seg: segments.append(seg); seg = []
        elif AB.fullmatch(t):
            seg.append(t.upper())
        elif NUM.fullmatch(t):
            # numbers are handled at the line level, but if they appear
            # mid-line we use them as a boundary
            if seg: segments.append(seg); seg = []
        else:
            # ignore anything else
            pass
    if seg:
        segments.append(seg)
    return segments

def last_number(tokens):
    """Return (tokens_wo_last_num, trailing_number_or_None)."""
    if tokens and NUM.fullmatch(tokens[-1]):
        try:
            return tokens[:-1], int(tokens[-1])
        except:
            return tokens, None
    return tokens, None

def annotate_dir(indir: Path, out_csv: Path, min_stem_len=1):
    rows = []
    for f in sorted(indir.glob("*.txt")):
        for raw in f.read_text(encoding="utf-8").splitlines():
            label, tail = split_label_and_tail(raw)
            toks = tokenize_tail(tail)
            if not toks:
                continue
            toks_wo_num, trailing_num = last_number(toks)
            segs = parse_line_to_segments(toks_wo_num)

            # For each segment, find [STEM] AB22 [ENDING]
            for si, seg in enumerate(segs, start=1):
                # scan for AB22 in the segment
                for i, tok in enumerate(seg):
                    if tok == "AB22":
                        stem = seg[:i] if i >= min_stem_len else []
                        ending = seg[i+1] if i + 1 < len(seg) else ""
                        if stem and ending:
                            rows.append({
                                "file": f.name,
                                "line_label": label,
                                "segment_index": si,
                                "stem": " ".join(stem),
                                "ending": ending,
                                "number": trailing_num if trailing_num is not None else "",
                                "example": f"{' '.join(stem)} AB22 {ending}" + (f" {trailing_num}" if trailing_num is not None else "")
                            })
                        # continue scanning in case there are multiple AB22s
    # write CSV
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "file","line_label","segment_index","stem","ending","number","example"
        ])
        w.writeheader()
        for r in rows:
            w.writerow(r)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Annotate [STEM] AB22 [UNIT] NUMBER patterns into a ledger CSV.")
    ap.add_argument("-d", "--dir", required=True, help="Input folder (e.g., data/clean)")
    ap.add_argument("-o", "--out", default="out/tables/annotated_ledger.csv")
    ap.add_argument("--min-stem-len", type=int, default=1, help="Minimum tokens before AB22 to accept as stem")
    args = ap.parse_args()

    indir = Path(args.dir)
    out_csv = Path(args.out)
    annotate_dir(indir, out_csv, min_stem_len=args.min_stem_len)
    print(f"Wrote {out_csv}")