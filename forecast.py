import pandas as pd
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
import argparse


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments and return them as a Namespace.
    """
    parser = argparse.ArgumentParser(description="Project Burndown Forecast")
    parser.add_argument(
        "total_items", type=int, help="Total number of items to be burned"
    )
    parser.add_argument(
        "total_points", type=int, help="Total number of points to be burned"
    )
    parser.add_argument(
        "deadline",
        type=lambda d: datetime.strptime(d, "%Y-%m-%d"),
        help="Project deadline (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--pert_factor",
        type=int,
        default=3,
        help="Number of largest and smallest values to use in PERT calculation (default: 3)",
    )
    parser.add_argument(
        "--stats_file",
        default="statistics.csv",
        help="Path to the CSV file containing statistics",
    )
    return parser.parse_args()


def read_and_clean_data(file_path: str) -> pd.DataFrame:
    """
    Read the CSV from file_path, clean data, and return a DataFrame.
    """
    df = pd.read_csv(
        file_path,
        sep=";",
        names=["date", "no_items", "no_points"],
        header=0,
        dtype=str,
        on_bad_lines="skip",
    )
    df.replace(r"^\s*$", pd.NA, regex=True, inplace=True)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    df.dropna(subset=["date"], inplace=True)
    df.sort_values("date", inplace=True)
    df["no_items"] = pd.to_numeric(df["no_items"], errors="coerce")
    df["no_points"] = pd.to_numeric(df["no_points"], errors="coerce")
    df.dropna(subset=["no_items", "no_points"], inplace=True)
    return df


def compute_cumulative_values(
    df: pd.DataFrame, total_items: int, total_points: int
) -> pd.DataFrame:
    """
    Compute cumulative remaining items and points based on the given totals.
    """
    df["cum_items"] = df["no_items"][::-1].cumsum()[::-1] + total_items
    df["cum_points"] = df["no_points"][::-1].cumsum()[::-1] + total_points
    return df


def compute_weekly_throughput(df: pd.DataFrame) -> tuple[pd.DataFrame, float, float]:
    """
    Group data by week to compute total items and points throughput.
    """
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = df.apply(lambda r: f"{r['year']}-{r['week']}", axis=1)
    grouped = (
        df.groupby("year_week")
        .agg({"no_items": "sum", "no_points": "sum"})
        .reset_index()
    )
    avg_items = grouped["no_items"].mean()
    avg_points = grouped["no_points"].mean()
    return grouped, avg_items, avg_points


def calculate_rates(
    grouped: pd.DataFrame, total_items: int, total_points: int, pert_factor: int
) -> tuple[float, float, float, float, float, float]:
    """
    Calculate optimistic, most likely, and pessimistic rates; apply PERT formula.
    """
    days_per_week = 7.0
    optimistic_items_rate = (
        grouped["no_items"].nlargest(pert_factor).mean() / days_per_week
    )
    pessimistic_items_rate = (
        grouped["no_items"].nsmallest(pert_factor).mean() / days_per_week
    )
    most_likely_items_rate = grouped["no_items"].mean() / days_per_week
    optimistic_points_rate = (
        grouped["no_points"].nlargest(pert_factor).mean() / days_per_week
    )
    pessimistic_points_rate = (
        grouped["no_points"].nsmallest(pert_factor).mean() / days_per_week
    )
    most_likely_points_rate = grouped["no_points"].mean() / days_per_week

    # Calculate days needed based on velocity and throughput
    optimistic_time_points = total_points / optimistic_points_rate
    most_likely_time_points = total_points / most_likely_points_rate
    pessimistic_time_points = total_points / pessimistic_points_rate

    optimistic_time_items = total_items / optimistic_items_rate
    most_likely_time_items = total_items / most_likely_items_rate
    pessimistic_time_items = total_items / pessimistic_items_rate

    # Apply the PERT formula to calculate expected completion time in days
    pert_time_points = (
        optimistic_time_points + 4 * most_likely_time_points + pessimistic_time_points
    ) / 6

    pert_time_items = (
        optimistic_time_items + 4 * most_likely_time_items + pessimistic_time_items
    ) / 6

    return (
        pert_time_items,
        optimistic_items_rate,
        pessimistic_items_rate,
        pert_time_points,
        optimistic_points_rate,
        pessimistic_points_rate,
    )


def daily_forecast(
    start_val: float, daily_rate: float, start_date: datetime
) -> tuple[list[datetime], list[float]]:
    """
    Generate daily forecast until start_val reaches zero, returning x and y values.
    """
    if daily_rate <= 0:
        return [start_date], [start_val]
    x_vals, y_vals = [], []
    val = start_val
    current_date = start_date
    while val > 0:
        x_vals.append(current_date)
        y_vals.append(val)
        val -= daily_rate
        current_date += timedelta(days=1)
    x_vals.append(current_date)
    y_vals.append(0)
    return x_vals, y_vals


def plot_forecast(
    df: pd.DataFrame,
    items_x_avg: list[datetime],
    items_y_avg: list[float],
    items_x_opt: list[datetime],
    items_y_opt: list[float],
    items_x_pes: list[datetime],
    items_y_pes: list[float],
    points_x_avg: list[datetime],
    points_y_avg: list[float],
    points_x_opt: list[datetime],
    points_y_opt: list[float],
    points_x_pes: list[datetime],
    points_y_pes: list[float],
    pert_time_items: float,
    pert_time_points: float,
    deadline: datetime,
) -> None:
    """
    Plot burndown and velocity forecasts, along with a PERT-based time estimate.
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))

    days_until_deadline = (deadline - datetime.now()).days
    text_box_color = (
        "green"
        if (
            pert_time_items <= days_until_deadline
            and pert_time_points <= days_until_deadline
        )
        else "red"
    )

    text_box = plt.figtext(
        0.5,
        0.75,
        f"PERT: $E = \\frac{{O + 4M + P}}{{6}}$"
        f"\nEstimated Days (Items): {pert_time_items:.2f}"
        f"\nEstimated Days (Points): {pert_time_points:.2f}"
        f"\nDeadline in {days_until_deadline} days",
        ha="center",
        fontsize="small",
        bbox={"facecolor": "white", "alpha": 0.5, "pad": 5},
        color=text_box_color,
    )

    text_box.set_position((0.5, 0.75))
    text_box.set_transform(ax1.transAxes)

    ax1.plot(
        df["date"],
        df["cum_items"],
        label="Throughput (Items)",
        marker="o",
        color="tab:blue",
    )
    ax1.plot(
        items_x_avg,
        items_y_avg,
        label="Throughput Forecast (M)",
        linestyle="-",
        linewidth=2.5,
        color="tab:blue",
    )
    ax1.plot(
        items_x_opt,
        items_y_opt,
        label="Throughput Forecast (O)",
        linestyle="--",
        linewidth=1.5,
        color="lightblue",
        alpha=0.7,
    )
    ax1.plot(
        items_x_pes,
        items_y_pes,
        label="Throughput Forecast (P)",
        linestyle="-.",
        linewidth=1.5,
        color="lightblue",
        alpha=0.7,
    )
    ax1.set_xlabel("Time", fontsize="small")
    ax1.set_ylabel("Remaining Items", fontsize="small")

    ax2 = ax1.twinx()
    ax2.plot(
        df["date"],
        df["cum_points"],
        label="Velocity (Points)",
        marker="o",
        color="tab:orange",
    )
    ax2.plot(
        points_x_avg,
        points_y_avg,
        label="Velocity Forecast (M)",
        linestyle="-",
        linewidth=2.5,
        color="tab:orange",
    )
    ax2.plot(
        points_x_opt,
        points_y_opt,
        label="Velocity Forecast (O)",
        linestyle="--",
        linewidth=1.5,
        color="lightsalmon",
        alpha=0.7,
    )
    ax2.plot(
        points_x_pes,
        points_y_pes,
        label="Velocity Forecast (P)",
        linestyle="-.",
        linewidth=1.5,
        color="lightsalmon",
        alpha=0.7,
    )
    ax2.set_ylabel("Remaining Points", fontsize="small")

    ax1.axvline(deadline, color="red", linestyle="--", linewidth=2)
    ax1.text(
        deadline,
        ax1.get_ylim()[1],
        deadline.strftime("%Y-%m-%d"),
        color="red",
        ha="center",
        va="bottom",
    )

    ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y-%m-%d"))

    forecast_zero_dates = pd.Series(
        [
            items_x_avg[-1],
            points_x_avg[-1],
            items_x_opt[-1],
            points_x_opt[-1],
            items_x_pes[-1],
            points_x_pes[-1],
        ]
    )
    all_dates = pd.concat([df["date"], forecast_zero_dates]).unique()
    ax1.set_xticks(all_dates)

    ax1.set_xticklabels(
        [date.strftime("%Y-%m-%d") for date in all_dates], rotation=45, fontsize="small"
    )

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(
        lines_1 + lines_2,
        labels_1 + labels_2,
        loc="upper right",
        bbox_to_anchor=(1, 1),
        bbox_transform=ax1.transAxes,
        fontsize="small",
    )

    plt.title("Project Burndown Forecast", fontsize="large")
    plt.tight_layout()
    plt.show()


def main() -> None:
    """
    Orchestrate reading data, computing rates, and plotting forecasts.
    """
    args = parse_arguments()
    try:
        df = read_and_clean_data(args.stats_file)
    except FileNotFoundError:
        print(f"Error: Stats file '{args.stats_file}' not found.")
        return
    df = compute_cumulative_values(df, args.total_items, args.total_points)
    df_grouped, _, _ = compute_weekly_throughput(df)
    (
        pert_time_items,
        optimistic_items_rate,
        pessimistic_items_rate,
        pert_time_points,
        optimistic_points_rate,
        pessimistic_points_rate,
    ) = calculate_rates(
        df_grouped, args.total_items, args.total_points, args.pert_factor
    )

    items_daily_rate = args.total_items / pert_time_items if pert_time_items > 0 else 0
    points_daily_rate = (
        args.total_points / pert_time_points if pert_time_points > 0 else 0
    )

    start_date = df["date"].iloc[-1]
    last_items = df["cum_items"].iloc[-1]
    last_points = df["cum_points"].iloc[-1]

    items_x_avg, items_y_avg = daily_forecast(last_items, items_daily_rate, start_date)
    points_x_avg, points_y_avg = daily_forecast(
        last_points, points_daily_rate, start_date
    )
    items_x_opt, items_y_opt = daily_forecast(
        last_items, optimistic_items_rate, start_date
    )
    points_x_opt, points_y_opt = daily_forecast(
        last_points, optimistic_points_rate, start_date
    )
    items_x_pes, items_y_pes = daily_forecast(
        last_items, pessimistic_items_rate, start_date
    )
    points_x_pes, points_y_pes = daily_forecast(
        last_points, pessimistic_points_rate, start_date
    )

    plot_forecast(
        df,
        items_x_avg,
        items_y_avg,
        items_x_opt,
        items_y_opt,
        items_x_pes,
        items_y_pes,
        points_x_avg,
        points_y_avg,
        points_x_opt,
        points_y_opt,
        points_x_pes,
        points_y_pes,
        pert_time_items,
        pert_time_points,
        args.deadline,
    )


if __name__ == "__main__":
    main()
