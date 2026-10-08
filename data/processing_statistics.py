from datetime import datetime, timedelta

import pandas as pd


def calculate_performance_trend(
    statistics_data: list[dict] | pd.DataFrame,
    metric: str = "completed_items",
    weeks_to_compare: int = 4,
    data_points_count: int | None = None,
) -> dict:

    if data_points_count is not None:
        data_points_count = int(data_points_count)

    if data_points_count is not None and data_points_count > 0:
        if isinstance(statistics_data, list):
            df_temp = pd.DataFrame(statistics_data)
            if not df_temp.empty and "date" in df_temp.columns:
                df_temp["date"] = pd.to_datetime(
                    df_temp["date"], format="mixed", errors="coerce"
                )
                df_temp = df_temp.dropna(subset=["date"])
                df_temp = df_temp.sort_values("date", ascending=True)

                latest_date = df_temp["date"].max()
                cutoff_date = latest_date - timedelta(weeks=data_points_count)
                df_temp = df_temp[df_temp["date"] > cutoff_date]

                statistics_data = df_temp.to_dict("records")
        elif isinstance(statistics_data, pd.DataFrame):
            df_temp = statistics_data.copy()
            if not df_temp.empty and "date" in df_temp.columns:
                df_temp["date"] = pd.to_datetime(
                    df_temp["date"], format="mixed", errors="coerce"
                )
                df_temp = df_temp.dropna(subset=["date"])
                df_temp = df_temp.sort_values("date", ascending=True)

                latest_date = df_temp["date"].max()
                cutoff_date = latest_date - timedelta(weeks=data_points_count)
                statistics_data = df_temp[df_temp["date"] > cutoff_date]

    if (
        statistics_data is None
        or (isinstance(statistics_data, pd.DataFrame) and statistics_data.empty)
        or (
            not isinstance(statistics_data, pd.DataFrame)
            and len(statistics_data) < weeks_to_compare * 2
        )
    ):
        return {
            "trend_direction": "stable",
            "percent_change": 0,
            "current_avg": 0,
            "previous_avg": 0,
            "is_significant": False,
            "weeks_compared": weeks_to_compare,
        }

    df = pd.DataFrame(statistics_data).copy()

    if "stat_date" in df.columns and "date" not in df.columns:
        df["date"] = df["stat_date"]

    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df = df.dropna(subset=["date"])

    df = df.sort_values("date", ascending=True)

    df[metric] = pd.to_numeric(df[metric], errors="coerce").fillna(0)

    df["week"] = df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
    df["year"] = df["date"].dt.year  # type: ignore[attr-defined]
    df["year_week"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    weekly_df = (
        df.groupby("year_week")
        .agg(
            metric_sum=(metric, "sum"),
            start_date=("date", "min"),
        )
        .reset_index()
    )

    weekly_df = weekly_df.sort_values("start_date")

    if len(weekly_df) < weeks_to_compare * 2:
        return {
            "trend_direction": "stable",
            "percent_change": 0,
            "current_avg": 0,
            "previous_avg": 0,
            "is_significant": False,
            "weeks_compared": len(weekly_df) // 2 if len(weekly_df) > 1 else 1,
        }

    recent_data = weekly_df.tail(weeks_to_compare * 2)

    current_period = recent_data.tail(weeks_to_compare)
    previous_period = recent_data.head(weeks_to_compare)

    current_avg = current_period["metric_sum"].mean()
    previous_avg = previous_period["metric_sum"].mean()

    if previous_avg > 0:
        percent_change = ((current_avg - previous_avg) / previous_avg) * 100
    else:
        percent_change = current_avg * 100 if current_avg > 0 else 0

    if abs(percent_change) < 5:
        trend_direction = "stable"
    elif percent_change > 0:
        trend_direction = "up"
    else:
        trend_direction = "down"
    is_significant = abs(percent_change) >= 20

    return {
        "trend_direction": trend_direction,
        "percent_change": round(percent_change, 1),
        "current_avg": round(current_avg, 2),
        "previous_avg": round(previous_avg, 2),
        "is_significant": is_significant,
        "weeks_compared": weeks_to_compare,
    }


def process_statistics_data(
    data: list[dict] | pd.DataFrame, settings: dict
) -> pd.DataFrame:

    if isinstance(data, list):
        if not data:
            return pd.DataFrame(
                columns=[
                    "date",
                    "completed_items",
                    "completed_points",
                    "created_items",
                    "created_points",
                ]
            )
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    for col in ["date", "completed_items", "completed_points"]:
        if col not in df.columns:
            df[col] = 0 if col != "date" else ""

    for col in ["created_items", "created_points"]:
        if col not in df.columns:
            df[col] = 0

    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    df = df.sort_values("date")

    numeric_cols = [
        "completed_items",
        "completed_points",
        "created_items",
        "created_points",
    ]
    df[numeric_cols] = df[numeric_cols].fillna(0).astype(int)

    df["cum_completed_items"] = df["completed_items"].cumsum()
    df["cum_completed_points"] = df["completed_points"].cumsum()
    df["cum_created_items"] = df["created_items"].cumsum()
    df["cum_created_points"] = df["created_points"].cumsum()

    baseline_items = settings.get("baseline", {}).get("items", 0) or 0
    baseline_points = settings.get("baseline", {}).get("points", 0) or 0

    df["total_scope_items"] = baseline_items + df["cum_created_items"]
    df["total_scope_points"] = baseline_points + df["cum_created_points"]

    return df


def establish_baseline(statistics_data: dict | None) -> dict:

    if not statistics_data or not statistics_data.get("data"):
        return {"items": 0, "points": 0, "date": datetime.now().strftime("%Y-%m-%d")}

    df = pd.DataFrame(statistics_data["data"])
    if "date" not in df.columns or df.empty:
        return {"items": 0, "points": 0, "date": datetime.now().strftime("%Y-%m-%d")}

    earliest_date = pd.to_datetime(df["date"], format="mixed", errors="coerce").min()

    return {
        "items": statistics_data.get("baseline", {}).get("items", 0),
        "points": statistics_data.get("baseline", {}).get("points", 0),
        "date": earliest_date.strftime("%Y-%m-%d"),
    }
