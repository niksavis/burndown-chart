"""
Visualization Helpers Module

This module provides utility functions that support chart generation and
visualization in the Burndown Chart application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import logging
import traceback
from datetime import datetime, timedelta

# Third-party library imports
import pandas as pd
import plotly.graph_objects as go

#######################################################################
# TYPE CONVERSION AND VALIDATION HELPERS
#######################################################################


def safe_numeric_convert(value, default=0.0):
    """
    Safely convert a value to a float with error handling.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Converted float value
    """
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def parse_deadline_milestone(deadline_str, milestone_str=None):
    """
    Parse deadline and optional milestone dates.

    Args:
        deadline_str: Deadline date string (YYYY-MM-DD)
        milestone_str: Optional milestone date string (YYYY-MM-DD)

    Returns:
        Tuple of (deadline, milestone) as datetime objects
    """
    # Parse deadline with error handling
    try:
        deadline = pd.to_datetime(deadline_str)
    except (ValueError, TypeError):
        # Use fallback date 30 days from now if deadline format is invalid
        deadline = pd.Timestamp.now() + pd.Timedelta(days=30)
        logging.getLogger("burndown_chart").warning(
            f"Invalid deadline format: {deadline_str}. Using default."
        )

    # Parse milestone date if provided
    milestone = None
    if milestone_str:
        try:
            milestone = pd.to_datetime(milestone_str)
            # Only reject milestones that are AFTER the deadline, not equal to it
            if milestone > deadline:
                logging.getLogger("burndown_chart").warning(
                    f"Milestone date {milestone_str} is after deadline {deadline_str}. Ignoring milestone."
                )
                milestone = None
        except (ValueError, TypeError):
            logging.getLogger("burndown_chart").warning(
                f"Invalid milestone format: {milestone_str}. Ignoring milestone."
            )

    return deadline, milestone


#######################################################################
# DATA CALCULATION HELPERS
#######################################################################


def get_weekly_metrics(df, data_points_count=None):
    """
    Calculate weekly metrics from the data frame.

    Args:
        df: DataFrame with historical data
        data_points_count: Number of data points to use for calculations (default: None, uses all data)

    Returns:
        Tuple of (avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points)
    """
    # Ensure data_points_count is an integer (could be float from UI slider)
    if data_points_count is not None:
        data_points_count = int(data_points_count)

    # Import here to avoid circular imports
    from data import calculate_weekly_averages

    avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
        0.0,
        0.0,
        0.0,
        0.0,
    )

    if not df.empty:
        # Apply filtering before calculating metrics
        filtered_df = df
        if (
            data_points_count is not None
            and data_points_count > 0
            and len(df) > data_points_count
        ):
            filtered_df = df.tail(data_points_count)

        # Get all four values from calculate_weekly_averages with filtering
        results = calculate_weekly_averages(
            filtered_df.to_dict("records"), data_points_count=data_points_count
        )
        if isinstance(results, (list, tuple)) and len(results) >= 4:
            avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
                results
            )

        # Ensure all are valid float values
        avg_weekly_items = float(
            avg_weekly_items if avg_weekly_items is not None else 0.0
        )
        avg_weekly_points = float(
            avg_weekly_points if avg_weekly_points is not None else 0.0
        )
        med_weekly_items = float(
            med_weekly_items if med_weekly_items is not None else 0.0
        )
        med_weekly_points = float(
            med_weekly_points if med_weekly_points is not None else 0.0
        )

    return avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points


def calculate_forecast_completion_dates(pert_time_items, pert_time_points):
    """
    Calculate formatted completion dates based on PERT estimates.

    Args:
        pert_time_items: PERT time estimate for items in days
        pert_time_points: PERT time estimate for points in days

    Returns:
        Tuple of (items_completion_enhanced, points_completion_enhanced) strings
    """
    import math

    # Handle NaN, None, or invalid values
    if pert_time_items is None or (
        isinstance(pert_time_items, float) and math.isnan(pert_time_items)
    ):
        items_completion_enhanced = "N/A (insufficient data)"
    else:
        current_date = datetime.now()
        items_completion_date = current_date + timedelta(days=pert_time_items)
        items_completion_str = items_completion_date.strftime("%Y-%m-%d")
        items_completion_enhanced = f"{items_completion_str} ({pert_time_items:.1f} days, {pert_time_items / 7:.1f} weeks)"

    if pert_time_points is None or (
        isinstance(pert_time_points, float) and math.isnan(pert_time_points)
    ):
        points_completion_enhanced = "N/A (insufficient data)"
    else:
        current_date = datetime.now()
        points_completion_date = current_date + timedelta(days=pert_time_points)
        points_completion_str = points_completion_date.strftime("%Y-%m-%d")
        points_completion_enhanced = f"{points_completion_str} ({pert_time_points:.1f} days, {pert_time_points / 7:.1f} weeks)"

    return items_completion_enhanced, points_completion_enhanced


def prepare_metrics_data(
    total_items,
    total_points,
    deadline,
    pert_time_items,
    pert_time_points,
    data_points_count,
    df,
    items_completion_enhanced,
    points_completion_enhanced,
    avg_weekly_items=0,
    avg_weekly_points=0,
    med_weekly_items=0,
    med_weekly_points=0,
):
    """
    Prepare metrics data for display in the forecast plot.

    Args:
        total_items: Total number of items
        total_points: Total number of points
        deadline: Deadline date
        pert_time_items: PERT time estimate for items in days
        pert_time_points: PERT time estimate for points in days
        data_points_count: Number of data points used for calculations
        df: DataFrame with historical data
        items_completion_enhanced: Enhanced items completion date string
        points_completion_enhanced: Enhanced points completion date string
        avg_weekly_items: Average weekly items
        avg_weekly_points: Average weekly points
        med_weekly_items: Median weekly items
        med_weekly_points: Median weekly points

    Returns:
        Dictionary with metrics data
    """
    # Calculate days to deadline
    current_date = datetime.now()

    # Handle NaT deadline safely
    if pd.isna(deadline):
        days_to_deadline = 0
        deadline_str = "No deadline set"
    else:
        days_to_deadline = max(0, (deadline - pd.Timestamp(current_date)).days)
        deadline_str = deadline.strftime("%Y-%m-%d")

    # Create metrics data dictionary
    return {
        "total_items": total_items,
        "total_points": total_points,
        "deadline": deadline_str,
        "days_to_deadline": days_to_deadline,
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "avg_weekly_items": avg_weekly_items,
        "avg_weekly_points": avg_weekly_points,
        "med_weekly_items": med_weekly_items,
        "med_weekly_points": med_weekly_points,
        "data_points_used": int(data_points_count)
        if data_points_count is not None and isinstance(data_points_count, (int, float))
        else (len(df) if hasattr(df, "__len__") else 0),
        "data_points_available": len(df) if hasattr(df, "__len__") else 0,
        "items_completion_enhanced": items_completion_enhanced,
        "points_completion_enhanced": points_completion_enhanced,
    }


#######################################################################
# FORECAST UTILITY FUNCTIONS
#######################################################################


def generate_burndown_forecast(
    last_value, avg_rate, opt_rate, pes_rate, start_date, end_date
):
    """
    Generate burndown forecast with a fixed end date to ensure consistency with burnup charts.
    Includes strict 10-year maximum cap for visualization performance.

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
    from datetime import datetime

    # STRICT 10-YEAR CAP: Never forecast beyond today + 10 years
    today = datetime.now()
    absolute_max_date = today + timedelta(
        days=3653
    )  # 10 years from today (accounting for leap years)
    MAX_FORECAST_DAYS = 3653  # Absolute maximum

    # Calculate days between start and end
    days_span = (end_date - start_date).days
    if days_span <= 0:
        # If end date is same as or before start date, use 1 day
        days_span = 1

    # Calculate days needed for each rate to reach zero, but cap at 10 years
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

    # Cap everything at maximum forecast horizon
    max_days = min(
        MAX_FORECAST_DAYS,
        max(days_span, days_to_zero_avg, days_to_zero_opt, days_to_zero_pes),
    )

    # Create date ranges with strict caps for performance
    dates_avg = [
        start_date + timedelta(days=i)
        for i in range(min(max_days, days_to_zero_avg) + 1)
        if start_date + timedelta(days=i) <= absolute_max_date
    ]
    dates_opt = [
        start_date + timedelta(days=i)
        for i in range(min(max_days, days_to_zero_opt) + 1)
        if start_date + timedelta(days=i) <= absolute_max_date
    ]
    dates_pes = [
        start_date + timedelta(days=i)
        for i in range(min(max_days, days_to_zero_pes) + 1)
        if start_date + timedelta(days=i) <= absolute_max_date
    ]

    # Calculate decreasing values for each rate
    avg_values = []
    opt_values = []
    pes_values = []

    # Average rate forecast
    for i in range(len(dates_avg)):
        remaining_avg = max(0, last_value - (avg_rate * i))
        avg_values.append(remaining_avg)

    # Optimistic rate forecast
    for i in range(len(dates_opt)):
        remaining_opt = max(0, last_value - (opt_rate * i))
        opt_values.append(remaining_opt)

    # Pessimistic rate forecast
    for i in range(len(dates_pes)):
        remaining_pes = max(0, last_value - (pes_rate * i))
        pes_values.append(remaining_pes)

    return {
        "avg": (dates_avg, avg_values),
        "opt": (dates_opt, opt_values),
        "pes": (dates_pes, pes_values),
    }


def format_hover_template_fix(
    title=None, fields=None, extra_info=None, include_extra_tag=True
):
    """
    Create a consistent hover template string for Plotly charts.
    This version properly escapes format specifiers for Plotly.

    Args:
        title (str, optional): Title to display at the top of the tooltip
        fields (dict, optional): Dictionary of {label: value_template} pairs
        extra_info (str, optional): Additional information for the <extra> tag
        include_extra_tag (bool, optional): Whether to include the <extra> tag

    Returns:
        str: Formatted hover template string for Plotly
    """
    template = []

    # Add title if provided
    if title:
        template.append(f"<b>{title}</b><br>")

    # Add fields if provided
    if fields:
        for label, value in fields.items():
            template.append(f"{label}: {value}<br>")

    # Join all template parts
    hover_text = "".join(template)

    # Add extra tag if requested
    if include_extra_tag:
        if extra_info:
            return f"{hover_text}<extra>{extra_info}</extra>"
        return f"{hover_text}<extra></extra>"

    return hover_text


#######################################################################
# ERROR HANDLING FUNCTIONS
#######################################################################


def handle_forecast_error(e):
    """
    Handle exceptions in forecast plot creation with detailed error reporting.

    Args:
        e: Exception that occurred

    Returns:
        Tuple of (error_figure, safe_data_dict)
    """
    # Get full stack trace
    error_trace = traceback.format_exc()
    logger = logging.getLogger("burndown_chart")
    logger.error(f"Error in create_forecast_plot: {str(e)}\n{error_trace}")

    # Create an empty figure with detailed error message
    fig = go.Figure()
    fig.add_annotation(
        text=f"Error in forecast plot generation:<br>{str(e)}",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="red"),
    )

    # Add button to show/hide detailed error info
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.5,
                y=0.4,
                xanchor="center",
                yanchor="top",
                buttons=[
                    dict(
                        label="Show Error Details",
                        method="update",
                        args=[
                            {},
                            {
                                "annotations": [
                                    {
                                        "text": f"Error in forecast plot generation:<br>{str(e)}<br><br>Stack trace (for developers):<br>{error_trace.replace(chr(10), '<br>')}",
                                        "xref": "paper",
                                        "yref": "paper",
                                        "x": 0.5,
                                        "y": 0.5,
                                        "showarrow": False,
                                        "font": dict(size=12, color="red"),
                                        "align": "left",
                                        "bgcolor": "rgba(255, 255, 255, 0.9)",
                                        "bordercolor": "red",
                                        "borderwidth": 1,
                                        "borderpad": 4,
                                    }
                                ]
                            },
                        ],
                    )
                ],
            )
        ]
    )

    # Return safe fallback values with consistent types
    safe_pert_data = {
        "pert_time_items": 0.0,
        "pert_time_points": 0.0,
        "items_completion_enhanced": "Error in calculation",
        "points_completion_enhanced": "Error in calculation",
        "days_to_deadline": 0,
        "avg_weekly_items": 0.0,
        "avg_weekly_points": 0.0,
        "med_weekly_items": 0.0,
        "med_weekly_points": 0.0,
        "error": str(e),
        "forecast_timestamp": datetime.now().isoformat(),
    }

    return fig, safe_pert_data


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
    for i, row in df.iterrows():
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
        df: DataFrame or list of dictionaries with historical data
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

    # Import needed functions
    from data.processing import (
        daily_forecast_burnup,
        compute_weekly_throughput,
        calculate_rates,
    )
    from utils.dataframe_utils import df_to_dict, ensure_dataframe

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
            "items_forecasts": {"avg": ([], []), "opt": ([], []), "pes": ([], [])},
            "points_forecasts": {"avg": ([], []), "opt": ([], []), "pes": ([], [])},
            "max_items": total_items,
            "max_points": total_points,
            "start_date": datetime.now(),
            "last_items": total_items,
            "last_points": total_points,
        }

    # Convert to DataFrame if input is a list of dictionaries
    df_calc = ensure_dataframe(df)

    # Convert string dates to datetime for calculations
    df_calc["date"] = pd.to_datetime(df_calc["date"])

    # Ensure data is sorted by date in ascending order
    df_calc = df_calc.sort_values("date", ascending=True)

    # Filter to use only the specified number of most recent data points
    if (
        data_points_count is not None
        and data_points_count > 0
        and len(df_calc) > data_points_count
    ):
        # Get the most recent data_points_count rows
        df_calc = df_calc.iloc[-data_points_count:]

    # Compute weekly throughput with the filtered data
    grouped_df = compute_weekly_throughput(df_calc)

    # Filter out zero-value weeks before calculating rates
    # These are artificial weeks added by _fill_missing_weeks and shouldn't
    # influence PERT pessimistic/optimistic calculations
    grouped_df_non_zero = grouped_df[
        (grouped_df["completed_items"] > 0) | (grouped_df["completed_points"] > 0)
    ].copy()

    # If all weeks are zero, use the original data to avoid empty DataFrame
    if len(grouped_df_non_zero) == 0:
        grouped_df_non_zero = grouped_df

    # Convert DataFrame to dictionary for caching
    # This prevents the "unhashable type: 'DataFrame'" error
    grouped_dict = df_to_dict(grouped_df_non_zero)

    # Log the data type for debugging
    logger = logging.getLogger("burndown_chart")
    logger.debug(f"Using {type(grouped_dict).__name__} as input to calculate_rates")

    # Convert dictionary back to DataFrame for calculate_rates
    if isinstance(grouped_dict, dict):
        grouped_df_for_rates = pd.DataFrame.from_dict(grouped_dict)
    elif isinstance(grouped_dict, list):
        grouped_df_for_rates = pd.DataFrame(grouped_dict)
    else:
        grouped_df_for_rates = (
            grouped_df_non_zero  # Use filtered df if conversion failed
        )

    # Call calculate_rates with DataFrame
    try:
        rates = calculate_rates(
            grouped_df_for_rates, total_items, total_points, pert_factor, show_points
        )
    except TypeError as e:
        logger.error(f"Type error in calculate_rates: {str(e)}")
        # Create safe default values in case of error
        rates = (0, 0, 0, 0, 0, 0)

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

    # Use completed items/points values for burnup chart
    if is_burnup:
        last_completed_items = df_calc["cum_items"].iloc[-1] if not df_calc.empty else 0
        last_completed_points = (
            df_calc["cum_points"].iloc[-1] if not df_calc.empty else 0
        )

        # For burnup charts, start from completed values and forecast toward scope
        items_forecasts = {
            "avg": daily_forecast_burnup(
                last_completed_items, items_daily_rate, start_date, scope_items
            ),
            "opt": daily_forecast_burnup(
                last_completed_items, optimistic_items_rate, start_date, scope_items
            ),
            "pes": daily_forecast_burnup(
                last_completed_items, pessimistic_items_rate, start_date, scope_items
            ),
        }

        points_forecasts = {
            "avg": daily_forecast_burnup(
                last_completed_points, points_daily_rate, start_date, scope_points
            ),
            "opt": daily_forecast_burnup(
                last_completed_points, optimistic_points_rate, start_date, scope_points
            ),
            "pes": daily_forecast_burnup(
                last_completed_points, pessimistic_points_rate, start_date, scope_points
            ),
        }
    else:
        # For burndown charts, we need to ensure consistent end dates with burnup charts
        # First, calculate burnup forecasts to get end dates
        burnup_items_avg = daily_forecast_burnup(
            0, items_daily_rate, start_date, total_items
        )
        burnup_points_avg = daily_forecast_burnup(
            0, points_daily_rate, start_date, total_points
        )

        # Get the end dates from burnup forecasts
        items_end_date = burnup_items_avg[0][-1] if burnup_items_avg[0] else start_date
        points_end_date = (
            burnup_points_avg[0][-1] if burnup_points_avg[0] else start_date
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
