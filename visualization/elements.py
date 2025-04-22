"""
Visualization Elements Module

This module provides low-level chart components like individual traces, axes configuration,
markers, and styling elements used to build the complete forecast visualization.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
# None

# Third-party library imports
import plotly.graph_objects as go

# Application imports
from configuration import COLOR_PALETTE
from ui.styles import create_hoverlabel_config, format_hover_template

#######################################################################
# EMPTY FIGURE FUNCTION
#######################################################################


def empty_figure(message="No data available"):
    """
    Create an empty figure with a message.

    Args:
        message: Message to display in the empty figure

    Returns:
        Plotly figure object with the message
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="#505050"),
    )
    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, showticklabels=False),
        plot_bgcolor="rgba(240, 240, 240, 0.1)",
        height=400,
    )
    return fig


#######################################################################
# TRACE CREATION FUNCTIONS
#######################################################################


def create_historical_trace(df, column_name, name, color, secondary_y=False):
    """
    Create a historical data trace with appropriate styling.

    Args:
        df: DataFrame with historical data
        column_name: Column name to plot
        name: Display name for the trace
        color: Color to use for the trace
        secondary_y: Whether this trace uses the secondary y-axis

    Returns:
        Dictionary with trace data and axis specification
    """
    return {
        "data": go.Scatter(
            x=df["date"],
            y=df[column_name],
            mode="lines+markers",
            name=name,
            line=dict(color=color, width=3),
            marker=dict(size=8, color=color),
            hovertemplate=format_hover_template(
                title=name,
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    name.split()[0]: "%{y}",
                },
                extra_info=name.split()[0],
            ),
            hoverlabel=create_hoverlabel_config("default"),
        ),
        "secondary_y": secondary_y,
    }


def create_forecast_trace(
    x_vals, y_vals, name, color, dash_style="dash", secondary_y=False
):
    """
    Create a forecast trace with appropriate styling.

    Args:
        x_vals: X-axis values (dates)
        y_vals: Y-axis values (forecast values)
        name: Display name for the trace
        color: Color to use for the trace
        dash_style: Line dash style ("dash", "dot", etc.)
        secondary_y: Whether this trace uses the secondary y-axis

    Returns:
        Dictionary with trace data and axis specification
    """
    # Determine tooltip variant based on name
    variant = "default"
    if "Optimistic" in name:
        variant = "success"
    elif "Pessimistic" in name:
        variant = "warning"
    elif "Most Likely" in name or "Average" in name:
        variant = "info"

    # Extract type from the name (e.g. "Items Forecast (Optimistic)" -> "Optimistic")
    forecast_type = name.split("(")[-1].strip(")") if "(" in name else "Forecast"
    data_type = "Items" if "Items" in name else "Points"

    return {
        "data": go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines",
            name=name,
            line=dict(color=color, dash=dash_style, width=2),
            hovertemplate=format_hover_template(
                title=f"{data_type} Forecast",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    data_type: "%{y:.1f}",
                    "Type": forecast_type,
                },
            ),
            hoverlabel=create_hoverlabel_config(variant),
        ),
        "secondary_y": secondary_y,
    }


def create_items_traces(df_calc, items_forecasts):
    """
    Create all traces related to items (historical and forecasts).

    Args:
        df_calc: DataFrame with calculated historical data
        items_forecasts: Dictionary with forecast data for items

    Returns:
        List of trace dictionaries
    """
    traces = []

    # Historical items trace
    traces.append(
        create_historical_trace(
            df_calc, "cum_items", "Items History", COLOR_PALETTE["items"], False
        )
    )

    # Most likely forecast trace
    traces.append(
        create_forecast_trace(
            items_forecasts["avg"][0],
            items_forecasts["avg"][1],
            "Items Forecast (Most Likely)",
            COLOR_PALETTE["items"],
            "dash",
            False,
        )
    )

    # Optimistic forecast trace
    traces.append(
        create_forecast_trace(
            items_forecasts["opt"][0],
            items_forecasts["opt"][1],
            "Items Forecast (Optimistic)",
            COLOR_PALETTE["optimistic"],
            "dot",
            False,
        )
    )

    # Pessimistic forecast trace
    traces.append(
        create_forecast_trace(
            items_forecasts["pes"][0],
            items_forecasts["pes"][1],
            "Items Forecast (Pessimistic)",
            COLOR_PALETTE["pessimistic"],
            "dot",
            False,
        )
    )

    return traces


def create_points_traces(df_calc, points_forecasts):
    """
    Create all traces related to points (historical and forecasts).

    Args:
        df_calc: DataFrame with calculated historical data
        points_forecasts: Dictionary with forecast data for points

    Returns:
        List of trace dictionaries
    """
    traces = []

    # Historical points trace
    traces.append(
        create_historical_trace(
            df_calc, "cum_points", "Points History", COLOR_PALETTE["points"], True
        )
    )

    # Most likely forecast trace
    traces.append(
        create_forecast_trace(
            points_forecasts["avg"][0],
            points_forecasts["avg"][1],
            "Points Forecast (Most Likely)",
            COLOR_PALETTE["points"],
            "dash",
            True,
        )
    )

    # Optimistic forecast trace
    traces.append(
        create_forecast_trace(
            points_forecasts["opt"][0],
            points_forecasts["opt"][1],
            "Points Forecast (Optimistic)",
            "rgb(184, 134, 11)",  # Gold color for optimistic points
            "dot",
            True,
        )
    )

    # Pessimistic forecast trace
    traces.append(
        create_forecast_trace(
            points_forecasts["pes"][0],
            points_forecasts["pes"][1],
            "Points Forecast (Pessimistic)",
            "rgb(165, 42, 42)",  # Brown color for pessimistic points
            "dot",
            True,
        )
    )

    return traces


#######################################################################
# AXIS CONFIGURATION FUNCTIONS
#######################################################################


def configure_x_axis(fig):
    """
    Configure the x-axis with consistent styling.

    Args:
        fig: Plotly figure object

    Returns:
        Updated figure object
    """
    fig.update_xaxes(
        title={"text": "Date", "font": {"size": 16}},
        tickmode="auto",
        nticks=20,
        gridcolor="rgba(200, 200, 200, 0.2)",
        automargin=True,
    )
    return fig


def configure_y_axes(fig, items_range, points_range):
    """
    Configure the primary and secondary y-axes with consistent styling.

    Args:
        fig: Plotly figure object
        items_range: Range values for the items axis
        points_range: Range values for the points axis

    Returns:
        Updated figure object
    """
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


def calculate_axis_ranges(max_items, max_points):
    """
    Calculate appropriate ranges for the y-axes to maintain visual alignment.

    Args:
        max_items: Maximum value for the items axis
        max_points: Maximum value for the points axis

    Returns:
        Tuple of (items_range, points_range)
    """
    # Calculate scale factor to align visually
    scale_factor = max_points / max_items if max_items > 0 else 1

    # Set y-axis ranges to maintain alignment
    items_range = [0, max_items * 1.1]
    points_range = [0, max_items * scale_factor * 1.1]

    return items_range, points_range


#######################################################################
# MARKER AND ANNOTATION FUNCTIONS
#######################################################################


def add_deadline_marker(fig, deadline_date):
    """
    Add a vertical line and annotation for the deadline.

    Args:
        fig: Plotly figure object
        deadline_date: Deadline date as a datetime object

    Returns:
        Updated figure object
    """
    # Add vertical line at deadline
    fig.add_shape(
        type="rect",
        x0=deadline_date,
        x1=deadline_date,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(
            color=COLOR_PALETTE["deadline"],
            dash="dash",
            width=3,
        ),
        fillcolor="rgba(0,0,0,0)",
    )

    # Add deadline annotation
    fig.add_annotation(
        x=deadline_date,
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


def create_metrics_background(fig, y_position=-0.2):
    """
    Create the background rectangle for the metrics section.

    Args:
        fig: Plotly figure object
        y_position: Base y position for the metrics area

    Returns:
        Updated figure object
    """
    fig.add_shape(
        type="rect",
        xref="paper",
        yref="paper",
        x0=0,
        y0=y_position - 0.13,  # Background bottom position
        x1=1,
        y1=y_position + 0.03,  # Background top position
        fillcolor="rgba(245, 245, 245, 0.8)",
        line=dict(color="rgba(200, 200, 200, 0.5)", width=1),
    )

    return fig


def add_metric_annotation(
    fig,
    x_pos,
    y_pos,
    label,
    value,
    format_str,
    is_estimate=False,
    estimate_value=None,
    deadline_days=None,
):
    """
    Add a single metric annotation to the figure.

    Args:
        fig: Plotly figure object
        x_pos: X position (paper coordinates)
        y_pos: Y position (paper coordinates)
        label: Label for the metric
        value: Value of the metric
        format_str: Format string for the value
        is_estimate: Whether this is an estimate that should be color-coded
        estimate_value: Value of the estimate (used for color coding)
        deadline_days: Days to deadline (used for color coding)

    Returns:
        Updated figure object
    """
    # Format the value according to the format string
    formatted_value = format_str.format(value)

    # Default text color
    text_color = "#505050"

    # Color coding for estimates
    if is_estimate and estimate_value is not None and deadline_days is not None:
        if estimate_value > deadline_days:
            text_color = "red"  # At risk of missing deadline

    # Add the annotation
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=x_pos,
        y=y_pos,
        text=f"<b>{label}:</b> {formatted_value}",
        showarrow=False,
        font=dict(size=14, color=text_color, family="Arial, sans-serif"),
        align="left",
        xanchor="left",
    )

    return fig


#######################################################################
# LAYOUT STYLING FUNCTIONS
#######################################################################


def apply_legend_styling(fig):
    """
    Apply consistent styling to the figure legend.

    Args:
        fig: Plotly figure object

    Returns:
        Updated figure object
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
    )
    return fig


def apply_base_layout_styling(fig):
    """
    Apply base layout styling to the figure.

    Args:
        fig: Plotly figure object

    Returns:
        Updated figure object
    """
    fig.update_layout(
        hovermode="closest",
        margin=dict(r=70, l=70, t=80, b=70),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font={"family": "Arial, sans-serif"},
    )
    return fig


def adjust_margins_for_metrics(fig, bottom_margin=180):
    """
    Adjust the figure margins to accommodate the metrics area.

    Args:
        fig: Plotly figure object
        bottom_margin: Bottom margin in pixels

    Returns:
        Updated figure object
    """
    fig.update_layout(margin=dict(b=bottom_margin))
    return fig
