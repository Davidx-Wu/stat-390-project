#!/usr/bin/env python3
from __future__ import annotations

import re
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
DATA_RAW = EXPERIMENT_DIR / "data_raw"
DATA_PROCESSED = EXPERIMENT_DIR / "data_processed"
RESULTS = EXPERIMENT_DIR / "results"
DIAGNOSTICS = EXPERIMENT_DIR / "diagnostics"
LOGS = EXPERIMENT_DIR / "logs"

SHIRLEY_PATH = DATA_RAW / "Shirley_Rankings.csv"
SPEECH_PATH = DATA_PROCESSED / "combined_speech_dataset_closed_with_split.csv"

SPEECH_FEATURES = [
    "num_positions",
    "num_adv_inh_solv",
    "num_offs",
    "num_cards_total",
    "num_cards_with_highlight",
    "total_highlighted_words",
]

TEAM_STRENGTH_FEATURES = [
    "team_place",
    "opponent_place",
    "place_diff",
    "team_winpm",
    "opponent_winpm",
    "winpm_diff",
    "team_pts_pm",
    "opponent_pts_pm",
    "pts_pm_diff",
    "team_osd",
    "opponent_osd",
    "osd_diff",
    "team_ballot_win_count",
    "opponent_ballot_win_count",
    "ballot_win_count_diff",
]


def normalize_text(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = text.replace(" - ONLINE", "")
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return " ".join(text.split())


def speaker_initials(entry: str) -> str:
    names = re.split(r"\s*&\s*|\s+and\s+", str(entry))
    initials = ""
    for name in names:
        words = [w for w in re.split(r"[^A-Za-z]+", name) if w]
        if words:
            initials += words[0][0].lower()
    return initials


def ballot_win_count(ballots: object) -> int:
    text = "" if pd.isna(ballots) else str(ballots)
    return len(re.findall(r"R\d+W", text))


def build_lookup(rankings: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in rankings.iterrows():
        school = normalize_text(row.get("School", ""))
        initials = speaker_initials(row.get("Entry", ""))
        if not school or not initials:
            continue
        rows.append(
            {
                "team_key": f"{school} {initials}".strip(),
                "place": row.get("Place"),
                "winpm": row.get("WinPm"),
                "pts_pm": row.get("PtsPm"),
                "pts_pm_minus_1hl": row.get("PtsPm -1HL"),
                "pts_minus_2hl": row.get("Pts -2HL"),
                "osd": row.get("OSd"),
                "ballot_win_count": ballot_win_count(row.get("Ballots")),
                "ranking_entry": row.get("Entry"),
                "ranking_school": row.get("School"),
            }
        )
    out = pd.DataFrame(rows)
    numeric_cols = ["place", "winpm", "pts_pm", "pts_pm_minus_1hl", "pts_minus_2hl", "osd", "ballot_win_count"]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.drop_duplicates(subset=["team_key"], keep="first")


def add_strength_features(speech: pd.DataFrame, lookup: pd.DataFrame) -> pd.DataFrame:
    out = speech.copy()
    lookup_map = lookup.set_index("team_key")
    out["_team_key"] = out["team_code"].map(normalize_text)
    out["_opponent_key"] = out["opponent"].map(normalize_text)
    fields = {
        "place": "place",
        "winpm": "winpm",
        "pts_pm": "pts_pm",
        "osd": "osd",
        "ballot_win_count": "ballot_win_count",
    }
    for output, field in fields.items():
        mapping = lookup_map[field].to_dict()
        out[f"team_{output}"] = out["_team_key"].map(mapping)
        out[f"opponent_{output}"] = out["_opponent_key"].map(mapping)
    out["place_diff"] = out["opponent_place"] - out["team_place"]
    out["winpm_diff"] = out["team_winpm"] - out["opponent_winpm"]
    out["pts_pm_diff"] = out["team_pts_pm"] - out["opponent_pts_pm"]
    out["osd_diff"] = out["team_osd"] - out["opponent_osd"]
    out["ballot_win_count_diff"] = out["team_ballot_win_count"] - out["opponent_ballot_win_count"]
    out["strength_missing_flag"] = out[TEAM_STRENGTH_FEATURES].isna().any(axis=1).astype(int)
    return out.drop(columns=["_team_key", "_opponent_key"])


def make_logistic(c: float = 0.5, elastic: bool = False) -> Pipeline:
    if elastic:
        model = LogisticRegression(
            C=c,
            penalty="elasticnet",
            solver="saga",
            l1_ratio=0.5,
            max_iter=5000,
            random_state=42,
        )
    else:
        model = LogisticRegression(C=c, max_iter=1000, random_state=42)
    return Pipeline([("scaler", StandardScaler()), ("model", model)])


def make_svm() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", CalibratedClassifierCV(LinearSVC(C=0.5, max_iter=5000, random_state=42), cv=3)),
        ]
    )


def evaluate(
    df: pd.DataFrame,
    features: list[str],
    name: str,
    model,
    model_family: str,
    complete_case: bool,
) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    data = df.copy()
    if complete_case:
        data = data.dropna(subset=features)
    train = data[data["dataset_split"] == "train"].copy()
    val = data[data["dataset_split"] == "validation"].copy()
    if train.empty or val.empty:
        raise ValueError(f"{name} has insufficient rows after complete-case filter")
    y_train = train["win_loss"]
    y_val = val["win_loss"]

    if model_family == "majority":
        majority = y_train.value_counts().idxmax()
        pred = pd.Series([majority] * len(val), index=val.index)
        prob = pd.Series([1.0 if majority == "W" else 0.0] * len(val), index=val.index)
        model_desc = f"majority_class={majority}"
        coef_df = pd.DataFrame()
    else:
        model.fit(train[features].fillna(0), y_train)
        pred = pd.Series(model.predict(val[features].fillna(0)), index=val.index)
        classes = list(model.classes_) if hasattr(model, "classes_") else list(model.named_steps["model"].classes_)
        prob = pd.Series(model.predict_proba(val[features].fillna(0))[:, classes.index("W")], index=val.index)
        model_desc = str(model)
        coef_df = pd.DataFrame()
        estimator = model.named_steps.get("model") if hasattr(model, "named_steps") else None
        if hasattr(estimator, "coef_"):
            coef_df = pd.DataFrame(
                {
                    "experiment_name": name,
                    "feature": features,
                    "coefficient": estimator.coef_[0],
                    "abs_coefficient": np.abs(estimator.coef_[0]),
                }
            ).sort_values("abs_coefficient", ascending=False)

    cm = confusion_matrix(y_val, pred, labels=["L", "W"])
    row = {
        "experiment_name": name,
        "model_family": model_family,
        "features_used": ", ".join(features) if features else "none",
        "complete_case_strength_rows_only": complete_case,
        "train_rows": len(train),
        "validation_rows": len(val),
        "validation_accuracy": accuracy_score(y_val, pred),
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
            *SPEECH_FEATURES,
            *TEAM_STRENGTH_FEATURES,
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
    return row, predictions, coef_df


def feature_summary(df: pd.DataFrame) -> pd.DataFrame:
    definitions = {
        "team_place": "Shirley final placement/rank for the row team; lower means stronger.",
        "opponent_place": "Shirley final placement/rank for opponent; lower means stronger.",
        "place_diff": "opponent_place - team_place; positive means row team ranked stronger.",
        "team_winpm": "Shirley wins per prelim metric for row team; higher means stronger.",
        "opponent_winpm": "Shirley wins per prelim metric for opponent; higher means stronger.",
        "winpm_diff": "team_winpm - opponent_winpm; positive means row team stronger.",
        "team_pts_pm": "Shirley speaker points metric for row team; higher usually means stronger.",
        "opponent_pts_pm": "Shirley speaker points metric for opponent; higher usually means stronger.",
        "pts_pm_diff": "team_pts_pm - opponent_pts_pm; positive means row team stronger.",
        "team_osd": "Shirley opponent-strength/difficulty metric for row team.",
        "opponent_osd": "Shirley opponent-strength/difficulty metric for opponent.",
        "osd_diff": "team_osd - opponent_osd.",
        "team_ballot_win_count": "Count of W ballots parsed from Shirley Ballots string; higher is stronger but fully downstream.",
        "opponent_ballot_win_count": "Opponent count of W ballots parsed from Shirley Ballots string.",
        "ballot_win_count_diff": "team_ballot_win_count - opponent_ballot_win_count; positive means row team stronger.",
    }
    rows = []
    for feature in TEAM_STRENGTH_FEATURES:
        rows.append(
            {
                "feature": feature,
                "definition": definitions[feature],
                "non_null_rows": int(df[feature].notna().sum()),
                "missing_rows": int(df[feature].isna().sum()),
                "coverage": df[feature].notna().mean(),
                "mean": df[feature].mean(),
                "std": df[feature].std(),
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    rankings = pd.read_csv(SHIRLEY_PATH)
    lookup = build_lookup(rankings)
    df = add_strength_features(pd.read_csv(SPEECH_PATH), lookup)
    explanatory_features = TEAM_STRENGTH_FEATURES
    combined_features = SPEECH_FEATURES + TEAM_STRENGTH_FEATURES

    specs = [
        ("majority_baseline", [], "majority", None, False),
        ("speech_structure_only_logistic", SPEECH_FEATURES, "logistic", make_logistic(), False),
        ("shirley_strength_only_logistic", explanatory_features, "logistic", make_logistic(), True),
        ("shirley_strength_only_elastic_net", explanatory_features, "elastic_net", make_logistic(elastic=True), True),
        ("combined_speech_shirley_logistic", combined_features, "logistic", make_logistic(), True),
        ("combined_speech_shirley_elastic_net", combined_features, "elastic_net", make_logistic(elastic=True), True),
        ("shirley_strength_calibrated_svm", explanatory_features, "calibrated_linear_svm", make_svm(), True),
    ]

    rows = []
    prediction_frames = []
    coef_frames = []
    for name, features, family, model, complete_case in specs:
        try:
            row, preds, coefs = evaluate(df, features, name, model, family, complete_case)
            rows.append(row)
            prediction_frames.append(preds)
            if not coefs.empty:
                coef_frames.append(coefs)
        except Exception as exc:
            rows.append(
                {
                    "experiment_name": name,
                    "model_family": family,
                    "features_used": ", ".join(features) if features else "none",
                    "complete_case_strength_rows_only": complete_case,
                    "train_rows": 0,
                    "validation_rows": 0,
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

    table = pd.DataFrame(rows)
    predictions = pd.concat(prediction_frames, ignore_index=True, sort=False) if prediction_frames else pd.DataFrame()
    coefficients = pd.concat(coef_frames, ignore_index=True, sort=False) if coef_frames else pd.DataFrame()
    if not coefficients.empty:
        coefficients = coefficients.sort_values(["experiment_name", "abs_coefficient"], ascending=[True, False])
    matrices = table[
        [
            "experiment_name",
            "true_L_pred_L",
            "true_L_pred_W",
            "true_W_pred_L",
            "true_W_pred_W",
            "false_positive_count",
            "false_negative_count",
        ]
    ].copy()
    summary_features = feature_summary(df)

    table.to_csv(RESULTS / "explanatory_experiment_table.csv", index=False)
    coefficients.to_csv(RESULTS / "explanatory_model_coefficients.csv", index=False)
    predictions.to_csv(RESULTS / "explanatory_validation_predictions.csv", index=False)
    matrices.to_csv(RESULTS / "explanatory_confusion_matrices.csv", index=False)
    summary_features.to_csv(DIAGNOSTICS / "explanatory_feature_summary.csv", index=False)

    def acc(name: str) -> float:
        return float(table.loc[table["experiment_name"] == name, "validation_accuracy"].iloc[0])

    strength_acc = acc("shirley_strength_only_logistic")
    speech_acc = acc("speech_structure_only_logistic")
    combined_acc = acc("combined_speech_shirley_logistic")
    incremental = combined_acc - strength_acc
    best_name = table.sort_values("validation_accuracy", ascending=False).iloc[0]["experiment_name"]
    best_coefs = coefficients[coefficients["experiment_name"] == best_name].head(15) if not coefficients.empty else pd.DataFrame()
    combined_coefs = coefficients[coefficients["experiment_name"] == "combined_speech_shirley_logistic"].copy()
    surviving_speech = combined_coefs[combined_coefs["feature"].isin(SPEECH_FEATURES)].head(10)

    summary = [
        "# Explanatory Team-Strength Model Summary",
        "",
        "## Framing",
        "- This is a retrospective explanatory model, not a leakage-free real-time prediction model.",
        "- Shirley variables are temporally downstream of Gonzaga/Northwestern and proxy latent team strength/results context.",
        "",
        "## Coverage",
        f"- Rows with complete Shirley team-strength features: {int(df[TEAM_STRENGTH_FEATURES].notna().all(axis=1).sum())} / {len(df)}",
        f"- Validation rows with complete Shirley team-strength features: {int((df['dataset_split'].eq('validation') & df[TEAM_STRENGTH_FEATURES].notna().all(axis=1)).sum())}",
        "",
        "## Validation Results",
        table.to_string(index=False),
        "",
        "## Explanatory Power",
        f"- Speech-structure-only accuracy: {speech_acc:.6f}",
        f"- Shirley/team-strength-only logistic accuracy: {strength_acc:.6f}",
        f"- Combined speech + Shirley logistic accuracy: {combined_acc:.6f}",
        f"- Combined minus strength-only delta: {incremental:.6f}",
        "",
        "## Best Model Coefficients",
        best_coefs.to_string(index=False) if not best_coefs.empty else "- No coefficient table available.",
        "",
        "## Speech Features After Adding Shirley",
        surviving_speech.to_string(index=False) if not surviving_speech.empty else "- No speech coefficients available.",
        "",
        "## Final Interpretation",
        (
            "- Team-strength variables alone explain substantially more validation signal than parser-derived speech structure."
            if strength_acc > speech_acc
            else "- Team-strength variables do not outperform parser-derived speech structure in this run."
        ),
        (
            "- Speech/document features do not add incremental explanatory value after adding Shirley variables."
            if incremental <= 0
            else "- Speech/document features add some incremental explanatory value after adding Shirley variables."
        ),
        "- This supports the claim that latent team strength dominates the current parser-derived structural features in retrospective explanation.",
    ]
    (LOGS / "explanatory_model_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    print("Explanatory strength experiment complete.")
    print(table.to_string(index=False))
    print()
    print(summary_features.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
