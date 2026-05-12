# Reproducibility Audit

## Current Reproducibility Status

The project is partly reproducible, but the workflow is spread across numbered folders, root scripts, AutoResearch folders, and closed experiment scripts. The strongest reproducibility pattern is the closed Northwestern+Gonzaga experiment, which contains its own copied scripts, data inputs, results, diagnostics, and logs.

The weakest reproducibility areas are:

- duplicated scripts and outputs,
- hardcoded local paths,
- stale README language,
- inconsistent naming such as `vTemp`,
- untracked/generated artifacts mixed with source scripts,
- raw data dependencies that are large and local.

## Dependencies

Current `requirements.txt` contains:

```text
numpy
pandas
python-docx
scikit-learn
pillow
```

This matches the main parser, diagnostics, and modeling scripts.

Potential dependency issues:

- Some scripts assume `sklearn` is installed but do not fail gracefully.
- LLM scripts may require additional API/client dependencies if revived.
- Plot/image diagnostics use Pillow, not matplotlib.
- README currently says there is no `requirements.txt`, which is outdated.

Recommendation:

- Update README to instruct:
  - `pip install -r requirements.txt`
  - then run scripts from quoted repo root paths.
- If LLM work remains archived, keep API dependencies out of the main requirements.

## Required Scripts for Final Reproduction

### Clean Gonzaga Predictive Workflow

Required:

- `src/parsing/debate_doc_parser.py`
- `src/parsing/count_tournament_disclosures.py`
- `src/parsing/select_tournament_docs.py`
- `src/parsing/build_gonzaga_dataset.py`
- `src/modeling/baseline_v3_structured_numeric.py`
- `experiments/gonzaga_autoresearch/prepare.py`
- `experiments/gonzaga_autoresearch/model.py`
- `experiments/gonzaga_autoresearch/run.py`

Core data:

- `data/processed/gonzaga_speech_dataset_v1.csv`

Core outputs:

- `experiments/gonzaga_autoresearch/results.tsv`
- `experiments/gonzaga_autoresearch/experiment_summary.md`
- `results/gonzaga/baseline_runs/baseline_v3_structured_numeric_metrics.csv`
- `results/gonzaga/error_analysis/validation_predictions.csv`

### Closed Northwestern+Gonzaga Workflow

Required:

- `experiments/northwestern_gonzaga_closed/scripts/preview_northwestern_doc_selection.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_closed_experiment.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_generalization_experiments.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_paired_round_experiment.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_ranking_prior_experiment.py`
- `experiments/northwestern_gonzaga_closed/scripts/run_explanatory_strength_model.py`

Core data:

- `experiments/northwestern_gonzaga_closed/data_processed/combined_speech_dataset_closed_with_split.csv`
- `experiments/northwestern_gonzaga_closed/data_processed/paired_round_dataset_closed_with_split.csv`
- `experiments/northwestern_gonzaga_closed/data_raw/Shirley_Rankings.csv`

Core outputs:

- `results/closed_experiment_table.csv`
- `results/generalization_experiment_table.csv`
- `results/paired_round_experiment_table.csv`
- `results/ranking_prior_experiment_table.csv`
- `results/explanatory_experiment_table.csv`

## Obsolete or Secondary Scripts

Likely archive after final tables are extracted:

- `archive/deprecated_scripts/baseline_v4_side_features.py`
- `archive/deprecated_scripts/baseline_v5_density_features.py`
- `archive/llm_dry_run/scripts/baseline_v6_llm_features.py`
- `archive/llm_dry_run/scripts/build_llm_argument_features_v6.py`
- `archive/llm_dry_run/scripts/score_llm_argument_features_v6.py`
- `archive/llm_dry_run/scripts/inspect_llm_prompts_v6.py`
- `archive/semantic_feature_ablation/scripts/build_semantic_highlight_features_v1.py`
- `archive/broad_feature_search/scripts/run_nonleaky_feature_search.py`

Reason:

- These are important historically but not part of the final clean reproduction path.
- They should remain accessible under `archive/experiments/` or `experiments/gonzaga_archived/`.

## Hardcoded Paths

Observed issues:

- Several scripts rely on current working directory or relative paths with numbered folders.
- Closed experiment scripts use repo-root discovery via `Path(__file__).resolve().parents[3]`, which is better but still assumes folder depth.
- Older scripts load CSVs relative to working directory.
- Paths contain spaces and dashes, so command examples must quote paths.

Recommendation:

- Standardize all active scripts around:
  - `Path(__file__).resolve()`
  - explicit repo root calculation
  - argparse overrides for data paths
- Add a top-level `config/project_paths.py` or `src/project_paths.py` later if reorganizing.

## Duplicated Logic

Duplicated areas:

- Tournament token extraction exists in:
  - `src/parsing/count_tournament_disclosures.py`
  - `src/parsing/select_tournament_docs.py`
  - closed preview script
- Logistic evaluation repeated across baseline scripts, AutoResearch scripts, and closed experiment scripts.
- Ranking/team-code normalization repeated in ranking prior and explanatory scripts.
- Manual interaction feature creation repeated in multiple scripts.

Recommendation:

- Later create reusable modules:
  - `src/tournament_selection.py`
  - `src/features.py`
  - `src/evaluation.py`
  - `src/ranking_linkage.py`
- Do not refactor before final report unless time allows; the current scripts are inspectable and already produce artifacts.

## Fragile Joins and Parsing Assumptions

Parser/join assumptions:

- Team codes are inferred from filenames and matched to Tabroom `Entry` rows.
- Some team-code normalization can misinfer schools, shown by Northwestern join failures such as Emory files becoming Michigan-coded in failure rows.
- Opponent matching for relative features had duplicate keys and required deterministic collapse.
- Pair-level dataset dropped 331 matchup groups because only one side was available.

Risks:

- Filename variation strongly affects parser and join success.
- `opponent` labels may include `- ONLINE`, which needs normalization.
- Tabroom CSV cells are complex text blocks and parsing assumes `W/L`, side, points, opponent, judge patterns.

Recommendation:

- For final presentation, explicitly list parser/join limitations.
- Preserve `join_failures.csv` and duplicate-handling diagnostics.
- Do not claim full round coverage.

## Files That Should Be Versioned or Renamed

Should be versioned/preserved if size and course rules allow:

- `data/processed/gonzaga_speech_dataset_v1.csv`
- `data/processed/gonzaga_speech_dataset_v2_with_text.csv`
- `results/gonzaga/baseline_runs/*.csv`
- `experiments/gonzaga_autoresearch/results.tsv`
- `experiments/gonzaga_autoresearch/experiment_summary.md`
- closed experiment result CSVs and Markdown logs

Rename suggestions:

- `src/parsing/build_gonzaga_dataset.py`
- `src/parsing/debate_doc_parser.py`
- `src/parsing/count_tournament_disclosures.py`
- `src/parsing/select_tournament_docs.py`

Do not rename until imports/scripts are updated and rerun.

## Generated/Temporary Files

Archive or ignore:

- `__pycache__/`
- `experiments/gonzaga_autoresearch/performance.png` if regenerated automatically
- row-level parse batches under closed experiment if aggregate CSVs are sufficient
- old LLM prompt files if not used in final report

## README Problems

Current README issues:

- It still frames the project primarily as LLM argument-quality prediction.
- It says no `requirements.txt` exists, but `requirements.txt` now exists.
- It does not foreground the final discovered story:
  - modest Gonzaga-only structured signal,
  - weak cross-tournament generalization,
  - latent team strength dominates retrospective explanation.

Recommended README sections:

1. Project question.
2. Final result summary.
3. Clean predictive vs retrospective explanatory distinction.
4. Reproduce Gonzaga-only model.
5. Reproduce closed Northwestern+Gonzaga robustness checks.
6. Important files.
7. Known limitations.
8. Archive/deprecated experiments.

## Reproducibility Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Raw `.docx` data may be absent or uncommitted | High | Preserve processed datasets and document raw-data expectations. |
| Hardcoded/local paths | Medium | Use repo-relative paths and argparse in final scripts. |
| Duplicate outputs | Medium | Choose canonical output folders. |
| Stale README | High | Update after restructuring plan is accepted. |
| LLM pipeline incomplete | Low for final, high if revived | Archive or label as incomplete. |
| Ranking variables are leaky for prediction | High | Keep in explanatory section only. |

## Reproducibility Checklist Before Final Submission

- Confirm `requirements.txt` installs all non-LLM dependencies.
- Choose canonical scripts and mark deprecated scripts.
- Update README.
- Add a one-command or numbered reproduction guide.
- Ensure final tables cite exact CSV paths.
- Keep test set untouched unless final evaluation is explicitly performed.
- Separate predictive and explanatory claims in all docs.
