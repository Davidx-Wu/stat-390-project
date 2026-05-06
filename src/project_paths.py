"""Repo-relative paths for the STAT 390 debate project.

This helper is intentionally lightweight. Existing scripts still use their
original paths; new reproducibility scripts can import this module to avoid
hardcoded local machine paths.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = REPO_ROOT / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = REPO_ROOT / "results"
EXPERIMENTS_DIR = REPO_ROOT / "experiments"
ARCHIVE_DIR = REPO_ROOT / "archive"

LEGACY_SRC_DIR = REPO_ROOT / "3 -- src"
LEGACY_RESULTS_DIR = REPO_ROOT / "4 -- results"
LEGACY_LOGS_DIR = REPO_ROOT / "5 -- logs"

GONZAGA_V1 = PROCESSED_DATA_DIR / "gonzaga_speech_dataset_v1.csv"
GONZAGA_V2_WITH_TEXT = PROCESSED_DATA_DIR / "gonzaga_speech_dataset_v2_with_text.csv"

CLOSED_EXPERIMENT_DIR = EXPERIMENTS_DIR / "northwestern_gonzaga_closed"
CLOSED_COMBINED_SPLIT = CLOSED_EXPERIMENT_DIR / "data_processed" / "combined_speech_dataset_closed_with_split.csv"
CLOSED_PAIRED_SPLIT = CLOSED_EXPERIMENT_DIR / "data_processed" / "paired_round_dataset_closed_with_split.csv"
