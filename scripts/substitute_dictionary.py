import pandas as pd

# Paths
DATA_PATH = "outputs/structured_sequences.csv"
OUTPUT_PATH = "outputs/tablets_substituted.csv"

# Substitution dictionary (based on stabilized lexicon)
SUBSTITUTIONS = {
    "AB81 AB02": "grain",
    "AB54 AB67": "oil",
    "AB51 AB24": "wineA",
    "AB51 AB45": "wineB",
    "AB04 AB69": "prestige?",
    "AB27 AB17": "prestige?",
    # weaker / tentative anchors
    "AB28 AB67": "commodity?",
    "AB54 AB28": "commodity?",
    "AB04 AB40": "link?"
}

def main():
    df = pd.read_csv(DATA_PATH)

    # Apply substitutions
    def substitute(stem):
        return SUBSTITUTIONS.get(stem, stem)

    df["stem_label"] = df["stem"].apply(substitute)
    df["ending_label"] = df["ending"].apply(substitute)

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Substituted tablets written to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()