"""Mini trend visualization components for metric cards.

Creates compact sparkline charts to show weekly trends inline with metric values.
"""

import plotly.graph_objects as go
from typing import List, Optional, Dict, Any
from dash import dcc


def create_metric_trend_sparkline(
    week_labels: List[str],
    values: List[float],
    metric_name: str,
    unit: str = "",
    height: int = 80,
    show_axes: bool = False,
    color: str = "#1f77b4",
) -> dcc.Graph:
    """
    Create a compact sparkline chart for metric trends.

    Args:
        week_labels: List of week labels (e.g., ["2025-W43", "2025-W44", ...])
        values: List of metric values corresponding to each week
        metric_name: Name of the metric (for accessibility)
        unit: Unit of measurement (for tooltip)
        height: Height of chart in pixels (default: 80)
        show_axes: Whether to show axis labels (default: False for sparkline)
        color: Line color (default: blue)

    Returns:
        Dash Graph component with sparkline visualization

    Example:
        >>> week_labels = ["2025-W40", "2025-W41", "2025-W42", "2025-W43"]
        >>> values = [12, 15, 14, 18]
        >>> sparkline = create_metric_trend_sparkline(
        ...     week_labels, values, "Deployment Frequency", "deployments"
        ... )
    """
    # Handle empty data
    if not week_labels or not values:
        return dcc.Graph(
            figure={
                "data": [],
                "layout": {
                    "height": height,
                    "margin": {"t": 0, "r": 0, "b": 0, "l": 0},
                    "xaxis": {"visible": False},
                    "yaxis": {"visible": False},
                    "annotations": [
                        {
                            "text": "No trend data available",
                            "xref": "paper",
                            "yref": "paper",
                            "x": 0.5,
                            "y": 0.5,
                            "showarrow": False,
                            "font": {"size": 10, "color": "#999"},
                        }
                    ],
                },
            },
            config={"displayModeBar": False},
            style={"height": f"{height}px"},
        )

    # Create sparkline trace
    trace = go.Scatter(
        x=week_labels,
        y=values,
        mode="lines+markers",
        line={"color": color, "width": 2},
        marker={"size": 4, "color": color},
        hovertemplate=f"<b>%{{x}}</b><br>%{{y:.2f}} {unit}<extra></extra>",
        name=metric_name,
    )

    # Determine y-axis range for better visualization
    if values:
        min_val = min(values)
        max_val = max(values)
        range_padding = (max_val - min_val) * 0.2 if max_val > min_val else 1
        y_range = [min_val - range_padding, max_val + range_padding]
    else:
        y_range = None

    # Create layout
    layout = {
        "height": height,
        "margin": {
            "t": 10,
            "r": 10,
            "b": 60 if show_axes else 5,  # Extra space for angled labels
            "l": 45 if show_axes else 5,
        },
        "xaxis": {
            "type": "category",  # Force categorical axis to prevent date interpretation
            "categoryorder": "array",  # Use exact order from data
            "categoryarray": week_labels,  # Explicit week order
            "visible": show_axes,
            "showgrid": False,
            "zeroline": False,
            "tickangle": -45,  # Angle labels to prevent overlap with many data points
            "tickfont": {"size": 9},  # Slightly smaller font for better fit
        },
        "yaxis": {
            "visible": show_axes,
            "showgrid": False,
            "zeroline": False,
            "range": y_range,
            "tickfont": {"size": 10},
        },
        "showlegend": False,
        "hovermode": "x unified",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
    }

    figure = {"data": [trace], "layout": layout}

    return dcc.Graph(
        figure=figure,
        config={"displayModeBar": False},
        style={"height": f"{height}px"},
        className="metric-sparkline",
    )


def create_metric_trend_full(
    week_labels: List[str],
    values: List[float],
    metric_name: str,
    unit: str = "",
    target_line: Optional[float] = None,
    target_label: str = "Target",
    height: int = 200,
) -> dcc.Graph:
    """
    Create a full-size trend chart for metric details.

    Used in collapsible sections or detail views.

    Args:
        week_labels: List of week labels
        values: List of metric values
        metric_name: Name of the metric
        unit: Unit of measurement
        target_line: Optional target value to show as horizontal line
        target_label: Label for target line
        height: Height of chart in pixels (default: 200)

    Returns:
        Dash Graph component with full trend visualization

    Example:
        >>> sparkline = create_metric_trend_full(
        ...     week_labels, values, "Lead Time", "days",
        ...     target_line=1.0, target_label="Elite (< 1 day)"
        ... )
    """
    # Handle empty data
    if not week_labels or not values:
        return dcc.Graph(
            figure={
                "data": [],
                "layout": {
                    "height": height,
                    "title": "No trend data available",
                    "xaxis": {"visible": False},
                    "yaxis": {"visible": False},
                },
            },
            config={"displayModeBar": False},
            style={"height": f"{height}px"},
        )

    # Create main trace
    traces = [
        go.Scatter(
            x=week_labels,
            y=values,
            mode="lines+markers",
            line={"color": "#1f77b4", "width": 3},
            marker={"size": 8, "color": "#1f77b4"},
            hovertemplate=f"<b>%{{x}}</b><br>%{{y:.2f}} {unit}<extra></extra>",
            name=metric_name,
        )
    ]

    # Add target line if provided
    if target_line is not None:
        traces.append(
            go.Scatter(
                x=[week_labels[0], week_labels[-1]],
                y=[target_line, target_line],
                mode="lines",
                line={"color": "red", "width": 2, "dash": "dash"},
                hovertemplate=f"<b>{target_label}</b><br>%{{y:.2f}} {unit}<extra></extra>",
                name=target_label,
            )
        )

    # Create layout
    layout = {
        "height": height,
        "title": {
            "text": f"{metric_name} Trend",
            "font": {"size": 14},
            "x": 0.5,
            "xanchor": "center",
        },
        "xaxis": {
            "title": "Week",
            "showgrid": True,
            "gridcolor": "#E5E5E5",
        },
        "yaxis": {
            "title": unit if unit else metric_name,
            "showgrid": True,
            "gridcolor": "#E5E5E5",
        },
        "hovermode": "x unified",
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    }

    figure = {"data": traces, "layout": layout}

    return dcc.Graph(
        figure=figure,
        config={"displayModeBar": True, "displaylogo": False},
        style={"height": f"{height}px"},
    )


def format_week_label(week_label: str) -> str:
    """
    Format week label for display.

    Args:
        week_label: Week label in format "YYYY-WW" (e.g., "2025-43")

    Returns:
        Formatted label (e.g., "W43")

    Example:
        >>> format_week_label("2025-43")
        "W43"
        >>> format_week_label("2025-W43")  # Also handles W prefix
        "W43"
    """
    if not week_label:
        return ""

    # Extract week number
    if "-W" in week_label:
        # Format: "2025-W43"
        week_num = week_label.split("-W")[1]
    elif "-" in week_label:
        # Format: "2025-43"
        week_num = week_label.split("-")[1]
    else:
        # Unknown format
        return week_label

    return f"W{week_num}"


def get_trend_indicator(
    current_value: Optional[float],
    previous_value: Optional[float],
    higher_is_better: bool = True,
) -> Dict[str, Any]:
    """
    Calculate trend direction and determine if it's good or bad.

    Args:
        current_value: Current period value
        previous_value: Previous period value
        higher_is_better: Whether higher values are better (e.g., deployment frequency)
                         False for metrics like MTTR where lower is better

    Returns:
        Dictionary with:
        - direction: "up", "down", or "stable"
        - percentage_change: Percentage change from previous value
        - is_good: Whether the trend is good (based on higher_is_better)
        - icon: Font Awesome icon class
        - color: Color for trend indicator

    Example:
        >>> get_trend_indicator(15, 12, higher_is_better=True)
        {
            "direction": "up",
            "percentage_change": 25.0,
            "is_good": True,
            "icon": "fa-arrow-up",
            "color": "success"
        }
    """
    if current_value is None or previous_value is None or previous_value == 0:
        return {
            "direction": "stable",
            "percentage_change": 0.0,
            "is_good": True,
            "icon": "fa-minus",
            "color": "secondary",
        }

    percentage_change = ((current_value - previous_value) / previous_value) * 100

    # Determine direction
    if abs(percentage_change) < 5:
        direction = "stable"
        icon = "fa-minus"
    elif percentage_change > 0:
        direction = "up"
        icon = "fa-arrow-up"
    else:
        direction = "down"
        icon = "fa-arrow-down"

    # Determine if trend is good
    if direction == "stable":
        is_good = True
        color = "secondary"
    elif direction == "up":
        is_good = higher_is_better
        color = "success" if is_good else "danger"
    else:  # down
        is_good = not higher_is_better
        color = "success" if is_good else "danger"

    return {
        "direction": direction,
        "percentage_change": round(abs(percentage_change), 1),
        "is_good": is_good,
        "icon": icon,
        "color": color,
    }
