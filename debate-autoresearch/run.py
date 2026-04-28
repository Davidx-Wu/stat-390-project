"""
FROZEN -- Do not modify this file during AutoResearch loops.

Run one experiment:
    python debate-autoresearch/run.py "baseline logistic" --baseline
    python debate-autoresearch/run.py "try interaction features"
"""
import subprocess
import sys
import time

from prepare import load_data, evaluate, log_result, plot_results


def get_git_hash():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "no-git"


def parse_args(args):
    status = "keep"
    description_parts = []
    for arg in args:
        if arg == "--baseline":
            status = "baseline"
        elif arg == "--discard":
            status = "discard"
        else:
            description_parts.append(arg)
    description = " ".join(description_parts) if description_parts else "experiment"
    return description, status


def main():
    description, status = parse_args(sys.argv[1:])

    X_train, y_train, X_val, y_val, feature_names = load_data()
    print(f"Data: {X_train.shape[0]} train, {X_val.shape[0]} validation, {len(feature_names)} features")

    from model import build_model

    model = build_model()
    print(f"Model: {model}")

    start = time.time()
    model.fit(X_train, y_train)
    elapsed = time.time() - start
    print(f"Training time: {elapsed:.2f}s")

    metrics = evaluate(model, X_val, y_val)
    print(f"validation_accuracy: {metrics['validation_accuracy']:.6f}")
    print(f"majority_baseline:   {metrics['majority_baseline']:.6f}")
    print("confusion_matrix, labels L/W:")
    print(metrics["confusion_matrix"])

    log_result(get_git_hash(), metrics, status, description)
    plot_results()
    print(f"Result logged to debate-autoresearch/results.tsv (status={status})")


if __name__ == "__main__":
    main()
