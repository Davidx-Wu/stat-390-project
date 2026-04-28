from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
DATA_PATH = REPO / "4 -- results" / "processed_datasets" / "gonzaga_speech_dataset_v1.csv"
OUT_DIR = REPO / "4 -- results" / "diagnostics"
BALANCE_OUT = OUT_DIR / "dataset_balance_summary.csv"
TEAM_OUT = OUT_DIR / "team_record_summary.csv"

OUTCOME_COL = "win_loss"
SPLIT_COL = "dataset_split"
TEAM_COL = "team_code"
MIN_TEAM_SPEECHES = 5


def add_rates(counts):
    summary = counts.copy()
    for outcome in ["W", "L"]:
        if outcome not in summary.columns:
            summary[outcome] = 0
    summary["total_speeches"] = summary["W"] + summary["L"]
    summary["win_rate"] = summary["W"] / summary["total_speeches"]
    return summary[["W", "L", "total_speeches", "win_rate"]]


def format_rate(value):
    return f"{value:.3f}"


def print_section(title, frame):
    print(f"\n{title}")
    print(frame.to_string())


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)

    overall_counts = add_rates(pd.crosstab(index=["overall"], columns=df[OUTCOME_COL]))
    split_counts = add_rates(pd.crosstab(index=df[SPLIT_COL], columns=df[OUTCOME_COL]))
    balance_summary = pd.concat(
        [
            overall_counts.assign(group_type="overall"),
            split_counts.assign(group_type="dataset_split"),
        ]
    )
    balance_summary.index.name = "group"
    balance_summary = balance_summary.reset_index()
    balance_summary = balance_summary[["group_type", "group", "W", "L", "total_speeches", "win_rate"]]

    team_counts = add_rates(pd.crosstab(index=df[TEAM_COL], columns=df[OUTCOME_COL]))
    team_counts.index.name = TEAM_COL
    team_summary = team_counts.reset_index()
    team_summary = team_summary.sort_values(
        ["total_speeches", TEAM_COL],
        ascending=[False, True],
    )

    eligible_teams = team_summary[team_summary["total_speeches"] >= MIN_TEAM_SPEECHES]
    top_by_speeches = team_summary.head(15)
    top_by_win_rate = eligible_teams.sort_values(
        ["win_rate", "total_speeches", TEAM_COL],
        ascending=[False, False, True],
    ).head(15)
    bottom_by_win_rate = eligible_teams.sort_values(
        ["win_rate", "total_speeches", TEAM_COL],
        ascending=[True, False, True],
    ).head(15)

    flagged_teams = eligible_teams[
        (eligible_teams["win_rate"] >= 0.80) | (eligible_teams["win_rate"] <= 0.20)
    ].sort_values(["win_rate", "total_speeches", TEAM_COL], ascending=[False, False, True])

    balance_summary.to_csv(BALANCE_OUT, index=False)
    team_summary.to_csv(TEAM_OUT, index=False)

    print("Dataset balance check")
    print(f"Dataset: {DATA_PATH}")
    print(f"Rows: {len(df)}")
    print_section("1. Overall win/loss distribution", overall_counts)
    print_section("2. Win/loss distribution by dataset_split", split_counts)
    print_section("3. Team-level record", team_summary)
    print_section("4. Top 15 teams by number of speeches", top_by_speeches)
    print_section(
        f"5. Top 15 teams by win rate, minimum {MIN_TEAM_SPEECHES} speeches",
        top_by_win_rate,
    )
    print_section(
        f"6. Bottom 15 teams by win rate, minimum {MIN_TEAM_SPEECHES} speeches",
        bottom_by_win_rate,
    )

    if not flagged_teams.empty:
        print(
            "\nWarning: teams with at least "
            f"{MIN_TEAM_SPEECHES} speeches have win rate >= 0.80 or <= 0.20."
        )
        print(flagged_teams.to_string(index=False))
    else:
        print(
            "\nNo team with at least "
            f"{MIN_TEAM_SPEECHES} speeches has win rate >= 0.80 or <= 0.20."
        )

    print("\nSummary")
    print(f"Overall win rate: {format_rate(overall_counts.loc['overall', 'win_rate'])}")
    print(f"Teams summarized: {len(team_summary)}")
    print(f"Teams with at least {MIN_TEAM_SPEECHES} speeches: {len(eligible_teams)}")
    print(f"Flagged teams: {len(flagged_teams)}")
    print(f"Saved dataset balance summary: {BALANCE_OUT}")
    print(f"Saved team record summary: {TEAM_OUT}")


if __name__ == "__main__":
    main()
