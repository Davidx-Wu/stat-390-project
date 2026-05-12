# Path Cleanup Plan

## Scope

This is a path-only cleanup. It renames/moves files into the final canonical structure and updates references. It does not change model code logic, result values, datasets, or experiment outputs.

## Rules

- No permanent deletion.
- No experiment reruns.
- No result-value changes.
- No test-set use.
- Use `git mv` for tracked files when possible.
- Preserve deprecated work under `archive/`.
- Preserve the experimental story and reproducibility trail.

## Final Top-Level Structure

```text
data/raw/
data/processed/
src/parsing/
src/modeling/
src/diagnostics/
experiments/gonzaga_autoresearch/
experiments/northwestern_gonzaga_closed/
results/gonzaga/
logs/
reports/
archive/
```

## Move/Rename Mapping

### Active Source Scripts

| Old Path | New Path | Rationale | Risk |
|---|---|---|---|
| `3 -- src/1 -- debate_doc_parser_vF.py` | `src/parsing/debate_doc_parser.py` | Remove numbering/version suffix; parser is canonical. | Medium |
| `3 -- src/2 -- count_tournament_disclosures_vF.py` | `src/parsing/count_tournament_disclosures.py` | Remove numbering/version suffix. | Low |
| `3 -- src/3 -- keep_only_tournament_docs_vF.py` | `src/parsing/select_tournament_docs.py` | Clearer action name. | Low |
| `3 -- src/4 -- build_gonzaga_dataset_vTemp.py` | `src/parsing/build_gonzaga_dataset.py` | Remove `vTemp`; builder is canonical. | Medium |
| `3 -- src/5 -- baseline_round_model.py` | `archive/deprecated_scripts/legacy_baseline_round_model.py` | Superseded by v3/AutoResearch workflows. | Low |
| `3 -- src/baseline_v3_structured_numeric.py` | `src/modeling/baseline_v3_structured_numeric.py` | Canonical clean structured baseline. | Low |
| `3 -- src/build_text_enriched_dataset_v2.py` | `src/parsing/build_text_enriched_dataset_v2.py` | Dataset-building utility. | Low |
| `3 -- src/check_dataset_balance.py` | `src/diagnostics/check_dataset_balance.py` | Diagnostics. | Low |
| `3 -- src/dataset_diagnostics.py` | `src/diagnostics/dataset_diagnostics.py` | Diagnostics. | Low |
| `3 -- src/inspect_feature_coverage.py` | `src/diagnostics/inspect_feature_coverage.py` | Diagnostics. | Low |
| `3 -- src/export_locked_validation_predictions.py` | `src/modeling/export_locked_validation_predictions.py` | Error-analysis prediction export. | Low |

### Deprecated/Archived Source Scripts

| Old Path | New Path | Rationale | Risk |
|---|---|---|---|
| `3 -- src/baseline_v4_side_features.py` | `archive/deprecated_scripts/baseline_v4_side_features.py` | Failed ablation. | Low |
| `3 -- src/baseline_v5_density_features.py` | `archive/deprecated_scripts/baseline_v5_density_features.py` | Failed ablation. | Low |
| `3 -- src/baseline_v6_llm_features.py` | `archive/llm_dry_run/scripts/baseline_v6_llm_features.py` | Incomplete LLM pipeline. | Low |
| `3 -- src/build_llm_argument_features_v6.py` | `archive/llm_dry_run/scripts/build_llm_argument_features_v6.py` | LLM dry-run/prep. | Low |
| `3 -- src/score_llm_argument_features_v6.py` | `archive/llm_dry_run/scripts/score_llm_argument_features_v6.py` | LLM scoring attempt. | Low |
| `3 -- src/inspect_llm_prompts_v6.py` | `archive/llm_dry_run/scripts/inspect_llm_prompts_v6.py` | LLM prompt inspection. | Low |
| `3 -- src/build_semantic_highlight_features_v1.py` | `archive/semantic_feature_ablation/scripts/build_semantic_highlight_features_v1.py` | Failed semantic ablation. | Low |
| `3 -- src/run_nonleaky_feature_search.py` | `archive/broad_feature_search/scripts/run_nonleaky_feature_search.py` | Broad supplementary feature search. | Low |

### Input Data

| Old Path | New Path | Rationale | Risk |
|---|---|---|---|
| `3 -- src/Gonzaga_Tabroom-prelims_table.csv` | `data/raw/Gonzaga_Tabroom-prelims_table.csv` | Raw/input CSV should not live in source folder. | Low |
| `1 -- data/processed/Georgetown_Tabroom-prelims_table.csv` | `data/processed/Georgetown_Tabroom-prelims_table.csv` | Remove numbered path. | Low |

### Results and Logs

| Old Path | New Path | Rationale | Risk |
|---|---|---|---|
| `4 -- results/baseline_runs/` | `results/gonzaga/baseline_runs/` | Canonical Gonzaga baseline results. | Low |
| `4 -- results/diagnostics/` | `results/gonzaga/diagnostics/` | Canonical Gonzaga diagnostics. | Low |
| `4 -- results/error_analysis/` | `results/gonzaga/error_analysis/` | Canonical error analysis. | Low |
| `4 -- results/processed_datasets/` | `data/processed/` | Processed datasets belong under data. | Medium |
| `4 -- results/llm_features/` | `archive/llm_dry_run/results/` | Incomplete LLM artifacts. | Low |
| `4 -- results/semantic_features/` | `archive/semantic_feature_ablation/results/` | Failed ablation artifacts. | Low |
| `4 -- results/feature_search/` | `archive/broad_feature_search/results/` | Supplementary feature search. | Low |
| `4 -- results/1 -- Baseline Model/` | `results/gonzaga/legacy_baseline_model/` | Legacy baseline artifacts. | Low |
| `gonzaga_dataset_output/` | `results/gonzaga/parser_output/` | Parser batch output. | Low |
| `5 -- logs/` | `logs/` | Final canonical logs path. | Low |

### Experiments and Reports

| Old Path | New Path | Rationale | Risk |
|---|---|---|---|
| `debate-autoresearch/` | `experiments/gonzaga_autoresearch/` | Canonical experiment path. | Medium |
| `6 -- experiments/northwestern_gonzaga_closed_experiment/` | `experiments/northwestern_gonzaga_closed/` | Canonical closed experiment path. | Medium |
| `6 -- evaluation/generate_join_failure_candidates.py` | `src/diagnostics/generate_join_failure_candidates.py` | Evaluation helper is diagnostic source code. | Low |
| `7 -- reports/` | `reports/` | Canonical reports path. | Low |
| `demo-autoresearch` | `archive/demo_autoresearch/` | Reference template, not project result. | Low |
| `8 -- data cleaning test lab/` | `archive/data_cleaning_test_lab/` | Deprecated parser lab. | Medium |

## Reference Updates Required

Update references in:

- `README.md`
- `CANONICAL_WORKFLOWS.md`
- `REPO_MIGRATION_PLAN.md`
- `PROJECT_AUDIT_SUMMARY.md`
- `PROJECT_TIMELINE.md`
- `REPRODUCIBILITY_AUDIT.md`
- `PROPOSED_REPO_STRUCTURE.md`
- active scripts moved into `src/`
- closed experiment scripts that compute repo root by path depth

## Validation Plan

- Run `python -m py_compile` on canonical scripts only.
- Check canonical CSV/result paths exist.
- Do not run modeling experiments.
- Write `PATH_CLEANUP_VALIDATION.md`.
