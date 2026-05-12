# Proposed Repository Structure

## Goals

The final structure should make the project easier to grade, reproduce, and present. It should separate raw data, processed data, source code, experiments, results, reports, and archived work.

The main principle is: active workflow first, archive second.

## Proposed Final Folder Tree

```text
stat-390-project/
  README.md
  requirements.txt
  AGENTS.md
  PROJECT_AUDIT_SUMMARY.md
  PROJECT_TIMELINE.md
  REPRODUCIBILITY_AUDIT.md
  PROPOSED_REPO_STRUCTURE.md

  data/
    raw/
      README.md
      # raw docs and Tabroom CSVs, possibly untracked
    processed/
      gonzaga_speech_dataset_v1.csv
      gonzaga_speech_dataset_v2_with_text.csv
      closed_northwestern_gonzaga/
        combined_speech_dataset_closed_with_split.csv
        paired_round_dataset_closed_with_split.csv

  src/
    parsing/
      debate_doc_parser.py
      build_gonzaga_dataset.py
      count_tournament_disclosures.py
      select_tournament_docs.py
    features/
      feature_transforms.py
      ranking_linkage.py
    modeling/
      baseline_v3_structured_numeric.py
      export_validation_predictions.py
    diagnostics/
      dataset_diagnostics.py
      check_dataset_balance.py

  experiments/
    gonzaga_autoresearch/
      README.md
      prepare.py
      model.py
      run.py
      program.md
      results.tsv
      experiment_summary.md
    northwestern_gonzaga_closed/
      README.md
      data_raw/
      data_processed/
      scripts/
      results/
      diagnostics/
      logs/

  results/
    gonzaga/
      baseline_runs/
      diagnostics/
      error_analysis/
    closed_northwestern_gonzaga/
      # optional mirror/copy of final closed result tables only

  logs/
    research_log.md
    evaluation_board.md
    build_runs/

  reports/
    final_report.md
    figures/

  archive/
    deprecated_scripts/
    old_results/
    llm_dry_run/
    semantic_feature_ablation/
    data_cleaning_test_lab/
    demo_autoresearch/
```

## Mapping From Current Structure

| Current Path | Proposed Path | Action |
|---|---|---|
| `1 -- data/` | `data/raw/` and `data/processed/` | Split raw and processed later. |
| `src/` | `src/parsing/`, `src/modeling/`, `src/diagnostics/` | Rename and group active scripts. |
| `data/processed/` | `data/processed/` | Move canonical datasets later. |
| `results/gonzaga/baseline_runs/` | `results/gonzaga/baseline_runs/` | Preserve. |
| `results/gonzaga/diagnostics/` | `results/gonzaga/diagnostics/` | Preserve. |
| `results/gonzaga/error_analysis/` | `results/gonzaga/error_analysis/` | Preserve. |
| `archive/broad_feature_search/results/` | `archive/old_results/feature_search/` | Archive after extracting final table. |
| `archive/semantic_feature_ablation/results/` | `archive/semantic_feature_ablation/` | Archive. |
| `archive/llm_dry_run/results/` | `archive/llm_dry_run/` | Archive unless revived. |
| `logs/` | `logs/` | Preserve. |
| `experiments/northwestern_gonzaga_closed/` | `experiments/northwestern_gonzaga_closed/` | Preserve as self-contained package. |
| `experiments/gonzaga_autoresearch/` | `experiments/gonzaga_autoresearch/` | Preserve. |
| `demo-autoresearch/` | `archive/demo_autoresearch/` | Archive. |
| `8 -- data cleaning test lab/` | `archive/data_cleaning_test_lab/` | Archive. |

## File Rename Suggestions

Rename only after confirming scripts still run:

| Current Name | Proposed Name |
|---|---|
| `src/parsing/debate_doc_parser.py` | `src/parsing/debate_doc_parser.py` |
| `src/parsing/count_tournament_disclosures.py` | `src/parsing/count_tournament_disclosures.py` |
| `src/parsing/select_tournament_docs.py` | `src/parsing/select_tournament_docs.py` |
| `src/parsing/build_gonzaga_dataset.py` | `src/parsing/build_gonzaga_dataset.py` |
| `archive/deprecated_scripts/legacy_baseline_round_model.py` | `src/modeling/legacy_baseline_round_model.py` |
| `src/modeling/export_locked_validation_predictions.py` | `src/modeling/export_validation_predictions.py` |
| `experiments/northwestern_gonzaga_closed/` | `experiments/northwestern_gonzaga_closed/` |

## README Structure

Recommended final README:

```text
# STAT 390 Debate Outcome Prediction

## Research Question
## Final Findings
## Predictive vs Explanatory Experiments
## Data Sources
## Setup
## Reproduce Clean Gonzaga Predictive Model
## Reproduce Closed Northwestern+Gonzaga Robustness Check
## Reproduce Retrospective Team-Strength Explanation
## Key Results Tables
## Repository Structure
## Limitations
## Archived/Deprecated Work
```

## Experiment Tracking Structure

Use one experiment folder per major study:

```text
experiments/<experiment_name>/
  README.md
  scripts/
  data_processed/
  results/
  diagnostics/
  logs/
```

Every experiment should include:

- `README.md`: purpose, inputs, commands, outputs.
- `results/experiment_table.csv`: one row per model.
- `logs/summary.md`: plain-English interpretation.
- `diagnostics/`: coverage, missingness, join failures.

## Archive Strategy

Create:

```text
archive/
  README.md
  deprecated_scripts/
  old_results/
  llm_dry_run/
  semantic_feature_ablation/
  broad_feature_search/
  data_cleaning_test_lab/
  demo_autoresearch/
```

Archive means:

- preserved for transparency,
- not part of final reproduction path,
- referenced only if discussing failed/abandoned directions.

## Final Presentation-Ready Workflow

The final report should point to three workflows:

1. Gonzaga-only clean predictive workflow:
   - modest structured-feature signal,
   - best clean model around `0.643836`.

2. Closed Northwestern+Gonzaga robustness workflow:
   - cross-tournament validation drops to about `0.530864`,
   - normalization/pairing do not rescue performance.

3. Retrospective explanatory workflow:
   - Shirley team-strength variables reach about `0.746479`,
   - not valid real-time predictors,
   - support latent team-strength dominance.

## Do Not Do Yet

Do not immediately move files until:

- README is updated,
- final report tables are frozen,
- large raw-data tracking policy is decided,
- a branch/backup is made,
- imports/paths are updated in one controlled pass.
