# Path Cleanup Validation

Date: 2026-05-06

## Scope

- Performed a path-only cleanup pass.
- Did not rerun modeling experiments.
- Did not modify model result values, dataset rows, or evaluation outputs.
- Used `git mv` for tracked files where possible.
- Preserved legacy/locked copies rather than deleting them.

## Canonical Paths Created/Used

- `data/raw/`
- `data/processed/`
- `src/parsing/`
- `src/modeling/`
- `src/diagnostics/`
- `experiments/gonzaga_autoresearch/`
- `experiments/northwestern_gonzaga_closed/`
- `results/gonzaga/`
- `logs/`
- `reports/`
- `archive/`

## Moved/Renamed Path Groups

- Active parsing scripts moved from `3 -- src/` to `src/parsing/`.
- Active modeling scripts moved from `3 -- src/` to `src/modeling/`.
- Active diagnostics scripts moved from `3 -- src/` and `6 -- evaluation/` to `src/diagnostics/`.
- Gonzaga processed datasets moved from `4 -- results/processed_datasets/` to `data/processed/`.
- Gonzaga baseline and diagnostics outputs moved from `4 -- results/` to `results/gonzaga/`.
- Gonzaga AutoResearch moved from `debate-autoresearch/` to `experiments/gonzaga_autoresearch/`.
- Logs moved from `5 -- logs/` to `logs/`.
- Deprecated LLM, semantic, broad-search, demo, and data-cleaning materials moved or copied under `archive/`.
- Closed Northwestern+Gonzaga canonical copy retained under `experiments/northwestern_gonzaga_closed/`.

## Deferred Locked Legacy Copies

The following legacy files or folders could not be fully removed/moved because files were locked by another process. Canonical copies were created where needed:

- `gonzaga_dataset_output/argument_audit_all.csv`
- `gonzaga_dataset_output/card_audit_all.csv`
- `4 -- results/error_analysis/validation_predictions.csv`
- `4 -- results/error_analysis/validation_misclassifications.csv`
- one residual file under `6 -- experiments/northwestern_gonzaga_closed_experiment/`

These are legacy leftovers only; canonical copies exist at:

- `results/gonzaga/parser_output/argument_audit_all.csv`
- `results/gonzaga/parser_output/card_audit_all.csv`
- `results/gonzaga/error_analysis/validation_predictions.csv`
- `results/gonzaga/error_analysis/validation_misclassifications.csv`
- `experiments/northwestern_gonzaga_closed/`

## Path Reference Updates

Updated path references in:

- `README.md`
- `CANONICAL_WORKFLOWS.md`
- `REPO_MIGRATION_PLAN.md`
- `PROJECT_AUDIT_SUMMARY.md`
- `PROJECT_TIMELINE.md`
- `REPRODUCIBILITY_AUDIT.md`
- `PROPOSED_REPO_STRUCTURE.md`
- `POST_RESTRUCTURE_VALIDATION.md`
- canonical scripts under `src/`
- canonical AutoResearch scripts under `experiments/gonzaga_autoresearch/`
- closed experiment scripts under `experiments/northwestern_gonzaga_closed/scripts/`

## Syntax Validation

`python` and `py` were not available on the shell PATH, so validation used the bundled workspace Python:

```powershell
& "C:\Users\thatd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m py_compile ...
```

Passed for:

- `src/project_paths.py`
- all canonical parsing scripts in `src/parsing/`
- all canonical modeling scripts in `src/modeling/`
- all canonical diagnostics scripts in `src/diagnostics/`
- `experiments/gonzaga_autoresearch/prepare.py`
- `experiments/gonzaga_autoresearch/model.py`
- `experiments/gonzaga_autoresearch/run.py`
- closed experiment scripts in `experiments/northwestern_gonzaga_closed/scripts/`

## Canonical Artifact Existence Check

Confirmed present:

- `data/raw/Gonzaga_Tabroom-prelims_table.csv`
- `data/raw/9 -- Build Gonzaga Dataset/gonzaga_dataset_output/Shirley_Rankings.csv`
- `data/processed/gonzaga_speech_dataset_v1.csv`
- `data/processed/gonzaga_speech_dataset_v2_with_text.csv`
- `results/gonzaga/baseline_runs/baseline_v3_structured_numeric_metrics.csv`
- `results/gonzaga/baseline_runs/baseline_v3_structured_numeric_coefficients.csv`
- `results/gonzaga/diagnostics/feature_coverage_summary.csv`
- `results/gonzaga/error_analysis/validation_predictions.csv`
- `results/gonzaga/error_analysis/validation_misclassifications.csv`
- `results/gonzaga/parser_output/card_audit_all.csv`
- `results/gonzaga/parser_output/argument_audit_all.csv`
- `experiments/gonzaga_autoresearch/prepare.py`
- `experiments/gonzaga_autoresearch/model.py`
- `experiments/gonzaga_autoresearch/run.py`
- `experiments/northwestern_gonzaga_closed/data_processed/combined_speech_dataset_closed_with_split.csv`
- `experiments/northwestern_gonzaga_closed/results/closed_experiment_table.csv`
- `experiments/northwestern_gonzaga_closed/results/explanatory_experiment_table.csv`

## Notes

- No modeling command was executed.
- No test-set evaluation was run.
- No result values were changed.
- `py_compile` created `__pycache__/` folders as normal syntax-validation byproducts.
