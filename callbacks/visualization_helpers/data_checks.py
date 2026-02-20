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
