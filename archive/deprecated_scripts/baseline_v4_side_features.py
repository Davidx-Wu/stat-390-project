from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REPO = Path(__file__).resolve().parents[1]
DATA_PATH = REPO / "4 -- results" / "processed_datasets" / "gonzaga_speech_dataset_v1.csv"
OUT_DIR = REPO / "4 -- results" / "baseline_runs"
METRICS_OUT = OUT_DIR / "baseline_v4_side_features_metrics.csv"
COEFFICIENTS_OUT = OUT_DIR / "baseline_v4_side_features_coefficients.csv"

OUTCOME_COL = "win_loss"
SPLIT_COL = "dataset_split"
SIDE_COL = "side"
SIDE_BINARY_COL = "side_binary_neg"
TRAIN_SPLIT = "train"
VALIDATION_SPLIT = "validation"
FEATURES = [
    "num_positions",
    "num_adv_inh_solv",
    "num_offs",
    "num_cards_total",
    "num_cards_with_highlight",
    "total_highlighted_words",
    SIDE_BINARY_COL,
]


def encode_outcome(series):
    return series.map({"L": 0, "W": 1})


def encode_side(series):
    normalized = series.astype(str).str.strip().str.lower()
    encoded = normalized.map({"aff": 0, "neg": 1})
    if encoded.isna().any():
        bad_values = sorted(series[encoded.isna()].dropna().unique())
        raise ValueError(f"Unexpected side values: {bad_values}")
    return encoded


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    df[SIDE_BINARY_COL] = encode_side(df[SIDE_COL])

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
            {"metric": "confusion_matrix_true_L_pred_L", "value": tn},
            {"metric": "confusion_matrix_true_L_pred_W", "value": fp},
            {"metric": "confusion_matrix_true_W_pred_L", "value": fn},
            {"metric": "confusion_matrix_true_W_pred_W", "value": tp},
        ]
    )

    metrics.to_csv(METRICS_OUT, index=False)
    coefficients.to_csv(COEFFICIENTS_OUT, index=False)

    print("Baseline v4: side-aware structured logistic regression")
    print(f"Dataset: {DATA_PATH}")
    print(f"Train rows: {len(train_df)}")
    print(f"Validation rows: {len(validation_df)}")
    print(f"Features: {', '.join(FEATURES)}")
    print("Side encoding: aff=0, neg=1")
    print("Implementation: scikit-learn Pipeline(StandardScaler, LogisticRegression)")
    print(f"Validation accuracy: {validation_accuracy:.4f}")
    print("Confusion matrix, labels L/W:")
    print(pd.DataFrame(matrix, index=["true_L", "true_W"], columns=["pred_L", "pred_W"]).to_string())
    print("\nFeature coefficients:")
    print(coefficients.to_string(index=False))
    print(f"\nSaved metrics: {METRICS_OUT}")
    print(f"Saved coefficients: {COEFFICIENTS_OUT}")


if __name__ == "__main__":
    main()
