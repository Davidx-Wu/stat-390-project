# Debate AutoResearch

This folder adapts the AutoResearch loop for the Gonzaga debate outcome prediction project.

Run the frozen baseline:

```powershell
python debate-autoresearch/run.py "baseline logistic" --baseline
```

Run a later experiment:

```powershell
python debate-autoresearch/run.py "try interaction features"
```

## Frozen vs Editable

Frozen files:

- `prepare.py`
- `run.py`

Editable file:

- `model.py`

The AutoResearch agent should only modify `model.py`. The frozen files define the dataset, split, allowed baseline features, validation metric, logging, and plotting.

## Data

Input dataset:

```text
4 -- results/processed_datasets/gonzaga_speech_dataset_v2_with_text.csv
```

Target:

```text
win_loss
```

Split column:

```text
dataset_split
```

The loop trains on `train`, evaluates on `validation`, and does not use `test`.

## Outputs

Experiment logs are written to:

```text
debate-autoresearch/results.tsv
```

Performance plot:

```text
debate-autoresearch/performance.png
```
