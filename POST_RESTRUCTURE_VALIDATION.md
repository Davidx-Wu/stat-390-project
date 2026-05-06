# Post-Restructure Validation

## Validation Scope

This validation checked the first controlled cleanup/reorganization pass. It did not rerun modeling experiments and did not evaluate any test set.

The pass was intentionally conservative:

- old paths were preserved,
- canonical mirrors were copied into cleaner folders,
- deprecated work was copied into `archive/`,
- active scripts were not renamed,
- no files were permanently deleted.

## Commands Run

### Python Syntax Validation

The following command compiled canonical scripts without executing experiments:

```powershell
python -m py_compile `
  "src/project_paths.py" `
  "src/parsing/debate_doc_parser.py" `
  "src/parsing/build_gonzaga_dataset.py" `
  "experiments/gonzaga_autoresearch/prepare.py" `
  "experiments/gonzaga_autoresearch/model.py" `
  "experiments/gonzaga_autoresearch/run.py" `
  "experiments/northwestern_gonzaga_closed/scripts/run_closed_experiment.py" `
  "experiments/northwestern_gonzaga_closed/scripts/run_generalization_experiments.py" `
  "experiments/northwestern_gonzaga_closed/scripts/run_paired_round_experiment.py" `
  "experiments/northwestern_gonzaga_closed/scripts/run_ranking_prior_experiment.py" `
  "experiments/northwestern_gonzaga_closed/scripts/run_explanatory_strength_model.py"
```

Result: success.

## Canonical Path Checks

The following important paths exist after restructuring:

| Path | Status |
|---|---|
| `REPO_MIGRATION_PLAN.md` | exists |
| `CANONICAL_WORKFLOWS.md` | exists |
| `README.md` | exists and updated |
| `src/project_paths.py` | exists |
| `data/processed/gonzaga_speech_dataset_v1.csv` | exists |
| `data/processed/gonzaga_speech_dataset_v2_with_text.csv` | exists |
| `data/processed/closed_northwestern_gonzaga/combined_speech_dataset_closed_with_split.csv` | exists |
| `data/processed/closed_northwestern_gonzaga/paired_round_dataset_closed_with_split.csv` | exists |
| `results/gonzaga/baseline_runs/baseline_v3_structured_numeric_metrics.csv` | exists |
| `results/gonzaga/diagnostics/feature_coverage_summary.csv` | exists |
| `results/gonzaga/error_analysis/validation_predictions.csv` | exists |
| `experiments/gonzaga_autoresearch/results.tsv` | exists |
| `experiments/northwestern_gonzaga_closed/results/closed_experiment_table.csv` | exists |
| `experiments/northwestern_gonzaga_closed/results/explanatory_experiment_table.csv` | exists |
| `archive/semantic_feature_ablation/scripts/build_semantic_highlight_features_v1.py` | exists |
| `archive/llm_dry_run/scripts/build_llm_argument_features_v6.py` | exists |
| `archive/broad_feature_search/scripts/run_nonleaky_feature_search.py` | exists |
| `archive/demo_autoresearch/run.py` | exists |
| `archive/data_cleaning_test_lab/` | exists |

## Migration Actions Completed

Created new planning/documentation files:

- `REPO_MIGRATION_PLAN.md`
- `CANONICAL_WORKFLOWS.md`
- `POST_RESTRUCTURE_VALIDATION.md`

Updated:

- `README.md`

Created helper:

- `src/project_paths.py`

Created cleaner mirror folders:

- `data/processed/`
- `data/processed/closed_northwestern_gonzaga/`
- `results/gonzaga/baseline_runs/`
- `results/gonzaga/diagnostics/`
- `results/gonzaga/error_analysis/`
- `experiments/gonzaga_autoresearch/`
- `experiments/northwestern_gonzaga_closed/`

Created archive folders and copied deprecated/supplementary work:

- `archive/semantic_feature_ablation/`
- `archive/llm_dry_run/`
- `archive/broad_feature_search/`
- `archive/demo_autoresearch/`
- `archive/data_cleaning_test_lab/`
- `archive/deprecated_scripts/`

## What Was Not Changed

- No model outputs were edited.
- No result values were changed.
- No experiments were rerun.
- No files were permanently deleted.
- No active scripts were renamed.
- Original numbered folders remain intact.
- Original Gonzaga-only paths remain intact.
- Original closed Northwestern+Gonzaga experiment path remains intact.

## Known Remaining Issues

- The repo now temporarily contains duplicate mirrors of key artifacts. This is intentional for safety during the first pass.
- The old numbered structure and new cleaner structure coexist.
- Active scripts still mostly point to old paths.
- `archive/deprecated_scripts/` is currently a placeholder and can be populated later if old source scripts are moved rather than copied.
- `__pycache__/` folders still exist and should be ignored/cleaned later.
- Raw data policy still needs final decision before grading/submission.

## Recommended Next Step

Do one of the following in a separate cleanup step:

1. Keep the current hybrid structure for grading and simply use the new README/audit docs as navigation.
2. Fully migrate active scripts into `src/`, update imports/paths, and rerun only lightweight validation commands.
3. Create a final release branch/tag after deciding whether raw data and mirrored outputs should be tracked.
