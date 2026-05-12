# Canonical Workflows

## Experiment Chronology

Chronology is preserved through staged experiment folders, timeline docs, logs, and Git history rather than numbered root-level folders.

| Stage | Folder | Purpose | Canonical Artifacts |
| --- | --- | --- | --- |
| 1 | `experiments/stage_1_gonzaga_predictive/` | Gonzaga-only predictive baselines and locked interaction-logistic model. | `experiments/gonzaga_autoresearch/`, `results/gonzaga/baseline_runs/` |
| 2 | `experiments/stage_2_feature_ablation/` | Gonzaga-only feature ablations, diagnostics, semantic/LLM/broad-search attempts. | `results/gonzaga/diagnostics/`, `results/gonzaga/error_analysis/`, `archive/` |
| 3 | `experiments/stage_3_cross_tournament/` | Closed Northwestern+Gonzaga robustness under tournament shift. | `experiments/northwestern_gonzaga_closed/results/closed_experiment_table.csv` |
| 4 | `experiments/stage_4_paired_rounds/` | Pair-level Aff-vs-Neg unit-of-analysis check. | `experiments/northwestern_gonzaga_closed/results/paired_round_experiment_table.csv` |
| 5 | `experiments/stage_5_explanatory_strength/` | Retrospective Shirley/team-strength explanatory models. | `experiments/northwestern_gonzaga_closed/results/explanatory_experiment_table.csv` |

## A. Clean Gonzaga Predictive Workflow

### Purpose

Estimate whether parser-derived speech structure contains non-leaky predictive signal for debate outcomes in the Gonzaga-only dataset.

### Canonical Dataset

- `data/processed/gonzaga_speech_dataset_v1.csv`
- Mirror: `data/processed/gonzaga_speech_dataset_v1.csv`

### Canonical Features

- `num_positions`
- `num_adv_inh_solv`
- `num_offs`
- `num_cards_total`
- `num_cards_with_highlight`
- `total_highlighted_words`
- interaction-only degree-2 transformations for the locked AutoResearch model

### Canonical Scripts

- `src/parsing/debate_doc_parser.py`
- `src/parsing/build_gonzaga_dataset.py`
- `src/modeling/baseline_v3_structured_numeric.py`
- `experiments/gonzaga_autoresearch/prepare.py`
- `experiments/gonzaga_autoresearch/model.py`
- `experiments/gonzaga_autoresearch/run.py`

### Canonical Outputs

- `results/gonzaga/baseline_runs/baseline_v3_structured_numeric_metrics.csv`
- `experiments/gonzaga_autoresearch/results.tsv`
- `experiments/gonzaga_autoresearch/experiment_summary.md`
- `results/gonzaga/error_analysis/validation_predictions.csv`
- `results/gonzaga/error_analysis/validation_misclassifications.csv`

### Main Result

- Structured v3 logistic validation accuracy: `0.616438`
- Locked interaction logistic validation accuracy: `0.643836`
- Broad non-leaky manual interaction candidate: `0.671233`, treated cautiously

### Deprecated Alternatives

- `baseline_v4_side_features.py`
- `baseline_v5_density_features.py`
- semantic highlighted-text ablation
- LLM dry-run prompt/scoring pipeline
- tree/boosting model attempts

## B. Closed Northwestern+Gonzaga Robustness Workflow

### Purpose

Test whether the Gonzaga-only structured-feature signal survives cross-tournament distribution shift after adding Northwestern tournament data.

### Canonical Dataset

- `experiments/northwestern_gonzaga_closed/data_processed/combined_speech_dataset_closed_with_split.csv`
- Mirror: `data/processed/closed_northwestern_gonzaga/combined_speech_dataset_closed_with_split.csv`

### Canonical Scripts

- `experiments/northwestern_gonzaga_closed/scripts/preview_northwestern_doc_selection.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_closed_experiment.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_generalization_experiments.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_paired_round_experiment.py`

### Canonical Outputs

- `experiments/northwestern_gonzaga_closed/results/closed_experiment_table.csv`
- `experiments/northwestern_gonzaga_closed/results/generalization_experiment_table.csv`
- `experiments/northwestern_gonzaga_closed/results/tournament_holdout_results.csv`
- `experiments/northwestern_gonzaga_closed/results/paired_round_experiment_table.csv`
- `experiments/northwestern_gonzaga_closed/logs/closed_experiment_summary.md`
- `experiments/northwestern_gonzaga_closed/logs/generalization_summary.md`
- `experiments/northwestern_gonzaga_closed/logs/paired_round_experiment_summary.md`

### Main Results

- Combined speech rows: `1082`
- Closed validation rows: `162`
- Majority baseline: `0.518519`
- Structured logistic: `0.530864`
- Manual interaction logistic: `0.524691`
- Tournament z-normalization: tied raw model at `0.530864`
- Pair-level learned models did not improve over majority baseline

### Deprecated Alternatives

- Ranking variables as clean predictors
- semantic keyword expansion
- broad model search
- tree ensembles

## C. Retrospective Explanatory Workflow

### Purpose

Retrospectively test whether latent team-strength/result variables explain substantially more outcome variance than parser-derived speech structure.

### Important Framing

This is not a clean real-time prediction workflow. Shirley variables are temporally downstream and contain post-tournament metrics.

### Canonical Dataset

- `experiments/northwestern_gonzaga_closed/data_processed/combined_speech_dataset_closed_with_split.csv`
- `experiments/northwestern_gonzaga_closed/data_raw/Shirley_Rankings.csv`

### Canonical Scripts

- `experiments/northwestern_gonzaga_closed/scripts/run_ranking_prior_experiment.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_explanatory_strength_model.py`

### Canonical Outputs

- `experiments/northwestern_gonzaga_closed/results/ranking_prior_experiment_table.csv`
- `experiments/northwestern_gonzaga_closed/results/explanatory_experiment_table.csv`
- `experiments/northwestern_gonzaga_closed/results/explanatory_model_coefficients.csv`
- `experiments/northwestern_gonzaga_closed/diagnostics/explanatory_feature_summary.csv`
- `experiments/northwestern_gonzaga_closed/logs/ranking_prior_experiment_summary.md`
- `experiments/northwestern_gonzaga_closed/logs/explanatory_model_summary.md`

### Main Results

- Speech-structure-only logistic: `0.530864`
- Shirley/team-strength-only logistic: `0.746479`
- Shirley/team-strength-only elastic net: `0.746479`
- Combined speech + Shirley logistic: `0.704225`
- Combined speech + Shirley elastic net: `0.690141`

### Main Conclusion

Latent team-strength/result variables dominate parser-derived structural speech features in retrospective explanation. Speech features do not add incremental explanatory value after Shirley variables are included.

### Deprecated Alternatives

- Framing Shirley features as valid real-time predictors.
- Treating ranking prior results as clean predictive evidence.
