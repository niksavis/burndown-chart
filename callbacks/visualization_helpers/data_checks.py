"""
Data Validation Helpers

Helper functions for validating and checking data conditions in visualizations.
"""

from datetime import timedelta

import pandas as pd


def check_has_points_in_period(
    statistics: list | pd.DataFrame, data_points_count: int | None = None
) -> bool:
    """
    Check if there's any points data in the filtered time period.

    This respects the data_points_count slider to check only the selected time period,
    not the entire dataset. This ensures consistency with dashboard cards.

    Args:
        statistics: Statistics data (list or DataFrame)
        data_points_count: Number of weeks to check (None = all data)

    Returns:
        bool: True if there are any completed points > 0 in the period
    """
    if statistics is None or (isinstance(statistics, list) and len(statistics) == 0):
        return False

    df_check = (
        pd.DataFrame(statistics) if isinstance(statistics, list) else statistics.copy()
    )

    if df_check.empty or "completed_points" not in df_check.columns:
        return False

    # Apply same filtering logic as charts to respect data_points_count
    if data_points_count is not None and data_points_count > 0:
        if "date" in df_check.columns:
            df_check["date"] = pd.to_datetime(
                df_check["date"], format="mixed", errors="coerce"
            )
            df_check = df_check.dropna(subset=["date"]).sort_values(
                "date", ascending=True
            )

            if not df_check.empty:
                latest_date = df_check["date"].max()
                cutoff_date = latest_date - timedelta(weeks=data_points_count)
                df_check = df_check[df_check["date"] >= cutoff_date]

    # Check if any points in the filtered period
    return df_check["completed_points"].sum() > 0


def filter_df_by_week_labels(
    df: pd.DataFrame,
    data_points_count: int | None,
) -> pd.DataFrame:
    """
    Filter a statistics DataFrame to the most recent N weeks using ISO week labels.

    Falls back to date-range filtering when no ``week_label`` column is present.
    The input DataFrame must have a ``date`` column.

    Args:
        df: Statistics DataFrame to filter.
        data_points_count: Number of weeks to retain. None or 0 means no filtering.

    Returns:
        Filtered (and sorted ascending by date) DataFrame.
    """
    from datetime import datetime

    from data.time_period_calculator import format_year_week, get_iso_week

    if df.empty or not data_points_count or data_points_count <= 0:
        return df

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
        current_date = df["date"].max()
    else:
        current_date = datetime.now()

    weeks = []
    for _i in range(data_points_count):
        year, week = get_iso_week(current_date)
        weeks.append(format_year_week(year, week))
        current_date = current_date - timedelta(days=7)

    week_labels = set(reversed(weeks))

    if "week_label" in df.columns:
        df = df[df["week_label"].isin(week_labels)]
        return df.sort_values("date", ascending=True)

    # Fallback: date-range filtering
    df = df.dropna(subset=["date"]).sort_values("date", ascending=True)
    if df.empty:
        return df
    latest_date = df["date"].max()
    cutoff_date = latest_date - timedelta(weeks=data_points_count)
    return df[df["date"] >= cutoff_date]
