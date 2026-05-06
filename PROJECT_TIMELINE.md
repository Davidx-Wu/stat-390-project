# Project Timeline

## Stage Folder Map

- `experiments/stage_1_gonzaga_predictive/`: initial Gonzaga-only predictive baselines and locked interaction-logistic workflow.
- `experiments/stage_2_feature_ablation/`: feature coverage, v3/v4/v5 ablations, semantic/LLM/broad-search diagnostics, and error analysis.
- `experiments/stage_3_cross_tournament/`: closed Northwestern+Gonzaga speech-level robustness and tournament-shift analysis.
- `experiments/stage_4_paired_rounds/`: paired Aff-vs-Neg round-level modeling.
- `experiments/stage_5_explanatory_strength/`: retrospective Shirley/team-strength explanatory modeling.

The numbered sections below describe experiment chronology; the repository no longer depends on numbered root-level folders for that chronology.

## 1. Initial Dataset and Parser Development

- Built a `.docx` parser for policy debate speech files.
- Parser outputs:
  - `speech_summary.csv`
  - `argument_audit.csv`
  - `card_audit.csv`
- Main parser: `src/parsing/debate_doc_parser.py`.
- Gonzaga batch builder processed 515 selected Gonzaga documents.
- Gonzaga build snapshot:
  - Documents processed: 515
  - Successful parser runs: 514
  - Speech rows: 484
  - Failed files: 1
  - Runtime: about 1.5 hours

## 2. Gonzaga Processed Dataset and Diagnostics

- Created canonical Gonzaga processed dataset:
  - `data/processed/gonzaga_speech_dataset_v1.csv`
- Added deterministic split:
  - train 70%
  - validation 15%
  - test 15%
  - seed/random state 42
- Outcome column: `win_loss`.
- Split column: `dataset_split`.
- Core structured features:
  - `num_positions`
  - `num_adv_inh_solv`
  - `num_offs`
  - `num_cards_total`
  - `num_cards_with_highlight`
  - `total_highlighted_words`
- Dataset diagnostics implemented:
  - win/loss distribution
  - speeches per round
  - speeches per team
  - card count distribution
- Key diagnostic outputs:
  - `results/gonzaga/diagnostics/win_loss_distribution.png`
  - `results/gonzaga/diagnostics/speeches_per_round.png`
  - `results/gonzaga/diagnostics/speeches_per_team.png`
  - `results/gonzaga/diagnostics/card_count_distribution.png`

## 3. Early Baselines

- Baseline v1:
  - Dataset size: 89 rows
  - Model: logistic regression
  - Accuracy: 0.3913
- Baseline v2:
  - Dataset size: 484 rows
  - Model: logistic regression
  - Accuracy: 0.4306
- These were superseded by validation-split experiments using the fixed `dataset_split`.

## 4. Feature Coverage and AutoResearch Planning

- Created feature coverage inspection:
  - `src/diagnostics/inspect_feature_coverage.py`
  - `results/gonzaga/diagnostics/feature_coverage_summary.csv`
- Wrote AutoResearch plan:
  - `logs/autoresearch_plan.md`
- Locked validation principle:
  - train/validation for model selection
  - reserve test for final evaluation

## 5. Gonzaga-Only Structured Baselines

- Baseline v3:
  - Features: six safe structured numeric features
  - Model: logistic regression
  - Validation accuracy: `0.616438`
  - Majority validation baseline: `0.602740`
- Baseline v4:
  - Added `side`
  - Validation accuracy: `0.575342`
  - Result: discarded
- Baseline v5:
  - Added density features
  - Validation accuracy: `0.452055`
  - Result: discarded
- Citation-year v6 attempt:
  - Removed because processed dataset had no citation/year fields.

## 6. Gonzaga AutoResearch Loop

- Created `experiments/gonzaga_autoresearch/` using frozen/ editable boundary:
  - `prepare.py`: frozen data/evaluation
  - `run.py`: frozen runner
  - `model.py`: editable model only
  - `program.md`: rules
- Baseline logistic accuracy: `0.616438`.
- Interaction-only degree-2 logistic accuracy: `0.630137`.
- Tuned interaction logistic with `C=0.5`: `0.643836`.
- Discarded:
  - full degree-2 polynomial logistic
  - random forest
  - gradient boosting
  - hist gradient boosting
  - class-weight balanced logistic
- Core Week 6 locked model:
  - interaction-only degree-2 features
  - `LogisticRegression(C=0.5)`
  - validation accuracy: `0.643836`

## 7. Error Analysis

- Created locked validation prediction exports:
  - `src/modeling/export_locked_validation_predictions.py`
  - `results/gonzaga/error_analysis/validation_predictions.csv`
  - `results/gonzaga/error_analysis/validation_misclassifications.csv`
- Gonzaga locked validation errors:
  - validation rows: 73
  - correct: 47
  - false positives: 20
  - false negatives: 6
- Main observation:
  - Model over-predicted wins for dense-looking speeches, especially where structure looked strong but ballot outcome was a loss.

## 8. Semantic and LLM Feature Attempts

- Built text-enriched Gonzaga v2 dataset:
  - `data/processed/gonzaga_speech_dataset_v2_with_text.csv`
- LLM prompt pipeline:
  - prompt generation succeeded/dry-run artifacts exist
  - LLM scoring infrastructure was not part of final clean result
- Highlighted semantic feature ablation:
  - `archive/semantic_feature_ablation/scripts/build_semantic_highlight_features_v1.py`
  - features included causal/certainty/impact/numeric-reference counts
  - semantic+highlight features accuracy: `0.561644`
  - Result: discarded

## 9. Aggressive Non-Leaky Feature Search

- Created `archive/broad_feature_search/scripts/run_nonleaky_feature_search.py`.
- Outputs:
  - `archive/broad_feature_search/results/feature_inventory.csv`
  - `archive/broad_feature_search/results/experiment_table.csv`
  - `archive/broad_feature_search/results/best_model_validation_predictions.csv`
  - `archive/broad_feature_search/results/feature_search_summary.md`
- Best found:
  - manual selected interactions logistic
  - validation accuracy: `0.671233`
- Interpretation:
  - promising but should be treated cautiously because validation size is small.
  - did not reach the 70% target.

## 10. Closed Northwestern+Gonzaga Experiment

- Created closed folder:
  - `experiments/northwestern_gonzaga_closed/`
- Confirmed Northwestern tournament document selection using tournament-counting logic:
  - expected count from `tournament_disclosure_counts.csv`: 665
  - selected docs: 665
- Parsed Northwestern in resumable batches.
- Northwestern build:
  - docs selected: 665
  - docs parsed successfully: 665
  - rows joined to outcomes: 598
  - join failures: 67
  - usable Northwestern rows: 598
- Combined closed dataset:
  - Gonzaga rows: 484
  - Northwestern rows: 598
  - total rows: 1082
- Closed split:
  - train: 757
  - validation: 162
  - test: 163
- Closed validation results:
  - majority baseline: `0.518519`
  - structured logistic: `0.530864`
  - manual interaction logistic: `0.524691`
- Discovery:
  - adding Northwestern caused a large accuracy drop, indicating cross-tournament distribution shift.

## 11. Generalization Under Distribution Shift

- Created:
  - `run_generalization_experiments.py`
  - `generalization_experiment_table.csv`
  - `tournament_holdout_results.csv`
  - `calibration_summary.csv`
  - `error_cluster_summary.csv`
- Tested:
  - tournament z-normalized features
  - percentile features
  - centered features
  - relative/opponent-paired speech features
  - elastic net
  - calibrated linear SVM
- Closed validation:
  - raw logistic: `0.530864`
  - z-normalized only: `0.530864`
  - centered only: `0.530864`
  - relative-only: `0.518519`
- Tournament holdout:
  - train Gonzaga -> validate Northwestern best: relative-only `0.539526`
  - train Northwestern -> validate Gonzaga best: raw+relative `0.532688`
- Discovery:
  - normalization did not solve distribution shift.
  - relative features are a small robustness clue but not a strong fix.

## 12. Paired Round Unit-of-Analysis Experiment

- Created:
  - `run_paired_round_experiment.py`
  - `paired_round_dataset_closed_with_split.csv`
  - `paired_round_experiment_table.csv`
- Pairing:
  - input speech rows: 1082
  - candidate matchup groups: 704
  - paired rounds created: 373
  - dropped one-sided groups: 331
  - duplicate side groups handled: 5
- Pair-level split:
  - train: 261
  - validation: 56
  - test: 56
- Validation:
  - paired majority baseline: `0.535714`
  - raw paired logistic: `0.410714`
  - diff-only logistic: `0.446429`
  - manual interaction paired logistic: `0.410714`
- Discovery:
  - pair-level framing was theoretically sensible but parser-derived paired features did not improve learned performance.

## 13. Ranking Prior Diagnostic

- Shirley ranking audit:
  - columns include `Place`, `WinPm`, `PtsPm`, `OSd`, `Ballots`
  - file is high leakage risk for real-time prediction because it contains post-tournament results
- Diagnostic results:
  - Shirley rank-only speech model: `0.718310` on 71 covered validation rows
  - Shirley rank + speech structure: `0.690141`
  - paired rank-diff only: `0.680000` on 25 covered validation rows
  - paired rank-diff + paired speech features: `0.520000`
- Discovery:
  - team-strength/result context dominates document structure, but this is diagnostic only.

## 14. Retrospective Explanatory Model

- Created:
  - `run_explanatory_strength_model.py`
  - `explanatory_experiment_table.csv`
  - `explanatory_model_coefficients.csv`
  - `explanatory_model_summary.md`
- Complete Shirley-linked rows:
  - 444 of 1082
  - validation rows: 71
- Explanatory results:
  - speech structure only: `0.530864`
  - Shirley strength only logistic: `0.746479`
  - Shirley strength only elastic net: `0.746479`
  - combined speech + Shirley logistic: `0.704225`
  - combined speech + Shirley elastic net: `0.690141`
- Final explanatory conclusion:
  - latent team strength/result variables explain much more than parser-derived speech structure.
  - speech features do not add incremental explanatory value after Shirley variables are included.

## Final Chronological Conclusion

The project started with the hypothesis that structured debate speech features, and possibly semantic/LLM argument-quality features, could predict debate outcomes. Gonzaga-only experiments found modest signal, especially through interaction terms. Cross-tournament experiments showed that this signal generalizes poorly. Retrospective Shirley explanatory models showed that latent team strength dominates parser-derived structural features, but those variables are not valid clean predictive features.
