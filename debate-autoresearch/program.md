# Debate AutoResearch Program

## Objective
Maximize validation accuracy predicting `win_loss` for the Gonzaga debate dataset.

## Editable Boundary
You may ONLY modify:

- `debate-autoresearch/model.py`

Do NOT modify:

- `debate-autoresearch/prepare.py`
- `debate-autoresearch/run.py`
- raw datasets
- processed datasets
- logs outside `debate-autoresearch/` unless explicitly asked

## Data Rules
- Use `4 -- results/processed_datasets/gonzaga_speech_dataset_v2_with_text.csv`.
- Use the existing `dataset_split` column.
- Train on `train`.
- Evaluate on `validation`.
- Do NOT use the `test` split.

## Feature Rules
Do NOT use these fields unless explicitly instructed:

- `team_code`
- `judge`
- `opponent`
- `tournament_name`

Do NOT call LLM APIs unless explicitly asked.

## Experiment Runtime
Each experiment must run under 60 seconds.

## Experiment Loop
1. Read `debate-autoresearch/model.py`.
2. Propose a small model change.
3. Modify only `debate-autoresearch/model.py`.
4. Run `python debate-autoresearch/run.py "<description>"`.
5. Compare validation accuracy against the current best.
6. If improved, keep `model.py`.
7. If worse, revert `model.py`.
8. Repeat only when asked.

## Search Ideas
- Logistic regression variants.
- Interaction features.
- sklearn tree ensembles.
- Calibrated linear models.
- Later: LLM feature columns if available.
