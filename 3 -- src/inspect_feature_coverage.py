from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
DATA_PATH = REPO / "4 -- results" / "processed_datasets" / "gonzaga_speech_dataset_v1.csv"
OUT_PATH = REPO / "4 -- results" / "diagnostics" / "feature_coverage_summary.csv"

OUTCOME_COL = "win_loss"
SPLIT_COL = "dataset_split"
META_COLS = {
    "source_file",
    "team_code",
    "tournament_name",
    "round_number",
    "side",
    "opponent",
    "judge",
    "parse_confidence",
    "warnings",
}
LEAKAGE_KEYWORDS = ("winner", "outcome", "result", "win", "loss", "ballot")
RAW_TEXT_KEYWORDS = ("text", "speech", "content", "transcript")
ID_PATH_KEYWORDS = ("file", "path", "doc", "document")


def classify_column(name, dtype):
    lower = name.lower()

    if name == OUTCOME_COL:
        return "outcome/split/meta", "exclude", "outcome target"
    if name == SPLIT_COL:
        return "outcome/split/meta", "exclude", "split label"
    if any(keyword in lower for keyword in LEAKAGE_KEYWORDS):
        return "outcome/split/meta", "exclude", "possible outcome leakage"
    if any(keyword in lower for keyword in ID_PATH_KEYWORDS):
        return "outcome/split/meta", "exclude", "file path or document identifier"
    if any(keyword in lower for keyword in RAW_TEXT_KEYWORDS):
        return "text/object feature candidates", "exclude", "raw text not vectorized"
    if pd.api.types.is_numeric_dtype(dtype):
        if name in META_COLS:
            return "numeric feature candidates", "review", "numeric metadata candidate"
        return "numeric feature candidates", "usable", "structured numeric feature"
    if name in META_COLS:
        return "outcome/split/meta", "review", "metadata; encode only if justified"
    return "text/object feature candidates", "review", "object/categorical candidate"


def print_group(title, columns):
    print(f"\n{title}")
    if columns:
        for column in columns:
            print(f"- {column}")
    else:
        print("- none")


def main():
    df = pd.read_csv(DATA_PATH)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for column in df.columns:
        group, recommendation, reason = classify_column(column, df[column].dtype)
        rows.append(
            {
                "column": column,
                "dtype": str(df[column].dtype),
                "non_null_count": int(df[column].notna().sum()),
                "missing_count": int(df[column].isna().sum()),
                "unique_count": int(df[column].nunique(dropna=True)),
                "group": group,
                "recommendation": recommendation,
                "reason": reason,
            }
        )

    summary = pd.DataFrame(rows)
    summary.to_csv(OUT_PATH, index=False)

    outcome_meta = summary[summary["group"] == "outcome/split/meta"]["column"].tolist()
    numeric_candidates = summary[summary["group"] == "numeric feature candidates"]["column"].tolist()
    text_candidates = summary[summary["group"] == "text/object feature candidates"]["column"].tolist()
    usable_features = summary[summary["recommendation"] == "usable"]["column"].tolist()
    review_features = summary[summary["recommendation"] == "review"]["column"].tolist()
    excluded_columns = summary[summary["recommendation"] == "exclude"]["column"].tolist()

    print("Feature coverage inspection")
    print(f"Dataset: {DATA_PATH}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print_group("Outcome/split/meta columns", outcome_meta)
    print_group("Numeric feature candidates", numeric_candidates)
    print_group("Text/object feature candidates", text_candidates)
    print_group("Likely usable model features", usable_features)
    print_group("Review before modeling", review_features)
    print_group("Excluded to avoid leakage or unsupported inputs", excluded_columns)
    print(f"\nSaved feature coverage summary: {OUT_PATH}")


if __name__ == "__main__":
    main()
