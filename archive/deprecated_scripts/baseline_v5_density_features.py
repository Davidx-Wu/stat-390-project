from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REPO = Path(__file__).resolve().parents[1]
DATA_PATH = REPO / "4 -- results" / "processed_datasets" / "gonzaga_speech_dataset_v1.csv"
OUT_DIR = REPO / "4 -- results" / "baseline_runs"
METRICS_OUT = OUT_DIR / "baseline_v5_density_metrics.csv"
COEFFICIENTS_OUT = OUT_DIR / "baseline_v5_density_coefficients.csv"
V3_METRICS_PATH = OUT_DIR / "baseline_v3_structured_numeric_metrics.csv"

OUTCOME_COL = "win_loss"
SPLIT_COL = "dataset_split"
TRAIN_SPLIT = "train"
VALIDATION_SPLIT = "validation"
BASE_FEATURES = [
    "num_positions",
    "num_adv_inh_solv",
    "num_offs",
    "num_cards_total",
    "num_cards_with_highlight",
    "total_highlighted_words",
]
DENSITY_FEATURES = [
    "cards_per_position",
    "offs_ratio",
    "highlight_ratio",
    "highlight_words_per_card",
]
FEATURES = BASE_FEATURES + DENSITY_FEATURES


def encode_outcome(series):
    return series.map({"L": 0, "W": 1})


def denominator_at_least_one(series):
    return series.where(series >= 1, 1)


def add_density_features(df):
    df = df.copy()
    positions_denominator = denominator_at_least_one(df["num_positions"])
    cards_denominator = denominator_at_least_one(df["num_cards_total"])

    df["cards_per_position"] = df["num_cards_total"] / positions_denominator
    df["offs_ratio"] = df["num_offs"] / positions_denominator
    df["highlight_ratio"] = df["num_cards_with_highlight"] / cards_denominator
    df["highlight_words_per_card"] = df["total_highlighted_words"] / cards_denominator
    return df


def read_v3_accuracy():
    if not V3_METRICS_PATH.exists():
        return None
    metrics = pd.read_csv(V3_METRICS_PATH)
    row = metrics.loc[metrics["metric"] == "validation_accuracy", "value"]
    if row.empty:
        return None
    return float(row.iloc[0])


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = add_density_features(pd.read_csv(DATA_PATH))

    train_df = df[df[SPLIT_COL] == TRAIN_SPLIT].copy()
    validation_df = df[df[SPLIT_COL] == VALIDATION_SPLIT].copy()

    if train_df.empty:
        raise ValueError("No train rows found.")
    if validation_df.empty:
        raise ValueError("No validation rows found.")

    x_train = train_df[FEATURES].fillna(0)
    y_train = encode_outcome(train_df[OUTCOME_COL])
    x_validation = validation_df[FEATURES].fillna(0)
    y_validation = encode_outcome(validation_df[OUTCOME_COL])

    if y_train.isna().any() or y_validation.isna().any():
        raise ValueError("Outcome column contains values outside expected labels: W, L.")

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("logistic", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
    model.fit(x_train, y_train)

    validation_predictions = model.predict(x_validation)
    validation_accuracy = accuracy_score(y_validation, validation_predictions)

    majority_class = y_train.mode().iloc[0]
    majority_predictions = pd.Series(majority_class, index=y_validation.index)
    majority_validation_accuracy = accuracy_score(y_validation, majority_predictions)

    v3_validation_accuracy = read_v3_accuracy()
    v3_delta = None if v3_validation_accuracy is None else validation_accuracy - v3_validation_accuracy

    matrix = confusion_matrix(y_validation, validation_predictions, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()

    coefficients = pd.DataFrame(
        {
            "feature": FEATURES,
            "coefficient": model.named_steps["logistic"].coef_[0],
        }
    ).sort_values("coefficient", ascending=False)

    metrics = pd.DataFrame(
        [
            {"metric": "train_rows", "value": len(train_df)},
            {"metric": "validation_rows", "value": len(validation_df)},
            {"metric": "validation_accuracy", "value": validation_accuracy},
            {
                "metric": "majority_class_validation_baseline",
                "value": majority_validation_accuracy,
            },
            {"metric": "majority_class_label", "value": "W" if majority_class == 1 else "L"},
            {"metric": "v3_validation_accuracy", "value": v3_validation_accuracy},
            {"metric": "v5_minus_v3_validation_accuracy", "value": v3_delta},
            {"metric": "confusion_matrix_true_L_pred_L", "value": tn},
            {"metric": "confusion_matrix_true_L_pred_W", "value": fp},
            {"metric": "confusion_matrix_true_W_pred_L", "value": fn},
            {"metric": "confusion_matrix_true_W_pred_W", "value": tp},
        ]
    )

    metrics.to_csv(METRICS_OUT, index=False)
    coefficients.to_csv(COEFFICIENTS_OUT, index=False)

    print("Baseline v5: argument density features")
    print(f"Dataset: {DATA_PATH}")
    print(f"Train rows: {len(train_df)}")
    print(f"Validation rows: {len(validation_df)}")
    print(f"Features: {', '.join(FEATURES)}")
    print("Implementation: scikit-learn Pipeline(StandardScaler, LogisticRegression)")
    print(f"Validation accuracy: {validation_accuracy:.4f}")
    print(f"Majority-class validation baseline: {majority_validation_accuracy:.4f}")
    if v3_validation_accuracy is not None:
        print(f"Baseline v3 validation accuracy: {v3_validation_accuracy:.4f}")
        print(f"V5 minus v3 validation accuracy: {v3_delta:.4f}")
    print("Confusion matrix, labels L/W:")
    print(pd.DataFrame(matrix, index=["true_L", "true_W"], columns=["pred_L", "pred_W"]).to_string())
    print("\nFeature coefficients:")
    print(coefficients.to_string(index=False))
    print(f"\nSaved metrics: {METRICS_OUT}")
    print(f"Saved coefficients: {COEFFICIENTS_OUT}")


if __name__ == "__main__":
    main()
