# STAT 390 Capstone Project — stat-390-project

This project tests whether LLM-based scores of argument quality—claim, warrant, and impact—can predict policy debate round outcomes better than simple heuristics such as evidence quantity or source type, using evidence cards and tournament rounds from a focused topic area.

## Evaluating Debate Argument Quality with Large Language Models

### Problem

Can large language models evaluate the quality of policy debate arguments and predict round outcomes better than simple heuristics based on evidence quantity or source type?

### Data

The dataset consists of:

- Policy debate **evidence cards** (text and metadata such as source and citation).
- Debate rounds with **known winners** (counts to be finalized when cleaning finishes).

These are used to build baseline features and, where applicable, LLM-derived argument quality scores.

### Method

The project compares two approaches:

**Baseline heuristics**

- Evidence quantity (for example, number of cards).
- Source type or citation-related signals.

**LLM-based argument evaluation** (planned direction)

- Extract structured argument components (claim, warrant, impact).
- Score argument quality with a large language model.
- Use those features to predict debate round outcomes.

There is **no** dedicated LLM evaluation script checked in under `3 -- src/` yet; when it exists, it will live alongside the other pipeline scripts.

### Metric

Primary evaluation metric: **round outcome prediction accuracy**.

Secondary metrics may include F1, precision, and recall. Comparisons between baseline features and LLM-derived features will use the evaluation materials under `6 -- evaluation/` when defined.

### Baseline artifacts in this repository

Baseline-related files that are **currently checked in** live under **`4 -- results/1 -- Baseline Model/`** (for example speech summaries, rankings inputs, predictions, coefficients, run logs, and parser failure logs). Treat them as **committed artifacts**, not as a guarantee of what you last ran locally—**re-run** the baseline script from the correct working directory if you need fresh outputs.

### Repository structure

Numbered folders are intentional; paths often contain spaces, so quote them in shells.

```
1 -- data/                      local datasets (raw data should stay uncommitted per .gitignore)
2 -- notebooks/                 exploratory notebooks
3 -- src/                       preprocessing, parsing, filtering, dataset build, baseline model scripts
4 -- results/                   generated outputs (including baseline artifacts)
5 -- logs/                      research log, evaluation notes, failure logs
6 -- evaluation/                metrics, splits, evaluation materials
7 -- reports/                   written reports
8 -- data cleaning test lab/    experimental parsing helpers
```

Root files include **`README.md`**, **`AGENTS.md`**, **`program.md`**, and **`.gitignore`**.

### Source scripts (`3 -- src/`)

| Path | Role |
|------|------|
| `3 -- src/1 -- debate_doc_parser_vF.py` | Parse a debate speech `.docx` into summary and audit CSVs |
| `3 -- src/2 -- count_tournament_disclosures_vF.py` | Tournament / disclosure counting utilities |
| `3 -- src/3 -- keep_only_tournament_docs_vF.py` | Filter or retain tournament-related disclosure documents |
| `3 -- src/4 -- build_gonzaga_dataset_vTemp.py` | Temporary / in-progress Gonzaga dataset builder |
| `3 -- src/5 -- baseline_round_model.py` | Baseline logistic-regression round-outcome model (expects local CSVs next to the working directory—see below) |

### Dependencies

There is **no** `requirements.txt` in this repository yet. Install Python packages **manually** for now (see the `pip install` hints at the top of each script—for example **`python-docx`** and **`pandas`** for the parser; **`numpy`**, **`pandas`**, and **`scikit-learn`** for the baseline model).

### How to run (examples)

Use **quoted** paths whenever a folder name contains spaces or punctuation.

**1. Clone and enter the repository**

```
git clone https://github.com/Davidx-Wu/stat-390-project
cd "C:\Users\thatd\Desktop\1 -- Statistics\Stat390DataScienceProject\stat-390-project"
```

**2. Parse one speech `.docx`** (writes outputs under `--outdir`; see `--help` for options)

```
python "3 -- src/1 -- debate_doc_parser_vF.py" --doc "path\to\speech.docx" --outdir "parser_output"
```

**3. Baseline round model** (`3 -- src/5 -- baseline_round_model.py` and the copy under `4 -- results/1 -- Baseline Model/` load **`speech_summary_all.csv`** and **`NDT_Rankings.csv`** using paths **relative to the current working directory**)

From the baseline results folder:

```
cd "4 -- results/1 -- Baseline Model"
python baseline_round_model.py
```

Other scripts in `3 -- src/` accept CLI arguments; run `python "3 -- src/<script>.py" --help` as needed.

New predictions and logs from the baseline step are written alongside the inputs when you run from **`4 -- results/1 -- Baseline Model/`** (same behavior as when this folder was populated).
