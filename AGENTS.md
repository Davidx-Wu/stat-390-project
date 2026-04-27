# Agent Instructions for stat-390-project

## Project purpose
This is a STAT 390 data science project on predicting policy debate round outcomes from debate speech documents and tournament results.

## Current repo structure
The actual repo uses numbered folders:

- `1 -- data/`: local data. Raw data should not be committed.
- `2 -- notebooks/`: exploratory notebooks.
- `3 -- src/`: main source scripts.
- `4 -- results/`: generated outputs and baseline model artifacts.
- `5 -- logs/`: research logs, evaluation notes, failure logs.
- `6 -- evaluation/`: evaluation materials.
- `7 -- reports/`: written reports.
- `8 -- data cleaning test lab/`: experimental parsing scripts.

Do not assume standard folders like `src/`, `data/`, or `results/` unless they actually exist.

## Current pipeline
1. Parse debate `.docx` files into structured speech-level features.
2. Filter tournament-specific disclosure files.
3. Merge speech features with tournament outcome / ranking data.
4. Train a baseline model.
5. Save predictions, coefficients, logs, and failed-file outputs.

## Coding rules
- Preserve existing folder names unless explicitly asked to rename them.
- Be careful with paths containing spaces and dashes.
- Use `pathlib.Path` instead of raw string paths when possible.
- Do not overwrite raw data.
- Do not move files unless explicitly asked.
- Make small, reviewable changes.
- Prefer clear Python over clever abstractions.

## Validation rules
Before claiming a change works, run the relevant script and report:
- command used
- whether it succeeded
- output files created
- any warnings/errors

## Documentation rules
Keep README.md, logs, and actual scripts consistent.
If the baseline has been run, do not leave documentation saying it has not.