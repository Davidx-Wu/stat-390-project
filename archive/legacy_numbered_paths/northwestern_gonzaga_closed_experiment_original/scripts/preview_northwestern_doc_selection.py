#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_DIR = ROOT / "6 -- experiments" / "northwestern_gonzaga_closed_experiment"
NDT_ROOT = ROOT / "1 -- data" / "raw" / "8 -- Keep Only Tournament Docs" / "ndtceda25"
COUNTS_PATH = NDT_ROOT / "tournament_disclosure_counts.csv"
OUTPUT_PATH = EXPERIMENT_DIR / "diagnostics" / "northwestern_doc_selection_preview.csv"

TARGET_TOURNAMENT = "Northwestern"


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


def detect_team_code(path: Path) -> str:
    stem = path.stem
    parts = [part for part in stem.split("-") if part]
    if len(parts) < 2:
        return ""
    return parts[1]


def main() -> int:
    if not NDT_ROOT.exists():
        raise SystemExit(f"NDT root not found: {NDT_ROOT}")
    if not COUNTS_PATH.exists():
        raise SystemExit(f"Counts file not found: {COUNTS_PATH}")

    counts = pd.read_csv(COUNTS_PATH)
    row = counts[counts["tournament"].astype(str).str.lower() == TARGET_TOURNAMENT.lower()]
    expected_count = int(row.iloc[0]["count"]) if not row.empty else None

    selected_rows = []
    rejected_northwestern_rows = []

    for path in sorted(NDT_ROOT.rglob("*.docx")):
        rel = path.relative_to(NDT_ROOT)
        school_folder = rel.parts[0] if rel.parts else ""
        stem = path.stem
        tournament = None if is_elim_filename(stem) else extract_tournament_token(stem)

        if tournament == TARGET_TOURNAMENT:
            selected_rows.append(
                {
                    "selected_file_path": str(rel),
                    "detected_tournament_label": tournament,
                    "detected_school_folder": school_folder,
                    "detected_team_code": detect_team_code(path),
                    "reason_selected": "matched tournament token using tournament_disclosure_counts logic",
                }
            )
        elif "northwestern" in str(rel).lower():
            reason = "rejected: path contains Northwestern but tournament token did not match"
            if school_folder.lower() == "northwestern":
                reason = "rejected: Northwestern appears as school folder, not tournament token"
            if is_elim_filename(stem):
                reason = "rejected: elimination-round filename"
            rejected_northwestern_rows.append(
                {
                    "selected_file_path": str(rel),
                    "detected_tournament_label": tournament or "",
                    "detected_school_folder": school_folder,
                    "detected_team_code": detect_team_code(path),
                    "reason_selected": reason,
                }
            )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(selected_rows).to_csv(OUTPUT_PATH, index=False)

    print(f"Counts file: {COUNTS_PATH}")
    print(f"Northwestern count row expected docs: {expected_count}")
    print(f"Total selected Northwestern tournament docs: {len(selected_rows)}")
    print(f"Preview written to: {OUTPUT_PATH}")
    print()
    print("First 20 selected paths:")
    for row_data in selected_rows[:20]:
        print(f"- {row_data['selected_file_path']}")
    print()
    print('First 20 rejected paths containing "Northwestern":')
    for row_data in rejected_northwestern_rows[:20]:
        print(f"- {row_data['selected_file_path']} | {row_data['reason_selected']}")

    if expected_count is not None and len(selected_rows) != expected_count:
        print()
        print(
            "WARNING: selected count does not match tournament_disclosure_counts.csv "
            f"({len(selected_rows)} != {expected_count})"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
