from datetime import datetime, timedelta  # noqa: F401 (re-exported via processing.py)

import pandas as pd

from utils.caching import (
    memoize,  # noqa: F401 (used by calculate_rates in rates module)
)


def calculate_total_points(
    total_items: float,
    estimated_items: float,
    estimated_points: float,
    statistics_data: list[dict] | None = None,
    use_fallback: bool = True,
) -> tuple[float, float]:

    if not use_fallback and estimated_items == 0 and estimated_points == 0:
        return 0.0, 0.0

    if estimated_items <= 0:
        if statistics_data and len(statistics_data) > 0:
            df = pd.DataFrame(statistics_data)
            df["completed_items"] = pd.to_numeric(
                df["completed_items"], errors="coerce"
            ).fillna(0)
            df["completed_points"] = pd.to_numeric(
                df["completed_points"], errors="coerce"
            ).fillna(0)

            total_completed_items = df["completed_items"].sum()
            total_completed_points = df["completed_points"].sum()

            if total_completed_items > 0:
                avg_points_per_item = total_completed_points / total_completed_items
                estimated_total_points = total_items * avg_points_per_item
                return estimated_total_points, avg_points_per_item

        if use_fallback:
            return total_items * 10, 10
        else:
            return 0.0, 0.0

    avg_points_per_item = estimated_points / estimated_items

    unestimated_items = max(0, total_items - estimated_items)
    estimated_total_points = estimated_points + (
        avg_points_per_item * unestimated_items
    )

    return estimated_total_points, avg_points_per_item


def read_and_clean_data(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    df.dropna(subset=["date"], inplace=True)
    df.sort_values("date", inplace=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")  # type: ignore[attr-defined]
    df["completed_items"] = pd.to_numeric(df["completed_items"], errors="coerce")
    df["completed_points"] = pd.to_numeric(df["completed_points"], errors="coerce")
    df.dropna(subset=["completed_items", "completed_points"], inplace=True)
    return df


def compute_cumulative_values(
    df: pd.DataFrame, total_items: float, total_points: float
) -> pd.DataFrame:

    df = df.copy()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], format="mixed")
        df = df.sort_values("date", ascending=True)

    df["completed_items"] = pd.to_numeric(
        df["completed_items"], errors="coerce"
    ).fillna(0)
    df["completed_points"] = pd.to_numeric(
        df["completed_points"], errors="coerce"
    ).fillna(0)

    df["cumulative_completed_items"] = df["completed_items"].cumsum()
    df["cumulative_completed_points"] = df["completed_points"].cumsum()

    df["cum_items"] = total_items + df["cumulative_completed_items"]
    df["cum_points"] = total_points + df["cumulative_completed_points"]

    return df


def calculate_velocity_from_dataframe(
    df: pd.DataFrame, column: str = "completed_items"
) -> float:

    if df.empty or len(df) == 0:
        return 0.0

    if "date" not in df.columns:
        raise KeyError("DataFrame must have 'date' column")
    if column not in df.columns:
        raise KeyError(f"DataFrame must have '{column}' column")

    df_with_week = df.copy()
    df_with_week["week_year"] = df_with_week["date"].dt.strftime("%Y-%U")  # type: ignore[attr-defined]
    unique_weeks = df_with_week["week_year"].nunique()

    if unique_weeks == 0:
        return 0.0

    total = df[column].sum()
    return total / unique_weeks


def compute_weekly_throughput(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df["week"] = df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
    df["year"] = df["date"].dt.year  # type: ignore[attr-defined]
    df["year_week"] = df["year"].astype(str) + "-" + df["week"].astype(str)

    grouped = (
        df.groupby("year_week")
        .agg({"completed_items": "sum", "completed_points": "sum"})
        .reset_index()
    )
    return grouped
