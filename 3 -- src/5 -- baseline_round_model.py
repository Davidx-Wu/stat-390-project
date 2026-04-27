#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, log_loss
from sklearn.model_selection import train_test_split


def normalize_team_name(s: str) -> str:
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = s.replace("university of ", "")
    s = s.replace("&", "and")
    s = re.sub(r"\s+", " ", s)
    return s


def main() -> None:
    summary_path = Path("speech_summary_all.csv")
    rankings_path = Path("NDT_Rankings.csv")

    if not summary_path.exists():
        raise FileNotFoundError(f"Missing file: {summary_path.resolve()}")
    if not rankings_path.exists():
        raise FileNotFoundError(f"Missing file: {rankings_path.resolve()}")

    summary = pd.read_csv(summary_path)
    rankings = pd.read_csv(rankings_path)

    required_summary_cols = [
        "team_code",
        "side",
        "win_loss",
        "num_positions",
        "num_offs",
        "num_cards_total",
        "num_cards_with_highlight",
        "total_highlighted_words",
    ]
    missing_summary = [c for c in required_summary_cols if c not in summary.columns]
    if missing_summary:
        raise ValueError(f"speech_summary_all.csv is missing required columns: {missing_summary}")

    if "Entry" not in rankings.columns or "Place" not in rankings.columns:
        raise ValueError(
            "NDT_Rankings.csv must contain 'Entry' and 'Place' columns. "
            f"Found columns: {list(rankings.columns)}"
        )

    summary = summary[summary["win_loss"].isin(["W", "L"])].copy()
    if summary.empty:
        raise ValueError("No rows with win_loss in {'W','L'} were found.")

    summary["y"] = summary["win_loss"].map({"W": 1, "L": 0})

    summary["team_clean"] = summary["team_code"].apply(normalize_team_name)
    rankings["team_clean"] = rankings["Entry"].apply(normalize_team_name)
    rankings["rank"] = pd.to_numeric(rankings["Place"], errors="coerce")

    df = summary.merge(
        rankings[["team_clean", "rank"]],
        on="team_clean",
        how="left",
    )

    if df["rank"].notna().any():
        fill_rank = float(df["rank"].max()) + 10.0
    else:
        fill_rank = 999.0
    df["rank"] = df["rank"].fillna(fill_rank)

    df["side_aff"] = (df["side"].astype(str).str.lower() == "aff").astype(int)

    numeric_features = [
        "side_aff",
        "num_positions",
        "num_offs",
        "num_cards_total",
        "num_cards_with_highlight",
        "total_highlighted_words",
        "rank",
    ]

    X = df[numeric_features].copy()
    y = df["y"].copy()

    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

    train_idx, test_idx = train_test_split(
        df.index,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    X_train = X.loc[train_idx]
    X_test = X.loc[test_idx]
    y_train = y.loc[train_idx]
    y_test = y.loc[test_idx]

    model = LogisticRegression(max_iter=2000)
    model.fit(X_train, y_train)

    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    print("\nMODEL PERFORMANCE")
    print("-" * 30)
    print(f"Rows used: {len(df)}")
    print(f"Train rows: {len(X_train)}")
    print(f"Test rows: {len(X_test)}")
    print(f"Accuracy: {accuracy_score(y_test, preds):.4f}")
    print(f"Log Loss: {log_loss(y_test, probs):.4f}")

    print("\nCLASSIFICATION REPORT")
    print("-" * 30)
    print(classification_report(y_test, preds, digits=4))

    coef_df = pd.DataFrame(
        {
            "feature": numeric_features,
            "coefficient": model.coef_[0],
        }
    ).sort_values("coefficient", ascending=False)

    print("\nFEATURE COEFFICIENTS")
    print("-" * 30)
    print(coef_df.to_string(index=False))

    results = df.loc[test_idx].copy()
    results["predicted_label"] = preds
    results["predicted_win_probability"] = probs

    output_cols = [
        c
        for c in [
            "source_file",
            "team_code",
            "round_number",
            "side",
            "opponent",
            "win_loss",
            "predicted_label",
            "predicted_win_probability",
            "rank",
            "num_positions",
            "num_offs",
            "num_cards_total",
            "num_cards_with_highlight",
            "total_highlighted_words",
        ]
        if c in results.columns
    ]

    results = results[output_cols].sort_values(
        by=["predicted_win_probability"],
        ascending=False,
    )

    results.to_csv("round_predictions.csv", index=False)
    coef_df.to_csv("feature_coefficients.csv", index=False)

    print("\nSaved files:")
    print(" - round_predictions.csv")
    print(" - feature_coefficients.csv")

    missing_rank_count = int((df["rank"] == fill_rank).sum())
    print(f"\nRows without matched rank (filled with {fill_rank:.0f}): {missing_rank_count}")

    print("\nExample predictions:")
    print(results.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
