# Research Log

## 2026-04-27
- Ran Gonzaga dataset rebuild after join/matching updates and parser path fix in the temp builder.
- Processed 515 documents total.
- 514 parser runs succeeded; 1 file remained unmatched to a tournament row.
- Combined speech summary output contains 484 rows.
- Full run took approximately 1.5 hours.
- Implemented and verified dataset diagnostics for `4 -- results/processed_datasets/gonzaga_speech_dataset_v1.csv`.
- Diagnostics fields used: `win_loss`, `team_code`, `round_number`, `num_cards_total`.
- Generated diagnostic outputs: `win_loss_distribution.png`, `speeches_per_round.png`, `speeches_per_team.png`, `card_count_distribution.png`.

## 2026-04-16
- Set up repo structure
- Defined baseline as evidence quantity and source type
- Next: finalize data schema
