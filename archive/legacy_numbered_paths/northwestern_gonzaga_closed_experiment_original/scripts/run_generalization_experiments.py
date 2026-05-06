#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC


REPO_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_DIR = REPO_ROOT / "6 -- experiments" / "northwestern_gonzaga_closed_experiment"
DATA_PATH = EXPERIMENT_DIR / "data_processed" / "combined_speech_dataset_closed_with_split.csv"
RESULTS = EXPERIMENT_DIR / "results"
LOGS = EXPERIMENT_DIR / "logs"

BASE_FEATURES = [
    "num_positions",
    "num_adv_inh_solv",
    "num_offs",
    "num_cards_total",
    "num_cards_with_highlight",
    "total_highlighted_words",
]

NORMALIZED_FEATURES = [f"{col}_tournament_z" for col in BASE_FEATURES]
PERCENTILE_FEATURES = [f"{col}_tournament_pct" for col in BASE_FEATURES]
CENTERED_FEATURES = [f"{col}_tournament_centered" for col in BASE_FEATURES]

RELATIVE_FEATURES = [
    "positions_diff",
    "adv_inh_solv_diff",
    "offs_diff",
    "cards_diff",
    "highlight_cards_diff",
    "highlight_words_diff",
    "cards_per_position_diff",
    "opponent_match_found",
]


def normalize_team(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = text.replace(" - ONLINE", "")
    return " ".join(text.lower().split())


def add_tournament_normalized_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in BASE_FEATURES:
        grouped = out.groupby("tournament_source")[col]
        means = grouped.transform("mean")
        stds = grouped.transform("std").replace(0, np.nan)
        out[f"{col}_tournament_z"] = ((out[col] - means) / stds).fillna(0)
        out[f"{col}_tournament_centered"] = (out[col] - means).fillna(0)
        out[f"{col}_tournament_pct"] = grouped.rank(pct=True, method="average").fillna(0.5)
    return out


def add_relative_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["_team_norm"] = out["team_code"].map(normalize_team)
    out["_opponent_norm"] = out["opponent"].map(normalize_team)
    out["_join_key"] = (
        out["tournament_source"].astype(str)
        + "|"
        + out["round_number"].astype(str)
        + "|"
        + out["_team_norm"]
        + "|"
        + out["_opponent_norm"]
    )
    opponent_keys = (
        out["tournament_source"].astype(str)
        + "|"
        + out["round_number"].astype(str)
        + "|"
        + out["_opponent_norm"]
        + "|"
        + out["_team_norm"]
    )
    opponent_lookup = out.assign(_opponent_lookup_key=opponent_keys).drop_duplicates(
        subset=["_opponent_lookup_key"], keep="first"
    ).set_index("_opponent_lookup_key")

    for feature, base_col in [
        ("positions_diff", "num_positions"),
        ("adv_inh_solv_diff", "num_adv_inh_solv"),
        ("offs_diff", "num_offs"),
        ("cards_diff", "num_cards_total"),
        ("highlight_cards_diff", "num_cards_with_highlight"),
        ("highlight_words_diff", "total_highlighted_words"),
    ]:
        opp_values = opponent_lookup.reindex(out["_join_key"])[base_col].to_numpy()
        out[feature] = out[base_col].to_numpy() - np.nan_to_num(opp_values, nan=out[base_col].to_numpy())

    own_cpp = out["num_cards_total"] / out["num_positions"].clip(lower=1)
    opp_positions = opponent_lookup.reindex(out["_join_key"])["num_positions"].to_numpy()
    opp_cards = opponent_lookup.reindex(out["_join_key"])["num_cards_total"].to_numpy()
    opp_cpp = np.nan_to_num(opp_cards / np.clip(opp_positions, 1, None), nan=own_cpp.to_numpy())
    out["cards_per_position_diff"] = own_cpp.to_numpy() - opp_cpp
    out["opponent_match_found"] = opponent_lookup.reindex(out["_join_key"])["source_file"].notna().astype(int).to_numpy()
    return out.drop(columns=["_team_norm", "_opponent_norm", "_join_key"])


def make_logistic(c: float = 0.5) -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(C=c, max_iter=1000, random_state=42)),
        ]
    )


def make_elastic_net() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    C=0.5,
                    penalty="elasticnet",
                    solver="saga",
                    l1_ratio=0.5,
                    max_iter=5000,
                    random_state=42,
                ),
            ),
        ]
    )


def make_calibrated_svm() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", CalibratedClassifierCV(LinearSVC(C=0.5, max_iter=5000, random_state=42), cv=3)),
        ]
    )


def evaluate_model(
    df: pd.DataFrame,
    train_mask: pd.Series,
    val_mask: pd.Series,
    features: list[str],
    model,
    experiment_name: str,
    feature_set: str,
    tournament_setting: str,
) -> tuple[dict, pd.DataFrame]:
    train = df.loc[train_mask].copy()
    val = df.loc[val_mask].copy()
    if train.empty or val.empty:
        raise ValueError(f"empty train/validation set for {experiment_name}")

    model.fit(train[features].fillna(0), train["win_loss"])
    pred = pd.Series(model.predict(val[features].fillna(0)), index=val.index)
    if hasattr(model, "predict_proba"):
        classes = list(model.classes_) if hasattr(model, "classes_") else list(model.named_steps["model"].classes_)
        prob_array = model.predict_proba(val[features].fillna(0))
        p_win = pd.Series(prob_array[:, classes.index("W")] if "W" in classes else 0.0, index=val.index)
    else:
        p_win = pd.Series(np.nan, index=val.index)

    y_val = val["win_loss"]
    cm = confusion_matrix(y_val, pred, labels=["L", "W"])
    false_positive = int(((pred == "W") & (y_val == "L")).sum())
    false_negative = int(((pred == "L") & (y_val == "W")).sum())
    row = {
        "experiment_name": experiment_name,
        "feature_set": feature_set,
        "features_used": ", ".join(features),
        "tournament_setting": tournament_setting,
        "model": str(model),
        "validation_accuracy": accuracy_score(y_val, pred),
        "validation_rows": len(val),
        "true_L_pred_L": int(cm[0, 0]),
        "true_L_pred_W": int(cm[0, 1]),
        "true_W_pred_L": int(cm[1, 0]),
        "true_W_pred_W": int(cm[1, 1]),
        "false_positive_count": false_positive,
        "false_negative_count": false_negative,
    }
    predictions = val[
        [
            "source_file",
            "team_code",
            "opponent",
            "round_number",
            "side",
            "tournament_source",
            "parse_confidence",
            *BASE_FEATURES,
        ]
    ].copy()
    predictions["experiment_name"] = experiment_name
    predictions["actual_outcome"] = y_val
    predictions["predicted_outcome"] = pred
    predictions["predicted_win_probability"] = p_win
    predictions["error_type"] = np.where(
        predictions["actual_outcome"] == predictions["predicted_outcome"],
        "correct",
        np.where(predictions["predicted_outcome"] == "W", "false_positive", "false_negative"),
    )
    return row, predictions


def calibration_rows(predictions: pd.DataFrame, experiment_name: str) -> list[dict]:
    rows = []
    valid = predictions[predictions["predicted_win_probability"].notna()].copy()
    if valid.empty:
        return rows
    for outcome, group in valid.groupby("actual_outcome"):
        rows.append(
            {
                "experiment_name": experiment_name,
                "summary_type": "avg_probability_by_actual",
                "group": outcome,
                "rows": len(group),
                "avg_predicted_win_probability": group["predicted_win_probability"].mean(),
                "actual_win_rate": (group["actual_outcome"] == "W").mean(),
            }
        )
    valid["probability_bin"] = pd.cut(valid["predicted_win_probability"], bins=np.linspace(0, 1, 11), include_lowest=True)
    for bin_label, group in valid.groupby("probability_bin", observed=False):
        rows.append(
            {
                "experiment_name": experiment_name,
                "summary_type": "probability_histogram_bin",
                "group": str(bin_label),
                "rows": len(group),
                "avg_predicted_win_probability": group["predicted_win_probability"].mean() if len(group) else np.nan,
                "actual_win_rate": (group["actual_outcome"] == "W").mean() if len(group) else np.nan,
            }
        )
    return rows


def make_error_cluster_summary(predictions: pd.DataFrame) -> pd.DataFrame:
    df = predictions.copy()
    df["is_error"] = df["error_type"] != "correct"
    df["cards_per_position"] = df["num_cards_total"] / df["num_positions"].clip(lower=1)
    df["offs_density"] = df["num_offs"] / df["num_positions"].clip(lower=1)
    rows = []
    for field in ["tournament_source", "side", "parse_confidence"]:
        for value, group in df.groupby(field, dropna=False):
            rows.append(
                {
                    "cluster_field": field,
                    "cluster_value": value,
                    "rows": len(group),
                    "errors": int(group["is_error"].sum()),
                    "error_rate": group["is_error"].mean(),
                    "false_positives": int((group["error_type"] == "false_positive").sum()),
                    "false_negatives": int((group["error_type"] == "false_negative").sum()),
                    "avg_cards_per_position": group["cards_per_position"].mean(),
                    "avg_offs_density": group["offs_density"].mean(),
                }
            )
    for field in ["cards_per_position", "offs_density"]:
        labels = ["low", "mid", "high"]
        try:
            df[f"{field}_bin"] = pd.qcut(df[field], q=3, labels=labels, duplicates="drop")
        except ValueError:
            df[f"{field}_bin"] = "single_bin"
        for value, group in df.groupby(f"{field}_bin", dropna=False, observed=False):
            rows.append(
                {
                    "cluster_field": f"{field}_bin",
                    "cluster_value": value,
                    "rows": len(group),
                    "errors": int(group["is_error"].sum()),
                    "error_rate": group["is_error"].mean(),
                    "false_positives": int((group["error_type"] == "false_positive").sum()),
                    "false_negatives": int((group["error_type"] == "false_negative").sum()),
                    "avg_cards_per_position": group["cards_per_position"].mean(),
                    "avg_offs_density": group["offs_density"].mean(),
                }
            )
    return pd.DataFrame(rows)


def interpretation(row: dict, baseline_accuracy: float) -> str:
    diff = row["validation_accuracy"] - baseline_accuracy
    if diff >= 0.02:
        return "meaningful improvement over raw baseline on the closed validation split"
    if diff > 0:
        return "small improvement over raw baseline; treat cautiously"
    if diff == 0:
        return "matches raw baseline"
    return "does not improve over raw baseline"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    df = df[df["dataset_split"].isin(["train", "validation", "test"])].copy()
    df = add_tournament_normalized_features(df)
    df = add_relative_features(df)

    train_mask = df["dataset_split"] == "train"
    val_mask = df["dataset_split"] == "validation"
    non_test_mask = df["dataset_split"].isin(["train", "validation"])

    experiment_specs = [
        ("raw_only_logistic", "raw_only", BASE_FEATURES, make_logistic(), "closed train -> closed validation"),
        ("z_normalized_only_logistic", "z_normalized_only", NORMALIZED_FEATURES, make_logistic(), "closed train -> closed validation"),
        ("percentile_only_logistic", "percentile_only", PERCENTILE_FEATURES, make_logistic(), "closed train -> closed validation"),
        ("centered_only_logistic", "centered_only", CENTERED_FEATURES, make_logistic(), "closed train -> closed validation"),
        ("raw_plus_z_logistic", "raw_plus_z", BASE_FEATURES + NORMALIZED_FEATURES, make_logistic(), "closed train -> closed validation"),
        ("raw_plus_percentile_logistic", "raw_plus_percentile", BASE_FEATURES + PERCENTILE_FEATURES, make_logistic(), "closed train -> closed validation"),
        ("relative_only_logistic", "relative_only", RELATIVE_FEATURES, make_logistic(), "closed train -> closed validation"),
        ("raw_plus_relative_logistic", "raw_plus_relative", BASE_FEATURES + RELATIVE_FEATURES, make_logistic(), "closed train -> closed validation"),
        ("raw_plus_z_plus_relative_logistic", "raw_plus_z_plus_relative", BASE_FEATURES + NORMALIZED_FEATURES + RELATIVE_FEATURES, make_logistic(), "closed train -> closed validation"),
        ("raw_elastic_net_logistic", "raw_only", BASE_FEATURES, make_elastic_net(), "closed train -> closed validation"),
        ("raw_calibrated_linear_svm", "raw_only", BASE_FEATURES, make_calibrated_svm(), "closed train -> closed validation"),
    ]

    generalization_rows = []
    normalized_rows = []
    prediction_frames = []
    failure_rows = []
    baseline_accuracy = None

    for name, feature_set, features, model, setting in experiment_specs:
        try:
            row, predictions = evaluate_model(df, train_mask, val_mask, features, model, name, feature_set, setting)
            if name == "raw_only_logistic":
                baseline_accuracy = row["validation_accuracy"]
            generalization_rows.append(row)
            prediction_frames.append(predictions)
            if "normalized" in feature_set or feature_set in {"raw_plus_z", "raw_plus_percentile", "centered_only", "percentile_only"}:
                normalized_rows.append(row.copy())
        except Exception as exc:
            failure_rows.append(
                {
                    "experiment_name": name,
                    "feature_set": feature_set,
                    "features_used": ", ".join(features),
                    "tournament_setting": setting,
                    "model": str(model),
                    "validation_accuracy": np.nan,
                    "validation_rows": 0,
                    "true_L_pred_L": np.nan,
                    "true_L_pred_W": np.nan,
                    "true_W_pred_L": np.nan,
                    "true_W_pred_W": np.nan,
                    "false_positive_count": np.nan,
                    "false_negative_count": np.nan,
                    "interpretation": f"crash: {exc}",
                }
            )

    baseline_accuracy = baseline_accuracy if baseline_accuracy is not None else np.nan
    for row in generalization_rows:
        row["interpretation"] = interpretation(row, baseline_accuracy)

    holdout_specs = [
        ("holdout_train_gonzaga_validate_northwestern", df["tournament_source"].eq("Gonzaga") & non_test_mask, df["tournament_source"].eq("Northwestern") & non_test_mask),
        ("holdout_train_northwestern_validate_gonzaga", df["tournament_source"].eq("Northwestern") & non_test_mask, df["tournament_source"].eq("Gonzaga") & non_test_mask),
    ]
    holdout_rows = []
    for name, holdout_train, holdout_val in holdout_specs:
        for feature_set, features in [
            ("raw_only", BASE_FEATURES),
            ("z_normalized_only", NORMALIZED_FEATURES),
            ("raw_plus_z", BASE_FEATURES + NORMALIZED_FEATURES),
            ("relative_only", RELATIVE_FEATURES),
            ("raw_plus_relative", BASE_FEATURES + RELATIVE_FEATURES),
        ]:
            try:
                row, _predictions = evaluate_model(
                    df,
                    holdout_train,
                    holdout_val,
                    features,
                    make_logistic(),
                    f"{name}_{feature_set}",
                    feature_set,
                    name.replace("_", " "),
                )
                row["interpretation"] = "tournament-holdout robustness check using train+validation rows only"
                holdout_rows.append(row)
            except Exception as exc:
                holdout_rows.append(
                    {
                        "experiment_name": f"{name}_{feature_set}",
                        "feature_set": feature_set,
                        "features_used": ", ".join(features),
                        "tournament_setting": name.replace("_", " "),
                        "model": "LogisticRegression(C=0.5)",
                        "validation_accuracy": np.nan,
                        "validation_rows": 0,
                        "true_L_pred_L": np.nan,
                        "true_L_pred_W": np.nan,
                        "true_W_pred_L": np.nan,
                        "true_W_pred_W": np.nan,
                        "false_positive_count": np.nan,
                        "false_negative_count": np.nan,
                        "interpretation": f"crash: {exc}",
                    }
                )

    all_predictions = pd.concat(prediction_frames, ignore_index=True, sort=False) if prediction_frames else pd.DataFrame()
    raw_predictions = all_predictions[all_predictions["experiment_name"] == "raw_only_logistic"].copy()
    calibration = pd.DataFrame(calibration_rows(raw_predictions, "raw_only_logistic"))
    error_clusters = make_error_cluster_summary(raw_predictions) if not raw_predictions.empty else pd.DataFrame()

    generalization = pd.DataFrame(generalization_rows + failure_rows)
    normalized = pd.DataFrame(normalized_rows)
    holdout = pd.DataFrame(holdout_rows)

    generalization.to_csv(RESULTS / "generalization_experiment_table.csv", index=False)
    holdout.to_csv(RESULTS / "tournament_holdout_results.csv", index=False)
    calibration.to_csv(RESULTS / "calibration_summary.csv", index=False)
    error_clusters.to_csv(RESULTS / "error_cluster_summary.csv", index=False)
    normalized.to_csv(RESULTS / "normalized_feature_ablation.csv", index=False)

    best = generalization.sort_values("validation_accuracy", ascending=False).iloc[0]
    best_holdout = holdout.sort_values("validation_accuracy", ascending=False).iloc[0]
    opponent_match_rate = df["opponent_match_found"].mean()
    summary = [
        "# Generalization Experiment Summary",
        "",
        "## Objective",
        "- Improve cross-tournament robustness under Gonzaga + Northwestern distribution shift using only closed-folder artifacts.",
        "- No closed test-set rows were used for same-split model optimization.",
        "",
        "## Relative Feature Diagnostic",
        f"- Opponent speech match coverage across combined data: {opponent_match_rate:.3f}",
        "- Relative features were evaluated with an opponent-match flag and zero difference fallback for unmatched rows.",
        "",
        "## Best Closed Validation Result",
        f"- Experiment: {best['experiment_name']}",
        f"- Feature set: {best['feature_set']}",
        f"- Validation accuracy: {best['validation_accuracy']:.6f}",
        f"- False positives: {int(best['false_positive_count'])}",
        f"- False negatives: {int(best['false_negative_count'])}",
        f"- Interpretation: {best['interpretation']}",
        "",
        "## Tournament Holdout",
        f"- Best holdout experiment: {best_holdout['experiment_name']}",
        f"- Holdout accuracy: {best_holdout['validation_accuracy']:.6f}",
        "- Holdout rows use train+validation rows only and are not comparable to final test evidence.",
        "",
        "## Calibration/Error Notes",
        "- Calibration and error-cluster summaries were generated for the raw logistic closed validation model.",
        "- Use calibration_summary.csv and error_cluster_summary.csv for probability and cluster-level diagnostics.",
        "",
        "## Recommendation",
        "- Treat any same-split gains as robustness clues, not final evidence.",
        "- The key question is whether normalized or relative features reduce tournament dependence without sacrificing interpretability.",
    ]
    (LOGS / "generalization_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    print("Generalization experiments complete.")
    print(generalization[["experiment_name", "validation_accuracy", "false_positive_count", "false_negative_count", "interpretation"]].to_string(index=False))
    print()
    print("Tournament holdout:")
    print(holdout[["experiment_name", "validation_accuracy", "validation_rows", "false_positive_count", "false_negative_count"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
