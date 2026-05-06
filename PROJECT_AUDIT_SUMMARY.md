# Project Audit Summary

## Scope

This audit summarizes the current STAT 390 debate outcome prediction repository without moving, deleting, or rerunning existing experiments. It is intended to prepare the project for final presentation, reproducibility cleanup, and long-term legibility.

## High-Level Project State

The project now contains three distinct research layers:

1. Clean Gonzaga-only predictive modeling from parser-derived structured speech features.
2. Closed Northwestern+Gonzaga robustness checks under cross-tournament distribution shift.
3. Retrospective explanatory modeling using Shirley post-tournament variables as latent team-strength proxies.

The most important methodological separation is:

- Clean predictive results should use only parser-derived or pre-round safe features.
- Shirley variables should be framed only as retrospective/explanatory because the file contains downstream fields such as `WinPm`, speaker points, `OSd`, and `Ballots`.

## Repository Inventory

| Path | Purpose | Current Use | Recommendation |
|---|---|---|---|
| `data/raw/` and `data/processed/` | Canonical raw/processed data locations. | Required for rebuilding and reproducing final workflows. | Preserve; legacy `1 -- data/` exists only as a locked-file compatibility exception if present. |
| `archive/legacy_root_structure/2 -- notebooks/` | Exploratory notebooks. | Not central to final reproducibility based on current workflow. | Archived. |
| `src/` | Main parsing, build, diagnostics, and experiment scripts. | Mixed active and deprecated scripts. | Preserve active scripts; move deprecated attempts to an archive folder later. |
| `data/processed/` | Gonzaga v1/v2 processed datasets. | Core clean predictive data artifacts. | Preserve and version if allowed. |
| `results/gonzaga/baseline_runs/` | Gonzaga baseline v3/v4/v5 and related metrics/coefficient outputs. | Important for final ablation table. | Preserve. |
| `results/gonzaga/diagnostics/` | Dataset balance and diagnostic plots/CSVs. | Important for data understanding. | Preserve. |
| `results/gonzaga/error_analysis/` | Locked model validation predictions/misclassifications. | Important for final error analysis. | Preserve. |
| `archive/broad_feature_search/results/` | Non-leaky feature-search outputs. | Useful audit trail; not final model path. | Preserve as supplementary/archived experiment output. |
| `archive/semantic_feature_ablation/results/` | Highlighted-text semantic feature ablation outputs. | Important failed direction. | Preserve as archived experiment evidence. |
| `archive/llm_dry_run/results/` | LLM prompt/features prep artifacts. | Partially attempted infrastructure; not final. | Archive with clear "incomplete/dry-run" label. |
| `logs/` | Research log, evaluation board, failure/build logs. | Important project history, but partly stale. | Preserve and update only after cleanup plan is accepted. |
| `archive/legacy_root_structure/6 -- evaluation/` | Legacy evaluation helpers/materials. | Not central in final pipeline. | Archived. |
| `experiments/northwestern_gonzaga_closed/` | Self-contained closed Northwestern+Gonzaga robustness and explanatory experiment. | Very important for final narrative about distribution shift. | Preserve as a standalone experiment package. |
| `reports/` | Written reports. | Presentation/report staging. | Preserve. |
| `archive/data_cleaning_test_lab/` | Experimental parsing/data-cleaning work. | Not part of final pipeline. | Archived as deprecated development material. |
| `experiments/gonzaga_autoresearch/` | Gonzaga-only AutoResearch loop and locked model search. | Important for clean predictive model selection. | Preserve, but clean generated files and document frozen/editable boundary. |
| `demo-autoresearch/` | Reference template/demo. | Not part of project results. | Archive or mark as external reference. |
| `results/gonzaga/parser_output/` | Gonzaga parser outputs and audits. | Duplicates raw build output also present under raw data. | Preserve one canonical copy; archive duplicate later. |

## Important Scripts

| Script | Purpose | Status | Recommendation |
|---|---|---|---|
| `src/parsing/debate_doc_parser.py` | Parses one `.docx` into speech summary, argument audit, and card audit. | Active core parser. | Preserve. |
| `src/parsing/count_tournament_disclosures.py` | Counts tournament disclosure docs by filename-derived tournament labels. | Active for tournament selection logic. | Preserve. |
| `src/parsing/select_tournament_docs.py` | Copies selected tournament docs using same label logic. | Active/reference for closed experiment. | Preserve. |
| `src/parsing/build_gonzaga_dataset.py` | Batch Gonzaga builder. | Important but name says temp. | Rename later to `build_gonzaga_dataset.py` after verifying behavior. |
| `src/modeling/baseline_v3_structured_numeric.py` | Gonzaga clean structured logistic baseline. | Active historical baseline. | Preserve. |
| `archive/deprecated_scripts/baseline_v4_side_features.py` | Side-aware baseline. | Failed ablation. | Archive after final table. |
| `archive/deprecated_scripts/baseline_v5_density_features.py` | Density feature baseline. | Failed ablation. | Archive after final table. |
| `src/parsing/build_text_enriched_dataset_v2.py` | Builds v2 text-enriched dataset from audit files. | Useful for LLM/semantic attempts. | Preserve if text discussion remains. |
| `archive/semantic_feature_ablation/scripts/build_semantic_highlight_features_v1.py` | Highlighted text semantic ablation. | Failed direction. | Archive as supplementary. |
| `archive/broad_feature_search/scripts/run_nonleaky_feature_search.py` | Aggressive but non-leaky feature search. | Useful audit trail; not final model. | Archive/supplement. |
| `src/modeling/export_locked_validation_predictions.py` | Exports locked validation predictions. | Active for error analysis. | Preserve. |
| `experiments/gonzaga_autoresearch/model.py` | Locked Gonzaga-only interaction logistic model. | Active final clean model artifact. | Preserve. |
| `experiments/gonzaga_autoresearch/prepare.py` | Frozen AutoResearch data/eval support. | Active for Gonzaga-only loop. | Preserve. |
| `experiments/gonzaga_autoresearch/run.py` | Frozen AutoResearch runner. | Active for Gonzaga-only loop. | Preserve. |
| `experiments/northwestern_gonzaga_closed/scripts/run_closed_experiment.py` | Closed Northwestern parser/build/split/models. | Active closed robustness experiment. | Preserve. |
| `experiments/northwestern_gonzaga_closed/scripts/run_generalization_experiments.py` | Tournament normalization/relative feature checks. | Active closed robustness experiment. | Preserve. |
| `experiments/northwestern_gonzaga_closed/scripts/run_paired_round_experiment.py` | Pair-level round modeling. | Active failed/theory-driven ablation. | Preserve. |
| `experiments/northwestern_gonzaga_closed/scripts/run_ranking_prior_experiment.py` | Diagnostic Shirley ranking prior comparison. | Diagnostic only due leakage risk. | Preserve with warning. |
| `experiments/northwestern_gonzaga_closed/scripts/run_explanatory_strength_model.py` | Retrospective latent team-strength explanatory model. | Active explanatory result. | Preserve with warning. |

## Important Datasets and Outputs

| Artifact | Purpose | Key Facts | Recommendation |
|---|---|---|---|
| `data/processed/gonzaga_speech_dataset_v1.csv` | Clean Gonzaga speech-level dataset with fixed split. | 484 rows; `dataset_split` present. | Preserve as canonical Gonzaga predictive dataset. |
| `data/processed/gonzaga_speech_dataset_v2_with_text.csv` | Gonzaga v1 plus aggregated card/argument text. | Used for LLM prompt prep and semantic attempts. | Preserve if discussing semantic/LLM limitations. |
| `experiments/northwestern_gonzaga_closed/data_processed/combined_speech_dataset_closed_with_split.csv` | Closed Gonzaga+Northwestern speech dataset. | 1082 rows; train 757, validation 162, test 163. | Preserve as canonical closed robustness dataset. |
| `experiments/northwestern_gonzaga_closed/data_processed/paired_round_dataset_closed_with_split.csv` | Closed pair-level Aff-vs-Neg dataset. | 373 paired rounds; train 261, validation 56, test 56. | Preserve as pair-level diagnostic dataset. |
| `experiments/gonzaga_autoresearch/results.tsv` | Gonzaga AutoResearch experiment log. | Contains key 0.616, 0.630, 0.644 progression. | Preserve. |
| `experiments/gonzaga_autoresearch/experiment_summary.md` | Summary of Gonzaga AutoResearch loop. | Best clean model documented at 0.643836. | Preserve. |
| `experiments/northwestern_gonzaga_closed/results/closed_experiment_table.csv` | Closed combined baseline results. | Structured logistic 0.530864; manual interaction 0.524691. | Preserve. |
| `experiments/northwestern_gonzaga_closed/results/generalization_experiment_table.csv` | Tournament-normalized/relative feature results. | No meaningful closed-validation improvement. | Preserve. |
| `experiments/northwestern_gonzaga_closed/results/paired_round_experiment_table.csv` | Pair-level modeling results. | Learned paired models underperform majority. | Preserve. |
| `experiments/northwestern_gonzaga_closed/results/explanatory_experiment_table.csv` | Retrospective Shirley explanatory results. | Team-strength-only logistic 0.746479. | Preserve with leakage/explanatory warning. |

## Preserve, Archive, Remove Later

Preserve in final main workflow:

- Core parser and tournament selection scripts.
- Gonzaga processed datasets and baseline results.
- `experiments/gonzaga_autoresearch/` locked clean model workflow.
- Closed Northwestern+Gonzaga experiment folder.
- Final audit/reproducibility docs.

Archive after final report tables are stable:

- LLM prompt dry-run artifacts.
- Semantic highlight ablation outputs.
- Broad feature-search outputs.
- Failed v4/v5/v6 scripts if not directly used in final reproduction.
- `demo-autoresearch/`.
- `archive/data_cleaning_test_lab/`.

Remove only after explicit review:

- `__pycache__/` folders.
- Temporary parser output folders such as `_northwestern_temp_single_run` if present.
- Duplicate copies of large audit outputs once one canonical copy is chosen.

## Key Results That Matter

- Gonzaga-only clean predictive best: interaction-only degree-2 logistic regression with `C=0.5`, validation accuracy `0.643836`.
- Aggressive non-leaky feature search found a manual-interaction candidate at `0.671233`, but it should be treated cautiously because of small validation size.
- Closed Gonzaga+Northwestern structured logistic accuracy dropped to `0.530864`, showing cross-tournament distribution shift.
- Tournament normalization did not improve closed validation accuracy.
- Pair-level Aff-vs-Neg modeling did not improve learned validation performance.
- Retrospective Shirley/team-strength variables reached `0.746479` on complete Shirley-linked validation rows, but this is explanatory only because the variables are downstream/post-tournament.

## Final Audit Recommendation

The final project should present two separate findings:

1. Clean predictive finding: parser-derived structural features contain modest signal in Gonzaga-only data but generalize poorly across tournaments.
2. Explanatory finding: downstream team-strength/result proxies explain substantially more variance, suggesting latent team strength dominates the current parser-derived structural signal.
