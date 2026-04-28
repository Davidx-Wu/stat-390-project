from pathlib import Path
import json

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
DATA_PATH = REPO / "4 -- results" / "processed_datasets" / "gonzaga_speech_dataset_v2_with_text.csv"
OUT_DIR = REPO / "4 -- results" / "llm_features"
PROMPTS_OUT = OUT_DIR / "llm_argument_prompts_v6.jsonl"
DIAGNOSTIC_OUT = OUT_DIR / "llm_argument_features_v6_diagnostic.txt"

SPLIT_COL = "dataset_split"
SCORING_SPLITS = {"train", "validation"}
PREFERRED_TEXT_COLUMNS = [
    "argument_text_combined",
    "card_text_combined",
]
METADATA_EXCLUSIONS = {
    "win_loss",
    "team_code",
    "opponent",
    "judge",
    "tournament_name",
    "dataset_split",
    "source_file",
}
MAX_TEXT_CHARS = 6000

PROMPT_TEMPLATE = """You are evaluating a policy debate speech excerpt for argument quality, not predicting the winner.

Do not infer from team names, school names, judge names, tournament names, or speaker identity. Score only the argument content.

Evaluate the excerpt on:
1. claim clarity
2. warrant strength
3. evidence quality
4. impact quality
5. argument clash/comparison
6. strategic coherence

Return JSON only:
{{
  "claim_clarity": 0.0,
  "warrant_strength": 0.0,
  "evidence_quality": 0.0,
  "impact_quality": 0.0,
  "argument_clash": 0.0,
  "strategic_coherence": 0.0,
  "overall_argument_quality": 0.0
}}

Speech excerpt:
<<<{text}>>>"""


def usable_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def choose_text(row):
    for column in PREFERRED_TEXT_COLUMNS:
        text = usable_text(row.get(column, ""))
        if text:
            return column, text
    return None, ""


def write_diagnostic(message):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DIAGNOSTIC_OUT.write_text(message + "\n", encoding="utf-8")
    print(message)
    print(f"Diagnostic saved to: {DIAGNOSTIC_OUT}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    work_df = df[df[SPLIT_COL].isin(SCORING_SPLITS)].copy()

    missing_text_columns = [column for column in PREFERRED_TEXT_COLUMNS if column not in df.columns]
    if missing_text_columns:
        message = (
            "LLM argument prompts cannot be built because expected text columns are missing: "
            f"{missing_text_columns}."
        )
        write_diagnostic(message)
        return

    rows_to_prompt = []
    text_column_counts = {column: 0 for column in PREFERRED_TEXT_COLUMNS}
    rows_skipped_missing_text = 0
    for row_id, row in work_df.iterrows():
        text_column, text = choose_text(row)
        if not text:
            rows_skipped_missing_text += 1
            continue
        text_column_counts[text_column] += 1
        truncated = len(text) > MAX_TEXT_CHARS
        rows_to_prompt.append(
            {
                "row_id": int(row_id),
                "dataset_split": row[SPLIT_COL],
                "source_text_column": text_column,
                "text_truncated": truncated,
                "prompt": PROMPT_TEMPLATE.format(text=text[:MAX_TEXT_CHARS]),
            }
        )

    with PROMPTS_OUT.open("w", encoding="utf-8") as handle:
        for item in rows_to_prompt:
            handle.write(json.dumps(item) + "\n")

    print("LLM argument prompt dry run")
    print(f"Input dataset: {DATA_PATH}")
    print(f"total rows: {len(df)}")
    print(f"train/validation rows: {len(work_df)}")
    print(f"prompt rows created: {len(rows_to_prompt)}")
    print(f"rows skipped for missing text: {rows_skipped_missing_text}")
    print("text column usage counts:")
    for column in PREFERRED_TEXT_COLUMNS:
        print(f"  {column}: {text_column_counts[column]}")
    print(f"output path: {PROMPTS_OUT}")


if __name__ == "__main__":
    main()
