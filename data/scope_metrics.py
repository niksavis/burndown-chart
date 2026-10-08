from datetime import datetime, timedelta
from typing import Any

import pandas as pd


def calculate_scope_change_rate(
    df, baseline_items, baseline_points, data_points_count=None
):

    if data_points_count is not None:
        data_points_count = int(data_points_count)

    if (
        data_points_count is not None
        and data_points_count > 0
        and not df.empty
        and "date" in df.columns
    ):
        df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date", ascending=True)

        latest_date = df["date"].max()
        cutoff_date = latest_date - timedelta(weeks=data_points_count)
        df = df[df["date"] > cutoff_date]

    if df.empty:
        return {
            "items_rate": 0,
            "points_rate": 0,
            "throughput_ratio": {"items": 0, "points": 0},
        }

    total_created_items = df["created_items"].sum()
    total_created_points = df["created_points"].sum()
    total_completed_items = df["completed_items"].sum()
    total_completed_points = df["completed_points"].sum()

    items_throughput_ratio = (
        total_created_items / total_completed_items
        if total_completed_items > 0
        else float("inf")
        if total_created_items > 0
        else 0
    )

    points_throughput_ratio = (
        total_created_points / total_completed_points
        if total_completed_points > 0
        else float("inf")
        if total_created_points > 0
        else 0
    )

    if baseline_items == 0 or baseline_points == 0:
        return {
            "items_rate": 0,
            "points_rate": 0,
            "throughput_ratio": {
                "items": round(items_throughput_ratio, 2),
                "points": round(points_throughput_ratio, 2),
            },
        }

    items_rate = (
        (total_created_items / baseline_items) * 100 if baseline_items > 0 else 0
    )
    points_rate = (
        (total_created_points / baseline_points) * 100 if baseline_points > 0 else 0
    )

    return {
        "items_rate": round(items_rate, 1),
        "points_rate": round(points_rate, 1),
        "throughput_ratio": {
            "items": round(items_throughput_ratio, 2),
            "points": round(points_throughput_ratio, 2),
        },
    }


def calculate_scope_creep_rate(
    df, baseline_items, baseline_points, data_points_count=None
):
    return calculate_scope_change_rate(
        df, baseline_items, baseline_points, data_points_count
    )


def calculate_total_project_scope(
    df: pd.DataFrame, remaining_items: int, remaining_points: int
) -> dict[str, int]:

    if df.empty:
        return {"total_items": remaining_items, "total_points": remaining_points}

    total_completed_items = df["completed_items"].sum()
    total_completed_points = df["completed_points"].sum()

    total_items = remaining_items + total_completed_items
    total_points = remaining_points + total_completed_points

    return {"total_items": int(total_items), "total_points": int(total_points)}


def calculate_weekly_scope_growth(
    df: pd.DataFrame, data_points_count: int | None = None
) -> pd.DataFrame:

    if data_points_count is not None:
        data_points_count = int(data_points_count)

    if (
        data_points_count is not None
        and data_points_count > 0
        and not df.empty
        and "date" in df.columns
    ):
        df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date", ascending=True)

        latest_date = df["date"].max()
        cutoff_date = latest_date - timedelta(weeks=data_points_count)
        df = df[df["date"] > cutoff_date]

    if df.empty:
        return pd.DataFrame(columns=["week", "items_growth", "points_growth"])

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    df["week"] = df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
    df["year"] = df["date"].dt.isocalendar().year  # type: ignore[attr-defined]

    weekly = (
        df.groupby(["year", "week"])
        .agg(
            {
                "completed_items": "sum",
                "completed_points": "sum",
                "created_items": "sum",
                "created_points": "sum",
            }
        )
        .reset_index()
    )

    weekly["items_growth"] = weekly["created_items"] - weekly["completed_items"]
    weekly["points_growth"] = weekly["created_points"] - weekly["completed_points"]

    weekly["week_label"] = weekly.apply(
        lambda row: f"{row['year']}-W{row['week']:02d}", axis=1
    )

    weekly["start_date"] = weekly.apply(
        lambda row: get_week_start_date(row["year"], row["week"]), axis=1
    )

    weekly = weekly.sort_values("start_date")

    result = weekly[
        [
            "week_label",
            "items_growth",
            "points_growth",
            "start_date",
            "created_items",
            "completed_items",
            "created_points",
            "completed_points",
        ]
    ]

    return result


def get_week_start_date(year: int, week: int) -> datetime:
    first_day = datetime.strptime(f"{year}-{week}-1", "%G-%V-%u")
    return first_day


def calculate_scope_stability_index(
    df, baseline_items, baseline_points, data_points_count=None
):

    if data_points_count is not None:
        data_points_count = int(data_points_count)

    if (
        data_points_count is not None
        and data_points_count > 0
        and not df.empty
        and "date" in df.columns
    ):
        df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date", ascending=True)

        latest_date = df["date"].max()
        cutoff_date = latest_date - timedelta(weeks=data_points_count)
        df = df[df["date"] > cutoff_date]

    if df.empty or baseline_items == 0 or baseline_points == 0:
        return {"items_stability": 1.0, "points_stability": 1.0}

    total_created_items = df["created_items"].sum()
    total_created_points = df["created_points"].sum()

    total_items = baseline_items + total_created_items
    total_points = baseline_points + total_created_points

    items_stability = 1 - (total_created_items / total_items) if total_items > 0 else 1
    points_stability = (
        1 - (total_created_points / total_points) if total_points > 0 else 1
    )

    return {
        "items_stability": round(max(0, min(1, items_stability)), 2),
        "points_stability": round(max(0, min(1, points_stability)), 2),
    }


def check_scope_change_threshold(
    scope_change_rate: dict[str, Any], threshold: float
) -> dict[str, str]:

    items_exceeded = scope_change_rate["items_rate"] > threshold
    points_exceeded = scope_change_rate["points_rate"] > threshold

    items_throughput_concern = scope_change_rate["throughput_ratio"]["items"] > 1
    points_throughput_concern = scope_change_rate["throughput_ratio"]["points"] > 1

    status = "info"
    if (items_exceeded or points_exceeded) and (
        items_throughput_concern or points_throughput_concern
    ):
        status = "warning"

    message = ""

    if status == "warning":
        parts = []
        if items_exceeded:
            parts.append(f"Items scope growth ({scope_change_rate['items_rate']}%)")
        if points_exceeded:
            parts.append(f"Points scope growth ({scope_change_rate['points_rate']}%)")

        if parts:
            message = f"{' and '.join(parts)} exceed threshold ({threshold}%)."

            if items_throughput_concern and points_throughput_concern:
                message += (
                    " Scope is growing "
                    f"{scope_change_rate['throughput_ratio']['items']}x faster "
                    "than items completion and "
                    f"{scope_change_rate['throughput_ratio']['points']}x faster "
                    "than points completion."
                )
            elif items_throughput_concern:
                message += (
                    " Scope is growing "
                    f"{scope_change_rate['throughput_ratio']['items']}x faster "
                    "than items completion."
                )
            elif points_throughput_concern:
                message += (
                    " Scope is growing "
                    f"{scope_change_rate['throughput_ratio']['points']}x faster "
                    "than points completion."
                )

    return {"status": status, "message": message}


check_scope_creep_threshold = check_scope_change_threshold
