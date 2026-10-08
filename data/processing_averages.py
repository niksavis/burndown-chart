from datetime import datetime, timedelta

import pandas as pd

from data.metrics.blending import calculate_current_week_blend
from data.metrics_calculator import calculate_forecast
from data.metrics_snapshots import get_metric_weekly_values
from data.time_period_calculator import format_year_week, get_iso_week


def calculate_weekly_averages(
    statistics_data: list[dict] | pd.DataFrame,
    data_points_count: int | None = None,
) -> tuple[float, float, float, float]:

    import logging  # noqa: PLC0415

    logger = logging.getLogger(__name__)

    if data_points_count is not None:
        data_points_count = int(data_points_count)

    if (
        statistics_data is None
        or (isinstance(statistics_data, pd.DataFrame) and statistics_data.empty)
        or (not isinstance(statistics_data, pd.DataFrame) and len(statistics_data) == 0)
    ):
        return 0, 0, 0, 0

    try:
        if data_points_count is not None and data_points_count > 0:
            weeks = []
            current_date = datetime.now()
            for _i in range(data_points_count):
                year, week = get_iso_week(current_date)
                week_label = format_year_week(year, week)
                weeks.append(week_label)
                current_date = current_date - timedelta(days=7)

            week_labels = list(reversed(weeks))

            velocity_items = get_metric_weekly_values(
                week_labels, "flow_velocity", "completed_count"
            )

            if velocity_items and len(velocity_items) >= 2:
                current_week_actual = velocity_items[-1]

                prior_weeks = velocity_items[:-1]
                forecast_weeks = (
                    prior_weeks[-4:] if len(prior_weeks) >= 4 else prior_weeks
                )

                forecast_value = 0
                if len(forecast_weeks) >= 2:
                    try:
                        forecast_data = calculate_forecast(forecast_weeks)
                        forecast_value = (
                            forecast_data.get("forecast_value", 0)
                            if forecast_data
                            else 0
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to calculate velocity forecast in "
                            f"processing.py: {e}"
                        )

                if forecast_value > 0:
                    blended_value = calculate_current_week_blend(
                        current_week_actual, forecast_value
                    )

                    velocity_items[-1] = blended_value

                    logger.info(
                        "[Blending-Dashboard] Flow Velocity - "
                        f"Actual: {current_week_actual:.1f}, "
                        f"Forecast: {forecast_value:.1f}, Blended: {blended_value:.1f}"
                    )

            if velocity_items and any(v > 0 for v in velocity_items):
                avg_items = (
                    sum(velocity_items) / len(velocity_items) if velocity_items else 0
                )
                median_items = (
                    pd.Series(velocity_items).median() if velocity_items else 0
                )

                logger.info(
                    f"[VELOCITY] Using metric snapshots: {len(velocity_items)} weeks, "
                    f"avg={avg_items:.2f}, median={median_items:.2f}"
                )

                df = pd.DataFrame(statistics_data)
                if not df.empty and "completed_points" in df.columns:
                    if "week_label" in df.columns:
                        df = df[df["week_label"].isin(week_labels)]

                    df["completed_points"] = pd.to_numeric(
                        df["completed_points"], errors="coerce"
                    ).fillna(0)

                    avg_points = df["completed_points"].mean()
                    median_points = df["completed_points"].median()
                else:
                    avg_points = 0.0
                    median_points = 0.0

                return avg_items, avg_points, median_items, median_points
            else:
                logger.warning(
                    "[VELOCITY] No metric snapshots found for "
                    f"{len(week_labels)} weeks, "
                    f"falling back to statistics"
                )
    except Exception as e:
        logger.warning(
            "[VELOCITY] Failed to load metric snapshots: "
            f"{e}, falling back to statistics"
        )

    if data_points_count is not None and data_points_count > 0:
        df_temp = pd.DataFrame(statistics_data)
        if not df_temp.empty:
            date_col = (
                "date"
                if "date" in df_temp.columns
                else ("stat_date" if "stat_date" in df_temp.columns else None)
            )
            if date_col:
                df_temp[date_col] = pd.to_datetime(
                    df_temp[date_col], errors="coerce", format="mixed"
                )
                df_temp = df_temp.dropna(subset=[date_col])
                df_temp = df_temp.sort_values(date_col, ascending=True)

                actual_weeks_available = len(df_temp)
                effective_data_points = min(data_points_count, actual_weeks_available)

                if effective_data_points < actual_weeks_available:
                    latest_date = df_temp[date_col].max()
                    cutoff_date = latest_date - timedelta(weeks=effective_data_points)  # type: ignore[possibly-unbound]
                    df_temp = df_temp[df_temp[date_col] > cutoff_date]
                    logger.info(
                        f"[VELOCITY] Filtered to {effective_data_points} weeks "
                        f"(requested {data_points_count}, "
                        f"available {actual_weeks_available})"
                    )
                else:
                    logger.info(
                        f"[VELOCITY] Using all {actual_weeks_available} weeks "
                        f"(slider set to {data_points_count}, no filtering applied)"
                    )

                if date_col != "date":
                    df_temp["date"] = df_temp[date_col]

                if isinstance(statistics_data, list):
                    statistics_data = df_temp.to_dict("records")
                else:
                    statistics_data = df_temp

    df = pd.DataFrame(statistics_data)

    if "stat_date" in df.columns and "date" not in df.columns:
        df["date"] = df["stat_date"]

    df["completed_items"] = pd.to_numeric(
        df["completed_items"], errors="coerce"
    ).fillna(0)
    df["completed_points"] = pd.to_numeric(
        df["completed_points"], errors="coerce"
    ).fillna(0)

    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values("date", ascending=True)

    df["week"] = df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
    df["year"] = df["date"].dt.year  # type: ignore[attr-defined]

    df["year_week"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    weekly_df = (
        df.groupby("year_week")
        .agg(
            items=("completed_items", "sum"),
            points=("completed_points", "sum"),
            start_date=("date", "min"),
        )
        .reset_index()
    )

    weekly_df = weekly_df.sort_values("start_date")

    if data_points_count is not None:
        recent_data = weekly_df
    else:
        recent_data = weekly_df.tail(10)

    import logging  # noqa: PLC0415

    logger = logging.getLogger(__name__)
    logger.debug(
        f"[APP VELOCITY] weeks in recent_data: {len(recent_data)}, "
        f"items per week: {recent_data['items'].tolist()}, "
        f"points per week: {recent_data['points'].tolist()}"
    )

    avg_weekly_items = recent_data["items"].mean()
    avg_weekly_points = recent_data["points"].mean()
    med_weekly_items = recent_data["items"].median()
    med_weekly_points = recent_data["points"].median()

    logger.debug(
        f"[APP VELOCITY] median items={med_weekly_items}, "
        f"median points={med_weekly_points}"
    )

    def round_up_2(x):
        return round(float(x), 2) if pd.notnull(x) else 0.0

    return (
        round_up_2(avg_weekly_items),
        round_up_2(avg_weekly_points),
        round_up_2(med_weekly_items),
        round_up_2(med_weekly_points),
    )
