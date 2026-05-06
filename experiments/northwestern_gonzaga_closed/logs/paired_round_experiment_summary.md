# Paired Round Closed Experiment Summary

## Unit of Analysis
- One row is one paired Aff-vs-Neg matchup when both sides could be identified.
- Target is aff_win_label, where 1 means Aff won and 0 means Neg won.

## Dataset
- Paired rounds created: 373
- Dropped groups because only one side was available: 331
- Dropped groups because outcomes were inconsistent: 0
- Duplicate side groups handled deterministically: 5
- Split source: new_pair_level_split_random_state_42
- Split sizes: {'train': 261, 'validation': 56, 'test': 56}
- Tournament counts: {'Northwestern': 203, 'Gonzaga': 170}
- Aff win label counts: {0: 203, 1: 170}

## Validation Results
- majority_baseline: accuracy=0.535714, FP=0, FN=26
- raw_paired_logistic: accuracy=0.410714, FP=14, FN=19
- diff_only_logistic: accuracy=0.446429, FP=12, FN=19
- aff_neg_diff_logistic: accuracy=0.410714, FP=13, FN=20
- manual_interaction_paired_logistic: accuracy=0.410714, FP=14, FN=19

## Best Model
- Best experiment: majority_baseline
- Best validation accuracy: 0.535714
- The paired majority baseline is slightly above the closed speech-level structured logistic baseline, but learned paired logistic models do not improve over either baseline.

## Error Clustering
- Error clusters for the best paired model are included below.
       cluster_field cluster_value  rows  errors  error_rate  false_positive_aff_win  false_negative_aff_win
   tournament_source       Gonzaga    27      10    0.370370                       0                      10
   tournament_source  Northwestern    29      16    0.551724                       0                      16
aff_parse_confidence          high    31      13    0.419355                       0                      13
aff_parse_confidence        medium    25      13    0.520000                       0                      13
neg_parse_confidence          high    29      13    0.448276                       0                      13
neg_parse_confidence        medium    27      13    0.481481                       0                      13
     both_high_parse         False    39      18    0.461538                       0                      18
     both_high_parse          True    17       8    0.470588                       0                       8

## Interpretation
- This is a theory-driven unit-of-analysis correction, not an open-ended search.
- Pairing is theoretically better aligned with debate rounds, but these structured paired features did not improve learned validation performance.
- This supports the broader project story that parser noise, missing side-comparative substance, and limited structured features remain the bottleneck under cross-tournament shift.
