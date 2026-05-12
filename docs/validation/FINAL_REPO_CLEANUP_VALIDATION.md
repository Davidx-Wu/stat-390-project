# Final Repository Cleanup Validation

Date: 2026-05-06

## Scope

- Final organization pass focused on chronology and legibility.
- No experiments were rerun.
- No model logic was changed.
- No model result values or dataset rows were modified.
- No test-set artifacts were evaluated or regenerated.

## Final Root Folder List

Canonical root folders:

- `archive/`
- `data/`
- `experiments/`
- `logs/`
- `reports/`
- `results/`
- `src/`

Key root docs retained:

- `README.md`
- `PROJECT_TIMELINE.md`
- `PROJECT_AUDIT_SUMMARY.md`
- `REPRODUCIBILITY_AUDIT.md`
- `CANONICAL_WORKFLOWS.md`
- `REPO_MIGRATION_PLAN.md`
- `PATH_CLEANUP_PLAN.md`
- `PATH_CLEANUP_VALIDATION.md`
- `POST_RESTRUCTURE_VALIDATION.md`
- `PROPOSED_REPO_STRUCTURE.md`

## Experiment Stage Mapping

| Stage | Folder | Purpose |
| --- | --- | --- |
| 1 | `experiments/stage_1_gonzaga_predictive/` | Gonzaga-only predictive baselines and locked interaction-logistic workflow. |
| 2 | `experiments/stage_2_feature_ablation/` | Feature coverage, v3/v4/v5 ablations, semantic/LLM/broad-search diagnostics, and error analysis. |
| 3 | `experiments/stage_3_cross_tournament/` | Closed Northwestern+Gonzaga robustness and distribution-shift analysis. |
| 4 | `experiments/stage_4_paired_rounds/` | Pair-level Aff-vs-Neg unit-of-analysis experiment. |
| 5 | `experiments/stage_5_explanatory_strength/` | Retrospective Shirley/team-strength explanatory modeling. |

Runnable canonical experiment folders:

- `experiments/gonzaga_autoresearch/`
- `experiments/northwestern_gonzaga_closed/`

## Archived Legacy Folders

Archived under `archive/legacy_root_structure/` where possible:

- `2 -- notebooks/`
- `3 -- src/`
- `5 -- logs/`
- `6 -- evaluation/`
- `7 -- reports/`
- `8 -- data cleaning test lab/`
- `program.md`

Other archived experiment material:

- `archive/deprecated_scripts/`
- `archive/llm_dry_run/`
- `archive/semantic_feature_ablation/`
- `archive/broad_feature_search/`
- `archive/data_cleaning_test_lab/`
- `archive/demo_autoresearch_reference/`

## Compatibility Exceptions

Final lock-aware cleanup pass completed after the locked files were released. The remaining legacy root folders were moved into:

- `archive/legacy_root_structure/remaining_legacy_root_2026_05_06/`

Archived legacy leftovers:

- `archive/legacy_root_structure/remaining_legacy_root_2026_05_06/1 -- data/`
- `archive/legacy_root_structure/remaining_legacy_root_2026_05_06/4 -- results/`
- `archive/legacy_root_structure/remaining_legacy_root_2026_05_06/6 -- experiments/`
- `archive/legacy_root_structure/remaining_legacy_root_2026_05_06/gonzaga_dataset_output/`

Canonical copies exist for the relevant artifacts:

- `data/raw/7 -- Tournament Counts/tournament_disclosure_counts.csv`
- `data/raw/8 -- Keep Only Tournament Docs/ndtceda25/tournament_disclosure_counts.csv`
- `data/raw/9 -- Build Gonzaga Dataset/Gonzaga_Tabroom-prelims_table.csv`
- `results/gonzaga/error_analysis/validation_predictions.csv`
- `results/gonzaga/error_analysis/validation_misclassifications.csv`
- `results/gonzaga/parser_output/argument_audit_all.csv`
- `results/gonzaga/parser_output/card_audit_all.csv`
- `experiments/northwestern_gonzaga_closed/`

Active scripts were updated to use canonical paths rather than the numbered root folders.

No manual-removal checklist is required; the target root cleanup succeeded.

## Documentation Updates

Updated:

- `README.md`
- `PROJECT_TIMELINE.md`
- `CANONICAL_WORKFLOWS.md`
- `PROJECT_AUDIT_SUMMARY.md`

Chronology is now represented by:

- staged experiment folders under `experiments/`
- `PROJECT_TIMELINE.md`
- logs under `logs/` and closed experiment log folders
- Git history

## Validation Commands

Ran:

```powershell
git status --short
git diff --stat
```

Ran path existence checks for:

- stage README files
- canonical Gonzaga AutoResearch scripts
- canonical closed experiment script
- canonical raw tournament-count file
- canonical Gonzaga Tabroom file
- canonical processed Gonzaga dataset
- canonical validation prediction file

All checked canonical paths existed.

Ran syntax-only validation with bundled workspace Python:

```powershell
& "C:\Users\thatd\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m py_compile ...
```

Validated:

- `src/project_paths.py`
- canonical parsing scripts
- canonical modeling scripts
- canonical diagnostics scripts
- `experiments/gonzaga_autoresearch/`
- `experiments/northwestern_gonzaga_closed/scripts/`

`py_compile` completed successfully.

## Final Notes

- No modeling experiments were run.
- No result CSV values were edited.
- No test-set outputs were touched.
- Remaining numbered root folders should be treated as locked compatibility leftovers, not canonical workflow locations.
