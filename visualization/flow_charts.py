"""Flow metrics visualization charts.

Provides chart generation functions for Flow metrics including
distribution pie chart and efficiency trend charts.
"""

import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
from .chart_config import get_mobile_first_layout, get_consistent_colors


def create_flow_distribution_chart(distribution_data: Dict[str, Any]) -> go.Figure:
    """Create pie chart for Flow Distribution metric.

    Args:
        distribution_data: Flow distribution metric data with breakdown

    Returns:
        Plotly Figure with pie chart
    """
    breakdown = distribution_data.get("distribution_breakdown", {})

    if not breakdown:
        # Return empty chart with message
        return _create_empty_chart("No distribution data available")

    # Extract data for chart
    labels = []
    values = []
    colors = []
    hover_text = []

    color_map = {
        "Feature": "#198754",  # Green - growth/new capabilities
        "Defect": "#dc3545",  # Red - problems/bugs
        "Risk": "#ffc107",  # Yellow - caution/risk
        "Technical_Debt": "#fd7e14",  # Orange - maintenance/technical work
    }

    for work_type, data in breakdown.items():
        count = data.get("count", 0)
        percentage = data.get("percentage", 0)
        within_range = data.get("within_range", True)
        recommended_min = data.get("recommended_min", 0)
        recommended_max = data.get("recommended_max", 0)

        label = work_type.replace("_", " ")
        labels.append(label)
        values.append(count)
        colors.append(color_map.get(work_type, "#6c757d"))

        # Create hover text with range info
        range_status = "✓ Within range" if within_range else "⚠ Outside range"
        hover_text.append(
            f"<b>{label}</b><br>"
            f"Count: {count}<br>"
            f"Percentage: {percentage:.1f}%<br>"
            f"Recommended: {recommended_min}%-{recommended_max}%<br>"
            f"{range_status}"
        )

    # Create pie chart
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                marker=dict(colors=colors),
                hovertemplate="%{customdata}<extra></extra>",
                customdata=hover_text,
                textinfo="label+percent",
                textposition="inside",
            )
        ]
    )

    fig.update_layout(
        title={
            "text": "Flow Distribution by Work Type",
            "x": 0.5,
            "xanchor": "center",
        },
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
        height=400,
        margin=dict(t=80, b=80, l=40, r=40),
    )

    return fig


def create_flow_velocity_trend_chart(trend_data: List[Dict[str, Any]]) -> go.Figure:
    """Create line chart for Flow Velocity trend over time.

    Args:
        trend_data: List of velocity measurements over time

    Returns:
        Plotly Figure with line chart
    """
    if not trend_data:
        return _create_empty_chart("No trend data available")

    dates = [item["date"] for item in trend_data]
    values = [item["value"] for item in trend_data]
    colors = get_consistent_colors()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name="Flow Velocity",
            line=dict(
                color=colors["flow_velocity"], width=3
            ),  # Use consistent color and width
            marker=dict(size=6, color=colors["flow_velocity"]),
            hovertemplate="<b>%{x}</b><br>Velocity: %{y} items<extra></extra>",
        )
    )

    # Use mobile-first layout for consistency with other charts
    layout = get_mobile_first_layout("Flow Velocity Trend")
    layout.update(
        {
            "yaxis": {
                "title": "Items per Period",
                "showgrid": True,  # FORCE visible grid
                "gridwidth": 1,
                "gridcolor": "rgba(0,0,0,0.1)",  # Slightly more visible grid
                "tickfont": {"size": 10},
            },
            "xaxis": {
                "title": "Week",
                "showgrid": True,  # FORCE visible grid
                "gridwidth": 1,
                "gridcolor": "rgba(0,0,0,0.1)",  # Slightly more visible grid
                "tickfont": {"size": 10},
            },
            "plot_bgcolor": "white",  # FORCE white plot area
            "paper_bgcolor": "white",  # FORCE white outer area
        }
    )

    fig.update_layout(layout)
    return fig


def create_flow_efficiency_trend_chart(
    trend_data: List[Dict[str, Any]], line_color: Optional[str] = None
) -> go.Figure:
    """Create line chart for Flow Efficiency trend over time.

    Mobile-first design with clean presentation and immediate value.

    Args:
        trend_data: List of efficiency measurements over time
        line_color: Optional hex color for the line (default: uses config color or green)

    Returns:
        Plotly Figure with line chart and threshold zones
    """
    if not trend_data:
        return _create_empty_chart("No trend data available")

    dates = [item["date"] for item in trend_data]
    values = [item["value"] for item in trend_data]
    colors = get_consistent_colors()

    # Use provided color or fall back to config color (green for efficiency)
    efficiency_color = line_color or colors["flow_efficiency"]

    fig = go.Figure()

    # REMOVED: Performance zones create visual noise
    # Clean design without distracting background zones

    # Add efficiency line with dynamic color based on performance
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name="Flow Efficiency",
            line=dict(color=efficiency_color, width=3),
            marker=dict(size=6, color=efficiency_color),
            hovertemplate="<b>%{x}</b><br>Efficiency: %{y:.1f}%<extra></extra>",
        )
    )

    # Use mobile-first layout with EXPLICIT white backgrounds
    layout = get_mobile_first_layout("Flow Efficiency Trend")
    layout.update(
        {
            "yaxis": {
                "title": "Efficiency (%)",
                "range": [0, max(100, max(values) + 10)] if values else [0, 100],
                "showgrid": True,  # FORCE visible grid
                "gridwidth": 1,
                "gridcolor": "rgba(0,0,0,0.1)",  # Slightly more visible grid
                "tickfont": {"size": 10},
            },
            "xaxis": {
                "title": "Week",
                "showgrid": True,  # FORCE visible grid
                "gridwidth": 1,
                "gridcolor": "rgba(0,0,0,0.1)",  # Slightly more visible grid
                "tickfont": {"size": 10},
            },
            "plot_bgcolor": "white",  # FORCE white plot area
            "paper_bgcolor": "white",  # FORCE white outer area
        }
    )

    fig.update_layout(layout)
    return fig


def create_flow_time_trend_chart(trend_data: List[Dict[str, Any]]) -> go.Figure:
    """Create line chart for Flow Time trend over time.

    Mobile-first design with clean presentation and consistent colors.

    Args:
        trend_data: List of flow time measurements over time

    Returns:
        Plotly Figure with line chart
    """
    if not trend_data:
        return _create_empty_chart("No trend data available")

    dates = [item["date"] for item in trend_data]
    values = [item["value"] for item in trend_data]
    colors = get_consistent_colors()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name="Flow Time",
            line=dict(color=colors["flow_time"], width=3),
            marker=dict(size=6, color=colors["flow_time"]),
            hovertemplate="<b>%{x}</b><br>Flow Time: %{y:.1f} days<extra></extra>",
        )
    )

    # Use mobile-first layout
    layout = get_mobile_first_layout("Flow Time Trend")
    layout.update(
        {
            "yaxis": {
                "title": "Days",
                "showgrid": True,  # FORCE visible grid
                "gridwidth": 1,
                "gridcolor": "rgba(0,0,0,0.1)",  # Slightly more visible grid
                "tickfont": {"size": 10},
            },
            "xaxis": {
                "title": "Week",
                "showgrid": True,  # FORCE visible grid
                "gridwidth": 1,
                "gridcolor": "rgba(0,0,0,0.1)",  # Slightly more visible grid
                "tickfont": {"size": 10},
            },
            "plot_bgcolor": "white",  # FORCE white plot area
            "paper_bgcolor": "white",  # FORCE white outer area
        }
    )

    fig.update_layout(layout)
    return fig


def create_flow_load_trend_chart(
    trend_data: List[Dict[str, Any]], wip_thresholds: Optional[Dict[str, Any]] = None
) -> go.Figure:
    """Create line chart for Flow Load (WIP) trend over time with threshold lines.

    Args:
        trend_data: List of WIP count measurements over time
        wip_thresholds: Dictionary with threshold values from Little's Law calculation
            {
                "healthy": float,
                "warning": float,
                "high": float,
                "critical": float,
                "method": str
            }

    Returns:
        Plotly Figure with line chart and threshold lines
    """
    if not trend_data:
        return _create_empty_chart("No trend data available")

    dates = [item["date"] for item in trend_data]
    values = [item["value"] for item in trend_data]
    colors = get_consistent_colors()

    fig = go.Figure()

    # Add main WIP trend line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name="Flow Load (WIP)",
            line=dict(color=colors["flow_load"], width=3),  # Use consistent styling
            marker=dict(size=6, color=colors["flow_load"]),
            hovertemplate="<b>%{x}</b><br>WIP Count: %{y} items<extra></extra>",
        )
    )

    # Add threshold lines if available
    if wip_thresholds and "healthy" in wip_thresholds:
        # Create hover traces for threshold lines (invisible but hoverable)
        # This allows users to see threshold values on hover

        # Healthy threshold (green zone upper limit)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[wip_thresholds["healthy"]] * len(dates),
                mode="lines",
                name=f"Healthy Threshold ({wip_thresholds['healthy']:.1f})",
                line=dict(color="#198754", width=2, dash="dot"),
                hovertemplate=f"<b>Healthy Threshold</b><br>WIP &lt; {wip_thresholds['healthy']:.1f} items<br>%{{x}}<extra></extra>",
                showlegend=False,
            )
        )

        # Warning threshold (yellow zone upper limit)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[wip_thresholds["warning"]] * len(dates),
                mode="lines",
                name=f"Warning Threshold ({wip_thresholds['warning']:.1f})",
                line=dict(color="#ffc107", width=2, dash="dot"),
                hovertemplate=f"<b>Warning Threshold</b><br>WIP &lt; {wip_thresholds['warning']:.1f} items<br>%{{x}}<extra></extra>",
                showlegend=False,
            )
        )

        # High threshold (orange zone upper limit)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[wip_thresholds["high"]] * len(dates),
                mode="lines",
                name=f"High Threshold ({wip_thresholds['high']:.1f})",
                line=dict(color="#fd7e14", width=2, dash="dot"),
                hovertemplate=f"<b>High Threshold</b><br>WIP &lt; {wip_thresholds['high']:.1f} items<br>%{{x}}<extra></extra>",
                showlegend=False,
            )
        )

        # Critical threshold (red zone starts here)
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[wip_thresholds["critical"]] * len(dates),
                mode="lines",
                name=f"Critical Threshold ({wip_thresholds['critical']:.1f})",
                line=dict(color="#dc3545", width=2, dash="dash"),
                hovertemplate=f"<b>Critical Threshold</b><br>WIP ≥ {wip_thresholds['critical']:.1f} items<br>%{{x}}<extra></extra>",
                showlegend=False,
            )
        )

    # Use mobile-first layout for consistency
    layout = get_mobile_first_layout("Flow Load (Work in Progress) Trend")
    layout.update(
        {
            "yaxis": {
                "title": "Items in Progress",
                "showgrid": True,  # FORCE visible grid
                "gridwidth": 1,
                "gridcolor": "rgba(0,0,0,0.1)",  # Slightly more visible grid
                "tickfont": {"size": 10},
            },
            "xaxis": {
                "title": "Week",
                "showgrid": True,  # FORCE visible grid
                "gridwidth": 1,
                "gridcolor": "rgba(0,0,0,0.1)",  # Slightly more visible grid
                "tickfont": {"size": 10},
            },
            "plot_bgcolor": "white",  # FORCE white plot area
            "paper_bgcolor": "white",  # FORCE white outer area
        }
    )

    fig.update_layout(layout)
    return fig


def _create_empty_chart(message: str) -> go.Figure:
    """Create an empty chart with a message.

    Args:
        message: Message to display

    Returns:
        Empty Plotly Figure with annotation
    """
    fig = go.Figure()

    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color="gray"),
    )

    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=350,
        margin=dict(t=40, b=40, l=40, r=40),
    )

    return fig
