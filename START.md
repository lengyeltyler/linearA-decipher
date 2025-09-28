source .venv/bin/activate
bash scripts/run_pipeline.sh

Step 0 — Add tablets
	•	Drop new tablet files (plain text) into data/clean/ as *.txt.
Each line should look like:
ABxx AByy AB22 ABzz N (where N is the trailing number).


Step 1 — Extract ledger sequences
python3 scripts/analyze_ledger.py -d data/clean

Outputs:
	•	outputs/structured_sequences.csv (stem, ending, number per line)
	•	outputs/ending_totals.csv and other diagnostics


Step 2 — Summarize stems/endings (draft lexicon cues)
python3 scripts/stabilize_lexicon.py

Outputs:
	•	outputs/lexicon_summary.csv (what stems/endings appear and how often)


Step 3 — Produce labeled rows for translation

This applies your current best dictionary to the sequences.
python3 scripts/substitute_dictionary.py

Outputs:
	•	outputs/tablets_substituted.csv
(columns: file, line, stem, ending, number, stem_label, ending_label)


Step 4 — Render proto-translations (readable lines)
python3 scripts/render_translations.py

Outputs:
	•	outputs/proto_translations.csv
	•	outputs/proto_translations/HT13_translated.txt (and friends)


Step 5 — Mine templates & freeze dictionary
python3 scripts/mine_templates.py
python3 scripts/validate_constraints.py

Outputs:
	•	outputs/phrase_templates.csv, commodity_unit_counts.csv
	•	outputs/constraint_violations.csv (ideally empty)
	•	outputs/lexicon_frozen.json (frozen dictionary snapshot)


Step 6 — Render final tablets using frozen dictionary
python3 scripts/render_final.py

Outputs:
	•	outputs/final_translations.csv
	•	outputs/final_translations/*_final.txt


(Optional) Step 7 — Volume math & clustering
python3 scripts/report_volumes.py
python3 scripts/analyze_volumes.py

Outputs:
	•	outputs/tablet_volumes.csv, volume_report.txt
	•	outputs/volume_clusters_*.png, volume_clusters.csv

Shortcut: once Steps 1–3 are done, you can run the one-click:

bash scripts/run_pipeline.sh


push to github
git add .
git commit -m "updates"
git push