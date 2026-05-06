#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REPO_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_DIR = REPO_ROOT / "6 -- experiments" / "northwestern_gonzaga_closed_experiment"
INPUT_PATH = EXPERIMENT_DIR / "data_processed" / "combined_speech_dataset_closed_with_split.csv"
DATA_PROCESSED = EXPERIMENT_DIR / "data_processed"
RESULTS = EXPERIMENT_DIR / "results"
DIAGNOSTICS = EXPERIMENT_DIR / "diagnostics"
LOGS = EXPERIMENT_DIR / "logs"

BASE_FEATURES = [
    "num_positions",
    "num_adv_inh_solv",
    "num_offs",
    "num_cards_total",
    "num_cards_with_highlight",
    "total_highlighted_words",
]

CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}


def normalize_team(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = text.replace(" - ONLINE", "")
    return " ".join(text.lower().split())


def add_pair_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["_team_norm"] = out["team_code"].map(normalize_team)
    out["_opponent_norm"] = out["opponent"].map(normalize_team)
    out["_team_a"] = np.minimum(out["_team_norm"], out["_opponent_norm"])
    out["_team_b"] = np.maximum(out["_team_norm"], out["_opponent_norm"])
    out["_match_key"] = (
        out["tournament_source"].astype(str)
        + "|"
        + out["round_number"].astype(str)
        + "|"
        + out["_team_a"]
        + "|"
        + out["_team_b"]
    )
    out["_parse_rank"] = out["parse_confidence"].map(CONFIDENCE_RANK).fillna(0)
    out["_source_sort"] = out["source_file"].astype(str)
    return out


def choose_best_side(group: pd.DataFrame) -> pd.Series:
    sorted_group = group.sort_values(
        by=["_parse_rank", "num_cards_total", "total_highlighted_words", "_source_sort"],
        ascending=[False, False, False, True],
    )
    return sorted_group.iloc[0]


def zero_flag(row: pd.Series) -> int:
    return int(sum(float(row.get(col, 0) or 0) for col in BASE_FEATURES) == 0)


def build_paired_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    keyed = add_pair_keys(df[df["win_loss"].isin(["W", "L"])].copy())
    duplicate_rows = []
    pair_rows = []
    dropped_missing_side = 0
    dropped_inconsistent_outcome = 0

    for match_key, group in keyed.groupby("_match_key"):
        aff_group = group[group["side"].astype(str).str.lower() == "aff"]
        neg_group = group[group["side"].astype(str).str.lower() == "neg"]
        if len(aff_group) > 1:
            duplicate_rows.append(
                {
                    "match_key": match_key,
                    "side": "aff",
                    "duplicate_count": len(aff_group),
                    "chosen_source_file": choose_best_side(aff_group)["source_file"],
                }
            )
        if len(neg_group) > 1:
            duplicate_rows.append(
                {
                    "match_key": match_key,
                    "side": "neg",
                    "duplicate_count": len(neg_group),
                    "chosen_source_file": choose_best_side(neg_group)["source_file"],
                }
            )
        if aff_group.empty or neg_group.empty:
            dropped_missing_side += 1
            continue

        aff = choose_best_side(aff_group)
        neg = choose_best_side(neg_group)
        if aff["win_loss"] == "W" and neg["win_loss"] == "L":
            aff_win_label = 1
        elif aff["win_loss"] == "L" and neg["win_loss"] == "W":
            aff_win_label = 0
        else:
            dropped_inconsistent_outcome += 1
            continue

        row = {
            "match_key": match_key,
            "tournament_source": aff["tournament_source"],
            "round_number": aff["round_number"],
            "aff_team": aff["team_code"],
            "neg_team": neg["team_code"],
            "aff_source_file": aff["source_file"],
            "neg_source_file": neg["source_file"],
            "aff_win_label": aff_win_label,
            "aff_original_split": aff.get("dataset_split", ""),
            "neg_original_split": neg.get("dataset_split", ""),
            "aff_parse_confidence": aff.get("parse_confidence", ""),
            "neg_parse_confidence": neg.get("parse_confidence", ""),
            "aff_parse_high": int(aff.get("parse_confidence") == "high"),
            "aff_parse_medium": int(aff.get("parse_confidence") == "medium"),
            "neg_parse_high": int(neg.get("parse_confidence") == "high"),
            "neg_parse_medium": int(neg.get("parse_confidence") == "medium"),
            "aff_zero_feature_flag": zero_flag(aff),
            "neg_zero_feature_flag": zero_flag(neg),
            "tournament_northwestern": int(aff["tournament_source"] == "Northwestern"),
        }
        for col in BASE_FEATURES:
            row[f"aff_{col}"] = aff[col]
            row[f"neg_{col}"] = neg[col]
            row[f"diff_{col}"] = aff[col] - neg[col]
        row["diff_cards_per_position"] = (
            aff["num_cards_total"] / max(float(aff["num_positions"]), 1.0)
        ) - (
            neg["num_cards_total"] / max(float(neg["num_positions"]), 1.0)
        )
        pair_rows.append(row)

    summary = {
        "speech_rows_input": len(df),
        "candidate_match_groups": keyed["_match_key"].nunique(),
        "paired_rounds_created": len(pair_rows),
        "dropped_missing_side_groups": dropped_missing_side,
        "dropped_inconsistent_outcome_groups": dropped_inconsistent_outcome,
        "duplicate_side_groups": len(duplicate_rows),
    }
    return pd.DataFrame(pair_rows), pd.DataFrame(duplicate_rows), summary


def assign_pair_split(pairs: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    out = pairs.copy()
    inherited_ok = (
        (out["aff_original_split"].notna())
        & (out["neg_original_split"].notna())
        & (out["aff_original_split"] == out["neg_original_split"])
    )
    if bool(inherited_ok.all()) and set(out["aff_original_split"]).issubset({"train", "validation", "test"}):
        out["dataset_split"] = out["aff_original_split"]
        return out, "inherited_from_speech_rows"

    train, temp = train_test_split(
        out,
        train_size=0.70,
        random_state=42,
        stratify=out["aff_win_label"],
    )
    validation, test = train_test_split(
        temp,
        train_size=0.50,
        random_state=42,
        stratify=temp["aff_win_label"],
    )
    train = train.copy()
    validation = validation.copy()
    test = test.copy()
    train["dataset_split"] = "train"
    validation["dataset_split"] = "validation"
    test["dataset_split"] = "test"
    return pd.concat([train, validation, test], ignore_index=True), "new_pair_level_split_random_state_42"


def make_model() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(C=0.5, max_iter=1000, random_state=42)),
        ]
    )


def evaluate(
    df: pd.DataFrame,
    features: list[str],
    experiment_name: str,
    model_kind: str = "logistic",
) -> tuple[dict, pd.DataFrame]:
    train = df[df["dataset_split"] == "train"].copy()
    validation = df[df["dataset_split"] == "validation"].copy()
    y_train = train["aff_win_label"]
    y_val = validation["aff_win_label"]

    if model_kind == "majority":
        majority = int(y_train.value_counts().idxmax())
        pred = pd.Series([majority] * len(validation), index=validation.index)
        p_aff = pd.Series([float(majority)] * len(validation), index=validation.index)
        model_desc = f"majority_class={majority}"
    else:
        model = make_model()
        model.fit(train[features].fillna(0), y_train)
        pred = pd.Series(model.predict(validation[features].fillna(0)), index=validation.index)
        classes = list(model.named_steps["model"].classes_)
        p_aff = pd.Series(
            model.predict_proba(validation[features].fillna(0))[:, classes.index(1)],
            index=validation.index,
        )
        model_desc = str(model)

    cm = confusion_matrix(y_val, pred, labels=[0, 1])
    row = {
        "experiment_name": experiment_name,
        "features_used": ", ".join(features) if features else "none",
        "model": model_desc,
        "validation_accuracy": accuracy_score(y_val, pred),
        "validation_rows": len(validation),
        "true_negwin_pred_negwin": int(cm[0, 0]),
        "true_negwin_pred_affwin": int(cm[0, 1]),
        "true_affwin_pred_negwin": int(cm[1, 0]),
        "true_affwin_pred_affwin": int(cm[1, 1]),
        "false_positive_count": int(((pred == 1) & (y_val == 0)).sum()),
        "false_negative_count": int(((pred == 0) & (y_val == 1)).sum()),
    }
    predictions = validation[
        [
            "match_key",
            "tournament_source",
            "round_number",
            "aff_team",
            "neg_team",
            "aff_source_file",
            "neg_source_file",
            "aff_parse_confidence",
            "neg_parse_confidence",
            "aff_zero_feature_flag",
            "neg_zero_feature_flag",
            *[f"aff_{col}" for col in BASE_FEATURES],
            *[f"neg_{col}" for col in BASE_FEATURES],
            *[f"diff_{col}" for col in BASE_FEATURES],
        ]
    ].copy()
    predictions["experiment_name"] = experiment_name
    predictions["actual_aff_win_label"] = y_val
    predictions["predicted_aff_win_label"] = pred
    predictions["predicted_aff_win_probability"] = p_aff
    predictions["error_type"] = np.where(
        predictions["actual_aff_win_label"] == predictions["predicted_aff_win_label"],
        "correct",
        np.where(predictions["predicted_aff_win_label"] == 1, "false_positive_aff_win", "false_negative_aff_win"),
    )
    return row, predictions


def error_cluster_summary(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    predictions = predictions.copy()
    predictions["is_error"] = predictions["error_type"] != "correct"
    predictions["both_high_parse"] = (
        (predictions["aff_parse_confidence"] == "high")
        & (predictions["neg_parse_confidence"] == "high")
    )
    for field in ["tournament_source", "aff_parse_confidence", "neg_parse_confidence", "both_high_parse"]:
        for value, group in predictions.groupby(field, dropna=False):
            rows.append(
                {
                    "cluster_field": field,
                    "cluster_value": value,
                    "rows": len(group),
                    "errors": int(group["is_error"].sum()),
                    "error_rate": group["is_error"].mean(),
                    "false_positive_aff_win": int((group["error_type"] == "false_positive_aff_win").sum()),
                    "false_negative_aff_win": int((group["error_type"] == "false_negative_aff_win").sum()),
                }
            )
    return pd.DataFrame(rows)


def main() -> int:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    speech_df = pd.read_csv(INPUT_PATH)
    pairs, duplicates, summary = build_paired_dataset(speech_df)
    pairs.to_csv(DATA_PROCESSED / "paired_round_dataset_closed.csv", index=False)
    duplicates.to_csv(DIAGNOSTICS / "paired_duplicate_handling.csv", index=False)
    pairs_with_split, split_source = assign_pair_split(pairs)
    pairs_with_split.to_csv(DATA_PROCESSED / "paired_round_dataset_closed_with_split.csv", index=False)

    aff_features = [f"aff_{col}" for col in BASE_FEATURES]
    neg_features = [f"neg_{col}" for col in BASE_FEATURES]
    diff_features = [f"diff_{col}" for col in BASE_FEATURES] + ["diff_cards_per_position"]
    flags = [
        "aff_parse_high",
        "aff_parse_medium",
        "neg_parse_high",
        "neg_parse_medium",
        "aff_zero_feature_flag",
        "neg_zero_feature_flag",
        "tournament_northwestern",
    ]
    manual_interactions = [
        "diff_offs_x_diff_cards_total",
        "diff_cards_total_x_diff_highlighted_words",
        "aff_adv_x_neg_offs",
        "neg_offs_x_aff_cards_total",
    ]
    pairs_with_split["diff_offs_x_diff_cards_total"] = pairs_with_split["diff_num_offs"] * pairs_with_split["diff_num_cards_total"]
    pairs_with_split["diff_cards_total_x_diff_highlighted_words"] = pairs_with_split["diff_num_cards_total"] * pairs_with_split["diff_total_highlighted_words"]
    pairs_with_split["aff_adv_x_neg_offs"] = pairs_with_split["aff_num_adv_inh_solv"] * pairs_with_split["neg_num_offs"]
    pairs_with_split["neg_offs_x_aff_cards_total"] = pairs_with_split["neg_num_offs"] * pairs_with_split["aff_num_cards_total"]
    pairs_with_split.to_csv(DATA_PROCESSED / "paired_round_dataset_closed_with_split.csv", index=False)

    experiments = [
        ("majority_baseline", [], "majority"),
        ("raw_paired_logistic", aff_features + neg_features + flags, "logistic"),
        ("diff_only_logistic", diff_features + flags, "logistic"),
        ("aff_neg_diff_logistic", aff_features + neg_features + diff_features + flags, "logistic"),
        ("manual_interaction_paired_logistic", aff_features + neg_features + diff_features + flags + manual_interactions, "logistic"),
    ]

    rows = []
    prediction_frames = []
    for name, features, kind in experiments:
        row, predictions = evaluate(pairs_with_split, features, name, kind)
        rows.append(row)
        prediction_frames.append(predictions)

    experiment_table = pd.DataFrame(rows)
    all_predictions = pd.concat(prediction_frames, ignore_index=True, sort=False)
    best_name = experiment_table.sort_values("validation_accuracy", ascending=False).iloc[0]["experiment_name"]
    best_predictions = all_predictions[all_predictions["experiment_name"] == best_name].copy()
    misclassifications = best_predictions[best_predictions["error_type"] != "correct"].copy()

    experiment_table.to_csv(RESULTS / "paired_round_experiment_table.csv", index=False)
    all_predictions.to_csv(RESULTS / "paired_validation_predictions.csv", index=False)
    misclassifications.to_csv(RESULTS / "paired_validation_misclassifications.csv", index=False)
    clusters = error_cluster_summary(best_predictions)

    split_counts = pairs_with_split["dataset_split"].value_counts().to_dict()
    tournament_counts = pairs_with_split["tournament_source"].value_counts().to_dict()
    label_counts = pairs_with_split["aff_win_label"].value_counts().to_dict()
    diagnostic_rows = [
        {"metric": "speech_rows_input", "value": summary["speech_rows_input"]},
        {"metric": "candidate_match_groups", "value": summary["candidate_match_groups"]},
        {"metric": "paired_rounds_created", "value": summary["paired_rounds_created"]},
        {"metric": "dropped_missing_side_groups", "value": summary["dropped_missing_side_groups"]},
        {"metric": "dropped_inconsistent_outcome_groups", "value": summary["dropped_inconsistent_outcome_groups"]},
        {"metric": "duplicate_side_groups", "value": summary["duplicate_side_groups"]},
        {"metric": "split_source", "value": split_source},
        {"metric": "split_counts", "value": split_counts},
        {"metric": "tournament_counts", "value": tournament_counts},
        {"metric": "aff_win_label_counts", "value": label_counts},
    ]
    pd.DataFrame(diagnostic_rows).to_csv(DIAGNOSTICS / "paired_dataset_summary.csv", index=False)

    best = experiment_table.sort_values("validation_accuracy", ascending=False).iloc[0]
    speech_level_best = 0.5308641975308642
    comparison = (
        "Pair-level modeling improves over the closed speech-level structured logistic baseline."
        if best["validation_accuracy"] > speech_level_best
        else "Pair-level modeling does not improve over the closed speech-level structured logistic baseline."
    )
    summary_text = [
        "# Paired Round Closed Experiment Summary",
        "",
        "## Unit of Analysis",
        "- One row is one paired Aff-vs-Neg matchup when both sides could be identified.",
        "- Target is aff_win_label, where 1 means Aff won and 0 means Neg won.",
        "",
        "## Dataset",
        f"- Paired rounds created: {summary['paired_rounds_created']}",
        f"- Dropped groups because only one side was available: {summary['dropped_missing_side_groups']}",
        f"- Dropped groups because outcomes were inconsistent: {summary['dropped_inconsistent_outcome_groups']}",
        f"- Duplicate side groups handled deterministically: {summary['duplicate_side_groups']}",
        f"- Split source: {split_source}",
        f"- Split sizes: {split_counts}",
        f"- Tournament counts: {tournament_counts}",
        f"- Aff win label counts: {label_counts}",
        "",
        "## Validation Results",
        *[
            f"- {row.experiment_name}: accuracy={row.validation_accuracy:.6f}, FP={row.false_positive_count}, FN={row.false_negative_count}"
            for row in experiment_table.itertuples()
        ],
        "",
        "## Best Model",
        f"- Best experiment: {best['experiment_name']}",
        f"- Best validation accuracy: {best['validation_accuracy']:.6f}",
        f"- {comparison}",
        "",
        "## Error Clustering",
        "- Error clusters for the best paired model are included below.",
        clusters.to_string(index=False),
        "",
        "## Interpretation",
        "- This is a theory-driven unit-of-analysis correction, not an open-ended search.",
        "- If paired performance improves, it supports the idea that debate outcome prediction is comparative rather than speech-intrinsic.",
        "- If paired performance does not improve, it supports the broader project story that parser noise and limited structured features remain the bottleneck.",
    ]
    (LOGS / "paired_round_experiment_summary.md").write_text("\n".join(summary_text) + "\n", encoding="utf-8")

    print("Paired round experiment complete.")
    print(pd.DataFrame(diagnostic_rows).to_string(index=False))
    print()
    print(experiment_table.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
