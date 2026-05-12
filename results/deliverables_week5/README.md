# Week 5 Deliverable Index

This folder packages the Week 5 deliverables without rerunning experiments or changing result values. It points to the current canonical documentation, updated logs, experiment tables, and metric trajectory artifacts.

## Required Deliverables

### 1. Complete Experiment Log Bundle

Primary log files:

- `logs/research_log.md`
- `logs/evaluation_board.md`
- `logs/failure_log.md`
- `logs/autoresearch_plan.md`

Canonical reader-facing guide:

- `docs/CANONICAL_PIPELINE.md`

Experiment chronology and reproduction notes:

- `docs/chronology/PROJECT_TIMELINE.md`
- `docs/chronology/CANONICAL_WORKFLOWS.md`

Main experiment table:

- `experiments/gonzaga_autoresearch/results.tsv`

## 2. Metric Trajectory Plot

Copied into this folder:

- `metric_over_time_plot.png`
- `metric_over_time_data.csv`
- `metric_over_time_caption.md`

Original report figure location:

- `reports/figures/metric_over_time_plot.png`
- `reports/figures/metric_over_time_data.csv`
- `reports/figures/metric_over_time_caption.md`

## 3. Keep / Discard / Crash Summary

- `keep_discard_crash_summary.md`

## 4. Best Result vs Baseline

- `best_result_vs_baseline.md`

## 5. What Actually Worked Memo

- `what_actually_worked_memo.md`

## Interpretation Boundary

Clean predictive results use non-leaky parser-derived speech/document structure. Retrospective explanatory results use Shirley/team-strength variables that are downstream/post-tournament proxies and should not be framed as leakage-free prediction features.

Historical and archived work is preserved to show the research path, but the canonical clean predictive model remains the Gonzaga-only interaction-only logistic regression with `LogisticRegression(C=0.5)`.
