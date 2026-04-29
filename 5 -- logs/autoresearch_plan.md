# AutoResearch Plan

## Research Question
Can structured features extracted from Gonzaga policy debate speech documents improve prediction of round outcomes beyond the current baseline logistic regression model?

## Current Baseline
- Baseline v2 model: logistic regression.
- Baseline v2 accuracy: **0.4306**.
- Current outcome column: `win_loss`.
- Current split column: `dataset_split`.

## Current Dataset Status
- Processed dataset: `4 -- results/processed_datasets/gonzaga_speech_dataset_v1.csv`.
- Overall win rate: **0.514**.
- Existing diagnostics live under `4 -- results/diagnostics/`.
- Current known columns include team, round, side, opponent, judge, parser confidence, and structured evidence-count features.

## Candidate Feature Groups
- Evidence quantity features:
  - `num_positions`
  - `num_adv_inh_solv`
  - `num_offs`
  - `num_cards_total`
  - `num_cards_with_highlight`
  - `total_highlighted_words`
- Citation/year features:
  - Not yet represented as explicit structured columns in the processed dataset.
  - Future work can extract citation metadata and publication-year summaries if parser support is added.
- Speech length features:
  - Not yet represented as explicit structured columns in the processed dataset.
  - Future work can add token, word, paragraph, or card-text length summaries.
- Side/team/round metadata:
  - `side`
  - `team_code`
  - `opponent`
  - `round_number`
  - `judge`
  - `tournament_name`
  - `parse_confidence`
- Future LLM argument-quality features:
  - Claim clarity.
  - Warrant strength.
  - Impact quality.
  - Evidence relevance.
  - Argument interaction or comparative strength.

## Fixed Validation Principle
- Do not tune on the test set.
- Use train and validation splits first for feature selection, model comparison, and threshold/model decisions.
- Reserve the test split for final evaluation after the modeling approach is fixed.

## Next Experiment
Build baseline v3 using all safe structured numeric features from the processed dataset, then compare validation performance against baseline v2. Do not train this model until the feature coverage inspection has been reviewed.

## Baseline v3 Result
- Status: completed.
- Model: scikit-learn logistic regression using safe structured numeric features only.
- Fit split: train.
- Evaluation split: validation.
- Test split: not used.
- Features:
  - `num_positions`
  - `num_adv_inh_solv`
  - `num_offs`
  - `num_cards_total`
  - `num_cards_with_highlight`
  - `total_highlighted_words`
- Validation accuracy: **0.6164**.
- Majority-class validation baseline: **0.6027**.
- Result: baseline v3 beat the majority-class validation baseline.
- Outputs:
  - `4 -- results/baseline_runs/baseline_v3_structured_numeric_metrics.csv`
  - `4 -- results/baseline_runs/baseline_v3_structured_numeric_coefficients.csv`

## Baseline v5 Density-Feature Result
- Status: completed.
- Model: scikit-learn logistic regression using v3 structured numeric features plus derived argument-density features.
- Fit split: train.
- Evaluation split: validation.
- Test split: not used.
- Added density features:
  - `cards_per_position`
  - `offs_ratio`
  - `highlight_ratio`
  - `highlight_words_per_card`
- Validation accuracy: **0.4521**.
- Majority-class validation baseline: **0.6027**.
- Baseline v3 validation accuracy: **0.6164**.
- Result: baseline v5 did not beat baseline v3.
- Outputs:
  - `4 -- results/baseline_runs/baseline_v5_density_metrics.csv`
  - `4 -- results/baseline_runs/baseline_v5_density_coefficients.csv`

## Baseline v6 LLM Argument-Quality Result
- Status: blocked before LLM scoring or model training.
- Goal: score speech/card text for argument quality, then train logistic regression using v3 structured features plus LLM scores.
- Finding: no usable speech/card text column exists in `4 -- results/processed_datasets/gonzaga_speech_dataset_v1.csv`.
- Available text-like metadata is not suitable for prompting because fields such as `source_file`, `team_code`, `opponent`, `judge`, `tournament_name`, and `dataset_split` should not be included in LLM prompts.
- Diagnostic: `4 -- results/llm_features/llm_argument_features_v6_diagnostic.txt`.
- Scripts:
  - `3 -- src/build_llm_argument_features_v6.py`
  - `3 -- src/baseline_v6_llm_features.py`
- Next requirement: parser or dataset-building support must export usable speech/card text before LLM argument-quality features can be built.

## Text-Enriched Dataset v2
- Status: completed.
- Output: `4 -- results/processed_datasets/gonzaga_speech_dataset_v2_with_text.csv`.
- Input files:
  - `4 -- results/processed_datasets/gonzaga_speech_dataset_v1.csv`
  - `gonzaga_dataset_output/card_audit_all.csv`
  - `gonzaga_dataset_output/argument_audit_all.csv`
- Join key used: `source_file`.
- Stable key candidates inspected: `source_file`, `team_code`, `round_number`, `side`.
- v1 rows: **484**.
- Rows matched to card audit text: **207**.
- Rows matched to argument audit text: **376**.
- Rows missing both card and argument text: **108**.
- New text/count columns:
  - `card_text_combined`
  - `argument_text_combined`
  - `card_count_from_audit`
  - `argument_count_from_audit`
  - `card_text_char_count`
  - `argument_text_char_count`
  - `card_text_truncated`
  - `argument_text_truncated`
- Note: v1 was not overwritten. No model was trained from v2 yet.

## Shirley Ranking Strength Analysis
- Status: completed.
- Ranking file: `1 -- data/raw/9 -- Build Gonzaga Dataset/gonzaga_dataset_output/Shirley_Rankings.csv`.
- Ranking columns used: `Place` as rank/seed, with lower `Place` meaning stronger; team codes derived from `School` plus debater initials from `Entry`.
- In-memory joined columns: `team_rank`, `opponent_rank`, `rank_diff`.
- Interpretation: `rank_diff = opponent_rank - team_rank`; positive means the current team is stronger.
- Train/validation rows: **412**.
- `team_rank` matched: **287**.
- `opponent_rank` matched: **276**.
- non-null `rank_diff`: **193**.
- Full validation results:
  - arguments only, all validation rows: accuracy **0.6438**, majority baseline **0.6027**, validation rows **73**.
  - rank only, non-null rank rows: accuracy **0.6471**, majority baseline **0.6765**, validation rows **34**, `rank_diff` coefficient **1.7353**.
  - arguments + `rank_diff`, non-null rank rows: accuracy **0.6471**, majority baseline **0.6765**, validation rows **34**, main `rank_diff` coefficient **1.2857**.
- Close-match results:
  - `abs(rank_diff) <= 5`: only **2** validation rows; all models accuracy **0.5000**, majority baseline **1.0000**.
  - `abs(rank_diff) <= 10`: **7** validation rows; all models accuracy **0.5714**, majority baseline **0.5714**.
- Interpretation: this validation slice is too small to show that argument features matter more among similarly ranked teams. Adding argument features did not improve over rank-only in the close-match subsets.
- Outputs:
  - `debate-autoresearch/ranking_strength_results.tsv`
  - `debate-autoresearch/ranking_strength_close_match_results.tsv`

## Citation-Year Feature Note
Citation-year feature experiment was attempted, but no citation/year columns exist in the processed dataset, so the experiment was removed as non-informative. Future work requires parser support for citation-year extraction.
