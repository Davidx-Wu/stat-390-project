# Keep / Discard / Crash Summary

## Keep

| Item | Evidence | Reason |
| --- | --- | --- |
| Baseline v3 structured logistic | validation accuracy `0.616438`; majority baseline `0.602740` | Establishes that parser-derived structured features contain modest predictive signal. |
| Locked interaction-only logistic, `C=0.5` | validation accuracy `0.643836` | Best clean Gonzaga-only final predictive model; improves over v3 without changing the feature family. |
| Error analysis outputs | `results/gonzaga/error_analysis/validation_predictions.csv`; `validation_misclassifications.csv` | Supports interpretation of false positives/false negatives and model behavior. |
| Closed Northwestern+Gonzaga robustness check | structured logistic `0.530864`; manual interaction logistic `0.524691` | Important negative evidence showing distribution shift across tournaments. |
| Retrospective Shirley/team-strength explanatory model | Shirley-only logistic `0.746479` | Strong explanatory result showing latent team strength dominates speech-structure features; not clean prediction. |
| Metric trajectory plot | `reports/figures/metric_over_time_plot.png` and copied Week 5 version | Clear visual summary of project progression. |

## Discard

| Item | Evidence | Reason |
| --- | --- | --- |
| Side-feature v4 | validation accuracy `0.575342` | Did not improve over structured v3. |
| Density-feature v5 | validation accuracy `0.452055` | Underperformed both v3 and majority baseline. |
| Full degree-2 logistic | validation accuracy `0.602740` in AutoResearch log | Did not improve over locked interaction-only model. |
| Tree and boosting models | random forest `0.479452`; gradient boosting `0.479452`; hist gradient boosting `0.493151` | More flexible models did not generalize on the small/noisy feature set. |
| `class_weight="balanced"` logistic | validation accuracy `0.438356` | Hurt validation performance. |
| Highlighted semantic feature ablation | validation accuracy `0.561644` | Semantic keyword features weakened the locked model. |
| Paired-round learned logistic variants | raw paired logistic `0.410714`; diff-only `0.446429`; paired majority `0.535714` | Theory-driven unit change did not improve performance. |

## Crash / Blocked / Removed

| Item | Status | Reason |
| --- | --- | --- |
| Citation-year v6 | removed as non-informative | Processed dataset had no citation/year columns. Future work requires parser support. |
| Original LLM argument-quality model | blocked before final scoring/training | No usable text field existed in v1; later text-enrichment/prompt work stayed outside final clean result. |
| Generic semantic expansion | archived | Too broad for locked Week 5 scope and did not improve clean predictive performance. |

## Historical / Archived Work

Archived experiments remain useful for transparency but are not final:

- `archive/semantic_feature_ablation/`
- `archive/llm_dry_run/`
- `archive/broad_feature_search/`
- `results/gonzaga/legacy_baseline_model/`

The broad non-leaky search found a `0.671233` candidate, but it is treated cautiously because the validation set is small and the Week 5 final direction was already locked around the interpretable interaction-logistic model.
