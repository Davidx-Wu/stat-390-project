#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REPO_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_DIR = REPO_ROOT / "6 -- experiments" / "northwestern_gonzaga_closed_experiment"
DATA_RAW = EXPERIMENT_DIR / "data_raw"
DATA_PROCESSED = EXPERIMENT_DIR / "data_processed"
RESULTS = EXPERIMENT_DIR / "results"
DIAGNOSTICS = EXPERIMENT_DIR / "diagnostics"
LOGS = EXPERIMENT_DIR / "logs"

SHIRLEY_PATH = DATA_RAW / "Shirley_Rankings.csv"
SPEECH_PATH = DATA_PROCESSED / "combined_speech_dataset_closed_with_split.csv"
PAIRED_PATH = DATA_PROCESSED / "paired_round_dataset_closed_with_split.csv"

BASE_FEATURES = [
    "num_positions",
    "num_adv_inh_solv",
    "num_offs",
    "num_cards_total",
    "num_cards_with_highlight",
    "total_highlighted_words",
]


def normalize_text(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = text.replace(" - ONLINE", "")
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return " ".join(text.split())


def speaker_initials(entry: str) -> str:
    names = re.split(r"\s*&\s*|\s+and\s+", entry)
    initials = ""
    for name in names:
        words = [w for w in re.split(r"[^A-Za-z]+", name) if w]
        if words:
            initials += words[0][0].upper()
    return initials


def build_ranking_lookup(rankings: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in rankings.iterrows():
        school = normalize_text(row.get("School", ""))
        entry = str(row.get("Entry", ""))
        initials = speaker_initials(entry)
        if not school or not initials:
            continue
        rows.append(
            {
                "rank_key": f"{school} {initials.lower()}".strip(),
                "team_rank": float(row["Place"]),
                "ranking_entry": entry,
                "ranking_school": row.get("School", ""),
            }
        )
    lookup = pd.DataFrame(rows)
    return lookup.drop_duplicates(subset=["rank_key"], keep="first")


def add_speech_ranks(speech: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
    out = speech.copy()
    out["_team_key"] = out["team_code"].map(normalize_text)
    out["_opponent_key"] = out["opponent"].map(normalize_text)
    rank_map = lookup.set_index("rank_key")["team_rank"].to_dict()
    out["team_rank"] = out["_team_key"].map(rank_map)
    out["opponent_rank"] = out["_opponent_key"].map(rank_map)
    out["rank_diff"] = out["opponent_rank"] - out["team_rank"]
    out["rank_missing_flag"] = out["rank_diff"].isna().astype(int)
    out["rank_diff_filled"] = out["rank_diff"].fillna(0)
    return out.drop(columns=["_team_key", "_opponent_key"])


def add_paired_ranks(pairs: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
    out = pairs.copy()
    rank_map = lookup.set_index("rank_key")["team_rank"].to_dict()
    out["_aff_key"] = out["aff_team"].map(normalize_text)
    out["_neg_key"] = out["neg_team"].map(normalize_text)
    out["aff_rank"] = out["_aff_key"].map(rank_map)
    out["neg_rank"] = out["_neg_key"].map(rank_map)
    out["rank_diff"] = out["neg_rank"] - out["aff_rank"]
    out["rank_missing_flag"] = out["rank_diff"].isna().astype(int)
    out["rank_diff_filled"] = out["rank_diff"].fillna(0)
    return out.drop(columns=["_aff_key", "_neg_key"])


def make_model() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(C=0.5, max_iter=1000, random_state=42)),
        ]
    )


def evaluate_speech(
    df: pd.DataFrame,
    features: list[str],
    name: str,
    kind: str = "logistic",
    require_rank: bool = False,
) -> tuple[dict, pd.DataFrame]:
    data = df.copy()
    if require_rank:
        data = data[data["rank_diff"].notna()].copy()
    train = data[data["dataset_split"] == "train"].copy()
    val = data[data["dataset_split"] == "validation"].copy()
    if train.empty or val.empty:
        raise ValueError(f"{name} has insufficient rank coverage: train={len(train)}, validation={len(val)}")
    y_train = train["win_loss"]
    y_val = val["win_loss"]
    if kind == "majority":
        majority = y_train.value_counts().idxmax()
        pred = pd.Series([majority] * len(val), index=val.index)
        prob = pd.Series([1.0 if majority == "W" else 0.0] * len(val), index=val.index)
        model_desc = f"majority_class={majority}"
    else:
        model = make_model()
        model.fit(train[features].fillna(0), y_train)
        pred = pd.Series(model.predict(val[features].fillna(0)), index=val.index)
        classes = list(model.named_steps["model"].classes_)
        prob = pd.Series(model.predict_proba(val[features].fillna(0))[:, classes.index("W")], index=val.index)
        model_desc = str(model)
    cm = confusion_matrix(y_val, pred, labels=["L", "W"])
    row = {
        "experiment_name": name,
        "unit": "speech",
        "features_used": ", ".join(features) if features else "none",
        "model": model_desc,
        "coverage_train_rows": len(train),
        "coverage_validation_rows": len(val),
        "validation_accuracy": accuracy_score(y_val, pred) if len(val) else np.nan,
        "true_L_pred_L": int(cm[0, 0]),
        "true_L_pred_W": int(cm[0, 1]),
        "true_W_pred_L": int(cm[1, 0]),
        "true_W_pred_W": int(cm[1, 1]),
        "false_positive_count": int(((pred == "W") & (y_val == "L")).sum()),
        "false_negative_count": int(((pred == "L") & (y_val == "W")).sum()),
    }
    predictions = val[
        [
            "source_file",
            "team_code",
            "opponent",
            "round_number",
            "side",
            "tournament_source",
            "win_loss",
            "team_rank",
            "opponent_rank",
            "rank_diff",
            *BASE_FEATURES,
        ]
    ].copy()
    predictions["experiment_name"] = name
    predictions["actual_outcome"] = y_val
    predictions["predicted_outcome"] = pred
    predictions["predicted_win_probability"] = prob
    predictions["error_type"] = np.where(
        predictions["actual_outcome"] == predictions["predicted_outcome"],
        "correct",
        np.where(predictions["predicted_outcome"] == "W", "false_positive", "false_negative"),
    )
    return row, predictions


def paired_feature_columns() -> list[str]:
    cols = []
    for prefix in ["aff", "neg", "diff"]:
        for col in BASE_FEATURES:
            cols.append(f"{prefix}_{col}")
    return cols + [
        "diff_cards_per_position",
        "aff_parse_high",
        "aff_parse_medium",
        "neg_parse_high",
        "neg_parse_medium",
        "aff_zero_feature_flag",
        "neg_zero_feature_flag",
        "tournament_northwestern",
    ]


def evaluate_paired(
    df: pd.DataFrame,
    features: list[str],
    name: str,
    require_rank: bool = True,
) -> tuple[dict, pd.DataFrame]:
    data = df.copy()
    if require_rank:
        data = data[data["rank_diff"].notna()].copy()
    train = data[data["dataset_split"] == "train"].copy()
    val = data[data["dataset_split"] == "validation"].copy()
    if train.empty or val.empty:
        raise ValueError(f"{name} has insufficient rank coverage: train={len(train)}, validation={len(val)}")
    y_train = train["aff_win_label"]
    y_val = val["aff_win_label"]
    model = make_model()
    model.fit(train[features].fillna(0), y_train)
    pred = pd.Series(model.predict(val[features].fillna(0)), index=val.index)
    classes = list(model.named_steps["model"].classes_)
    prob = pd.Series(model.predict_proba(val[features].fillna(0))[:, classes.index(1)], index=val.index)
    cm = confusion_matrix(y_val, pred, labels=[0, 1])
    row = {
        "experiment_name": name,
        "unit": "paired_round",
        "features_used": ", ".join(features),
        "model": str(model),
        "coverage_train_rows": len(train),
        "coverage_validation_rows": len(val),
        "validation_accuracy": accuracy_score(y_val, pred) if len(val) else np.nan,
        "true_negwin_pred_negwin": int(cm[0, 0]),
        "true_negwin_pred_affwin": int(cm[0, 1]),
        "true_affwin_pred_negwin": int(cm[1, 0]),
        "true_affwin_pred_affwin": int(cm[1, 1]),
        "false_positive_count": int(((pred == 1) & (y_val == 0)).sum()),
        "false_negative_count": int(((pred == 0) & (y_val == 1)).sum()),
    }
    predictions = val[
        [
            "match_key",
            "tournament_source",
            "round_number",
            "aff_team",
            "neg_team",
            "aff_win_label",
            "aff_rank",
            "neg_rank",
            "rank_diff",
            *paired_feature_columns(),
        ]
    ].copy()
    predictions["experiment_name"] = name
    predictions["actual_aff_win_label"] = y_val
    predictions["predicted_aff_win_label"] = pred
    predictions["predicted_aff_win_probability"] = prob
    predictions["error_type"] = np.where(
        predictions["actual_aff_win_label"] == predictions["predicted_aff_win_label"],
        "correct",
        np.where(predictions["predicted_aff_win_label"] == 1, "false_positive_aff_win", "false_negative_aff_win"),
    )
    return row, predictions


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    rankings = pd.read_csv(SHIRLEY_PATH)
    leakage_indicators = [col for col in ["WinPm", "PtsPm -1HL", "PtsPm", "Pts -2HL", "OSd", "Ballots"] if col in rankings.columns]
    leakage_risk = "high_post_tournament_result_file" if leakage_indicators else "uncertain"
    lookup = build_ranking_lookup(rankings)

    speech = add_speech_ranks(pd.read_csv(SPEECH_PATH), lookup)
    pairs = add_paired_ranks(pd.read_csv(PAIRED_PATH), lookup)

    rank_features = ["rank_diff_filled", "rank_missing_flag"]
    speech_structure_features = BASE_FEATURES
    pair_rank_features = ["rank_diff_filled", "rank_missing_flag"]
    pair_structure_features = paired_feature_columns()

    rows = []
    prediction_frames = []
    for name, features, kind, require_rank in [
        ("majority_baseline", [], "majority", False),
        ("shirley_rank_only", rank_features, "logistic", True),
        ("speech_structure_only", speech_structure_features, "logistic", False),
        ("shirley_rank_plus_speech_structure", rank_features + speech_structure_features, "logistic", True),
    ]:
        try:
            row, predictions = evaluate_speech(speech, features, name, kind, require_rank=require_rank)
            rows.append(row)
            prediction_frames.append(predictions)
        except Exception as exc:
            rows.append(
                {
                    "experiment_name": name,
                    "unit": "speech",
                    "features_used": ", ".join(features) if features else "none",
                    "model": "crash",
                    "coverage_train_rows": 0,
                    "coverage_validation_rows": 0,
                    "validation_accuracy": np.nan,
                    "true_L_pred_L": np.nan,
                    "true_L_pred_W": np.nan,
                    "true_W_pred_L": np.nan,
                    "true_W_pred_W": np.nan,
                    "false_positive_count": np.nan,
                    "false_negative_count": np.nan,
                    "notes": f"crash: {exc}",
                }
            )

    for name, features in [
        ("paired_rank_diff_only", pair_rank_features),
        ("paired_rank_diff_plus_paired_speech_features", pair_rank_features + pair_structure_features),
    ]:
        try:
            row, predictions = evaluate_paired(pairs, features, name, require_rank=True)
            rows.append(row)
            prediction_frames.append(predictions)
        except Exception as exc:
            rows.append(
                {
                    "experiment_name": name,
                    "unit": "paired_round",
                    "features_used": ", ".join(features),
                    "model": "crash",
                    "coverage_train_rows": 0,
                    "coverage_validation_rows": 0,
                    "validation_accuracy": np.nan,
                    "true_negwin_pred_negwin": np.nan,
                    "true_negwin_pred_affwin": np.nan,
                    "true_affwin_pred_negwin": np.nan,
                    "true_affwin_pred_affwin": np.nan,
                    "false_positive_count": np.nan,
                    "false_negative_count": np.nan,
                    "notes": f"crash: {exc}",
                }
            )

    experiment_table = pd.DataFrame(rows)
    predictions = pd.concat(prediction_frames, ignore_index=True, sort=False) if prediction_frames else pd.DataFrame()
    experiment_table.to_csv(RESULTS / "ranking_prior_experiment_table.csv", index=False)
    predictions.to_csv(RESULTS / "ranking_prior_validation_predictions.csv", index=False)

    coverage_rows = [
        {
            "unit": "ranking_file",
            "rows": len(rankings),
            "lookup_rows": len(lookup),
            "leakage_risk": leakage_risk,
            "leakage_indicators": ", ".join(leakage_indicators),
        },
        {
            "unit": "speech_all",
            "rows": len(speech),
            "team_rank_non_null": int(speech["team_rank"].notna().sum()),
            "opponent_rank_non_null": int(speech["opponent_rank"].notna().sum()),
            "rank_diff_non_null": int(speech["rank_diff"].notna().sum()),
            "validation_rank_diff_non_null": int((speech["dataset_split"].eq("validation") & speech["rank_diff"].notna()).sum()),
        },
        {
            "unit": "paired_all",
            "rows": len(pairs),
            "aff_rank_non_null": int(pairs["aff_rank"].notna().sum()),
            "neg_rank_non_null": int(pairs["neg_rank"].notna().sum()),
            "rank_diff_non_null": int(pairs["rank_diff"].notna().sum()),
            "validation_rank_diff_non_null": int((pairs["dataset_split"].eq("validation") & pairs["rank_diff"].notna()).sum()),
        },
    ]
    pd.DataFrame(coverage_rows).to_csv(DIAGNOSTICS / "ranking_coverage_summary.csv", index=False)

    def acc(name: str) -> float:
        values = experiment_table.loc[experiment_table["experiment_name"] == name, "validation_accuracy"]
        return float(values.iloc[0]) if len(values) else np.nan

    speech_increment = acc("shirley_rank_plus_speech_structure") - acc("shirley_rank_only")
    paired_increment = acc("paired_rank_diff_plus_paired_speech_features") - acc("paired_rank_diff_only")
    summary = [
        "# Ranking Prior Closed Experiment Summary",
        "",
        "## Ranking File Audit",
        f"- Shirley file path: {SHIRLEY_PATH}",
        f"- Columns: {list(rankings.columns)}",
        f"- Leakage risk: {leakage_risk}",
        f"- Leakage indicators: {leakage_indicators}",
        "- Because the file contains post-tournament records, speaker points, and ballot strings, rankings are diagnostic only, not a safe final feature.",
        "",
        "## Coverage",
        pd.DataFrame(coverage_rows).to_string(index=False),
        "",
        "## Validation Results",
        experiment_table.to_string(index=False),
        "",
        "## Incremental Signal Question",
        f"- Speech structure over rank-only delta: {speech_increment:.6f}",
        f"- Paired speech structure over paired rank-only delta: {paired_increment:.6f}",
        "- Positive deltas would suggest document structure adds signal beyond team strength; negative deltas suggest rank priors dominate or coverage/noise overwhelms structure.",
        "",
        "## Conclusion",
        (
            "- Debate-document structure adds incremental validation signal beyond Shirley rank-only in the speech-level diagnostic."
            if speech_increment > 0
            else "- Debate-document structure does not add incremental validation signal beyond Shirley rank-only in the speech-level diagnostic."
        ),
        (
            "- Paired speech features add incremental validation signal beyond paired rank_diff."
            if paired_increment > 0
            else "- Paired speech features do not add incremental validation signal beyond paired rank_diff."
        ),
        "- Because Shirley appears post-tournament, this experiment should not replace non-leaky document-only findings.",
    ]
    (LOGS / "ranking_prior_experiment_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    print("Ranking prior experiment complete.")
    print(experiment_table.to_string(index=False))
    print()
    print(pd.DataFrame(coverage_rows).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
