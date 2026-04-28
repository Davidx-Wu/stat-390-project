from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
V1_PATH = REPO / "4 -- results" / "processed_datasets" / "gonzaga_speech_dataset_v1.csv"
CARD_AUDIT_PATH = REPO / "gonzaga_dataset_output" / "card_audit_all.csv"
ARGUMENT_AUDIT_PATH = REPO / "gonzaga_dataset_output" / "argument_audit_all.csv"
OUT_PATH = REPO / "4 -- results" / "processed_datasets" / "gonzaga_speech_dataset_v2_with_text.csv"

JOIN_KEY = "source_file"
STABLE_KEY_CANDIDATES = ["source_file", "team_code", "round_number", "side"]
MAX_COMBINED_TEXT_CHARS = 50000


def safe_text_join(values):
    parts = [str(value).strip() for value in values if pd.notna(value) and str(value).strip()]
    combined = "\n\n---\n\n".join(parts)
    original_length = len(combined)
    truncated = original_length > MAX_COMBINED_TEXT_CHARS
    if truncated:
        combined = combined[:MAX_COMBINED_TEXT_CHARS]
    return combined, original_length, truncated


def aggregate_text(df, text_col, count_col, output_text_col, prefix):
    if text_col not in df.columns:
        return pd.DataFrame(columns=[JOIN_KEY, output_text_col, count_col])

    rows = []
    for source_file, group in df.groupby(JOIN_KEY, dropna=False):
        combined, original_length, truncated = safe_text_join(group[text_col])
        rows.append(
            {
                JOIN_KEY: source_file,
                output_text_col: combined,
                count_col: int(len(group)),
                f"{prefix}_text_char_count": original_length,
                f"{prefix}_text_truncated": bool(truncated),
            }
        )
    return pd.DataFrame(rows)


def main():
    v1 = pd.read_csv(V1_PATH)
    card_audit = pd.read_csv(CARD_AUDIT_PATH)
    argument_audit = pd.read_csv(ARGUMENT_AUDIT_PATH)

    card_text = aggregate_text(
        card_audit,
        text_col="card_text",
        count_col="card_count_from_audit",
        output_text_col="card_text_combined",
        prefix="card",
    )
    argument_text = aggregate_text(
        argument_audit,
        text_col="position_text_excerpt",
        count_col="argument_count_from_audit",
        output_text_col="argument_text_combined",
        prefix="argument",
    )

    v2 = v1.merge(card_text, on=JOIN_KEY, how="left")
    v2 = v2.merge(argument_text, on=JOIN_KEY, how="left")

    count_cols = ["card_count_from_audit", "argument_count_from_audit"]
    truncate_cols = ["card_text_truncated", "argument_text_truncated"]
    char_count_cols = ["card_text_char_count", "argument_text_char_count"]
    text_cols = ["card_text_combined", "argument_text_combined"]

    for col in count_cols + char_count_cols:
        if col in v2.columns:
            v2[col] = v2[col].fillna(0).astype(int)
    for col in truncate_cols:
        if col in v2.columns:
            v2[col] = v2[col].fillna(False).astype(bool)
    for col in text_cols:
        if col in v2.columns:
            v2[col] = v2[col].fillna("")

    rows_matched_card = int(v2["card_count_from_audit"].gt(0).sum())
    rows_matched_argument = int(v2["argument_count_from_audit"].gt(0).sum())
    rows_missing_text = int(
        (v2["card_count_from_audit"].eq(0) & v2["argument_count_from_audit"].eq(0)).sum()
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    v2.to_csv(OUT_PATH, index=False)

    print("Text-enriched Gonzaga dataset v2 build")
    print(f"Join key used: {JOIN_KEY}")
    print(f"Stable key candidates inspected: {', '.join(STABLE_KEY_CANDIDATES)}")
    print(f"v1 rows: {len(v1)}")
    print(f"rows matched to card audit text: {rows_matched_card}")
    print(f"rows matched to argument audit text: {rows_matched_argument}")
    print(f"rows missing text: {rows_missing_text}")
    print(f"card text truncations: {int(v2['card_text_truncated'].sum())}")
    print(f"argument text truncations: {int(v2['argument_text_truncated'].sum())}")
    print(f"output path: {OUT_PATH}")


if __name__ == "__main__":
    main()
