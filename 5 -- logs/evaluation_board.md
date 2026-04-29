# Evaluation Board

## Baseline
- Gonzaga rebuild completed (2026-04-27):
  - 515 docs processed
  - 514 successful parser runs
  - 484 speech summary rows
  - 1 failed file
  - runtime ~1.5 hours
- Baseline v3 structured numeric model:
  - model: logistic regression
  - train split only for fitting; validation split only for evaluation
  - features: `num_positions`, `num_adv_inh_solv`, `num_offs`, `num_cards_total`, `num_cards_with_highlight`, `total_highlighted_words`
  - implementation: scikit-learn `Pipeline(StandardScaler, LogisticRegression)`
  - validation accuracy: **0.6164**
  - majority-class validation baseline: **0.6027**
  - confusion matrix: true L/pred L = 5, true L/pred W = 24, true W/pred L = 4, true W/pred W = 40
  - outputs: `4 -- results/baseline_runs/baseline_v3_structured_numeric_metrics.csv`, `4 -- results/baseline_runs/baseline_v3_structured_numeric_coefficients.csv`
- Baseline v5 density-feature model:
  - model: logistic regression
  - train split only for fitting; validation split only for evaluation
  - added features: `cards_per_position`, `offs_ratio`, `highlight_ratio`, `highlight_words_per_card`
  - validation accuracy: **0.4521**
  - majority-class validation baseline: **0.6027**
  - comparison to v3: **-0.1644**
  - confusion matrix: true L/pred L = 10, true L/pred W = 19, true W/pred L = 21, true W/pred W = 23
  - outputs: `4 -- results/baseline_runs/baseline_v5_density_metrics.csv`, `4 -- results/baseline_runs/baseline_v5_density_coefficients.csv`
- Baseline v6 LLM argument-quality model:
  - status: blocked before scoring/training
  - reason: no usable speech/card text column exists in `4 -- results/processed_datasets/gonzaga_speech_dataset_v1.csv`
  - diagnostic: `4 -- results/llm_features/llm_argument_features_v6_diagnostic.txt`
  - scripts: `3 -- src/build_llm_argument_features_v6.py`, `3 -- src/baseline_v6_llm_features.py`
- Citation-year feature experiment was attempted, but no citation/year columns exist in the processed dataset, so the experiment was removed as non-informative. Future work requires parser support for citation-year extraction.

## Current Best
- Current best validation result from the debate AutoResearch loop is interaction-only degree-2 logistic regression with `C=0.5`, with validation accuracy **0.6438**.

## Dataset Diagnostics
- Implemented and verified for `4 -- results/processed_datasets/gonzaga_speech_dataset_v1.csv`.
- Fields used: `win_loss`, `team_code`, `round_number`, `num_cards_total`.
- Generated outputs under `4 -- results/diagnostics/`:
  - `win_loss_distribution.png`
  - `speeches_per_round.png`
  - `speeches_per_team.png`
  - `card_count_distribution.png`
- Text-enriched dataset v2 created at `4 -- results/processed_datasets/gonzaga_speech_dataset_v2_with_text.csv`.
  - join key used: `source_file`
  - stable key candidates inspected: `source_file`, `team_code`, `round_number`, `side`
  - v1 rows: **484**
  - rows matched to card audit text: **207**
  - rows matched to argument audit text: **376**
  - rows missing both text sources: **108**
  - new text columns: `card_text_combined`, `argument_text_combined`
  - new audit count columns: `card_count_from_audit`, `argument_count_from_audit`
- Shirley ranking strength analysis completed:
  - ranking file: `1 -- data/raw/9 -- Build Gonzaga Dataset/gonzaga_dataset_output/Shirley_Rankings.csv`
  - rank feature: `rank_diff = opponent_rank - team_rank`
  - train/validation rows: **412**
  - `team_rank` matched: **287**
  - `opponent_rank` matched: **276**
  - non-null `rank_diff`: **193**
  - full validation: arguments only accuracy **0.6438** on 73 rows; rank only accuracy **0.6471** on 34 rank-matched rows; arguments + rank accuracy **0.6471** on 34 rank-matched rows
  - close validation subsets were very small: **2** rows for `abs(rank_diff) <= 5`, **7** rows for `abs(rank_diff) <= 10`
  - outputs: `debate-autoresearch/ranking_strength_results.tsv`, `debate-autoresearch/ranking_strength_close_match_results.tsv`

## Metric
- Round outcome prediction accuracy

## Notes
- One known unmatched file remains (Michigan State JV-related team code mismatch).
- Iowa BS Round 1 FFT-style entry is now captured in parsing/join flow.
- Baseline v3 did not use the test split.
- Baseline v5 did not use the test split and did not improve over v3.
- Baseline v6 LLM features could not be trained because the processed dataset does not include speech/card text.
- Text-enriched v2 was built from audit files without overwriting v1; no model has been trained on v2 yet.
- Shirley rank close-match subsets are too small to support a strong claim that argument features matter more among similarly ranked teams.
