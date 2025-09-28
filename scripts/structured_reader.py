#!/usr/bin/env python3
import re, glob
from pathlib import Path
import pandas as pd

# --- Load glossary (same file you already created) ---
def load_glossary(path="out/tables/glossary_hypothesis.tsv"):
    df = pd.read_csv(path, sep="\t")
    d = {}
    for _, r in df.iterrows():
        d[r["token"]] = (r["role"], r["hypothesis"], r["confidence"])
    return d

# Units we want to normalize (AB22-first canonical form)
CANON_UNITS = {
    "AB22 AB67", "AB22 AB03", "AB22 AB09", "AB22 AB59",
    "AB22 AB40", "AB22 AB41", "AB22 AB54", "AB22 AB28"
}

def normalize_pair(p):
    """Normalize reversed unit pairs like 'AB67 AB22' -> 'AB22 AB67'."""
    a, b = p.split()
    if a == "AB22":
        return p
    if b == "AB22":
        cand = f"AB22 {a}"
        return cand if cand in CANON_UNITS else p
    return p

def is_AB(token): return token.startswith("AB")
def is_num(token): return bool(re.fullmatch(r"\d+", token))

def parse_line(tokens):
    """
    Reconstruct sequences of: STEM (ABxx AByy) + LINK AB22 + ENDING (ABzz) + NUMBER
    Return a list of dicts: {stem, ending, number, raw}
    """
    seqs = []
    i = 0
    n = len(tokens)
    while i < n - 3:
        # pattern: AB AB AB22 AB (then maybe NUMBER later)
        if is_AB(tokens[i]) and is_AB(tokens[i+1]) and tokens[i+2] == "AB22" and is_AB(tokens[i+3]):
            stem = f"{tokens[i]} {tokens[i+1]}"
            ending = f"{tokens[i+2]} {tokens[i+3]}"
            # consume possible number immediately after or a few positions after (robust to stray AB-pairs)
            num = None
            j = i + 4
            while j < n and j <= i + 8:  # lookahead window
                if is_num(tokens[j]):
                    num = int(tokens[j]); break
                j += 1
            seqs.append({"stem": stem, "ending": normalize_pair(ending), "number": num,
                         "raw": " ".join(tokens[i:j+1 if num is not None else i+4])})
            i = j if (num is not None and j > i) else i + 4
        else:
            i += 1
    return seqs

def gloss_item(pair, gl):
    info = gl.get(pair)
    if not info: return ("unknown", "", "")
    return info  # (role, hypothesis, confidence)

def render_seq(seq, gl):
    s_role, s_hyp, s_conf = gloss_item(seq["stem"], gl)
    e_role, e_hyp, e_conf = gloss_item(seq["ending"], gl)
    num = seq["number"]
    parts = []
    if s_hyp: parts.append(f"{seq['stem']} ≈ {s_hyp} [{s_conf}]")
    else:     parts.append(f"{seq['stem']} (unknown)")
    if e_hyp: parts.append(f"{seq['ending']} ≈ {e_hyp} [{e_conf}]")
    else:     parts.append(f"{seq['ending']} (unit?)")
    parts.append(f"count={num}" if num is not None else "count=?")
    return " — ".join(parts)

def summarize_line(seqs, gl):
    """Compact template like: 'ration: grain(12 big-unit); oil(5 small-unit)' when multiple seqs."""
    if not seqs: return "no structured sequence found"
    chunks = []
    for seq in seqs:
        _, s_hyp, _ = gloss_item(seq["stem"], gl)
        _, e_hyp, _ = gloss_item(seq["ending"], gl)
        label = s_hyp or "commodity?"
        unit  = e_hyp or "unit?"
        num   = seq["number"] if seq["number"] is not None else "?"
        chunks.append(f"{label} ({num} {unit})")
    # Heuristic label
    if len(chunks) >= 3: head = "bundle (triad)"
    elif len(chunks) == 2: head = "bundle (pair)"
    else: head = "entry"
    return f"{head}: " + "; ".join(chunks)

def main(clean_dir="data/clean",
         out_csv="out/tables/structured_sequences.csv",
         out_readable_dir="out/readable_structured",
         glossary="out/tables/glossary_hypothesis.tsv"):
    gl = load_glossary(glossary)
    rows = []
    outp = Path(out_readable_dir); outp.mkdir(parents=True, exist_ok=True)

    for f in glob.glob(f"{clean_dir}/*.txt"):
        name = Path(f).name
        lines = Path(f).read_text().splitlines()
        rendered = []
        for idx, line in enumerate(lines, start=1):
            toks = line.strip().split()
            seqs = parse_line(toks)
            # Save sequences to table
            for s in seqs:
                rows.append({
                    "file": name, "line": idx,
                    "stem": s["stem"], "ending": s["ending"],
                    "number": s["number"], "raw_span": s["raw"]
                })
            # Build readable summary
            rseq = " | ".join(render_seq(s, gl) for s in seqs) if seqs else "—"
            template = summarize_line(seqs, gl)
            rendered.append(f"Line {idx}: {line}\n  → {template}\n  · {rseq}\n")
        Path(outp, name.replace(".txt", "_structured.txt")).write_text("\n".join(rendered))

    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"Wrote sequences table to {out_csv}")
    print(f"Wrote readable files to {outp}")

if __name__ == "__main__":
    main()