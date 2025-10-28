"""Flow metrics visualization charts.

Provides chart generation functions for Flow metrics including
distribution pie chart and efficiency trend charts.
"""

import plotly.graph_objects as go
from typing import Dict, Any, List


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
        "Feature": "#0d6efd",  # primary
        "Defect": "#dc3545",  # danger
        "Risk": "#ffc107",  # warning
        "Technical_Debt": "#0dcaf0",  # info
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

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name="Flow Velocity",
            line=dict(color="#0d6efd", width=2),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>Velocity: %{y} items<extra></extra>",
        )
    )

    fig.update_layout(
        title={
            "text": "Flow Velocity Trend",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="Date",
        yaxis_title="Items per Period",
        hovermode="x unified",
        height=350,
        margin=dict(t=60, b=60, l=60, r=40),
    )

    return fig


def create_flow_efficiency_trend_chart(trend_data: List[Dict[str, Any]]) -> go.Figure:
    """Create line chart for Flow Efficiency trend over time.

    Args:
        trend_data: List of efficiency measurements over time

    Returns:
        Plotly Figure with line chart and threshold zones
    """
    if not trend_data:
        return _create_empty_chart("No trend data available")

    dates = [item["date"] for item in trend_data]
    values = [item["value"] for item in trend_data]

    fig = go.Figure()

    # Add threshold zones
    # Healthy range (25-40%)
    fig.add_hrect(
        y0=25,
        y1=40,
        fillcolor="green",
        opacity=0.1,
        layer="below",
        line_width=0,
        annotation_text="Healthy Range",
        annotation_position="right",
    )

    # Warning zone (15-25%)
    fig.add_hrect(
        y0=15,
        y1=25,
        fillcolor="orange",
        opacity=0.1,
        layer="below",
        line_width=0,
    )

    # Critical zone (< 15%)
    fig.add_hrect(
        y0=0,
        y1=15,
        fillcolor="red",
        opacity=0.1,
        layer="below",
        line_width=0,
        annotation_text="Critical",
        annotation_position="right",
    )

    # Add efficiency line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name="Flow Efficiency",
            line=dict(color="#0dcaf0", width=2),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>Efficiency: %{y:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title={
            "text": "Flow Efficiency Trend",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="Date",
        yaxis_title="Efficiency (%)",
        hovermode="x unified",
        height=350,
        margin=dict(t=60, b=60, l=60, r=40),
        yaxis=dict(range=[0, max(100, max(values) + 10)]),
    )

    return fig


def create_flow_time_trend_chart(trend_data: List[Dict[str, Any]]) -> go.Figure:
    """Create line chart for Flow Time trend over time.

    Args:
        trend_data: List of flow time measurements over time

    Returns:
        Plotly Figure with line chart
    """
    if not trend_data:
        return _create_empty_chart("No trend data available")

    dates = [item["date"] for item in trend_data]
    values = [item["value"] for item in trend_data]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name="Flow Time",
            line=dict(color="#198754", width=2),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>Flow Time: %{y:.1f} days<extra></extra>",
        )
    )

    fig.update_layout(
        title={
            "text": "Flow Time Trend",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="Date",
        yaxis_title="Days",
        hovermode="x unified",
        height=350,
        margin=dict(t=60, b=60, l=60, r=40),
    )

    return fig


def create_flow_load_trend_chart(trend_data: List[Dict[str, Any]]) -> go.Figure:
    """Create line chart for Flow Load (WIP) trend over time.

    Args:
        trend_data: List of WIP count measurements over time

    Returns:
        Plotly Figure with line chart
    """
    if not trend_data:
        return _create_empty_chart("No trend data available")

    dates = [item["date"] for item in trend_data]
    values = [item["value"] for item in trend_data]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name="Flow Load (WIP)",
            line=dict(color="#ffc107", width=2),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>WIP Count: %{y} items<extra></extra>",
        )
    )

    fig.update_layout(
        title={
            "text": "Flow Load (Work in Progress) Trend",
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="Date",
        yaxis_title="Items in Progress",
        hovermode="x unified",
        height=350,
        margin=dict(t=60, b=60, l=60, r=40),
    )

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
