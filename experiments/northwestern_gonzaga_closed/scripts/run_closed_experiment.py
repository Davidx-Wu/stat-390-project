#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


REPO_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_DIR = REPO_ROOT / "experiments" / "northwestern_gonzaga_closed"
DATA_RAW = EXPERIMENT_DIR / "data_raw"
DATA_PROCESSED = EXPERIMENT_DIR / "data_processed"
DIAGNOSTICS = EXPERIMENT_DIR / "diagnostics"
RESULTS = EXPERIMENT_DIR / "results"
LOGS = EXPERIMENT_DIR / "logs"
SCRIPTS = EXPERIMENT_DIR / "scripts"

PREVIEW_PATH = DIAGNOSTICS / "northwestern_doc_selection_preview.csv"
NDT_ROOT = REPO_ROOT / "data" / "raw" / "8 -- Keep Only Tournament Docs" / "ndtceda25"
PARSER_PATH = SCRIPTS / "debate_doc_parser_vF.py"
NORTHWESTERN_TABROOM = DATA_RAW / "Northwestern_Tabroom-prelims_table.csv"
GONZAGA_SOURCE = REPO_ROOT / "data" / "processed" / "gonzaga_speech_dataset_v1.csv"

BASE_FEATURES = [
    "num_positions",
    "num_adv_inh_solv",
    "num_offs",
    "num_cards_total",
    "num_cards_with_highlight",
    "total_highlighted_words",
]

MANUAL_INTERACTIONS = [
    "num_offs_x_num_cards_total",
    "num_offs_x_total_highlighted_words",
    "num_cards_total_x_num_cards_with_highlight",
    "num_positions_x_num_cards_total",
    "num_adv_inh_solv_x_num_cards_total",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the closed Northwestern + Gonzaga experiment.")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Maximum new Northwestern docs to parse this run. Use 0 to parse all remaining docs.",
    )
    return parser


def read_csv_if_nonempty(path: Path) -> pd.DataFrame | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        df = pd.read_csv(path)
    except Exception:
        return None
    return None if df.empty else df


def ensure_dirs() -> None:
    for path in [
        DATA_PROCESSED,
        DATA_PROCESSED / "northwestern_speech_rows",
        DIAGNOSTICS,
        DIAGNOSTICS / "northwestern_parse_rows",
        RESULTS,
        LOGS,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def safe_to_csv(df: pd.DataFrame, path: Path, *, index: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(5):
        try:
            df.to_csv(path, index=index)
            return path
        except PermissionError:
            time.sleep(1 + attempt)
    fallback = path.with_name(f"{path.stem}_write_blocked_{int(time.time())}{path.suffix}")
    df.to_csv(fallback, index=index)
    return fallback


def safe_write_text(text: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(5):
        try:
            path.write_text(text, encoding="utf-8")
            return path
        except PermissionError:
            time.sleep(1 + attempt)
    fallback = path.with_name(f"{path.stem}_write_blocked_{int(time.time())}{path.suffix}")
    fallback.write_text(text, encoding="utf-8")
    return fallback


def read_csvs(paths: list[Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        df = read_csv_if_nonempty(path)
        if df is not None:
            frames.append(df)
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


def load_current_northwestern_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_out = DATA_PROCESSED / "northwestern_speech_dataset_closed.csv"
    run_out = DIAGNOSTICS / "northwestern_parse_summary.csv"
    row_dir = DATA_PROCESSED / "northwestern_speech_rows"
    run_row_dir = DIAGNOSTICS / "northwestern_parse_rows"

    northwestern = read_csvs(([summary_out] if summary_out.exists() else []) + sorted(row_dir.glob("*.csv")))
    if not northwestern.empty and "source_file" in northwestern.columns:
        northwestern = northwestern.drop_duplicates(subset=["source_file"], keep="first")
    run_log = read_csvs(([run_out] if run_out.exists() else []) + sorted(run_row_dir.glob("*.csv")))
    if not run_log.empty and "selected_file_path" in run_log.columns:
        run_log = run_log.drop_duplicates(subset=["selected_file_path"], keep="first")
    join_failures = (
        northwestern[~northwestern["win_loss"].isin(["W", "L"])].copy()
        if not northwestern.empty and "win_loss" in northwestern.columns
        else pd.DataFrame()
    )
    return northwestern, run_log, join_failures


def write_progress_log(preview: pd.DataFrame, northwestern: pd.DataFrame, run_log: pd.DataFrame, start: float, partial: bool) -> None:
    selected = len(preview)
    parsed = int(run_log["parse_success"].sum()) if not run_log.empty and "parse_success" in run_log else 0
    joined = int(run_log["join_success"].sum()) if not run_log.empty and "join_success" in run_log else 0
    usable_rows = int(northwestern["win_loss"].isin(["W", "L"]).sum()) if not northwestern.empty and "win_loss" in northwestern else 0
    lines = [
        "# Northwestern Closed Parse Progress",
        "",
        f"- Status: {'partial' if partial else 'complete'}",
        f"- Parsed count / selected docs: {len(run_log)} / {selected}",
        f"- Parsed successfully: {parsed}",
        f"- Joined to outcomes: {joined}",
        f"- Usable rows with non-null outcome: {usable_rows}",
        f"- Runtime seconds this invocation: {time.time() - start:.2f}",
    ]
    safe_write_text("\n".join(lines) + "\n", LOGS / "northwestern_progress.md")


def build_northwestern_dataset(batch_size: int = 100) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, bool]:
    preview = pd.read_csv(PREVIEW_PATH)
    temp_dir = DATA_PROCESSED / "_northwestern_temp_single_run"
    summary_out = DATA_PROCESSED / "northwestern_speech_dataset_closed.csv"
    run_out = DIAGNOSTICS / "northwestern_parse_summary.csv"
    join_out = DIAGNOSTICS / "northwestern_join_failures.csv"
    row_dir = DATA_PROCESSED / "northwestern_speech_rows"
    run_row_dir = DIAGNOSTICS / "northwestern_parse_rows"

    processed_paths: set[str] = set()
    _northwestern, existing_run, _join_failures = load_current_northwestern_outputs()
    if not existing_run.empty and "selected_file_path" in existing_run.columns:
        processed_paths = set(existing_run["selected_file_path"].astype(str))

    start = time.time()
    parsed_this_run = 0
    for index, row in preview.iterrows():
        rel_path = Path(row["selected_file_path"])
        rel_path_str = str(rel_path)
        if rel_path_str in processed_paths:
            continue
        if batch_size > 0 and parsed_this_run >= batch_size:
            break
        doc_path = NDT_ROOT / rel_path
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(PARSER_PATH),
            "--doc",
            str(doc_path),
            "--tournament-csv",
            str(NORTHWESTERN_TABROOM),
            "--outdir",
            str(temp_dir),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(EXPERIMENT_DIR))

        summary_df = read_csv_if_nonempty(temp_dir / "speech_summary.csv")
        summary_rows = 0 if summary_df is None else len(summary_df)
        parse_success = result.returncode == 0 and summary_rows > 0
        join_success = False

        if summary_df is not None:
            summary_df["source_file"] = summary_df["source_file"].astype(str)
            summary_df["tournament_source"] = "Northwestern"
            safe_to_csv(summary_df, row_dir / f"{index + 1:04d}.csv")
            for _, summary_row in summary_df.iterrows():
                join_success = summary_row.get("win_loss") in {"W", "L"}
                if not join_success:
                    safe_to_csv(pd.DataFrame([summary_row.to_dict()]), DIAGNOSTICS / "northwestern_join_failure_rows" / f"{index + 1:04d}.csv")

        safe_to_csv(
            pd.DataFrame(
                [
                    {
                "file_index": index + 1,
                "selected_file_path": rel_path_str,
                "returncode": result.returncode,
                "parse_success": parse_success,
                "join_success": join_success,
                "summary_rows": summary_rows,
                "stdout_excerpt": (result.stdout or "")[:500].replace("\n", " | "),
                "stderr_excerpt": (result.stderr or "")[:500].replace("\n", " | "),
                    }
                ]
            ),
            run_row_dir / f"{index + 1:04d}.csv",
        )
        processed_paths.add(rel_path_str)
        parsed_this_run += 1

        if (index + 1) % 50 == 0 or (index + 1) == len(preview):
            print(f"Parsed Northwestern progress: {len(processed_paths)}/{len(preview)} docs...")

    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    northwestern, run_log, join_failures = load_current_northwestern_outputs()
    aggregate_summary_written = safe_to_csv(northwestern, summary_out) if not northwestern.empty else summary_out
    aggregate_run_written = safe_to_csv(run_log, run_out) if not run_log.empty else run_out
    aggregate_join_written = safe_to_csv(join_failures, join_out) if not join_failures.empty else join_out
    complete = len(run_log) >= len(preview)

    usable_rows = int(northwestern["win_loss"].isin(["W", "L"]).sum()) if "win_loss" in northwestern else 0
    parse_success_count = int(run_log["parse_success"].sum()) if not run_log.empty else 0
    join_success_count = int(run_log["join_success"].sum()) if not run_log.empty else 0
    parse_failure_count = len(run_log) - parse_success_count
    join_failure_count = parse_success_count - join_success_count
    win_loss_distribution = (
        northwestern.loc[northwestern["win_loss"].isin(["W", "L"]), "win_loss"]
        .value_counts()
        .sort_index()
        .to_dict()
        if "win_loss" in northwestern
        else {}
    )

    safe_write_text(
        "\n".join(
            [
                "# Northwestern Closed Build Log",
                "",
                f"- Status: {'complete' if complete else 'partial'}",
                f"- Selected docs: {len(preview)}",
                f"- Parsed count / selected docs: {len(run_log)} / {len(preview)}",
                f"- Parsed successfully: {parse_success_count}",
                f"- Parse failures: {parse_failure_count}",
                f"- Joined to outcomes: {join_success_count}",
                f"- Join failures: {join_failure_count}",
                f"- Usable rows with non-null outcome: {usable_rows}",
                f"- Win/loss distribution: {win_loss_distribution}",
                f"- Runtime seconds: {time.time() - start:.2f}",
                f"- Aggregate summary path: {aggregate_summary_written}",
                f"- Aggregate parse summary path: {aggregate_run_written}",
                f"- Aggregate join failures path: {aggregate_join_written}",
            ]
        )
        + "\n",
        LOGS / "northwestern_build_log.md",
    )
    write_progress_log(preview, northwestern, run_log, start, partial=not complete)
    return northwestern, run_log, join_failures, complete


def quality_gate(northwestern: pd.DataFrame, run_log: pd.DataFrame) -> None:
    selected = len(pd.read_csv(PREVIEW_PATH))
    parsed = int(run_log["parse_success"].sum()) if not run_log.empty else 0
    joined = int(run_log["join_success"].sum()) if not run_log.empty else 0
    if selected == 0 or parsed == 0 or joined / selected < 0.5:
        msg = (
            "# Closed Experiment Stopped at Quality Gate\n\n"
            f"- Selected docs: {selected}\n"
            f"- Parsed successfully: {parsed}\n"
            f"- Joined to outcomes: {joined}\n"
            "- Reason: join success below 50%; modeling skipped.\n"
        )
        (LOGS / "closed_experiment_summary.md").write_text(msg, encoding="utf-8")
        raise SystemExit("Join success below quality gate; stopped before modeling.")


def add_manual_interactions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["num_offs_x_num_cards_total"] = out["num_offs"] * out["num_cards_total"]
    out["num_offs_x_total_highlighted_words"] = out["num_offs"] * out["total_highlighted_words"]
    out["num_cards_total_x_num_cards_with_highlight"] = out["num_cards_total"] * out["num_cards_with_highlight"]
    out["num_positions_x_num_cards_total"] = out["num_positions"] * out["num_cards_total"]
    out["num_adv_inh_solv_x_num_cards_total"] = out["num_adv_inh_solv"] * out["num_cards_total"]
    return out


def create_combined_dataset(northwestern: pd.DataFrame) -> pd.DataFrame:
    gonzaga = pd.read_csv(GONZAGA_SOURCE)
    gonzaga = gonzaga.drop(columns=["dataset_split"], errors="ignore")
    gonzaga["tournament_source"] = "Gonzaga"
    gonzaga.to_csv(DATA_PROCESSED / "gonzaga_speech_dataset_closed.csv", index=False)

    combined = pd.concat([gonzaga, northwestern], ignore_index=True, sort=False)
    combined = combined[combined["win_loss"].isin(["W", "L"])].copy()
    combined = add_manual_interactions(combined)
    combined.to_csv(DATA_PROCESSED / "combined_speech_dataset_closed.csv", index=False)
    return combined


def create_closed_split(combined: pd.DataFrame) -> pd.DataFrame:
    train, temp = train_test_split(
        combined,
        train_size=0.70,
        random_state=42,
        stratify=combined["win_loss"],
    )
    validation, test = train_test_split(
        temp,
        train_size=0.50,
        random_state=42,
        stratify=temp["win_loss"],
    )
    train = train.copy()
    validation = validation.copy()
    test = test.copy()
    train["dataset_split"] = "train"
    validation["dataset_split"] = "validation"
    test["dataset_split"] = "test"
    split_df = pd.concat([train, validation, test], ignore_index=True)
    split_df.to_csv(DATA_PROCESSED / "combined_speech_dataset_closed_with_split.csv", index=False)

    rows = []
    for split, group in split_df.groupby("dataset_split"):
        rows.append({"summary_type": "rows_by_split", "group": split, "rows": len(group), "W": "", "L": ""})
    for (tournament, split), group in split_df.groupby(["tournament_source", "dataset_split"]):
        rows.append({"summary_type": "rows_by_tournament_and_split", "group": f"{tournament}:{split}", "rows": len(group), "W": "", "L": ""})
    for split, group in split_df.groupby("dataset_split"):
        counts = group["win_loss"].value_counts().to_dict()
        rows.append({"summary_type": "win_loss_by_split", "group": split, "rows": len(group), "W": counts.get("W", 0), "L": counts.get("L", 0)})
    for tournament, group in split_df.groupby("tournament_source"):
        counts = group["win_loss"].value_counts().to_dict()
        rows.append({"summary_type": "win_loss_by_tournament", "group": tournament, "rows": len(group), "W": counts.get("W", 0), "L": counts.get("L", 0)})
    pd.DataFrame(rows).to_csv(DIAGNOSTICS / "combined_split_summary.csv", index=False)
    pd.DataFrame(rows).to_csv(DIAGNOSTICS / "split_summary.csv", index=False)
    return split_df


def save_diagnostics(split_df: pd.DataFrame, run_log: pd.DataFrame) -> None:
    coverage_rows = []
    for tournament, group in split_df.groupby("tournament_source"):
        counts = group["win_loss"].value_counts().to_dict()
        coverage_rows.append(
            {
                "tournament_source": tournament,
                "rows": len(group),
                "wins": counts.get("W", 0),
                "losses": counts.get("L", 0),
            }
        )
    pd.DataFrame(coverage_rows).to_csv(DIAGNOSTICS / "tournament_coverage_summary.csv", index=False)

    missing_rows = []
    for col in BASE_FEATURES:
        missing_rows.append(
            {
                "feature": col,
                "missing_rows": int(split_df[col].isna().sum()),
                "zero_rows": int((split_df[col].fillna(0) == 0).sum()),
            }
        )
    pd.DataFrame(missing_rows).to_csv(DIAGNOSTICS / "feature_missingness_summary.csv", index=False)


def fit_and_predict(split_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = split_df[split_df["dataset_split"] == "train"].copy()
    validation = split_df[split_df["dataset_split"] == "validation"].copy()
    y_train = train["win_loss"]
    y_val = validation["win_loss"]
    majority_class = y_train.value_counts().idxmax()

    experiments = [
        ("majority_baseline", [], "majority"),
        ("structured_logistic", BASE_FEATURES, "logistic"),
        ("manual_interaction_logistic", BASE_FEATURES + MANUAL_INTERACTIONS, "manual_logistic"),
    ]
    table_rows = []
    prediction_frames = []
    matrix_rows = []

    for name, features, model_kind in experiments:
        if model_kind == "majority":
            pred = pd.Series([majority_class] * len(validation), index=validation.index)
            prob = pd.Series([1.0 if majority_class == "W" else 0.0] * len(validation), index=validation.index)
            model_desc = f"majority_class={majority_class}"
        else:
            model = Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("model", LogisticRegression(C=0.5 if model_kind == "manual_logistic" else 1.0, max_iter=1000, random_state=42)),
                ]
            )
            model.fit(train[features].fillna(0), y_train)
            pred = pd.Series(model.predict(validation[features].fillna(0)), index=validation.index)
            classes = list(model.named_steps["model"].classes_)
            if "W" in classes:
                prob = pd.Series(model.predict_proba(validation[features].fillna(0))[:, classes.index("W")], index=validation.index)
            else:
                prob = pd.Series([0.0] * len(validation), index=validation.index)
            model_desc = str(model)

        acc = accuracy_score(y_val, pred)
        labels = ["L", "W"]
        cm = confusion_matrix(y_val, pred, labels=labels)
        table_rows.append(
            {
                "experiment_name": name,
                "features_used": ", ".join(features) if features else "none",
                "model": model_desc,
                "validation_accuracy": acc,
                "validation_rows": len(validation),
            }
        )
        matrix_rows.append(
            {
                "experiment_name": name,
                "true_L_pred_L": int(cm[0, 0]),
                "true_L_pred_W": int(cm[0, 1]),
                "true_W_pred_L": int(cm[1, 0]),
                "true_W_pred_W": int(cm[1, 1]),
            }
        )
        pred_frame = validation[
            [
                "source_file",
                "team_code",
                "opponent",
                "round_number",
                "side",
                "tournament_source",
                *BASE_FEATURES,
            ]
        ].copy()
        pred_frame["experiment_name"] = name
        pred_frame["actual_outcome"] = y_val
        pred_frame["predicted_outcome"] = pred
        pred_frame["predicted_win_probability"] = prob
        pred_frame["error_type"] = [
            "correct"
            if actual == predicted
            else ("false_positive" if predicted == "W" and actual == "L" else "false_negative")
            for actual, predicted in zip(y_val, pred)
        ]
        prediction_frames.append(pred_frame)

    experiment_table = pd.DataFrame(table_rows)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    matrices = pd.DataFrame(matrix_rows)
    misclassifications = predictions[predictions["error_type"] != "correct"].copy()

    experiment_table.to_csv(RESULTS / "closed_experiment_table.csv", index=False)
    predictions.to_csv(RESULTS / "closed_validation_predictions.csv", index=False)
    misclassifications.to_csv(RESULTS / "closed_validation_misclassifications.csv", index=False)
    matrices.to_csv(RESULTS / "closed_confusion_matrices.csv", index=False)
    return experiment_table, predictions, matrices


def write_summary(
    northwestern: pd.DataFrame,
    run_log: pd.DataFrame,
    split_df: pd.DataFrame,
    experiment_table: pd.DataFrame,
) -> None:
    selected = len(pd.read_csv(PREVIEW_PATH))
    parsed = int(run_log["parse_success"].sum())
    joined = int(run_log["join_success"].sum())
    parse_failures = selected - parsed
    join_failures = parsed - joined
    split_sizes = split_df["dataset_split"].value_counts().to_dict()
    result_lines = [
        f"- {row.experiment_name}: validation_accuracy={row.validation_accuracy:.6f}, validation_rows={row.validation_rows}"
        for row in experiment_table.itertuples()
    ]
    manual_acc = float(experiment_table.loc[experiment_table["experiment_name"] == "manual_interaction_logistic", "validation_accuracy"].iloc[0])
    structured_acc = float(experiment_table.loc[experiment_table["experiment_name"] == "structured_logistic", "validation_accuracy"].iloc[0])
    comparison_note = (
        "Manual interactions improved over structured logistic in the closed combined validation split."
        if manual_acc > structured_acc
        else "Manual interactions did not improve over structured logistic in the closed combined validation split."
    )
    safe_write_text(
        "\n".join(
            [
                "# Northwestern + Gonzaga Closed Experiment Summary",
                "",
                "## Inputs",
                f"- Northwestern preview: {PREVIEW_PATH}",
                f"- Northwestern Tabroom CSV: {NORTHWESTERN_TABROOM}",
                f"- Gonzaga closed copy source: {GONZAGA_SOURCE}",
                "",
                "## Northwestern Build",
                f"- Docs selected: {selected}",
                f"- Docs parsed successfully: {parsed}",
                f"- Parse failures: {parse_failures}",
                f"- Rows joined to Tabroom outcomes: {joined}",
                f"- Join failures: {join_failures}",
                f"- Usable Northwestern rows with non-null outcome: {int(northwestern['win_loss'].isin(['W', 'L']).sum())}",
                f"- Northwestern win/loss distribution: {northwestern['win_loss'].value_counts().to_dict()}",
                "",
                "## Combined Dataset",
                f"- Combined rows: {len(split_df)}",
                f"- Split sizes: {split_sizes}",
                "",
                "## Validation Results",
                *result_lines,
                "",
                "## Interpretation",
                f"- {comparison_note}",
                "- This is a closed robustness check, not final test-set evidence.",
            ]
        )
        + "\n",
        LOGS / "closed_experiment_summary.md",
    )


def write_partial_summary(northwestern: pd.DataFrame, run_log: pd.DataFrame) -> None:
    selected = len(pd.read_csv(PREVIEW_PATH))
    parsed = int(run_log["parse_success"].sum()) if not run_log.empty and "parse_success" in run_log else 0
    joined = int(run_log["join_success"].sum()) if not run_log.empty and "join_success" in run_log else 0
    usable = int(northwestern["win_loss"].isin(["W", "L"]).sum()) if not northwestern.empty and "win_loss" in northwestern else 0
    win_loss_distribution = (
        northwestern.loc[northwestern["win_loss"].isin(["W", "L"]), "win_loss"].value_counts().to_dict()
        if not northwestern.empty and "win_loss" in northwestern
        else {}
    )
    safe_write_text(
        "\n".join(
            [
                "# Partial Northwestern Closed Experiment Diagnostic",
                "",
                "- Status: partial parse; modeling not run.",
                f"- Selected docs: {selected}",
                f"- Parse-summary rows completed: {len(run_log)} / {selected}",
                f"- Docs parsed successfully: {parsed}",
                f"- Rows joined to Tabroom outcomes: {joined}",
                f"- Usable rows with non-null outcome: {usable}",
                f"- Win/loss distribution in parsed subset: {win_loss_distribution}",
                "- Next action: rerun this script to continue from diagnostics/northwestern_parse_summary.csv.",
            ]
        )
        + "\n",
        LOGS / "closed_experiment_summary.md",
    )


def main() -> int:
    args = build_parser().parse_args()
    ensure_dirs()
    northwestern, run_log, _join_failures, complete = build_northwestern_dataset(batch_size=args.batch_size)
    if not complete:
        write_partial_summary(northwestern, run_log)
        print("Partial closed experiment parse complete for this batch.")
        print(f"Northwestern parse-summary rows completed: {len(run_log)} / {len(pd.read_csv(PREVIEW_PATH))}")
        print(f"Docs parsed successfully: {int(run_log['parse_success'].sum()) if not run_log.empty else 0}")
        print(f"Rows joined to outcomes: {int(run_log['join_success'].sum()) if not run_log.empty else 0}")
        print("Modeling skipped until all selected Northwestern docs are parsed.")
        return 0
    quality_gate(northwestern, run_log)
    combined = create_combined_dataset(northwestern)
    split_df = create_closed_split(combined)
    save_diagnostics(split_df, run_log)
    experiment_table, _predictions, _matrices = fit_and_predict(split_df)
    write_summary(northwestern, run_log, split_df, experiment_table)

    print("Closed experiment complete.")
    print(f"Northwestern docs selected: {len(pd.read_csv(PREVIEW_PATH))}")
    print(f"Northwestern docs parsed successfully: {int(run_log['parse_success'].sum())}")
    print(f"Northwestern rows joined: {int(run_log['join_success'].sum())}")
    print(f"Combined dataset rows: {len(split_df)}")
    print(experiment_table[["experiment_name", "validation_accuracy", "validation_rows"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
