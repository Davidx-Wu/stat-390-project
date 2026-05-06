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

ROUND_TOKEN_RE = re.compile(r"^round$", re.I)
ROUND_NUM_RE = re.compile(r"^\d+\.?$")
SIDE_TOKENS = {"aff", "neg"}

STOPWORDS = {
    "round", "rd", "r", "prelim", "prelims", "1ac", "1nc", "2ac", "2nc", "1ar", "2ar", "2nr",
    "doc", "speech", "updated", "new", "redo", "copy", "operation", "zoomtown", "op",
    "college", "tournament", "debate", "debates", "annual", "memorial", "invitational",
    "open", "varsity", "novice", "jv", "swing", "online", "virtual"
}

# User-provided normalization / merges
ALIASES = {
    "shirley": "Wake",
    "fr": "Wake",
    "franklin r shirley": "Wake",
    "owen": "Northwestern",
    "owen l coon": "Northwestern",
    "55th": "Kentucky",
    "55th annual jw patterson": "Kentucky",
    "80th": "NDT",
    "usna": "Navy",
}

def normalize_piece(s: str) -> str:
    s = s.replace("_", " ").strip()
    s = re.sub(r"[()]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" -.")

def split_parts(stem: str) -> list[str]:
    # Split on one or more dashes to handle --- patterns
    raw = re.split(r"-+", stem)
    return [normalize_piece(p) for p in raw if normalize_piece(p)]

def is_elim_filename(stem: str) -> bool:
    return bool(ELIM_RE.search(stem))

def is_junk_token(token: str) -> bool:
    t = normalize_piece(token)
    low = t.lower()
    if not t:
        return True
    if low in STOPWORDS:
        return True
    if ROUND_NUM_RE.fullmatch(t):
        return True
    if len(t) <= 1 and not t.isalpha():
        return True
    return False

def canonicalize_tournament(name: str) -> str:
    t = normalize_piece(name)
    low = t.lower()

    # Strip generic wrappers
    low = re.sub(r"\bcollege tournament\b", "", low)
    low = re.sub(r"\btournament\b", "", low)
    low = re.sub(r"\bdebates?\b", "", low)
    low = re.sub(r"\bannual\b", "", low)
    low = re.sub(r"\binvitational\b", "", low)
    low = re.sub(r"\s+", " ", low).strip(" -.")

    if low in ALIASES:
        return ALIASES[low]

    # Title-case fallback, preserving known acronyms
    if low == "ndt qualifier":
        return "NDT-Qualifier"
    if low == "ndt":
        return "NDT"
    if low == "ada":
        return "ADA"
    if low == "nuso":
        return "NUSO"
    if low == "usna":
        return "Navy"

    return " ".join(w.capitalize() for w in low.split())

def extract_tournament_token(stem: str, exclude_qualifiers: bool = False) -> Optional[str]:
    parts = split_parts(stem)
    if len(parts) < 4:
        return None

    # Drop school + team code entirely, per user guidance.
    parts_wo_prefix = parts[2:]

    # Prefer "thing immediately before Round"
    round_idx = None
    for i, token in enumerate(parts_wo_prefix):
        if ROUND_TOKEN_RE.fullmatch(token):
            round_idx = i
            break

    candidate = None

    if round_idx is not None:
        # walk backwards from Round and take first plausible token
        for j in range(round_idx - 1, -1, -1):
            tok = parts_wo_prefix[j]
            low = tok.lower()
            if low in SIDE_TOKENS:
                continue
            if is_junk_token(tok):
                continue
            if ELIM_RE.search(tok):
                return None
            candidate = tok
            break
    else:
        # fallback: find side, then first plausible token after it
        side_idx = None
        for i, tok in enumerate(parts_wo_prefix):
            if tok.lower() in SIDE_TOKENS:
                side_idx = i
                break
        if side_idx is None:
            return None
        for tok in parts_wo_prefix[side_idx + 1:]:
            low = tok.lower()
            if low in SIDE_TOKENS:
                continue
            if is_junk_token(tok):
                continue
            if ELIM_RE.search(tok):
                return None
            candidate = tok
            break

    if not candidate:
        return None

    canon = canonicalize_tournament(candidate)
    if not canon:
        return None
    if exclude_qualifiers and canon.lower() == "ndt-qualifier":
        return None
    return canon

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
            if len(skipped_examples["elim"]) < 8:
                skipped_examples["elim"].append(path.name)
            continue

        tournament = extract_tournament_token(stem, exclude_qualifiers=args.exclude_qualifiers)
        if not tournament:
            if len(skipped_examples["bad_pattern_or_excluded"]) < 15:
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
