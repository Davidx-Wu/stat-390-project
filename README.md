# STAT 390 Debate Outcome Prediction

This project studies whether structured features parsed from policy debate speech documents can predict debate round outcomes, and whether those features generalize beyond a single tournament.

The final project story is not simply "find the highest accuracy model." The main finding is methodological:

- Parser-derived speech-structure features contain modest predictive signal in the Gonzaga-only setting.
- That signal weakens sharply under cross-tournament distribution shift after adding Northwestern.
- Retrospective team-strength/result variables explain much more outcome variation, but those variables are not valid real-time prediction features.

## Research Question

Can debate speech structure, extracted from `.docx` disclosure documents, predict round outcomes?

The project eventually separates this into two questions:

1. **Clean predictive question:** Can non-leaky parser-derived features predict outcomes?
2. **Retrospective explanatory question:** Do downstream team-strength variables explain more variance than speech structure?

## Predictive vs Explanatory Experiments

The distinction matters.

**Clean predictive experiments** use features that could plausibly exist before or during a round:

- number of positions
- number of advantages/inherency/solvency sections
- number of off-case positions
- number of evidence cards
- number of highlighted cards
- highlighted word counts

**Retrospective explanatory experiments** use Shirley variables such as `Place`, `WinPm`, `PtsPm`, `OSd`, and `Ballots`. These are downstream/post-tournament result variables, so they are not valid leakage-free prediction features. They are used only to test whether latent team strength explains more than document structure.

## Final Findings

### Clean Gonzaga Predictive Setting

Best clean Gonzaga-only model:

- interaction-only degree-2 logistic regression
- `LogisticRegression(C=0.5)`
- validation accuracy: `0.643836`

Structured baseline v3:

- six numeric parser-derived features
- validation accuracy: `0.616438`

### Closed Northwestern+Gonzaga Robustness Setting

Adding Northwestern data exposed distribution shift.

Closed combined validation results:

- majority baseline: `0.518519`
- structured logistic: `0.530864`
- manual interaction logistic: `0.524691`

Tournament normalization, relative features, and pair-level modeling did not meaningfully solve cross-tournament generalization.

### Retrospective Explanatory Setting

Using Shirley downstream team-strength variables:

- speech structure only: `0.530864`
- Shirley/team-strength-only logistic: `0.746479`
- combined speech + Shirley logistic: `0.704225`

This supports the explanatory claim that latent team strength dominates the current parser-derived structural speech features.

## Repository Structure

The repository now uses descriptive top-level folders. Experiment chronology is preserved in `experiments/stage_*` folders, logs, timeline docs, and Git history rather than numbered root folders.

```text
archive/                        legacy root structure and deprecated work
data/                           raw and processed data used by canonical scripts
experiments/                    staged experiment chronology and canonical experiments
logs/                           research/evaluation logs
reports/                        written reports
results/                        generated results and diagnostics
src/                            parsing, modeling, diagnostics source scripts
src/project_paths.py            lightweight repo-relative path helper
```

Some legacy numbered root folders may remain only when files are locked by another process. Canonical copies live under the descriptive paths above; see `FINAL_REPO_CLEANUP_VALIDATION.md`.

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

If `pip` is unavailable:

```powershell
python -m pip install -r requirements.txt
```

Required packages:

- `numpy`
- `pandas`
- `python-docx`
- `scikit-learn`
- `pillow`

## Canonical Workflows

Detailed canonical workflow definitions are in:

- `CANONICAL_WORKFLOWS.md`

Experiment chronology is explicitly represented as:

- `experiments/stage_1_gonzaga_predictive/`
- `experiments/stage_2_feature_ablation/`
- `experiments/stage_3_cross_tournament/`
- `experiments/stage_4_paired_rounds/`
- `experiments/stage_5_explanatory_strength/`

### A. Clean Gonzaga Predictive Workflow

Canonical dataset:

- `data/processed/gonzaga_speech_dataset_v1.csv`

Canonical AutoResearch workflow:

```powershell
python "experiments/gonzaga_autoresearch/run.py" "baseline logistic" --baseline
```

Key files:

- `experiments/gonzaga_autoresearch/prepare.py`
- `experiments/gonzaga_autoresearch/model.py`
- `experiments/gonzaga_autoresearch/run.py`
- `experiments/gonzaga_autoresearch/results.tsv`
- `experiments/gonzaga_autoresearch/experiment_summary.md`

### B. Closed Northwestern+Gonzaga Robustness Workflow

Canonical folder:

- `experiments/northwestern_gonzaga_closed/`

Key scripts:

```powershell
python "experiments/northwestern_gonzaga_closed/scripts/run_closed_experiment.py" --batch-size 100
python "experiments/northwestern_gonzaga_closed/scripts/run_generalization_experiments.py"
python "experiments/northwestern_gonzaga_closed/scripts/run_paired_round_experiment.py"
```

Key outputs:

- `results/closed_experiment_table.csv`
- `results/generalization_experiment_table.csv`
- `results/paired_round_experiment_table.csv`

### C. Retrospective Explanatory Workflow

Canonical scripts:

```powershell
python "experiments/northwestern_gonzaga_closed/scripts/run_ranking_prior_experiment.py"
python "experiments/northwestern_gonzaga_closed/scripts/run_explanatory_strength_model.py"
```

Key warning:

These use Shirley post-tournament variables and should not be described as leakage-free prediction models.

Key outputs:

- `results/ranking_prior_experiment_table.csv`
- `results/explanatory_experiment_table.csv`
- `results/explanatory_model_coefficients.csv`
- `logs/explanatory_model_summary.md`

## Important Audit Documents

- `PROJECT_AUDIT_SUMMARY.md`
- `PROJECT_TIMELINE.md`
- `REPRODUCIBILITY_AUDIT.md`
- `PROPOSED_REPO_STRUCTURE.md`
- `REPO_MIGRATION_PLAN.md`
- `CANONICAL_WORKFLOWS.md`
- `POST_RESTRUCTURE_VALIDATION.md`

## Limitations

- The parser is sensitive to filename conventions and document formatting.
- Many matchup pairs are incomplete because only one side is available.
- Cross-tournament generalization is weak.
- Shirley variables are downstream and should be used only for retrospective explanation.
- The test set remains reserved unless a final explicit evaluation is requested.

## Archived Work

Deprecated or abandoned work has been copied into `archive/` rather than deleted:

- semantic feature ablation
- LLM dry-run artifacts
- broad feature search
- demo AutoResearch template
- data-cleaning test lab

These artifacts preserve the research trail but are not part of the main final reproduction path.
