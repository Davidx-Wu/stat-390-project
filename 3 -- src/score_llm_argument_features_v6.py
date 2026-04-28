from pathlib import Path
import csv
import json
import os
import time
import urllib.error
import urllib.request


REPO = Path(__file__).resolve().parents[1]
PROMPTS_PATH = REPO / "4 -- results" / "llm_features" / "llm_argument_prompts_v6.jsonl"
OUT_PATH = REPO / "4 -- results" / "llm_features" / "llm_argument_features_v6.csv"
FAILURES_PATH = REPO / "4 -- results" / "llm_features" / "llm_argument_features_v6_failures.jsonl"

OPENAI_API_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
MAX_RETRIES = 2
REQUEST_TIMEOUT_SECONDS = 90
SCORE_FIELDS = [
    "claim_clarity",
    "warrant_strength",
    "evidence_quality",
    "impact_quality",
    "argument_clash",
    "strategic_coherence",
    "overall_argument_quality",
]
OUTPUT_FIELDS = ["row_id"] + SCORE_FIELDS


def load_prompts():
    with PROMPTS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("dataset_split") == "test":
                continue
            yield row


def already_scored_row_ids():
    if not OUT_PATH.exists():
        return set()
    with OUT_PATH.open("r", encoding="utf-8", newline="") as handle:
        return {int(row["row_id"]) for row in csv.DictReader(handle) if row.get("row_id")}


def validate_scores(row_id, data):
    if not isinstance(data, dict):
        raise ValueError("response JSON is not an object")

    output = {"row_id": int(row_id)}
    for field in SCORE_FIELDS:
        if field not in data:
            raise ValueError(f"missing field: {field}")
        try:
            value = float(data[field])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"field is not numeric: {field}") from exc
        if not 0 <= value <= 1:
            raise ValueError(f"field outside [0, 1]: {field}={value}")
        output[field] = value
    return output


def append_score(score):
    write_header = not OUT_PATH.exists()
    with OUT_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(score)


def append_failure(row_id, error, response_text=None):
    failure = {
        "row_id": int(row_id),
        "error": str(error),
        "response_text": response_text,
    }
    with FAILURES_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(failure) + "\n")


def call_llm(prompt):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Return valid JSON only. Do not include markdown or commentary.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        f"{OPENAI_API_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        response_payload = json.loads(response.read().decode("utf-8"))
    return response_payload["choices"][0]["message"]["content"]


def score_prompt(row):
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response_text = call_llm(row["prompt"])
            response_json = json.loads(response_text)
            return validate_scores(row["row_id"], response_json), response_text
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(1 + attempt)
                continue
            raise last_error


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    prompts = list(load_prompts())
    scored = already_scored_row_ids()
    pending = [row for row in prompts if int(row["row_id"]) not in scored]

    print("LLM argument feature scoring v6")
    print(f"Prompt file: {PROMPTS_PATH}")
    print(f"Prompts available: {len(prompts)}")
    print(f"Already scored: {len(scored)}")
    print(f"Prompts attempted: {len(pending)}")

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not configured; no API calls made.")
        print(f"Output path: {OUT_PATH}")
        return

    success_count = 0
    failure_count = 0
    for row in pending:
        row_id = int(row["row_id"])
        try:
            score, _ = score_prompt(row)
            append_score(score)
            success_count += 1
        except Exception as exc:
            append_failure(row_id, exc)
            failure_count += 1

    print(f"Successful scores: {success_count}")
    print(f"Failed scores: {failure_count}")
    print(f"Output path: {OUT_PATH}")
    print(f"Failure path: {FAILURES_PATH}")


if __name__ == "__main__":
    main()
