import logging
import traceback
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go

from data import calculate_weekly_averages


def fill_missing_weeks(weekly_df, start_date, end_date, value_columns):

    if weekly_df.empty:
        return weekly_df

    all_weeks = []
    current = start_date
    while current <= end_date:
        iso_calendar = current.isocalendar()
        year_week = f"{iso_calendar.year}-W{iso_calendar.week:02d}"
        all_weeks.append(
            {
                "year_week": year_week,
                "start_date": current - timedelta(days=current.weekday()),
            }
        )
        current += timedelta(weeks=1)

    all_weeks_df = pd.DataFrame(all_weeks)

    result_df = all_weeks_df.merge(
        weekly_df, on="year_week", how="left", suffixes=("", "_actual")
    )

    if "start_date_actual" in result_df.columns:
        result_df["start_date"] = result_df["start_date_actual"].fillna(
            result_df["start_date"]
        )
        result_df = result_df.drop("start_date_actual", axis=1)

    result_df["start_date"] = pd.to_datetime(result_df["start_date"])

    for col in value_columns:
        if col in result_df.columns:
            result_df[col] = result_df[col].fillna(0)

    return result_df.sort_values("start_date")


def safe_numeric_convert(value, default=0.0):

    try:
        return float(value) if value is not None else default
    except ValueError, TypeError:
        return default


def parse_deadline_milestone(deadline_str, milestone_str=None):

    try:
        deadline = pd.to_datetime(deadline_str, format="mixed", errors="coerce")
    except ValueError, TypeError:
        deadline = pd.Timestamp.now() + pd.Timedelta(days=30)
        logging.getLogger("burndown_chart").warning(
            f"Invalid deadline format: {deadline_str}. Using default."
        )

    milestone = None
    if milestone_str:
        try:
            milestone = pd.to_datetime(milestone_str, format="mixed", errors="coerce")
        except ValueError, TypeError:
            logging.getLogger("burndown_chart").warning(
                f"Invalid milestone format: {milestone_str}. Ignoring milestone."
            )

    return deadline, milestone


def get_weekly_metrics(df, data_points_count=None):

    if data_points_count is not None:
        data_points_count = int(data_points_count)

    avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
        0.0,
        0.0,
        0.0,
        0.0,
    )

    if not df.empty:
        results = calculate_weekly_averages(
            df.to_dict("records"), data_points_count=data_points_count
        )
        if isinstance(results, (list, tuple)) and len(results) >= 4:
            avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
                results
            )

        avg_weekly_items = float(
            avg_weekly_items if avg_weekly_items is not None else 0.0
        )
        avg_weekly_points = float(
            avg_weekly_points if avg_weekly_points is not None else 0.0
        )
        med_weekly_items = float(
            med_weekly_items if med_weekly_items is not None else 0.0
        )
        med_weekly_points = float(
            med_weekly_points if med_weekly_points is not None else 0.0
        )

    return avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points


def calculate_forecast_completion_dates(pert_time_items, pert_time_points):

    import math  # noqa: PLC0415

    if pert_time_items is None or (
        isinstance(pert_time_items, float) and math.isnan(pert_time_items)
    ):
        items_completion_enhanced = "N/A (insufficient data)"
    else:
        current_date = datetime.now()
        items_completion_date = current_date + timedelta(days=pert_time_items)
        items_completion_str = items_completion_date.strftime("%Y-%m-%d")
        items_completion_enhanced = (
            f"{items_completion_str} ({pert_time_items:.1f} days, "
            f"{pert_time_items / 7:.1f} weeks)"
        )

    if pert_time_points is None or (
        isinstance(pert_time_points, float) and math.isnan(pert_time_points)
    ):
        points_completion_enhanced = "N/A (insufficient data)"
    else:
        current_date = datetime.now()
        points_completion_date = current_date + timedelta(days=pert_time_points)
        points_completion_str = points_completion_date.strftime("%Y-%m-%d")
        points_completion_enhanced = (
            f"{points_completion_str} ({pert_time_points:.1f} days, "
            f"{pert_time_points / 7:.1f} weeks)"
        )

    return items_completion_enhanced, points_completion_enhanced


def prepare_metrics_data(
    total_items: int,
    total_points: int,
    deadline,
    pert_time_items: float,
    pert_time_points: float,
    data_points_count: int,
    df,
    items_completion_enhanced: str,
    points_completion_enhanced: str,
    avg_weekly_items: float = 0.0,
    avg_weekly_points: float = 0.0,
    med_weekly_items: float = 0.0,
    med_weekly_points: float = 0.0,
) -> dict:

    current_date = datetime.now()

    if deadline is None or pd.isna(deadline):
        days_to_deadline = 0
        deadline_str = "No deadline set"
    else:
        days_to_deadline = max(0, (deadline - pd.Timestamp(current_date)).days)
        deadline_str = deadline.strftime("%Y-%m-%d")

    return {
        "total_items": total_items,
        "total_points": total_points,
        "deadline": deadline_str,
        "days_to_deadline": days_to_deadline,
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "avg_weekly_items": avg_weekly_items,
        "avg_weekly_points": avg_weekly_points,
        "med_weekly_items": med_weekly_items,
        "med_weekly_points": med_weekly_points,
        "data_points_used": int(data_points_count)
        if data_points_count is not None and isinstance(data_points_count, (int, float))
        else (len(df) if hasattr(df, "__len__") else 0),
        "data_points_available": len(df) if hasattr(df, "__len__") else 0,
        "items_completion_enhanced": items_completion_enhanced,
        "points_completion_enhanced": points_completion_enhanced,
    }


def generate_burndown_forecast(
    last_value, avg_rate, opt_rate, pes_rate, start_date, end_date
):

    today = datetime.now()
    absolute_max_date = today + timedelta(days=3653)
    MAX_FORECAST_DAYS = 3653

    days_span = (end_date - start_date).days
    if days_span <= 0:
        days_span = 1

    days_to_zero_avg = min(
        MAX_FORECAST_DAYS,
        int(last_value / avg_rate) if avg_rate > 0.001 else days_span * 2,
    )
    days_to_zero_opt = min(
        MAX_FORECAST_DAYS,
        int(last_value / opt_rate) if opt_rate > 0.001 else days_span * 2,
    )
    days_to_zero_pes = min(
        MAX_FORECAST_DAYS,
        int(last_value / pes_rate) if pes_rate > 0.001 else days_span * 2,
    )

    max_days = min(
        MAX_FORECAST_DAYS,
        max(days_span, days_to_zero_avg, days_to_zero_opt, days_to_zero_pes),
    )

    dates_avg = [
        start_date + timedelta(days=i)
        for i in range(min(max_days, days_to_zero_avg) + 1)
        if start_date + timedelta(days=i) <= absolute_max_date
    ]
    dates_opt = [
        start_date + timedelta(days=i)
        for i in range(min(max_days, days_to_zero_opt) + 1)
        if start_date + timedelta(days=i) <= absolute_max_date
    ]
    dates_pes = [
        start_date + timedelta(days=i)
        for i in range(min(max_days, days_to_zero_pes) + 1)
        if start_date + timedelta(days=i) <= absolute_max_date
    ]

    avg_values = []
    opt_values = []
    pes_values = []

    for i in range(len(dates_avg)):
        remaining_avg = max(0, last_value - (avg_rate * i))
        avg_values.append(remaining_avg)

    for i in range(len(dates_opt)):
        remaining_opt = max(0, last_value - (opt_rate * i))
        opt_values.append(remaining_opt)

    for i in range(len(dates_pes)):
        remaining_pes = max(0, last_value - (pes_rate * i))
        pes_values.append(remaining_pes)

    return {
        "avg": (dates_avg, avg_values),
        "opt": (dates_opt, opt_values),
        "pes": (dates_pes, pes_values),
    }


def format_hover_template_fix(
    title=None, fields=None, extra_info=None, include_extra_tag=True
):

    template = []

    if title:
        template.append(f"<b>{title}</b><br>")

    if fields:
        for label, value in fields.items():
            template.append(f"{label}: {value}<br>")

    hover_text = "".join(template)

    if include_extra_tag:
        if extra_info:
            return f"{hover_text}<extra>{extra_info}</extra>"
        return f"{hover_text}<extra></extra>"

    return hover_text


def handle_forecast_error(e):

    error_trace = traceback.format_exc()
    logger = logging.getLogger("burndown_chart")
    logger.error(f"Error in create_forecast_plot: {str(e)}\n{error_trace}")

    fig = go.Figure()
    fig.add_annotation(
        text=f"Error in forecast plot generation:<br>{str(e)}",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="red"),
    )

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.5,
                y=0.4,
                xanchor="center",
                yanchor="top",
                buttons=[
                    dict(
                        label="Show Error Details",
                        method="update",
                        args=[
                            {},
                            {
                                "annotations": [
                                    {
                                        "text": (
                                            "Error in forecast plot generation:<br>"
                                            f"{str(e)}<br><br>"
                                            "Stack trace (for developers):<br>"
                                            f"{error_trace.replace(chr(10), '<br>')}"
                                        ),
                                        "xref": "paper",
                                        "yref": "paper",
                                        "x": 0.5,
                                        "y": 0.5,
                                        "showarrow": False,
                                        "font": dict(size=12, color="red"),
                                        "align": "left",
                                        "bgcolor": "rgba(255, 255, 255, 0.9)",
                                        "bordercolor": "red",
                                        "borderwidth": 1,
                                        "borderpad": 4,
                                    }
                                ]
                            },
                        ],
                    )
                ],
            )
        ]
    )

    safe_pert_data = {
        "pert_time_items": 0.0,
        "pert_time_points": 0.0,
        "items_completion_enhanced": "Error in calculation",
        "points_completion_enhanced": "Error in calculation",
        "days_to_deadline": 0,
        "avg_weekly_items": 0.0,
        "avg_weekly_points": 0.0,
        "med_weekly_items": 0.0,
        "med_weekly_points": 0.0,
        "error": str(e),
        "forecast_timestamp": datetime.now().isoformat(),
    }

    return fig, safe_pert_data


def identify_significant_scope_growth(df, threshold_pct=10):

    if df.empty:
        return []

    significant_periods = []
    current_period = None

    df = df.copy().sort_values("date")
    df["items_pct_change"] = df["cum_scope_items"].pct_change() * 100
    df["points_pct_change"] = df["cum_scope_points"].pct_change() * 100

    for _i, row in df.iterrows():
        if (
            row["items_pct_change"] > threshold_pct
            or row["points_pct_change"] > threshold_pct
        ):
            if current_period is None:
                current_period = {
                    "start_date": row["date"],
                    "end_date": row["date"],
                    "max_items_pct": row["items_pct_change"]
                    if not pd.isna(row["items_pct_change"])
                    else 0,
                    "max_points_pct": row["points_pct_change"]
                    if not pd.isna(row["points_pct_change"])
                    else 0,
                }
            else:
                current_period["end_date"] = row["date"]
                if (
                    not pd.isna(row["items_pct_change"])
                    and row["items_pct_change"] > current_period["max_items_pct"]
                ):
                    current_period["max_items_pct"] = row["items_pct_change"]
                if (
                    not pd.isna(row["points_pct_change"])
                    and row["points_pct_change"] > current_period["max_points_pct"]
                ):
                    current_period["max_points_pct"] = row["points_pct_change"]
        else:
            if current_period is not None:
                if (
                    current_period["end_date"] - current_period["start_date"]
                ).days >= 0:
                    significant_periods.append(current_period)
                current_period = None

    if current_period is not None:
        current_period["end_date"] = current_period["end_date"] + pd.Timedelta(days=1)
        significant_periods.append(current_period)

    return significant_periods
