from pathlib import Path
import math
import re
import time

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.svm import LinearSVC


REPO = Path(__file__).resolve().parents[1]
V2_PATH = REPO / "4 -- results" / "processed_datasets" / "gonzaga_speech_dataset_v2_with_text.csv"
CARD_AUDIT_PATH = REPO / "gonzaga_dataset_output" / "card_audit_all.csv"
ARGUMENT_AUDIT_PATH = REPO / "gonzaga_dataset_output" / "argument_audit_all.csv"
ERROR_ANALYSIS_PATH = REPO / "4 -- results" / "error_analysis" / "validation_predictions.csv"
OUT_DIR = REPO / "4 -- results" / "feature_search"
FEATURE_INVENTORY_OUT = OUT_DIR / "feature_inventory.csv"
EXPERIMENT_TABLE_OUT = OUT_DIR / "experiment_table.csv"
BEST_PREDICTIONS_OUT = OUT_DIR / "best_model_validation_predictions.csv"
SUMMARY_OUT = OUT_DIR / "feature_search_summary.md"

TARGET_COL = "win_loss"
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
PARSER_FEATURES = [
    "parse_confidence_high",
    "parse_confidence_medium",
    "all_zero_feature_flag",
    "missing_card_audit_flag",
    "missing_argument_audit_flag",
    "card_text_truncated_flag",
    "argument_text_truncated_flag",
    "card_count_from_audit",
    "argument_count_from_audit",
]
MANUAL_INTERACTIONS = [
    "num_offs_x_num_cards_total",
    "num_offs_x_total_highlighted_words",
    "num_cards_total_x_num_cards_with_highlight",
    "num_positions_x_num_cards_total",
    "num_adv_inh_solv_x_num_cards_total",
]
SIDE_FEATURES = [
    "side_neg",
    "num_offs_neg",
    "num_adv_inh_solv_aff",
    "num_cards_total_neg",
    "num_cards_total_aff",
    "total_highlighted_words_neg",
    "total_highlighted_words_aff",
]
HIGHLIGHT_FEATURES = [
    "audit_highlighted_word_count",
    "avg_highlighted_words_per_card",
    "share_cards_with_highlights",
    "causal_word_count",
    "certainty_word_count",
    "impact_word_count",
    "numeric_reference_count",
    "legal_keyword_count",
    "policy_keyword_count",
    "economics_keyword_count",
    "security_keyword_count",
]
DIRECT_CLASH_FEATURES = [
    "highlight_token_overlap_count",
    "highlight_token_jaccard",
    "tfidf_cosine_with_opponent",
    "tag_token_overlap_count",
    "rare_own_terms_in_opponent_count",
    "direct_clash_score_proxy",
]
TEXT_LIGHT_FEATURES = [
    "card_text_char_count",
    "argument_text_char_count",
    "card_text_word_count",
    "argument_text_word_count",
    "avg_card_length_from_audit",
    "year_reference_count",
    "text_numeric_reference_count",
    "quoted_span_count",
    "capitalized_entity_proxy_count",
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
CERTAINTY_WORDS = ["will", "must", "inevitable", "guarantees", "guarantee", "certain", "definitely"]
IMPACT_WORDS = ["extinction", "nuclear", "collapse", "recession", "war", "death", "deaths", "catastrophe", "catastrophic"]
LEGAL_WORDS = ["court", "law", "legal", "rights", "constitutional", "statute", "regulation"]
POLICY_WORDS = ["policy", "federal", "government", "agency", "public", "reform", "program"]
ECON_WORDS = ["economy", "economic", "recession", "inflation", "market", "growth", "spending"]
SECURITY_WORDS = ["war", "nuclear", "military", "security", "conflict", "deterrence", "terrorism"]
STOPWORDS = {
    "the", "and", "that", "with", "this", "from", "are", "for", "have", "not", "but",
    "you", "their", "will", "would", "can", "all", "our", "has", "they", "was", "were",
}


def normalize_team(value):
    return str(value).replace(" - ONLINE", "").strip().lower()


def encode_target(series):
    return series.map({"L": 0, "W": 1})


def count_words(text, words):
    text = str(text).lower()
    return sum(len(re.findall(rf"\b{re.escape(word)}\b", text)) for word in words)


def count_patterns(text, patterns):
    text = str(text).lower()
    return sum(len(re.findall(pattern, text)) for pattern in patterns)


def count_numeric(text):
    text = str(text)
    return len(re.findall(r"\b\d+(?:\.\d+)?\b", text)) + len(re.findall(r"\b\d+(?:\.\d+)?\s?%", text))


def count_years(text):
    return len(re.findall(r"\b(?:19|20)\d{2}\b", str(text)))


def tokenize(text):
    tokens = re.findall(r"[a-zA-Z][a-zA-Z]{2,}", str(text).lower())
    return [token for token in tokens if token not in STOPWORDS]


def combine(values):
    return " ".join(str(value) for value in values if pd.notna(value) and str(value).strip())


def locked_model():
    return Pipeline(
        [
            ("interactions", PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(C=0.5, max_iter=1000, random_state=42)),
        ]
    )


def plain_logistic(c=0.5):
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(C=c, max_iter=1000, random_state=42)),
        ]
    )


def build_audit_features():
    card = pd.read_csv(CARD_AUDIT_PATH)
    card_grouped = (
        card.groupby("source_file", dropna=False)
        .agg(
            highlighted_text_combined=("highlighted_text", combine),
            tagline_text_combined=("tagline_text", combine),
            audit_highlighted_word_count=("highlighted_word_count", "sum"),
            audit_card_word_count=("card_word_count", "sum"),
            audit_card_count=("card_order", "count"),
            audit_cards_with_highlight=("highlighted_word_count", lambda x: int((x.fillna(0) > 0).sum())),
        )
        .reset_index()
    )
    denominator_cards = card_grouped["audit_card_count"].where(card_grouped["audit_card_count"] > 0, 1)
    denominator_words = card_grouped["audit_card_word_count"].where(card_grouped["audit_card_word_count"] > 0, 1)
    card_grouped["avg_highlighted_words_per_card"] = card_grouped["audit_highlighted_word_count"] / denominator_cards
    card_grouped["share_cards_with_highlights"] = card_grouped["audit_cards_with_highlight"] / denominator_cards
    card_grouped["avg_card_length_from_audit"] = card_grouped["audit_card_word_count"] / denominator_cards
    card_grouped["highlighted_word_ratio_from_audit"] = card_grouped["audit_highlighted_word_count"] / denominator_words

    for column, words in [
        ("certainty_word_count", CERTAINTY_WORDS),
        ("impact_word_count", IMPACT_WORDS),
        ("legal_keyword_count", LEGAL_WORDS),
        ("policy_keyword_count", POLICY_WORDS),
        ("economics_keyword_count", ECON_WORDS),
        ("security_keyword_count", SECURITY_WORDS),
    ]:
        card_grouped[column] = card_grouped["highlighted_text_combined"].map(lambda text, w=words: count_words(text, w))
    card_grouped["causal_word_count"] = card_grouped["highlighted_text_combined"].map(lambda text: count_patterns(text, CAUSAL_PATTERNS))
    card_grouped["numeric_reference_count"] = card_grouped["highlighted_text_combined"].map(count_numeric)
    return card_grouped


def add_direct_clash_features(df):
    output = df.copy()
    output["team_norm"] = output["team_code"].map(normalize_team)
    output["opponent_norm"] = output["opponent"].map(normalize_team)
    text_by_team_round = {
        (row.round_number, row.team_norm): str(row.highlighted_text_combined)
        for row in output.itertuples()
    }
    tag_by_team_round = {
        (row.round_number, row.team_norm): str(row.tagline_text_combined)
        for row in output.itertuples()
    }
    opponent_texts = []
    opponent_tags = []
    for row in output.itertuples():
        opponent_texts.append(text_by_team_round.get((row.round_number, row.opponent_norm), ""))
        opponent_tags.append(tag_by_team_round.get((row.round_number, row.opponent_norm), ""))
    output["opponent_highlighted_text"] = opponent_texts
    output["opponent_tagline_text"] = opponent_tags

    all_texts = output["highlighted_text_combined"].fillna("").astype(str).tolist() + output["opponent_highlighted_text"].fillna("").astype(str).tolist()
    vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
    try:
        vectorizer.fit(all_texts)
        own_matrix = vectorizer.transform(output["highlighted_text_combined"].fillna("").astype(str))
        opp_matrix = vectorizer.transform(output["opponent_highlighted_text"].fillna("").astype(str))
        cosine = own_matrix.multiply(opp_matrix).sum(axis=1).A1
    except ValueError:
        cosine = [0.0] * len(output)
    output["tfidf_cosine_with_opponent"] = cosine

    overlaps = []
    jaccards = []
    tag_overlaps = []
    rare_counts = []
    for row in output.itertuples():
        own_tokens = set(tokenize(row.highlighted_text_combined))
        opp_tokens = set(tokenize(row.opponent_highlighted_text))
        own_tags = set(tokenize(row.tagline_text_combined))
        opp_tags = set(tokenize(row.opponent_tagline_text))
        overlap = len(own_tokens & opp_tokens)
        union = len(own_tokens | opp_tokens)
        tag_overlap = len(own_tags & opp_tags)
        rare_terms = {token for token in own_tokens if len(token) >= 8}
        rare_counts.append(len(rare_terms & opp_tokens))
        overlaps.append(overlap)
        jaccards.append(overlap / union if union else 0)
        tag_overlaps.append(tag_overlap)
    output["highlight_token_overlap_count"] = overlaps
    output["highlight_token_jaccard"] = jaccards
    output["tag_token_overlap_count"] = tag_overlaps
    output["rare_own_terms_in_opponent_count"] = rare_counts
    output["direct_clash_score_proxy"] = (
        output["highlight_token_jaccard"]
        + output["tfidf_cosine_with_opponent"]
        + output["tag_token_overlap_count"].clip(upper=10) / 10
    )
    return output


def build_feature_frame():
    df = pd.read_csv(V2_PATH)
    audit = build_audit_features()
    df = df.merge(audit, on="source_file", how="left")
    fill_zero = [
        "audit_highlighted_word_count", "audit_card_word_count", "audit_card_count",
        "audit_cards_with_highlight", "avg_highlighted_words_per_card",
        "share_cards_with_highlights", "avg_card_length_from_audit",
        "highlighted_word_ratio_from_audit", "causal_word_count", "certainty_word_count",
        "impact_word_count", "numeric_reference_count", "legal_keyword_count",
        "policy_keyword_count", "economics_keyword_count", "security_keyword_count",
    ]
    for column in fill_zero:
        df[column] = df[column].fillna(0)
    for column in ["highlighted_text_combined", "tagline_text_combined"]:
        df[column] = df[column].fillna("")

    base_sum = df[BASE_FEATURES].fillna(0).sum(axis=1)
    df["parse_confidence_high"] = (df["parse_confidence"].astype(str).str.lower() == "high").astype(int)
    df["parse_confidence_medium"] = (df["parse_confidence"].astype(str).str.lower() == "medium").astype(int)
    df["all_zero_feature_flag"] = (base_sum == 0).astype(int)
    df["missing_card_audit_flag"] = (df["card_count_from_audit"].fillna(0) == 0).astype(int)
    df["missing_argument_audit_flag"] = (df["argument_count_from_audit"].fillna(0) == 0).astype(int)
    df["card_text_truncated_flag"] = df["card_text_truncated"].fillna(False).astype(bool).astype(int)
    df["argument_text_truncated_flag"] = df["argument_text_truncated"].fillna(False).astype(bool).astype(int)

    df["num_offs_x_num_cards_total"] = df["num_offs"] * df["num_cards_total"]
    df["num_offs_x_total_highlighted_words"] = df["num_offs"] * df["total_highlighted_words"]
    df["num_cards_total_x_num_cards_with_highlight"] = df["num_cards_total"] * df["num_cards_with_highlight"]
    df["num_positions_x_num_cards_total"] = df["num_positions"] * df["num_cards_total"]
    df["num_adv_inh_solv_x_num_cards_total"] = df["num_adv_inh_solv"] * df["num_cards_total"]

    side = df["side"].astype(str).str.lower()
    df["side_neg"] = (side == "neg").astype(int)
    df["num_offs_neg"] = df["num_offs"] * df["side_neg"]
    df["num_adv_inh_solv_aff"] = df["num_adv_inh_solv"] * (1 - df["side_neg"])
    df["num_cards_total_neg"] = df["num_cards_total"] * df["side_neg"]
    df["num_cards_total_aff"] = df["num_cards_total"] * (1 - df["side_neg"])
    df["total_highlighted_words_neg"] = df["total_highlighted_words"] * df["side_neg"]
    df["total_highlighted_words_aff"] = df["total_highlighted_words"] * (1 - df["side_neg"])

    df["card_text_word_count"] = df["card_text_combined"].fillna("").astype(str).map(lambda text: len(text.split()))
    df["argument_text_word_count"] = df["argument_text_combined"].fillna("").astype(str).map(lambda text: len(text.split()))
    combined_text = df["card_text_combined"].fillna("").astype(str) + " " + df["argument_text_combined"].fillna("").astype(str)
    df["year_reference_count"] = combined_text.map(count_years)
    df["text_numeric_reference_count"] = combined_text.map(count_numeric)
    df["quoted_span_count"] = combined_text.map(lambda text: len(re.findall(r"[\"“”]", str(text))) // 2)
    df["capitalized_entity_proxy_count"] = combined_text.map(lambda text: len(re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", str(text))))

    df = add_direct_clash_features(df)
    return df


def evaluate_experiment(df, name, features, model, notes):
    train = df[df["dataset_split"] == "train"].copy()
    val = df[df["dataset_split"] == "validation"].copy()
    x_train = train[features].fillna(0)
    y_train = encode_target(train["win_loss"])
    x_val = val[features].fillna(0)
    y_val = encode_target(val["win_loss"])
    start = time.time()
    model.fit(x_train, y_train)
    pred = model.predict(x_val)
    elapsed = time.time() - start
    accuracy = float(accuracy_score(y_val, pred))
    majority = float(accuracy_score(y_val, pd.Series(y_val.mode().iloc[0], index=y_val.index)))
    matrix = confusion_matrix(y_val, pred, labels=[0, 1])
    tn, fp, fn, tp = [int(value) for value in matrix.ravel()]
    return {
        "experiment_name": name,
        "features_used": ", ".join(features),
        "model": str(model),
        "validation_accuracy": accuracy,
        "majority_baseline": majority,
        "difference_vs_locked_baseline": None,
        "true_L_pred_L": tn,
        "true_L_pred_W": fp,
        "true_W_pred_L": fn,
        "true_W_pred_W": tp,
        "status": "pending",
        "runtime_seconds": elapsed,
        "notes": notes,
        "_model_object": model,
        "_features": features,
    }


def make_inventory(df):
    rows = []
    groups = [
        (BASE_FEATURES, "processed v2", "low", "keep"),
        (PARSER_FEATURES, "processed v2", "low/moderate", "test"),
        (MANUAL_INTERACTIONS, "derived from processed v2", "low", "test"),
        (SIDE_FEATURES, "derived from processed v2", "low", "test"),
        (HIGHLIGHT_FEATURES, "card_audit_all.csv highlighted_text", "low", "test"),
        (DIRECT_CLASH_FEATURES, "card_audit_all.csv highlighted text matched by opponent/round", "low/moderate", "test"),
        (TEXT_LIGHT_FEATURES, "processed v2 and card audit", "low", "test"),
    ]
    for features, source, risk, rec in groups:
        for feature in features:
            coverage = int(df[feature].notna().sum()) if feature in df.columns else 0
            nonzero = int((df[feature].fillna(0) != 0).sum()) if feature in df.columns else 0
            rows.append({
                "feature_name": feature,
                "source_file": source,
                "coverage_non_null_rows": coverage,
                "nonzero_rows": nonzero,
                "leakage_risk": risk,
                "keep_discard_recommendation": rec,
            })
    for feature, source, reason in [
        ("win_loss", "processed datasets", "target/outcome leakage"),
        ("dataset_split", "processed datasets", "split label, not a model feature"),
        ("judge", "processed datasets", "judge assignment may encode decision context and is disallowed"),
        ("tournament_name", "processed datasets", "single tournament/meta, not argument feature"),
        ("opponent", "processed datasets", "team identity/context disallowed by scope"),
        ("team_code", "processed datasets", "team identity/context disallowed by scope"),
        ("Ballots", "ranking CSVs", "post-round/tournament result leakage"),
        ("WinPm", "ranking CSVs", "post-tournament performance leakage"),
        ("PtsPm", "ranking CSVs", "speaker points/post-result leakage"),
        ("Place", "Shirley/NDT rankings", "not clearly pre-round; excluded by default"),
        ("rank_diff", "Shirley rankings", "context feature only; not used in primary search"),
    ]:
        rows.append({
            "feature_name": feature,
            "source_file": source,
            "coverage_non_null_rows": "",
            "nonzero_rows": "",
            "leakage_risk": "high",
            "keep_discard_recommendation": f"exclude: {reason}",
        })
    return pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = build_feature_frame()
    inventory = make_inventory(df)
    inventory.to_csv(FEATURE_INVENTORY_OUT, index=False)

    experiments = [
        ("locked_interaction_logistic", BASE_FEATURES, locked_model(), "comparison baseline"),
        ("parser_quality_plus_locked", BASE_FEATURES + PARSER_FEATURES, locked_model(), "tests parse/data-quality flags"),
        ("manual_interactions_logistic", BASE_FEATURES + MANUAL_INTERACTIONS, plain_logistic(), "small selected interaction terms only"),
        ("side_specific_plus_locked", BASE_FEATURES + SIDE_FEATURES, locked_model(), "aff/neg-specific structure"),
        ("highlight_semantic_plus_locked", BASE_FEATURES + HIGHLIGHT_FEATURES, locked_model(), "highlighted evidence semantic counts"),
        ("direct_clash_plus_locked", BASE_FEATURES + DIRECT_CLASH_FEATURES, locked_model(), "matched aff/neg highlighted evidence overlap"),
        ("text_light_plus_locked", BASE_FEATURES + TEXT_LIGHT_FEATURES, locked_model(), "lightweight text length/citation proxies"),
        ("combined_safe_features", BASE_FEATURES + PARSER_FEATURES + HIGHLIGHT_FEATURES + DIRECT_CLASH_FEATURES + TEXT_LIGHT_FEATURES, locked_model(), "broad but non-leaky combined diagnostic"),
        ("elastic_net_logistic", BASE_FEATURES, Pipeline([
            ("interactions", PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(C=0.5, penalty="elasticnet", solver="saga", l1_ratio=0.5, max_iter=5000, random_state=42)),
        ]), "elastic net diagnostic on locked feature space"),
        ("linear_svm", BASE_FEATURES, Pipeline([
            ("interactions", PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)),
            ("scaler", StandardScaler()),
            ("model", LinearSVC(C=0.5, random_state=42, max_iter=5000)),
        ]), "linear SVM diagnostic"),
        ("calibrated_linear_svm", BASE_FEATURES, Pipeline([
            ("interactions", PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)),
            ("scaler", StandardScaler()),
            ("model", CalibratedClassifierCV(LinearSVC(C=0.5, random_state=42, max_iter=5000), cv=3)),
        ]), "calibrated linear SVM diagnostic"),
        ("small_random_forest", BASE_FEATURES, Pipeline([
            ("model", RandomForestClassifier(n_estimators=100, max_depth=3, min_samples_leaf=8, random_state=42)),
        ]), "small RF diagnostic"),
        ("gradient_boosting_diagnostic", BASE_FEATURES, Pipeline([
            ("model", GradientBoostingClassifier(n_estimators=75, learning_rate=0.05, max_depth=2, random_state=42)),
        ]), "gradient boosting diagnostic"),
    ]

    results = []
    failures = []
    for name, features, model, notes in experiments:
        try:
            result = evaluate_experiment(df, name, features, model, notes)
            results.append(result)
        except Exception as exc:
            failures.append({
                "experiment_name": name,
                "features_used": ", ".join(features),
                "model": str(model),
                "validation_accuracy": math.nan,
                "majority_baseline": math.nan,
                "difference_vs_locked_baseline": math.nan,
                "true_L_pred_L": "",
                "true_L_pred_W": "",
                "true_W_pred_L": "",
                "true_W_pred_W": "",
                "status": "crash",
                "runtime_seconds": "",
                "notes": f"{notes}; crash: {exc}",
            })

    locked_accuracy = next(result["validation_accuracy"] for result in results if result["experiment_name"] == "locked_interaction_logistic")
    for result in results:
        result["difference_vs_locked_baseline"] = result["validation_accuracy"] - locked_accuracy
        if result["experiment_name"] == "locked_interaction_logistic":
            result["status"] = "baseline"
        elif result["validation_accuracy"] > locked_accuracy:
            result["status"] = "keep_candidate"
        else:
            result["status"] = "discard"

    public_results = [
        {key: value for key, value in result.items() if not key.startswith("_")}
        for result in results
    ] + failures
    experiment_table = pd.DataFrame(public_results).sort_values("validation_accuracy", ascending=False, na_position="last")
    experiment_table.to_csv(EXPERIMENT_TABLE_OUT, index=False)

    best_result = max(results, key=lambda item: item["validation_accuracy"])
    best_model = best_result["_model_object"]
    best_features = best_result["_features"]
    train = df[df["dataset_split"] == "train"].copy()
    val = df[df["dataset_split"] == "validation"].copy().reset_index(names="row_id")
    best_model.fit(train[best_features].fillna(0), encode_target(train["win_loss"]))
    pred = best_model.predict(val[best_features].fillna(0))
    if hasattr(best_model, "predict_proba"):
        proba = best_model.predict_proba(val[best_features].fillna(0))[:, 1]
    else:
        proba = [math.nan] * len(val)
    val["actual_outcome"] = val["win_loss"]
    val["predicted_outcome"] = ["W" if int(value) == 1 else "L" for value in pred]
    val["predicted_win_probability"] = proba
    val["error_type"] = "correct"
    val.loc[(val["actual_outcome"] == "L") & (val["predicted_outcome"] == "W"), "error_type"] = "false_positive"
    val.loc[(val["actual_outcome"] == "W") & (val["predicted_outcome"] == "L"), "error_type"] = "false_negative"
    prediction_cols = [
        "row_id", "source_file", "team_code", "opponent", "round_number", "side",
        "actual_outcome", "predicted_outcome", "predicted_win_probability", "error_type",
    ] + BASE_FEATURES
    val[prediction_cols].to_csv(BEST_PREDICTIONS_OUT, index=False)

    mistakes = val[val["error_type"] != "correct"].copy()
    false_pos = int((val["error_type"] == "false_positive").sum())
    false_neg = int((val["error_type"] == "false_negative").sum())
    high_conf = mistakes.sort_values("predicted_win_probability", ascending=False).head(5)

    with SUMMARY_OUT.open("w", encoding="utf-8") as handle:
        handle.write("# Non-Leaky Feature Search Summary\n\n")
        handle.write(f"- Locked baseline accuracy: {locked_accuracy:.6f}\n")
        handle.write(f"- Best validation accuracy found: {best_result['validation_accuracy']:.6f}\n")
        handle.write(f"- Best experiment: {best_result['experiment_name']}\n")
        handle.write(f"- Best features: {', '.join(best_features)}\n")
        handle.write(f"- Best confusion matrix: true_L_pred_L={best_result['true_L_pred_L']}, true_L_pred_W={best_result['true_L_pred_W']}, true_W_pred_L={best_result['true_W_pred_L']}, true_W_pred_W={best_result['true_W_pred_W']}\n")
        handle.write(f"- False positives for best model: {false_pos}\n")
        handle.write(f"- False negatives for best model: {false_neg}\n")
        handle.write(f"- Reached >70% validation accuracy: {best_result['validation_accuracy'] > 0.70}\n")
        handle.write("\n## Leakage Audit\n")
        handle.write("- Excluded outcome/result fields: `win_loss`, `Ballots`, `WinPm`, `PtsPm`, judge-decision style fields.\n")
        handle.write("- Excluded identity/context fields by default: `team_code`, `opponent`, `judge`, `tournament_name`.\n")
        handle.write("- Excluded ranking features from primary search because Shirley/NDT ranking files appear to include tournament results, not clearly pre-round rankings.\n")
        handle.write("\n## Recommendation\n")
        if best_result["validation_accuracy"] > locked_accuracy:
            handle.write("- A non-leaky candidate beat the locked baseline, but validate carefully because the validation set is small.\n")
        else:
            handle.write("- No searched non-leaky feature set credibly replaces the locked interaction-logistic model.\n")
        handle.write("- Treat failures to exceed 70% as evidence that feature quality/noise remains the bottleneck.\n")
        handle.write("\n## Highest-Confidence Mistakes Preview\n")
        for row in high_conf.itertuples():
            handle.write(f"- {row.team_code} vs {row.opponent}, round {row.round_number}, actual={row.actual_outcome}, predicted={row.predicted_outcome}, p_win={row.predicted_win_probability}\n")

    print("Feature search complete")
    print(f"Locked baseline accuracy: {locked_accuracy:.6f}")
    print(f"Best experiment: {best_result['experiment_name']}")
    print(f"Best validation accuracy: {best_result['validation_accuracy']:.6f}")
    print(f"Outputs: {FEATURE_INVENTORY_OUT}, {EXPERIMENT_TABLE_OUT}, {BEST_PREDICTIONS_OUT}, {SUMMARY_OUT}")


if __name__ == "__main__":
    main()
