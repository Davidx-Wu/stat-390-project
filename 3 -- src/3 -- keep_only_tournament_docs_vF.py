#!/usr/bin/env python3
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
    r"\bdoubles\b",
]
ELIM_RE = re.compile("|".join(ELIM_PATTERNS), re.IGNORECASE)

TOURNAMENT_PATTERNS = [
    (r"\bndt[- ]?qualifier\b", "NDT-Qualifier"),
    (r"\bfranklin\s+r\.?\s+shirley\b", "Wake"),
    (r"\bshirley\b", "Wake"),
    (r"\bfr\b", "Wake"),
    (r"\bowen\s+l\.?\s+coon\b", "Northwestern"),
    (r"\bowen\b", "Northwestern"),
    (r"\b55th\b", "Kentucky"),
    (r"\bjw\s+patterson\b", "Kentucky"),
    (r"\b80th\b", "NDT"),
    (r"\busna\b", "Navy"),
    (r"\bwfu\b", "Wake"),
    (r"\buk\b", "Kentucky"),
    (r"\bmostate\b", "Missouri State"),
    (r"\bmissouri\s+state\b", "Missouri State"),
    (r"\bnuso\b", "NUSO"),
    (r"\bada\b", "ADA"),
    (r"\bd3\b", "D3"),
    (r"\bsunflower\b", "Sunflower"),
    (r"\bhouston\b", "Houston"),
    (r"\boklahoma\b", "Oklahoma"),
    (r"\bindiana\b", "Indiana"),
    (r"\bminnesota\b", "Minnesota"),
    (r"\bgonzaga\b", "Gonzaga"),
    (r"\bgeorgetown\b", "Georgetown"),
    (r"\bkentucky\b", "Kentucky"),
    (r"\bnorthwestern\b", "Northwestern"),
    (r"\bwake(?:\s+forest)?\b", "Wake"),
    (r"\bnavy\b", "Navy"),
    (r"\bndt\b", "NDT"),
    (r"\btexas\b", "Texas"),
]

def is_elim_filename(stem: str) -> bool:
    return bool(ELIM_RE.search(stem))

def normalize_filename_for_search(stem: str) -> str:
    parts = stem.split("-")
    if len(parts) > 1:
        stem = "-".join(parts[1:])
    s = stem.replace("_", " ")
    s = s.replace("(", " ").replace(")", " ")
    s = re.sub(r"-+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_tournament_token(stem: str, exclude_qualifiers: bool = False) -> Optional[str]:
    search_text = normalize_filename_for_search(stem)
    if not search_text:
        return None
    if re.search(r"\baff[- ]+aff\b|\bneg[- ]+neg\b", search_text, flags=re.I):
        return None
    for pattern, canonical in TOURNAMENT_PATTERNS:
        if exclude_qualifiers and canonical == "NDT-Qualifier":
            continue
        if re.search(pattern, search_text, flags=re.I):
            return canonical
    return None

def main() -> int:
    parser = argparse.ArgumentParser(description="Copy only docs from a chosen prelim tournament.")
    parser.add_argument("--root", required=True, help="Path to ndtceda25")
    parser.add_argument("--tournament", required=True, help="Tournament token to keep")
    parser.add_argument("--dest", default=None, help="Destination folder")
    parser.add_argument("--exclude-qualifiers", action="store_true", help="Exclude NDT-Qualifier")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root folder not found or not a directory: {root}")

    target = args.tournament.strip().lower()
    dest = Path(args.dest) if args.dest else root.parent / f"{args.tournament.strip()}_only"
    dest.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped_elims = 0
    skipped_nonmatching = 0
    skipped_unmatched = 0

    for path in root.rglob("*.docx"):
        stem = path.stem
        if is_elim_filename(stem):
            skipped_elims += 1
            continue

        tournament = extract_tournament_token(stem, exclude_qualifiers=args.exclude_qualifiers)
        if not tournament:
            skipped_unmatched += 1
            continue

        if tournament.lower() != target:
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
    print(f"Skipped unmatched docs: {skipped_unmatched}")

if __name__ == "__main__":
    main()
