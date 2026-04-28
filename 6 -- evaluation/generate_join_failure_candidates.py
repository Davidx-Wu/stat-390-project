#!/usr/bin/env python3
"""
One-off diagnostic: Tabroom join failures -> join_failure_candidates.csv
Imports parser module without modifying it.
"""

from __future__ import annotations

import csv
import difflib
import importlib.util
import re
import sys
from pathlib import Path

import pandas as pd


def load_parser(repo_root: Path):
    path = repo_root / "3 -- src" / "1 -- debate_doc_parser_vF.py"
    name = "debate_parser_diag"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def filename_parts_from_stem(stem: str) -> tuple[str, str | None]:
    """Mirror parse_filename split for school (parts[0]) and team token (parts[1])."""
    parts = [p for p in re.split(r"[-_]+", stem) if p]
    school = parts[0] if parts else ""
    team = parts[1] if len(parts) >= 4 else None
    return school, team


def build_target_variants(dp, filename_team_code: str | None) -> set[str | None]:
    if not filename_team_code:
        return set()
    out: set[str | None] = set()
    for variant in dp.derive_team_code_variants(filename_team_code):
        out.add(dp.normalize_team_code_for_matching(f"Michigan {variant}"))
        out.add(dp.normalize_team_code_for_matching(f"University of Michigan {variant}"))
        out.add(dp.normalize_team_code_for_matching(variant))
    return out


def filename_school_display(part0: str) -> str:
    if not part0:
        return ""
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", part0)


def entry_school_from_team(entry_team: str | None) -> str:
    if not entry_team:
        return ""
    m = re.match(r"^(.+?)\s+[A-Z]{2}$", entry_team.strip())
    return m.group(1).strip().lower() if m else entry_team.strip().lower()


def school_prefix_aligns(filename_school_part0: str, candidate_entry_raw: str, dp) -> bool:
    """Loose check: CamelCase folder slug vs school substring of Tabroom Entry."""
    slug = re.sub(r"[^a-z0-9]", "", filename_school_display(filename_school_part0).lower())
    if len(slug) < 3:
        return False
    et = dp.parse_entry_team_code(candidate_entry_raw or "")
    if not et:
        return False
    sch = entry_school_from_team(et)
    ent_c = re.sub(r"[^a-z0-9]", "", sch)
    if not ent_c:
        return False
    return slug in ent_c or ent_c in slug or ent_c.startswith(slug[: min(5, len(slug))])


def top_fuzzy_candidates(
    variants: set[str | None],
    entry_rows: list[tuple[str, str | None, str | None]],
    filename_school_part0: str,
    k: int = 8,
) -> list[tuple[float, float, str, str | None]]:
    """
    Rank Tabroom rows by blended score:
    - max difflib ratio of any target_variant vs normalized entry team code
    - bonus when filename school slug (CamelCase -> words, alphanumeric) appears in raw Entry
    Short tokens (e.g. 'ad') otherwise tie many Michigan teams at ~0.91; the bonus surfaces same-school rows.
    """
    var_list = [v for v in variants if v]
    if not var_list:
        return []
    slug = re.sub(r"[^a-z0-9]", "", filename_school_display(filename_school_part0).lower())
    scored: list[tuple[float, float, float, str, str | None]] = []
    for raw, et, en in entry_rows:
        if not en:
            continue
        mx = max(difflib.SequenceMatcher(None, v, en).ratio() for v in var_list)
        # Match filename school slug only against the *entry team's school* (not opponent text in the cell).
        sch = entry_school_from_team(et)
        school_c = re.sub(r"[^a-z0-9]", "", sch)
        school_hit = (
            1.0
            if (len(slug) >= 4 and slug in school_c)
            else (0.5 if (len(slug) >= 3 and slug in school_c) else 0.0)
        )
        combined = mx + 0.15 * school_hit
        scored.append((combined, mx, school_hit, raw, et))
    # Prefer rows whose Entry text contains the filename school slug, then variant score.
    scored.sort(key=lambda t: (t[2], t[1], t[0]), reverse=True)
    out: list[tuple[float, float, str, str | None]] = []
    seen: set[str] = set()
    for combined, mx, _sh, raw, et in scored:
        key = (et or raw)[:220]
        if key in seen:
            continue
        seen.add(key)
        out.append((combined, mx, raw, et))
        if len(out) >= k:
            break
    return out


def suggested_match(
    best_variant_score: float,
    best_raw: str,
    best_team: str | None,
    filename_school: str,
    same_prefix: bool,
) -> str:
    if best_team is None:
        return ""
    if best_variant_score >= 0.90 and same_prefix:
        return best_team
    if best_variant_score >= 0.88 and same_prefix:
        return f"{best_team} (review)"
    if best_variant_score >= 0.92:
        return f"{best_team} (review: fuzzy only)"
    # Same Tabroom school as folder name, but initials/token did not hit parser target set.
    if same_prefix and best_variant_score >= 0.33:
        return f"{best_team} (review: same-school row; token score {best_variant_score:.2f})"
    return ""


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    dp = load_parser(repo)

    failed_list = repo / "4 -- results" / "1 -- Baseline Model" / "failed_files.txt"
    tab_csv = repo / "1 -- data" / "raw" / "9 -- Build Gonzaga Dataset" / "Gonzaga_Tabroom-prelims_table.csv"
    base_docs = repo / "1 -- data" / "raw" / "9 -- Build Gonzaga Dataset"
    out_csv = repo / "4 -- results" / "1 -- Baseline Model" / "join_failure_candidates.csv"

    lines = [ln.strip() for ln in failed_list.read_text(encoding="utf-8").splitlines() if ln.strip()]
    df = pd.read_csv(tab_csv, dtype=str).fillna("")
    entry_rows: list[tuple[str, str | None, str | None]] = []
    for _, row in df.iterrows():
        raw = str(row.get("Entry", ""))
        et = dp.parse_entry_team_code(raw)
        en = dp.normalize_team_code_for_matching(et)
        entry_rows.append((raw, et, en))

    fieldnames = [
        "source_file",
        "parsed_school_from_filename",
        "parsed_team_code_from_filename",
        "all_target_variants",
        "closest_tabroom_entry_candidates_fuzzy",
        "best_candidate_same_school_prefix",
        "suggested_match_if_high_confidence",
    ]

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for rel in lines:
            docx = (base_docs / rel).resolve()
            stem = docx.stem if docx.exists() else Path(rel).stem
            fm = dp.parse_filename(docx if docx.exists() else Path(rel))
            school_part, _ = filename_parts_from_stem(stem)
            team_code = fm.team_code_filename or ""

            variants = build_target_variants(dp, fm.team_code_filename)
            var_list = [v for v in variants if v]
            var_str = ";".join(sorted(var_list))

            tops = top_fuzzy_candidates(variants, entry_rows, school_part, k=8)
            cand_parts = []
            for comb, var_sc, raw, et in tops[:3]:
                excerpt = re.sub(r"\s+", " ", raw)[:140]
                cand_parts.append(f"{comb:.3f}|{var_sc:.3f}|{et or ''}|{excerpt}")
            cand_col = " || ".join(cand_parts)

            best_raw = tops[0][2] if tops else ""
            best_team = tops[0][3] if tops else None
            best_variant_only = float(tops[0][1]) if tops else 0.0
            same_prefix = bool(best_raw and school_prefix_aligns(school_part, best_raw, dp))
            suggest = suggested_match(best_variant_only, best_raw, best_team, school_part, same_prefix)

            w.writerow(
                {
                    "source_file": fm.source_file,
                    "parsed_school_from_filename": school_part,
                    "parsed_team_code_from_filename": team_code,
                    "all_target_variants": var_str,
                    "closest_tabroom_entry_candidates_fuzzy": cand_col,
                    "best_candidate_same_school_prefix": "yes" if same_prefix else "no",
                    "suggested_match_if_high_confidence": suggest,
                }
            )

    print(f"Wrote {len(lines)} rows to {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
