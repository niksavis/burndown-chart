import argparse
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def parse_arguments() -> argparse.Namespace:
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
    args = parser.parse_args()
    if args.pert_factor < 3:
        parser.error("--pert_factor cannot be lower than 3")
    return args


def read_and_clean_data(file_path: str) -> pd.DataFrame:
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
    df["cum_items"] = df["no_items"][::-1].cumsum()[::-1] + total_items
    df["cum_points"] = df["no_points"][::-1].cumsum()[::-1] + total_points
    return df


def compute_weekly_throughput(df: pd.DataFrame):
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = df.apply(lambda r: f"{r['year']}-{r['week']}", axis=1)
    grouped = (
        df.groupby("year_week")
        .agg({"no_items": "sum", "no_points": "sum"})
        .reset_index()
    )
    return grouped


def calculate_rates(
    grouped: pd.DataFrame, total_items: int, total_points: int, pert_factor: int
):
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

    optimistic_time_items = (
        total_items / optimistic_items_rate if optimistic_items_rate else 0
    )
    most_likely_time_items = (
        total_items / most_likely_items_rate if most_likely_items_rate else 0
    )
    pessimistic_time_items = (
        total_items / pessimistic_items_rate if pessimistic_items_rate else 0
    )

    optimistic_time_points = (
        total_points / optimistic_points_rate if optimistic_points_rate else 0
    )
    most_likely_time_points = (
        total_points / most_likely_points_rate if most_likely_points_rate else 0
    )
    pessimistic_time_points = (
        total_points / pessimistic_points_rate if pessimistic_points_rate else 0
    )

    pert_time_items = (
        optimistic_time_items + 4 * most_likely_time_items + pessimistic_time_items
    ) / 6
    pert_time_points = (
        optimistic_time_points + 4 * most_likely_time_points + pessimistic_time_points
    ) / 6

    return (
        pert_time_items,
        optimistic_items_rate,
        pessimistic_items_rate,
        pert_time_points,
        optimistic_points_rate,
        pessimistic_points_rate,
    )


def daily_forecast(start_val: float, daily_rate: float, start_date: datetime):
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
    deadline,
):
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Historical items
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["cum_items"],
            mode="lines+markers",
            name="Throughput",
            hovertemplate="%{x}<br>Items: %{y}<extra></extra>",
        ),
        secondary_y=False,
    )
    # Forecast (Items)
    fig.add_trace(
        go.Scatter(
            x=items_x_avg,
            y=items_y_avg,
            mode="lines",
            name="Throughput Forecast (M)",
            hovertemplate="%{x}<br>Items: %{y}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=items_x_opt,
            y=items_y_opt,
            mode="lines",
            name="Throughput Forecast (O)",
            hovertemplate="%{x}<br>Items: %{y}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=items_x_pes,
            y=items_y_pes,
            mode="lines",
            name="Throughput Forecast (P)",
            hovertemplate="%{x}<br>Items: %{y}<extra></extra>",
        ),
        secondary_y=False,
    )

    # Historical points
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["cum_points"],
            mode="lines+markers",
            name="Velocity",
            hovertemplate="%{x}<br>Points: %{y}<extra></extra>",
        ),
        secondary_y=True,
    )
    # Forecast (Points)
    fig.add_trace(
        go.Scatter(
            x=points_x_avg,
            y=points_y_avg,
            mode="lines",
            name="Velocity Forecast (M)",
            hovertemplate="%{x}<br>Points: %{y}<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=points_x_opt,
            y=points_y_opt,
            mode="lines",
            name="Velocity Forecast (O)",
            hovertemplate="%{x}<br>Points: %{y}<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=points_x_pes,
            y=points_y_pes,
            mode="lines",
            name="Velocity Forecast (P)",
            hovertemplate="%{x}<br>Points: %{y}<extra></extra>",
        ),
        secondary_y=True,
    )

    # Deadline line
    fig.add_shape(
        type="line",
        x0=deadline,
        x1=deadline,
        y0=0,
        y1=max(df["cum_items"].max(), df["cum_points"].max()),
        line=dict(color="Red", dash="dash"),
    )
    fig.add_annotation(
        x=deadline,
        y=max(df["cum_items"].max(), df["cum_points"].max()),
        text="Deadline",
        showarrow=True,
        arrowhead=1,
    )

    # New PERT annotation at top center
    items_color = (
        "green" if pert_time_items <= (deadline - datetime.now()).days else "red"
    )
    points_color = (
        "green" if pert_time_points <= (deadline - datetime.now()).days else "red"
    )

    fig.add_annotation(
        x=0.5,
        y=1,
        xref="paper",
        yref="paper",
        text=(
            "PERT Formula: E = (O + 4M + P) / 6"
            f"<br>Estimated Days (Items): <span style='color:{items_color}'>{pert_time_items:.2f}</span>"
            f"<br>Estimated Days (Points): <span style='color:{points_color}'>{pert_time_points:.2f}</span>"
            f"<br>Deadline in: {(deadline - datetime.now()).days} days"
        ),
        showarrow=False,
        bordercolor="black",
        borderwidth=1,
        font=dict(color="black"),
    )

    fig.update_layout(
        title="Project Burndown Forecast",
        xaxis=dict(
            title="Time",
            tickmode="auto",
            nticks=20,  # Increase to show more x-axis ticks
        ),
        yaxis=dict(title="Remaining Items", range=[0, None]),  # Set y-axis range
        yaxis2=dict(
            title="Remaining Points",
            overlaying="y",
            side="right",
            range=[0, None],  # Set y-axis2 range
        ),
        legend=dict(x=1, y=1),
        hovermode="closest",
        margin=dict(r=200),  # Add extra right margin to avoid cutting off text
    )
    fig.show()


def main():
    args = parse_arguments()
    # Read data with same logic as forecast.py
    df = read_and_clean_data(args.stats_file)
    df = compute_cumulative_values(df, args.total_items, args.total_points)
    grouped = compute_weekly_throughput(df)

    # Match forecast.py's PERT-based rate calculation
    (
        pert_time_items,
        optimistic_items_rate,
        pessimistic_items_rate,
        pert_time_points,
        optimistic_points_rate,
        pessimistic_points_rate,
    ) = calculate_rates(grouped, args.total_items, args.total_points, args.pert_factor)

    # Compute daily rates from PERT
    items_daily_rate = args.total_items / pert_time_items if pert_time_items > 0 else 0
    points_daily_rate = (
        args.total_points / pert_time_points if pert_time_points > 0 else 0
    )

    start_date = df["date"].iloc[-1]
    last_items = df["cum_items"].iloc[-1]
    last_points = df["cum_points"].iloc[-1]

    # Forecast lines (M, O, P) for items
    items_x_avg, items_y_avg = daily_forecast(last_items, items_daily_rate, start_date)
    items_x_opt, items_y_opt = daily_forecast(
        last_items, optimistic_items_rate, start_date
    )
    items_x_pes, items_y_pes = daily_forecast(
        last_items, pessimistic_items_rate, start_date
    )

    # Forecast lines (M, O, P) for points
    points_x_avg, points_y_avg = daily_forecast(
        last_points, points_daily_rate, start_date
    )
    points_x_opt, points_y_opt = daily_forecast(
        last_points, optimistic_points_rate, start_date
    )
    points_x_pes, points_y_pes = daily_forecast(
        last_points, pessimistic_points_rate, start_date
    )

    # Build plot
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
