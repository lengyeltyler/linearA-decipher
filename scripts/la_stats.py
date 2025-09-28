#!/usr/bin/env python3
import re, csv, json, argparse
from pathlib import Path
from collections import Counter, defaultdict

AB = re.compile(r"\bAB\d{1,3}\b", re.I)
IDEO = re.compile(r"\*\d+[A-Z]+", re.I)
NUM = re.compile(r"^\d+$")
LABEL = re.compile(r"^(?:\.?\d+[a-z]?|line\s+\d+)", re.I)

def read_tablet(path: Path):
    rows=[]
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or LABEL.match(s): rows.append(("LABEL", s)); continue
        toks = [t for t in s.replace(",", " ").split() if t]
        rows.append(("DATA", toks))
    return rows

def analyze(dirpath: Path):
    files = sorted(dirpath.glob("*.txt"))
    freqs=Counter(); ideos=Counter(); nums=Counter()
    bigr=Counter(); trigr=Counter(); starts=Counter(); ends=Counter()
    contexts=defaultdict(Counter)
    for f in files:
        for kind,toks in read_tablet(f):
            if kind!="DATA": continue
            signs=[t.upper() for t in toks if AB.fullmatch(t)]
            ideos.update([t.upper() for t in toks if IDEO.fullmatch(t)])
            nums.update([t for t in toks if NUM.fullmatch(t)])
            if signs:
                starts.update([signs[0]]); ends.update([signs[-1]])
            for i in range(len(signs)-1):
                a,b=signs[i],signs[i+1]
                bigr.update([(a,b)]); contexts[a].update([b]); contexts[b].update([a])
            for i in range(len(signs)-2):
                trigr.update([(signs[i],signs[i+1],signs[i+2])])
    return dict(freqs=freqs, ideos=ideos, nums=nums, bigr=bigr,
                trigr=trigr, starts=starts, ends=ends,
                contexts={k:dict(v) for k,v in contexts.items()})

def write_out(res, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    def dump_ctr(name, ctr, headers):
        with (outdir/f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
            w=csv.writer(f); w.writerow(headers)
            rows = ctr.most_common() if hasattr(ctr,"most_common") else ctr.items()
            for k,v in rows: w.writerow([k,v])
    dump_ctr("freq_signs", res["freqs"], ["sign","count"])
    dump_ctr("freq_ideograms", res["ideos"], ["ideogram","count"])
    dump_ctr("freq_numbers", res["nums"], ["number","count"])
    dump_ctr("starts", res["starts"], ["sign","line_initial_count"])
    dump_ctr("ends", res["ends"], ["sign","line_final_count"])
    with (outdir/"bigrams.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["s1","s2","count"])
        for (a,b),c in res["bigr"].most_common(): w.writerow([a,b,c])
    with (outdir/"trigrams.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["s1","s2","s3","count"])
        for (a,b,c),n in res["trigr"].most_common(): w.writerow([a,b,c,n])
    (outdir/"contexts.json").write_text(json.dumps(res["contexts"],indent=2), encoding="utf-8")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("-d","--dir", required=True)
    ap.add_argument("-o","--out", default="out/tables")
    a=ap.parse_args()
    res=analyze(Path(a.dir))
    write_out(res, Path(a.out))
    print(f"Wrote CSV/JSON to {a.out}")