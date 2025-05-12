"""
Data Processing Module

This module handles all data transformation, calculation logic, and
forecasting algorithms for the burndown chart application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from datetime import datetime, timedelta

# Third-party library imports
import pandas as pd

# Application imports
from caching import memoize

#######################################################################
# DATA PROCESSING FUNCTIONS
#######################################################################


def calculate_total_points(
    total_items: float,
    estimated_items: float,
    estimated_points: float,
    statistics_data: list[dict] | None = None,
) -> tuple[float, float]:
    """
    Calculate the total points based on estimated points and items.

    Args:
        total_items: Total number of items in the project
        estimated_items: Number of items that have been estimated
        estimated_points: Number of points for the estimated items
        statistics_data: Optional historical data to use as fallback

    Returns:
        Tuple of (estimated_total_points, avg_points_per_item)
    """
    # Basic validation to prevent division by zero
    if estimated_items <= 0:
        # If no items are estimated, try to use historical data
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

        # Default to 10 points per item if no data available
        return total_items * 10, 10

    # Calculate average points per item based on estimates
    avg_points_per_item = estimated_points / estimated_items

    # Calculate total points using the average
    estimated_total_points = total_items * avg_points_per_item

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
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.dropna(subset=["date"], inplace=True)
    df.sort_values("date", inplace=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
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
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=True)

    # Convert to numeric in case there are any string values
    df["completed_items"] = pd.to_numeric(
        df["completed_items"], errors="coerce"
    ).fillna(0)
    df["completed_points"] = pd.to_numeric(
        df["completed_points"], errors="coerce"
    ).fillna(0)

    # Calculate cumulative sums from the end to the beginning
    # This gives us the remaining items/points at each data point
    # We reverse the dataframe, calculate cumulative sum, then reverse back
    reversed_items = df["completed_items"][::-1].cumsum()[::-1]
    reversed_points = df["completed_points"][::-1].cumsum()[::-1]

    # Calculate remaining items and points by adding the total to the reverse cumsum
    df["cum_items"] = reversed_items + total_items
    df["cum_points"] = reversed_points + total_points

    return df


def compute_weekly_throughput(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily data to weekly throughput for more stable calculations.

    Args:
        df: DataFrame with daily completion data

    Returns:
        DataFrame with weekly aggregated data
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = df.apply(lambda r: f"{r['year']}-{r['week']}", axis=1)

    grouped = (
        df.groupby("year_week")
        .agg({"completed_items": "sum", "completed_points": "sum"})
        .reset_index()
    )
    return grouped


@memoize(max_age_seconds=300)
def calculate_rates(
    grouped: pd.DataFrame, total_items: float, total_points: float, pert_factor: int
) -> tuple[float, float, float, float, float, float]:
    """
    Calculate burn rates using PERT methodology.

    Args:
        grouped: DataFrame with weekly aggregated data
        total_items: Total number of items to complete
        total_points: Total number of points to complete
        pert_factor: Number of data points to use for optimistic/pessimistic estimates

    Returns:
        Tuple of calculated values:
        (pert_time_items, optimistic_items_rate, pessimistic_items_rate,
         pert_time_points, optimistic_points_rate, pessimistic_points_rate)
    """
    days_per_week = 7.0

    # If no data or empty dataframe, return safe default values
    if grouped is None or len(grouped) == 0:
        # Return zeros to avoid calculations with empty data
        return 0, 0, 0, 0, 0, 0

    # Validate and adjust pert_factor based on available data
    valid_data_count = len(grouped)

    # When data is limited, adjust strategy to ensure stable results
    if valid_data_count <= 3:
        # With very few data points, just use the mean for all estimates
        # This prevents crashes when pert_factor is 3 but we only have 1-3 data points
        most_likely_items_rate = grouped["completed_items"].mean() / days_per_week
        most_likely_points_rate = grouped["completed_points"].mean() / days_per_week

        # Use the same value for optimistic and pessimistic to avoid erratic forecasts
        # with tiny datasets
        optimistic_items_rate = most_likely_items_rate
        pessimistic_items_rate = most_likely_items_rate
        optimistic_points_rate = most_likely_points_rate
        pessimistic_points_rate = most_likely_points_rate
    else:
        # Normal case with sufficient data
        # Adjust PERT factor to be at most 1/3 of available data for stable results
        valid_pert_factor = min(pert_factor, max(1, valid_data_count // 3))
        valid_pert_factor = max(valid_pert_factor, 1)  # Ensure at least 1

        # Calculate daily rates for items
        optimistic_items_rate = (
            grouped["completed_items"].nlargest(valid_pert_factor).mean()
            / days_per_week
        )
        pessimistic_items_rate = (
            grouped["completed_items"].nsmallest(valid_pert_factor).mean()
            / days_per_week
        )
        most_likely_items_rate = grouped["completed_items"].mean() / days_per_week

        # Calculate daily rates for points
        optimistic_points_rate = (
            grouped["completed_points"].nlargest(valid_pert_factor).mean()
            / days_per_week
        )
        pessimistic_points_rate = (
            grouped["completed_points"].nsmallest(valid_pert_factor).mean()
            / days_per_week
        )
        most_likely_points_rate = grouped["completed_points"].mean() / days_per_week

    # Prevent any zero or negative rates that would cause division by zero errors
    # or negative time forecasts
    optimistic_items_rate = max(0.001, optimistic_items_rate)
    pessimistic_items_rate = max(0.001, pessimistic_items_rate)
    most_likely_items_rate = max(0.001, most_likely_items_rate)
    optimistic_points_rate = max(0.001, optimistic_points_rate)
    pessimistic_points_rate = max(0.001, pessimistic_points_rate)
    most_likely_points_rate = max(0.001, most_likely_points_rate)

    # Calculate time estimates for items
    optimistic_time_items = (
        total_items / optimistic_items_rate if optimistic_items_rate else float("inf")
    )
    most_likely_time_items = (
        total_items / most_likely_items_rate if most_likely_items_rate else float("inf")
    )
    pessimistic_time_items = (
        total_items / pessimistic_items_rate if pessimistic_items_rate else float("inf")
    )

    # Calculate time estimates for points
    optimistic_time_points = (
        total_points / optimistic_points_rate
        if optimistic_points_rate
        else float("inf")
    )
    most_likely_time_points = (
        total_points / most_likely_points_rate
        if most_likely_points_rate
        else float("inf")
    )
    pessimistic_time_points = (
        total_points / pessimistic_points_rate
        if pessimistic_points_rate
        else float("inf")
    )

    # Apply PERT formula: (O + 4M + P) / 6
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


def daily_forecast(
    start_val: float, daily_rate: float, start_date: datetime
) -> tuple[list[datetime], list[float]]:
    """
    Generate daily forecast values from start to completion.

    Args:
        start_val: Starting value (remaining items/points)
        daily_rate: Daily completion rate
        start_date: Starting date for the forecast

    Returns:
        Tuple of (x_values, y_values) for plotting
    """
    # If rate is too small, we'll hit timestamp limits; enforce a minimum
    if daily_rate < 0.001:
        daily_rate = 0.001

    # If rate is still effectively zero, return just the start point
    if daily_rate <= 0:
        return [start_date], [start_val]

    x_vals, y_vals = [], []
    val = start_val
    current_date = start_date

    # Calculate expected end date
    days_needed = val / daily_rate if daily_rate > 0 else 0

    # Cap forecast at 10 years (3650 days) to prevent timestamp overflow
    MAX_FORECAST_DAYS = 3650
    if days_needed > MAX_FORECAST_DAYS:
        # Create a capped forecast
        num_points = min(
            100, MAX_FORECAST_DAYS
        )  # Use at most 100 points for the forecast
        day_step = MAX_FORECAST_DAYS / num_points

        for i in range(num_points):
            days_elapsed = i * day_step
            if days_elapsed > MAX_FORECAST_DAYS:
                break

            forecast_date = start_date + timedelta(days=days_elapsed)
            forecast_val = max(0, val - (daily_rate * days_elapsed))

            x_vals.append(forecast_date)
            y_vals.append(forecast_val)

        # Add final point at the maximum forecast date
        final_date = start_date + timedelta(days=MAX_FORECAST_DAYS)
        final_val = max(0, val - (daily_rate * MAX_FORECAST_DAYS))
        x_vals.append(final_date)
        y_vals.append(final_val)

        return x_vals, y_vals

    # Normal case - forecast until completion
    while val > 0:
        x_vals.append(current_date)
        y_vals.append(val)
        val -= daily_rate
        current_date += timedelta(days=1)

        # Safety check to prevent infinite loops
        if len(x_vals) > MAX_FORECAST_DAYS:
            break

    # Add final zero point
    x_vals.append(current_date)
    y_vals.append(0)

    return x_vals, y_vals


def daily_forecast_burnup(current, daily_rate, start_date, target_scope):
    """
    Generate a daily burnup forecast from current completed work to target scope.

    Args:
        current: Current completed value (starting point)
        daily_rate: Daily completion rate
        start_date: Starting date for forecast
        target_scope: Target scope value to reach (upper limit)

    Returns:
        Tuple of (dates, values) for the forecast
    """
    if daily_rate <= 0 or current >= target_scope:
        # If rate is zero or we've already reached target, return empty forecast
        return ([], [])

    # Calculate days needed to reach target scope
    remaining = target_scope - current
    days_needed = int(remaining / daily_rate) + 1  # Add 1 to ensure we reach target

    # Generate dates
    dates = [start_date + timedelta(days=i) for i in range(days_needed + 1)]

    # Generate values
    values = []
    for i in range(len(dates)):
        # Calculate forecasted value, but cap at target scope
        value = min(current + (daily_rate * i), target_scope)
        values.append(value)

    # Ensure the last value is exactly the target scope
    if values and values[-1] < target_scope:
        values[-1] = target_scope

    return (dates, values)


def calculate_weekly_averages(
    statistics_data: list[dict] | pd.DataFrame,
) -> tuple[float, float, float, float]:
    """
    Calculate average and median weekly items and points for the last 10 weeks.

    Args:
        statistics_data: List of dictionaries containing statistics data

    Returns:
        Tuple of (avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points)
    """
    # Check if statistics_data is empty or None
    if (
        statistics_data is None
        or (isinstance(statistics_data, pd.DataFrame) and statistics_data.empty)
        or (not isinstance(statistics_data, pd.DataFrame) and len(statistics_data) == 0)
    ):
        return 0, 0, 0, 0

    # Create DataFrame and ensure numeric types
    df = pd.DataFrame(statistics_data)
    df["completed_items"] = pd.to_numeric(
        df["completed_items"], errors="coerce"
    ).fillna(0)
    df["completed_points"] = pd.to_numeric(
        df["completed_points"], errors="coerce"
    ).fillna(0)

    # Convert date to datetime and ensure it's sorted chronologically
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])  # Remove rows with invalid dates
    df = df.sort_values("date", ascending=True)

    # Group by week to ensure consistent weekly aggregation
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(
            items=("completed_items", "sum"),
            points=("completed_points", "sum"),
            start_date=("date", "min"),
        )
        .reset_index()
    )

    # Sort by date again to ensure chronological order after grouping
    weekly_df = weekly_df.sort_values("start_date")

    # Get the last 10 weeks or all if less than 10
    recent_data = weekly_df.tail(10)

    # Calculate averages and medians
    avg_weekly_items = recent_data["items"].mean()
    avg_weekly_points = recent_data["points"].mean()
    med_weekly_items = recent_data["items"].median()
    med_weekly_points = recent_data["points"].median()

    return (
        round(avg_weekly_items, 1),
        round(avg_weekly_points, 1),
        round(med_weekly_items, 1),
        round(med_weekly_points, 1),
    )


@memoize(max_age_seconds=300)
def generate_weekly_forecast(
    statistics_data: list[dict] | pd.DataFrame,
    pert_factor: int = 3,
    forecast_weeks: int = 1,
) -> dict:
    """
    Generate a weekly forecast for items and points per week using PERT methodology.

    Args:
        statistics_data: List of dictionaries containing statistics data
        pert_factor: Number of data points to use for optimistic/pessimistic scenarios
        forecast_weeks: Number of weeks to forecast (default: 1)

    Returns:
        Dictionary containing forecast data for items and points
    """
    # Create DataFrame from statistics data
    df = pd.DataFrame(statistics_data).copy()
    if df.empty:
        # Return empty forecast data if no historical data
        return {
            "items": {
                "dates": [],
                "most_likely": [],
                "optimistic": [],
                "pessimistic": [],
            },
            "points": {
                "dates": [],
                "most_likely": [],
                "optimistic": [],
                "pessimistic": [],
            },
        }

    # Convert date to datetime and ensure proper format
    df["date"] = pd.to_datetime(df["date"])

    # Ensure data is sorted chronologically
    df = df.sort_values("date", ascending=True)

    # Add week and year columns for grouping
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(
            items=("completed_items", "sum"),
            points=("completed_points", "sum"),
            start_date=("date", "min"),
        )
        .reset_index()
    )

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Calculate PERT estimates for weekly items
    if len(weekly_df) > 0:
        valid_data_count = len(weekly_df)

        # Special handling for very small datasets
        if valid_data_count <= 3:
            # With very few data points, just use the mean for all estimates
            # This prevents crashes when pert_factor is 3 but we only have 1-3 data points
            most_likely_items = weekly_df["items"].mean()
            most_likely_points = weekly_df["points"].mean()

            # Use the same values for optimistic and pessimistic to avoid erratic forecasts
            # with tiny datasets
            optimistic_items = most_likely_items * 1.2  # Slightly optimistic
            pessimistic_items = max(
                0.1, most_likely_items * 0.8
            )  # Slightly pessimistic but positive

            optimistic_points = most_likely_points * 1.2  # Slightly optimistic
            pessimistic_points = max(
                0.1, most_likely_points * 0.8
            )  # Slightly pessimistic but positive
        else:
            # Adjust PERT factor to be at most 1/3 of available data for stable results
            valid_pert_factor = min(pert_factor, max(1, valid_data_count // 3))
            valid_pert_factor = max(valid_pert_factor, 1)  # Ensure at least 1

            # Most likely: average of all data
            most_likely_items = weekly_df["items"].mean()

            # Optimistic: average of best performing weeks
            optimistic_items = weekly_df["items"].nlargest(valid_pert_factor).mean()

            # Pessimistic: average of worst performing weeks (excluding zeros)
            non_zero_items = weekly_df[weekly_df["items"] > 0]["items"]
            if len(non_zero_items) >= valid_pert_factor:
                pessimistic_items = non_zero_items.nsmallest(valid_pert_factor).mean()
            else:
                # If we don't have enough non-zero values, use min value or a percentage of most_likely
                pessimistic_items = (
                    non_zero_items.min()
                    if len(non_zero_items) > 0
                    else max(0.1, most_likely_items * 0.5)
                )

            # Same calculations for points
            most_likely_points = weekly_df["points"].mean()
            optimistic_points = weekly_df["points"].nlargest(valid_pert_factor).mean()

            non_zero_points = weekly_df[weekly_df["points"] > 0]["points"]
            if len(non_zero_points) >= valid_pert_factor:
                pessimistic_points = non_zero_points.nsmallest(valid_pert_factor).mean()
            else:
                # If we don't have enough non-zero values, use min value or a percentage of most_likely
                pessimistic_points = (
                    non_zero_points.min()
                    if len(non_zero_points) > 0
                    else max(0.1, most_likely_points * 0.5)
                )

        # Get the last date from historical data as starting point
        last_date = weekly_df["start_date"].max()

        # Generate the next week forecast date (ensuring proper progression)
        next_date = last_date + timedelta(weeks=1)

        # Format date for display - clear indication this is the next week
        formatted_date = next_date.strftime("%b %d")

        # Create forecast values for items (single week)
        most_likely_items_forecast = [most_likely_items]
        optimistic_items_forecast = [optimistic_items]
        pessimistic_items_forecast = [pessimistic_items]

        # Create forecast values for points (single week)
        most_likely_points_forecast = [most_likely_points]
        optimistic_points_forecast = [optimistic_points]
        pessimistic_points_forecast = [pessimistic_points]

        return {
            "items": {
                "dates": [formatted_date],
                "most_likely": most_likely_items_forecast,
                "optimistic": optimistic_items_forecast,
                "pessimistic": pessimistic_items_forecast,
                "most_likely_value": most_likely_items,
                "optimistic_value": optimistic_items,
                "pessimistic_value": pessimistic_items,
                "next_date": next_date,  # Include the actual date object for proper date progression
            },
            "points": {
                "dates": [formatted_date],
                "most_likely": most_likely_points_forecast,
                "optimistic": optimistic_points_forecast,  # Fixed: use optimistic_points_forecast instead of most_likely_points_forecast
                "pessimistic": pessimistic_points_forecast,
                "most_likely_value": most_likely_points,
                "optimistic_value": optimistic_points,
                "pessimistic_value": pessimistic_points,
                "next_date": next_date,  # Include the actual date object for proper date progression
            },
        }
    else:
        return {
            "items": {
                "dates": [],
                "most_likely": [],
                "optimistic": [],
                "pessimistic": [],
            },
            "points": {
                "dates": [],
                "most_likely": [],
                "optimistic": [],
                "pessimistic": [],
            },
        }


def calculate_performance_trend(
    statistics_data: list[dict] | pd.DataFrame,
    metric: str = "completed_items",
    weeks_to_compare: int = 4,
) -> dict:
    """
    Calculate performance trend indicators based on historical data.

    Args:
        statistics_data: List of dictionaries containing statistics data
        metric: The metric to calculate trend for ("completed_items" or "completed_points")
        weeks_to_compare: Number of weeks to use for trend calculation

    Returns:
        Dictionary containing trend data:
        - trend_direction: "up", "down", or "stable"
        - percent_change: Percentage change between periods
        - current_avg: Average value for current period
        - previous_avg: Average value for previous period
        - is_significant: True if change is >20%
    """
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
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["date"])  # Remove rows with invalid dates

    # Ensure chronological order
    df = df.sort_values("date", ascending=True)

    # Convert metric values to numeric
    df[metric] = pd.to_numeric(df[metric], errors="coerce").fillna(0)

    # Group by week for consistent weekly aggregation
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

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
        trend_direction = "down"

    # Check if change is significant (>20%)
    is_significant = abs(percent_change) >= 20

    return {
        "trend_direction": trend_direction,
        "percent_change": round(percent_change, 1),
        "current_avg": round(current_avg, 1),
        "previous_avg": round(previous_avg, 1),
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
    df["date"] = pd.to_datetime(df["date"])

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

    earliest_date = pd.to_datetime(df["date"]).min()

    # Return baseline info
    return {
        "items": statistics_data.get("baseline", {}).get("items", 0),
        "points": statistics_data.get("baseline", {}).get("points", 0),
        "date": earliest_date.strftime("%Y-%m-%d"),
    }
