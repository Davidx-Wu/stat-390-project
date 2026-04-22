#!/usr/bin/env python3
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
    (r"\bnuso\b", "Northwestern"),
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

def iter_docx_files(root: Path) -> Iterable[Path]:
    yield from root.rglob("*.docx")

def safe_tournament_filename(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    return s.strip("_") or "unknown"

def main() -> int:
    parser = argparse.ArgumentParser(description="Count prelim tournament disclosures using keyword matching.")
    parser.add_argument("--root", required=True, help="Path to ndtceda25")
    parser.add_argument("--top", type=int, default=25, help="How many top tournaments to print")
    parser.add_argument("--output", default="tournament_disclosure_counts.csv", help="Output CSV name")
    parser.add_argument("--exclude-qualifiers", action="store_true", help="Exclude NDT-Qualifier")
    parser.add_argument(
        "--write-file-lists",
        action="store_true",
        help="Write one text file per tournament listing all matched filenames",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root folder not found or not a directory: {root}")

    counts: Counter[str] = Counter()
    matched_files: defaultdict[str, list[str]] = defaultdict(list)
    skipped_examples: defaultdict[str, list[str]] = defaultdict(list)

    total_docx = 0
    counted_docx = 0

    for path in iter_docx_files(root):
        total_docx += 1
        stem = path.stem

        if is_elim_filename(stem):
            if len(skipped_examples["elim"]) < 8:
                skipped_examples["elim"].append(path.name)
            continue

        tournament = extract_tournament_token(stem, exclude_qualifiers=args.exclude_qualifiers)
        if not tournament:
            if len(skipped_examples["unmatched"]) < 20:
                skipped_examples["unmatched"].append(path.name)
            continue

        counts[tournament] += 1
        counted_docx += 1
        matched_files[tournament].append(str(path.relative_to(root)))

    output_path = root / args.output
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "tournament", "count"])
        for rank, (tournament, count) in enumerate(counts.most_common(), start=1):
            writer.writerow([rank, tournament, count])

    if args.write_file_lists:
        lists_dir = root / "tournament_file_lists"
        lists_dir.mkdir(exist_ok=True)
        for tournament, files in matched_files.items():
            out = lists_dir / f"{safe_tournament_filename(tournament)}.txt"
            with out.open("w", encoding="utf-8") as f:
                for file_name in sorted(files):
                    f.write(file_name + "\n")

    print(f"Scanned .docx files: {total_docx}")
    print(f"Counted prelim disclosures: {counted_docx}")
    print(f"Output written to: {output_path}")
    if args.write_file_lists:
        print(f"Tournament file lists written to: {root / 'tournament_file_lists'}")
    print()
    print(f"Top {args.top} tournaments by disclosure count:")
    for rank, (tournament, count) in enumerate(counts.most_common(args.top), start=1):
        print(f"{rank:>2}. {tournament:<25} {count}")

    if skipped_examples:
        print("\nSkipped examples:")
        for reason, examples in skipped_examples.items():
            print(f"  {reason}:")
            for ex in examples:
                print(f"    - {ex}")

if __name__ == "__main__":
    main()
