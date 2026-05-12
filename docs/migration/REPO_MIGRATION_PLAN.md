# Repository Migration Plan

## Purpose

This plan freezes the current experimental story while making the repository easier to read, reproduce, and grade. It is intentionally conservative: no files are permanently deleted, and active paths are preserved during this first cleanup pass.

## Migration Principles

- Preserve all important experiments and result artifacts.
- Do not rerun modeling experiments.
- Do not change result values.
- Prefer copying into cleaner locations before removing old paths.
- Move or archive only work that is clearly deprecated or external-reference material.
- Keep canonical workflows clear:
  - Clean Gonzaga predictive workflow.
  - Closed Northwestern+Gonzaga robustness workflow.
  - Retrospective explanatory workflow.

## Proposed Folder Additions

| New Path | Rationale | Affected Scripts | Risk |
|---|---|---|---|
| `src/` | Future clean source-code namespace. | None yet; canonical source folders are active. | Low |
| `src/project_paths.py` | Lightweight repo-relative path helper for future scripts. | None currently import it. | Low |
| `data/processed/` | Canonical location for processed datasets in presentation-friendly structure. | None; copies only. | Low |
| `results/gonzaga/` | Canonical final Gonzaga result mirror. | None; copies only. | Low |
| `experiments/gonzaga_autoresearch/` | Cleaner mirror of `experiments/gonzaga_autoresearch/`. | None; copy only. | Low |
| `experiments/northwestern_gonzaga_closed/` | Cleaner mirror of closed experiment. | None; copy only. | Low |
| `archive/` | Root for deprecated and abandoned work. | None if copied only. | Low |
| `archive/semantic_feature_ablation/` | Preserve failed semantic-feature experiment. | None; copy only. | Low |
| `archive/llm_dry_run/` | Preserve incomplete LLM prompt/scoring artifacts. | None; copy only. | Low |
| `archive/broad_feature_search/` | Preserve broad non-leaky feature search as supplementary work. | None; copy only. | Low |
| `archive/demo_autoresearch/` | Archive external demo template/reference. | None; copy/move possible. | Low |
| `archive/data_cleaning_test_lab/` | Archive old parsing/data-cleaning experiments. | None expected; copy/move possible. | Medium |
| `archive/deprecated_scripts/` | Preserve scripts not in canonical reproduction path. | None if old paths remain. | Low |

## Proposed Copies

Copies are safe because they preserve existing paths while making canonical paths easier to find.

| Source | Destination | Rationale | Risk |
|---|---|---|---|
| `data/processed/gonzaga_speech_dataset_v1.csv` | `data/processed/gonzaga_speech_dataset_v1.csv` | Canonical clean Gonzaga dataset. | Low |
| `data/processed/gonzaga_speech_dataset_v2_with_text.csv` | `data/processed/gonzaga_speech_dataset_v2_with_text.csv` | Canonical text-enriched Gonzaga dataset. | Low |
| `experiments/northwestern_gonzaga_closed/data_processed/combined_speech_dataset_closed_with_split.csv` | `data/processed/closed_northwestern_gonzaga/combined_speech_dataset_closed_with_split.csv` | Canonical closed combined speech dataset mirror. | Low |
| `experiments/northwestern_gonzaga_closed/data_processed/paired_round_dataset_closed_with_split.csv` | `data/processed/closed_northwestern_gonzaga/paired_round_dataset_closed_with_split.csv` | Canonical paired-round dataset mirror. | Low |
| `experiments/gonzaga_autoresearch/` | `experiments/gonzaga_autoresearch/` | Presentation-friendly experiment path. | Medium because duplicate generated files may come along. |
| `experiments/northwestern_gonzaga_closed/` | `experiments/northwestern_gonzaga_closed/` | Presentation-friendly closed experiment path. | Medium because folder is large. |
| `results/gonzaga/baseline_runs/` | `results/gonzaga/baseline_runs/` | Canonical Gonzaga result mirror. | Low |
| `results/gonzaga/diagnostics/` | `results/gonzaga/diagnostics/` | Canonical Gonzaga diagnostics mirror. | Low |
| `results/gonzaga/error_analysis/` | `results/gonzaga/error_analysis/` | Canonical Gonzaga error-analysis mirror. | Low |
| `archive/semantic_feature_ablation/results/` | `archive/semantic_feature_ablation/results/` | Preserve failed semantic ablation. | Low |
| `archive/semantic_feature_ablation/scripts/build_semantic_highlight_features_v1.py` | `archive/semantic_feature_ablation/scripts/` | Preserve script with failed result. | Low |
| `archive/llm_dry_run/results/` | `archive/llm_dry_run/results/` | Preserve incomplete LLM artifacts. | Low |
| `archive/llm_dry_run/scripts/build_llm_argument_features_v6.py` | `archive/llm_dry_run/scripts/` | Preserve LLM prep script. | Low |
| `archive/llm_dry_run/scripts/score_llm_argument_features_v6.py` | `archive/llm_dry_run/scripts/` | Preserve LLM scoring script. | Low |
| `archive/llm_dry_run/scripts/inspect_llm_prompts_v6.py` | `archive/llm_dry_run/scripts/` | Preserve prompt inspection script. | Low |
| `archive/broad_feature_search/results/` | `archive/broad_feature_search/results/` | Preserve broad feature-search artifacts. | Low |
| `archive/broad_feature_search/scripts/run_nonleaky_feature_search.py` | `archive/broad_feature_search/scripts/` | Preserve broad feature-search script. | Low |

## Proposed Moves

For this first pass, risky moves are deferred. Old paths remain authoritative. The only archive action that may be safe as a later move is:

| Source | Destination | Rationale | Risk | First-Pass Action |
|---|---|---|---|---|
| `demo-autoresearch/` | `archive/demo_autoresearch/` | Reference template, not project evidence. | Low | Copy now; defer move. |
| `8 -- data cleaning test lab/` | `archive/data_cleaning_test_lab/` | Deprecated exploratory parsing work. | Medium | Copy now; defer move. |

## Rename Plan

No active script rename will be performed in this pass because old paths are referenced in logs, README examples, and experiment scripts.

| Current Name | Future Name | Affected References | Risk |
|---|---|---|---|
| `src/parsing/debate_doc_parser.py` | `src/parsing/debate_doc_parser.py` | Builder scripts, closed experiment copied parser, README. | Medium |
| `src/parsing/count_tournament_disclosures.py` | `src/parsing/count_tournament_disclosures.py` | Tournament selection scripts and docs. | Low/Medium |
| `src/parsing/select_tournament_docs.py` | `src/parsing/select_tournament_docs.py` | Tournament selection docs. | Low/Medium |
| `src/parsing/build_gonzaga_dataset.py` | `src/parsing/build_gonzaga_dataset.py` | README, logs, reproduction docs. | Medium |

## Canonical Workflow Impact

- Clean Gonzaga predictive workflow remains runnable from existing paths.
- Closed Northwestern+Gonzaga workflow remains runnable from existing closed folder.
- Retrospective explanatory workflow remains runnable from existing closed folder.
- New paths are mirrors/helpers, not replacements.

## Risk Management

- No permanent deletion.
- No test-set evaluation.
- No model reruns.
- Validation will check file existence and Python syntax compilation.
- Any future path migration should happen in a separate commit after updating imports and README commands.
