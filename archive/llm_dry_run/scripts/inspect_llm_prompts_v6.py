from pathlib import Path
import json
import random
import statistics


REPO = Path(__file__).resolve().parents[1]
PROMPTS_PATH = REPO / "4 -- results" / "llm_features" / "llm_argument_prompts_v6.jsonl"
SAMPLES_OUT = REPO / "4 -- results" / "llm_features" / "llm_prompt_samples_v6.txt"
LEAKAGE_TERMS = [
    "team_code",
    "opponent",
    "judge",
    "tournament_name",
    "win_loss",
    "dataset_split",
]
RANDOM_SEED = 42


def load_prompts():
    rows = []
    with PROMPTS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def prompt_length(row):
    return len(row["prompt"])


def sample_rows(rows):
    first_two = rows[:2]
    random_pool = rows[2:] if len(rows) > 2 else rows
    rng = random.Random(RANDOM_SEED)
    random_two = rng.sample(random_pool, k=min(2, len(random_pool)))
    longest = max(rows, key=prompt_length)
    return [
        ("first_1", first_two[0] if len(first_two) > 0 else None),
        ("first_2", first_two[1] if len(first_two) > 1 else None),
        ("random_seed_42_1", random_two[0] if len(random_two) > 0 else None),
        ("random_seed_42_2", random_two[1] if len(random_two) > 1 else None),
        ("longest", longest),
    ]


def leakage_hits(rows):
    hits = {term: 0 for term in LEAKAGE_TERMS}
    for row in rows:
        prompt = row["prompt"].lower()
        for term in LEAKAGE_TERMS:
            if term.lower() in prompt:
                hits[term] += 1
    return hits


def write_samples(samples):
    SAMPLES_OUT.parent.mkdir(parents=True, exist_ok=True)
    with SAMPLES_OUT.open("w", encoding="utf-8") as handle:
        for label, row in samples:
            if row is None:
                continue
            handle.write(f"===== {label} =====\n")
            handle.write(f"row_id: {row.get('row_id')}\n")
            handle.write(f"dataset_split: {row.get('dataset_split')}\n")
            handle.write(f"source_text_column: {row.get('source_text_column')}\n")
            handle.write(f"text_truncated: {row.get('text_truncated')}\n")
            handle.write(f"prompt_char_length: {prompt_length(row)}\n\n")
            handle.write(row["prompt"])
            handle.write("\n\n")


def main():
    rows = load_prompts()
    if not rows:
        raise ValueError(f"No prompts found in {PROMPTS_PATH}")

    lengths = [prompt_length(row) for row in rows]
    truncated_count = sum(1 for row in rows if row.get("text_truncated"))
    hits = leakage_hits(rows)
    samples = sample_rows(rows)
    write_samples(samples)

    print("LLM prompt inspection v6")
    print(f"Prompt file: {PROMPTS_PATH}")
    print(f"total prompt count: {len(rows)}")
    print(f"min prompt character length: {min(lengths)}")
    print(f"median prompt character length: {int(statistics.median(lengths))}")
    print(f"max prompt character length: {max(lengths)}")
    print(f"count of truncated prompts: {truncated_count}")
    print("leakage term hits in prompt text:")
    for term in LEAKAGE_TERMS:
        print(f"  {term}: {hits[term]}")
    print("\nSample prompts:")
    for label, row in samples:
        if row is None:
            continue
        print(
            f"- {label}: row_id={row.get('row_id')}, "
            f"length={prompt_length(row)}, truncated={row.get('text_truncated')}"
        )
    print(f"\nReadable samples saved to: {SAMPLES_OUT}")


if __name__ == "__main__":
    main()
