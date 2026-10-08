import logging
from collections.abc import Mapping, Sequence
from typing import Any

import plotly.graph_objects as go

from configuration import COLOR_PALETTE
from utils.chart_tooltip_utils import create_hoverlabel_config, format_hover_template

logger = logging.getLogger(__name__)

STATUS_COLORS = {
    "To Do": "#6c757d",
    "Backlog": "#6c757d",
    "Open": "#6c757d",
    "In Progress": "#0d6efd",
    "In Review": "#9b59b6",
    "Testing": "#0dcaf0",
    "Done": "#28a745",
    "Closed": "#28a745",
    "Resolved": "#28a745",
}


def create_sprint_cfd_chart(
    daily_snapshots: Sequence[Mapping[str, Any]],
    sprint_name: str = "Sprint",
    status_order: list[str] | None = None,
    height: int = 400,
    use_points: bool = False,
) -> go.Figure:

    if not daily_snapshots:
        return _create_empty_chart("No sprint data available")

    dates = [snapshot["date"] for snapshot in daily_snapshots]

    all_statuses = set()
    for snapshot in daily_snapshots:
        status_breakdown = snapshot.get("status_breakdown", {})
        all_statuses.update(status_breakdown.keys())

    default_order = [
        "Done",
        "Closed",
        "Resolved",
        "Testing",
        "In Review",
        "In Progress",
        "Analysis",
        "To Do",
        "Backlog",
        "Open",
    ]

    if status_order:
        ordered_statuses = [s for s in status_order if s in all_statuses]
    else:
        ordered_statuses = [s for s in default_order if s in all_statuses]

    remaining = all_statuses - set(ordered_statuses)
    ordered_statuses.extend(sorted(remaining))

    status_data = {}
    for status in ordered_statuses:
        values = []
        for snapshot in daily_snapshots:
            status_breakdown = snapshot.get("status_breakdown", {})
            status_info = status_breakdown.get(status, {"count": 0, "points": 0})
            value = status_info.get("points" if use_points else "count", 0)
            values.append(value)
        status_data[status] = values

    fig = go.Figure()

    for status in ordered_statuses:
        values = status_data[status]
        color = STATUS_COLORS.get(status, COLOR_PALETTE.get("secondary", "#6c757d"))

        cumulative = []
        for i, _val in enumerate(values):
            cum_sum = sum(
                status_data[s][i]
                for s in ordered_statuses[: ordered_statuses.index(status) + 1]
            )
            cumulative.append(cum_sum)

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                name=status,
                mode="lines",
                line=dict(width=0.5, color=color),
                fillcolor=color,
                stackgroup="one",
                hovertemplate=format_hover_template(
                    title=status,
                    fields={
                        "Date": "%{x}",
                        f"{'Points' if use_points else 'Issues'}": "%{y}",
                    },
                ),
                hoverlabel=create_hoverlabel_config("default"),
            )
        )

    metric_label = "Story Points" if use_points else "Issue Count"

    fig.update_layout(
        title=f"{sprint_name} - Status Flow",
        xaxis=dict(
            title="Date",
            showgrid=True,
            gridcolor="rgba(0, 0, 0, 0.1)",
            tickangle=45,
        ),
        yaxis=dict(
            title=metric_label,
            showgrid=True,
            gridcolor="rgba(0, 0, 0, 0.1)",
            rangemode="tozero",
        ),
        height=height,
        hovermode="x unified",
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1,
        ),
        margin=dict(l=60, r=120, t=80, b=80),
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        paper_bgcolor="white",
        template="plotly_white",
    )

    return fig


def _create_empty_chart(message: str = "No data available") -> go.Figure:

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
        height=400,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    return fig
