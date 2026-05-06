from pathlib import Path
import re

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


REPO = Path(__file__).resolve().parents[1]
DATA_PATH = REPO / "4 -- results" / "processed_datasets" / "gonzaga_speech_dataset_v2_with_text.csv"
CARD_AUDIT_PATH = REPO / "gonzaga_dataset_output" / "card_audit_all.csv"
OUT_DIR = REPO / "4 -- results" / "semantic_features"
SUMMARY_OUT = OUT_DIR / "semantic_feature_summary.csv"
ABLATION_OUT = OUT_DIR / "semantic_feature_ablation.csv"

TARGET_COL = "win_loss"
SPLIT_COL = "dataset_split"
TRAIN_SPLIT = "train"
VALIDATION_SPLIT = "validation"
JOIN_KEY = "source_file"

BASE_FEATURES = [
    "num_positions",
    "num_adv_inh_solv",
    "num_offs",
    "num_cards_total",
    "num_cards_with_highlight",
    "total_highlighted_words",
]
SEMANTIC_FEATURES = [
    "causal_word_count",
    "certainty_word_count",
    "impact_word_count",
    "numeric_reference_count",
    "highlighted_word_ratio",
]

CAUSAL_PATTERNS = [
    r"\bcauses?\b",
    r"\bleads?\s+to\b",
    r"\bresults?\s+in\b",
    r"\btriggers?\b",
    r"\bproduces?\b",
    r"\bbecause\b",
    r"\btherefore\b",
]
CERTAINTY_WORDS = [
    "will",
    "must",
    "inevitable",
    "guarantees",
    "guarantee",
    "certain",
    "definitely",
]
IMPACT_WORDS = [
    "extinction",
    "nuclear",
    "collapse",
    "recession",
    "war",
    "death",
    "deaths",
    "catastrophe",
    "catastrophic",
]


def encode_target(series):
    return series.map({"L": 0, "W": 1})


def count_patterns(text, patterns):
    text = str(text).lower()
    return sum(len(re.findall(pattern, text)) for pattern in patterns)


def count_words(text, words):
    text = str(text).lower()
    return sum(len(re.findall(rf"\b{re.escape(word)}\b", text)) for word in words)


def count_numeric_references(text):
    text = str(text)
    number_count = len(re.findall(r"\b\d+(?:\.\d+)?\b", text))
    percent_count = len(re.findall(r"\b\d+(?:\.\d+)?\s?%", text))
    year_count = len(re.findall(r"\b(?:19|20)\d{2}\b", text))
    return number_count + percent_count + year_count


def combine_text(values):
    return " ".join(str(value) for value in values if pd.notna(value) and str(value).strip())


def build_semantic_features():
    card_audit = pd.read_csv(CARD_AUDIT_PATH)
    grouped = (
        card_audit.groupby(JOIN_KEY, dropna=False)
        .agg(
            highlighted_text_combined=("highlighted_text", combine_text),
            audit_highlighted_word_count=("highlighted_word_count", "sum"),
            audit_card_word_count=("card_word_count", "sum"),
        )
        .reset_index()
    )
    grouped["causal_word_count"] = grouped["highlighted_text_combined"].map(
        lambda text: count_patterns(text, CAUSAL_PATTERNS)
    )
    grouped["certainty_word_count"] = grouped["highlighted_text_combined"].map(
        lambda text: count_words(text, CERTAINTY_WORDS)
    )
    grouped["impact_word_count"] = grouped["highlighted_text_combined"].map(
        lambda text: count_words(text, IMPACT_WORDS)
    )
    grouped["numeric_reference_count"] = grouped["highlighted_text_combined"].map(count_numeric_references)
    denominator = grouped["audit_card_word_count"].where(grouped["audit_card_word_count"] > 0, 1)
    grouped["highlighted_word_ratio"] = grouped["audit_highlighted_word_count"] / denominator
    return grouped[
        [
            JOIN_KEY,
            "audit_highlighted_word_count",
            "audit_card_word_count",
            "causal_word_count",
            "certainty_word_count",
            "impact_word_count",
            "numeric_reference_count",
            "highlighted_word_ratio",
        ]
    ]


def locked_model():
    return Pipeline(
        [
            ("interactions", PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)),
            ("scaler", StandardScaler()),
            ("logistic", LogisticRegression(C=0.5, max_iter=1000, random_state=42)),
        ]
    )


def evaluate_model(df, features, label):
    train_df = df[df[SPLIT_COL] == TRAIN_SPLIT].copy()
    val_df = df[df[SPLIT_COL] == VALIDATION_SPLIT].copy()
    x_train = train_df[features].fillna(0)
    y_train = encode_target(train_df[TARGET_COL])
    x_val = val_df[features].fillna(0)
    y_val = encode_target(val_df[TARGET_COL])

    model = locked_model()
    model.fit(x_train, y_train)
    predictions = model.predict(x_val)
    accuracy = float(accuracy_score(y_val, predictions))
    majority_class = y_val.mode().iloc[0]
    majority_accuracy = float(accuracy_score(y_val, pd.Series(majority_class, index=y_val.index)))
    matrix = confusion_matrix(y_val, predictions, labels=[0, 1])
    tn, fp, fn, tp = [int(value) for value in matrix.ravel()]
    return {
        "model": label,
        "features": ", ".join(features),
        "train_rows": len(train_df),
        "validation_rows": len(val_df),
        "validation_accuracy": accuracy,
        "majority_baseline": majority_accuracy,
        "true_L_pred_L": tn,
        "true_L_pred_W": fp,
        "true_W_pred_L": fn,
        "true_W_pred_W": tp,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    semantic = build_semantic_features()
    merged = df.merge(semantic, on=JOIN_KEY, how="left")
    for column in SEMANTIC_FEATURES + ["audit_highlighted_word_count", "audit_card_word_count"]:
        merged[column] = merged[column].fillna(0)

    summary = merged[
        [
            JOIN_KEY,
            SPLIT_COL,
            "audit_highlighted_word_count",
            "audit_card_word_count",
        ]
        + SEMANTIC_FEATURES
    ].copy()
    summary["has_highlight_text"] = summary["audit_highlighted_word_count"] > 0
    summary.to_csv(SUMMARY_OUT, index=False)

    baseline = evaluate_model(merged, BASE_FEATURES, "locked_interaction_logistic")
    semantic_result = evaluate_model(
        merged,
        BASE_FEATURES + SEMANTIC_FEATURES,
        "locked_interaction_logistic_plus_highlight_semantic",
    )
    ablation = pd.DataFrame([baseline, semantic_result])
    ablation["difference_vs_locked"] = ablation["validation_accuracy"] - baseline["validation_accuracy"]
    ablation.to_csv(ABLATION_OUT, index=False)

    train_val = merged[merged[SPLIT_COL].isin([TRAIN_SPLIT, VALIDATION_SPLIT])]
    print("Highlighted semantic feature ablation")
    print(f"Input dataset: {DATA_PATH}")
    print(f"Card audit input: {CARD_AUDIT_PATH}")
    print(f"Train/validation rows: {len(train_val)}")
    print(f"Rows with highlighted audit text: {int((train_val['audit_highlighted_word_count'] > 0).sum())}")
    print(f"Semantic features: {', '.join(SEMANTIC_FEATURES)}")
    print(f"Locked model accuracy: {baseline['validation_accuracy']:.6f}")
    print(f"Semantic model accuracy: {semantic_result['validation_accuracy']:.6f}")
    print(f"Difference: {semantic_result['validation_accuracy'] - baseline['validation_accuracy']:.6f}")
    print(f"Summary output: {SUMMARY_OUT}")
    print(f"Ablation output: {ABLATION_OUT}")


if __name__ == "__main__":
    main()
