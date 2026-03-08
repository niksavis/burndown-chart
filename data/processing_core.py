"""Core data-processing helpers for the Burndown application.

Handles basic data transformations, velocity calculation, and
weekly throughput aggregation.
"""

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
    """
    Calculate the total points based on estimated points and items.

    Args:
        total_items: Total number of items in the project
        estimated_items: Number of items that have been estimated
        estimated_points: Number of points for the estimated items
        statistics_data: Optional historical data to use as fallback
        use_fallback: Whether to use fallback calculation when no estimates provided

    Returns:
        Tuple of (estimated_total_points, avg_points_per_item)
    """
    # Fix for edge case: When user explicitly sets estimated items/points to 0
    # and fallback is disabled, respect their intent and return 0
    if not use_fallback and estimated_items == 0 and estimated_points == 0:
        # User explicitly indicated no estimates available and no fallback wanted
        return 0.0, 0.0

    # Basic validation to prevent division by zero
    if estimated_items <= 0:
        # Use fallback behavior (historical data or defaults)
        if statistics_data and len(statistics_data) > 0:
            # Calculate average points per item from historical data
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

        # Default to 10 points per item if no data available and fallback enabled
        if use_fallback:
            return total_items * 10, 10
        else:
            # No fallback - return zeros when no estimates provided
            return 0.0, 0.0

    # Calculate average points per item based on estimates
    avg_points_per_item = estimated_points / estimated_items

    # Calculate total points using JIRA scope calculator formula:
    # remaining_total_points = estimated_points + (avg × unestimated_items)
    unestimated_items = max(0, total_items - estimated_items)
    estimated_total_points = estimated_points + (
        avg_points_per_item * unestimated_items
    )

    return estimated_total_points, avg_points_per_item


def read_and_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare the input dataframe for analysis.

    Args:
        df: Pandas DataFrame with raw data

    Returns:
        Cleaned DataFrame with proper types and no missing values
    """
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
    """
    Compute cumulative values for items and points for burndown tracking.

    Args:
        df: DataFrame with historical data
        total_items: Total number of items to complete
        total_points: Total number of points to complete

    Returns:
        DataFrame with added cumulative columns
    """
    df = df.copy()

    # Make sure data is sorted by date in ascending order
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], format="mixed")
        df = df.sort_values("date", ascending=True)

    # Convert to numeric in case there are any string values
    df["completed_items"] = pd.to_numeric(
        df["completed_items"], errors="coerce"
    ).fillna(0)
    df["completed_points"] = pd.to_numeric(
        df["completed_points"], errors="coerce"
    ).fillna(0)

    # Calculate cumulative completed from beginning to each point
    df["cumulative_completed_items"] = df["completed_items"].cumsum()
    df["cumulative_completed_points"] = df["completed_points"].cumsum()

    # Calculate remaining at each point = Current remaining +
    # work completed in time window
    # This gives us the burndown: starting scope minus progress
    df["cum_items"] = total_items + df["cumulative_completed_items"]
    df["cum_points"] = total_points + df["cumulative_completed_points"]

    return df


def calculate_velocity_from_dataframe(
    df: pd.DataFrame, column: str = "completed_items"
) -> float:
    """Calculate velocity as items per week using actual number of weeks with data.

    This method counts the actual number of distinct weeks present in the data,
    rather than calculating the date range span. This produces accurate velocity
    when data is sparse or has gaps.

    **Why This Matters:**
        - Date range method: 2 weeks of data across 10-week span = items/10
            (WRONG - deflates velocity)
    - Actual weeks method: 2 weeks of data = items/2 (CORRECT - accurate velocity)

    **Example:**
    ```
    Week 1: 10 items
    Week 10: 10 items
    Total: 20 items

    Date range method: 20 items / 9 weeks = 2.2 items/week [X]
    Actual weeks method: 20 items / 2 weeks = 10 items/week [OK]
    ```

    Args:
        df: DataFrame with 'date' column (datetime type) and data column
        column: Name of column to calculate velocity for (default: "completed_items")

    Returns:
        Velocity as items per week (rounded to 1 decimal place)

    Raises:
        KeyError: If df doesn't have 'date' or specified column

    Examples:
        >>> df = pd.DataFrame({
        ...     "date": pd.to_datetime(["2025-01-01", "2025-01-08", "2025-03-15"]),
        ...     "completed_items": [10, 15, 12]
        ... })
        >>> calculate_velocity_from_dataframe(df)
        12.3  # 37 items / 3 weeks
    """
    if df.empty or len(df) == 0:
        return 0.0

    # Validate required columns
    if "date" not in df.columns:
        raise KeyError("DataFrame must have 'date' column")
    if column not in df.columns:
        raise KeyError(f"DataFrame must have '{column}' column")

    # Count actual number of distinct weeks with data
    df_with_week = df.copy()
    # Use ISO week format: YYYY-WW (Monday-based weeks)
    df_with_week["week_year"] = df_with_week["date"].dt.strftime("%Y-%U")  # type: ignore[attr-defined]
    unique_weeks = df_with_week["week_year"].nunique()

    if unique_weeks == 0:
        return 0.0

    total = df[column].sum()
    return total / unique_weeks


def compute_weekly_throughput(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily data to weekly throughput for more stable calculations.

    Args:
        df: DataFrame with daily completion data

    Returns:
        DataFrame with weekly aggregated data
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df["week"] = df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
    df["year"] = df["date"].dt.year  # type: ignore[attr-defined]
    # Use vectorized string formatting to avoid DataFrame return issues
    df["year_week"] = df["year"].astype(str) + "-" + df["week"].astype(str)

    grouped = (
        df.groupby("year_week")
        .agg({"completed_items": "sum", "completed_points": "sum"})
        .reset_index()
    )
    return grouped
