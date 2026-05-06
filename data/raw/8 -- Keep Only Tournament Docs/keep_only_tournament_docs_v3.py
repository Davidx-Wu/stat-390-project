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
    for raw in PARENS_RE.findall(stem):
        candidate = canonicalize_tournament(raw.replace("-", " "))
        if not candidate:
            continue
        if is_junk_token(candidate):
            continue
        return candidate
    return None

def extract_tournament_token(stem: str, exclude_qualifiers: bool = False) -> Optional[str]:
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

        if low == "ndt" and i + 1 < len(tokens) and tokens[i + 1].lower() == "qualifier":
            candidate = "NDT-Qualifier"
            if exclude_qualifiers:
                return None
            return candidate

        candidate = canonicalize_tournament(token)
        if exclude_qualifiers and QUALIFIER_RE.search(candidate):
            return None
        return candidate

    return None

def main() -> int:
    parser = argparse.ArgumentParser(description="Copy only docs from a chosen prelim tournament.")
    parser.add_argument("--root", required=True, help="Path to ndtceda25")
    parser.add_argument("--tournament", required=True, help="Tournament token to keep, e.g. Georgetown")
    parser.add_argument("--dest", default=None, help="Destination folder")
    parser.add_argument("--exclude-qualifiers", action="store_true", help="Exclude qualifier tournaments such as NDT-Qualifier")
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
    skipped_bad_pattern = 0

    for path in root.rglob("*.docx"):
        stem = path.stem

        if is_elim_filename(stem):
            skipped_elims += 1
            continue

        tournament = extract_tournament_token(stem, exclude_qualifiers=args.exclude_qualifiers)
        if not tournament:
            skipped_bad_pattern += 1
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
    print(f"Skipped bad-pattern/excluded docs: {skipped_bad_pattern}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
