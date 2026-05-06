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
    r"\bbid round(s)?\b",
    r"\bround robin\b",
    r"\bdoubles\b",
]
ELIM_RE = re.compile("|".join(ELIM_PATTERNS), re.IGNORECASE)

SIDE_TOKENS = {"aff", "neg"}
STOPWORDS = {
    "round", "rd", "r", "prelim", "prelims", "1ac", "1nc", "2ac", "2nc", "1ar", "2ar", "2nr",
    "doc", "speech", "updated", "new", "redo", "copy", "operation", "zoomtown", "op", "college", "tournament"
}
ROUND_RE = re.compile(r"^round\s*\d+$", re.I)
NUMERIC_RE = re.compile(r"^\d+\.?$")
ZERO_NUMERIC_RE = re.compile(r"^0\d+$")
PARENS_RE = re.compile(r"\(([^()]*)\)")
QUALIFIER_RE = re.compile(r"\bqualifier\b", re.I)

def is_elim_filename(stem: str) -> bool:
    return bool(ELIM_RE.search(stem))

def normalize_piece(s: str) -> str:
    s = s.replace("_", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return s.strip(" -.")

def is_junk_token(token: str) -> bool:
    t = normalize_piece(token)
    if not t:
        return True
    low = t.lower()
    if low in STOPWORDS:
        return True
    if NUMERIC_RE.fullmatch(t) or ZERO_NUMERIC_RE.fullmatch(t):
        return True
    if ROUND_RE.fullmatch(t):
        return True
    return False

def canonicalize_tournament(name: str) -> str:
    t = normalize_piece(name)
    # collapse things like Georgetown College Tournament -> Georgetown
    t = re.sub(r"\bcollege tournament\b", "", t, flags=re.I)
    t = re.sub(r"\btournament\b", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" -")
    return t

def tokens_after_side(stem: str) -> list[str]:
    parts = [normalize_piece(p) for p in stem.split("-") if normalize_piece(p)]
    side_idx = None
    for i, p in enumerate(parts):
        if p.lower() in SIDE_TOKENS:
            side_idx = i
            break
    if side_idx is None:
        return []
    return parts[side_idx + 1 :]

def extract_parenthetical_tournament(stem: str) -> Optional[str]:
    # Prefer explicit tournament names inside parentheses, e.g.
    # (Georgetown-College-Tournament)
    for raw in PARENS_RE.findall(stem):
        candidate = canonicalize_tournament(raw.replace("-", " "))
        if not candidate:
            continue
        if is_junk_token(candidate):
            continue
        return candidate
    return None

def extract_tournament_token(stem: str, exclude_qualifiers: bool = False) -> Optional[str]:
    # First, honor explicit parenthetical tournament names when present.
    paren = extract_parenthetical_tournament(stem)
    if paren:
        if exclude_qualifiers and QUALIFIER_RE.search(paren):
            return None
        return paren

    tokens = tokens_after_side(stem)
    if not tokens:
        return None

    i = 0
    while i < len(tokens):
        token = tokens[i]
        low = token.lower()

        if is_junk_token(token):
            i += 1
            continue
        if ELIM_RE.search(token):
            return None

        # Merge obvious multiword tournaments
        if low == "ndt" and i + 1 < len(tokens) and tokens[i + 1].lower() == "qualifier":
            candidate = "NDT-Qualifier"
            if exclude_qualifiers:
                return None
            return candidate

        # plain NDT remains distinct from NDT-Qualifier
        candidate = canonicalize_tournament(token)
        if exclude_qualifiers and QUALIFIER_RE.search(candidate):
            return None
        return candidate

    return None

def iter_docx_files(root: Path) -> Iterable[Path]:
    yield from root.rglob("*.docx")

def main() -> int:
    parser = argparse.ArgumentParser(description="Count prelim tournament disclosures.")
    parser.add_argument("--root", required=True, help="Path to ndtceda25")
    parser.add_argument("--top", type=int, default=25, help="How many top tournaments to print")
    parser.add_argument("--output", default="tournament_disclosure_counts.csv", help="Output CSV name")
    parser.add_argument("--exclude-qualifiers", action="store_true", help="Exclude qualifier tournaments such as NDT-Qualifier")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root folder not found or not a directory: {root}")

    counts: Counter[str] = Counter()
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

        tournament = extract_tournament_token(stem, exclude_qualifiers=args.exclude_qualifiers)
        if not tournament:
            if len(skipped_examples["bad_pattern_or_excluded"]) < 12:
                skipped_examples["bad_pattern_or_excluded"].append(path.name)
            continue

        counts[tournament] += 1
        counted_docx += 1

    output_path = root / args.output
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "tournament", "count"])
        for rank, (tournament, count) in enumerate(counts.most_common(), start=1):
            writer.writerow([rank, tournament, count])

    print(f"Scanned .docx files: {total_docx}")
    print(f"Counted prelim disclosures: {counted_docx}")
    print(f"Output written to: {output_path}")
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

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
