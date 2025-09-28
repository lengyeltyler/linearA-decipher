#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/outputs"
mkdir -p "$OUT"

echo "=== A) AB-pipeline (safe if files absent) ==="

# Optional diagnostics — only run if present
[ -f "$ROOT/scripts/stem_endings_matrix.py" ] && python3 "$ROOT/scripts/stem_endings_matrix.py" || echo "(skip) stem_endings_matrix.py"
# annotate_ledger.py requires the clean dir; run only if present
if [ -f "$ROOT/scripts/annotate_ledger.py" ]; then
  python3 "$ROOT/scripts/annotate_ledger.py" -d "$ROOT/data/clean" -o "$OUT/annotated_ledger.csv" || true
else
  echo "(skip) annotate_ledger.py"
fi
[ -f "$ROOT/scripts/ledger_summary.py" ] && python3 "$ROOT/scripts/ledger_summary.py" || echo "(skip) ledger_summary.py"

# Stabilize lexicon + substitute dictionary (these you have)
python3 "$ROOT/scripts/stabilize_lexicon.py"
python3 "$ROOT/scripts/substitute_dictionary.py"   # -> outputs/tablets_substituted.csv

echo "=== B) Syllabic tablets -> same 'substituted' format ==="
python3 "$ROOT/scripts/ingest_syllabic.py"         # -> outputs/ht_syllabic_ledger.csv
python3 "$ROOT/scripts/syllabic_to_substituted.py" # appends to outputs/tablets_substituted.csv

echo "=== C) Downstream (exactly as before) ==="
python3 "$ROOT/scripts/render_translations.py"     # -> outputs/proto_translations/*.txt + proto_translations.csv
python3 "$ROOT/scripts/compute_volumes_from_subs.py"   # -> outputs/tablet_volumes.csv + tablet_volumes.txt
python3 "$ROOT/scripts/analyze_volumes.py"         # -> plots, clusters
python3 "$ROOT/scripts/economy_summary.py"         # -> economy_totals.txt

echo "=== D) Final report ==="
python3 "$ROOT/scripts/build_report.py"            # -> outputs/LinearA_report.md + LinearA_report.pdf

echo "Pipeline complete. Report available at outputs/LinearA_report.md and .pdf"