# Gonzaga Build Run — 2026-04-27

## Summary
- Documents processed: **515**
- Successful parser runs: **514**
- Failed files: **1**
- `speech_summary_all.csv` rows: **484**
- Runtime: **~1.5 hours**

## Remaining failed file
- `Gonzaga_only\MichiganState\Asst\MichiganState-Asst-Aff-02---Gonzaga-University-Jesuit-Debates-Round-6.docx`
- Join warning: `no_matching_team_row_in_tournament_csv`
- Note: known Michigan State JV/team-code mismatch case.

## Notes
- Parser code was not changed during this logging update.
- This record reflects the completed Gonzaga rebuild results reported on 2026-04-27.

## Dataset diagnostics
- Implemented and verified for `4 -- results/processed_datasets/gonzaga_speech_dataset_v1.csv`.
- Fields used: `win_loss`, `team_code`, `round_number`, `num_cards_total`.
- Generated outputs under `4 -- results/diagnostics/`:
  - `win_loss_distribution.png`
  - `speeches_per_round.png`
  - `speeches_per_team.png`
  - `card_count_distribution.png`
