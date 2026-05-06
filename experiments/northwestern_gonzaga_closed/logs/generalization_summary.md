# Generalization Experiment Summary

## Objective
- Improve cross-tournament robustness under Gonzaga + Northwestern distribution shift using only closed-folder artifacts.
- No closed test-set rows were used for same-split model optimization.

## Relative Feature Diagnostic
- Opponent speech match coverage across combined data: 0.694
- Relative features were evaluated with an opponent-match flag and zero difference fallback for unmatched rows.
- First relative-feature attempt exposed duplicate opponent-match keys; the script now collapses duplicate keys deterministically before evaluation.

## Best Closed Validation Result
- Experiment: raw_only_logistic
- Feature set: raw_only
- Validation accuracy: 0.530864
- False positives: 52
- False negatives: 24
- Interpretation: matches raw baseline

## Tournament Holdout
- Best holdout experiment: holdout_train_gonzaga_validate_northwestern_relative_only
- Holdout accuracy: 0.539526
- Holdout rows use train+validation rows only and are not comparable to final test evidence.

## Calibration/Error Notes
- Calibration and error-cluster summaries were generated for the raw logistic closed validation model.
- Use calibration_summary.csv and error_cluster_summary.csv for probability and cluster-level diagnostics.

## Recommendation
- Treat any same-split gains as robustness clues, not final evidence.
- The key question is whether normalized or relative features reduce tournament dependence without sacrificing interpretability.
