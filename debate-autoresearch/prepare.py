"""
FROZEN -- Do not modify this file during AutoResearch loops.

Data loading, train/validation split, evaluation metric, logging, and plotting
for the Gonzaga debate outcome prediction project.
"""
from pathlib import Path
import csv

import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from sklearn.metrics import accuracy_score, confusion_matrix


BASE_DIR = Path(__file__).resolve().parent
REPO = BASE_DIR.parent
DATA_PATH = REPO / "4 -- results" / "processed_datasets" / "gonzaga_speech_dataset_v2_with_text.csv"
RESULTS_FILE = BASE_DIR / "results.tsv"
PERFORMANCE_PNG = BASE_DIR / "performance.png"

TARGET_COL = "win_loss"
SPLIT_COL = "dataset_split"
TRAIN_SPLIT = "train"
VALIDATION_SPLIT = "validation"

ALLOWED_FEATURE_COLUMNS = [
    "num_positions",
    "num_adv_inh_solv",
    "num_offs",
    "num_cards_total",
    "num_cards_with_highlight",
    "total_highlighted_words",
]


def encode_target(series):
    return series.map({"L": 0, "W": 1})


def load_data():
    """Load v2 and return train/validation matrices using frozen safe features."""
    df = pd.read_csv(DATA_PATH)
    train_df = df[df[SPLIT_COL] == TRAIN_SPLIT].copy()
    val_df = df[df[SPLIT_COL] == VALIDATION_SPLIT].copy()

    if train_df.empty:
        raise ValueError("No train rows found.")
    if val_df.empty:
        raise ValueError("No validation rows found.")

    X_train = train_df[ALLOWED_FEATURE_COLUMNS].fillna(0)
    y_train = encode_target(train_df[TARGET_COL])
    X_val = val_df[ALLOWED_FEATURE_COLUMNS].fillna(0)
    y_val = encode_target(val_df[TARGET_COL])

    if y_train.isna().any() or y_val.isna().any():
        raise ValueError("Target column contains values outside expected labels: W, L.")

    return X_train, y_train, X_val, y_val, ALLOWED_FEATURE_COLUMNS


def evaluate(model, X_val, y_val):
    """Compute frozen validation metrics. Higher accuracy is better."""
    y_pred = model.predict(X_val)
    accuracy = float(accuracy_score(y_val, y_pred))

    majority_class = y_val.mode().iloc[0]
    majority_pred = pd.Series(majority_class, index=y_val.index)
    majority_accuracy = float(accuracy_score(y_val, majority_pred))

    matrix = confusion_matrix(y_val, y_pred, labels=[0, 1])
    tn, fp, fn, tp = [int(value) for value in matrix.ravel()]
    return {
        "validation_accuracy": accuracy,
        "majority_baseline": majority_accuracy,
        "confusion_matrix": matrix,
        "true_L_pred_L": tn,
        "true_L_pred_W": fp,
        "true_W_pred_L": fn,
        "true_W_pred_W": tp,
    }


def log_result(experiment_id, metrics, status, description):
    """Append one experiment row to debate-autoresearch/results.tsv."""
    file_exists = RESULTS_FILE.exists()
    with RESULTS_FILE.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        if not file_exists:
            writer.writerow(
                [
                    "experiment",
                    "validation_accuracy",
                    "majority_baseline",
                    "true_L_pred_L",
                    "true_L_pred_W",
                    "true_W_pred_L",
                    "true_W_pred_W",
                    "status",
                    "description",
                ]
            )
        writer.writerow(
            [
                experiment_id,
                f"{metrics['validation_accuracy']:.6f}",
                f"{metrics['majority_baseline']:.6f}",
                metrics["true_L_pred_L"],
                metrics["true_L_pred_W"],
                metrics["true_W_pred_L"],
                metrics["true_W_pred_W"],
                status,
                description,
            ]
        )


def plot_results(save_path=PERFORMANCE_PNG):
    """Plot validation accuracy over experiments from results.tsv."""
    if not RESULTS_FILE.exists():
        print("No results.tsv found. Run an experiment first.")
        return

    rows = []
    with RESULTS_FILE.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
    if not rows:
        print("No results to plot.")
        return

    accuracies = [float(row["validation_accuracy"]) for row in rows]
    descriptions = [row["description"] for row in rows]
    statuses = [row["status"] for row in rows]

    width, height = 900, 520
    margin_left, margin_right = 70, 30
    margin_top, margin_bottom = 55, 115
    plot_left = margin_left
    plot_right = width - margin_right
    plot_top = margin_top
    plot_bottom = height - margin_bottom
    plot_width = plot_right - plot_left
    plot_height = plot_bottom - plot_top

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    title_font = ImageFont.load_default(size=22)

    draw.text((plot_left, 20), "Debate AutoResearch Validation Accuracy", font=title_font, fill="#202124")
    for i in range(6):
        value = i / 5
        y = plot_bottom - value * plot_height
        draw.line((plot_left, y, plot_right, y), fill="#dadce0")
        draw.text((18, y - 6), f"{value:.1f}", font=font, fill="#202124")
    draw.line((plot_left, plot_top, plot_left, plot_bottom), fill="#202124", width=2)
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill="#202124", width=2)

    colors = {"baseline": "#1a73e8", "keep": "#188038", "discard": "#d93025"}
    count = len(accuracies)
    x_step = plot_width / max(1, count - 1)
    points = []
    for index, accuracy in enumerate(accuracies):
        x = plot_left + index * x_step if count > 1 else (plot_left + plot_right) / 2
        y = plot_bottom - accuracy * plot_height
        points.append((x, y))

    if len(points) > 1:
        draw.line(points, fill="#5f6368", width=2)
    for index, (x, y) in enumerate(points):
        color = colors.get(statuses[index], "#5f6368")
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)
        draw.text((x - 18, y - 20), f"{accuracies[index]:.3f}", font=font, fill="#202124")
        label = descriptions[index][:18]
        draw.text((x - 35, plot_bottom + 18), label, font=font, fill="#202124")

    img.save(save_path)
    print(f"Saved {save_path}")


if __name__ == "__main__":
    plot_results()
