#!/usr/bin/env python3
"""
debate_doc_parser.py

Parse a single debate speech .docx into:
1) speech_summary.csv   - one-row summary for modeling
2) argument_audit.csv  - one row per detected position/off/advantage
3) card_audit.csv      - one row per detected card with full text + highlighted text

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
from typing import Dict, List, Optional, Tuple

import pandas as pd
from docx import Document


CARD_START_RE = re.compile(
    r"""^
    [A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ.\-,'&/ ]{1,120}
    \s*[’'](?:\d{1,2}-)?\d{2}\b
    """,
    re.VERBOSE,
)
ROUND_NUM_RE = re.compile(r"round[-_ ]?(\d+)", re.I)
SIDE_RE = re.compile(r"\b(aff|neg)\b", re.I)
SPEECH_LABEL_RE = re.compile(r"^\s*(1ac|1nc|2ac|2nc|1ar|2ar|2nr)\s*$", re.I)


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
    num_cards_with_highlight: int
    total_highlighted_words: int
    parse_confidence: str
    warnings: str


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
    num_cards_with_highlight: int
    position_word_count: int
    highlighted_word_count: int
    card_starts: str
    position_text_excerpt: str
    highlighted_text_excerpt: str
    notes: str = ""


@dataclass
class CardRecord:
    source_file: str
    team_code: Optional[str]
    round_number: Optional[int]
    side: Optional[str]
    position_order: int
    position_title: str
    card_order: int
    start_paragraph: int
    end_paragraph: int
    tagline_text: str
    cite_line: str
    card_text: str
    highlighted_text: str
    underlined_text: str
    read_proxy_text: str
    card_word_count: int
    highlighted_word_count: int


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2014", "-").replace("\u2013", "-")
    text = text.replace("\u2018", "'").replace("\u2019", "’")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def safe_excerpt(text: str, n: int = 300) -> str:
    text = normalize_ws(text)
    return text if len(text) <= n else text[: n - 3] + "..."


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def derive_team_code_variants(raw: str) -> List[str]:
    raw = normalize_ws(raw)
    variants = {raw}
    letters = "".join(ch for ch in raw if ch.isalpha())
    if letters:
        variants.add(letters)
        initials = "".join(ch.upper() for ch in raw if ch.isupper())
        if len(initials) >= 2:
            variants.add(initials)
            variants.add(initials[::-1])
        if len(letters) >= 2:
            variants.add((letters[0] + letters[-1]).upper())
            variants.add((letters[-1] + letters[0]).upper())
    return [v for v in variants if v]


def paragraphs_from_docx(docx_path: Path) -> List[Dict[str, str]]:
    doc = Document(str(docx_path))
    rows: List[Dict[str, str]] = []
    for i, p in enumerate(doc.paragraphs):
        full_text = clean_text(p.text)
        if not full_text:
            continue
        style_name = ""
        try:
            style_name = p.style.name if p.style else ""
        except Exception:
            style_name = ""

        highlighted_bits: List[str] = []
        underlined_bits: List[str] = []
        for run in p.runs:
            run_text = clean_text(run.text)
            if not run_text:
                continue
            if run.font.highlight_color is not None:
                highlighted_bits.append(run_text)
            if bool(run.underline):
                underlined_bits.append(run_text)

        rows.append(
            {
                "idx": i,
                "text": full_text,
                "style": style_name,
                "highlighted_text": normalize_ws(" ".join(highlighted_bits)),
                "underlined_text": normalize_ws(" ".join(underlined_bits)),
            }
        )
    return rows


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

    team_code = None
    opponent = None
    warning_bits = []

    if len(parts) >= 4:
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


def extract_tournament_name(csv_path: Path) -> str:
    name = csv_path.stem
    name = re.sub(r"[_-]*tabroom.*$", "", name, flags=re.I)
    return name.replace("_", " ").replace("-", " ").strip() or csv_path.stem


def parse_entry_team_code(entry_text: str) -> Optional[str]:
    s = normalize_ws(entry_text)
    if not s:
        return None
    m = re.match(r"^([A-Za-z&.' ]+?)\s+([A-Z]{2})\b", s)
    if m:
        school = normalize_ws(m.group(1))
        code = m.group(2).upper()
        return f"{school} {code}"
    return None


def normalize_team_code_for_matching(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    return normalize_ws(name).replace("University of ", "").lower()


def parse_round_cell(cell_text: str) -> Dict[str, Optional[str]]:
    s = normalize_ws(cell_text)
    if not s:
        return {"win_loss": None, "side_csv": None, "opponent_csv": None, "judge": None}

    m = re.match(r"^(W|L)\s+(Aff|Neg)\s+[\d.]+\s+(.+)$", s, flags=re.I)
    if not m:
        return {"win_loss": None, "side_csv": None, "opponent_csv": None, "judge": None}

    win_loss = m.group(1).upper()
    side_csv = m.group(2).lower()
    remainder = m.group(3)

    opponent_csv = None
    judge = None
    left, sep, right = remainder.partition(":")
    if sep:
        opponent_csv = normalize_ws(left)
        judge_match = re.search(r"\b([A-Z][A-Za-z' -]+,\s*[A-Z][A-Za-z' -]+)\b", right)
        if judge_match:
            judge = normalize_ws(judge_match.group(1))
        else:
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

    target_variants = set()
    for variant in derive_team_code_variants(filename_team_code):
        target_variants.add(normalize_team_code_for_matching(f"Michigan {variant}"))
        target_variants.add(normalize_team_code_for_matching(f"University of Michigan {variant}"))
        target_variants.add(normalize_team_code_for_matching(variant))

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    matched_row = None
    matched_team_code = None
    for _, row in df.iterrows():
        entry_team = parse_entry_team_code(row.get("Entry", ""))
        if normalize_team_code_for_matching(entry_team) in target_variants:
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
    return TournamentRoundInfo(
        tournament_name=tournament_name,
        team_code_csv=matched_team_code,
        round_number=round_number,
        win_loss=parsed["win_loss"],
        side_csv=parsed["side_csv"],
        opponent_csv=parsed["opponent_csv"],
        judge=parsed["judge"],
        join_ok=join_ok,
        join_warning="" if join_ok else f"could_not_parse_{round_col}_cell",
    )


def is_card_start(text: str) -> bool:
    return bool(CARD_START_RE.match(clean_text(text)))


def is_short_heading_candidate(text: str) -> bool:
    return len(clean_text(text)) <= 140


def is_generic_scaffolding_line(text: str) -> bool:
    t = clean_text(text).lower()
    return t in {"off", "offs", "on", "1nc", "2nc", "1ac", "2ac", "1ar", "2ar", "2nr", "block", "blocks"}


def is_round_title_line(text: str) -> bool:
    t = clean_text(text).lower()
    return bool(re.search(r"\bround\s*\d+\b", t) and re.search(r"\b(1ac|1nc|2ac|2nc|1ar|2ar|2nr)\b", t))


def is_aff_position_header(text: str, style: str) -> Optional[str]:
    t = clean_text(text)
    low = t.lower()
    if not is_short_heading_candidate(t):
        return None
    if is_generic_scaffolding_line(t) or is_round_title_line(t):
        return None
    if re.match(r"^(adv(?:antage)?)(\s+\w+)?\s*[:\-]", low):
        return "advantage"
    if re.match(r"^adv\s*---", low):
        return "advantage"
    if re.fullmatch(r"solvency(:.*|---.*)?", low):
        return "solvency"
    if re.fullmatch(r"inherency(:.*|---.*)?", low):
        return "inherency"
    if style and style.lower().startswith("heading"):
        if "adv" in low:
            return "advantage"
        if "solvency" in low:
            return "solvency"
        if "inherency" in low:
            return "inherency"
    return None


def is_neg_case_boundary(text: str) -> bool:
    low = clean_text(text).lower()
    return bool(re.match(r"^adv\s*---", low) or re.match(r"^advantage(\s+\w+)?\s*[:\-]", low))


def is_neg_subpoint_line(text: str) -> bool:
    t = clean_text(text)
    low = t.lower()
    if not t:
        return False
    if t.startswith("---"):
        return True
    if "2nc" in low or "1nr" in low or "2nr" in low:
        return True
    if re.match(r"^(perm|link|impact|internal|uq|uniqueness|answers?|at:|overview|kick|solvency|adv|advantage|inherency)\b", low):
        return True
    if re.match(r"^\d+\.", low):
        return True
    return False


def is_plan_text_line(text: str) -> bool:
    low = clean_text(text).lower()
    return bool(
        re.match(
            r"^(the united states|the united states federal government|the united states executive|the united states federal judiciary|the fifty states|the national labor relations board|the european union)\b",
            low,
        )
    )


def is_explicit_neg_shell_title(text: str) -> bool:
    t = clean_text(text)
    low = t.lower()
    if not is_short_heading_candidate(t):
        return False
    if is_generic_scaffolding_line(t) or is_round_title_line(t):
        return False
    if is_neg_subpoint_line(t):
        return False
    if re.search(r"\b(counterplan|cp|disadvantage|da|kritik|topicality|pic)\b", low):
        return True
    if re.fullmatch(r"[A-Za-z0-9 /&+\-]{1,50}\s+k:?", t, flags=re.I):
        return True
    if re.fullmatch(r"(theory|framework|fw)(:.*|---.*)?", low):
        return True
    if re.fullmatch(r"(cp|da|pic|k|t|fw|theory)\s*---\s*.+", low):
        return True
    if len(t) <= 55 and re.search(r"\b(cp|da|k|pic|topicality|theory|framework|fw)\b", low):
        return True
    return False


def looks_like_long_off_claim(text: str) -> bool:
    t = clean_text(text)
    low = t.lower()
    if len(t) < 35 or len(t) > 180:
        return False
    if is_card_start(t) or is_plan_text_line(t) or is_round_title_line(t):
        return False
    if "2nc" in low or "1nr" in low or "2nr" in low:
        return False
    if ":" in t:
        return False
    return bool(re.search(r"\b(judicial|labor|doctrine|rights|capital|flight|permitting|mqd|unionization|congress|extinction|inequality|monopsony|preemption)\b", low))


def parse_aff_positions(paragraphs: List[Dict[str, str]]) -> List[Dict]:
    positions: List[Dict] = []
    current = None
    order = 0
    for row in paragraphs:
        idx, text, style = row["idx"], row["text"], row["style"]
        pos_type = is_aff_position_header(text, style)
        if pos_type:
            if current is not None:
                current["end_paragraph"] = idx - 1
                positions.append(current)
            order += 1
            current = {
                "position_order": order,
                "position_type": pos_type,
                "position_title": text,
                "start_paragraph": idx,
                "end_paragraph": idx,
                "notes": "",
            }
        elif current is not None:
            current["end_paragraph"] = idx
    if current is not None:
        positions.append(current)
    return positions


def parse_neg_positions(paragraphs: List[Dict[str, str]]) -> List[Dict]:
    positions: List[Dict] = []
    current = None
    order = 0
    prev_low = ""
    for row in paragraphs:
        idx, text, style = row["idx"], row["text"], row["style"]
        low = clean_text(text).lower()
        if is_round_title_line(text) or SPEECH_LABEL_RE.match(text) or low in {"off", "offs"}:
            prev_low = low
            continue
        if is_neg_case_boundary(text):
            if current is not None:
                current["end_paragraph"] = idx - 1
                positions.append(current)
            break

        start_new = False
        notes = ""
        if is_explicit_neg_shell_title(text):
            start_new = True
        elif prev_low == "1nc":
            if is_plan_text_line(text):
                start_new = True
                notes = "started_after_1nc_from_plan_text"
            elif looks_like_long_off_claim(text):
                start_new = True
                notes = "started_after_1nc_from_long_claim"

        if start_new:
            if current is not None:
                current["end_paragraph"] = idx - 1
                positions.append(current)
            order += 1
            current = {
                "position_order": order,
                "position_type": "off",
                "position_title": text,
                "start_paragraph": idx,
                "end_paragraph": idx,
                "notes": notes,
            }
        elif current is not None:
            current["end_paragraph"] = idx
        prev_low = low

    if current is not None and (not positions or positions[-1] is not current):
        positions.append(current)
    return positions


def parse_positions(paragraphs: List[Dict[str, str]], side: str) -> List[Dict]:
    if side == "aff":
        return parse_aff_positions(paragraphs)
    if side == "neg":
        return parse_neg_positions(paragraphs)
    return []


def looks_like_tagline(text: str) -> bool:
    t = clean_text(text)
    low = t.lower()
    if not t:
        return False
    if is_card_start(t):
        return False
    if is_generic_scaffolding_line(t) or is_round_title_line(t):
        return False
    if SPEECH_LABEL_RE.match(t):
        return False
    if is_explicit_neg_shell_title(t) or is_neg_case_boundary(t):
        return False
    if is_aff_position_header(t, "") is not None:
        return False
    if t.startswith("---"):
        return False
    if is_plan_text_line(t):
        return False
    # sentence-like or tag-like line, shorter than evidence paragraph
    if len(t) > 220:
        return False
    if ":" in t and len(t) < 35:
        return False
    return True


def build_cards_for_position(position: Dict, paragraphs: List[Dict[str, str]]) -> List[Dict]:
    start = position["start_paragraph"]
    end = position["end_paragraph"]
    pos_paras = [p for p in paragraphs if start <= p["idx"] <= end]

    cite_indices = [i for i, p in enumerate(pos_paras) if is_card_start(p["text"])]
    cards: List[Dict] = []
    if not cite_indices:
        return cards

    for card_order, cite_rel_idx in enumerate(cite_indices, start=1):
        tagline_text = ""
        chunk_start = cite_rel_idx

        # Attach the immediately preceding tagline if present.
        prev_idx = cite_rel_idx - 1
        if prev_idx >= 0:
            prev_text = pos_paras[prev_idx]["text"]
            if looks_like_tagline(prev_text):
                tagline_text = prev_text
                chunk_start = prev_idx

        rel_end = (cite_indices[card_order] - 1) if card_order < len(cite_indices) else (len(pos_paras) - 1)
        chunk = pos_paras[chunk_start : rel_end + 1]
        cite_line = pos_paras[cite_rel_idx]["text"]
        card_text = normalize_ws(" ".join(p["text"] for p in chunk))
        highlighted_text = normalize_ws(" ".join(p["highlighted_text"] for p in chunk if p["highlighted_text"]))
        underlined_text = normalize_ws(" ".join(p["underlined_text"] for p in chunk if p["underlined_text"]))
        read_proxy_text = highlighted_text or underlined_text

        cards.append(
            {
                "card_order": card_order,
                "start_paragraph": chunk[0]["idx"],
                "end_paragraph": chunk[-1]["idx"],
                "tagline_text": tagline_text,
                "cite_line": cite_line,
                "card_text": card_text,
                "highlighted_text": highlighted_text,
                "underlined_text": underlined_text,
                "read_proxy_text": read_proxy_text,
                "card_word_count": word_count(card_text),
                "highlighted_word_count": word_count(read_proxy_text),
            }
        )
    return cards


def build_argument_and_card_rows(
    positions: List[Dict],
    paragraphs: List[Dict[str, str]],
    team_code: Optional[str],
    round_number: Optional[int],
    side: Optional[str],
    source_file: str,
) -> Tuple[List[PositionRecord], List[CardRecord]]:
    argument_rows: List[PositionRecord] = []
    card_rows: List[CardRecord] = []

    for position in positions:
        cards = build_cards_for_position(position, paragraphs)
        start = position["start_paragraph"]
        end = position["end_paragraph"]
        pos_paras = [p for p in paragraphs if start <= p["idx"] <= end]
        position_text = normalize_ws(" ".join(p["text"] for p in pos_paras))
        highlighted_position_text = normalize_ws(
            " ".join((p["highlighted_text"] or p["underlined_text"]) for p in pos_paras if p["highlighted_text"] or p["underlined_text"])
        )

        argument_rows.append(
            PositionRecord(
                source_file=source_file,
                team_code=team_code,
                round_number=round_number,
                side=side,
                position_order=position["position_order"],
                position_type=position["position_type"],
                position_title=position["position_title"],
                start_paragraph=start,
                end_paragraph=end,
                num_cards=len(cards),
                num_cards_with_highlight=sum(1 for c in cards if c["read_proxy_text"]),
                position_word_count=word_count(position_text),
                highlighted_word_count=word_count(highlighted_position_text),
                card_starts=" || ".join(c["cite_line"] for c in cards),
                position_text_excerpt=safe_excerpt(position_text, 350),
                highlighted_text_excerpt=safe_excerpt(highlighted_position_text, 350),
                notes=position.get("notes", ""),
            )
        )

        for card in cards:
            card_rows.append(
                CardRecord(
                    source_file=source_file,
                    team_code=team_code,
                    round_number=round_number,
                    side=side,
                    position_order=position["position_order"],
                    position_title=position["position_title"],
                    card_order=card["card_order"],
                    start_paragraph=card["start_paragraph"],
                    end_paragraph=card["end_paragraph"],
                    tagline_text=card["tagline_text"],
                    cite_line=card["cite_line"],
                    card_text=card["card_text"],
                    highlighted_text=card["highlighted_text"],
                    underlined_text=card["underlined_text"],
                    read_proxy_text=card["read_proxy_text"],
                    card_word_count=card["card_word_count"],
                    highlighted_word_count=card["highlighted_word_count"],
                )
            )

    return argument_rows, card_rows


def make_summary(
    file_meta: FileMeta,
    round_info: Optional[TournamentRoundInfo],
    argument_rows: List[PositionRecord],
    card_rows: List[CardRecord],
) -> SummaryRecord:
    warnings = []
    team_code = None
    if round_info and round_info.team_code_csv:
        team_code = round_info.team_code_csv
    elif file_meta.team_code_filename:
        preferred = next((v for v in derive_team_code_variants(file_meta.team_code_filename) if len(v) == 2 and v.isupper()), file_meta.team_code_filename)
        team_code = f"Michigan {preferred}"

    if not file_meta.filename_parse_ok:
        warnings.append(file_meta.filename_warning)
    if round_info and not round_info.join_ok:
        warnings.append(round_info.join_warning)

    if file_meta.side == "aff":
        num_adv_inh_solv = len(argument_rows)
        num_offs = 0
    elif file_meta.side == "neg":
        num_adv_inh_solv = 0
        num_offs = len(argument_rows)
    else:
        num_adv_inh_solv = 0
        num_offs = 0
        warnings.append("unknown_side")

    parse_confidence = "high"
    if warnings:
        parse_confidence = "low"
    elif not card_rows:
        parse_confidence = "medium"

    opponent = round_info.opponent_csv if round_info and round_info.opponent_csv else file_meta.opponent_filename

    return SummaryRecord(
        source_file=file_meta.source_file,
        team_code=team_code,
        tournament_name=round_info.tournament_name if round_info else None,
        round_number=file_meta.round_number,
        side=file_meta.side,
        opponent=opponent,
        win_loss=round_info.win_loss if round_info else None,
        judge=round_info.judge if round_info else None,
        num_positions=len(argument_rows),
        num_adv_inh_solv=num_adv_inh_solv,
        num_offs=num_offs,
        num_cards_total=len(card_rows),
        num_cards_with_highlight=sum(1 for c in card_rows if c.read_proxy_text),
        total_highlighted_words=sum(c.highlighted_word_count for c in card_rows),
        parse_confidence=parse_confidence,
        warnings=";".join(w for w in warnings if w),
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
    pd.DataFrame(rows).to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse one debate speech .docx into summary and audit CSVs.")
    parser.add_argument("--doc", required=True, help="Path to one .docx speech file")
    parser.add_argument("--tournament-csv", required=False, help="Path to tournament CSV with round outcomes")
    parser.add_argument("--outdir", default="parser_output", help="Output directory")
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
        round_info = load_and_match_tournament_row(csv_path, file_meta.team_code_filename, file_meta.round_number)

    team_code = None
    if round_info and round_info.team_code_csv:
        team_code = round_info.team_code_csv
    elif file_meta.team_code_filename:
        preferred = next((v for v in derive_team_code_variants(file_meta.team_code_filename) if len(v) == 2 and v.isupper()), file_meta.team_code_filename)
        team_code = f"Michigan {preferred}"

    argument_rows, card_rows = build_argument_and_card_rows(
        positions, paragraphs, team_code, file_meta.round_number, file_meta.side, file_meta.source_file
    )
    summary = make_summary(file_meta, round_info, argument_rows, card_rows)

    should_drop = False
    drop_reason = ""
    if args.strict:
        should_drop, drop_reason = strict_fail(summary, round_info)
        if should_drop:
            summary.warnings = ";".join(x for x in [summary.warnings, drop_reason] if x)

    write_csv(outdir / "speech_summary.csv", [] if should_drop else [asdict(summary)])
    write_csv(outdir / "argument_audit.csv", [asdict(r) for r in argument_rows])
    write_csv(outdir / "card_audit.csv", [asdict(r) for r in card_rows])

    print("Parse complete.")
    print(f"Doc: {docx_path.name}")
    print(f"Positions detected: {len(argument_rows)}")
    print(f"Cards detected: {len(card_rows)}")
    print(f"Cards with highlighted/underlined read proxy: {sum(1 for c in card_rows if c.read_proxy_text)}")
    if args.strict and should_drop:
        print(f"STRICT MODE: summary row omitted because {drop_reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
