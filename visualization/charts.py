"""
Visualization Charts Module

This module contains functions to create and customize the forecast chart
with all its components like traces, markers, and metrics annotations.
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
from plotly.subplots import make_subplots

# Application imports
from configuration import COLOR_PALETTE
from data import (
    calculate_weekly_averages,
    generate_weekly_forecast,
)
from ui.tooltip_utils import create_hoverlabel_config, format_hover_template
# Mobile optimization removed for simplicity - will implement via CSS and responsive config

#######################################################################
# HELPER FUNCTIONS
#######################################################################


def _fill_missing_weeks(weekly_df, start_date, end_date, value_columns):
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
    result_df["start_date"] = pd.to_datetime(
        result_df["start_date"], format="mixed", errors="coerce"
    )

    # Fill missing value columns with 0
    for col in value_columns:
        if col in result_df.columns:
            result_df[col] = result_df[col].fillna(0)

    return result_df.sort_values("start_date")


#######################################################################
# CHART CREATION FUNCTIONS
#######################################################################


def create_plot_traces(
    forecast_data, show_forecast=True, forecast_visibility=True, show_points=True
):
    """
    Create all the traces for the plot.

    Args:
        forecast_data: Dictionary of forecast data from prepare_forecast_data
        show_forecast: Whether to show forecast lines (default: True)
        forecast_visibility: Visibility mode for forecast traces - True, False, or "legendonly" (default: "legendonly")
        show_points: Whether points tracking is enabled (default: True)

    Returns:
        List of traces for Plotly figure
    """
    df_calc = forecast_data["df_calc"]
    items_forecasts = forecast_data["items_forecasts"]
    points_forecasts = forecast_data["points_forecasts"]

    traces = []

    # Historical items trace - enhanced markers
    traces.append(
        {
            "data": go.Scatter(
                x=df_calc["date"],
                y=df_calc["cum_items"],
                mode="lines+markers",
                name="Items History",
                line=dict(color=COLOR_PALETTE["items"], width=3),
                marker=dict(
                    size=10,
                    color=COLOR_PALETTE["items"],
                    symbol="circle",
                    line=dict(width=2, color="white"),
                ),
                hovertemplate=format_hover_template(
                    title="Items History",
                    fields={
                        "Date": "%{x|%Y-%m-%d}",
                        "Items": "%{y}",
                    },
                    extra_info="Items",
                ),
                hoverlabel=create_hoverlabel_config("default"),
            ),
            "secondary_y": False,
        }
    )

    # Items forecast traces - improved line visibility
    traces.append(
        {
            "data": go.Scatter(
                x=items_forecasts["avg"][0],
                y=items_forecasts["avg"][1],
                mode="lines+markers",  # Added markers for better data point visualization
                name="Items Forecast (Most Likely)",
                line=dict(
                    color=COLOR_PALETTE["items"], dash="dash", width=3
                ),  # Increased width
                marker=dict(
                    size=8,
                    symbol="diamond",
                    color=COLOR_PALETTE["items"],
                    line=dict(color="white", width=1),
                ),
                hovertemplate=format_hover_template(
                    title="Items Forecast",
                    fields={
                        "Date": "%{x|%Y-%m-%d}",
                        "Items": "%{y:.1f}",
                        "Type": "Most Likely",
                    },
                ),
                hoverlabel=create_hoverlabel_config("info"),
                visible=True,
            ),
            "secondary_y": False,
        }
    )

    traces.append(
        {
            "data": go.Scatter(
                x=items_forecasts["opt"][0],
                y=items_forecasts["opt"][1],
                mode="lines+markers",  # Added markers
                name="Items Forecast (Optimistic)",
                line=dict(color=COLOR_PALETTE["optimistic"], dash="dot", width=2.5),
                marker=dict(
                    size=7,
                    symbol="triangle-up",
                    color=COLOR_PALETTE["optimistic"],
                    line=dict(color="white", width=1),
                ),
                visible=True,
                hovertemplate=format_hover_template(
                    title="Items Forecast",
                    fields={
                        "Date": "%{x|%Y-%m-%d}",
                        "Items": "%{y:.1f}",
                        "Type": "Optimistic",
                    },
                ),
                hoverlabel=create_hoverlabel_config("success"),
            ),
            "secondary_y": False,
        }
    )

    traces.append(
        {
            "data": go.Scatter(
                x=items_forecasts["pes"][0],
                y=items_forecasts["pes"][1],
                mode="lines+markers",  # Added markers
                name="Items Forecast (Pessimistic)",
                line=dict(color=COLOR_PALETTE["pessimistic"], dash="dot", width=2.5),
                marker=dict(
                    size=7,
                    symbol="triangle-down",
                    color=COLOR_PALETTE["pessimistic"],
                    line=dict(color="white", width=1),
                ),
                visible=True,
                hovertemplate=format_hover_template(
                    title="Items Forecast",
                    fields={
                        "Date": "%{x|%Y-%m-%d}",
                        "Items": "%{y:.1f}",
                        "Type": "Pessimistic",
                    },
                ),
                hoverlabel=create_hoverlabel_config("warning"),
            ),
            "secondary_y": False,
        }
    )

    # Only add points traces if points tracking is enabled
    if show_points:
        # Historical points trace - enhanced markers
        traces.append(
            {
                "data": go.Scatter(
                    x=df_calc["date"],
                    y=df_calc["cum_points"],
                    mode="lines+markers",
                    name="Points History",
                    line=dict(color=COLOR_PALETTE["points"], width=3),
                    marker=dict(
                        size=10,
                        color=COLOR_PALETTE["points"],
                        symbol="circle",
                        line=dict(width=2, color="white"),
                    ),
                    hovertemplate=format_hover_template(
                        title="Points History",
                        fields={
                            "Date": "%{x|%Y-%m-%d}",
                            "Points": "%{y}",
                        },
                        extra_info="Points",
                    ),
                    hoverlabel=create_hoverlabel_config("default"),
                ),
                "secondary_y": True,
            }
        )

        # Points forecast traces - improving visibility
        traces.append(
            {
                "data": go.Scatter(
                    x=points_forecasts["avg"][0],
                    y=points_forecasts["avg"][1],
                    mode="lines+markers",  # Added markers
                    name="Points Forecast (Most Likely)",
                    line=dict(
                        color=COLOR_PALETTE["points"], dash="dash", width=3
                    ),  # Increased width
                    marker=dict(
                        size=8,
                        symbol="diamond",
                        color=COLOR_PALETTE["points"],
                        line=dict(color="white", width=1),
                    ),
                    hovertemplate=format_hover_template(
                        title="Points Forecast",
                        fields={
                            "Date": "%{x|%Y-%m-%d}",
                            "Points": "%{y:.1f}",
                            "Type": "Most Likely",
                        },
                    ),
                    hoverlabel=create_hoverlabel_config("info"),
                    visible=True,
                ),
                "secondary_y": True,
            }
        )

        # Use gold color for optimistic points forecast (matching info card description)
        traces.append(
            {
                "data": go.Scatter(
                    x=points_forecasts["opt"][0],
                    y=points_forecasts["opt"][1],
                    mode="lines+markers",  # Added markers
                    name="Points Forecast (Optimistic)",
                    line=dict(
                        color="rgb(184, 134, 11)", dash="dot", width=2.5
                    ),  # Gold color for optimistic points
                    marker=dict(
                        size=7,
                        symbol="triangle-up",
                        color="rgb(184, 134, 11)",  # Gold color for marker
                        line=dict(color="white", width=1),
                    ),
                    visible=True,
                    hovertemplate=format_hover_template(
                        title="Points Forecast",
                        fields={
                            "Date": "%{x|%Y-%m-%d}",
                            "Points": "%{y:.1f}",
                            "Type": "Optimistic",
                        },
                    ),
                    hoverlabel=create_hoverlabel_config("success"),
                ),
                "secondary_y": True,
            }
        )

        # Use brown color for pessimistic points forecast (matching info card description)
        traces.append(
            {
                "data": go.Scatter(
                    x=points_forecasts["pes"][0],
                    y=points_forecasts["pes"][1],
                    mode="lines+markers",  # Added markers
                    name="Points Forecast (Pessimistic)",
                    line=dict(
                        color="rgb(165, 42, 42)", dash="dot", width=2.5
                    ),  # Brown color for pessimistic points
                    marker=dict(
                        size=7,
                        symbol="triangle-down",
                        color="rgb(165, 42, 42)",  # Brown color for marker
                        line=dict(color="white", width=1),
                    ),
                    visible=True,
                    hovertemplate=format_hover_template(
                        title="Points Forecast",
                        fields={
                            "Date": "%{x|%Y-%m-%d}",
                            "Points": "%{y:.1f}",
                            "Type": "Pessimistic",
                        },
                    ),
                    hoverlabel=create_hoverlabel_config("warning"),
                ),
                "secondary_y": True,
            }
        )

    return traces


def configure_axes(fig, forecast_data):
    """
    Configure the axis scales and styling for the figure.

    Args:
        fig: Plotly figure object
        forecast_data: Dictionary of forecast data

    Returns:
        Updated figure with configured axes
    """
    max_items = forecast_data["max_items"]
    max_points = forecast_data["max_points"]

    # Calculate scale factor to align visually
    scale_factor = max_points / max_items if max_items > 0 else 1

    # Set y-axis ranges to maintain alignment
    items_range = [0, max_items * 1.1]
    points_range = [0, max_items * scale_factor * 1.1]

    # Configure x-axis
    fig.update_xaxes(
        title="",  # No axis title
        tickmode="auto",
        nticks=20,
        gridcolor="rgba(200, 200, 200, 0.2)",
        automargin=True,
        tickangle=-45,  # Consistent 45° rotation
    )

    # Configure primary y-axis (items)
    fig.update_yaxes(
        title="",  # No axis title
        range=items_range,
        gridcolor=COLOR_PALETTE["items_grid"],
        zeroline=True,
        zerolinecolor="black",
        secondary_y=False,
    )

    # Configure secondary y-axis (points)
    fig.update_yaxes(
        title="",  # No axis title
        range=points_range,
        gridcolor=COLOR_PALETTE["points_grid"],
        zeroline=True,
        zerolinecolor="black",
        secondary_y=True,
    )

    return fig


def apply_layout_settings(fig):
    """Apply common layout settings to the forecast plot."""
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        hovermode="x unified",  # Changed from "closest" to "x unified" for vertical guideline
        margin=dict(l=60, r=60, t=80, b=50),
        height=700,
        template="plotly_white",
    )
    return fig


def add_metrics_annotations(fig, metrics_data, data_points_count=None):
    """
    Add metrics as annotations below the x-axis of the plot.

    Organized for responsive display on various screen sizes with more consistent spacing.

    Args:
        fig: Plotly figure object
        metrics_data: Dictionary with metrics to display
        data_points_count: Number of data points used for velocity calculations (for label display)

    Returns:
        Updated figure with metrics annotations
    """
    # Ensure metrics_data is a dictionary
    if metrics_data is None:
        metrics_data = {}  # Define positions and styles for metrics display
    base_y_position = (
        -0.20
    )  # Y position for the top row of metrics (moved down from -0.15)
    font_color = "rgba(50, 50, 50, 0.9)"  # Default text color for metrics
    value_font_size = 12  # Font size for metric values

    # Define styles for metrics display
    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=0,
        y0=base_y_position - 0.15,  # Lower position for background bottom
        x1=1,
        y1=base_y_position + 0.05,  # Increased top position to fit all metrics
        fillcolor="rgba(245, 245, 245, 0.8)",
        line=dict(color="rgba(200, 200, 200, 0.5)", width=1),
    )

    # Detect if points data is meaningful
    # Points data is considered available if:
    # 1. There's any historical completed points data (sum > 0), OR
    # 2. There's meaningful weekly points data (average > 0), OR
    # 3. There's both scope and remaining points configured and they're different
    points_data_available = (
        metrics_data.get("completed_points", 0) > 0
        or metrics_data.get("avg_weekly_points", 0) > 0
        or (
            metrics_data.get("total_scope_points", 0) > 0
            and metrics_data.get("total_points", 0) > 0
        )
    )

    # Additional check: if total_scope_points == total_points, it suggests no historical data
    if (
        metrics_data.get("total_scope_points", 0) == metrics_data.get("total_points", 0)
        and metrics_data.get("completed_points", 0) == 0
    ):
        points_data_available = False

    # Using a layout that can reflow to 3x4 grid on small screens
    metrics = [
        # Row 1 - Scope metrics
        {
            "label": "Scope Items",
            "value": metrics_data.get("total_scope_items", 0),
            "format": "{:,.0f}",
        },
        {
            "label": "Scope Points",
            "value": metrics_data.get("total_scope_points", 0)
            if points_data_available
            else None,
            "format": "{:,.0f}" if points_data_available else "n/a",
        },
        {"label": "Deadline", "value": metrics_data["deadline"], "format": "{}"},
        # Row 2 - Completed metrics
        {
            "label": "Completed Items",
            "value": metrics_data.get("completed_items", 0),
            "format": "{:,.0f} ({:.1f}%)",
            "extra_value": metrics_data.get("items_percent_complete", 0),
        },
        {
            "label": "Completed Points",
            "value": metrics_data.get("completed_points", 0)
            if points_data_available
            else None,
            "format": "{:,.0f} ({:.1f}%)" if points_data_available else "n/a",
            "extra_value": metrics_data.get("points_percent_complete", 0)
            if points_data_available
            else None,
        },
        {
            "label": "Deadline in",
            "value": metrics_data["days_to_deadline"],
            "format": "{:,} days",
        },
        # Row 3 - Remaining items and points
        {
            "label": "Remaining Items",
            "value": metrics_data["total_items"],
            "format": "{:,.0f}",
        },
        {
            "label": "Remaining Points",
            "value": metrics_data["total_points"] if points_data_available else None,
            "format": "{:,.0f}" if points_data_available else "n/a",
        },
        {
            "label": "Est. Days (Items)",
            "value": metrics_data["pert_time_items"],
            "format": "{:.1f} days",
        },
        # Row 4 - Averages and other estimates
        {
            "label": f"Avg Weekly Items ({data_points_count or 'All'}W)",
            "value": metrics_data["avg_weekly_items"],
            "format": "{:.2f}",  # Changed from {:.1f} to show 2 decimal places
        },
        {
            "label": f"Avg Weekly Points ({data_points_count or 'All'}W)",
            "value": metrics_data["avg_weekly_points"]
            if points_data_available
            else None,
            "format": "{:.2f}"
            if points_data_available
            else "n/a",  # Changed from {:.1f} to show 2 decimal places
        },
        {
            "label": "Est. Days (Points)",
            "value": metrics_data["pert_time_points"]
            if points_data_available
            else None,
            "format": "{:.1f} days" if points_data_available else "n/a",
        },
    ]

    # Responsive grid layout
    # Use division to calculate positions rather than fixed values
    columns = 3  # Number of columns in the grid

    for idx, metric in enumerate(metrics):
        # Calculate row and column position
        row = idx // columns
        col = idx % columns

        # Calculate x and y positions based on grid
        x_pos = 0.02 + (col * (1.0 - 0.04) / columns)  # 2% margin on sides
        y_offset = -0.05 * row
        y_pos = base_y_position + y_offset

        # Format the label and value
        if metric["value"] is None:
            # Handle n/a case
            formatted_value = metric["format"]
        elif "extra_value" in metric and metric["extra_value"] is not None:
            formatted_value = metric["format"].format(
                metric["value"], metric["extra_value"]
            )
        else:
            formatted_value = metric["format"].format(metric["value"])

        # Color for estimated days
        text_color = font_color
        if "Est. Days" in metric["label"]:
            if "Items" in metric["label"]:
                if metrics_data["pert_time_items"] > metrics_data["days_to_deadline"]:
                    text_color = "red"
                else:
                    text_color = "green"
            elif "Points" in metric["label"] and metric["value"] is not None:
                if metrics_data["pert_time_points"] > metrics_data["days_to_deadline"]:
                    text_color = "red"
                else:
                    text_color = "green"

        # Add the metric to the figure
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=x_pos,
            y=y_pos,
            text=f"<b>{metric['label']}:</b> {formatted_value}",
            showarrow=False,
            font=dict(
                size=value_font_size, color=text_color, family="Arial, sans-serif"
            ),
            align="left",
            xanchor="left",
        )  # Update the figure margin to accommodate the metrics area
    # Increased for better display on small screens and to prevent overlay with x-axis
    fig.update_layout(
        margin=dict(b=220)  # Increased bottom margin for better spacing (was 200)
    )

    return fig


def create_forecast_plot(
    df,
    total_items,
    total_points,
    pert_factor,
    deadline_str,
    milestone_str=None,
    data_points_count=None,
    show_forecast=True,
    forecast_visibility=True,
    hover_mode="x unified",
    show_points=True,
):
    """
    Create the complete forecast plot with all components.

    Args:
        df: DataFrame with historical data
        total_items: Total number of items to complete
        total_points: Total number of points to complete
        pert_factor: PERT factor for calculations
        deadline_str: Deadline date as string (YYYY-MM-DD)
        milestone_str: Milestone date as string (YYYY-MM-DD), optional
        data_points_count: Number of most recent data points to use (defaults to all)
        show_forecast: Whether to show forecast traces
        forecast_visibility: Visibility mode for forecast traces ("legendonly", True, False)
        hover_mode: Hover mode for the plot ("x unified", "closest", etc.)
        show_points: Whether points tracking is enabled (default: True)
        viewport_size: Target viewport size ("mobile", "tablet", "desktop")

    Returns:
        Tuple of (figure, pert_data_dict) where pert_data_dict contains all PERT forecast information
    """
    try:
        # Validate inputs with stronger type checking
        if df is None:
            df = pd.DataFrame()
        elif not isinstance(df, pd.DataFrame):
            if isinstance(df, (list, dict)):
                # Convert list of dictionaries or dictionary to DataFrame
                try:
                    df = pd.DataFrame(df)
                except Exception:
                    df = pd.DataFrame()
            else:
                df = pd.DataFrame()

        # Ensure numeric types for calculations with explicit conversion
        total_items = _safe_numeric_convert(total_items, default=0.0)
        total_points = _safe_numeric_convert(total_points, default=0.0)
        pert_factor = int(_safe_numeric_convert(pert_factor, default=3.0))

        # Parse deadline and milestone dates
        deadline, milestone = _parse_deadline_milestone(deadline_str, milestone_str)

        # Prepare all data needed for the visualization
        forecast_data = prepare_visualization_data(
            df,
            total_items,
            total_points,
            pert_factor,
            data_points_count,
            is_burnup=False,
            scope_items=None,
            scope_points=None,
            show_points=show_points,
        )

        # Create subplot with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add all traces to the figure
        traces = create_plot_traces(
            forecast_data, show_forecast, forecast_visibility, show_points
        )
        for trace in traces:
            # Only add forecast traces if show_forecast is True
            is_forecast = (
                "Forecast" in trace["data"].name
                if hasattr(trace["data"], "name")
                else False
            )

            if not is_forecast or (is_forecast and show_forecast):
                # Set visibility for all forecast traces based on forecast_visibility parameter
                if is_forecast:
                    trace["data"].visible = forecast_visibility

                fig.add_trace(trace["data"], secondary_y=trace["secondary_y"])

        # Add deadline marker and configure axes
        fig = add_deadline_marker(fig, deadline, milestone)
        fig = configure_axes(fig, forecast_data)

        # Apply layout settings with the specified hover_mode
        fig.update_layout(
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5
            ),
            hovermode=hover_mode,
            margin=dict(l=60, r=60, t=80, b=50),
            height=700,
            template="plotly_white",
        )

        # Calculate days to deadline for metrics
        current_date = datetime.now()
        # Handle None or NaT deadline safely
        if deadline is None or pd.isna(deadline):
            days_to_deadline = 0
        else:
            days_to_deadline = max(0, (deadline - pd.Timestamp(current_date)).days)

        # Calculate weekly metrics
        avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
            _get_weekly_metrics(df, data_points_count)
        )

        # Calculate enhanced formatted strings for PERT estimates
        pert_time_items = forecast_data.get("pert_time_items", 0.0)
        pert_time_points = forecast_data.get("pert_time_points", 0.0)

        # Ensure valid numbers for PERT times
        pert_time_items = _safe_numeric_convert(pert_time_items, default=0.0)
        pert_time_points = _safe_numeric_convert(pert_time_points, default=0.0)

        # Get formatted completion date strings
        items_completion_enhanced, points_completion_enhanced = (
            _calculate_forecast_completion_dates(pert_time_items, pert_time_points)
        )

        # Prepare metrics data for display
        try:
            metrics_data = _prepare_metrics_data(
                total_items,
                total_points,
                deadline,
                pert_time_items,
                pert_time_points,
                data_points_count,
                df,
                items_completion_enhanced,
                points_completion_enhanced,
                avg_weekly_items,  # Removed round() to preserve decimal places
                avg_weekly_points,  # Removed round() to preserve decimal places
                med_weekly_items,  # Removed round() to preserve decimal places
                med_weekly_points,  # Removed round() to preserve decimal places
            )

            # Ensure metrics_data is never None
            if metrics_data is None:
                metrics_data = {}  # Default to empty dict if None

            # Add metrics annotations
            fig = add_metrics_annotations(fig, metrics_data, data_points_count)
        except Exception as metrics_error:
            # Log the error but continue without metrics
            logger = logging.getLogger("burndown_chart")
            logger.error(
                f"[Visualization] Error preparing metrics data: {str(metrics_error)}"
            )

            # Create minimal metrics data with default values
            metrics_data = {
                "total_items": total_items,
                "total_points": total_points,
                "deadline": deadline.strftime("%Y-%m-%d")
                if deadline is not None
                and hasattr(deadline, "strftime")
                and not pd.isna(deadline)
                else "Unknown",
                "days_to_deadline": days_to_deadline,
                "avg_weekly_items": float(avg_weekly_items),
                "avg_weekly_points": float(avg_weekly_points),
                "med_weekly_items": float(med_weekly_items),
                "med_weekly_points": float(med_weekly_points),
            }

            # Try to add metrics with the minimal data
            try:
                fig = add_metrics_annotations(fig, metrics_data, data_points_count)
            except Exception:
                # If even this fails, just continue without metrics
                pass

        # Calculate velocity_cv and schedule_variance_days for health score
        velocity_cv = forecast_data.get("velocity_cv", 0)
        schedule_variance_days = (
            abs(pert_time_items - days_to_deadline)
            if pert_time_items > 0 and days_to_deadline > 0
            else 0
        )

        # Create a complete PERT data dictionary with explicit type conversion
        pert_data = {
            "pert_time_items": float(pert_time_items),
            "pert_time_points": float(pert_time_points),
            "items_completion_enhanced": str(items_completion_enhanced),
            "points_completion_enhanced": str(points_completion_enhanced),
            "days_to_deadline": int(days_to_deadline),
            "avg_weekly_items": float(
                avg_weekly_items
            ),  # Ensure this is a float without rounding
            "avg_weekly_points": float(
                avg_weekly_points
            ),  # Ensure this is a float without rounding
            "med_weekly_items": float(med_weekly_items),  # Also keep this as float
            "med_weekly_points": float(med_weekly_points),  # Also keep this as float
            "forecast_timestamp": datetime.now().isoformat(),
            "velocity_cv": float(velocity_cv),
            "schedule_variance_days": float(schedule_variance_days),
        }

        return fig, pert_data

    except Exception as e:
        return _handle_forecast_error(e)


def _safe_numeric_convert(value, default=0.0):
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


def _parse_deadline_milestone(deadline_str, milestone_str=None):
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

    # Parse milestone date if provided
    milestone = None
    if milestone_str:
        try:
            milestone = pd.to_datetime(milestone_str, format="mixed", errors="coerce")
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


def _get_weekly_metrics(df, data_points_count=None):
    """
    Calculate weekly metrics from the data frame.

    Args:
        df: DataFrame with historical data
        data_points_count: Number of most recent data points to use (defaults to all)

    Returns:
        Tuple of (avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points)
    """
    avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
        0.0,
        0.0,
        0.0,
        0.0,
    )

    if not df.empty:
        # Get all four values from calculate_weekly_averages with data_points_count
        results = calculate_weekly_averages(
            df.to_dict("records"), data_points_count=data_points_count
        )
        if isinstance(results, (list, tuple)) and len(results) >= 4:
            avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
                results  # Ensure all are valid float values with preserved decimal places
            )
        avg_weekly_items = round(
            float(avg_weekly_items if avg_weekly_items is not None else 0.0), 2
        )
        avg_weekly_points = round(
            float(avg_weekly_points if avg_weekly_points is not None else 0.0), 2
        )
        med_weekly_items = round(
            float(med_weekly_items if med_weekly_items is not None else 0.0), 2
        )
        med_weekly_points = round(
            float(med_weekly_points if med_weekly_points is not None else 0.0), 2
        )

    return avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points


def _handle_forecast_error(e):
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
    logger.error(f"[Visualization] Error in create_forecast_plot: {str(e)}")

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
        "avg_weekly_items": 0.0,  # Ensure consistent with non-error case
        "avg_weekly_points": 0.0,  # Ensure consistent with non-error case
        "med_weekly_items": 0.0,  # Keep as float
        "med_weekly_points": 0.0,  # Keep as float
        "error": str(e),
        "forecast_timestamp": datetime.now().isoformat(),
    }

    return fig, safe_pert_data


def create_weekly_items_chart(
    statistics_data,
    date_range_weeks=12,
    pert_factor=3,
    include_forecast=True,
    data_points_count=None,
):
    """
    Create a bar chart showing weekly completed items with optional forecast for the next week.

    Args:
        statistics_data: List of dictionaries containing statistics data
        date_range_weeks: Number of weeks to display (default: 12 weeks)
        pert_factor: PERT factor for calculations (for forecast)
        include_forecast: Whether to include forecast data (default: True)
        data_points_count: Number of data points to use for calculations (default: None, uses all data)
        viewport_size: Target viewport size ("mobile", "tablet", "desktop")

    Returns:
        Plotly figure object with the weekly items chart
    """
    # CRITICAL FIX: Apply data points filtering by DATE RANGE, not row count
    # data_points_count represents WEEKS, not rows. With sparse data,
    # filtering by row count gives incorrect results.
    filtered_statistics_data = statistics_data
    if data_points_count is not None and data_points_count > 0:
        if isinstance(statistics_data, list):
            # Convert to DataFrame for date-based filtering
            df_temp = pd.DataFrame(statistics_data)
            if not df_temp.empty and "date" in df_temp.columns:
                df_temp["date"] = pd.to_datetime(
                    df_temp["date"], format="mixed", errors="coerce"
                )
                df_temp = df_temp.dropna(subset=["date"])
                df_temp = df_temp.sort_values("date", ascending=True)

                latest_date = df_temp["date"].max()
                cutoff_date = latest_date - timedelta(weeks=data_points_count)
                df_temp = df_temp[df_temp["date"] >= cutoff_date]

                filtered_statistics_data = df_temp.to_dict("records")
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
                filtered_statistics_data = df_temp[df_temp["date"] >= cutoff_date]

    # Create DataFrame from filtered statistics data
    df = pd.DataFrame(filtered_statistics_data).copy()
    if df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Weekly Completed Items (No Data Available)",
            xaxis_title="Week",
            yaxis_title="Items Completed",
        )
        return fig

    # Convert date to datetime and ensure proper format
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    # Always filter by date range for better visualization
    # Ensure date_range_weeks is not None and is a positive number
    weeks = 12  # Default to 12 weeks
    if (
        date_range_weeks is not None
        and isinstance(date_range_weeks, (int, float))
        and date_range_weeks > 0
    ):
        weeks = int(date_range_weeks)

    latest_date = df["date"].max()
    start_date = latest_date - timedelta(weeks=weeks)
    df = df[df["date"] >= start_date]

    # Add week and year columns for grouping
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    # Use vectorized string formatting to avoid DataFrame return issues
    df["year_week"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(items=("completed_items", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Fill in missing weeks with zeros to show complete time range
    # Use date range from aggregated data to respect data_points_count filtering
    if not weekly_df.empty:
        weekly_start = weekly_df["start_date"].min()
        weekly_end = weekly_df["start_date"].max()
        weekly_df = _fill_missing_weeks(weekly_df, weekly_start, weekly_end, ["items"])
    else:
        weekly_df = _fill_missing_weeks(weekly_df, start_date, latest_date, ["items"])

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Ensure start_date is datetime for type safety
    weekly_df["start_date"] = pd.to_datetime(
        weekly_df["start_date"], format="mixed", errors="coerce"
    )

    # Format date for display
    weekly_df["week_label"] = weekly_df["start_date"].dt.strftime("%b %d")  # type: ignore[attr-defined]

    # Calculate weighted moving average (last 4 weeks)
    # More weight given to recent weeks using exponential weights
    if len(weekly_df) >= 4:
        # Create a copy of items column for calculation
        values = weekly_df["items"].values
        weighted_avg = []

        for i in range(len(weekly_df)):
            if i < 3:  # First 3 weeks don't have enough prior data
                weighted_avg.append(None)
            else:
                # Get last 4 weeks of data
                window = values[i - 3 : i + 1]
                # Apply exponential weights (more weight to recent weeks)
                weights = [0.1, 0.2, 0.3, 0.4]  # Weights sum to 1.0
                w_avg = sum(w * v for w, v in zip(weights, window))
                weighted_avg.append(w_avg)

        weekly_df["weighted_avg"] = weighted_avg

    # Create the figure
    fig = go.Figure()

    # Add bar chart
    fig.add_trace(
        go.Bar(
            x=weekly_df["week_label"],
            y=weekly_df["items"],
            marker_color=COLOR_PALETTE["items"],
            name="Completed Items",
            text=weekly_df["items"],
            textposition="outside",
            customdata=weekly_df["week_label"],
            hovertemplate=format_hover_template(
                title="Weekly Items",
                fields={
                    "Week of": "%{customdata}",
                    "Items": "%{y}",
                },
            ),
            hoverlabel=create_hoverlabel_config("default"),
        )
    )

    # Add weighted moving average line if we have enough data
    if len(weekly_df) >= 4 and "weighted_avg" in weekly_df.columns:
        # Filter out None values for display
        weighted_df = weekly_df.dropna(subset=["weighted_avg"])

        # Create a separate trace for the weighted average line
        fig.add_trace(
            go.Scatter(
                x=weighted_df["week_label"],
                y=weighted_df["weighted_avg"],
                mode="lines+markers",
                name="Weighted 4-Week Average",
                line=dict(
                    color="#0047AB",  # Cobalt blue - darker shade of blue
                    width=3,
                    dash="solid",
                ),
                marker=dict(size=6, opacity=1),
                customdata=weighted_df["week_label"],
                hovertemplate=format_hover_template(
                    title="Weighted Moving Average",
                    fields={
                        "Week of": "%{customdata}",
                        "Weighted Avg": "%{y:.1f} items",
                        "Method": "Exponential weights (0.1, 0.2, 0.3, 0.4)",
                        "Purpose": "Recent weeks have 4x more influence",
                    },
                ),
                hoverlabel=create_hoverlabel_config("info"),
                hoverinfo="all",  # Ensure hover info shows
            )
        )

    # Add forecast data if requested
    if include_forecast and len(weekly_df) > 0:
        # Generate forecast data using filtered statistics data
        forecast_data = generate_weekly_forecast(
            filtered_statistics_data, pert_factor, data_points_count=data_points_count
        )

        if forecast_data["items"]["dates"]:
            # Get items forecast for next week with confidence intervals
            most_likely = forecast_data["items"]["most_likely"]
            optimistic = forecast_data["items"]["optimistic"]
            pessimistic = forecast_data["items"]["pessimistic"]

            # Calculate confidence interval bounds (25% of difference)
            upper_bound = [
                ml + 0.25 * (opt - ml) for ml, opt in zip(most_likely, optimistic)
            ]
            lower_bound = [
                ml - 0.25 * (ml - pes) for ml, pes in zip(most_likely, pessimistic)
            ]

            # Single next week forecast with confidence interval
            fig.add_trace(
                go.Bar(
                    x=forecast_data["items"]["dates"],
                    y=most_likely,
                    marker_color=COLOR_PALETTE["items"],
                    marker_pattern_shape="x",  # Add pattern to distinguish forecast
                    opacity=0.7,
                    name="Next Week Forecast",
                    text=[round(val, 1) for val in most_likely],
                    textposition="outside",
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=[u - ml for u, ml in zip(upper_bound, most_likely)],
                        arrayminus=[
                            ml - lb for ml, lb in zip(most_likely, lower_bound)
                        ],
                        color="rgba(0, 0, 0, 0.3)",
                    ),
                    hovertemplate=format_hover_template(
                        title="Next Week Items Forecast",
                        fields={
                            "Week": "%{x}",
                            "Predicted Items": "%{y:.1f}",
                            "Confidence Range": "±25% of PERT variance",
                            "Method": "PERT 3-point estimation",
                        },
                    ),
                    hoverlabel=create_hoverlabel_config("info"),
                )
            )

            # Add vertical line between historical and forecast data
            fig.add_vline(
                x=len(weekly_df["week_label"])
                - 0.5,  # Position between last historical and first forecast
                line_dash="dash",
                line_color="rgba(0, 0, 0, 0.5)",
                annotation_text="Forecast starts",
                annotation_position="top",
            )

    # Update layout with grid lines and styling
    fig.update_layout(
        title=None,  # Remove chart title
        xaxis_title="Week",
        yaxis_title="Items Completed",
        hovermode="x unified",
        hoverlabel=dict(
            font_size=14,
        ),
        yaxis=dict(
            gridcolor="rgba(200, 200, 200, 0.2)",
            zeroline=True,
            zerolinecolor="rgba(0, 0, 0, 0.2)",
        ),
        xaxis=dict(
            tickangle=45,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        margin=dict(
            b=70  # Reduced from 130 to 70
        ),
    )

    return fig


def create_weekly_points_chart(
    statistics_data,
    date_range_weeks=12,
    pert_factor=3,
    include_forecast=True,
    data_points_count=None,
):
    """
    Create a bar chart showing weekly completed points with a weighted moving average line and optional forecast for next week.

    Args:
        statistics_data: List of dictionaries containing statistics data
        date_range_weeks: Number of weeks to display (default: 12 weeks)
        pert_factor: PERT factor for calculations (for forecast)
        include_forecast: Whether to include forecast data (default: True)
        data_points_count: Number of data points to use for calculations (default: None, uses all data)
        viewport_size: Target viewport size ("mobile", "tablet", "desktop")

    Returns:
        Plotly figure object with the weekly points chart
    """
    # CRITICAL FIX: Apply data points filtering by DATE RANGE, not row count
    # data_points_count represents WEEKS, not rows. With sparse data,
    # filtering by row count gives incorrect results.
    filtered_statistics_data = statistics_data
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
                df_temp = df_temp[df_temp["date"] >= cutoff_date]

                filtered_statistics_data = df_temp.to_dict("records")
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
                filtered_statistics_data = df_temp[df_temp["date"] >= cutoff_date]

    # Create DataFrame from filtered statistics data
    df = pd.DataFrame(filtered_statistics_data).copy()
    if df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Weekly Completed Points (No Data Available)",
            xaxis_title="Week",
            yaxis_title="Points Completed",
        )
        return fig

    # Convert date to datetime and ensure proper format
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    # Always filter by date range for better visualization
    # Ensure date_range_weeks is not None and is a positive number
    weeks = 12  # Default to 12 weeks
    if (
        date_range_weeks is not None
        and isinstance(date_range_weeks, (int, float))
        and date_range_weeks > 0
    ):
        weeks = int(date_range_weeks)

    latest_date = df["date"].max()
    start_date = latest_date - timedelta(weeks=weeks)
    df = df[df["date"] >= start_date]

    # Add week and year columns for grouping
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    # Use vectorized string formatting to avoid DataFrame return issues
    df["year_week"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(points=("completed_points", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Fill in missing weeks with zeros to show complete time range
    # Use date range from aggregated data to respect data_points_count filtering
    if not weekly_df.empty:
        weekly_start = weekly_df["start_date"].min()
        weekly_end = weekly_df["start_date"].max()
        weekly_df = _fill_missing_weeks(weekly_df, weekly_start, weekly_end, ["points"])
    else:
        weekly_df = _fill_missing_weeks(weekly_df, start_date, latest_date, ["points"])

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Ensure start_date is datetime for type safety
    weekly_df["start_date"] = pd.to_datetime(
        weekly_df["start_date"], format="mixed", errors="coerce"
    )

    # Format date for display
    weekly_df["week_label"] = weekly_df["start_date"].dt.strftime("%b %d")  # type: ignore[attr-defined]

    # Calculate weighted moving average (last 4 weeks)
    # More weight given to recent weeks using exponential weights
    if len(weekly_df) >= 4:
        # Create a copy of points column for calculation
        values = weekly_df["points"].values
        weighted_avg = []

        for i in range(len(weekly_df)):
            if i < 3:  # First 3 weeks don't have enough prior data
                weighted_avg.append(None)
            else:
                # Get last 4 weeks of data
                window = values[i - 3 : i + 1]
                # Apply exponential weights (more weight to recent weeks)
                weights = [0.1, 0.2, 0.3, 0.4]  # Weights sum to 1.0
                w_avg = sum(w * v for w, v in zip(weights, window))
                weighted_avg.append(w_avg)

        weekly_df["weighted_avg"] = weighted_avg

    # Create the figure
    fig = go.Figure()

    # Add bar chart
    fig.add_trace(
        go.Bar(
            x=weekly_df["week_label"],
            y=weekly_df["points"],
            marker_color=COLOR_PALETTE["points"],
            name="Completed Points",
            text=weekly_df["points"],
            textposition="outside",
            customdata=weekly_df["week_label"],
            hovertemplate=format_hover_template(
                title="Weekly Points",
                fields={
                    "Week of": "%{customdata}",
                    "Points": "%{y}",
                },
            ),
            hoverlabel=create_hoverlabel_config("default"),
        )
    )

    # Add weighted moving average line if we have enough data
    if len(weekly_df) >= 4 and "weighted_avg" in weekly_df.columns:
        # Filter out None values for display
        weighted_df = weekly_df.dropna(subset=["weighted_avg"])

        # Create a separate trace for the weighted average line
        fig.add_trace(
            go.Scatter(
                x=weighted_df["week_label"],
                y=weighted_df["weighted_avg"],
                mode="lines+markers",
                name="Weighted 4-Week Average",
                line=dict(
                    color="#FF6347",  # Tomato color
                    width=3,
                    dash="solid",
                ),
                marker=dict(size=6, opacity=1),
                customdata=weighted_df["week_label"],
                hovertemplate=format_hover_template(
                    title="Weighted Moving Average",
                    fields={
                        "Week of": "%{customdata}",
                        "Weighted Avg": "%{y:.1f} points",
                        "Method": "Exponential weights (0.1, 0.2, 0.3, 0.4)",
                        "Purpose": "Recent weeks have 4x more influence",
                    },
                ),
                hoverlabel=create_hoverlabel_config("info"),
                hoverinfo="all",  # Ensure hover info shows
            )
        )

    # Add forecast data if requested
    if include_forecast and len(weekly_df) > 0:
        # Generate forecast data using filtered statistics data
        forecast_data = generate_weekly_forecast(
            filtered_statistics_data, pert_factor, data_points_count=data_points_count
        )

        if forecast_data["points"]["dates"]:
            # Get points forecast for next week
            most_likely = forecast_data["points"]["most_likely"]
            optimistic = forecast_data["points"]["optimistic"]
            pessimistic = forecast_data["points"]["pessimistic"]

            # Calculate confidence interval bounds (25% of difference)
            upper_bound = [
                ml + 0.25 * (opt - ml) for ml, opt in zip(most_likely, optimistic)
            ]
            lower_bound = [
                ml - 0.25 * (ml - pes) for ml, pes in zip(most_likely, pessimistic)
            ]

            # Single next week forecast with confidence interval
            fig.add_trace(
                go.Bar(
                    x=forecast_data["points"]["dates"],
                    y=most_likely,
                    marker_color=COLOR_PALETTE["points"],
                    marker_pattern_shape="x",  # Add pattern to distinguish forecast
                    opacity=0.7,
                    name="Next Week Forecast",
                    text=[round(val, 1) for val in most_likely],
                    textposition="outside",
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=[u - ml for u, ml in zip(upper_bound, most_likely)],
                        arrayminus=[
                            ml - lb for ml, lb in zip(most_likely, lower_bound)
                        ],
                        color="rgba(0, 0, 0, 0.3)",
                    ),
                    hovertemplate=format_hover_template(
                        title="Next Week Points Forecast",
                        fields={
                            "Week": "%{x}",
                            "Predicted Points": "%{y:.1f}",
                            "Confidence Range": "±25% of PERT variance",
                            "Method": "PERT 3-point estimation",
                        },
                    ),
                    hoverlabel=create_hoverlabel_config("info"),
                )
            )

            # Add vertical line between historical and forecast data
            fig.add_vline(
                x=len(weekly_df["week_label"])
                - 0.5,  # Position between last historical and first forecast
                line_dash="dash",
                line_color="rgba(0, 0, 0, 0.5)",
                annotation_text="Forecast starts",
                annotation_position="top",
            )

    # Update layout with grid lines and styling
    fig.update_layout(
        title=None,  # Remove chart title
        xaxis_title="Week",
        yaxis_title="Points Completed",
        hovermode="x unified",
        hoverlabel=dict(
            font_size=14,
        ),
        yaxis=dict(
            gridcolor="rgba(200, 200, 200, 0.2)",
            zeroline=True,
            zerolinecolor="rgba(0, 0, 0, 0.2)",
        ),
        xaxis=dict(
            tickangle=45,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        margin=dict(
            b=60  # Reduced from 130 to 60
        ),
    )

    return fig


def create_weekly_items_forecast_chart(
    statistics_data, pert_factor=3, date_range_weeks=12, data_points_count=None
):
    """
    Create a chart showing weekly completed items with a 4-week forecast.

    Args:
        statistics_data: List of dictionaries containing statistics data
        pert_factor: Number of data points to use for optimistic/pessimistic scenarios
        date_range_weeks: Number of weeks of historical data to display (default: 12 weeks)
        data_points_count: Number of data points to use for calculations (default: None, uses all data)

    Returns:
        Plotly figure object with the weekly items forecast chart
    """
    # CRITICAL FIX: Apply data points filtering by DATE RANGE, not row count
    # data_points_count represents WEEKS, not rows. With sparse data,
    # filtering by row count gives incorrect results.
    filtered_statistics_data = statistics_data
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
                df_temp = df_temp[df_temp["date"] >= cutoff_date]

                filtered_statistics_data = df_temp.to_dict("records")
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
                filtered_statistics_data = df_temp[df_temp["date"] >= cutoff_date]

    # Create DataFrame from filtered statistics data
    df = pd.DataFrame(filtered_statistics_data).copy()
    if df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Weekly Items Forecast (No Data Available)",
            xaxis_title="Week",
            yaxis_title="Items Completed",
        )
        return fig

    # Convert date to datetime and ensure proper format
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    # Always filter by date range for better visualization
    # Ensure date_range_weeks is not None and is a positive number
    weeks = 12  # Default to 12 weeks
    if (
        date_range_weeks is not None
        and isinstance(date_range_weeks, (int, float))
        and date_range_weeks > 0
    ):
        weeks = int(date_range_weeks)

    latest_date = df["date"].max()
    start_date = latest_date - timedelta(weeks=weeks)
    df = df[df["date"] >= start_date]

    # Add week and year columns for grouping
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    # Use vectorized string formatting to avoid DataFrame return issues
    df["year_week"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(items=("completed_items", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Fill in missing weeks with zeros to show complete time range
    # Use date range from aggregated data to respect data_points_count filtering
    if not weekly_df.empty:
        weekly_start = weekly_df["start_date"].min()
        weekly_end = weekly_df["start_date"].max()
        weekly_df = _fill_missing_weeks(weekly_df, weekly_start, weekly_end, ["items"])
    else:
        weekly_df = _fill_missing_weeks(weekly_df, start_date, latest_date, ["items"])

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Ensure start_date is datetime for type safety
    weekly_df["start_date"] = pd.to_datetime(
        weekly_df["start_date"], format="mixed", errors="coerce"
    )

    # Format date for display
    weekly_df["week_label"] = weekly_df["start_date"].dt.strftime("%b %d")  # type: ignore[attr-defined]

    # Generate forecast data using filtered statistics data
    forecast_data = generate_weekly_forecast(
        filtered_statistics_data, pert_factor, data_points_count=data_points_count
    )

    # Create the figure
    fig = go.Figure()

    # Add historical data as bar chart
    fig.add_trace(
        go.Bar(
            x=weekly_df["week_label"],
            y=weekly_df["items"],
            marker_color=COLOR_PALETTE["items"],
            name="Completed Items",
            text=weekly_df["items"],
            textposition="outside",
            customdata=weekly_df["week_label"],
            hovertemplate=format_hover_template(
                title="Weekly Items",
                fields={
                    "Week of": "%{customdata}",
                    "Items": "%{y}",
                },
            ),
            hoverlabel=create_hoverlabel_config("default"),
        )
    )

    # Add forecast data if available
    if forecast_data["items"]["dates"]:
        # Most likely forecast
        fig.add_trace(
            go.Bar(
                x=forecast_data["items"]["dates"],
                y=forecast_data["items"]["most_likely"],
                marker_color=COLOR_PALETTE["items"],
                marker_pattern_shape="x",  # Add pattern to distinguish forecast
                opacity=0.7,
                name="Most Likely Forecast",
                text=[round(val, 1) for val in forecast_data["items"]["most_likely"]],
                textposition="outside",
                hovertemplate=format_hover_template(
                    title="Items Forecast",
                    fields={"Week": "%{x}", "Items": "%{y:.1f}", "Type": "Most Likely"},
                ),
                hoverlabel=create_hoverlabel_config("info"),
            )
        )

        # Optimistic forecast
        fig.add_trace(
            go.Bar(
                x=forecast_data["items"]["dates"],
                y=forecast_data["items"]["optimistic"],
                marker_color=COLOR_PALETTE["optimistic"],
                marker_pattern_shape="x",  # Add pattern to distinguish forecast
                opacity=0.6,
                name="Optimistic Forecast",
                text=[round(val, 1) for val in forecast_data["items"]["optimistic"]],
                textposition="outside",
                hovertemplate=format_hover_template(
                    title="Items Forecast",
                    fields={"Week": "%{x}", "Items": "%{y:.1f}", "Type": "Optimistic"},
                ),
                hoverlabel=create_hoverlabel_config("success"),
            )
        )

        # Pessimistic forecast
        fig.add_trace(
            go.Bar(
                x=forecast_data["items"]["dates"],
                y=forecast_data["items"]["pessimistic"],
                marker_color=COLOR_PALETTE["pessimistic"],
                marker_pattern_shape="x",  # Add pattern to distinguish forecast
                opacity=0.6,
                name="Pessimistic Forecast",
                text=[round(val, 1) for val in forecast_data["items"]["pessimistic"]],
                textposition="outside",
                hovertemplate=format_hover_template(
                    title="Items Forecast",
                    fields={"Week": "%{x}", "Items": "%{y:.1f}", "Type": "Pessimistic"},
                ),
                hoverlabel=create_hoverlabel_config("warning"),
            )
        )

    # Add vertical line between historical and forecast data
    if weekly_df["week_label"].any() and forecast_data["items"]["dates"]:
        fig.add_vline(
            x=len(weekly_df["week_label"])
            - 0.5,  # Position between last historical and first forecast
            line_dash="dash",
            line_color="rgba(0, 0, 0, 0.5)",
            annotation_text="Forecast starts",
            annotation_position="top",
        )

    # Update layout with grid lines, styling, and forecast explanation
    fig.update_layout(
        title="Weekly Items Forecast (Next 4 Weeks)",
        xaxis_title="Week Starting",
        yaxis_title="Items Completed",
        hovermode="x unified",
        hoverlabel=dict(
            font_size=14,
        ),
        yaxis=dict(
            gridcolor="rgba(200, 200, 200, 0.2)",
            zeroline=True,
            zerolinecolor="rgba(0, 0, 0, 0.2)",
        ),
        xaxis=dict(
            tickangle=45,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        annotations=[
            dict(
                x=0.5,
                y=-0.25,  # Adjusted from -0.3 to -0.25
                xref="paper",
                yref="paper",
                text=(
                    f"<b>Forecast Methodology:</b> Based on PERT analysis using historical data.<br>"
                    f"<b>Most Likely:</b> {forecast_data['items'].get('most_likely_value', 0):.1f} items/week (historical average)<br>"
                    f"<b>Optimistic:</b> {forecast_data['items'].get('optimistic_value', 0):.1f} items/week<br>"
                    f"<b>Pessimistic:</b> {forecast_data['items'].get('pessimistic_value', 0):.1f} items/week"
                ),
                showarrow=False,
                font=dict(size=12),
                align="center",
                bordercolor="rgba(200, 200, 200, 0.5)",
                borderwidth=1,
                borderpad=8,
                bgcolor="rgba(250, 250, 250, 0.8)",
            )
        ],
        margin=dict(b=70),  # Reduced from 100 to 70
    )

    return fig


def create_weekly_points_forecast_chart(
    statistics_data, pert_factor=3, date_range_weeks=12, data_points_count=None
):
    """
    Create a chart showing weekly completed points with a 4-week forecast.

    Args:
        statistics_data: List of dictionaries containing statistics data
        pert_factor: Number of data points to use for optimistic/pessimistic scenarios
        date_range_weeks: Number of weeks of historical data to display (default: 12 weeks)
        data_points_count: Number of data points to use for calculations (default: None, uses all data)

    Returns:
        Plotly figure object with the weekly points forecast chart
    """
    # CRITICAL FIX: Apply data points filtering by DATE RANGE, not row count
    # data_points_count represents WEEKS, not rows. With sparse data,
    # filtering by row count gives incorrect results.
    filtered_statistics_data = statistics_data
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
                df_temp = df_temp[df_temp["date"] >= cutoff_date]

                filtered_statistics_data = df_temp.to_dict("records")
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
                filtered_statistics_data = df_temp[df_temp["date"] >= cutoff_date]

    # Create DataFrame from filtered statistics data
    df = pd.DataFrame(filtered_statistics_data).copy()
    if df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(
            title="Weekly Points Forecast (No Data Available)",
            xaxis_title="Week",
            yaxis_title="Points Completed",
        )
        return fig

    # Convert date to datetime and ensure proper format
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    # Always filter by date range for better visualization
    # Ensure date_range_weeks is not None and is a positive number
    weeks = 12  # Default to 12 weeks
    if (
        date_range_weeks is not None
        and isinstance(date_range_weeks, (int, float))
        and date_range_weeks > 0
    ):
        weeks = int(date_range_weeks)

    latest_date = df["date"].max()
    start_date = latest_date - timedelta(weeks=weeks)
    df = df[df["date"] >= start_date]

    # Add week and year columns for grouping
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.year
    # Use vectorized string formatting to avoid DataFrame return issues
    df["year_week"] = (
        df["year"].astype(str) + "-W" + df["week"].astype(str).str.zfill(2)
    )

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(points=("completed_points", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Fill in missing weeks with zeros to show complete time range
    # Use date range from aggregated data to respect data_points_count filtering
    if not weekly_df.empty:
        weekly_start = weekly_df["start_date"].min()
        weekly_end = weekly_df["start_date"].max()
        weekly_df = _fill_missing_weeks(weekly_df, weekly_start, weekly_end, ["points"])
    else:
        weekly_df = _fill_missing_weeks(weekly_df, start_date, latest_date, ["points"])

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Ensure start_date is datetime for type safety
    weekly_df["start_date"] = pd.to_datetime(
        weekly_df["start_date"], format="mixed", errors="coerce"
    )

    # Format date for display
    weekly_df["week_label"] = weekly_df["start_date"].dt.strftime("%b %d")  # type: ignore[attr-defined]

    # Calculate weighted moving average (last 4 weeks)
    if len(weekly_df) >= 4:
        values = weekly_df["points"].values
        weighted_avg = []

        for i in range(len(weekly_df)):
            if i < 3:  # First 3 weeks don't have enough prior data
                weighted_avg.append(None)
            else:
                # Get last 4 weeks of data
                window = values[i - 3 : i + 1]
                # Apply exponential weights (more weight to recent weeks)
                weights = [0.1, 0.2, 0.3, 0.4]  # Weights sum to 1.0
                w_avg = sum(w * v for w, v in zip(weights, window))
                weighted_avg.append(w_avg)

        weekly_df["weighted_avg"] = weighted_avg

    # Generate forecast data using filtered statistics data
    forecast_data = generate_weekly_forecast(
        filtered_statistics_data, pert_factor, data_points_count=data_points_count
    )

    # Create the figure
    fig = go.Figure()

    # Add historical data as bar chart
    fig.add_trace(
        go.Bar(
            x=weekly_df["week_label"],
            y=weekly_df["points"],
            marker_color=COLOR_PALETTE["points"],
            name="Completed Points",
            text=weekly_df["points"],
            textposition="outside",
            customdata=weekly_df["week_label"],
            hovertemplate=format_hover_template(
                title="Weekly Points",
                fields={
                    "Week of": "%{customdata}",
                    "Points": "%{y}",
                },
            ),
            hoverlabel=create_hoverlabel_config("default"),
        )
    )

    # Add weighted moving average line if we have enough historical data
    if len(weekly_df) >= 4 and "weighted_avg" in weekly_df.columns:
        # Filter out None values for display
        weighted_df = weekly_df.dropna(subset=["weighted_avg"])

        fig.add_trace(
            go.Scatter(
                x=weighted_df["week_label"],
                y=weighted_df["weighted_avg"],
                mode="lines+markers",
                name="Weighted 4-Week Average",
                line=dict(
                    color="#FF6347",  # Tomato color
                    width=3,
                    dash="solid",
                ),
                marker=dict(size=6, opacity=1),
                customdata=weighted_df[
                    "week_label"
                ],  # Add custom data for hover template
                hovertemplate=format_hover_template(
                    title="Weekly Average",
                    fields={
                        "Week of": "%{customdata}",
                        "Weighted Avg": "%{y:.1f}",
                    },
                ),
                hoverlabel=create_hoverlabel_config("info"),
                hoverinfo="all",  # Ensure hover info shows
            )
        )

    # Add forecast data if available
    if forecast_data["points"]["dates"]:
        # Create confidence interval for the most likely forecast
        most_likely = forecast_data["points"]["most_likely"]
        optimistic = forecast_data["points"]["optimistic"]
        pessimistic = forecast_data["points"]["pessimistic"]

        # Calculate upper and lower bounds for confidence interval (25% of difference)
        upper_bound = [
            ml + 0.25 * (opt - ml) for ml, opt in zip(most_likely, optimistic)
        ]
        lower_bound = [
            ml - 0.25 * (ml - pes) for ml, pes in zip(most_likely, pessimistic)
        ]

        # Most likely forecast with confidence interval
        fig.add_trace(
            go.Bar(
                x=forecast_data["points"]["dates"],
                y=most_likely,
                marker_color=COLOR_PALETTE["points"],
                marker_pattern_shape="x",  # Add pattern to distinguish forecast
                opacity=0.7,
                name="Most Likely Forecast",
                text=[round(val, 1) for val in most_likely],
                textposition="outside",
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=[u - ml for u, ml in zip(upper_bound, most_likely)],
                    arrayminus=[ml - lb for ml, lb in zip(most_likely, lower_bound)],
                    color="rgba(0, 0, 0, 0.3)",
                ),
                hovertemplate=format_hover_template(
                    title="Points Forecast",
                    fields={
                        "Week": "%{x}",
                        "Points": "%{y:.1f}",
                        "Range": "[%{error_y.arrayminus:.1f}, %{error_y.array:.1f}]",
                    },
                ),
                hoverlabel=create_hoverlabel_config("info"),
            )
        )

        # Optimistic forecast
        fig.add_trace(
            go.Bar(
                x=forecast_data["points"]["dates"],
                y=optimistic,
                marker_color=COLOR_PALETTE["optimistic"],
                marker_pattern_shape="x",  # Add pattern to distinguish forecast
                opacity=0.6,
                name="Optimistic Forecast",
                text=[round(val, 1) for val in optimistic],
                textposition="outside",
                hovertemplate=format_hover_template(
                    title="Points Forecast",
                    fields={"Week": "%{x}", "Points": "%{y:.1f}", "Type": "Optimistic"},
                ),
                hoverlabel=create_hoverlabel_config("success"),
            )
        )

        # Pessimistic forecast
        fig.add_trace(
            go.Bar(
                x=forecast_data["points"]["dates"],
                y=pessimistic,
                marker_color=COLOR_PALETTE["pessimistic"],
                marker_pattern_shape="x",  # Add pattern to distinguish forecast
                opacity=0.6,
                name="Pessimistic Forecast",
                text=[round(val, 1) for val in pessimistic],
                textposition="outside",
                hovertemplate=format_hover_template(
                    title="Points Forecast",
                    fields={
                        "Week": "%{x}",
                        "Points": "%{y:.1f}",
                        "Type": "Pessimistic",
                    },
                ),
                hoverlabel=create_hoverlabel_config("warning"),
            )
        )

    # Add vertical line between historical and forecast data
    if weekly_df["week_label"].any() and forecast_data["points"]["dates"]:
        fig.add_vline(
            x=len(weekly_df["week_label"])
            - 0.5,  # Position between last historical and first forecast
            line_dash="dash",
            line_color="rgba(0, 0, 0, 0.5)",
            annotation_text="Forecast starts",
            annotation_position="top",
        )

    # Update layout with grid lines, styling, and forecast explanation
    fig.update_layout(
        title="Weekly Points Forecast (Next 4 Weeks)",
        xaxis_title="Week Starting",
        yaxis_title="Points Completed",
        hovermode="x unified",
        hoverlabel=dict(
            font_size=14,
        ),
        yaxis=dict(
            gridcolor="rgba(200, 200, 200, 0.2)",
            zeroline=True,
            zerolinecolor="rgba(0, 0, 0, 0.2)",
        ),
        xaxis=dict(
            tickangle=45,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        annotations=[
            dict(
                x=0.5,
                y=-0.25,  # Adjusted from -0.3 to -0.25
                xref="paper",
                yref="paper",
                text=(
                    f"<b>Forecast Methodology:</b> Based on PERT analysis using historical data.<br>"
                    f"<b>Most Likely:</b> {forecast_data['points'].get('most_likely_value', 0):.1f} points/week (historical average)<br>"
                    f"<b>Optimistic:</b> {forecast_data['points'].get('optimistic_value', 0):.1f} points/week<br>"
                    f"<b>Pessimistic:</b> {forecast_data['points'].get('pessimistic_value', 0):.1f} points/week<br>"
                    f"<b>Weighted Average:</b> More weight given to recent data (40% for most recent week, 30%, 20%, 10% for earlier weeks)"
                ),
                showarrow=False,
                font=dict(size=12),
                align="center",
                bordercolor="rgba(200, 200, 200, 0.5)",
                borderwidth=1,
                borderpad=8,
                bgcolor="rgba(250, 250, 250, 0.8)",
            )
        ],
        margin=dict(b=70),  # Reduced from 120 to 70
    )

    return fig


def create_capacity_chart(capacity_data, forecast_data, settings):
    """
    Create a chart visualizing team capacity against forecasted work.

    Args:
        capacity_data (dict): Dictionary with capacity metrics
        forecast_data (dict): Dictionary with forecasted work
        settings (dict): Application settings

    Returns:
        plotly.graph_objects.Figure: Capacity chart
    """
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Extract dates and convert to datetime objects
    dates = [
        pd.to_datetime(date, format="mixed", errors="coerce")
        for date in forecast_data.get("dates", [])
    ]

    if not dates:
        # If no forecast data, return empty chart with message
        fig.add_annotation(
            text="No forecast data available.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        return fig

    # Calculate weekly capacity line (constant)
    team_capacity = capacity_data.get("weekly_capacity", 0)
    capacity_line = [team_capacity] * len(dates)

    # Extract forecasted work requirements
    forecasted_items = forecast_data.get("forecasted_items", [])
    forecasted_points = forecast_data.get("forecasted_points", [])

    # Calculate required hours based on hours per item/point
    hours_per_item = capacity_data.get("avg_hours_per_item", 0)
    hours_per_point = capacity_data.get("avg_hours_per_point", 0)

    items_hours = [items * hours_per_item for items in forecasted_items]
    points_hours = [points * hours_per_point for points in forecasted_points]

    # Create capacity line (constant team capacity)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=capacity_line,
            mode="lines",
            name="Team Capacity",
            line=dict(color="rgba(0, 200, 0, 0.8)", width=2, dash="dash"),
            hovertemplate=format_hover_template(
                title="Team Capacity",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Hours": "%{y:.1f}",
                },
            ),
            hoverlabel=create_hoverlabel_config("success"),
        ),
        secondary_y=False,
    )

    # Create items-based required capacity
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=items_hours,
            mode="lines",
            name="Required (Items)",
            line=dict(color=COLOR_PALETTE["items"], width=2),
            fill="tozeroy",
            hovertemplate=format_hover_template(
                title="Items Work Hours",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Hours": "%{y:.1f}",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        ),
        secondary_y=False,
    )

    # Create points-based required capacity
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=points_hours,
            mode="lines",
            name="Required (Points)",
            line=dict(color=COLOR_PALETTE["points"], width=2),
            fill="tozeroy",
            hovertemplate=format_hover_template(
                title="Points Work Hours",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Hours": "%{y:.1f}",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        ),
        secondary_y=False,
    )

    # Add utilization percentage on secondary y-axis
    max_utilization = (
        max(
            max(items_hours + [0.1]) / team_capacity if team_capacity else 1,
            max(points_hours + [0.1]) / team_capacity if team_capacity else 1,
            1,
        )
        * 100
    )

    # Utilization threshold lines
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[100] * len(dates),
            mode="lines",
            name="100% Utilization",
            line=dict(color="rgba(255, 165, 0, 0.8)", width=1.5, dash="dot"),
            hovertemplate=format_hover_template(
                title="Utilization Threshold",
                fields={
                    "Threshold": "100%",
                },
            ),
            hoverlabel=create_hoverlabel_config("warning"),
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[85] * len(dates),
            mode="lines",
            name="85% Target Utilization",
            line=dict(color="rgba(0, 128, 0, 0.6)", width=1.5, dash="dot"),
            hovertemplate=format_hover_template(
                title="Utilization Target",
                fields={
                    "Target": "85%",
                },
            ),
            hoverlabel=create_hoverlabel_config("success"),
        ),
        secondary_y=True,
    )

    # Calculate utilization percentages
    items_utilization = [
        (hours / team_capacity * 100) if team_capacity else 0 for hours in items_hours
    ]
    points_utilization = [
        (hours / team_capacity * 100) if team_capacity else 0 for hours in points_hours
    ]

    # Add utilization percentages traces
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=items_utilization,
            mode="lines",
            name="Items Utilization %",
            line=dict(color=COLOR_PALETTE["items"], width=1.5),
            visible=True,
            hovertemplate=format_hover_template(
                title="Items Utilization",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Utilization": "%{y:.1f}%",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=points_utilization,
            mode="lines",
            name="Points Utilization %",
            line=dict(color=COLOR_PALETTE["points"], width=1.5),
            visible=True,
            hovertemplate=format_hover_template(
                title="Points Utilization",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Utilization": "%{y:.1f}%",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        ),
        secondary_y=True,
    )

    # Customize axis labels
    fig.update_layout(
        title="Team Capacity vs. Forecasted Work",
        xaxis_title="Date",
        yaxis_title="Hours per Week",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        hovermode="x unified",
        margin=dict(l=60, r=60, t=50, b=50),
        hoverlabel=dict(font_size=14),
    )

    fig.update_yaxes(title_text="Hours per Week", secondary_y=False)

    fig.update_yaxes(
        title_text="Utilization (%)",
        secondary_y=True,
        range=[
            0,
            max(max_utilization * 1.1, 110),
        ],  # Set scale to maximum utilization + 10%
    )

    return fig


def add_deadline_marker(fig, deadline, milestone=None):
    """
    Add vertical lines marking the deadline and optional milestone on the plot.

    Args:
        fig: Plotly figure object
        deadline: Deadline date (pandas datetime or datetime object)
        milestone: Optional milestone date (pandas datetime or datetime object)

    Returns:
        Updated figure with deadline and milestone markers
    """
    # Early return if deadline is None or NaT
    if deadline is None or (isinstance(deadline, pd.Timestamp) and pd.isna(deadline)):
        return fig

    # Convert pandas Timestamp to a format compatible with Plotly
    if isinstance(deadline, pd.Timestamp):
        # Convert to Python datetime to prevent FutureWarning
        deadline_datetime = deadline.to_pydatetime()
    else:
        deadline_datetime = deadline

    # Create a vertical line shape that spans the entire y-axis
    # This approach doesn't depend on specific y-values but uses paper coordinates (0-1)
    # which represent the entire visible area
    fig.add_shape(
        type="line",
        x0=deadline_datetime,
        x1=deadline_datetime,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="#FF0000", width=2, dash="dash"),
        layer="above",
    )

    # Add deadline annotation manually
    fig.add_annotation(
        x=deadline_datetime,
        y=1.03,  # Just above the top of the plot
        xref="x",
        yref="paper",
        text="Deadline",
        showarrow=False,
        font=dict(color="#FF0000", size=14),
        xanchor="center",
        yanchor="bottom",
    )

    # Add shaded region before deadline
    current_date = pd.Timestamp.now()

    # Add a light red shaded region for the critical period (last 14 days before deadline)
    if current_date < deadline:
        # Calculate the start of the critical period (14 days before deadline)
        critical_start = deadline - pd.Timedelta(days=14)

        # Convert to datetime for better compatibility
        if isinstance(critical_start, pd.Timestamp):
            critical_start_datetime = critical_start.to_pydatetime()
        else:
            critical_start_datetime = critical_start

        # Use shape for consistent behavior
        fig.add_shape(
            type="rect",
            x0=critical_start_datetime,
            x1=deadline_datetime,
            y0=0,
            y1=1,
            yref="paper",
            fillcolor="rgba(255, 0, 0, 0.15)",
            line=dict(width=0),
            layer="below",
        )
    # If deadline has passed, shade the region after deadline
    else:
        # Convert current_date to datetime for compatibility
        if isinstance(current_date, pd.Timestamp):
            current_datetime = current_date.to_pydatetime()
        else:
            current_datetime = current_date

        # Use shape for consistent behavior
        fig.add_shape(
            type="rect",
            x0=deadline_datetime,
            x1=current_datetime,
            y0=0,
            y1=1,
            yref="paper",
            fillcolor="rgba(255, 0, 0, 0.15)",
            line=dict(width=0),
            layer="below",
        )

    # Add milestone marker if provided
    if milestone is not None:
        # Convert pandas Timestamp to a format compatible with Plotly
        if isinstance(milestone, pd.Timestamp):
            milestone_datetime = milestone.to_pydatetime()
        else:
            milestone_datetime = milestone

        # Use a color from the color palette that fits well with the other colors
        milestone_color = COLOR_PALETTE.get(
            "optimistic", "#5E35B1"
        )  # Default to purple if not in palette

        # Create a vertical line for milestone
        fig.add_shape(
            type="line",
            x0=milestone_datetime,
            x1=milestone_datetime,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color=milestone_color, width=2, dash="dot"),
            layer="above",
        )

        # Add milestone annotation
        fig.add_annotation(
            x=milestone_datetime,
            y=0.99,  # Position it slightly above the chart but below the deadline text
            xref="x",
            yref="paper",
            text=f"MS-{milestone_datetime.strftime('%Y-%m-%d')}",
            showarrow=False,
            font=dict(color=milestone_color, size=14),
            xanchor="center",
            yanchor="bottom",
        )

    return fig


def create_chart_with_loading(
    id, figure=None, loading_state=None, type="default", height=None
):
    """
    Create a chart component with built-in loading states.

    Args:
        id (str): Component ID for the chart
        figure (dict, optional): Initial Plotly figure
        loading_state (dict, optional): Loading state information
        type (str): Chart type (default, bar, line, scatter)
        height (str, optional): Chart height

    Returns:
        html.Div: Chart component with loading states
    """
    from dash import dcc
    from ui.loading_utils import create_loading_overlay

    # Determine if we're in a loading state
    is_loading = loading_state is not None and loading_state.get("is_loading", False)

    # Create appropriate loading message based on chart type
    loading_messages = {
        "default": "Loading chart...",
        "bar": "Generating bar chart...",
        "line": "Preparing line chart...",
        "scatter": "Creating scatter plot...",
        "pie": "Building pie chart...",
        "area": "Creating area chart...",
    }
    message = loading_messages.get(type, "Loading chart...")

    # Create the chart component
    chart = dcc.Graph(
        id=id,
        figure=figure or {},
        config={
            "displayModeBar": True,
            "responsive": True,
            "toImageButtonOptions": {
                "format": "png",
                "filename": f"{id.replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "scale": 2,
            },
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "toggleSpikelines",
            ],
        },
        style={"height": height or "100%", "width": "100%"},
    )

    # Wrap the chart with a loading state
    return create_loading_overlay(
        children=chart,
        style_key="primary",
        size_key="lg",
        text=message,
        is_loading=is_loading,
        opacity=0.7,
        className=f"{id}-loading-wrapper",
    )


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


# create_burnup_chart function removed - burnup functionality deprecated


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
        daily_forecast_burnup,
        compute_weekly_throughput,
        calculate_rates,
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
    if (
        data_points_count is not None
        and data_points_count > 0
        and len(df_calc) > data_points_count
    ):
        # Get the most recent data_points_count rows
        df_calc = df_calc.iloc[-data_points_count:]

    # Compute weekly throughput with the filtered data
    grouped = compute_weekly_throughput(df_calc)

    # Ensure grouped is a DataFrame
    if not isinstance(grouped, pd.DataFrame):
        grouped = pd.DataFrame(grouped)

    # Filter out zero-value weeks before calculating rates
    # These are artificial weeks added by _fill_missing_weeks and shouldn't
    # influence PERT pessimistic/optimistic calculations
    # Use AND condition to ensure weeks with meaningful data for both metrics
    grouped_non_zero = grouped[
        (grouped["completed_items"] > 0) & (grouped["completed_points"] > 0)
    ].copy()

    # If no valid weeks exist, return early with safe defaults
    # (prevents pessimistic forecasts from extending years into the future)
    if len(grouped_non_zero) == 0:
        # Return empty forecast data to indicate insufficient data
        return {
            "df_calc": df_calc,
            "pert_time_items": 0,
            "pert_time_points": 0,
            "items_forecasts": {"avg": ([], []), "opt": ([], []), "pes": ([], [])},
            "points_forecasts": {"avg": ([], []), "opt": ([], []), "pes": ([], [])},
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
    if is_burnup:
        # For burnup charts, start from completed values and forecast toward scope
        items_forecasts = {
            "avg": daily_forecast_burnup(
                last_items, items_daily_rate, start_date, scope_items
            ),
            "opt": daily_forecast_burnup(
                last_items, optimistic_items_rate, start_date, scope_items
            ),
            "pes": daily_forecast_burnup(
                last_items, pessimistic_items_rate, start_date, scope_items
            ),
        }

        points_forecasts = {
            "avg": daily_forecast_burnup(
                last_points, points_daily_rate, start_date, scope_points
            ),
            "opt": daily_forecast_burnup(
                last_points, optimistic_points_rate, start_date, scope_points
            ),
            "pes": daily_forecast_burnup(
                last_points, pessimistic_points_rate, start_date, scope_points
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


def _create_forecast_axes_titles(fig, forecast_data):
    """
    Configure the axis titles for the forecast plot.

    Args:
        fig: Plotly figure object
        forecast_data: Dictionary with forecast data

    Returns:
        Updated figure with configured axis titles
    """
    # Configure x-axis title
    fig.update_xaxes(
        title={"text": "Date", "font": {"size": 16}},
    )

    # Configure primary y-axis (items) title
    fig.update_yaxes(
        title={"text": "Remaining Items", "font": {"size": 16}},
        secondary_y=False,
    )

    # Configure secondary y-axis (points) title
    fig.update_yaxes(
        title={"text": "Remaining Points", "font": {"size": 16}},
        secondary_y=True,
    )

    return fig


def _calculate_forecast_completion_dates(pert_time_items, pert_time_points):
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


def _prepare_metrics_data(
    total_items,
    total_points,
    deadline,
    pert_time_items,
    pert_time_points,
    data_points_count,
    df,
    items_completion_enhanced,
    points_completion_enhanced,
    avg_weekly_items=0.0,
    avg_weekly_points=0.0,
    med_weekly_items=0.0,
    med_weekly_points=0.0,
):
    """
    Prepare metrics data for display in the forecast plot.

    Args:
        total_items: Total number of remaining items to complete
        total_points: Total number of remaining points to complete
        deadline: Deadline date
        pert_time_items: PERT time estimate for items in days
        pert_time_points: PERT time estimate for points in days
        data_points_count: Number of data points used in the forecast
        df: DataFrame with historical data
        items_completion_enhanced: Enhanced completion date string for items
        points_completion_enhanced: Enhanced completion date string for points
        avg_weekly_items: Average weekly completed items
        avg_weekly_points: Average weekly completed points
        med_weekly_items: Median weekly completed items
        med_weekly_points: Median weekly completed points

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

    # Calculate completed work from the dataframe
    completed_items = 0
    completed_points = 0

    if (
        not df.empty
        and "completed_items" in df.columns
        and "completed_points" in df.columns
    ):
        completed_items = (
            df["completed_items"].sum() if "completed_items" in df.columns else 0
        )
        completed_points = (
            df["completed_points"].sum() if "completed_points" in df.columns else 0
        )

    # Calculate total scope (completed + remaining)
    total_scope_items = completed_items + total_items
    total_scope_points = completed_points + total_points

    # Calculate completion percentage
    items_percent_complete = 0
    points_percent_complete = 0

    if total_scope_items > 0:
        items_percent_complete = (completed_items / total_scope_items) * 100

    if total_scope_points > 0:
        points_percent_complete = (completed_points / total_scope_points) * 100

    # Create metrics data dictionary with explicit float conversions for weekly metrics
    return {
        "total_items": total_items,
        "total_points": total_points,
        "total_scope_items": total_scope_items,
        "total_scope_points": total_scope_points,
        "completed_items": completed_items,
        "completed_points": completed_points,
        "items_percent_complete": items_percent_complete,
        "points_percent_complete": points_percent_complete,
        "deadline": deadline_str,
        "days_to_deadline": days_to_deadline,
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "avg_weekly_items": round(float(avg_weekly_items), 2),
        "avg_weekly_points": round(float(avg_weekly_points), 2),
        "med_weekly_items": round(float(med_weekly_items), 2),
        "med_weekly_points": round(float(med_weekly_points), 2),
        # Ensure string representations use 2 decimal places and never get converted to integers
        "avg_weekly_items_str": f"{float(avg_weekly_items):.2f}",
        "avg_weekly_points_str": f"{float(avg_weekly_points):.2f}",
        "med_weekly_items_str": f"{float(med_weekly_items):.2f}",
        "med_weekly_points_str": f"{float(med_weekly_points):.2f}",
        "data_points_used": int(data_points_count)
        if data_points_count is not None and isinstance(data_points_count, (int, float))
        else (len(df) if hasattr(df, "__len__") else 0),
        "data_points_available": len(df) if hasattr(df, "__len__") else 0,
        "items_completion_enhanced": items_completion_enhanced,
        "points_completion_enhanced": points_completion_enhanced,
    }


#######################################################################
# DASHBOARD VISUALIZATIONS (User Story 2)
#######################################################################


def create_pert_timeline_chart(pert_data: dict) -> go.Figure:
    """
    Create horizontal timeline visualization for PERT forecasts.

    This function supports User Story 2: Dashboard as Primary Landing View.
    It creates an interactive timeline showing optimistic, most likely, and
    pessimistic completion dates with visual indicators for confidence range.

    Args:
        pert_data: PERTTimelineData dictionary from calculate_pert_timeline()

    Returns:
        go.Figure: Plotly figure with horizontal timeline

    Example:
        >>> pert_data = calculate_pert_timeline(stats, settings)
        >>> fig = create_pert_timeline_chart(pert_data)

    Chart Features:
        - Horizontal bar showing date range
        - Markers for optimistic, most likely, pessimistic dates
        - PERT weighted average highlighted
        - Confidence range shading
    """
    from datetime import datetime

    # Parse dates
    try:
        optimistic = (
            datetime.strptime(pert_data["optimistic_date"], "%Y-%m-%d")
            if pert_data.get("optimistic_date")
            else None
        )
        most_likely = (
            datetime.strptime(pert_data["most_likely_date"], "%Y-%m-%d")
            if pert_data.get("most_likely_date")
            else None
        )
        pessimistic = (
            datetime.strptime(pert_data["pessimistic_date"], "%Y-%m-%d")
            if pert_data.get("pessimistic_date")
            else None
        )
        pert_estimate = (
            datetime.strptime(pert_data["pert_estimate_date"], "%Y-%m-%d")
            if pert_data.get("pert_estimate_date")
            else None
        )
    except (ValueError, TypeError):
        # Return empty chart if dates are invalid
        fig = go.Figure()
        fig.add_annotation(
            text="No forecast data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
        )
        return fig

    if not all([optimistic, most_likely, pessimistic, pert_estimate]):
        # Return empty chart if dates are missing
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for timeline forecast",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
        )
        return fig

    # Create figure
    fig = go.Figure()

    # Add confidence range bar (optimistic to pessimistic)
    fig.add_trace(
        go.Scatter(
            x=[optimistic, pessimistic],
            y=[0, 0],
            mode="lines",
            line=dict(color="rgba(13, 110, 253, 0.2)", width=20),
            name="Confidence Range",
            showlegend=True,
            hovertemplate="Range: %{x}<extra></extra>",
        )
    )

    # Add markers for key dates
    scenarios = [
        (optimistic, "Optimistic", "green", "circle"),
        (most_likely, "Most Likely", "blue", "diamond"),
        (pert_estimate, "PERT Estimate", "purple", "star"),
        (pessimistic, "Pessimistic", "orange", "circle"),
    ]

    for date, label, color, symbol in scenarios:
        fig.add_trace(
            go.Scatter(
                x=[date],
                y=[0],
                mode="markers+text",
                marker=dict(
                    size=15,
                    color=color,
                    symbol=symbol,
                    line=dict(width=2, color="white"),
                ),
                text=[label],
                textposition="top center",
                name=label,
                showlegend=True,
                hovertemplate=f"<b>{label}</b><br>Date: %{{x|%Y-%m-%d}}<br>Days: {pert_data.get(label.lower().replace(' ', '_') + '_days', 'N/A')}<extra></extra>",
            )
        )

    # Update layout
    fig.update_layout(
        title="PERT Timeline Forecast",
        xaxis=dict(
            title="Completion Date",
            type="date",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.1)",
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[-0.5, 0.5],
        ),
        height=300,
        hovermode="closest",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=60),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
        ),
    )

    return fig


#######################################################################
# MOBILE OPTIMIZATION HELPERS (Phase 7: User Story 5)
#######################################################################


def get_mobile_chart_config(is_mobile=False, is_tablet=False):
    """
    Get mobile-optimized chart configuration for Plotly graphs.

    This function provides responsive chart configurations that optimize
    chart display for different viewport sizes by adjusting margins,
    legends, and interactive features.

    Args:
        is_mobile: Whether the viewport is mobile (<768px)
        is_tablet: Whether the viewport is tablet (768-992px)

    Returns:
        dict: Plotly graph config object optimized for viewport

    Example:
        >>> config = get_mobile_chart_config(is_mobile=True)
        >>> dcc.Graph(figure=fig, config=config)
    """
    if is_mobile:
        # Mobile configuration: minimal UI, touch-optimized
        return {
            "displayModeBar": False,  # Hide modebar on mobile to save space
            "responsive": True,  # Enable responsive resizing
            "scrollZoom": False,  # Disable scroll zoom to avoid interference
            "doubleClick": "reset",  # Double tap to reset view
            "showTips": False,  # Hide tips
            "displaylogo": False,  # Hide Plotly logo
        }
    elif is_tablet:
        # Tablet configuration: show minimal modebar
        return {
            "displayModeBar": "hover",  # Show modebar on hover
            "modeBarButtonsToRemove": [
                "pan2d",
                "select2d",
                "lasso2d",
                "autoScale2d",
                "toggleSpikelines",
            ],
            "responsive": True,
            "scrollZoom": True,
            "doubleClick": "reset+autosize",
            "displaylogo": False,
        }
    else:
        # Desktop configuration: full features
        return {
            "displayModeBar": "hover",
            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
            "responsive": True,
            "scrollZoom": True,
            "doubleClick": "reset+autosize",
            "displaylogo": False,
        }


def get_mobile_chart_layout(
    is_mobile=False, is_tablet=False, show_legend=True, title=None
):
    """
    Get mobile-optimized layout configuration for Plotly charts.

    Adjusts margins, font sizes, legend placement, and other layout
    properties based on viewport size for optimal mobile experience.

    Args:
        is_mobile: Whether the viewport is mobile (<768px)
        is_tablet: Whether the viewport is tablet (768-992px)
        show_legend: Whether to show legend (automatically hidden on mobile)
        title: Chart title (optional, hidden on mobile to save space)

    Returns:
        dict: Plotly layout updates to merge with existing layout

    Example:
        >>> mobile_layout = get_mobile_chart_layout(is_mobile=True)
        >>> fig.update_layout(**mobile_layout)
    """
    if is_mobile:
        # Mobile layout: minimal margins, no legend, compact
        return {
            "margin": dict(l=40, r=10, t=30 if title else 10, b=40),
            "showlegend": False,  # Hide legend on mobile to maximize chart space
            "font": dict(size=10),  # Smaller font for mobile
            "title": dict(
                text=title if title else None,
                font=dict(size=14),
                x=0.5,
                xanchor="center",
            )
            if title
            else None,
            "height": 300,  # Fixed height for mobile
            "hovermode": "closest",  # Closest point for touch precision
        }
    elif is_tablet:
        # Tablet layout: moderate margins, bottom legend
        return {
            "margin": dict(
                l=50, r=20, t=50 if title else 20, b=80 if show_legend else 50
            ),
            "showlegend": show_legend,
            "font": dict(size=12),
            "title": dict(
                text=title if title else None,
                font=dict(size=16),
                x=0.5,
                xanchor="center",
            )
            if title
            else None,
            "legend": dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=11),
            )
            if show_legend
            else None,
            "height": 400,
            "hovermode": "x unified",
        }
    else:
        # Desktop layout: standard margins and configuration
        return {
            "margin": dict(
                l=60, r=30, t=80 if title else 30, b=100 if show_legend else 60
            ),
            "showlegend": show_legend,
            "font": dict(size=13),
            "title": dict(
                text=title if title else None,
                font=dict(size=18),
                x=0.5,
                xanchor="center",
            )
            if title
            else None,
            "legend": dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="right",
                x=1.15,
            )
            if show_legend
            else None,
            "height": 500,
            "hovermode": "x unified",
        }


def apply_mobile_optimization(fig, is_mobile=False, is_tablet=False, title=None):
    """
    Apply mobile optimization to an existing Plotly figure.

    This is a convenience function that applies both config and layout
    optimizations to a figure in one call.

    Args:
        fig: Plotly figure object to optimize
        is_mobile: Whether the viewport is mobile (<768px)
        is_tablet: Whether the viewport is tablet (768-992px)
        title: Optional chart title

    Returns:
        tuple: (optimized_figure, config_dict) ready for dcc.Graph

    Example:
        >>> fig = create_forecast_plot(...)
        >>> optimized_fig, config = apply_mobile_optimization(fig, is_mobile=True)
        >>> dcc.Graph(figure=optimized_fig, config=config)
    """
    # Get mobile-optimized layout
    layout_updates = get_mobile_chart_layout(
        is_mobile=is_mobile, is_tablet=is_tablet, show_legend=not is_mobile, title=title
    )

    # Apply layout updates
    fig.update_layout(**layout_updates)

    # Get config
    config = get_mobile_chart_config(is_mobile=is_mobile, is_tablet=is_tablet)

    return fig, config
