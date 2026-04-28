#!/usr/bin/env python3
"""
build_gonzaga_dataset.py

Batch-runs debate_doc_parser.py over every .docx in Gonzaga_only and combines
the outputs into three dataset files:

- speech_summary_all.csv
- argument_audit_all.csv
- card_audit_all.csv

It also writes:
- run_log.csv
- failed_files.txt

Expected folder layout (all inside the same working directory):
    debate_doc_parser.py
    Gonzaga_Tabroom-prelims_table.csv
    Gonzaga_only/

Usage:
    python build_gonzaga_dataset.py

Optional:
    python build_gonzaga_dataset.py --base-dir "C:/path/to/2 -- Data Creation"
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Dict

import pandas as pd


def read_csv_if_nonempty(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        if path.stat().st_size == 0:
            return None
        df = pd.read_csv(path)
        if df.empty:
            return None
        return df
    except Exception:
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build combined Gonzaga datasets from parsed debate docs.")
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Directory containing debate_doc_parser.py, Gonzaga_Tabroom-prelims_table.csv, and Gonzaga_only/",
    )
    parser.add_argument(
        "--parser-file",
        default="3 -- src/1 -- debate_doc_parser_vF.py",
        help="Path to the single-doc parser script (relative to --base-dir)",
    )
    parser.add_argument(
        "--tabroom-csv",
        default="Gonzaga_Tabroom-prelims_table.csv",
        help="Filename of the Gonzaga prelims table CSV",
    )
    parser.add_argument(
        "--doc-folder",
        default="Gonzaga_only",
        help="Folder containing the Gonzaga-only disclosure docs",
    )
    parser.add_argument(
        "--output-folder",
        default="gonzaga_dataset_output",
        help="Folder where combined outputs will be written",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    base_dir = Path(args.base_dir).resolve()
    parser_path = base_dir / args.parser_file
    tabroom_csv = base_dir / args.tabroom_csv
    doc_folder = base_dir / args.doc_folder
    output_folder = base_dir / args.output_folder
    temp_folder = output_folder / "_temp_single_run"

    if not base_dir.exists():
        raise SystemExit(f"Base directory not found: {base_dir}")
    if not parser_path.exists():
        raise SystemExit(f"Parser file not found: {parser_path}")
    if not tabroom_csv.exists():
        raise SystemExit(f"Tabroom CSV not found: {tabroom_csv}")
    if not doc_folder.exists() or not doc_folder.is_dir():
        raise SystemExit(f"Document folder not found or not a directory: {doc_folder}")

    output_folder.mkdir(parents=True, exist_ok=True)

    docx_files = sorted(doc_folder.rglob("*.docx"))
    if not docx_files:
        raise SystemExit(f"No .docx files found under: {doc_folder}")

    summary_frames: List[pd.DataFrame] = []
    argument_frames: List[pd.DataFrame] = []
    card_frames: List[pd.DataFrame] = []
    run_log: List[Dict[str, object]] = []
    failed_files: List[str] = []

    print(f"Found {len(docx_files)} .docx files.")
    print(f"Base directory: {base_dir}")
    print(f"Output folder: {output_folder}")
    print()

    for i, doc_path in enumerate(docx_files, start=1):
        if temp_folder.exists():
            shutil.rmtree(temp_folder)
        temp_folder.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(parser_path),
            "--doc",
            str(doc_path),
            "--tournament-csv",
            str(tabroom_csv),
            "--outdir",
            str(temp_folder),
            "--strict",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(base_dir),
        )

        summary_path = temp_folder / "speech_summary.csv"
        argument_path = temp_folder / "argument_audit.csv"
        card_path = temp_folder / "card_audit.csv"

        summary_df = read_csv_if_nonempty(summary_path)
        argument_df = read_csv_if_nonempty(argument_path)
        card_df = read_csv_if_nonempty(card_path)

        summary_rows = 0 if summary_df is None else len(summary_df)
        argument_rows = 0 if argument_df is None else len(argument_df)
        card_rows = 0 if card_df is None else len(card_df)

        success = result.returncode == 0 and (summary_rows > 0 or argument_rows > 0 or card_rows > 0)

        if summary_df is not None:
            summary_frames.append(summary_df)
        if argument_df is not None:
            argument_frames.append(argument_df)
        if card_df is not None:
            card_frames.append(card_df)

        rel_doc = str(doc_path.relative_to(base_dir))
        run_log.append(
            {
                "file_index": i,
                "source_file": rel_doc,
                "returncode": result.returncode,
                "success": success,
                "summary_rows": summary_rows,
                "argument_rows": argument_rows,
                "card_rows": card_rows,
                "stdout_excerpt": (result.stdout or "")[:500].replace("\n", " | "),
                "stderr_excerpt": (result.stderr or "")[:500].replace("\n", " | "),
            }
        )

        if not success:
            failed_files.append(rel_doc)

        if i % 25 == 0 or i == len(docx_files):
            print(f"Processed {i}/{len(docx_files)} files...")

    if temp_folder.exists():
        shutil.rmtree(temp_folder)

    if summary_frames:
        pd.concat(summary_frames, ignore_index=True).to_csv(
            output_folder / "speech_summary_all.csv", index=False
        )
    else:
        pd.DataFrame().to_csv(output_folder / "speech_summary_all.csv", index=False)

    if argument_frames:
        pd.concat(argument_frames, ignore_index=True).to_csv(
            output_folder / "argument_audit_all.csv", index=False
        )
    else:
        pd.DataFrame().to_csv(output_folder / "argument_audit_all.csv", index=False)

    if card_frames:
        pd.concat(card_frames, ignore_index=True).to_csv(
            output_folder / "card_audit_all.csv", index=False
        )
    else:
        pd.DataFrame().to_csv(output_folder / "card_audit_all.csv", index=False)

    pd.DataFrame(run_log).to_csv(output_folder / "run_log.csv", index=False)

    with (output_folder / "failed_files.txt").open("w", encoding="utf-8") as f:
        for item in failed_files:
            f.write(item + "\n")

    success_count = sum(1 for row in run_log if row["success"])
    fail_count = len(run_log) - success_count

    print()
    print("Done.")
    print(f"Successful files: {success_count}")
    print(f"Failed files: {fail_count}")
    print(f"speech_summary_all.csv -> {output_folder / 'speech_summary_all.csv'}")
    print(f"argument_audit_all.csv -> {output_folder / 'argument_audit_all.csv'}")
    print(f"card_audit_all.csv -> {output_folder / 'card_audit_all.csv'}")
    print(f"run_log.csv -> {output_folder / 'run_log.csv'}")
    print(f"failed_files.txt -> {output_folder / 'failed_files.txt'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
