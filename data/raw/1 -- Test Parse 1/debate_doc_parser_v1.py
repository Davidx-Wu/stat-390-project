#!/usr/bin/env python3
"""
debate_doc_parser.py

Parse a single debate speech .docx into:
1) speech_summary.csv   - one-row summary for modeling
2) argument_audit.csv   - position/card-level audit trail for review

Designed for prelim speech docs where metadata is primarily in the filename and
win/loss is joined from a tournament CSV exported from Tabroom-like sheets.

Example:
    python debate_doc_parser.py \
        --doc "Michigan-BaPa-Neg-Georgetown-Round-8.docx" \
        --tournament-csv "Gonzaga_Tabroom-prelims_table.csv" \
        --outdir "./outputs" \
        --strict

Dependencies:
    pip install python-docx pandas
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Tuple, Dict

import pandas as pd
from docx import Document


# ----------------------------
# Config and regexes
# ----------------------------

CARD_START_RE = re.compile(
    r"""^
    [A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ.\-,'&/ ]{1,80}     # author chunk
    \s*[’']\d{2}\b                                  # apostrophe year
    """,
    re.VERBOSE,
)

ROUND_NUM_RE = re.compile(r"round[-_ ]?(\d+)", re.I)
SIDE_RE = re.compile(r"\b(aff|neg)\b", re.I)

ADV_RE = re.compile(r"\badv(?:antage)?\b", re.I)
SOLVENCY_RE = re.compile(r"\bsolvency\b", re.I)
INHERENCY_RE = re.compile(r"\binherency\b", re.I)

# Broad neg off labels. These are intentionally inclusive because the user
# wants CP/T/K/etc. all counted as offs.
NEG_POSITION_HINT_RE = re.compile(
    r"""(?ix)
    \b(
        cp|counterplan|da|disad|disadvantage|kritik|k\b|topicality|t\b|
        theory|framework|fw|case|presumption|pic|perm|politics|tradeoff|
        turns?|impact\s+turn|link\s+turn|cap|states|consult|courts|
        elections|hegemony|economy|spending|process|agent
    )\b
    """
)

SPEECH_LABEL_RE = re.compile(r"^\s*(1ac|1nc|2ac|2nc|1ar|2ar|2nr)\s*$", re.I)


# ----------------------------
# Data classes
# ----------------------------

@dataclass
class FileMeta:
    source_file: str
    team_code_filename: Optional[str]
    side: Optional[str]
    opponent_filename: Optional[str]
    round_number: Optional[int]
    filename_parse_ok: bool
    filename_warning: str = ""

@dataclass
class TournamentRoundInfo:
    tournament_name: Optional[str]
    team_code_csv: Optional[str]
    round_number: Optional[int]
    win_loss: Optional[str]
    side_csv: Optional[str]
    opponent_csv: Optional[str]
    judge: Optional[str]
    join_ok: bool
    join_warning: str = ""

@dataclass
class PositionRecord:
    source_file: str
    team_code: Optional[str]
    round_number: Optional[int]
    side: Optional[str]
    position_order: int
    position_type: str
    position_title: str
    start_paragraph: int
    end_paragraph: int
    num_cards: int
    card_starts: str
    notes: str = ""

@dataclass
class SummaryRecord:
    source_file: str
    team_code: Optional[str]
    tournament_name: Optional[str]
    round_number: Optional[int]
    side: Optional[str]
    opponent: Optional[str]
    win_loss: Optional[str]
    judge: Optional[str]
    num_positions: int
    num_adv_inh_solv: int
    num_offs: int
    num_cards_total: int
    parse_confidence: str
    warnings: str


# ----------------------------
# Text helpers
# ----------------------------

def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "’")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

def paragraphs_from_docx(docx_path: Path) -> List[Dict[str, str]]:
    doc = Document(str(docx_path))
    rows: List[Dict[str, str]] = []
    for i, p in enumerate(doc.paragraphs):
        text = clean_text(p.text)
        if not text:
            continue
        style_name = ""
        try:
            style_name = p.style.name if p.style else ""
        except Exception:
            style_name = ""
        rows.append({"idx": i, "text": text, "style": style_name})
    return rows


# ----------------------------
# Filename parsing
# ----------------------------

def short_code_variants_from_filename_token(token: Optional[str]) -> List[str]:
    """Return plausible short team-code variants from filename token.

    Examples:
        BaPa -> ["BaPa", "BP", "PB"]
        WR   -> ["WR", "RW"]
    """
    if not token:
        return []

    token = normalize_ws(token)
    variants: List[str] = []

    def add(val: Optional[str]) -> None:
        if val and val not in variants:
            variants.append(val)

    add(token)

    letters_only = re.sub(r"[^A-Za-z]", "", token)
    if letters_only:
        uppers = "".join(ch for ch in token if ch.isupper())
        if len(uppers) >= 2:
            initials = uppers
        else:
            chunks = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", letters_only)
            initials = "".join(chunk[0].upper() for chunk in chunks if chunk)
            if len(initials) < 2 and len(letters_only) >= 2:
                initials = letters_only[:2].upper()

        if initials:
            add(initials)
            if len(initials) == 2:
                add(initials[::-1])

    return variants


def parse_filename(docx_path: Path) -> FileMeta:
    stem = docx_path.stem
    parts = [p for p in re.split(r"[-_]+", stem) if p]

    side = None
    side_match = SIDE_RE.search(stem)
    if side_match:
        side = side_match.group(1).lower()

    round_number = None
    round_match = ROUND_NUM_RE.search(stem)
    if round_match:
        round_number = int(round_match.group(1))

    # Expected rough pattern from sample:
    # Michigan-BaPa-Neg-Georgetown-Round-8
    # [school]-[team]-[side]-[opponent]-Round-[n]
    team_code = None
    opponent = None
    warning_bits = []

    if len(parts) >= 4:
        # Use the second token as the short team code from filename, e.g. BaPa.
        team_code = parts[1]
        try:
            side_index = next(i for i, p in enumerate(parts) if p.lower() in {"aff", "neg"})
        except StopIteration:
            side_index = None
        if side_index is not None and side_index + 1 < len(parts):
            opponent = parts[side_index + 1]
    else:
        warning_bits.append("filename_too_short_for_expected_pattern")

    if side is None:
        warning_bits.append("missing_side_in_filename")
    if round_number is None:
        warning_bits.append("missing_numeric_round_in_filename")
    if team_code is None:
        warning_bits.append("missing_team_code_in_filename")
    if opponent is None:
        warning_bits.append("missing_opponent_in_filename")

    return FileMeta(
        source_file=docx_path.name,
        team_code_filename=team_code,
        side=side,
        opponent_filename=opponent,
        round_number=round_number,
        filename_parse_ok=len(warning_bits) == 0,
        filename_warning=";".join(warning_bits),
    )


# ----------------------------
# Tournament CSV parsing
# ----------------------------

def extract_tournament_name(csv_path: Path) -> str:
    name = csv_path.stem
    name = re.sub(r"[_-]*tabroom.*$", "", name, flags=re.I)
    name = name.replace("_", " ").replace("-", " ").strip()
    return name or csv_path.stem

def parse_entry_team_code(entry_text: str) -> Optional[str]:
    s = normalize_ws(entry_text)
    if not s:
        return None
    # Usually starts like "Michigan BP Barrett & Park ..."
    m = re.match(r"^([A-Za-z&.' ]+?)\s+([A-Z]{2})\b", s)
    if m:
        school = normalize_ws(m.group(1))
        code = m.group(2).upper()
        return f"{school} {code}"
    return None

def normalize_team_code_for_matching(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    s = normalize_ws(name)
    s = s.replace("University of ", "")
    s = re.sub(r"\bUniv\.?\b", "University", s, flags=re.I)
    return s.lower()

def parse_round_cell(cell_text: str) -> Dict[str, Optional[str]]:
    s = normalize_ws(cell_text)
    if not s:
        return {
            "win_loss": None,
            "side_csv": None,
            "opponent_csv": None,
            "judge": None,
        }

    # Example:
    # "W Neg 59.3 Gonzaga WR: Wellman & Roe Symonds, Adam Barrett Eleanor 29.6 ..."
    m = re.match(r"^(W|L)\s+(Aff|Neg)\s+[\d.]+\s+(.+)$", s, flags=re.I)
    if not m:
        return {
            "win_loss": None,
            "side_csv": None,
            "opponent_csv": None,
            "judge": None,
        }

    win_loss = m.group(1).upper()
    side_csv = m.group(2).lower()
    remainder = m.group(3)

    opponent_csv = None
    judge = None

    # Opponent is typically before colon, e.g. "Gonzaga WR: ..."
    left, sep, right = remainder.partition(":")
    if sep:
        opponent_csv = normalize_ws(left)
        # Judge is the first name-ish chunk after the colon and before speaker names/scores.
        # Conservative extraction: take first comma-containing name chunk if present.
        judge_match = re.search(r"\b([A-Z][A-Za-z' -]+,\s*[A-Z][A-Za-z' -]+)\b", right)
        if judge_match:
            judge = normalize_ws(judge_match.group(1))
        else:
            # Fallback: first 6 words after colon
            judge = " ".join(normalize_ws(right).split()[:6]) if right else None
    else:
        parts = remainder.split()
        opponent_csv = " ".join(parts[:2]) if len(parts) >= 2 else remainder

    return {
        "win_loss": win_loss,
        "side_csv": side_csv,
        "opponent_csv": opponent_csv,
        "judge": judge,
    }

def load_and_match_tournament_row(
    csv_path: Path,
    filename_team_code: Optional[str],
    round_number: Optional[int],
) -> TournamentRoundInfo:
    tournament_name = extract_tournament_name(csv_path)
    if filename_team_code is None or round_number is None:
        return TournamentRoundInfo(
            tournament_name=tournament_name,
            team_code_csv=None,
            round_number=round_number,
            win_loss=None,
            side_csv=None,
            opponent_csv=None,
            judge=None,
            join_ok=False,
            join_warning="missing_filename_team_or_round_for_join",
        )

    code_variants = short_code_variants_from_filename_token(filename_team_code)
    target_team_variants = set()
    for code in code_variants:
        target_team_variants.add(normalize_team_code_for_matching(f"Michigan {code}"))
        target_team_variants.add(normalize_team_code_for_matching(f"University of Michigan {code}"))
        target_team_variants.add(normalize_team_code_for_matching(code))

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    matched_row = None
    matched_team_code = None

    for _, row in df.iterrows():
        entry = row.get("Entry", "")
        entry_team = parse_entry_team_code(entry)
        norm_entry_team = normalize_team_code_for_matching(entry_team)
        if norm_entry_team in target_team_variants:
            matched_row = row
            matched_team_code = entry_team
            break

    if matched_row is None:
        return TournamentRoundInfo(
            tournament_name=tournament_name,
            team_code_csv=None,
            round_number=round_number,
            win_loss=None,
            side_csv=None,
            opponent_csv=None,
            judge=None,
            join_ok=False,
            join_warning="no_matching_team_row_in_tournament_csv",
        )

    round_col = f"R{round_number}"
    if round_col not in df.columns:
        return TournamentRoundInfo(
            tournament_name=tournament_name,
            team_code_csv=matched_team_code,
            round_number=round_number,
            win_loss=None,
            side_csv=None,
            opponent_csv=None,
            judge=None,
            join_ok=False,
            join_warning=f"missing_round_column_{round_col}",
        )

    parsed = parse_round_cell(matched_row.get(round_col, ""))

    join_ok = bool(parsed["win_loss"] and parsed["side_csv"])
    join_warning = ""
    if not join_ok:
        join_warning = f"could_not_parse_{round_col}_cell"

    return TournamentRoundInfo(
        tournament_name=tournament_name,
        team_code_csv=matched_team_code,
        round_number=round_number,
        win_loss=parsed["win_loss"],
        side_csv=parsed["side_csv"],
        opponent_csv=parsed["opponent_csv"],
        judge=parsed["judge"],
        join_ok=join_ok,
        join_warning=join_warning,
    )


# ----------------------------
# Speech parsing
# ----------------------------

def is_card_start(text: str) -> bool:
    return bool(CARD_START_RE.match(text))

def classify_aff_position_title(text: str) -> Optional[str]:
    if ADV_RE.search(text):
        return "advantage"
    if SOLVENCY_RE.search(text):
        return "solvency"
    if INHERENCY_RE.search(text):
        return "inherency"
    return None

def looks_like_heading(text: str, style: str) -> bool:
    t = clean_text(text)
    if not t:
        return False
    if SPEECH_LABEL_RE.match(t):
        return True
    if style and style.lower().startswith("heading"):
        return True
    if len(t) <= 80 and (
        t.isupper()
        or t.endswith(":")
        or "---" in t
        or NEG_POSITION_HINT_RE.search(t)
        or ADV_RE.search(t)
        or SOLVENCY_RE.search(t)
        or INHERENCY_RE.search(t)
    ):
        return True
    return False

def parse_aff_positions(paragraphs: List[Dict[str, str]]) -> List[PositionRecord]:
    positions: List[PositionRecord] = []
    current = None
    order = 0

    for row in paragraphs:
        idx, text, style = row["idx"], row["text"], row["style"]
        pos_type = classify_aff_position_title(text)

        if pos_type:
            if current is not None:
                current["end_paragraph"] = idx - 1
                positions.append(_finalize_position(current))
            order += 1
            current = {
                "position_order": order,
                "position_type": pos_type,
                "position_title": text,
                "start_paragraph": idx,
                "end_paragraph": idx,
                "card_starts": [],
                "notes": "",
            }
            continue

        if current is not None:
            current["end_paragraph"] = idx
            if is_card_start(text):
                current["card_starts"].append(text)

    return positions + ([_finalize_position(current)] if current is not None else [])

def parse_neg_positions(paragraphs: List[Dict[str, str]]) -> List[PositionRecord]:
    positions: List[PositionRecord] = []
    current = None
    order = 0
    seen_first_real_position = False

    for row in paragraphs:
        idx, text, style = row["idx"], row["text"], row["style"]
        lower = text.lower()

        if SPEECH_LABEL_RE.match(text):
            continue

        # Ignore generic "OFF" line. It is a section marker, not itself an off.
        if lower in {"off", "offs"}:
            continue

        headingish = looks_like_heading(text, style)
        strong_neg_label = bool(NEG_POSITION_HINT_RE.search(text)) or ("---" in text) or text.endswith(":")

        if headingish and strong_neg_label:
            # Prevent cite lines from being mis-read as headings.
            if is_card_start(text):
                pass
            else:
                if current is not None:
                    current["end_paragraph"] = idx - 1
                    positions.append(_finalize_position(current))
                order += 1
                current = {
                    "position_order": order,
                    "position_type": "off",
                    "position_title": text,
                    "start_paragraph": idx,
                    "end_paragraph": idx,
                    "card_starts": [],
                    "notes": "",
                }
                seen_first_real_position = True
                continue

        if current is not None:
            current["end_paragraph"] = idx
            if is_card_start(text):
                current["card_starts"].append(text)

    return positions + ([_finalize_position(current)] if current is not None else [])

def _finalize_position(current: Dict) -> PositionRecord:
    return PositionRecord(
        source_file="",
        team_code=None,
        round_number=None,
        side=None,
        position_order=current["position_order"],
        position_type=current["position_type"],
        position_title=current["position_title"],
        start_paragraph=current["start_paragraph"],
        end_paragraph=current["end_paragraph"],
        num_cards=len(current["card_starts"]),
        card_starts=" || ".join(current["card_starts"]),
        notes=current.get("notes", ""),
    )

def parse_positions(paragraphs: List[Dict[str, str]], side: str) -> List[PositionRecord]:
    if side == "aff":
        return parse_aff_positions(paragraphs)
    if side == "neg":
        return parse_neg_positions(paragraphs)
    return []


# ----------------------------
# Validation and output
# ----------------------------

def attach_metadata_to_positions(
    positions: List[PositionRecord],
    team_code: Optional[str],
    round_number: Optional[int],
    side: Optional[str],
    source_file: str,
) -> List[PositionRecord]:
    out = []
    for p in positions:
        p.source_file = source_file
        p.team_code = team_code
        p.round_number = round_number
        p.side = side
        out.append(p)
    return out

def make_summary(
    file_meta: FileMeta,
    round_info: Optional[TournamentRoundInfo],
    positions: List[PositionRecord],
) -> SummaryRecord:
    warnings = []

    team_code = None
    if round_info and round_info.team_code_csv:
        team_code = round_info.team_code_csv
    elif file_meta.team_code_filename:
        code_variants = short_code_variants_from_filename_token(file_meta.team_code_filename)
        best_code = code_variants[1] if len(code_variants) > 1 else code_variants[0]
        team_code = f"Michigan {best_code}"

    if not file_meta.filename_parse_ok:
        warnings.append(file_meta.filename_warning)

    if round_info and not round_info.join_ok:
        warnings.append(round_info.join_warning)

    if file_meta.side == "aff":
        num_adv_inh_solv = len(positions)
        num_offs = 0
    elif file_meta.side == "neg":
        num_adv_inh_solv = 0
        num_offs = len(positions)
    else:
        num_adv_inh_solv = 0
        num_offs = 0
        warnings.append("unknown_side")

    num_cards_total = sum(p.num_cards for p in positions)

    parse_confidence = "high"
    if warnings:
        parse_confidence = "low"
    elif num_cards_total == 0:
        parse_confidence = "medium"

    opponent = file_meta.opponent_filename
    if round_info and round_info.opponent_csv:
        opponent = round_info.opponent_csv

    return SummaryRecord(
        source_file=file_meta.source_file,
        team_code=team_code,
        tournament_name=round_info.tournament_name if round_info else None,
        round_number=file_meta.round_number,
        side=file_meta.side,
        opponent=opponent,
        win_loss=round_info.win_loss if round_info else None,
        judge=round_info.judge if round_info else None,
        num_positions=len(positions),
        num_adv_inh_solv=num_adv_inh_solv,
        num_offs=num_offs,
        num_cards_total=num_cards_total,
        parse_confidence=parse_confidence,
        warnings=";".join([w for w in warnings if w]),
    )

def strict_fail(summary: SummaryRecord, round_info: Optional[TournamentRoundInfo]) -> Tuple[bool, str]:
    if summary.round_number is None:
        return True, "strict_fail_missing_round"
    if summary.side not in {"aff", "neg"}:
        return True, "strict_fail_missing_side"
    if summary.team_code is None:
        return True, "strict_fail_missing_team_code"
    if round_info is None or not round_info.join_ok:
        return True, "strict_fail_tournament_join"
    if summary.win_loss not in {"W", "L"}:
        return True, "strict_fail_missing_win_loss"
    return False, ""

def write_csv(path: Path, rows: List[dict]) -> None:
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse one debate speech .docx into summary and audit CSVs.")
    parser.add_argument("--doc", required=True, help="Path to one .docx speech file")
    parser.add_argument("--tournament-csv", required=False, help="Path to tournament CSV with round outcomes")
    parser.add_argument("--outdir", required=False, default="parser_output", help="Output directory")
    parser.add_argument("--strict", action="store_true", help="Drop summary row if key fields cannot be matched confidently")
    return parser

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    docx_path = Path(args.doc)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not docx_path.exists():
        print(f"ERROR: doc file not found: {docx_path}", file=sys.stderr)
        return 1
    if docx_path.suffix.lower() != ".docx":
        print("ERROR: --doc must point to a .docx file", file=sys.stderr)
        return 1

    file_meta = parse_filename(docx_path)
    paragraphs = paragraphs_from_docx(docx_path)

    if file_meta.side not in {"aff", "neg"}:
        print("ERROR: could not determine aff/neg from filename", file=sys.stderr)
        return 1

    positions = parse_positions(paragraphs, file_meta.side)
    round_info = None

    if args.tournament_csv:
        csv_path = Path(args.tournament_csv)
        if not csv_path.exists():
            print(f"ERROR: tournament csv not found: {csv_path}", file=sys.stderr)
            return 1
        round_info = load_and_match_tournament_row(
            csv_path=csv_path,
            filename_team_code=file_meta.team_code_filename,
            round_number=file_meta.round_number,
        )

    team_code = None
    if round_info and round_info.team_code_csv:
        team_code = round_info.team_code_csv
    elif file_meta.team_code_filename:
        code_variants = short_code_variants_from_filename_token(file_meta.team_code_filename)
        best_code = code_variants[1] if len(code_variants) > 1 else code_variants[0]
        team_code = f"Michigan {best_code}"

    positions = attach_metadata_to_positions(
        positions=positions,
        team_code=team_code,
        round_number=file_meta.round_number,
        side=file_meta.side,
        source_file=file_meta.source_file,
    )

    summary = make_summary(file_meta=file_meta, round_info=round_info, positions=positions)

    should_drop = False
    drop_reason = ""
    if args.strict:
        should_drop, drop_reason = strict_fail(summary, round_info)
        if should_drop:
            summary.warnings = ";".join([x for x in [summary.warnings, drop_reason] if x])

    summary_rows = [] if should_drop else [asdict(summary)]
    audit_rows = [asdict(p) for p in positions]

    write_csv(outdir / "speech_summary.csv", summary_rows)
    write_csv(outdir / "argument_audit.csv", audit_rows)

    print("\nParse complete.")
    print(f"Doc: {docx_path.name}")
    print(f"Positions detected: {len(positions)}")
    print(f"Cards detected: {sum(p.num_cards for p in positions)}")
    print(f"Summary written: {outdir / 'speech_summary.csv'}")
    print(f"Audit written:   {outdir / 'argument_audit.csv'}")
    if args.strict and should_drop:
        print(f"STRICT MODE: summary row omitted because {drop_reason}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
