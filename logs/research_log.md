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

## 2026-05-12 -- Week 5 repository and pipeline clarification
- Added the canonical reader-facing guide at `docs/CANONICAL_PIPELINE.md`.
- Current canonical repo structure uses descriptive folders: `data/`, `src/`, `results/`, `experiments/`, `logs/`, `reports/`, `archive/`, and `docs/`.
- Older references to numbered folders such as `3 -- src`, `4 -- results`, and `5 -- logs` are preserved as historical path references from earlier project stages.
- Final clean predictive model is the Gonzaga-only interaction-only degree-2 logistic regression with `LogisticRegression(C=0.5)`, implemented in `experiments/gonzaga_autoresearch/model.py`.
- Final clean predictive result remains validation accuracy **0.643836** on the Gonzaga validation split.
- Retrospective Shirley/team-strength models are tracked separately from clean prediction because Shirley variables are downstream/post-tournament proxies for latent team strength.
- Metric trajectory plot and source data are stored in `reports/figures/`:
  - `metric_over_time_plot.png`
  - `metric_over_time_data.csv`
  - `metric_over_time_caption.md`
- No experiments were rerun for this documentation update, and no result values were changed.
