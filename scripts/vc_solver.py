#!/usr/bin/env python3
import re, csv, json, math, argparse
from pathlib import Path
from collections import Counter

AB = re.compile(r"\bAB\d{1,3}\b", re.I)
IDEO= re.compile(r"\*\d+[A-Z]+", re.I)
NUM = re.compile(r"^\d+$")
LABEL=re.compile(r"^(?:\.?\d+[a-z]?|line\s+\d+)", re.I)

def read_sequences(dirpath: Path):
    seqs=[]
    for f in sorted(dirpath.glob("*.txt")):
        for raw in f.read_text(encoding="utf-8").splitlines():
            s=raw.strip()
            if not s or LABEL.match(s): continue
            toks=[t for t in s.replace(","," ").split() if t]
            # keep only AB signs for parsing; break at ideos/nums
            cur=[]
            for t in toks:
                if AB.fullmatch(t):
                    cur.append(t.upper())
                elif IDEO.fullmatch(t) or NUM.fullmatch(t):
                    if cur: seqs.append(cur); cur=[]
            if cur: seqs.append(cur)
    return seqs

def load_vowel_candidates(path: Path, topk: int):
    # expects out/tables/vowel_candidates.csv
    rows=[]
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            sign,freq,neigh,edge,score = line.strip().split(",")
            rows.append((sign, float(score)))
    rows.sort(key=lambda r:r[1], reverse=True)
    return [s for s,_ in rows[:topk]]

def score_parse(seq, vowels:set, templates):
    # templates are tuples like ("C","V","C"), ("C","V")
    # greedy window over sequence; count how many tokens fall into any template
    i=0; covered=0; chunks=0
    while i < len(seq):
        matched=False
        for tpl in templates:
            L=len(tpl)
            if i+L<=len(seq):
                ok=True
                for j,ch in enumerate(tpl):
                    is_v = seq[i+j] in vowels
                    if ch=="V" and not is_v: ok=False; break
                    if ch=="C" and is_v: ok=False; break
                if ok:
                    covered += L; chunks += 1
                    i += L
                    matched=True
                    break
        if not matched:
            i += 1
    # score rewards coverage and compact chunking
    return covered, chunks

def try_assignments(seqs, cand_vowels, k_values, templates):
    results=[]
    all_signs = list({s for seq in seqs for s in seq})
    freq = Counter(s for seq in seqs for s in seq)
    for k in k_values:
        vowels=set(cand_vowels[:k])  # take top-k by vowelish score
        covTot=0; chunksTot=0; tokensTot=sum(len(s) for s in seqs)
        sample_out=[]
        for idx,seq in enumerate(seqs[:200]):  # score on a slice for speed
            cov,ch=score_parse(seq, vowels, templates)
            covTot+=cov; chunksTot+=ch
            if idx<10:
                sample_out.append((seq, cov, ch))
        score = covTot / max(1,tokensTot)
        results.append({
            "k": k,
            "score_coverage": round(score,4),
            "vowels": sorted(vowels),
            "avg_chunk_len": round((covTot/max(1,chunksTot)),3) if chunksTot else 0.0,
            "samples": sample_out
        })
    results.sort(key=lambda r:r["score_coverage"], reverse=True)
    return results, freq, all_signs

def main():
    ap=argparse.ArgumentParser(description="Assign vowels to maximize parseability under CV/CVC templates.")
    ap.add_argument("-d","--dir", required=True, help="data/clean")
    ap.add_argument("--vowel-csv", default="out/tables/vowel_candidates.csv",
                    help="ranking produced by la_vowel_probe.py")
    ap.add_argument("--topk", type=int, default=25, help="how many top candidates to consider")
    ap.add_argument("--k-values", default="3,4,5,6,7", help="number of vowels to test")
    ap.add_argument("-o","--out", default="out/tables/vc_results.json")
    args=ap.parse_args()

    seqs = read_sequences(Path(args.dir))
    cand = load_vowel_candidates(Path(args.vowel_csv), args.topk)
    k_vals = [int(x) for x in args.k_values.split(",")]

    # Define syllable templates to test (tweak as needed)
    templates = [
        ("C","V"), ("V","C"), ("C","V","C"), ("V"), ("C")
    ]

    results, freq, signs = try_assignments(seqs, cand, k_vals, templates)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Write a quick TSV summary of the best run
    best = results[0] if results else None
    if best:
        with open("out/tables/vc_best.tsv","w",encoding="utf-8") as f:
            f.write(f"k\t{best['k']}\ncoverage\t{best['score_coverage']}\n")
            f.write("vowels\t" + " ".join(best["vowels"]) + "\n")
    print(f"Wrote {args.out}")
    if results:
        print(f"Best coverage: {results[0]['score_coverage']} with k={results[0]['k']}")
        print("See out/tables/vc_best.tsv for summary.")

if __name__=="__main__":
    main()