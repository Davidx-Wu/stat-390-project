from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


REPO = Path(__file__).resolve().parents[1]
DATA_PATH = REPO / "4 -- results" / "processed_datasets" / "gonzaga_speech_dataset_v1.csv"
OUT_DIR = REPO / "4 -- results" / "diagnostics"

OUTCOME_COL = "win_loss"
TEAM_COL = "team_code"
ROUND_COL = "round_number"
CARD_COUNT_COL = "num_cards_total"

WIDTH = 1000
HEIGHT = 650
MARGIN_LEFT = 95
MARGIN_RIGHT = 40
MARGIN_TOP = 80
MARGIN_BOTTOM = 115
BG = "white"
INK = "#202124"
GRID = "#dadce0"
BAR = "#2f6f73"


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), str(text), font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_centered(draw, xy, text, font, fill=INK):
    x, y = xy
    width, height = text_size(draw, text, font)
    draw.text((x - width / 2, y - height / 2), str(text), font=font, fill=fill)


def nice_axis_max(value):
    if value <= 10:
        return max(1, value)
    base = 10 ** (len(str(int(value))) - 1)
    return int(((value + base - 1) // base) * base)


def save_bar_chart(series, title, x_label, y_label, output_path):
    series = series.fillna(0)
    font = ImageFont.load_default()
    title_font = ImageFont.load_default(size=24)
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    plot_left = MARGIN_LEFT
    plot_top = MARGIN_TOP
    plot_right = WIDTH - MARGIN_RIGHT
    plot_bottom = HEIGHT - MARGIN_BOTTOM
    plot_width = plot_right - plot_left
    plot_height = plot_bottom - plot_top

    ymax = nice_axis_max(max(1, int(series.max())))
    draw.text((plot_left, 25), title, font=title_font, fill=INK)

    for i in range(6):
        y_value = ymax * i / 5
        y = plot_bottom - (y_value / ymax) * plot_height
        draw.line((plot_left, y, plot_right, y), fill=GRID)
        draw.text((18, y - 7), str(int(y_value)), font=font, fill=INK)

    draw.line((plot_left, plot_top, plot_left, plot_bottom), fill=INK, width=2)
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill=INK, width=2)

    count = len(series)
    gap = 8
    bar_width = max(3, (plot_width - gap * (count + 1)) / max(1, count))

    for index, (label, value) in enumerate(series.items()):
        x0 = plot_left + gap + index * (bar_width + gap)
        x1 = x0 + bar_width
        y0 = plot_bottom - (float(value) / ymax) * plot_height
        draw.rectangle((x0, y0, x1, plot_bottom), fill=BAR)
        draw_centered(draw, ((x0 + x1) / 2, y0 - 11), int(value), font)

        label_text = str(label)
        if len(label_text) > 18:
            label_text = label_text[:15] + "..."
        draw_centered(draw, ((x0 + x1) / 2, plot_bottom + 18), label_text, font)

    draw_centered(draw, ((plot_left + plot_right) / 2, HEIGHT - 35), x_label, font)
    draw.text((18, plot_top - 30), y_label, font=font, fill=INK)
    img.save(output_path)


def histogram_counts(values, bins):
    values = pd.to_numeric(values, errors="coerce").dropna()
    if values.empty:
        return pd.Series(dtype=int)

    min_value = float(values.min())
    max_value = float(values.max())
    if min_value == max_value:
        return pd.Series({str(int(min_value)): len(values)})

    counts = pd.cut(values, bins=bins, include_lowest=True).value_counts().sort_index()
    labels = []
    for interval in counts.index:
        left = int(interval.left)
        right = int(interval.right)
        labels.append(f"{left}-{right}")
    counts.index = labels
    return counts


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)

    win_loss_counts = df[OUTCOME_COL].value_counts().sort_index()
    speeches_per_round = df[ROUND_COL].value_counts().sort_index()
    speeches_per_team = histogram_counts(df[TEAM_COL].value_counts(), bins=20)
    card_count_distribution = histogram_counts(df[CARD_COUNT_COL], bins=30)

    save_bar_chart(
        win_loss_counts,
        "Win/Loss Distribution",
        "Outcome",
        "Number of speeches",
        OUT_DIR / "win_loss_distribution.png",
    )
    save_bar_chart(
        speeches_per_round,
        "Speeches per Round",
        "Round number",
        "Number of speeches",
        OUT_DIR / "speeches_per_round.png",
    )
    save_bar_chart(
        speeches_per_team,
        "Speeches per Team",
        "Speeches per team",
        "Number of teams",
        OUT_DIR / "speeches_per_team.png",
    )
    save_bar_chart(
        card_count_distribution,
        "Card Count Distribution",
        "Total cards",
        "Number of speeches",
        OUT_DIR / "card_count_distribution.png",
    )

    print("Dataset:", DATA_PATH)
    print("Rows:", len(df))
    print("Columns used:")
    print(f"  outcome: {OUTCOME_COL}")
    print(f"  team: {TEAM_COL}")
    print(f"  round: {ROUND_COL}")
    print(f"  card count: {CARD_COUNT_COL}")
    print("Diagnostics saved to:", OUT_DIR)


if __name__ == "__main__":
    main()
