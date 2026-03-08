"""Statistics, trend, and baseline helpers for the Burndown application.

Computes performance trends, processes statistics DataFrames, and
establishes project baselines from historical data.
"""

from datetime import datetime, timedelta

import pandas as pd


def calculate_performance_trend(
    statistics_data: list[dict] | pd.DataFrame,
    metric: str = "completed_items",
    weeks_to_compare: int = 4,
    data_points_count: int | None = None,  # NEW PARAMETER
) -> dict:
    """
    Calculate performance trend indicators based on historical data.

    Args:
        statistics_data: List of dictionaries containing statistics data
        metric: The metric to calculate trend for
            ("completed_items" or "completed_points")
        weeks_to_compare: Number of weeks to use for trend calculation
        data_points_count: Optional parameter to limit data to most recent N data points

    Returns:
        Dictionary containing trend data:
        - trend_direction: "up", "down", or "stable"
        - percent_change: Percentage change between periods
        - current_avg: Average value for current period
        - previous_avg: Average value for previous period
        - is_significant: True if change is >20%
    """
    # Ensure data_points_count is an integer (could be float from UI slider)
    if data_points_count is not None:
        data_points_count = int(data_points_count)

    # CRITICAL FIX: Apply data points filtering by DATE RANGE, not row count
    # data_points_count represents WEEKS, not rows. With sparse data,
    # filtering by row count gives incorrect results.
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

    # Check if statistics_data is empty or None
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

    # Create DataFrame and ensure proper date format
    df = pd.DataFrame(statistics_data).copy()

    # Handle both "date" and "stat_date" column names
    if "stat_date" in df.columns and "date" not in df.columns:
        df["date"] = df["stat_date"]

    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df = df.dropna(subset=["date"])  # Remove rows with invalid dates

    # Ensure chronological order
    df = df.sort_values("date", ascending=True)

    # Convert metric values to numeric
    df[metric] = pd.to_numeric(df[metric], errors="coerce").fillna(0)

    # Group by week for consistent weekly aggregation
    df["week"] = df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
    df["year"] = df["date"].dt.year  # type: ignore[attr-defined]
    # Use vectorized string formatting to avoid DataFrame return issues
    df["year_week"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(
            metric_sum=(metric, "sum"),
            start_date=("date", "min"),
        )
        .reset_index()
    )

    # Sort by date again to ensure chronological order
    weekly_df = weekly_df.sort_values("start_date")

    # Make sure we have enough weeks for comparison
    if len(weekly_df) < weeks_to_compare * 2:
        return {
            "trend_direction": "stable",
            "percent_change": 0,
            "current_avg": 0,
            "previous_avg": 0,
            "is_significant": False,
            "weeks_compared": len(weekly_df) // 2 if len(weekly_df) > 1 else 1,
        }

    # Get the latest data points for comparison
    recent_data = weekly_df.tail(weeks_to_compare * 2)

    # Split into current and previous periods
    current_period = recent_data.tail(weeks_to_compare)
    previous_period = recent_data.head(weeks_to_compare)

    # Calculate averages for each period
    current_avg = current_period["metric_sum"].mean()
    previous_avg = previous_period["metric_sum"].mean()

    # Calculate percentage change
    if previous_avg > 0:
        percent_change = ((current_avg - previous_avg) / previous_avg) * 100
    else:
        # If previous average is 0, use current average as the change
        percent_change = current_avg * 100 if current_avg > 0 else 0

    # Determine trend direction
    if abs(percent_change) < 5:
        trend_direction = "stable"
    elif percent_change > 0:
        trend_direction = "up"
    else:
        trend_direction = "down"  # Check if change is significant (>20%)
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
    """Process statistics data for visualization and analysis.

    Args:
        data: Statistics data as list of dictionaries or DataFrame
        settings: Dictionary with project settings including baseline

    Returns:
        DataFrame with processed statistics data including cumulative values
    """
    # Convert data to DataFrame if not already
    if isinstance(data, list):
        if not data:  # Empty list
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

    # Ensure all required columns exist
    for col in ["date", "completed_items", "completed_points"]:
        if col not in df.columns:
            df[col] = 0 if col != "date" else ""

    # Add scope tracking columns if they don't exist
    for col in ["created_items", "created_points"]:
        if col not in df.columns:
            df[col] = 0

    # Convert date to datetime
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    # Sort by date
    df = df.sort_values("date")

    # Fill missing values with 0
    numeric_cols = [
        "completed_items",
        "completed_points",
        "created_items",
        "created_points",
    ]
    df[numeric_cols] = df[numeric_cols].fillna(0).astype(int)

    # Add cumulative columns for both completed and created items/points
    df["cum_completed_items"] = df["completed_items"].cumsum()
    df["cum_completed_points"] = df["completed_points"].cumsum()
    df["cum_created_items"] = df["created_items"].cumsum()
    df["cum_created_points"] = df["created_points"].cumsum()

    # Calculate total scope (baseline + created)
    baseline_items = settings.get("baseline", {}).get("items", 0) or 0
    baseline_points = settings.get("baseline", {}).get("points", 0) or 0

    df["total_scope_items"] = baseline_items + df["cum_created_items"]
    df["total_scope_points"] = baseline_points + df["cum_created_points"]

    return df


def establish_baseline(statistics_data: dict | None) -> dict:
    """Establish a baseline from initial scope.

    Args:
        statistics_data: Dictionary containing statistics data and baseline info

    Returns:
        Dictionary with baseline items, points, and date
    """
    if not statistics_data or not statistics_data.get("data"):
        return {"items": 0, "points": 0, "date": datetime.now().strftime("%Y-%m-%d")}

    # Get the earliest date in the dataset
    df = pd.DataFrame(statistics_data["data"])
    if "date" not in df.columns or df.empty:
        return {"items": 0, "points": 0, "date": datetime.now().strftime("%Y-%m-%d")}

    earliest_date = pd.to_datetime(df["date"], format="mixed", errors="coerce").min()

    # Return baseline info
    return {
        "items": statistics_data.get("baseline", {}).get("items", 0),
        "points": statistics_data.get("baseline", {}).get("points", 0),
        "date": earliest_date.strftime("%Y-%m-%d"),
    }


#######################################################################
# DASHBOARD CALCULATIONS (User Story 2)
#######################################################################
