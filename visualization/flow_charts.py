"""Flow metrics visualization charts.

Provides chart generation functions for Flow metrics including
distribution pie chart and efficiency trend charts.
"""

from typing import Any

import plotly.graph_objects as go

from .chart_config import get_consistent_colors, get_mobile_first_layout


def create_flow_distribution_chart(distribution_data: dict[str, Any]) -> go.Figure:
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
        range_status = "Within range" if within_range else "Outside range"
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
                marker=dict(
                    colors=colors,
                    line=dict(
                        # Add thicker border to out-of-range segments for visual indicator
                        color=[
                            "#ffffff"
                            if breakdown.get(work_type.replace(" ", "_"), {}).get(
                                "within_range", True
                            )
                            else "#dc3545"  # Red border for out-of-range
                            for work_type in labels
                        ],
                        width=[
                            2
                            if breakdown.get(work_type.replace(" ", "_"), {}).get(
                                "within_range", True
                            )
                            else 4  # Thicker border for out-of-range
                            for work_type in labels
                        ],
                    ),
                ),
                hovertemplate="%{customdata}<extra></extra>",
                customdata=hover_text,
                textinfo="label+percent",
                textposition="inside",
            )
        ]
    )

    # Add annotations showing target ranges for each work type
    annotations = []
    y_position = 1.15  # Start position above chart

    for work_type, data in breakdown.items():
        recommended_min = data.get("recommended_min", 0)
        recommended_max = data.get("recommended_max", 0)
        within_range = data.get("within_range", True)

        label = work_type.replace("_", " ")
        status_icon = "[OK]" if within_range else "[WARN]"
        color = "green" if within_range else "red"

        annotations.append(
            dict(
                text=f"{status_icon} {label}: {recommended_min}-{recommended_max}%",
                xref="paper",
                yref="paper",
                x=0.5,
                y=y_position,
                xanchor="center",
                yanchor="top",
                showarrow=False,
                font=dict(size=10, color=color),
                bgcolor="rgba(255, 255, 255, 0.8)",
                borderpad=2,
            )
        )
        y_position -= 0.06  # Move down for next annotation

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
        annotations=annotations,
        height=500,  # Increased height to accommodate target range annotations
        margin=dict(t=60, b=80, l=40, r=40),  # Reduced top margin since no title
    )

    return fig


def create_flow_velocity_trend_chart(trend_data: list[dict[str, Any]]) -> go.Figure:
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
            "plot_bgcolor": "white",  # FORCE white plot area
            "paper_bgcolor": "white",  # FORCE white outer area
        }
    )

    fig.update_layout(layout)
    return fig


def create_flow_efficiency_trend_chart(
    trend_data: list[dict[str, Any]], line_color: str | None = None
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

    # Add "Excellent" range zone (60%+) - minimal waiting, highly efficient
    fig.add_shape(
        type="rect",
        x0=dates[0] if dates else 0,
        x1=dates[-1] if dates else 1,
        y0=60,
        y1=100,
        fillcolor="rgba(25, 135, 84, 0.20)",  # Darker green for excellent zone
        line=dict(
            color="rgba(25, 135, 84, 0.5)",
            width=1,
            dash="dot",
        ),
        layer="below",
    )

    # Add "Good" range zone (40-60%) - balanced flow with acceptable waiting
    fig.add_shape(
        type="rect",
        x0=dates[0] if dates else 0,
        x1=dates[-1] if dates else 1,
        y0=40,
        y1=60,
        fillcolor="rgba(25, 135, 84, 0.10)",  # Light green for good zone
        line=dict(
            color="rgba(25, 135, 84, 0.3)",
            width=1,
            dash="dot",
        ),
        layer="below",
    )

    # Add "Fair" range zone (25-40%) - acceptable but high wait time
    fig.add_shape(
        type="rect",
        x0=dates[0] if dates else 0,
        x1=dates[-1] if dates else 1,
        y0=25,
        y1=40,
        fillcolor="rgba(255, 193, 7, 0.10)",  # Yellow for fair zone
        line=dict(
            color="rgba(255, 193, 7, 0.3)",
            width=1,
            dash="dot",
        ),
        layer="below",
    )

    # Add annotation explaining the excellent range
    fig.add_annotation(
        x=dates[len(dates) // 2] if dates else 0.5,  # Middle of chart
        y=75,  # Middle of 60-100% range
        text="Excellent (60%+)",
        showarrow=False,
        font=dict(size=10, color="rgba(25, 135, 84, 0.9)"),
        bgcolor="rgba(255, 255, 255, 0.9)",
        borderpad=4,
    )

    # Add annotation for good range
    fig.add_annotation(
        x=dates[len(dates) // 3] if dates else 0.33,  # Left third of chart
        y=50,  # Middle of 40-60% range
        text="Good (40-60%)",
        showarrow=False,
        font=dict(size=9, color="rgba(25, 135, 84, 0.7)"),
        bgcolor="rgba(255, 255, 255, 0.9)",
        borderpad=3,
    )

    # Add annotation for fair range
    fig.add_annotation(
        x=dates[2 * len(dates) // 3] if dates else 0.67,  # Right third of chart
        y=32,  # Middle of 25-40% range
        text="Fair (25-40%)",
        showarrow=False,
        font=dict(size=9, color="rgba(255, 193, 7, 0.8)"),
        bgcolor="rgba(255, 255, 255, 0.9)",
        borderpad=3,
    )

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
                "range": [0, max(100, max(values) + 10)] if values else [0, 100],
            },
            "plot_bgcolor": "white",  # FORCE white plot area
            "paper_bgcolor": "white",  # FORCE white outer area
        }
    )

    fig.update_layout(layout)
    return fig


def create_flow_time_trend_chart(trend_data: list[dict[str, Any]]) -> go.Figure:
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
            "plot_bgcolor": "white",  # FORCE white plot area
            "paper_bgcolor": "white",  # FORCE white outer area
        }
    )

    fig.update_layout(layout)
    return fig


def create_flow_load_trend_chart(
    trend_data: list[dict[str, Any]],
    wip_thresholds: dict[str, Any] | None = None,
    line_color: str = "#6f42c1",  # Default purple, but accept dynamic color
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
        line_color: Color for the main trend line (dynamic based on performance tier)

    Returns:
        Plotly Figure with line chart and threshold lines
    """
    if not trend_data:
        return _create_empty_chart("No trend data available")

    dates = [item["date"] for item in trend_data]
    values = [item["value"] for item in trend_data]

    fig = go.Figure()

    # Add main WIP trend line with dynamic color
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name="Flow Load (WIP)",
            line=dict(color=line_color, width=3),  # Use dynamic tier-based color
            marker=dict(size=6, color=line_color),
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
