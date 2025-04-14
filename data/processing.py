"""
Data Processing Module

This module handles all data transformation, calculation logic, and
forecasting algorithms for the burndown chart application.
"""

#######################################################################
# IMPORTS
#######################################################################
import pandas as pd
from datetime import datetime, timedelta

#######################################################################
# DATA PROCESSING FUNCTIONS
#######################################################################


def calculate_total_points(
    total_items, estimated_items, estimated_points, statistics_data=None
):
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
            df["no_items"] = pd.to_numeric(df["no_items"], errors="coerce").fillna(0)
            df["no_points"] = pd.to_numeric(df["no_points"], errors="coerce").fillna(0)

            total_completed_items = df["no_items"].sum()
            total_completed_points = df["no_points"].sum()

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


def read_and_clean_data(df):
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
    df["no_items"] = pd.to_numeric(df["no_items"], errors="coerce")
    df["no_points"] = pd.to_numeric(df["no_points"], errors="coerce")
    df.dropna(subset=["no_items", "no_points"], inplace=True)
    return df


def compute_cumulative_values(df, total_items, total_points):
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
    df["cum_items"] = df["no_items"][::-1].cumsum()[::-1] + total_items
    df["cum_points"] = df["no_points"][::-1].cumsum()[::-1] + total_points
    return df


def compute_weekly_throughput(df):
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
        .agg({"no_items": "sum", "no_points": "sum"})
        .reset_index()
    )
    return grouped


def calculate_rates(grouped, total_items, total_points, pert_factor):
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

    # Validate and adjust pert_factor based on available data
    pert_factor = min(pert_factor, len(grouped) // 2) if len(grouped) > 0 else 1
    pert_factor = max(pert_factor, 1)  # Ensure at least 1

    if len(grouped) == 0:
        return 0, 0, 0, 0, 0, 0

    # Calculate daily rates for items
    optimistic_items_rate = (
        grouped["no_items"].nlargest(pert_factor).mean() / days_per_week
    )
    pessimistic_items_rate = (
        grouped["no_items"].nsmallest(pert_factor).mean() / days_per_week
    )
    most_likely_items_rate = grouped["no_items"].mean() / days_per_week

    # Calculate daily rates for points
    optimistic_points_rate = (
        grouped["no_points"].nlargest(pert_factor).mean() / days_per_week
    )
    pessimistic_points_rate = (
        grouped["no_points"].nsmallest(pert_factor).mean() / days_per_week
    )
    most_likely_points_rate = grouped["no_points"].mean() / days_per_week

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


def daily_forecast(start_val, daily_rate, start_date):
    """
    Generate daily forecast values from start to completion.

    Args:
        start_val: Starting value (remaining items/points)
        daily_rate: Daily completion rate
        start_date: Starting date for the forecast

    Returns:
        Tuple of (x_values, y_values) for plotting
    """
    if daily_rate <= 0:
        return [start_date], [start_val]

    x_vals, y_vals = [], []
    val = start_val
    current_date = start_date

    while val > 0:
        x_vals.append(current_date)
        y_vals.append(val)
        val -= daily_rate
        current_date += timedelta(days=1)

    # Add final zero point
    x_vals.append(current_date)
    y_vals.append(0)

    return x_vals, y_vals


def calculate_weekly_averages(statistics_data):
    """
    Calculate average and median weekly items and points for the last 10 weeks.

    Args:
        statistics_data: List of dictionaries containing statistics data

    Returns:
        Tuple of (avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points)
    """
    if not statistics_data or len(statistics_data) == 0:
        return 0, 0, 0, 0

    # Create DataFrame and ensure numeric types
    df = pd.DataFrame(statistics_data)
    df["no_items"] = pd.to_numeric(df["no_items"], errors="coerce").fillna(0)
    df["no_points"] = pd.to_numeric(df["no_points"], errors="coerce").fillna(0)

    # Sort by date to ensure we get the most recent 10 weeks
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")

    # Get the last 10 entries or all if less than 10
    recent_data = df.tail(10)

    # Calculate averages and medians
    avg_weekly_items = recent_data["no_items"].mean()
    avg_weekly_points = recent_data["no_points"].mean()
    med_weekly_items = recent_data["no_items"].median()
    med_weekly_points = recent_data["no_points"].median()

    return (
        round(avg_weekly_items, 1),
        round(avg_weekly_points, 1),
        round(med_weekly_items, 1),
        round(med_weekly_points, 1),
    )


def prepare_forecast_data(
    df, total_items, total_points, pert_factor, data_points_count=None
):
    """
    Prepare all necessary data for the forecast visualization.

    Args:
        df: DataFrame with historical data
        total_items: Total number of items to complete
        total_points: Total number of points to complete
        pert_factor: PERT factor for calculations
        data_points_count: Number of most recent data points to use (defaults to all)

    Returns:
        Dictionary containing all data needed for visualization
    """
    # Handle empty dataframe case
    if df.empty:
        return {
            "df_calc": df,
            "pert_time_items": 0,
            "pert_time_points": 0,
            "items_forecasts": {"avg": ([], []), "opt": ([], []), "pes": ([], [])},
            "points_forecasts": {"avg": ([], []), "opt": ([], []), "pes": ([], [])},
            "max_items": total_items,
            "max_points": total_points,
            "start_date": datetime.now(),
            "last_items": total_items,
            "last_points": total_points,
        }

    # Convert string dates to datetime for calculations
    df_calc = df.copy()
    df_calc["date"] = pd.to_datetime(df_calc["date"])

    # Filter to use only the specified number of most recent data points
    if data_points_count is not None and len(df_calc) > data_points_count:
        # Sort by date descending to get most recent first
        df_calc = df_calc.sort_values("date", ascending=False)
        # Take only the specified number of rows
        df_calc = df_calc.head(data_points_count)
        # Resort by date ascending for calculations
        df_calc = df_calc.sort_values("date", ascending=True)

    # Compute weekly throughput and rates
    grouped = compute_weekly_throughput(df_calc)
    rates = calculate_rates(grouped, total_items, total_points, pert_factor)

    (
        pert_time_items,
        optimistic_items_rate,
        pessimistic_items_rate,
        pert_time_points,
        optimistic_points_rate,
        pessimistic_points_rate,
    ) = rates

    # Compute daily rates
    items_daily_rate = (
        total_items / pert_time_items
        if pert_time_items > 0 and pert_time_items != float("inf")
        else 0
    )

    points_daily_rate = (
        total_points / pert_time_points
        if pert_time_points > 0 and pert_time_points != float("inf")
        else 0
    )

    # Get starting points for forecast
    start_date = df_calc["date"].iloc[-1] if not df_calc.empty else datetime.now()
    last_items = df_calc["cum_items"].iloc[-1] if not df_calc.empty else total_items
    last_points = df_calc["cum_points"].iloc[-1] if not df_calc.empty else total_points

    # Generate forecast data
    items_forecasts = {
        "avg": daily_forecast(last_items, items_daily_rate, start_date),
        "opt": daily_forecast(last_items, optimistic_items_rate, start_date),
        "pes": daily_forecast(last_items, pessimistic_items_rate, start_date),
    }

    points_forecasts = {
        "avg": daily_forecast(last_points, points_daily_rate, start_date),
        "opt": daily_forecast(last_points, optimistic_points_rate, start_date),
        "pes": daily_forecast(last_points, pessimistic_points_rate, start_date),
    }

    # Calculate max values for axis scaling
    max_items = max(
        df_calc["cum_items"].max() if not df_calc.empty else total_items,
        max(
            max(items_forecasts["avg"][1]) if items_forecasts["avg"][1] else 0,
            max(items_forecasts["opt"][1]) if items_forecasts["opt"][1] else 0,
            max(items_forecasts["pes"][1]) if items_forecasts["pes"][1] else 0,
        ),
    )

    max_points = max(
        df_calc["cum_points"].max() if not df_calc.empty else total_points,
        max(
            max(points_forecasts["avg"][1]) if points_forecasts["avg"][1] else 0,
            max(points_forecasts["opt"][1]) if points_forecasts["opt"][1] else 0,
            max(points_forecasts["pes"][1]) if points_forecasts["pes"][1] else 0,
        ),
    )

    return {
        "df_calc": df_calc,
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "items_forecasts": items_forecasts,
        "points_forecasts": points_forecasts,
        "max_items": max_items,
        "max_points": max_points,
        "start_date": start_date,
        "last_items": last_items,
        "last_points": last_points,
    }
