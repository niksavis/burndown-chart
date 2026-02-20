"""Mini trend visualization components for metric cards.

Creates compact sparkline charts to show weekly trends inline with metric values.
"""

from typing import Any

import plotly.graph_objects as go
from dash import dcc


def _add_performance_tier_zones(
    figure: go.Figure,
    metric_name: str,
    y_max: float,
    x_range: list[str],
) -> None:
    """Add colored background zones for performance tiers to chart.

    Adds visual performance tier zones (Elite/High/Medium/Low) as colored
    background rectangles to help users immediately understand if their
    metric values are good or need improvement.

    Args:
        figure: Plotly figure object to add zones to
        metric_name: DORA metric name
            (deployment_frequency, lead_time_for_changes, etc.)
        y_max: Maximum y-axis value for positioning zones
        x_range: X-axis range (typically week labels) for zone width

    Modifies figure in place by adding shape annotations for each tier.
    """
    from configuration.dora_config import DORA_BENCHMARKS

    if metric_name not in DORA_BENCHMARKS:
        return  # No zones for non-DORA metrics

    benchmarks = DORA_BENCHMARKS[metric_name]

    # Define tier boundaries based on metric type
    if metric_name == "deployment_frequency":
        # Higher is better - Elite at top
        # Convert thresholds to deployments per month for consistency
        elite_threshold = benchmarks["elite"]["threshold"] * 30  # per day to per month
        high_threshold = benchmarks["high"]["threshold"] * 4  # per week to per month
        medium_threshold = benchmarks["medium"]["threshold"]  # already per month

        zones = [
            {
                "y0": elite_threshold,
                "y1": y_max * 1.1,
                "color": "rgba(25, 135, 84, 0.02)",  # BARELY visible green
                "name": "Elite",
            },
            {
                "y0": high_threshold,
                "y1": elite_threshold,
                "color": "rgba(255, 193, 7, 0.02)",  # BARELY visible yellow
                "name": "High",
            },
            {
                "y0": medium_threshold,
                "y1": high_threshold,
                "color": "rgba(253, 126, 20, 0.02)",  # BARELY visible orange
                "name": "Medium",
            },
            {
                "y0": 0,
                "y1": medium_threshold,
                "color": "rgba(220, 53, 69, 0.02)",  # BARELY visible red
                "name": "Low",
            },
        ]

    elif metric_name in ["lead_time_for_changes", "mean_time_to_recovery"]:
        # Lower is better - Elite at bottom
        elite_threshold = benchmarks["elite"]["threshold"]
        high_threshold = benchmarks["high"]["threshold"]
        medium_threshold = benchmarks["medium"]["threshold"]

        # For display: convert hours to days if metric is MTTR
        if metric_name == "mean_time_to_recovery":
            elite_threshold = elite_threshold / 24  # hours to days
            high_threshold = high_threshold * 1  # already in days
            medium_threshold = medium_threshold * 1  # already in days

        zones = [
            {
                "y0": 0,
                "y1": elite_threshold,
                "color": "rgba(25, 135, 84, 0.02)",  # BARELY visible green
                "name": "Elite",
            },
            {
                "y0": elite_threshold,
                "y1": high_threshold,
                "color": "rgba(255, 193, 7, 0.02)",  # BARELY visible yellow
                "name": "High",
            },
            {
                "y0": high_threshold,
                "y1": medium_threshold,
                "color": "rgba(253, 126, 20, 0.02)",  # BARELY visible orange
                "name": "Medium",
            },
            {
                "y0": medium_threshold,
                "y1": y_max * 1.1,
                "color": "rgba(220, 53, 69, 0.02)",  # BARELY visible red
                "name": "Low",
            },
        ]

    elif metric_name == "change_failure_rate":
        # Lower is better - Elite at bottom (percentage)
        elite_threshold = benchmarks["elite"]["threshold"]
        high_threshold = benchmarks["high"]["threshold"]
        medium_threshold = benchmarks["medium"]["threshold"]

        zones = [
            {
                "y0": 0,
                "y1": elite_threshold,
                "color": "rgba(25, 135, 84, 0.02)",  # BARELY visible green
                "name": "Elite",
            },
            {
                "y0": elite_threshold,
                "y1": high_threshold,
                "color": "rgba(255, 193, 7, 0.02)",  # BARELY visible yellow
                "name": "High",
            },
            {
                "y0": high_threshold,
                "y1": medium_threshold,
                "color": "rgba(253, 126, 20, 0.02)",  # BARELY visible orange
                "name": "Medium",
            },
            {
                "y0": medium_threshold,
                "y1": 100,
                "color": "rgba(220, 53, 69, 0.02)",  # BARELY visible red
                "name": "Low",
            },
        ]
    else:
        return  # Unknown metric type

    # Add zones as background shapes (drawn first, behind data)
    for zone in zones:
        figure.add_shape(
            type="rect",
            xref="paper",  # Use paper coordinates for full width
            yref="y",
            x0=0,
            y0=zone["y0"],
            x1=1,
            y1=zone["y1"],
            fillcolor=zone["color"],
            line={"width": 0},
            layer="below",  # Draw behind data traces
        )


def create_metric_trend_sparkline(
    week_labels: list[str],
    values: list[float],
    metric_name: str,
    adjusted_values: list[float] | None = None,
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
        adjusted_values: Optional adjusted values for blended current week
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
        line={"color": color, "width": 3},
        marker={"size": 6, "color": color},
        hovertemplate=f"<b>%{{x}}</b><br>%{{y:.2f}} {unit}<extra></extra>",
        name=metric_name,
    )

    adjusted_trace = None
    if adjusted_values and len(adjusted_values) == len(week_labels):
        adjusted_trace = go.Scatter(
            x=week_labels,
            y=adjusted_values,
            mode="lines+markers",
            line={"color": color, "width": 2, "dash": "dot"},
            marker={"size": 5, "color": color, "symbol": "circle-open"},
            hovertemplate=(
                f"<b>%{{x}}</b><br>Adjusted: %{{y:.2f}} {unit}"
                "<extra></extra>"
            ),
            name="Adjusted",
        )

    # Determine y-axis range for better visualization
    all_values = values + adjusted_values if adjusted_values else values
    if all_values:
        min_val = min(all_values)
        max_val = max(all_values)
        range_padding = (max_val - min_val) * 0.2 if max_val > min_val else 1
        y_min = min_val - range_padding
        y_max = max_val + range_padding

        # For percentage/ratio metrics (values between 0-100), never go below 0
        if max_val <= 100 and min_val >= 0:
            y_min = max(0, y_min)  # Don't go below 0 for percentages

        y_range = [y_min, y_max]
    else:
        y_range = None

    # Create layout
    layout = {
        "height": height,
        "margin": {
            "t": 10,
            "r": 20,
            "b": 50 if show_axes else 5,  # Consistent bottom margin for date labels
            "l": 50 if show_axes else 5,
        },
        "xaxis": {
            "type": "category",  # Force categorical axis to prevent date interpretation
            "categoryorder": "array",  # Use exact order from data
            "categoryarray": week_labels,  # Explicit week order
            "visible": show_axes,
            "showgrid": True if show_axes else False,  # Show grid when axes visible
            "gridcolor": "rgba(0,0,0,0.1)",  # Consistent grid color
            "gridwidth": 1,
            "zeroline": False,
            "tickangle": 45,  # Consistent 45° rotation (right tilt)
            "tickfont": {"size": 9},  # Slightly smaller font for better fit
        },
        "yaxis": {
            "visible": show_axes,
            "showgrid": True if show_axes else False,  # Show grid when axes visible
            "gridcolor": "rgba(0,0,0,0.1)",  # Consistent grid color
            "gridwidth": 1,
            "zeroline": False,
            "range": y_range,
            "tickfont": {"size": 10},
        },
        "showlegend": False,
        "hovermode": "x unified",
        "plot_bgcolor": "white",  # White background for visibility
        "paper_bgcolor": "white",  # White background for visibility
    }

    chart_traces = [trace]
    if adjusted_trace is not None:
        chart_traces.append(adjusted_trace)

    figure = {"data": chart_traces, "layout": layout}

    return dcc.Graph(
        figure=figure,
        config={
            "displayModeBar": False,  # Mobile-first: Remove plotly toolbar
            "responsive": True,  # Mobile-responsive scaling
            "scrollZoom": False,  # Disable scroll zoom on mobile
            "doubleClick": False,  # Disable double-click interactions
            "showTips": False,  # Cleaner appearance
        },
        style={"height": f"{height}px"},
        className="metric-sparkline",
    )


def create_metric_trend_full(
    week_labels: list[str],
    values: list[float],
    metric_name: str,
    adjusted_values: list[float] | None = None,
    unit: str = "",
    target_line: float | None = None,
    target_label: str = "Target",
    height: int = 200,
    show_performance_zones: bool = True,
    line_color: str = "#1f77b4",
) -> dcc.Graph:
    """
    Create a full-size trend chart for metric details.

    Used in collapsible sections or detail views. Optionally shows
    performance tier zones (Elite/High/Medium/Low) as colored backgrounds.

    Args:
        week_labels: List of week labels
        values: List of metric values
        metric_name: Name of the metric
        adjusted_values: Optional adjusted values for blended current week
        unit: Unit of measurement
        target_line: Optional target value to show as horizontal line
        target_label: Label for target line
        height: Height of chart in pixels (default: 200)
        show_performance_zones: Whether to show performance tier zones (default: True)
        line_color: Color for the trend line
            (default: blue, or dynamic based on performance tier)

    Returns:
        Dash Graph component with full trend visualization

    Example:
        >>> sparkline = create_metric_trend_full(
        ...     week_labels, values, "lead_time_for_changes", "days",
        ...     target_line=1.0, target_label="Elite (< 1 day)",
        ...     line_color="#198754"  # Green for Elite tier
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
            config={
                "displayModeBar": False,  # Mobile-first: Remove plotly toolbar
                "responsive": True,  # Mobile-responsive scaling
                "scrollZoom": False,  # Disable scroll zoom on mobile
                "doubleClick": False,  # Disable double-click interactions
                "showTips": False,  # Cleaner appearance
            },
            style={"height": f"{height}px"},
        )

    # Determine y-axis range
    all_values = values + adjusted_values if adjusted_values else values
    min_val = min(all_values)
    max_val = max(all_values)
    range_padding = (max_val - min_val) * 0.2 if max_val > min_val else 1
    y_min = max(0, min_val - range_padding)  # Never go below 0
    y_max = max_val + range_padding

    # Create main trace
    traces = [
        go.Scatter(
            x=week_labels,
            y=values,
            mode="lines+markers",
            line={"color": line_color, "width": 3},
            marker={"size": 8, "color": line_color},
            hovertemplate=f"<b>%{{x}}</b><br>%{{y:.2f}} {unit}<extra></extra>",
            name=metric_name,
        )
    ]

    if adjusted_values and len(adjusted_values) == len(week_labels):
        traces.append(
            go.Scatter(
                x=week_labels,
                y=adjusted_values,
                mode="lines+markers",
                line={"color": line_color, "width": 2, "dash": "dot"},
                marker={"size": 6, "color": line_color, "symbol": "circle-open"},
                hovertemplate=(
                    f"<b>%{{x}}</b><br>Adjusted: %{{y:.2f}} {unit}"
                    "<extra></extra>"
                ),
                name="Adjusted",
            )
        )

    # Add target line if provided
    if target_line is not None:
        traces.append(
            go.Scatter(
                x=[week_labels[0], week_labels[-1]],
                y=[target_line, target_line],
                mode="lines",
                line={"color": "red", "width": 2, "dash": "dash"},
                hovertemplate=(
                    f"<b>{target_label}</b><br>%{{y:.2f}} {unit}"
                    "<extra></extra>"
                ),
                name=target_label,
            )
        )

    # Create mobile-first layout - CLEAN design
    layout = {
        "height": height,
        "xaxis": {
            "title": "",  # No axis title
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "tickfont": {"size": 10},
            "tickangle": 45,  # Consistent 45° rotation (right tilt)
        },
        "yaxis": {
            "title": "",  # No axis title
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "range": [y_min, y_max],
            "tickfont": {"size": 10},
        },
        "hovermode": "x unified",
        "showlegend": False,  # Cleaner for trend charts
        "margin": dict(
            l=50, r=20, t=10, b=50
        ),  # Consistent margins across all metric charts
        "plot_bgcolor": "white",  # CRITICAL: White plot area
        "paper_bgcolor": "white",  # CRITICAL: White outer background
        "font": {"size": 12},
    }

    figure = go.Figure(data=traces, layout=layout)

    # REMOVED: Performance tier zones create visual noise even at low opacity
    # Zones removed for cleaner, professional appearance
    # if show_performance_zones:
    #     _add_performance_tier_zones(figure, metric_name, y_max, week_labels)

    return dcc.Graph(
        figure=figure,
        config={
            "displayModeBar": False,  # CRITICAL: Remove plotly toolbar completely
            "staticPlot": False,  # Allow hover but no tools
            "responsive": True,  # Mobile-responsive scaling
        },
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
    current_value: float | None,
    previous_value: float | None,
    higher_is_better: bool = True,
) -> dict[str, Any]:
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


def create_dual_line_trend(
    week_labels: list[str],
    deployment_values: list[float],
    release_values: list[float],
    adjusted_deployment_values: list[float] | None = None,
    height: int = 250,
    show_axes: bool = True,
    primary_color: str = "#0d6efd",
    secondary_color: str = "#28a745",
    chart_title: str = "Deployment Frequency",
) -> dcc.Graph:
    """Create dual-line trend chart for deployments vs releases.

    Visualizes both operational deployments and unique releases on the same chart
    to help users understand the relationship between deployment activities and
    actual code releases.

    Args:
        week_labels: List of week labels (e.g., ["2025-W40", "2025-W41", ...])
        deployment_values: Deployment counts per week (operational tasks)
        release_values: Release counts per week (unique fixVersions)
        height: Height of chart in pixels (default: 250)
        show_axes: Whether to show axis labels (default: True)
        primary_color: Color for deployment line
            (default: blue, or dynamic based on performance)
        secondary_color: Color for release line (default: green)
        chart_title: Title to display on chart (default: "Deployment Frequency")

    Returns:
        Dash Graph component with dual-line visualization

    Example:
        >>> week_labels = ["2025-W40", "2025-W41", "2025-W42"]
        >>> deployments = [12, 15, 14]
        >>> releases = [6, 8, 7]
        >>> chart = create_dual_line_trend(
        ...     week_labels, deployments, releases,
        ...     primary_color="#198754",  # Green for Elite tier
        ...     chart_title="Deployment Frequency"
        ... )
    """
    # Handle empty data
    if not week_labels or not deployment_values:
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

    # Create traces for releases (primary) and deployments (secondary)
    traces = []

    # Release trace (PRIMARY - unique fixVersions, what we measure for DORA)
    traces.append(
        go.Scatter(
            x=week_labels,
            y=release_values,
            mode="lines+markers",
            name="Releases",
            line={"color": primary_color, "width": 3},
            marker={"size": 8, "color": primary_color},
            hovertemplate="<b>%{x}</b><br>Releases: %{y}<extra></extra>",
        )
    )

    # Deployment trace (SECONDARY - operational tasks, supporting detail)
    traces.append(
        go.Scatter(
            x=week_labels,
            y=deployment_values,
            mode="lines+markers",
            name="Deployments",
            line={"color": secondary_color, "width": 2, "dash": "dot"},
            marker={"size": 6, "color": secondary_color, "symbol": "diamond"},
            hovertemplate="<b>%{x}</b><br>Deployments: %{y}<extra></extra>",
        )
    )

    if adjusted_deployment_values and len(adjusted_deployment_values) == len(
        week_labels
    ):
        traces.append(
            go.Scatter(
                x=week_labels,
                y=adjusted_deployment_values,
                mode="lines+markers",
                name="Adjusted Deployments",
                line={"color": secondary_color, "width": 2, "dash": "dash"},
                marker={"size": 5, "color": secondary_color, "symbol": "circle-open"},
                hovertemplate="<b>%{x}</b><br>Adjusted: %{y}<extra></extra>",
            )
        )

    # Determine y-axis range based on both lines
    all_values = deployment_values + release_values
    if adjusted_deployment_values:
        all_values += adjusted_deployment_values
    if all_values:
        min_val = min(all_values)
        max_val = max(all_values)
        range_padding = (max_val - min_val) * 0.2 if max_val > min_val else 1
        y_min = max(0, min_val - range_padding)  # Never go below 0 for counts
        y_max = max_val + range_padding
        y_range = [y_min, y_max]
    else:
        y_range = None

    # Create layout
    layout = {
        "height": height,
        "margin": {
            "t": 10,  # No title
            "r": 10,
            "b": 60 if show_axes else 5,
            "l": 45 if show_axes else 5,
        },
        "xaxis": {
            "type": "category",
            "categoryorder": "array",
            "categoryarray": week_labels,
            "visible": show_axes,
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "zeroline": False,
            "tickangle": 45,  # Consistent 45° rotation (right tilt)
            "tickfont": {"size": 9},
            "title": "",  # No axis title
        },
        "yaxis": {
            "visible": show_axes,
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "zeroline": False,
            "range": y_range,
            "tickfont": {"size": 10},
            "title": "",  # No axis title
        },
        "showlegend": True,
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,  # Above chart to avoid overlap with x-axis dates
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 10},
        },
        "hovermode": "x unified",
        "plot_bgcolor": "white",  # CRITICAL: White plot area, NOT transparent
        "paper_bgcolor": "white",  # CRITICAL: White outer area, NOT transparent
    }

    figure = {"data": traces, "layout": layout}

    return dcc.Graph(
        figure=figure,
        config={"displayModeBar": False},
        style={"height": f"{height}px"},
        className="metric-dual-line-chart",
    )
