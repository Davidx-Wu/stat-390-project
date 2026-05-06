from pathlib import Path
import sys

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "experiments" / "gonzaga_autoresearch"))

from model import build_model
from prepare import (  # noqa: E402
    ALLOWED_FEATURE_COLUMNS,
    SPLIT_COL,
    TARGET_COL,
    TRAIN_SPLIT,
    VALIDATION_SPLIT,
    encode_target,
    load_ranked_dataframe,
)


OUT_DIR = REPO / "results" / "gonzaga" / "error_analysis"
PREDICTIONS_OUT = OUT_DIR / "validation_predictions.csv"
MISCLASSIFICATIONS_OUT = OUT_DIR / "validation_misclassifications.csv"


DISPLAY_COLUMNS = [
    "source_file",
    "team_code",
    "opponent",
    "round_number",
    "side",
    "actual_outcome",
    "predicted_outcome",
    "predicted_win_probability",
    "prediction_confidence",
    "error_type",
    "team_rank",
    "opponent_rank",
    "rank_diff",
] + ALLOWED_FEATURE_COLUMNS + [
    "parse_confidence",
    "card_count_from_audit",
    "argument_count_from_audit",
    "card_text_truncated",
    "argument_text_truncated",
]


def outcome_label(value):
    return "W" if int(value) == 1 else "L"


def classify_error(row):
    if row["actual_outcome"] == row["predicted_outcome"]:
        return "correct"
    if row["actual_outcome"] == "L" and row["predicted_outcome"] == "W":
        return "false_positive"
    if row["actual_outcome"] == "W" and row["predicted_outcome"] == "L":
        return "false_negative"
    return "error"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_ranked_dataframe().reset_index(names="row_id")
    train_df = df[df[SPLIT_COL] == TRAIN_SPLIT].copy()
    val_df = df[df[SPLIT_COL] == VALIDATION_SPLIT].copy()

    x_train = train_df[ALLOWED_FEATURE_COLUMNS].fillna(0)
    y_train = encode_target(train_df[TARGET_COL])
    x_val = val_df[ALLOWED_FEATURE_COLUMNS].fillna(0)

    model = build_model()
    model.fit(x_train, y_train)
    predicted = model.predict(x_val)
    probabilities = model.predict_proba(x_val)[:, 1]

    output = val_df.copy()
    output["actual_outcome"] = output[TARGET_COL]
    output["predicted_outcome"] = [outcome_label(value) for value in predicted]
    output["predicted_win_probability"] = probabilities
    output["prediction_confidence"] = output["predicted_win_probability"].where(
        output["predicted_outcome"] == "W",
        1 - output["predicted_win_probability"],
    )
    output["distance_from_threshold"] = (output["predicted_win_probability"] - 0.5).abs()
    output["error_type"] = output.apply(classify_error, axis=1)

    for column in DISPLAY_COLUMNS:
        if column not in output.columns:
            output[column] = pd.NA

    predictions = output[["row_id"] + DISPLAY_COLUMNS + ["distance_from_threshold"]].copy()
    misclassified = predictions[predictions["error_type"] != "correct"].copy()
    misclassified = misclassified.sort_values(
        ["prediction_confidence", "round_number"],
        ascending=[False, True],
    )

    predictions.to_csv(PREDICTIONS_OUT, index=False)
    misclassified.to_csv(MISCLASSIFICATIONS_OUT, index=False)

    false_positive_count = int((predictions["error_type"] == "false_positive").sum())
    false_negative_count = int((predictions["error_type"] == "false_negative").sum())
    highest_confidence_mistakes = misclassified.head(5)
    lowest_confidence_predictions = predictions.sort_values("distance_from_threshold").head(5)

    print("Locked validation prediction export")
    print(f"Validation rows: {len(predictions)}")
    print(f"False positives: {false_positive_count}")
    print(f"False negatives: {false_negative_count}")
    print(f"Predictions output: {PREDICTIONS_OUT}")
    print(f"Misclassifications output: {MISCLASSIFICATIONS_OUT}")
    print("\nHighest-confidence mistakes:")
    print(
        highest_confidence_mistakes[
            [
                "team_code",
                "opponent",
                "round_number",
                "side",
                "actual_outcome",
                "predicted_outcome",
                "predicted_win_probability",
                "prediction_confidence",
                "error_type",
                "rank_diff",
                "parse_confidence",
                "num_cards_total",
                "total_highlighted_words",
            ]
        ].to_string(index=False)
    )
    print("\nLowest-confidence predictions:")
    print(
        lowest_confidence_predictions[
            [
                "team_code",
                "opponent",
                "round_number",
                "side",
                "actual_outcome",
                "predicted_outcome",
                "predicted_win_probability",
                "distance_from_threshold",
                "error_type",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
