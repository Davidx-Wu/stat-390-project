# Best Result vs Baseline

## Clean Predictive Setting

| Model | Feature Set | Validation Accuracy | Difference vs Majority | Difference vs v3 |
| --- | --- | ---: | ---: | ---: |
| Majority baseline | Predict majority validation class | `0.602740` | `0.000000` | `-0.013699` |
| Baseline v3 structured logistic | Six parser-derived numeric features | `0.616438` | `+0.013699` | `0.000000` |
| Locked interaction logistic | Interaction-only degree-2 features + `LogisticRegression(C=0.5)` | `0.643836` | `+0.041096` | `+0.027397` |

## Locked Final Predictive Model

The locked clean predictive model is:

- interaction-only degree-2 logistic regression
- `LogisticRegression(C=0.5)`
- six base structured features:
  - `num_positions`
  - `num_adv_inh_solv`
  - `num_offs`
  - `num_cards_total`
  - `num_cards_with_highlight`
  - `total_highlighted_words`

Canonical implementation:

- `experiments/gonzaga_autoresearch/model.py`

Primary result table:

- `experiments/gonzaga_autoresearch/results.tsv`

## Retrospective Explanatory Setting

| Model | Feature Set | Validation Accuracy | Interpretation |
| --- | --- | ---: | --- |
| Speech-structure-only logistic | Parser-derived speech structure | `0.530864` | Weak cross-tournament signal. |
| Shirley/team-strength-only logistic | Downstream team-strength/result proxies | `0.746479` | Strong retrospective explanatory signal, not clean prediction. |
| Combined speech + Shirley logistic | Speech structure plus Shirley variables | `0.704225` | Speech features did not add incremental value over Shirley-only. |

## Main Week 5 Conclusion

The best clean predictive result is the locked interaction-logistic model at `0.643836` validation accuracy. The stronger Shirley/team-strength result is explanatory rather than leakage-free prediction, so it should not replace the locked predictive model.
