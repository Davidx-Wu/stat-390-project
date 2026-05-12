# Failure Log

## 2026-04-27 — Gonzaga rebuild
- Build totals: 515 docs processed, 514 successful, 1 failed, runtime ~1.5 hours.
- Remaining failed file:
  - `Gonzaga_only\MichiganState\Asst\MichiganState-Asst-Aff-02---Gonzaga-University-Jesuit-Debates-Round-6.docx`
- Failure type:
  - `no_matching_team_row_in_tournament_csv`
- Context:
  - This appears to be a Michigan State JV policy team mismatch relative to the tournament table entries.

## 2026-04-16
- No failures yet
- Known risk: outcome labels may be noisy or sparse

## 2026-05-12 -- Week 5 documentation and scope risks
- This update is additive; older path references are preserved as historical notes.
- Current canonical structure is described in `docs/CANONICAL_PIPELINE.md`.
- Older numbered-folder paths such as `3 -- src`, `4 -- results`, and `5 -- logs` should be read as legacy references, not current canonical paths.
- LLM/semantic feature work remains a non-final direction:
  - LLM scoring was not part of the final clean result.
  - highlighted semantic features underperformed and are preserved as historical/archived work.
- Cross-tournament accuracy drop after adding Northwestern is not treated as a crash. It is a substantive distribution-shift finding.
- Paired-round modeling was theoretically motivated but did not improve validation performance; it should be treated as a negative result, not a pipeline failure.
- Retrospective Shirley/team-strength results have leakage risk for real-time prediction because the variables are downstream/post-tournament proxies. They should be framed only as explanatory evidence.
- Metric trajectory artifacts are stored in `reports/figures/`.
- No experiments were rerun and no result values were changed for this update.
