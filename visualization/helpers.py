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
# DATA PREPARATION HELPERS
#######################################################################


def fill_missing_weeks(weekly_df, start_date, end_date, value_columns):
    """Fill in missing weeks with zero values to show complete time range.

    Args:
        weekly_df: DataFrame with aggregated weekly data (may have gaps)
        start_date: Start date of the time range
        end_date: End date of the time range
        value_columns: List of column names to fill with zeros (e.g., ['items', 'points'])

    Returns:
        DataFrame with all weeks in the range, missing weeks filled with zeros
    """
    if weekly_df.empty:
        return weekly_df

    # Create complete week range
    all_weeks = []
    current = start_date
    while current <= end_date:
        # Get ISO week info
        iso_calendar = current.isocalendar()
        year_week = f"{iso_calendar.year}-W{iso_calendar.week:02d}"
        all_weeks.append(
            {
                "year_week": year_week,
                "start_date": current
                - timedelta(days=current.weekday()),  # Monday of the week
            }
        )
        current += timedelta(weeks=1)

    # Create DataFrame with all weeks
    all_weeks_df = pd.DataFrame(all_weeks)

    # Merge with actual data, filling missing values with 0
    result_df = all_weeks_df.merge(
        weekly_df, on="year_week", how="left", suffixes=("", "_actual")
    )

    # Use the actual start_date if it exists, otherwise use the computed one
    if "start_date_actual" in result_df.columns:
        result_df["start_date"] = result_df["start_date_actual"].fillna(
            result_df["start_date"]
        )
        result_df = result_df.drop("start_date_actual", axis=1)

    # Ensure start_date is datetime type
    result_df["start_date"] = pd.to_datetime(result_df["start_date"])

    # Fill missing value columns with 0
    for col in value_columns:
        if col in result_df.columns:
            result_df[col] = result_df[col].fillna(0)

    return result_df.sort_values("start_date")


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
        deadline = pd.to_datetime(deadline_str, format="mixed", errors="coerce")
    except (ValueError, TypeError):
        # Use fallback date 30 days from now if deadline format is invalid
        deadline = pd.Timestamp.now() + pd.Timedelta(days=30)
        logging.getLogger("burndown_chart").warning(
            f"Invalid deadline format: {deadline_str}. Using default."
        )

    # Parse milestone date if provided (no restriction - allows visual marker anywhere)
    milestone = None
    if milestone_str:
        try:
            milestone = pd.to_datetime(milestone_str, format="mixed", errors="coerce")
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
        # No pre-filtering needed - calculate_weekly_averages will handle it with date-based filtering
        # Get all four values from calculate_weekly_averages with filtering
        results = calculate_weekly_averages(
            df.to_dict("records"), data_points_count=data_points_count
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
    total_items: int,
    total_points: int,
    deadline,
    pert_time_items: float,
    pert_time_points: float,
    data_points_count: int,
    df,
    items_completion_enhanced: str,
    points_completion_enhanced: str,
    avg_weekly_items: float = 0.0,
    avg_weekly_points: float = 0.0,
    med_weekly_items: float = 0.0,
    med_weekly_points: float = 0.0,
) -> dict:
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

    # Handle None or NaT deadline safely
    if deadline is None or pd.isna(deadline):
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
