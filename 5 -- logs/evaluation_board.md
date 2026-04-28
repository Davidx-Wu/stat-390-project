# Evaluation Board

## Baseline
- Gonzaga rebuild completed (2026-04-27):
  - 515 docs processed
  - 514 successful parser runs
  - 484 speech summary rows
  - 1 failed file
  - runtime ~1.5 hours

## Current Best
- Current best available build snapshot is the 2026-04-27 Gonzaga rebuild above.

## Dataset Diagnostics
- Implemented and verified for `4 -- results/processed_datasets/gonzaga_speech_dataset_v1.csv`.
- Fields used: `win_loss`, `team_code`, `round_number`, `num_cards_total`.
- Generated outputs under `4 -- results/diagnostics/`:
  - `win_loss_distribution.png`
  - `speeches_per_round.png`
  - `speeches_per_team.png`
  - `card_count_distribution.png`

## Metric
- Round outcome prediction accuracy

## Notes
- One known unmatched file remains (Michigan State JV-related team code mismatch).
- Iowa BS Round 1 FFT-style entry is now captured in parsing/join flow.
