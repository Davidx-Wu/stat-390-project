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

ROUND_TOKEN_RE = re.compile(r"^round$", re.I)
ROUND_NUM_RE = re.compile(r"^\d+\.?$")
SIDE_TOKENS = {"aff", "neg"}

STOPWORDS = {
    "round", "rd", "r", "prelim", "prelims", "1ac", "1nc", "2ac", "2nc", "1ar", "2ar", "2nr",
    "doc", "speech", "updated", "new", "redo", "copy", "operation", "zoomtown", "op",
    "college", "tournament", "debate", "debates", "annual", "memorial", "invitational",
    "open", "varsity", "novice", "jv", "swing", "online", "virtual"
}

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
    low = re.sub(r"\bcollege tournament\b", "", low)
    low = re.sub(r"\btournament\b", "", low)
    low = re.sub(r"\bdebates?\b", "", low)
    low = re.sub(r"\bannual\b", "", low)
    low = re.sub(r"\binvitational\b", "", low)
    low = re.sub(r"\s+", " ", low).strip(" -.")

    if low in ALIASES:
        return ALIASES[low]
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

    parts_wo_prefix = parts[2:]
    round_idx = None
    for i, token in enumerate(parts_wo_prefix):
        if ROUND_TOKEN_RE.fullmatch(token):
            round_idx = i
            break

    candidate = None
    if round_idx is not None:
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

def main() -> int:
    parser = argparse.ArgumentParser(description="Copy only docs from a chosen prelim tournament.")
    parser.add_argument("--root", required=True, help="Path to ndtceda25")
    parser.add_argument("--tournament", required=True, help="Tournament token to keep")
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
