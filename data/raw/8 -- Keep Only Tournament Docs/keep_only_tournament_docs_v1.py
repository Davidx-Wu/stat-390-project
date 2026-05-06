#!/usr/bin/env python3
"""
keep_only_tournament_docs.py

Copy only the docs from one chosen tournament into a new folder, preserving
the original school/team subfolder structure.

Rules:
- Uses the 4th hyphen-delimited token in the filename as the tournament key.
- Ignores elim rounds such as Octas, Doubles, Quarters, Semis, Finals, etc.
- Only copies .docx files by default.

Usage:
    python keep_only_tournament_docs.py ^
        --root "C:/path/to/ndtceda25" ^
        --tournament "Georgetown"

Optional:
    --dest "C:/path/to/georgetown_only"
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Optional

ELIM_PATTERNS = [
    r"\bocta(s)?\b",
    r"\bdouble[- ]?octa(s)?\b",
    r"\btriple[- ]?octa(s)?\b",
    r"\bquarter(s|finals)?\b",
    r"\bsemi(s|finals)?\b",
    r"\bfinal(s)?\b",
    r"\bpartial[- ]?double(s)?\b",
    r"\boutround(s)?\b",
    r"\belim(s)?\b",
    r"\bbid round(s)?\b",
    r"\bround robin\b",
]
ELIM_RE = re.compile("|".join(ELIM_PATTERNS), re.IGNORECASE)


def is_elim_filename(stem: str) -> bool:
    return bool(ELIM_RE.search(stem))


def extract_tournament_token(stem: str) -> Optional[str]:
    parts = [p.strip() for p in stem.split("-") if p.strip()]
    if len(parts) < 4:
        return None
    return parts[3]


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy only docs from a chosen prelim tournament.")
    parser.add_argument("--root", required=True, help="Path to the ndtceda25 root folder")
    parser.add_argument("--tournament", required=True, help="Tournament token to keep, e.g. Georgetown")
    parser.add_argument(
        "--dest",
        default=None,
        help="Destination folder. Default: <root_parent>/<tournament>_only",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root folder not found or not a directory: {root}")

    tournament_target = args.tournament.strip().lower()
    dest = Path(args.dest) if args.dest else root.parent / f"{args.tournament.strip()}_only"
    dest.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped_elims = 0
    skipped_nonmatching = 0
    skipped_bad_pattern = 0

    for path in root.rglob("*.docx"):
        stem = path.stem

        if is_elim_filename(stem):
            skipped_elims += 1
            continue

        tournament = extract_tournament_token(stem)
        if not tournament:
            skipped_bad_pattern += 1
            continue

        if tournament.lower() != tournament_target:
            skipped_nonmatching += 1
            continue

        relative_path = path.relative_to(root)
        target_path = dest / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target_path)
        copied += 1

    print(f"Destination: {dest}")
    print(f"Copied docs: {copied}")
    print(f"Skipped elim docs: {skipped_elims}")
    print(f"Skipped nonmatching prelim docs: {skipped_nonmatching}")
    print(f"Skipped bad-pattern docs: {skipped_bad_pattern}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
