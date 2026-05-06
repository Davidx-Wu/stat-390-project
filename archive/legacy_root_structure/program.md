# Agent Instructions

Goal: Improve round outcome prediction over baseline heuristics.

Allowed edits:
- src/features.py
- src/baseline.py
- src/llm_eval.py

Frozen files:
- evaluation/metrics_definition.md
- evaluation/split_plan.md
- test set

Rules:
- Do not modify evaluation logic after results are observed
- Record every experiment in logs/experiment_log.csv
- Compare all changes against baseline