# Debate AutoResearch Experiment Summary

## Results
- Baseline accuracy: **0.616438**
- Best accuracy: **0.643836**
- Best model: interaction-only degree-2 features + `LogisticRegression(C=0.5)`

## Discarded Models
- Full degree-2 logistic regression
- Random forest
- Gradient boosting
- Hist gradient boosting
- `class_weight="balanced"` logistic regression

## Interpretation
Interaction features improve validation performance over the structured numeric logistic baseline. More flexible tree models appear to overfit or fail on this small, noisy feature set.

## Next Planned Feature Families
1. LLM argument-quality scores
2. Team strength control from NDT seeds
3. Citation-year features if parser adds them later
