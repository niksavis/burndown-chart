from typing import Any

import plotly.graph_objects as go

from .chart_config import get_consistent_colors, get_mobile_first_layout


def create_flow_distribution_chart(distribution_data: dict[str, Any]) -> go.Figure:

    breakdown = distribution_data.get("distribution_breakdown", {})

    if not breakdown:
        return _create_empty_chart("No distribution data available")

    labels = []
    values = []
    colors = []
    hover_text = []

    color_map = {
        "Feature": "#198754",
        "Defect": "#dc3545",
        "Risk": "#ffc107",
        "Technical_Debt": "#fd7e14",
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

        range_status = "Within range" if within_range else "Outside range"
        hover_text.append(
            f"<b>{label}</b><br>"
            f"Count: {count}<br>"
            f"Percentage: {percentage:.1f}%<br>"
            f"Recommended: {recommended_min}%-{recommended_max}%<br>"
            f"{range_status}"
        )

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                marker=dict(
                    colors=colors,
                    line=dict(
                        color=[
                            "#ffffff"
                            if breakdown.get(work_type.replace(" ", "_"), {}).get(
                                "within_range", True
                            )
                            else "#dc3545"
                            for work_type in labels
                        ],
                        width=[
                            2
                            if breakdown.get(work_type.replace(" ", "_"), {}).get(
                                "within_range", True
                            )
                            else 4
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

    annotations = []
    y_position = 1.15

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
        y_position -= 0.06

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
        height=500,
        margin=dict(t=60, b=80, l=40, r=40),
    )

    return fig


def create_flow_velocity_trend_chart(trend_data: list[dict[str, Any]]) -> go.Figure:

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
            line=dict(color=colors["flow_velocity"], width=3),
            marker=dict(size=6, color=colors["flow_velocity"]),
            hovertemplate="<b>%{x}</b><br>Velocity: %{y} items<extra></extra>",
        )
    )

    layout = get_mobile_first_layout("Flow Velocity Trend")
    layout.update(
        {
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
        }
    )

    fig.update_layout(layout)
    return fig


def create_flow_efficiency_trend_chart(
    trend_data: list[dict[str, Any]], line_color: str | None = None
) -> go.Figure:

    if not trend_data:
        return _create_empty_chart("No trend data available")

    dates = [item["date"] for item in trend_data]
    values = [item["value"] for item in trend_data]
    colors = get_consistent_colors()

    efficiency_color = line_color or colors["flow_efficiency"]

    fig = go.Figure()

    fig.add_shape(
        type="rect",
        x0=dates[0] if dates else 0,
        x1=dates[-1] if dates else 1,
        y0=60,
        y1=100,
        fillcolor="rgba(25, 135, 84, 0.20)",
        line=dict(
            color="rgba(25, 135, 84, 0.5)",
            width=1,
            dash="dot",
        ),
        layer="below",
    )

    fig.add_shape(
        type="rect",
        x0=dates[0] if dates else 0,
        x1=dates[-1] if dates else 1,
        y0=40,
        y1=60,
        fillcolor="rgba(25, 135, 84, 0.10)",
        line=dict(
            color="rgba(25, 135, 84, 0.3)",
            width=1,
            dash="dot",
        ),
        layer="below",
    )

    fig.add_shape(
        type="rect",
        x0=dates[0] if dates else 0,
        x1=dates[-1] if dates else 1,
        y0=25,
        y1=40,
        fillcolor="rgba(255, 193, 7, 0.10)",
        line=dict(
            color="rgba(255, 193, 7, 0.3)",
            width=1,
            dash="dot",
        ),
        layer="below",
    )

    fig.add_annotation(
        x=dates[len(dates) // 2] if dates else 0.5,
        y=75,
        text="Excellent (60%+)",
        showarrow=False,
        font=dict(size=10, color="rgba(25, 135, 84, 0.9)"),
        bgcolor="rgba(255, 255, 255, 0.9)",
        borderpad=4,
    )

    fig.add_annotation(
        x=dates[len(dates) // 3] if dates else 0.33,
        y=50,
        text="Good (40-60%)",
        showarrow=False,
        font=dict(size=9, color="rgba(25, 135, 84, 0.7)"),
        bgcolor="rgba(255, 255, 255, 0.9)",
        borderpad=3,
    )

    fig.add_annotation(
        x=dates[2 * len(dates) // 3] if dates else 0.67,
        y=32,
        text="Fair (25-40%)",
        showarrow=False,
        font=dict(size=9, color="rgba(255, 193, 7, 0.8)"),
        bgcolor="rgba(255, 255, 255, 0.9)",
        borderpad=3,
    )

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

    layout = get_mobile_first_layout("Flow Efficiency Trend")
    layout.update(
        {
            "yaxis": {
                "range": [0, max(100, max(values) + 10)] if values else [0, 100],
            },
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
        }
    )

    fig.update_layout(layout)
    return fig


def create_flow_time_trend_chart(trend_data: list[dict[str, Any]]) -> go.Figure:

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

    layout = get_mobile_first_layout("Flow Time Trend")
    layout.update(
        {
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
        }
    )

    fig.update_layout(layout)
    return fig


def create_flow_load_trend_chart(
    trend_data: list[dict[str, Any]],
    wip_thresholds: dict[str, Any] | None = None,
    line_color: str = "#6f42c1",
) -> go.Figure:

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
            line=dict(color=line_color, width=3),
            marker=dict(size=6, color=line_color),
            hovertemplate="<b>%{x}</b><br>WIP Count: %{y} items<extra></extra>",
        )
    )

    if wip_thresholds and "healthy" in wip_thresholds:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[wip_thresholds["healthy"]] * len(dates),
                mode="lines",
                name=f"Healthy Threshold ({wip_thresholds['healthy']:.1f})",
                line=dict(color="#198754", width=2, dash="dot"),
                hovertemplate=(
                    "<b>Healthy Threshold</b><br>WIP &lt; "
                    f"{wip_thresholds['healthy']:.1f} items"
                    "<br>%{x}<extra></extra>"
                ),
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[wip_thresholds["warning"]] * len(dates),
                mode="lines",
                name=f"Warning Threshold ({wip_thresholds['warning']:.1f})",
                line=dict(color="#ffc107", width=2, dash="dot"),
                hovertemplate=(
                    "<b>Warning Threshold</b><br>WIP &lt; "
                    f"{wip_thresholds['warning']:.1f} items"
                    "<br>%{x}<extra></extra>"
                ),
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[wip_thresholds["high"]] * len(dates),
                mode="lines",
                name=f"High Threshold ({wip_thresholds['high']:.1f})",
                line=dict(color="#fd7e14", width=2, dash="dot"),
                hovertemplate=(
                    "<b>High Threshold</b><br>WIP &lt; "
                    f"{wip_thresholds['high']:.1f} items"
                    "<br>%{x}<extra></extra>"
                ),
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[wip_thresholds["critical"]] * len(dates),
                mode="lines",
                name=f"Critical Threshold ({wip_thresholds['critical']:.1f})",
                line=dict(color="#dc3545", width=2, dash="dash"),
                hovertemplate=(
                    "<b>Critical Threshold</b><br>WIP ≥ "
                    f"{wip_thresholds['critical']:.1f} items"
                    "<br>%{x}<extra></extra>"
                ),
                showlegend=False,
            )
        )

    layout = get_mobile_first_layout("Flow Load (Work in Progress) Trend")
    layout.update(
        {
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
        }
    )

    fig.update_layout(layout)
    return fig


def _create_empty_chart(message: str) -> go.Figure:

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
