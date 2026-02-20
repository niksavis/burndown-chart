"""
Forecast Chart Module

This module contains functions specifically for creating and configuring
forecast plots with traces, axes, layouts, and annotations.

Split from visualization/charts.py to maintain manageable file sizes
following architectural guidelines (Python: 500 line limit).
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import logging
from datetime import datetime

# Third-party library imports
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Application imports
from configuration import COLOR_PALETTE
from ui.tooltip_utils import create_hoverlabel_config, format_hover_template
from visualization.elements import create_empty_figure
from visualization.helpers import (
    get_weekly_metrics,
    handle_forecast_error,
    parse_deadline_milestone,
    safe_numeric_convert,
)

#######################################################################
# FORECAST CHART FUNCTIONS
#######################################################################


def create_plot_traces(
    forecast_data, show_forecast=True, forecast_visibility=True, show_points=True
):
    """
    Create all the traces for the plot.

    Args:
        forecast_data: Dictionary of forecast data from prepare_forecast_data
        show_forecast: Whether to show forecast lines (default: True)
        forecast_visibility: Visibility mode for forecast traces
            - True, False, or "legendonly" (default: "legendonly")
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
                mode="lines+markers",  # Added markers for better visibility
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

    if items_forecasts.get("ewma", ([], []))[0]:
        traces.append(
            {
                "data": go.Scatter(
                    x=items_forecasts["ewma"][0],
                    y=items_forecasts["ewma"][1],
                    mode="lines+markers",
                    name="Items Forecast (EWMA)",
                    line=dict(color="#6b7c93", dash="dashdot", width=2.0),
                    marker=dict(
                        size=7,
                        symbol="diamond",
                        color="#6b7c93",
                        line=dict(color="white", width=1),
                    ),
                    hovertemplate=format_hover_template(
                        title="Items Forecast",
                        fields={
                            "Date": "%{x|%Y-%m-%d}",
                            "Items": "%{y:.1f}",
                            "Type": "EWMA",
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

        if points_forecasts.get("ewma", ([], []))[0]:
            traces.append(
                {
                    "data": go.Scatter(
                        x=points_forecasts["ewma"][0],
                        y=points_forecasts["ewma"][1],
                        mode="lines+markers",
                        name="Points Forecast (EWMA)",
                        line=dict(color="#8a6d3b", dash="dashdot", width=2.0),
                        marker=dict(
                            size=7,
                            symbol="diamond",
                            color="#8a6d3b",
                            line=dict(color="white", width=1),
                        ),
                        hovertemplate=format_hover_template(
                            title="Points Forecast",
                            fields={
                                "Date": "%{x|%Y-%m-%d}",
                                "Points": "%{y:.1f}",
                                "Type": "EWMA",
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

        # Use brown color for pessimistic points forecast
        # (matching info card description)
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
        tickformat="%Y-W%V",  # ISO week format (2026-W07)
        gridcolor="rgba(200, 200, 200, 0.2)",
        automargin=True,
        tickangle=45,  # Consistent 45° rotation (right tilt)
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
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            itemclick="toggle",
            itemdoubleclick=False,
        ),
        # Changed from "closest" to "x unified" for vertical guideline
        hovermode="x unified",
        margin=dict(l=60, r=60, t=80, b=50),
        height=700,
        template="plotly_white",
    )
    return fig


def add_metrics_annotations(fig, metrics_data, data_points_count=None):
    """
    Add metrics as annotations below the x-axis of the plot.

    Organized for responsive display on various screen sizes
    with more consistent spacing.

    Args:
        fig: Plotly figure object
        metrics_data: Dictionary with metrics to display
        data_points_count: Number of data points used
            for velocity calculations (for label display)

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

    # Additional check: if total_scope_points == total_points,
    # it suggests no historical data
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

    # Add a light red shaded region for the critical period
    # (last 14 days before deadline)
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
        forecast_visibility: Visibility mode for forecast traces
            ("legendonly", True, False)
        hover_mode: Hover mode for the plot ("x unified", "closest", etc.)
        show_points: Whether points tracking is enabled (default: True)

    Returns:
        Tuple of (figure, pert_data_dict) where pert_data_dict
        contains all PERT forecast information
    """
    # Import helper functions (to avoid circular dependency)
    from visualization.charts import (
        _calculate_forecast_completion_dates,
        _prepare_metrics_data,
    )
    from visualization.data_preparation import prepare_visualization_data

    try:
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
        total_items = safe_numeric_convert(total_items, default=0.0)
        total_points = safe_numeric_convert(total_points, default=0.0)
        pert_factor = int(safe_numeric_convert(pert_factor, default=3.0))

        # Parse deadline and milestone dates
        deadline, milestone = parse_deadline_milestone(deadline_str, milestone_str)

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

        df_calc = forecast_data.get("df_calc")
        if df_calc is None or df_calc.empty or "date" not in df_calc.columns:
            fig = create_empty_figure("No data available for forecast")
            pert_data = {
                "pert_time_items": 0.0,
                "pert_time_points": 0.0,
                "items_completion_enhanced": "Unknown",
                "points_completion_enhanced": "Unknown",
                "days_to_deadline": 0,
                "avg_weekly_items": 0.0,
                "avg_weekly_points": 0.0,
                "med_weekly_items": 0.0,
                "med_weekly_points": 0.0,
                "forecast_timestamp": datetime.now().isoformat(),
                "velocity_cv": 0.0,
                "schedule_variance_days": 0.0,
            }
            return fig, pert_data

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
                # Set visibility for all forecast traces
                # based on forecast_visibility parameter
                if is_forecast:
                    trace["data"].visible = forecast_visibility

                fig.add_trace(trace["data"], secondary_y=trace["secondary_y"])

        # Add deadline marker and configure axes
        fig = add_deadline_marker(fig, deadline, milestone)
        fig = configure_axes(fig, forecast_data)

        # Apply layout settings with the specified hover_mode
        # Increased top margin from 80 to 100px
        # to accommodate legend (y=1.06) and toolbar without overlap
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.06,
                xanchor="center",
                x=0.5,
                itemclick="toggle",
                itemdoubleclick=False,
            ),
            hovermode=hover_mode,
            margin=dict(l=60, r=60, t=100, b=50),
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
            get_weekly_metrics(df, data_points_count)
        )

        # Calculate enhanced formatted strings for PERT estimates
        pert_time_items = forecast_data.get("pert_time_items", 0.0)
        pert_time_points = forecast_data.get("pert_time_points", 0.0)

        # Ensure valid numbers for PERT times
        pert_time_items = safe_numeric_convert(pert_time_items, default=0.0)
        pert_time_points = safe_numeric_convert(pert_time_points, default=0.0)

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
        return handle_forecast_error(e)
