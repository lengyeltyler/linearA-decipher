import pandas as pd
from collections import defaultdict

# Input file with all structured sequences
DATA_PATH = "outputs/structured_sequences.csv"
OUTPUT_PATH = "outputs/lexicon_summary.csv"

def main():
    df = pd.read_csv(DATA_PATH)

    # Count attestations by stem
    lexicon = defaultdict(lambda: {"commodities": set(), "endings": set(), "numbers": []})

    for _, row in df.iterrows():
        stem = row["stem"]
        ending = row["ending"]
        number = row["number"]
        # Commodity assignment is already implied by context (grain/oil/wine/etc.)
        # For now we’ll use file-specific context to track usage
        lexicon[stem]["endings"].add(ending)
        lexicon[stem]["numbers"].append(number)

    # Convert to DataFrame
    rows = []
    for stem, data in lexicon.items():
        endings = "; ".join(sorted(data["endings"]))
        num_examples = len(data["numbers"])
        unique_numbers = len(set(data["numbers"]))
        rows.append({
            "stem": stem,
            "endings": endings,
            "n_obs": num_examples,
            "unique_numbers": unique_numbers
        })

    out_df = pd.DataFrame(rows)
    out_df = out_df.sort_values(by="n_obs", ascending=False)

    out_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Lexicon summary written to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()