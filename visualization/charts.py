"""
Visualization Charts Module

This module contains functions to create and customize the forecast chart
with all its components like traces, markers, and metrics annotations.
"""

#######################################################################
# IMPORTS
#######################################################################
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime

# Import from other modules
from config import COLOR_PALETTE
from data.processing import (
    prepare_forecast_data,
    calculate_weekly_averages,
)

#######################################################################
# CHART CREATION FUNCTIONS
#######################################################################


def create_plot_traces(forecast_data):
    """
    Create all the traces for the plot.

    Args:
        forecast_data: Dictionary of forecast data from prepare_forecast_data

    Returns:
        List of traces for Plotly figure
    """
    df_calc = forecast_data["df_calc"]
    items_forecasts = forecast_data["items_forecasts"]
    points_forecasts = forecast_data["points_forecasts"]

    traces = []

    # Historical items trace
    traces.append(
        {
            "data": go.Scatter(
                x=df_calc["date"],
                y=df_calc["cum_items"],
                mode="lines+markers",
                name="Items History",
                line=dict(color=COLOR_PALETTE["items"], width=3),
                marker=dict(size=8, color=COLOR_PALETTE["items"]),
                hovertemplate="%{x}<br>Items: %{y}",
            ),
            "secondary_y": False,
        }
    )

    # Items forecast traces
    traces.append(
        {
            "data": go.Scatter(
                x=items_forecasts["avg"][0],
                y=items_forecasts["avg"][1],
                mode="lines",
                name="Items Forecast (Most Likely)",
                line=dict(color=COLOR_PALETTE["items"], dash="dash", width=2),
                hovertemplate="%{x}<br>Items: %{y}",
            ),
            "secondary_y": False,
        }
    )

    traces.append(
        {
            "data": go.Scatter(
                x=items_forecasts["opt"][0],
                y=items_forecasts["opt"][1],
                mode="lines",
                name="Items Forecast (Optimistic)",
                line=dict(color=COLOR_PALETTE["optimistic"], dash="dot", width=2),
                hovertemplate="%{x}<br>Items: %{y}",
            ),
            "secondary_y": False,
        }
    )

    traces.append(
        {
            "data": go.Scatter(
                x=items_forecasts["pes"][0],
                y=items_forecasts["pes"][1],
                mode="lines",
                name="Items Forecast (Pessimistic)",
                line=dict(color=COLOR_PALETTE["pessimistic"], dash="dot", width=2),
                hovertemplate="%{x}<br>Items: %{y}",
            ),
            "secondary_y": False,
        }
    )

    # Historical points trace
    traces.append(
        {
            "data": go.Scatter(
                x=df_calc["date"],
                y=df_calc["cum_points"],
                mode="lines+markers",
                name="Points History",
                line=dict(color=COLOR_PALETTE["points"], width=3),
                marker=dict(size=8, color=COLOR_PALETTE["points"]),
                hovertemplate="%{x}<br>Points: %{y}",
            ),
            "secondary_y": True,
        }
    )

    # Points forecast traces
    traces.append(
        {
            "data": go.Scatter(
                x=points_forecasts["avg"][0],
                y=points_forecasts["avg"][1],
                mode="lines",
                name="Points Forecast (Most Likely)",
                line=dict(color=COLOR_PALETTE["points"], dash="dash", width=2),
                hovertemplate="%{x}<br>Points: %{y}",
            ),
            "secondary_y": True,
        }
    )

    traces.append(
        {
            "data": go.Scatter(
                x=points_forecasts["opt"][0],
                y=points_forecasts["opt"][1],
                mode="lines",
                name="Points Forecast (Optimistic)",
                line=dict(color="rgb(184, 134, 11)", dash="dot", width=2),
                hovertemplate="%{x}<br>Points: %{y}",
            ),
            "secondary_y": True,
        }
    )

    traces.append(
        {
            "data": go.Scatter(
                x=points_forecasts["pes"][0],
                y=points_forecasts["pes"][1],
                mode="lines",
                name="Points Forecast (Pessimistic)",
                line=dict(color="rgb(165, 42, 42)", dash="dot", width=2),
                hovertemplate="%{x}<br>Points: %{y}",
            ),
            "secondary_y": True,
        }
    )

    return traces


def add_deadline_marker(fig, deadline):
    """
    Add deadline marker line and annotation to the figure.

    Args:
        fig: Plotly figure object
        deadline: Deadline date (datetime object)

    Returns:
        Updated figure with deadline marker
    """
    # Add vertical line at deadline
    fig.add_shape(
        type="line",
        x0=deadline,
        x1=deadline,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color=COLOR_PALETTE["deadline"], dash="dash", width=3),
    )

    # Add deadline annotation
    fig.add_annotation(
        x=deadline,
        y=1,
        yref="paper",
        text="Deadline",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-40,
        font=dict(color=COLOR_PALETTE["deadline"], size=14, family="Arial, sans-serif"),
    )

    return fig


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
    """
    Apply final layout settings to the figure.

    Args:
        fig: Plotly figure object

    Returns:
        Figure with finalized layout settings
    """
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.0,
            xanchor="center",
            x=0.5,
            font={"size": 12},
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="lightgray",
            borderwidth=1,
        ),
        hovermode="closest",
        margin=dict(r=70, l=70, t=80, b=70),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font={"family": "Arial, sans-serif"},
    )

    return fig


def add_metrics_annotations(fig, metrics_data):
    """
    Add metrics as annotations below the x-axis of the plot.

    Args:
        fig: Plotly figure object
        metrics_data: Dictionary with metrics to display

    Returns:
        Updated figure with metrics annotations
    """
    # Define styles for metrics display
    base_y_position = -0.2  # Starting position below x-axis
    font_color = "#505050"
    title_font_size = 16
    value_font_size = 14

    # Create background shape for metrics area
    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=0,
        y0=base_y_position - 0.13,  # Background bottom position
        x1=1,
        y1=base_y_position + 0.03,  # Background top position
        fillcolor="rgba(245, 245, 245, 0.8)",
        line=dict(color="rgba(200, 200, 200, 0.5)", width=1),
    )

    # Create a title for the metrics section
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.02,  # Left aligned
        y=base_y_position + 0.04,  # Position at the top of the metrics area
        text="<b>Project Metrics</b>",
        showarrow=False,
        font=dict(size=title_font_size, color=font_color, family="Arial, sans-serif"),
        align="left",
    )

    # Define the metrics to display in columns
    metrics_columns = [
        [
            {
                "label": "Total Items",
                "value": metrics_data["total_items"],
                "format": "{:,}",
            },
            {
                "label": "Total Points",
                "value": metrics_data["total_points"],
                "format": "{:,.0f}",
            },
        ],
        [
            {"label": "Deadline", "value": metrics_data["deadline"], "format": "{}"},
            {
                "label": "Deadline in",
                "value": metrics_data["days_to_deadline"],
                "format": "{:,} days",
            },
        ],
        [
            {
                "label": "Est. Days (Items)",
                "value": metrics_data["pert_time_items"],
                "format": "{:.1f} days",
            },
            {
                "label": "Est. Days (Points)",
                "value": metrics_data["pert_time_points"],
                "format": "{:.1f} days",
            },
        ],
        [
            {
                "label": "Avg Weekly Items (10W)",
                "value": metrics_data["avg_weekly_items"],
                "format": "{:.1f}",
            },
            {
                "label": "Avg Weekly Points (10W)",
                "value": metrics_data["avg_weekly_points"],
                "format": "{:.1f}",
            },
        ],
        [
            {
                "label": "Med Weekly Items (10W)",
                "value": metrics_data["med_weekly_items"],
                "format": "{:.1f}",
            },
            {
                "label": "Med Weekly Points (10W)",
                "value": metrics_data["med_weekly_points"],
                "format": "{:.1f}",
            },
        ],
    ]

    # Calculate column positions with better spacing
    # Use fixed positions rather than relative calculations to ensure consistent spacing
    column_positions = [0.02, 0.21, 0.40, 0.60, 0.80]  # Left position of each column

    # Add metrics to the figure - ensure all are left-aligned
    for col_idx, column in enumerate(metrics_columns):
        x_pos = column_positions[col_idx]  # Use fixed position for consistent spacing

        for row_idx, metric in enumerate(column):
            # Spacing between rows
            y_offset = -0.05 - 0.05 * row_idx
            y_pos = base_y_position + y_offset

            # Format the label and value
            formatted_value = metric["format"].format(metric["value"])

            # Color for estimated days
            text_color = font_color
            if "Est. Days" in metric["label"]:
                if (
                    "Items" in metric["label"]
                    and metrics_data["pert_time_items"]
                    > metrics_data["days_to_deadline"]
                ):
                    text_color = "red"
                elif (
                    "Points" in metric["label"]
                    and metrics_data["pert_time_points"]
                    > metrics_data["days_to_deadline"]
                ):
                    text_color = "red"

            # Add the metric to the figure with explicit left alignment for all columns
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
                xanchor="left",  # Explicitly set left anchor for text alignment
            )

    # Update the figure margin to accommodate the metrics area
    fig.update_layout(
        margin=dict(b=180)  # Increase bottom margin to make room for added metrics
    )

    return fig


def create_forecast_plot(df, total_items, total_points, pert_factor, deadline_str):
    """
    Create the complete forecast plot with all components.

    Args:
        df: DataFrame with historical data
        total_items: Total number of items to complete
        total_points: Total number of points to complete
        pert_factor: PERT factor for calculations
        deadline_str: Deadline date as string (YYYY-MM-DD)

    Returns:
        Tuple of (figure, pert_time_items, pert_time_points)
    """
    # Ensure proper date format for deadline
    deadline = pd.to_datetime(deadline_str)

    # Prepare all data needed for the visualization
    forecast_data = prepare_forecast_data(df, total_items, total_points, pert_factor)

    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add all traces to the figure
    traces = create_plot_traces(forecast_data)
    for trace in traces:
        fig.add_trace(trace["data"], secondary_y=trace["secondary_y"])

    # Add deadline marker and configure axes
    fig = add_deadline_marker(fig, deadline)
    fig = configure_axes(fig, forecast_data)
    fig = apply_layout_settings(fig)

    # Calculate days to deadline for metrics
    current_date = datetime.now()
    days_to_deadline = max(0, (deadline - current_date).days)

    # Calculate average and median weekly metrics for display
    avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
        0,
        0,
        0,
        0,
    )
    if not df.empty:
        # Get all four values from calculate_weekly_averages
        avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
            calculate_weekly_averages(df.to_dict("records"))
        )

    # Add metrics data to the plot
    metrics_data = {
        "total_items": total_items,
        "total_points": total_points,
        "deadline": deadline.strftime("%Y-%m-%d"),
        "days_to_deadline": days_to_deadline,
        "pert_time_items": forecast_data["pert_time_items"],
        "pert_time_points": forecast_data["pert_time_points"],
        "avg_weekly_items": avg_weekly_items,
        "avg_weekly_points": avg_weekly_points,
        "med_weekly_items": med_weekly_items,
        "med_weekly_points": med_weekly_points,
    }

    fig = add_metrics_annotations(fig, metrics_data)

    return fig, forecast_data["pert_time_items"], forecast_data["pert_time_points"]
