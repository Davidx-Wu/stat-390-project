# stat-390-project
This project tests whether LLM-based scores of argument quality - claim, warrant, and impact - can predict policy debate round outcomes better than simple heuristics like evidence quantity or source type, using a few hundred cards and 50-150 rounds from a single topic area.

Here is a **clean first version of your `README.md`** that matches the course requirements and your project idea. You can **copy and paste this directly** into the README file.

---

# STAT 390 Capstone Project

## Evaluating Debate Argument Quality with Large Language Models

### Problem

Can large language models evaluate the quality of policy debate arguments and predict round outcomes better than simple heuristics based on evidence quantity or source type?

### Data

The dataset consists of:

* A few hundred **policy debate evidence cards**
* Approximately **X debate rounds (to be specified one cleaning concludes)**
* Each round includes a **known winner**

Cards contain argument text and metadata (e.g., source, citation). These are used to build both baseline features and LLM-derived argument quality scores.

### Method

The project compares two approaches:

**Baseline heuristics**

* Evidence quantity (number of cards)
* Source type or citation strength

**LLM-based argument evaluation**

* Extract structured argument components:

  * Claim
  * Warrant
  * Impact
* Score argument quality using a large language model
* Use these features to predict debate round outcomes

### Metric

Primary evaluation metric:

**Round outcome prediction accuracy**

Secondary metrics may include:

* F1 score
* Precision / recall

Performance will be compared between baseline heuristics and LLM-derived features.

### Current Best Result

Baseline not yet implemented.

Current best result: **TBD**

### Repository Structure

```
data/           raw and processed datasets
src/            preprocessing, feature extraction, and models
notebooks/      exploratory analysis
evaluation/     metrics, dataset splits, and evaluation scripts
logs/           research log and failure log
results/        figures, tables, and predictions
reports/        final report materials
```

### How to Run the Project

1. Clone the repository

```
git clone https://github.com/Davidx-Wu/stat-390-project 
cd "C:\Users\thatd\Desktop\1 -- Statistics\Stat390DataScienceProject\stat-390-project"
```

2. Install dependencies

```
pip install -r requirements.txt
```

3. Run baseline experiment

```
python src/baseline.py
```

4. Run LLM evaluation pipeline

```
python src/llm_eval.py
```

Results will be saved in the `results/` directory.

If you want, the **next step we should do** (and it will save you headaches later) is write a **very short `requirements.txt` and `.gitignore`**, because those two things are what make your repo actually runnable by your TA.
