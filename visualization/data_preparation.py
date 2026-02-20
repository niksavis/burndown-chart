"""
Data Preparation Module

This module contains functions for preparing and processing data
for forecast visualizations including burndown/burnup charts.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import logging
from datetime import datetime, timedelta

# Third-party library imports
import pandas as pd

# Get logger
logger = logging.getLogger(__name__)


#######################################################################
# SCOPE ANALYSIS FUNCTIONS
#######################################################################


def identify_significant_scope_growth(df, threshold_pct=10):
    """
    Identify periods with significant scope growth.

    Args:
        df: DataFrame with statistics data including cum_scope_items and cum_scope_points
        threshold_pct: Percentage threshold for significant growth (default: 10%)

    Returns:
        List of dictionaries with start_date and end_date for periods of significant growth
    """
    if df.empty:
        return []

    significant_periods = []
    current_period = None

    # Calculate percentage changes
    df = df.copy().sort_values("date")
    df["items_pct_change"] = df["cum_scope_items"].pct_change() * 100
    df["points_pct_change"] = df["cum_scope_points"].pct_change() * 100

    # Find periods with significant growth
    for _i, row in df.iterrows():
        if (
            row["items_pct_change"] > threshold_pct
            or row["points_pct_change"] > threshold_pct
        ):
            if current_period is None:
                # Start a new significant period
                current_period = {
                    "start_date": row["date"],
                    "end_date": row["date"],
                    "max_items_pct": row["items_pct_change"]
                    if not pd.isna(row["items_pct_change"])
                    else 0,
                    "max_points_pct": row["points_pct_change"]
                    if not pd.isna(row["points_pct_change"])
                    else 0,
                }
            else:
                # Extend the current period
                current_period["end_date"] = row["date"]
                if (
                    not pd.isna(row["items_pct_change"])
                    and row["items_pct_change"] > current_period["max_items_pct"]
                ):
                    current_period["max_items_pct"] = row["items_pct_change"]
                if (
                    not pd.isna(row["points_pct_change"])
                    and row["points_pct_change"] > current_period["max_points_pct"]
                ):
                    current_period["max_points_pct"] = row["points_pct_change"]
        else:
            # End the current period if it exists
            if current_period is not None:
                # Only include periods that span at least one day
                if (
                    current_period["end_date"] - current_period["start_date"]
                ).days >= 0:
                    significant_periods.append(current_period)
                current_period = None

    # Handle case where last row is part of a significant period
    if current_period is not None:
        current_period["end_date"] = current_period["end_date"] + pd.Timedelta(days=1)
        significant_periods.append(current_period)

    return significant_periods


#######################################################################
# FORECAST GENERATION FUNCTIONS
#######################################################################


def generate_burndown_forecast(
    last_value, avg_rate, opt_rate, pes_rate, start_date, end_date
):
    """
    Generate burndown forecast with a fixed end date to ensure consistency with burnup charts.
    Includes strict performance optimizations: 2-year max horizon, 100 points per line max.

    Args:
        last_value: Current remaining value (items or points)
        avg_rate: Average daily completion rate
        opt_rate: Optimistic daily completion rate
        pes_rate: Pessimistic daily completion rate
        start_date: Start date for forecast
        end_date: End date the forecast should reach (for alignment with burnup chart)

    Returns:
        Dictionary containing forecasts for average, optimistic, and pessimistic scenarios
    """
    # PERFORMANCE: Limit forecast to 2 years and max 100 points per line
    # This prevents chart freezing with thousands of data points
    MAX_FORECAST_DAYS = 730  # 2 years maximum
    MAX_POINTS_PER_LINE = 100  # Maximum data points per forecast line

    # Calculate days between start and end
    days_span = (end_date - start_date).days
    if days_span <= 0:
        # If end date is same as or before start date, use 1 day
        days_span = 1

    # Calculate days needed for each rate to reach zero, but cap at max
    days_to_zero_avg = min(
        MAX_FORECAST_DAYS,
        int(last_value / avg_rate) if avg_rate > 0.001 else days_span * 2,
    )
    days_to_zero_opt = min(
        MAX_FORECAST_DAYS,
        int(last_value / opt_rate) if opt_rate > 0.001 else days_span * 2,
    )
    days_to_zero_pes = min(
        MAX_FORECAST_DAYS,
        int(last_value / pes_rate) if pes_rate > 0.001 else days_span * 2,
    )

    # PERFORMANCE: Calculate sampling interval to limit data points
    def generate_sampled_forecast(days_to_zero, rate):
        """Generate forecast with even sampling throughout the entire forecast period."""
        # Calculate interval to distribute points evenly across entire forecast
        # This ensures consistent spacing from start to finish (no condensed-then-sparse appearance)
        sample_interval = max(1, int(days_to_zero / MAX_POINTS_PER_LINE))

        dates = []
        values = []
        day = 0

        # Sample evenly across the entire forecast period
        while day <= days_to_zero:
            forecast_date = start_date + timedelta(days=day)
            remaining = max(0, last_value - (rate * day))
            dates.append(forecast_date)
            values.append(remaining)

            # Stop if we reached zero
            if remaining <= 0:
                break

            day += sample_interval

        # Always ensure we have a final point at zero for visual closure
        if values and values[-1] > 0:
            final_date = start_date + timedelta(days=days_to_zero)
            dates.append(final_date)
            values.append(0)

        return dates, values

    # Generate forecasts with sampling
    dates_avg, avg_values = generate_sampled_forecast(days_to_zero_avg, avg_rate)
    dates_opt, opt_values = generate_sampled_forecast(days_to_zero_opt, opt_rate)
    dates_pes, pes_values = generate_sampled_forecast(days_to_zero_pes, pes_rate)

    # Debug logging
    logger.info(
        f"[BURNDOWN FORECAST] Generated forecasts: avg={len(dates_avg)} points, "
        f"opt={len(dates_opt)} points, pes={len(dates_pes)} points"
    )

    return {
        "avg": (dates_avg, avg_values),
        "opt": (dates_opt, opt_values),
        "pes": (dates_pes, pes_values),
    }


#######################################################################
# DATA PREPARATION FUNCTIONS
#######################################################################


def prepare_visualization_data(
    df,
    total_items,
    total_points,
    pert_factor,
    data_points_count=None,
    is_burnup=False,
    scope_items=None,
    scope_points=None,
    show_points=True,
):
    """
    Prepare all necessary data for the forecast visualization.

    Args:
        df: DataFrame with historical data
        total_items: Total number of items to complete
        total_points: Total number of points to complete
        pert_factor: PERT factor for calculations
        data_points_count: Number of most recent data points to use (defaults to all)
        is_burnup: Whether this is for a burnup chart (True) or burndown chart (False)
        scope_items: Total scope of items (required for burnup charts)
        scope_points: Total scope of points (required for burnup charts)
        show_points: Whether points tracking is enabled (default: True)

    Returns:
        Dictionary containing all data needed for visualization
    """
    # Ensure data_points_count is an integer (could be float from UI slider)
    if data_points_count is not None:
        data_points_count = int(data_points_count)

    # Import needed functions from data module
    from data.processing import (
        calculate_rates,
        compute_weekly_throughput,
        daily_forecast_burnup,
    )
    from utils.dataframe_utils import ensure_dataframe

    # Handle empty dataframe case
    if (
        df is None
        or (isinstance(df, pd.DataFrame) and df.empty)
        or (isinstance(df, list) and len(df) == 0)
    ):
        return {
            "df_calc": pd.DataFrame() if not isinstance(df, pd.DataFrame) else df,
            "pert_time_items": 0,
            "pert_time_points": 0,
            "items_forecasts": {
                "avg": ([], []),
                "opt": ([], []),
                "pes": ([], []),
                "ewma": ([], []),
            },
            "points_forecasts": {
                "avg": ([], []),
                "opt": ([], []),
                "pes": ([], []),
                "ewma": ([], []),
            },
            "max_items": total_items,
            "max_points": total_points,
            "start_date": datetime.now(),
            "last_items": total_items,
            "last_points": total_points,
        }

    # Convert to DataFrame if input is a list of dictionaries
    df_calc = ensure_dataframe(df)

    # Convert string dates to datetime for calculations
    df_calc["date"] = pd.to_datetime(df_calc["date"], format="mixed", errors="coerce")

    # Ensure data is sorted by date in ascending order
    df_calc = df_calc.sort_values("date", ascending=True)

    # Initialize scope variables
    total_scope_items = total_items
    total_scope_points = total_points

    # Calculate total scope by adding completed work and remaining work
    if not is_burnup:
        # For burndown charts, calculate completed work
        completed_items = (
            df_calc["completed_items"].sum()
            if "completed_items" in df_calc.columns
            else 0
        )
        completed_points = (
            df_calc["completed_points"].sum()
            if "completed_points" in df_calc.columns
            else 0
        )

        # Calculate total scope
        total_scope_items = completed_items + total_items
        total_scope_points = completed_points + total_points

        # PERFORMANCE OPTIMIZATION: Use vectorized operations instead of slow loop
        # Calculate remaining work by reverse cumsum (much faster than iterative approach)
        if (
            "completed_items" in df_calc.columns
            and "completed_points" in df_calc.columns
        ):
            # Ensure numeric types
            df_calc["completed_items"] = pd.to_numeric(
                df_calc["completed_items"], errors="coerce"
            ).fillna(0)
            df_calc["completed_points"] = pd.to_numeric(
                df_calc["completed_points"], errors="coerce"
            ).fillna(0)

            # Vectorized calculation: reverse cumsum to get remaining work at each point
            reversed_items = df_calc["completed_items"][::-1].cumsum()[::-1]
            reversed_points = df_calc["completed_points"][::-1].cumsum()[::-1]

            df_calc["cum_items"] = reversed_items + total_items
            df_calc["cum_points"] = reversed_points + total_points
        else:
            # Fallback if columns don't exist
            df_calc["cum_items"] = total_scope_items
            df_calc["cum_points"] = total_scope_points

    # Filter to use only the specified number of most recent data points
    # CRITICAL FIX: Use date-based filtering instead of row count (.iloc)
    # data_points_count represents WEEKS, not rows. With sparse data,
    # row-based filtering gives incorrect results.

    if (
        data_points_count is not None
        and data_points_count > 0
        and not df_calc.empty
        and "date" in df_calc.columns
    ):
        # Apply date-based filtering
        latest_date = df_calc["date"].max()
        cutoff_date = latest_date - timedelta(weeks=data_points_count)
        rows_before = len(df_calc)
        df_calc = df_calc[df_calc["date"] >= cutoff_date]
        rows_after = len(df_calc)

        logger.info(
            f"[FORECAST FILTER] data_points_count={data_points_count} weeks, "
            f"latest_date={latest_date.strftime('%Y-%m-%d') if hasattr(latest_date, 'strftime') else latest_date}, "
            f"cutoff_date={cutoff_date.strftime('%Y-%m-%d') if hasattr(cutoff_date, 'strftime') else cutoff_date}, "
            f"rows: {rows_before} -> {rows_after}"
        )

    # Compute weekly throughput with the filtered data
    grouped = compute_weekly_throughput(df_calc)

    # Ensure grouped is a DataFrame
    if not isinstance(grouped, pd.DataFrame):
        grouped = pd.DataFrame(grouped)
    logger.info(
        f"[CHART DATA] df_calc rows={len(df_calc)}, grouped weeks={len(grouped)}, "
        f"data_points_count={data_points_count}, "
        f"grouped non-zero items={len(grouped[grouped['completed_items'] > 0])}, "
        f"grouped non-zero points={len(grouped[grouped['completed_points'] > 0])}"
    )

    # Filter out zero-value weeks before calculating rates
    # Filter separately for items and points to support projects with only one tracking type
    # Zero weeks (often from fill_missing_weeks) shouldn't influence rate calculations
    grouped_items_non_zero = grouped[grouped["completed_items"] > 0].copy()
    grouped_points_non_zero = grouped[grouped["completed_points"] > 0].copy()

    # Determine which filtering to use based on available data
    has_items_data = len(grouped_items_non_zero) > 0
    has_points_data = len(grouped_points_non_zero) > 0

    # If no valid weeks exist for either metric, return early with safe defaults
    # (prevents pessimistic forecasts from extending years into the future)
    if not has_items_data and not has_points_data:
        # Return empty forecast data to indicate insufficient data
        return {
            "df_calc": df_calc,
            "pert_time_items": 0,
            "pert_time_points": 0,
            "items_forecasts": {
                "avg": ([], []),
                "opt": ([], []),
                "pes": ([], []),
                "ewma": ([], []),
            },
            "points_forecasts": {
                "avg": ([], []),
                "opt": ([], []),
                "pes": ([], []),
                "ewma": ([], []),
            },
            "max_items": df_calc["cum_items"].max()
            if not df_calc.empty
            else total_items,
            "max_points": df_calc["cum_points"].max()
            if not df_calc.empty
            else total_points,
            "start_date": df_calc["date"].iloc[-1]
            if not df_calc.empty
            else datetime.now(),
            "last_items": df_calc["cum_items"].iloc[-1]
            if not df_calc.empty
            else total_items,
            "last_points": df_calc["cum_points"].iloc[-1]
            if not df_calc.empty
            else total_points,
        }

    from data.metrics.forecast_calculator import calculate_ewma_forecast

    ewma_items_weekly = (
        calculate_ewma_forecast(
            grouped_items_non_zero["completed_items"].tolist(), alpha=0.3
        )
        if has_items_data
        else None
    )
    ewma_points_weekly = (
        calculate_ewma_forecast(
            grouped_points_non_zero["completed_points"].tolist(), alpha=0.3
        )
        if has_points_data
        else None
    )

    ewma_items_daily_rate = (
        ewma_items_weekly.get("forecast_value", 0) / 7.0 if ewma_items_weekly else None
    )
    ewma_points_daily_rate = (
        ewma_points_weekly.get("forecast_value", 0) / 7.0
        if ewma_points_weekly
        else None
    )

    # Use items data for calculation if available, otherwise use points data
    # This ensures we can calculate forecasts even when only one type has data
    grouped_non_zero = (
        grouped_items_non_zero if has_items_data else grouped_points_non_zero
    )

    rates = calculate_rates(
        grouped_non_zero, total_items, total_points, pert_factor, show_points
    )

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

    # Debug logging for forecast calculation
    logger.info(
        f"[CHART FORECAST] start_date={start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else start_date}, "
        f"pert_time_items={pert_time_items:.2f}, total_items={total_items}, "
        f"items_daily_rate={items_daily_rate:.4f}"
    )

    # For burndown charts, we need to get the correct last values
    # (these represent remaining work, not completed work)
    if not is_burnup:
        last_items = (
            df_calc["cum_items"].iloc[-1] if not df_calc.empty else total_scope_items
        )
        last_points = (
            df_calc["cum_points"].iloc[-1] if not df_calc.empty else total_scope_points
        )
    else:
        # For burnup charts, use the completed work values
        last_completed_items = df_calc["cum_items"].iloc[-1] if not df_calc.empty else 0
        last_completed_points = (
            df_calc["cum_points"].iloc[-1] if not df_calc.empty else 0
        )
        last_items = last_completed_items  # This is completed items for burnup
        last_points = last_completed_points  # This is completed points for burnup

    # Use completed items/points values for burnup chart
    # PERFORMANCE: Limit forecast to 2 years (730 days) and max 100 points per line
    if is_burnup:
        # For burnup charts, start from completed values and forecast toward scope
        items_forecasts = {
            "avg": daily_forecast_burnup(
                last_items,
                items_daily_rate,
                start_date,
                scope_items,
                max_days=730,
                max_points=100,
            ),
            "opt": daily_forecast_burnup(
                last_items,
                optimistic_items_rate,
                start_date,
                scope_items,
                max_days=730,
                max_points=100,
            ),
            "pes": daily_forecast_burnup(
                last_items,
                pessimistic_items_rate,
                start_date,
                scope_items,
                max_days=730,
                max_points=100,
            ),
        }

        points_forecasts = {
            "avg": daily_forecast_burnup(
                last_points,
                points_daily_rate,
                start_date,
                scope_points,
                max_days=730,
                max_points=100,
            ),
            "opt": daily_forecast_burnup(
                last_points,
                optimistic_points_rate,
                start_date,
                scope_points,
                max_days=730,
                max_points=100,
            ),
            "pes": daily_forecast_burnup(
                last_points,
                pessimistic_points_rate,
                start_date,
                scope_points,
                max_days=730,
                max_points=100,
            ),
        }

        items_ewma_forecast = (
            daily_forecast_burnup(
                last_items,
                ewma_items_daily_rate,
                start_date,
                scope_items,
                max_days=730,
                max_points=100,
            )
            if ewma_items_daily_rate is not None
            else ([], [])
        )

        points_ewma_forecast = (
            daily_forecast_burnup(
                last_points,
                ewma_points_daily_rate,
                start_date,
                scope_points,
                max_days=730,
                max_points=100,
            )
            if ewma_points_daily_rate is not None
            else ([], [])
        )
    else:
        # For burndown charts, we need to ensure consistent end dates with burnup charts
        # First, calculate burnup forecasts to get end dates
        # PERFORMANCE: Limit forecast to 2 years (730 days) and max 100 points per line
        burnup_items_avg = daily_forecast_burnup(
            0, items_daily_rate, start_date, total_items, max_days=730, max_points=100
        )
        burnup_points_avg = daily_forecast_burnup(
            0, points_daily_rate, start_date, total_points, max_days=730, max_points=100
        )

        # Get the end dates from burnup forecasts
        items_end_date = burnup_items_avg[0][-1] if burnup_items_avg[0] else start_date
        points_end_date = (
            burnup_points_avg[0][-1] if burnup_points_avg[0] else start_date
        )

        logger.info(
            f"[CHART FORECAST] Burndown end dates: items_end_date={items_end_date.strftime('%Y-%m-%d') if hasattr(items_end_date, 'strftime') else items_end_date}, "
            f"days_to_items_end={(items_end_date - start_date).days if hasattr(items_end_date, 'strftime') else 0}"
        )

        # Now calculate burndown forecasts with fixed end dates
        items_forecasts = generate_burndown_forecast(
            last_items,
            items_daily_rate,
            optimistic_items_rate,
            pessimistic_items_rate,
            start_date,
            items_end_date,
        )

        points_forecasts = generate_burndown_forecast(
            last_points,
            points_daily_rate,
            optimistic_points_rate,
            pessimistic_points_rate,
            start_date,
            points_end_date,
        )

        items_ewma_forecast = (
            generate_burndown_forecast(
                last_items,
                ewma_items_daily_rate,
                ewma_items_daily_rate,
                ewma_items_daily_rate,
                start_date,
                items_end_date,
            ).get("avg", ([], []))
            if ewma_items_daily_rate is not None
            else ([], [])
        )

        points_ewma_forecast = (
            generate_burndown_forecast(
                last_points,
                ewma_points_daily_rate,
                ewma_points_daily_rate,
                ewma_points_daily_rate,
                start_date,
                points_end_date,
            ).get("avg", ([], []))
            if ewma_points_daily_rate is not None
            else ([], [])
        )

    items_forecasts["ewma"] = items_ewma_forecast
    points_forecasts["ewma"] = points_ewma_forecast

    # Calculate max values for axis scaling
    max_items = max(
        df_calc["cum_items"].max() if not df_calc.empty else total_items,
        max(
            max(items_forecasts["avg"][1]) if items_forecasts["avg"][1] else 0,
            max(items_forecasts["opt"][1]) if items_forecasts["opt"][1] else 0,
            max(items_forecasts["pes"][1]) if items_forecasts["pes"][1] else 0,
            max(items_forecasts["ewma"][1]) if items_forecasts["ewma"][1] else 0,
        ),
    )

    max_points = max(
        df_calc["cum_points"].max() if not df_calc.empty else total_points,
        max(
            max(points_forecasts["avg"][1]) if points_forecasts["avg"][1] else 0,
            max(points_forecasts["opt"][1]) if points_forecasts["opt"][1] else 0,
            max(points_forecasts["pes"][1]) if points_forecasts["pes"][1] else 0,
            max(points_forecasts["ewma"][1]) if points_forecasts["ewma"][1] else 0,
        ),
    )

    # Y-axis now dynamically scales to actual data shown on chart
    # (removed fixed scope ceiling that was pushing graphs down)

    # Return results with scope information for burndown charts
    result = {
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

    # Add total scope information for burndown charts
    if not is_burnup:
        result["total_scope_items"] = total_scope_items
        result["total_scope_points"] = total_scope_points

    return result
