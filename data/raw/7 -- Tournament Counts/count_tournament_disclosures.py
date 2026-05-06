#!/usr/bin/env python3
"""
count_tournament_disclosures.py

Recursively scan a disclosure tree like:

ndtceda25/
    Michigan/
        BaPa/
            Michigan-BaPa-Aff-Georgetown-Doubles.docx
            Michigan-BaPa-Neg-NDT-Round-3.docx
            ...

and count how many disclosed docs belong to each prelim tournament.

Rules:
- Uses the 4th hyphen-delimited token in the filename as the tournament key.
- Ignores elim rounds such as Octas, Doubles, Quarters, Semis, Finals, etc.
- By default only counts .docx files.
- Outputs a CSV and prints the top tournaments.

Usage:
    python count_tournament_disclosures.py --root "C:/path/to/ndtceda25"
    python count_tournament_disclosures.py --root "C:/path/to/ndtceda25" --top 30
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Optional

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


def looks_like_doc(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".docx"


def is_elim_filename(stem: str) -> bool:
    return bool(ELIM_RE.search(stem))


def extract_tournament_token(stem: str) -> Optional[str]:
    """
    Expected pattern:
        School-TeamCode-Side-Tournament-...
    Example:
        Michigan-BaPa-Aff-Georgetown-Doubles
    returns:
        Georgetown
    """
    parts = [p.strip() for p in stem.split("-") if p.strip()]
    if len(parts) < 4:
        return None
    return parts[3]


def iter_docx_files(root: Path) -> Iterable[Path]:
    yield from root.rglob("*.docx")


def main() -> int:
    parser = argparse.ArgumentParser(description="Count prelim tournament disclosures in a nested disclosure tree.")
    parser.add_argument("--root", required=True, help="Path to the ndtceda25 root folder")
    parser.add_argument("--top", type=int, default=25, help="How many top tournaments to print")
    parser.add_argument(
        "--output",
        default="tournament_disclosure_counts.csv",
        help="Output CSV filename",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root folder not found or not a directory: {root}")

    tournament_counts: Counter[str] = Counter()
    skipped_examples: defaultdict[str, list[str]] = defaultdict(list)

    total_docx = 0
    counted_docx = 0

    for path in iter_docx_files(root):
        total_docx += 1
        stem = path.stem

        if is_elim_filename(stem):
            if len(skipped_examples["elim"]) < 5:
                skipped_examples["elim"].append(path.name)
            continue

        tournament = extract_tournament_token(stem)
        if not tournament:
            if len(skipped_examples["bad_pattern"]) < 5:
                skipped_examples["bad_pattern"].append(path.name)
            continue

        tournament_counts[tournament] += 1
        counted_docx += 1

    output_path = root / args.output
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "tournament", "count"])
        for rank, (tournament, count) in enumerate(tournament_counts.most_common(), start=1):
            writer.writerow([rank, tournament, count])

    print(f"Scanned .docx files: {total_docx}")
    print(f"Counted prelim disclosures: {counted_docx}")
    print(f"Output written to: {output_path}")
    print()
    print(f"Top {args.top} tournaments by disclosure count:")
    for rank, (tournament, count) in enumerate(tournament_counts.most_common(args.top), start=1):
        print(f"{rank:>2}. {tournament:<25} {count}")

    if skipped_examples:
        print("\nSkipped examples:")
        for reason, examples in skipped_examples.items():
            print(f"  {reason}:")
            for ex in examples:
                print(f"    - {ex}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
