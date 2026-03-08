"""Forecast chart layout, axes, annotations, and deadline markers.

Configures axis scales, legend, hover settings, metrics annotation grid,
and deadline/milestone vertical markers.
Part of visualization/forecast_chart.py split.
"""

import pandas as pd

from configuration import COLOR_PALETTE


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
