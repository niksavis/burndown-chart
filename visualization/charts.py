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
        title={"text": "Date", "font": {"size": 16}},
        tickmode="auto",
        nticks=20,
        gridcolor="rgba(200, 200, 200, 0.2)",
        automargin=True,
    )

    # Configure primary y-axis (items)
    fig.update_yaxes(
        title={"text": "Remaining Items", "font": {"size": 16}},
        range=items_range,
        gridcolor=COLOR_PALETTE["items_grid"],
        zeroline=True,
        zerolinecolor="black",
        secondary_y=False,
    )

    # Configure secondary y-axis (points)
    fig.update_yaxes(
        title={"text": "Remaining Points", "font": {"size": 16}},
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


def add_metrics_annotations(fig, metrics_data):
    """
    Add metrics as annotations below the x-axis of the plot.

    Organized for responsive display on various screen sizes with more consistent spacing.

    Args:
        fig: Plotly figure object
        metrics_data: Dictionary with metrics to display

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
        # Row 3 - Remaining and estimates
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
            "label": "Avg Weekly Items (10W)",
            "value": metrics_data["avg_weekly_items"],
            "format": "{:.2f}",  # Changed from {:.1f} to show 2 decimal places
        },
        {
            "label": "Avg Weekly Points (10W)",
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
        days_to_deadline = max(0, (deadline - pd.Timestamp(current_date)).days)

        # Calculate weekly metrics
        avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
            _get_weekly_metrics(df)
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
            fig = add_metrics_annotations(fig, metrics_data)
        except Exception as metrics_error:
            # Log the error but continue without metrics
            logger = logging.getLogger("burndown_chart")
            logger.error(
                f"Error preparing metrics data: {str(metrics_error)}\n{traceback.format_exc()}"
            )

            # Create minimal metrics data with default values
            metrics_data = {
                "total_items": total_items,
                "total_points": total_points,
                "deadline": deadline.strftime("%Y-%m-%d")
                if hasattr(deadline, "strftime")
                else "Unknown",
                "days_to_deadline": days_to_deadline,
                "avg_weekly_items": float(avg_weekly_items),
                "avg_weekly_points": float(avg_weekly_points),
                "med_weekly_items": float(med_weekly_items),
                "med_weekly_points": float(med_weekly_points),
            }

            # Try to add metrics with the minimal data
            try:
                fig = add_metrics_annotations(fig, metrics_data)
            except Exception:
                # If even this fails, just continue without metrics
                pass

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


def _get_weekly_metrics(df):
    """
    Calculate weekly metrics from the data frame.

    Args:
        df: DataFrame with historical data

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
        # Get all four values from calculate_weekly_averages
        results = calculate_weekly_averages(df.to_dict("records"))
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
        "avg_weekly_items": 0.0,  # Ensure consistent with non-error case
        "avg_weekly_points": 0.0,  # Ensure consistent with non-error case
        "med_weekly_items": 0.0,  # Keep as float
        "med_weekly_points": 0.0,  # Keep as float
        "error": str(e),
        "forecast_timestamp": datetime.now().isoformat(),
    }

    return fig, safe_pert_data


def create_weekly_items_chart(
    statistics_data, date_range_weeks=12, pert_factor=3, include_forecast=True
):
    """
    Create a bar chart showing weekly completed items with optional forecast for the next week.

    Args:
        statistics_data: List of dictionaries containing statistics data
        date_range_weeks: Number of weeks to display (default: 12 weeks)
        pert_factor: PERT factor for calculations (for forecast)
        include_forecast: Whether to include forecast data (default: True)

    Returns:
        Plotly figure object with the weekly items chart
    """
    # Create DataFrame from statistics data
    df = pd.DataFrame(statistics_data).copy()
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
    df["date"] = pd.to_datetime(df["date"])

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
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(items=("completed_items", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Format date for display
    weekly_df["week_label"] = weekly_df["start_date"].dt.strftime("%b %d")

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

    # Add forecast data if requested
    if include_forecast and len(weekly_df) > 0:
        # Generate forecast data
        forecast_data = generate_weekly_forecast(statistics_data, pert_factor)

        if forecast_data["items"]["dates"]:
            # Most likely forecast - only display the single bar for the next week
            fig.add_trace(
                go.Bar(
                    x=forecast_data["items"]["dates"],
                    y=forecast_data["items"]["most_likely"],
                    marker_color=COLOR_PALETTE["items"],
                    marker_pattern_shape="x",  # Add pattern to distinguish forecast
                    opacity=0.7,
                    name="Next Week Forecast",
                    text=[
                        round(val, 1) for val in forecast_data["items"]["most_likely"]
                    ],
                    textposition="outside",
                    hovertemplate=format_hover_template(
                        title="Items Forecast",
                        fields={
                            "Week": "%{x}",
                            "Items": "%{y:.1f}",
                            "Type": "Most Likely",
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
    statistics_data, date_range_weeks=12, pert_factor=3, include_forecast=True
):
    """
    Create a bar chart showing weekly completed points with a weighted moving average line and optional forecast for next week.

    Args:
        statistics_data: List of dictionaries containing statistics data
        date_range_weeks: Number of weeks to display (default: 12 weeks)
        pert_factor: PERT factor for calculations (for forecast)
        include_forecast: Whether to include forecast data (default: True)

    Returns:
        Plotly figure object with the weekly points chart
    """
    # Create DataFrame from statistics data
    df = pd.DataFrame(statistics_data).copy()
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
    df["date"] = pd.to_datetime(df["date"])

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
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(points=("completed_points", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Format date for display
    weekly_df["week_label"] = weekly_df["start_date"].dt.strftime("%b %d")

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

    # Add forecast data if requested
    if include_forecast and len(weekly_df) > 0:
        # Generate forecast data
        forecast_data = generate_weekly_forecast(statistics_data, pert_factor)

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
    statistics_data, pert_factor=3, date_range_weeks=12
):
    """
    Create a chart showing weekly completed items with a 4-week forecast.

    Args:
        statistics_data: List of dictionaries containing statistics data
        pert_factor: Number of data points to use for optimistic/pessimistic scenarios
        date_range_weeks: Number of weeks of historical data to display (default: 12 weeks)

    Returns:
        Plotly figure object with the weekly items forecast chart
    """
    # Create DataFrame from statistics data
    df = pd.DataFrame(statistics_data).copy()
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
    df["date"] = pd.to_datetime(df["date"])

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
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(items=("completed_items", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Format date for display
    weekly_df["week_label"] = weekly_df["start_date"].dt.strftime("%b %d")

    # Generate forecast data
    forecast_data = generate_weekly_forecast(statistics_data, pert_factor)

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
    statistics_data, pert_factor=3, date_range_weeks=12
):
    """
    Create a chart showing weekly completed points with a 4-week forecast.

    Args:
        statistics_data: List of dictionaries containing statistics data
        pert_factor: Number of data points to use for optimistic/pessimistic scenarios
        date_range_weeks: Number of weeks of historical data to display (default: 12 weeks)

    Returns:
        Plotly figure object with the weekly points forecast chart
    """
    # Create DataFrame from statistics data
    df = pd.DataFrame(statistics_data).copy()
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
    df["date"] = pd.to_datetime(df["date"])

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
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(points=("completed_points", "sum"), start_date=("date", "min"))
        .reset_index()
    )

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Format date for display
    weekly_df["week_label"] = weekly_df["start_date"].dt.strftime("%b %d")

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

    # Generate forecast data
    forecast_data = generate_weekly_forecast(statistics_data, pert_factor)

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
                    f"<b>Optimistic:</b> {forecast_data['points'].get('optimistic_value', 0)::.1f} points/week<br>"
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
    dates = [pd.to_datetime(date) for date in forecast_data.get("dates", [])]

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


def create_burnup_chart(
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
    Create a burnup chart showing both completed work and total scope over time.

    Args:
        df: DataFrame with statistics data
        total_items: Total number of remaining items to complete (not the original baseline)
        total_points: Total number of remaining points to complete (not the original baseline)
        pert_factor: PERT factor for calculations
        deadline_str: Deadline date as string (YYYY-MM-DD)
        milestone_str: Milestone date as string (YYYY-MM-DD), optional
        data_points_count: Number of most recent data points to use (defaults to all)
        show_forecast: Whether to show forecast traces (default: True)
        forecast_visibility: Visibility mode for forecast traces ("legendonly" or True)
        hover_mode: Hover mode for the chart ("x unified" or "closest")
        show_points: Whether points tracking is enabled (default: True)

    Returns:
        Tuple of (figure, data_dict) where data_dict contains all chart information
    """
    try:
        # Ensure numeric types for calculations with explicit conversion and error handling
        try:
            total_items = float(total_items) if total_items is not None else 0.0
        except (ValueError, TypeError):
            total_items = 0.0

        try:
            total_points = float(total_points) if total_points is not None else 0.0
        except (ValueError, TypeError):
            total_points = 0.0

        try:
            pert_factor = int(pert_factor) if pert_factor is not None else 3
        except (ValueError, TypeError):
            pert_factor = 3

        # Ensure proper date format for deadline
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
                # Ensure milestone is not after or equal to deadline
                if milestone >= deadline:
                    logging.getLogger("burndown_chart").warning(
                        f"Milestone date {milestone_str} is not before deadline {deadline_str}. Ignoring milestone."
                    )
                    milestone = None
            except (ValueError, TypeError):
                logging.getLogger("burndown_chart").warning(
                    f"Invalid milestone format: {milestone_str}. Ignoring milestone."
                )
                milestone = None

        # Create a single figure with subplots - force exact alignment with proper options
        fig = make_subplots(
            specs=[[{"secondary_y": True}]],
            shared_xaxes=True,
            horizontal_spacing=0.0,  # Force perfect alignment by eliminating any spacing
        )

        # Create empty figure if no data
        if df is None or df.empty:
            fig.add_annotation(
                text="No data available for burnup chart",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16),
            )
            return fig, {}

        # Ensure DataFrame has required columns
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        # Sort by date
        df = df.sort_values("date")

        # Calculate cumulative completed work
        if "completed_items" not in df.columns:
            df["completed_items"] = 0
        if "completed_points" not in df.columns:
            df["completed_points"] = 0
        if "created_items" not in df.columns:
            df["created_items"] = 0
        if "created_points" not in df.columns:
            df["created_points"] = 0

        # IMPORTANT: Ensure this is exactly the same starting point logic as in create_forecast_plot
        # Add starting point 7 days before the first data point with zero values
        if not df.empty:
            first_date = df["date"].min()
            start_date = first_date - pd.Timedelta(days=7)

            # Create starting point row with only essential zero values
            # This ensures consistent behavior with the burndown chart
            required_cols = ["date", "completed_items", "completed_points"]
            extra_cols = (
                ["created_items", "created_points"]
                if "created_items" in df.columns
                else []
            )

            start_dict = {col: [0] for col in required_cols + extra_cols}
            start_dict["date"] = [start_date]
            start_row = pd.DataFrame(start_dict)

            # Add the starting point to the dataframe
            df = pd.concat([start_row, df], ignore_index=True)
            df = df.sort_values("date")  # Ensure proper sorting

        # Now continue with the burnup chart specific calculations
        df["cum_completed_items"] = df["completed_items"].cumsum()
        df["cum_completed_points"] = df["completed_points"].cumsum()

        # Calculate cumulative created items/points
        df["cum_created_items"] = df["created_items"].cumsum()
        df["cum_created_points"] = df["created_points"].cumsum()

        # Get current completed and created totals
        completed_items_total = df["cum_completed_items"].iloc[-1]
        completed_points_total = df["cum_completed_points"].iloc[-1]
        created_items_total = df["cum_created_items"].iloc[-1]
        created_points_total = df["cum_created_points"].iloc[-1]

        # Log the data for debugging
        logger = logging.getLogger("burndown_chart")
        logger.info(f"Burnup chart - Completed items total: {completed_items_total}")
        logger.info(f"Burnup chart - Completed points total: {completed_points_total}")
        logger.info(f"Burnup chart - Created items total: {created_items_total}")
        logger.info(f"Burnup chart - Created points total: {created_points_total}")

        # For display purposes, use the cumulative created values
        df["cum_scope_items"] = df["cum_created_items"]
        df["cum_scope_points"] = df["cum_created_points"]

        # Create a copy of the dataframe with column names expected by prepare_forecast_data
        df_forecast = df.copy()
        df_forecast["cum_items"] = df_forecast["cum_completed_items"]
        df_forecast["cum_points"] = df_forecast["cum_completed_points"]

        # Calculate total scope (completed + remaining) for forecast target
        # This ensures forecasts reach expected scope values, not just cum_created
        final_scope_items = completed_items_total + total_items
        final_scope_points = completed_points_total + total_points

        logger.info(
            f"Burnup chart - Final scope items (completed + remaining): {final_scope_items}"
        )
        logger.info(
            f"Burnup chart - Final scope points (completed + remaining): {final_scope_points}"
        )
        logger.info(
            f"Burnup chart - Created scope items (from dataset): {created_items_total}"
        )
        logger.info(
            f"Burnup chart - Created scope points (from dataset): {created_points_total}"
        )

        # Ensure we have valid scope values - if scope is zero, forecasts won't show
        if final_scope_items <= 0:
            final_scope_items = max(
                10, completed_items_total * 1.5
            )  # Set a reasonable fallback
            logger.warning(
                f"Final scope items was zero or negative, using fallback value: {final_scope_items}"
            )

        if final_scope_points <= 0:
            final_scope_points = max(
                10, completed_points_total * 1.5
            )  # Set a reasonable fallback
            logger.warning(
                f"Final scope points was zero or negative, using fallback value: {final_scope_points}"
            )

        # Calculate remaining work to be done (the actual values needed for forecast calculation)
        remaining_items = max(0, final_scope_items - completed_items_total)
        remaining_points = max(0, final_scope_points - completed_points_total)

        logger.info(f"Burnup chart - Remaining items to complete: {remaining_items}")
        logger.info(f"Burnup chart - Remaining points to complete: {remaining_points}")

        # Calculate forecast data using the prepare_visualization_data function with burnup=True
        # Pass the remaining work values instead of the raw total_items/total_points
        forecast_data = prepare_visualization_data(
            df_forecast,
            remaining_items,  # Pass remaining items to complete (not total_items)
            remaining_points,  # Pass remaining points to complete (not total_points)
            pert_factor,
            data_points_count,
            is_burnup=True,
            scope_items=final_scope_items,
            scope_points=final_scope_points,
            show_points=show_points,
        )

        # Log forecast data for debugging
        items_forecasts = forecast_data["items_forecasts"]
        points_forecasts = forecast_data["points_forecasts"]

        # Debug: Log the first and last forecast values for both items and points
        logger.info(
            f"Burnup chart - First items forecast value: {items_forecasts['avg'][1][0] if items_forecasts['avg'][1] else 'N/A'}"
        )
        logger.info(
            f"Burnup chart - Last items forecast value: {items_forecasts['avg'][1][-1] if items_forecasts['avg'][1] else 'N/A'}"
        )
        logger.info(f"Burnup chart - Target scope items: {final_scope_items}")

        logger.info(
            f"Burnup chart - First points forecast value: {points_forecasts['avg'][1][0] if points_forecasts['avg'][1] else 'N/A'}"
        )
        logger.info(
            f"Burnup chart - Last points forecast value: {points_forecasts['avg'][1][-1] if points_forecasts['avg'][1] else 'N/A'}"
        )
        logger.info(f"Burnup chart - Target scope points: {final_scope_points}")

        # Check if forecasts reach their target scope values
        if (
            items_forecasts["avg"][1]
            and abs(items_forecasts["avg"][1][-1] - final_scope_items) > 1
        ):
            logger.warning(
                f"Items forecast doesn't reach target scope: {items_forecasts['avg'][1][-1]} vs {final_scope_items}"
            )

        if (
            points_forecasts["avg"][1]
            and abs(points_forecasts["avg"][1][-1] - final_scope_points) > 1
        ):
            logger.warning(
                f"Points forecast doesn't reach target scope: {points_forecasts['avg'][1][-1]} vs {final_scope_points}"
            )

        # Check if we have valid forecast data and log it consistently for both items and points
        def validate_forecast_data(forecast_data, forecast_type):
            """Helper function to validate forecast data and log issues"""
            is_valid = True
            for key in ["avg", "opt", "pes"]:
                if not (
                    forecast_data
                    and forecast_data[key]
                    and len(forecast_data[key]) >= 2
                    and len(forecast_data[key][0]) > 0
                    and len(forecast_data[key][1]) > 0
                ):
                    logger.warning(
                        f"{forecast_type} forecast '{key}' data is invalid or empty"
                    )
                    is_valid = False
                else:
                    logger.info(
                        f"{forecast_type} forecast '{key}' data length: {len(forecast_data[key][0])}"
                    )
                    if len(forecast_data[key][0]) > 0:
                        logger.info(
                            f"First few values: {forecast_data[key][1][:3] if len(forecast_data[key][1]) > 3 else forecast_data[key][1]}"
                        )
            return is_valid

        # Check and log forecast data for both items and points
        has_items_forecast = validate_forecast_data(items_forecasts, "Items")
        has_points_forecast = validate_forecast_data(points_forecasts, "Points")

        logger.info(f"Burnup chart - Has items forecast data: {has_items_forecast}")
        logger.info(f"Burnup chart - Has points forecast data: {has_points_forecast}")

        # Create traces for completed work
        completed_items_trace = go.Scatter(
            x=df["date"],
            y=df["cum_completed_items"],
            mode="lines+markers",
            name="Completed Items",
            line=dict(color=COLOR_PALETTE["items"], width=3),
            marker=dict(
                size=8,
                color=COLOR_PALETTE["items"],
                symbol="circle",
                line=dict(width=2, color="white"),
            ),
            hovertemplate=format_hover_template(
                title="Completed Items",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Items": "%{y}",
                },
                extra_info="Items",
            ),
            hoverlabel=create_hoverlabel_config("default"),
        )

        completed_points_trace = go.Scatter(
            x=df["date"],
            y=df["cum_completed_points"],
            mode="lines+markers",
            name="Completed Points",
            line=dict(color=COLOR_PALETTE["points"], width=3),
            marker=dict(
                size=8,
                color=COLOR_PALETTE["points"],
                symbol="circle",
                line=dict(width=2, color="white"),
            ),
            hovertemplate=format_hover_template(
                title="Completed Points",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Points": "%{y}",
                },
                extra_info="Points",
            ),
            hoverlabel=create_hoverlabel_config("default"),
        )

        # Create traces for total scope
        scope_items_trace = go.Scatter(
            x=df["date"],
            y=df["cum_scope_items"],
            mode="lines",
            name="Created Items",
            line=dict(
                color="#0047AB", width=3, dash="dot"
            ),  # Darker blue and thicker line
            marker=dict(
                size=10,  # Increased marker size
                color="#0047AB",  # Matching darker blue color
                symbol="square",
                line=dict(width=2, color="white"),
            ),
            hovertemplate=format_hover_template(
                title="Created Items",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Items": "%{y}",
                },
                extra_info="Created Items",
            ),
            hoverlabel=create_hoverlabel_config("default"),
        )

        scope_points_trace = go.Scatter(
            x=df["date"],
            y=df["cum_scope_points"],
            mode="lines",
            name="Created Points",
            line=dict(
                color="#B22222", width=3, dash="dot"
            ),  # Firebrick red and thicker line
            marker=dict(
                size=10,  # Increased marker size
                color="#B22222",  # Matching firebrick red color
                symbol="square",
                line=dict(width=2, color="white"),
            ),
            hovertemplate=format_hover_template(
                title="Created Points",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Points": "%{y}",
                },
                extra_info="Created Points",
            ),
            hoverlabel=create_hoverlabel_config("default"),
        )

        # Add forecasts to the chart if show_forecast is True
        if show_forecast:
            # Add PERT forecast traces for items if available
            def add_forecast_trace(
                fig,
                forecast_data,
                key,
                forecast_type,
                color,
                dash_style,
                symbol,
                name,
                hover_type,
                hover_style,
                secondary_y,
            ):
                """Helper function to add forecast traces with error handling"""
                if not (
                    forecast_data
                    and forecast_data[key]
                    and len(forecast_data[key]) >= 2
                    and len(forecast_data[key][0]) > 0
                    and len(forecast_data[key][1]) > 0
                ):
                    logger.warning(
                        f"Cannot add {forecast_type} {key} forecast trace - invalid data"
                    )
                    return False  # Return False to indicate failure

                # Log more details about the first and last points for debugging
                logger.info(
                    f"{forecast_type} {key} forecast: Start={forecast_data[key][1][0]}, End={forecast_data[key][1][-1]}"
                )

                fig.add_trace(
                    go.Scatter(
                        x=forecast_data[key][0],
                        y=forecast_data[key][1],
                        mode="lines+markers",
                        name=name,
                        line=dict(
                            color=color,
                            dash=dash_style,
                            width=3 if key == "avg" else 2.5,
                        ),
                        marker=dict(
                            size=8 if key == "avg" else 7,
                            symbol=symbol,
                            color=color,
                            line=dict(color="white", width=1),
                        ),
                        hovertemplate=format_hover_template(
                            title=f"{forecast_type} Forecast",
                            fields={
                                "Date": "%{x|%Y-%m-%d}",
                                forecast_type: "%{y:.1f}",
                                "Type": hover_type,
                            },
                        ),
                        hoverlabel=create_hoverlabel_config(hover_style),
                        visible=True,
                    ),
                    secondary_y=secondary_y,
                )
                return True  # Return True to indicate success

            # Track if we've successfully added any forecasts
            items_forecasts_added = False
            points_forecasts_added = False

            # Items forecasts
            for key in ["avg", "opt", "pes"]:
                color = (
                    COLOR_PALETTE["items"]
                    if key == "avg"
                    else (
                        COLOR_PALETTE["optimistic"]
                        if key == "opt"
                        else COLOR_PALETTE["pessimistic"]
                    )
                )
                dash_style = "dash" if key == "avg" else "dot"
                symbol = (
                    "diamond"
                    if key == "avg"
                    else ("triangle-up" if key == "opt" else "triangle-down")
                )
                name = (
                    "Items Forecast (Most Likely)"
                    if key == "avg"
                    else (
                        "Items Forecast (Optimistic)"
                        if key == "opt"
                        else "Items Forecast (Pessimistic)"
                    )
                )
                hover_type = (
                    "Most Likely"
                    if key == "avg"
                    else ("Optimistic" if key == "opt" else "Pessimistic")
                )
                hover_style = (
                    "info"
                    if key == "avg"
                    else ("success" if key == "opt" else "warning")
                )

                if add_forecast_trace(
                    fig,
                    items_forecasts,
                    key,
                    "Items",
                    color,
                    dash_style,
                    symbol,
                    name,
                    hover_type,
                    hover_style,
                    False,  # Items are on primary y-axis
                ):
                    items_forecasts_added = True

            # Log results of forecast traces
            logger.info(f"Added items forecast traces: {items_forecasts_added}")

            # Points forecasts - only if show_points is True
            if show_points:
                for key in ["avg", "opt", "pes"]:
                    color = (
                        COLOR_PALETTE["points"]
                        if key == "avg"
                        else (
                            "rgb(184, 134, 11)" if key == "opt" else "rgb(165, 42, 42)"
                        )
                    )
                    dash_style = "dash" if key == "avg" else "dot"
                    symbol = (
                        "diamond"
                        if key == "avg"
                        else ("triangle-up" if key == "opt" else "triangle-down")
                    )
                    name = (
                        "Points Forecast (Most Likely)"
                        if key == "avg"
                        else (
                            "Points Forecast (Optimistic)"
                            if key == "opt"
                            else "Points Forecast (Pessimistic)"
                        )
                    )
                    hover_type = (
                        "Most Likely"
                        if key == "avg"
                        else ("Optimistic" if key == "opt" else "Pessimistic")
                    )
                    hover_style = (
                        "info"
                        if key == "avg"
                        else ("success" if key == "opt" else "warning")
                    )

                    if add_forecast_trace(
                        fig,
                        points_forecasts,
                        key,
                        "Points",
                        color,
                        dash_style,
                        symbol,
                        name,
                        hover_type,
                        hover_style,
                        True,  # Points are on secondary y-axis
                    ):
                        points_forecasts_added = True

                logger.info(f"Added points forecast traces: {points_forecasts_added}")

        # Add traces to figure - all visible by default
        fig.add_trace(completed_items_trace, secondary_y=False)
        fig.add_trace(scope_items_trace, secondary_y=False)

        # Only add points traces if points tracking is enabled
        if show_points:
            fig.add_trace(completed_points_trace, secondary_y=True)
            fig.add_trace(scope_points_trace, secondary_y=True)

        # Add deadline and milestone marker
        fig = add_deadline_marker(fig, deadline, milestone)

        # Calculate max value for y-axis range
        # Improve y-axis range calculation for points
        def safe_max(values):
            if not values or len(values) == 0:
                return 0
            return max(values)

        # Ensure we have appropriate room for the points forecast lines
        max_points_val = max(
            df["cum_scope_points"].max() if not df.empty else 0,
            safe_max(points_forecasts["avg"][1])
            if points_forecasts
            and "avg" in points_forecasts
            and len(points_forecasts["avg"]) > 1
            and points_forecasts["avg"][1]
            else 0,
            safe_max(points_forecasts["opt"][1])
            if points_forecasts
            and "opt" in points_forecasts
            and len(points_forecasts["opt"]) > 1
            and points_forecasts["opt"][1]
            else 0,
            safe_max(points_forecasts["pes"][1])
            if points_forecasts
            and "pes" in points_forecasts
            and len(points_forecasts["pes"]) > 1
            and points_forecasts["pes"][1]
            else 0,
        )

        # If still zero, use a reasonable default
        if max_points_val <= 0:
            max_points_val = max(10, completed_points_total * 1.5)
            logger.warning(
                f"Max points value was zero, using fallback: {max_points_val}"
            )

        # Calculate max items value for consistent scaling
        max_items_val = max(
            df["cum_scope_items"].max() if not df.empty else 0,
            safe_max(items_forecasts["avg"][1])
            if items_forecasts
            and "avg" in items_forecasts
            and len(items_forecasts["avg"]) > 1
            and items_forecasts["avg"][1]
            else 0,
            safe_max(items_forecasts["opt"][1])
            if items_forecasts
            and "opt" in items_forecasts
            and len(items_forecasts["opt"]) > 1
            and items_forecasts["opt"][1]
            else 0,
            safe_max(items_forecasts["pes"][1])
            if items_forecasts
            and "pes" in items_forecasts
            and len(items_forecasts["pes"]) > 1
            and items_forecasts["pes"][1]
            else 0,
        )

        # If still zero, use a reasonable default
        if max_items_val <= 0:
            max_items_val = max(10, completed_items_total * 1.5)

        # Configure x-axis consistently for all plots
        fig.update_xaxes(
            title={"text": "Date", "font": {"size": 16}},
            tickmode="auto",
            nticks=20,
            gridcolor="rgba(200, 200, 200, 0.2)",
            automargin=True,
            domain=[0, 1],  # Ensure x-axis spans the entire width
            rangeslider=dict(visible=False),  # Disable any potential rangeslider
            matches="x",  # Ensure x-axes match each other
        )

        # Calculate scale factor to align visually (same approach as in configure_axes)
        scale_factor = max_points_val / max_items_val if max_items_val > 0 else 1

        # Set y-axis ranges to maintain alignment
        items_range = [0, max_items_val * 1.1]
        points_range = [0, max_items_val * scale_factor * 1.1]

        # Configure primary y-axis (items) with items grid color
        fig.update_yaxes(
            title={"text": "Items", "font": {"size": 16}},
            gridcolor=COLOR_PALETTE["items_grid"],
            zeroline=True,
            zerolinecolor="black",
            secondary_y=False,
            range=items_range,  # Set explicit range for better visual alignment
            side="left",
        )

        # Configure secondary y-axis (points) with points grid color - only if points tracking is enabled
        if show_points:
            fig.update_yaxes(
                title={"text": "Points", "font": {"size": 16}},
                gridcolor=COLOR_PALETTE["points_grid"],
                zeroline=True,
                zerolinecolor="black",
                secondary_y=True,
                range=points_range,  # Set explicit range for better visual alignment
                side="right",
                anchor="x",  # Anchor to the x-axis to keep alignment
            )

        # Apply consistent layout settings to match burndown chart
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=12),
            ),
            hovermode=hover_mode,  # Use the passed hover_mode parameter for consistent behavior
            margin=dict(l=60, r=60, t=80, b=50),  # Match burndown chart margins
            height=700,
            template="plotly_white",
            plot_bgcolor="white",  # Match burndown chart background
            uirevision="true",  # Keep UI state consistent
        )

        # Calculate PERT time estimates for the metrics
        current_date = datetime.now()
        days_to_deadline = max(0, (deadline - pd.Timestamp(current_date)).days)
        pert_time_items = forecast_data.get("pert_time_items", 0.0)
        pert_time_points = forecast_data.get("pert_time_points", 0.0)

        # Calculate enhanced completion date strings
        items_completion_date = current_date + timedelta(days=pert_time_items)
        points_completion_date = current_date + timedelta(days=pert_time_points)

        items_completion_str = items_completion_date.strftime("%Y-%m-%d")
        points_completion_str = points_completion_date.strftime("%Y-%m-%d")

        items_completion_enhanced = f"{items_completion_str} ({pert_time_items:.1f} days, {pert_time_items / 7:.1f} weeks)"
        points_completion_enhanced = f"{points_completion_str} ({pert_time_points:.1f} days, {pert_time_points / 7:.1f} weeks)"

        # Calculate average and median weekly metrics for display
        avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
            0.0,
            0.0,
            0.0,
            0.0,
        )
        if not df.empty:
            # Get all four values from calculate_weekly_averages
            results = calculate_weekly_averages(df.to_dict("records"))
            if isinstance(results, (list, tuple)) and len(results) >= 4:
                (
                    avg_weekly_items,
                    avg_weekly_points,
                    med_weekly_items,
                    med_weekly_points,
                ) = results

        # Add metrics data to the plot - same as burndown chart
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

            # Add metrics annotations in the same position as the burndown chart
            fig = add_metrics_annotations(fig, metrics_data)
        except Exception as metrics_error:
            # Log the error but continue without metrics
            logger = logging.getLogger("burndown_chart")
            logger.error(
                f"Error preparing burnup metrics data: {str(metrics_error)}\n{traceback.format_exc()}"
            )

            # Create minimal metrics data with default values
            metrics_data = {
                "total_items": total_items,
                "total_points": total_points,
                "total_scope_items": completed_items_total + total_items,
                "total_scope_points": completed_points_total + total_points,
                "completed_items": completed_items_total,
                "completed_points": completed_points_total,
                "deadline": deadline.strftime("%Y-%m-%d")
                if hasattr(deadline, "strftime")
                else "Unknown",
                "days_to_deadline": days_to_deadline,
                "avg_weekly_items": float(avg_weekly_items),
                "avg_weekly_points": float(avg_weekly_points),
                "med_weekly_items": float(med_weekly_items),
                "med_weekly_points": float(med_weekly_points),
            }

            # Try to add metrics with the minimal data
            try:
                fig = add_metrics_annotations(fig, metrics_data)
            except Exception:
                # If even this fails, just continue without metrics
                pass

        # Return more comprehensive data for dashboard metrics
        return (
            fig,
            {
                "baseline_items": 0,  # No baseline scope calculation needed
                "baseline_points": 0,  # No baseline scope calculation needed
                "current_scope_items": metrics_data[
                    "total_scope_items"
                ],  # Use consistent scope values
                "current_scope_points": metrics_data[
                    "total_scope_points"
                ],  # Use consistent scope values
                "completed_items": df["cum_completed_items"].iloc[-1]
                if not df.empty
                else 0,
                "completed_points": df["cum_completed_points"].iloc[-1]
                if not df.empty
                else 0,
                "pert_time_items": pert_time_items,
                "pert_time_points": pert_time_points,
                "days_to_deadline": days_to_deadline,
                "avg_weekly_items": float(
                    avg_weekly_items
                ),  # Explicitly ensure float value (no rounding)
                "avg_weekly_points": float(
                    avg_weekly_points
                ),  # Explicitly ensure float value (no rounding)
                "med_weekly_items": float(med_weekly_items),  # Also keep as float
                "med_weekly_points": float(med_weekly_points),  # Also keep as float
                "items_completion_enhanced": items_completion_enhanced,
                "points_completion_enhanced": points_completion_enhanced,
            },
        )

    except Exception as e:
        # Comprehensive error handling with full stack trace
        error_trace = traceback.format_exc()
        logger = logging.getLogger("burndown_chart")
        logger.error(f"Error in create_burnup_chart: {str(e)}\n{error_trace}")

        # Create an empty figure with error message
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error in burnup chart generation:<br>{str(e)}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="red"),
        )

        # Add button to show/hide detailed error info to match burndown chart
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
                                            "text": f"Error in burnup chart generation:<br>{str(e)}<br><br>Stack trace (for developers):<br>{error_trace.replace(chr(10), '<br>')}",
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

        return fig, {}


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
    # Import needed functions from data module
    from data.processing import (
        daily_forecast_burnup,
        compute_weekly_throughput,
        calculate_rates,
    )

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

        # Create remaining work columns for burndown charts
        # These will start at total scope and decrease with each data point
        remaining_items = [total_scope_items]
        remaining_points = [total_scope_points]

        for i in range(1, len(df_calc)):
            # Subtract completed work in this period
            items_completed_in_period = (
                df_calc["completed_items"].iloc[i]
                if "completed_items" in df_calc.columns
                else 0
            )
            points_completed_in_period = (
                df_calc["completed_points"].iloc[i]
                if "completed_points" in df_calc.columns
                else 0
            )

            remaining_items.append(remaining_items[-1] - items_completed_in_period)
            remaining_points.append(remaining_points[-1] - points_completed_in_period)

        # Update the dataframe with the correct remaining work columns
        df_calc["cum_items"] = remaining_items
        df_calc["cum_points"] = remaining_points

    # Filter to use only the specified number of most recent data points
    if (
        data_points_count is not None
        and data_points_count > 0
        and len(df_calc) > data_points_count
    ):
        # Get the most recent data_points_count rows
        df_calc = df_calc.iloc[-data_points_count:]

    # Compute weekly throughput and rates with the filtered data
    grouped = compute_weekly_throughput(df_calc)
    rates = calculate_rates(
        grouped, total_items, total_points, pert_factor, show_points
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

    # For burndown charts, make sure max values include total scope
    if not is_burnup:
        max_items = max(max_items, total_scope_items)
        max_points = max(max_points, total_scope_points)

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
    current_date = datetime.now()

    # Generate the enhanced formatted strings
    items_completion_date = current_date + timedelta(days=pert_time_items)
    points_completion_date = current_date + timedelta(days=pert_time_points)

    items_completion_str = items_completion_date.strftime("%Y-%m-%d")
    points_completion_str = points_completion_date.strftime("%Y-%m-%d")

    items_completion_enhanced = f"{items_completion_str} ({pert_time_items:.1f} days, {pert_time_items / 7:.1f} weeks)"
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
    days_to_deadline = max(0, (deadline - pd.Timestamp(current_date)).days)

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
        "deadline": deadline.strftime("%Y-%m-%d"),
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
