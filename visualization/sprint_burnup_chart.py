import logging
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

import plotly.graph_objects as go

from configuration import COLOR_PALETTE
from utils.chart_tooltip_utils import create_hoverlabel_config, format_hover_template

logger = logging.getLogger(__name__)


def create_sprint_burnup_chart(
    daily_snapshots: Sequence[Mapping[str, Any]],
    sprint_name: str = "Sprint",
    sprint_start_date: str | None = None,
    sprint_end_date: str | None = None,
    height: int = 400,
    show_points: bool = True,
) -> go.Figure:

    if not daily_snapshots:
        return _create_empty_chart("No sprint data available")

    dates = [snapshot["date"] for snapshot in daily_snapshots]

    completed_items = [
        snapshot.get("completed_count", 0) for snapshot in daily_snapshots
    ]
    total_items = [snapshot.get("total_count", 0) for snapshot in daily_snapshots]

    completed_points = [snapshot["completed_points"] for snapshot in daily_snapshots]
    total_points = [snapshot["total_scope"] for snapshot in daily_snapshots]

    has_points_data = any(p > 0 for p in completed_points + total_points)

    final_items = total_items[-1] if total_items else 0
    final_points = total_points[-1] if total_points else 0

    ideal_items = [
        (i / (len(dates) - 1)) * final_items if len(dates) > 1 else 0
        for i in range(len(dates))
    ]

    ideal_points = [
        (i / (len(dates) - 1)) * final_points if len(dates) > 1 else 0
        for i in range(len(dates))
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=ideal_items,
            mode="lines",
            name="Ideal Progress (Items)",
            line=dict(color="rgba(13, 110, 253, 0.3)", width=2, dash="dash"),
            yaxis="y",
            hovertemplate=format_hover_template(
                title="Ideal Progress (Items)",
                fields={
                    "Date": "%{x}",
                    "Items": "%{y}",
                },
            ),
            hoverlabel=create_hoverlabel_config("default"),
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=total_items,
            mode="lines+markers",
            name="Sprint Scope (Items)",
            line=dict(color=COLOR_PALETTE.get("items", "#007bff"), width=3),
            marker=dict(size=6, color=COLOR_PALETTE.get("items", "#007bff")),
            yaxis="y",
            hovertemplate=format_hover_template(
                title="Sprint Scope (Items)",
                fields={
                    "Date": "%{x}",
                    "Total Items": "%{y}",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=completed_items,
            mode="lines+markers",
            name="Completed Issues",
            line=dict(color=COLOR_PALETTE.get("items", "#007bff"), width=3, dash="dot"),
            marker=dict(
                size=7, color=COLOR_PALETTE.get("items", "#007bff"), symbol="circle"
            ),
            yaxis="y",
            hovertemplate=format_hover_template(
                title="Completed Issues",
                fields={
                    "Date": "%{x}",
                    "Issues": "%{y}",
                    "Delta from Ideal": "%{customdata[0]:+d}",
                },
            ),
            customdata=[
                [
                    int(ci - ii)
                    for ci, ii in zip(completed_items, ideal_items, strict=False)
                ]
            ],
            hoverlabel=create_hoverlabel_config("primary"),
            showlegend=True,
        )
    )

    if show_points and has_points_data:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=ideal_points,
                mode="lines",
                name="Ideal Progress (Points)",
                line=dict(color="rgba(253, 126, 20, 0.3)", width=2, dash="dash"),
                yaxis="y2",
                hovertemplate=format_hover_template(
                    title="Ideal Progress (Points)",
                    fields={
                        "Date": "%{x}",
                        "Points": "%{y:.1f}",
                    },
                ),
                hoverlabel=create_hoverlabel_config("default"),
                showlegend=True,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=total_points,
                mode="lines+markers",
                name="Sprint Scope (Points)",
                line=dict(color=COLOR_PALETTE.get("points", "#fd7e14"), width=3),
                marker=dict(size=6, color=COLOR_PALETTE.get("points", "#fd7e14")),
                yaxis="y2",
                hovertemplate=format_hover_template(
                    title="Sprint Scope (Points)",
                    fields={
                        "Date": "%{x}",
                        "Total Points": "%{y:.1f}",
                    },
                ),
                hoverlabel=create_hoverlabel_config("warning"),
                showlegend=True,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=completed_points,
                mode="lines+markers",
                name="Completed Points",
                line=dict(
                    color=COLOR_PALETTE.get("points", "#fd7e14"), width=3, dash="dot"
                ),
                marker=dict(
                    size=7,
                    color=COLOR_PALETTE.get("points", "#fd7e14"),
                    symbol="diamond",
                ),
                yaxis="y2",
                hovertemplate=format_hover_template(
                    title="Completed Points",
                    fields={
                        "Date": "%{x}",
                        "Points": "%{y:.1f}",
                        "Delta from Ideal": "%{customdata[0]:+.1f}",
                    },
                ),
                customdata=[
                    [
                        cp - ip
                        for cp, ip in zip(completed_points, ideal_points, strict=False)
                    ]
                ],
                hoverlabel=create_hoverlabel_config("warning"),
                showlegend=True,
            )
        )

    if sprint_start_date and sprint_end_date:
        try:
            start_dt = datetime.fromisoformat(sprint_start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(sprint_end_date.replace("Z", "+00:00"))

            start_str = start_dt.date().isoformat()
            end_str = end_dt.date().isoformat()

            if start_str in dates:
                max_y = max(total_items) * 1.1 if total_items else 100

                fig.add_trace(
                    go.Scatter(
                        x=[start_str, start_str],
                        y=[0, max_y],
                        mode="lines",
                        name="Sprint Start",
                        line=dict(color="rgba(0, 0, 0, 0.2)", width=2, dash="dot"),
                        hovertemplate=(
                            f"<b>Sprint Start</b><br>{start_str}<extra></extra>"
                        ),
                        showlegend=False,
                        yaxis="y",
                    )
                )

            if end_str in dates:
                max_y = max(total_items) * 1.1 if total_items else 100

                fig.add_trace(
                    go.Scatter(
                        x=[end_str, end_str],
                        y=[0, max_y],
                        mode="lines",
                        name="Sprint End",
                        line=dict(color="rgba(0, 0, 0, 0.2)", width=2, dash="dot"),
                        hovertemplate=f"<b>Sprint End</b><br>{end_str}<extra></extra>",
                        showlegend=False,
                        yaxis="y",
                    )
                )
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to add sprint date markers: {e}")

    layout_config = {
        "title": f"{sprint_name} - Burnup Chart",
        "xaxis": dict(
            title="Date",
            showgrid=True,
            gridcolor="rgba(0, 0, 0, 0.1)",
            tickangle=45,
        ),
        "yaxis": dict(
            title="Issue Count",
            showgrid=True,
            gridcolor="rgba(0, 0, 0, 0.1)",
            rangemode="tozero",
            side="left",
        ),
        "height": height,
        "hovermode": "x unified",
        "legend": dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
        ),
        "margin": dict(l=60, r=60, t=80, b=80),
        "plot_bgcolor": "rgba(255, 255, 255, 0.9)",
        "paper_bgcolor": "white",
        "template": "plotly_white",
    }

    if show_points and has_points_data:
        layout_config["yaxis2"] = dict(
            title="Story Points",
            showgrid=False,
            rangemode="tozero",
            overlaying="y",
            side="right",
        )

    fig.update_layout(**layout_config)

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
