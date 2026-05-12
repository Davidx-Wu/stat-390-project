# Canonical Pipeline

This document explains the repository as it exists today. It is meant for a first-time reader who wants to understand what is canonical, what is historical, and how the main results can be reproduced without reopening the full research search.

The project asks whether policy debate speech documents contain enough structured information to predict debate round outcomes. The final answer is deliberately split into two parts:

- Clean predictive setting: parser-derived speech structure contains modest signal, especially with interaction terms, but generalizes poorly across tournaments.
- Retrospective explanatory setting: downstream Shirley/team-strength variables explain substantially more outcome variation, but they are not valid real-time prediction features.

## Repository Map

The active repository uses descriptive top-level folders:

```text
archive/       Historical, deprecated, or abandoned work preserved for transparency.
data/          Raw and processed data used by canonical workflows.
experiments/   Staged experiment folders and closed experiment workspaces.
logs/          Research logs, evaluation notes, and build/failure history.
reports/       Presentation-ready figures and report artifacts.
results/       Generated Gonzaga diagnostics, parser outputs, and baseline artifacts.
src/           Canonical parsing, modeling, and diagnostics scripts.
docs/          Reader-facing documentation such as this pipeline guide.
```

Older numbered root folders were removed or archived during cleanup. Some historical logs may still mention paths such as `3 -- src`, `4 -- results`, or `5 -- logs`; those references describe earlier project states. The canonical current paths are the descriptive paths listed in this document.

## Data Flow

The core data flow is:

```text
raw debate .docx files
  -> parser/audit outputs
  -> processed speech-level datasets
  -> diagnostics and feature coverage
  -> Gonzaga-only predictive models
  -> closed Northwestern+Gonzaga robustness checks
  -> retrospective Shirley/team-strength explanatory models
```

### Canonical Inputs

- Gonzaga processed dataset: `data/processed/gonzaga_speech_dataset_v1.csv`
- Text-enriched Gonzaga dataset: `data/processed/gonzaga_speech_dataset_v2_with_text.csv`
- Closed combined dataset: `experiments/northwestern_gonzaga_closed/data_processed/combined_speech_dataset_closed_with_split.csv`
- Shirley rankings used for retrospective explanation: `experiments/northwestern_gonzaga_closed/data_raw/Shirley_Rankings.csv`

### Canonical Parser Outputs

- `results/gonzaga/parser_output/speech_summary_all.csv`
- `results/gonzaga/parser_output/argument_audit_all.csv`
- `results/gonzaga/parser_output/card_audit_all.csv`
- `results/gonzaga/parser_output/run_log.csv`
- `results/gonzaga/parser_output/failed_files.txt`

### Canonical Diagnostics

- `results/gonzaga/diagnostics/feature_coverage_summary.csv`
- `results/gonzaga/diagnostics/dataset_balance_summary.csv`
- `results/gonzaga/diagnostics/team_record_summary.csv`
- `results/gonzaga/diagnostics/win_loss_distribution.png`
- `results/gonzaga/diagnostics/speeches_per_round.png`
- `results/gonzaga/diagnostics/speeches_per_team.png`
- `results/gonzaga/diagnostics/card_count_distribution.png`

## Canonical Scripts

### Parsing and Data Construction

- `src/parsing/debate_doc_parser.py`: canonical `.docx` parser for debate documents.
- `src/parsing/build_gonzaga_dataset.py`: Gonzaga batch parser/builder.
- `src/parsing/build_text_enriched_dataset_v2.py`: creates the text-enriched v2 dataset from parser audit files.
- `src/parsing/count_tournament_disclosures.py`: counts disclosure documents by detected tournament.
- `src/parsing/select_tournament_docs.py`: selects documents for a tournament using the tournament-counting logic.

### Diagnostics

- `src/diagnostics/dataset_diagnostics.py`: creates dataset diagnostic plots.
- `src/diagnostics/check_dataset_balance.py`: creates win/loss and team balance summaries.
- `src/diagnostics/inspect_feature_coverage.py`: classifies columns as likely safe features, metadata, text, or leakage risks.
- `src/diagnostics/generate_join_failure_candidates.py`: historical parser/join diagnostic; useful for auditing but not part of the main final workflow.

### Modeling

- `src/modeling/baseline_v3_structured_numeric.py`: structured six-feature logistic baseline.
- `src/modeling/export_locked_validation_predictions.py`: exports locked-model validation predictions and misclassifications for error analysis.
- `experiments/gonzaga_autoresearch/prepare.py`: frozen Gonzaga AutoResearch data/evaluation support.
- `experiments/gonzaga_autoresearch/model.py`: locked final Gonzaga predictive model.
- `experiments/gonzaga_autoresearch/run.py`: Gonzaga AutoResearch runner.

### Closed Northwestern+Gonzaga Experiments

The closed experiment folder is intentionally self-contained:

- `experiments/northwestern_gonzaga_closed/scripts/preview_northwestern_doc_selection.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_closed_experiment.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_generalization_experiments.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_paired_round_experiment.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_ranking_prior_experiment.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_explanatory_strength_model.py`

This folder also contains copied parser utilities with historical names such as `*_vF.py` and `*_vTemp_copy.py`. Those names are messy but intentional: they preserve the closed experiment exactly as it was run.

## Experiment Chronology

Chronology is preserved in `docs/chronology/PROJECT_TIMELINE.md`, logs, Git history, and the staged experiment folders:

```text
experiments/stage_1_gonzaga_predictive/
experiments/stage_2_feature_ablation/
experiments/stage_3_cross_tournament/
experiments/stage_4_paired_rounds/
experiments/stage_5_explanatory_strength/
```

### Stage 1: Gonzaga Predictive Baselines

The project began with Gonzaga-only speech-level prediction. The canonical processed dataset is `data/processed/gonzaga_speech_dataset_v1.csv`.

Important results:

- Baseline v3 structured logistic validation accuracy: `0.616438`
- Locked interaction-only logistic validation accuracy: `0.643836`

### Stage 2: Feature Ablations and Error Analysis

The project tested side features, density features, citation-year features, semantic highlighted-text features, LLM dry-run prompts, and broader non-leaky feature search.

Important outcomes:

- Side and density features did not improve the locked model.
- Citation-year features were removed because the processed dataset did not contain citation/year fields.
- Highlighted semantic features underperformed and were archived.
- LLM scoring was not part of the final clean result.
- Error analysis showed the locked model often over-predicted wins for dense-looking speeches.

### Stage 3: Closed Northwestern+Gonzaga Robustness

Northwestern was added in a closed experiment folder so the original Gonzaga workflow remained untouched.

Important results:

- Combined rows: `1082`
- Closed validation rows: `162`
- Majority baseline: `0.518519`
- Structured logistic: `0.530864`
- Manual interaction logistic: `0.524691`

This showed that the Gonzaga-only signal weakened sharply under cross-tournament distribution shift.

### Stage 4: Paired Round Modeling

The project then changed the unit of analysis from speech rows to paired Aff-vs-Neg round rows.

Important results:

- Paired rounds created: `373`
- Validation rows: `56`
- Paired majority baseline: `0.535714`
- Raw paired logistic: `0.410714`
- Diff-only logistic: `0.446429`
- Manual interaction paired logistic: `0.410714`

The paired design was theoretically reasonable, but parser-derived paired features did not improve performance.

### Stage 5: Retrospective Shirley/Team-Strength Explanation

The final explanatory stage tested whether latent team strength explains more than document structure.

Important warning:

Shirley variables are downstream/post-tournament result variables. They should not be framed as leakage-free real-time prediction features.

Important results:

- Speech-structure-only logistic: `0.530864`
- Shirley/team-strength-only logistic: `0.746479`
- Shirley/team-strength-only elastic net: `0.746479`
- Combined speech + Shirley logistic: `0.704225`

This supports the final explanatory claim that latent team strength dominates the current parser-derived speech features.

## Locked Final Model

The locked clean predictive model is:

- interaction-only degree-2 logistic regression
- `LogisticRegression(C=0.5)`
- six parser-derived structured features:
  - `num_positions`
  - `num_adv_inh_solv`
  - `num_offs`
  - `num_cards_total`
  - `num_cards_with_highlight`
  - `total_highlighted_words`

Implementation:

- `experiments/gonzaga_autoresearch/model.py`

Evaluation:

- train split for fitting
- validation split for model comparison
- test split reserved unless explicitly requested

Main Gonzaga-only validation accuracy:

- `0.643836`

## Exploratory vs Final Artifacts

### Final / Canonical

- Gonzaga locked interaction-logistic model:
  - `experiments/gonzaga_autoresearch/model.py`
  - `experiments/gonzaga_autoresearch/results.tsv`
  - `experiments/gonzaga_autoresearch/experiment_summary.md`
- Gonzaga diagnostics:
  - `results/gonzaga/diagnostics/`
- Gonzaga error analysis:
  - `results/gonzaga/error_analysis/`
- Closed Northwestern+Gonzaga robustness:
  - `experiments/northwestern_gonzaga_closed/results/closed_experiment_table.csv`
  - `experiments/northwestern_gonzaga_closed/results/generalization_experiment_table.csv`
  - `experiments/northwestern_gonzaga_closed/logs/generalization_summary.md`
- Retrospective explanatory model:
  - `experiments/northwestern_gonzaga_closed/results/explanatory_experiment_table.csv`
  - `experiments/northwestern_gonzaga_closed/results/explanatory_model_coefficients.csv`
  - `experiments/northwestern_gonzaga_closed/logs/explanatory_model_summary.md`

### Exploratory / Historical

- `archive/semantic_feature_ablation/`: highlighted evidence semantic feature ablation.
- `archive/llm_dry_run/`: LLM prompt/scoring infrastructure attempts.
- `archive/broad_feature_search/`: broader non-leaky feature search.
- `results/gonzaga/legacy_baseline_model/`: earlier baseline/parser artifacts.
- `experiments/northwestern_gonzaga_closed/scripts/*_vF.py`: closed copied parser utilities preserved for reproducibility.

These artifacts should not be deleted. They explain how the project narrowed its scope and why the final model is modest and interpretable.

## Output Locations

### Gonzaga Outputs

- Baseline metrics and coefficients: `results/gonzaga/baseline_runs/`
- Parser outputs: `results/gonzaga/parser_output/`
- Diagnostics: `results/gonzaga/diagnostics/`
- Error analysis: `results/gonzaga/error_analysis/`

### AutoResearch Outputs

- Main experiment table: `experiments/gonzaga_autoresearch/results.tsv`
- Performance image: `experiments/gonzaga_autoresearch/performance.png`
- Summary: `experiments/gonzaga_autoresearch/experiment_summary.md`

### Closed Experiment Outputs

- Closed datasets: `experiments/northwestern_gonzaga_closed/data_processed/`
- Closed diagnostics: `experiments/northwestern_gonzaga_closed/diagnostics/`
- Closed results: `experiments/northwestern_gonzaga_closed/results/`
- Closed logs: `experiments/northwestern_gonzaga_closed/logs/`

### Report Figures

- Metric trajectory plot: `reports/figures/metric_over_time_plot.png`
- Metric trajectory source data: `reports/figures/metric_over_time_data.csv`
- Metric trajectory caption: `reports/figures/metric_over_time_caption.md`

## How to Reproduce the Main Pipeline

Install dependencies:

```powershell
pip install -r requirements.txt
```

If `pip` is unavailable:

```powershell
python -m pip install -r requirements.txt
```

### 1. Reproduce Gonzaga Dataset Diagnostics

```powershell
python "src/diagnostics/dataset_diagnostics.py"
python "src/diagnostics/check_dataset_balance.py"
python "src/diagnostics/inspect_feature_coverage.py"
```

Expected outputs are written under:

- `results/gonzaga/diagnostics/`

### 2. Reproduce Baseline v3

```powershell
python "src/modeling/baseline_v3_structured_numeric.py"
```

Expected outputs:

- `results/gonzaga/baseline_runs/baseline_v3_structured_numeric_metrics.csv`
- `results/gonzaga/baseline_runs/baseline_v3_structured_numeric_coefficients.csv`

### 3. Reproduce the Locked Gonzaga AutoResearch Model

```powershell
python "experiments/gonzaga_autoresearch/run.py" "baseline logistic" --baseline
python "experiments/gonzaga_autoresearch/run.py" "locked interaction logistic C=0.5"
```

Expected output:

- `experiments/gonzaga_autoresearch/results.tsv`

The locked model is defined in:

- `experiments/gonzaga_autoresearch/model.py`

### 4. Reproduce Locked Validation Predictions

```powershell
python "src/modeling/export_locked_validation_predictions.py"
```

Expected outputs:

- `results/gonzaga/error_analysis/validation_predictions.csv`
- `results/gonzaga/error_analysis/validation_misclassifications.csv`

### 5. Reproduce Closed Northwestern+Gonzaga Robustness

The closed experiment is intentionally isolated. It should write only inside `experiments/northwestern_gonzaga_closed/`.

```powershell
python "experiments/northwestern_gonzaga_closed/scripts/preview_northwestern_doc_selection.py"
python "experiments/northwestern_gonzaga_closed/scripts/run_closed_experiment.py" --batch-size 100
python "experiments/northwestern_gonzaga_closed/scripts/run_generalization_experiments.py"
```

Expected outputs include:

- `experiments/northwestern_gonzaga_closed/results/closed_experiment_table.csv`
- `experiments/northwestern_gonzaga_closed/results/generalization_experiment_table.csv`
- `experiments/northwestern_gonzaga_closed/results/tournament_holdout_results.csv`
- `experiments/northwestern_gonzaga_closed/logs/closed_experiment_summary.md`
- `experiments/northwestern_gonzaga_closed/logs/generalization_summary.md`

### 6. Reproduce Paired Round Check

```powershell
python "experiments/northwestern_gonzaga_closed/scripts/run_paired_round_experiment.py"
```

Expected outputs:

- `experiments/northwestern_gonzaga_closed/data_processed/paired_round_dataset_closed_with_split.csv`
- `experiments/northwestern_gonzaga_closed/results/paired_round_experiment_table.csv`
- `experiments/northwestern_gonzaga_closed/logs/paired_round_experiment_summary.md`

### 7. Reproduce Retrospective Explanatory Models

```powershell
python "experiments/northwestern_gonzaga_closed/scripts/run_ranking_prior_experiment.py"
python "experiments/northwestern_gonzaga_closed/scripts/run_explanatory_strength_model.py"
```

Expected outputs:

- `experiments/northwestern_gonzaga_closed/results/ranking_prior_experiment_table.csv`
- `experiments/northwestern_gonzaga_closed/results/explanatory_experiment_table.csv`
- `experiments/northwestern_gonzaga_closed/results/explanatory_model_coefficients.csv`
- `experiments/northwestern_gonzaga_closed/logs/explanatory_model_summary.md`

Again, these are retrospective explanatory models, not clean real-time prediction models.

## What Not to Reinterpret

- Do not treat Shirley/team-strength variables as clean predictive features.
- Do not treat archived semantic or LLM artifacts as part of the locked final model.
- Do not treat cross-tournament accuracy drop as a pipeline failure; it is a substantive finding about distribution shift.
- Do not treat old numbered paths in historical logs as current canonical paths.

## Main Takeaway

The project found modest but real predictive signal in parser-derived debate structure for Gonzaga-only validation. Interaction terms improved the structured baseline, but more flexible models and broader feature searches did not provide a stable final direction. When Northwestern was added, performance dropped sharply, showing weak cross-tournament generalization. Retrospective Shirley/team-strength variables explained much more, supporting the conclusion that latent team strength dominates the current parser-derived speech features.
