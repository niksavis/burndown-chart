"""Sprint Burnup Chart Visualization.

Creates a Plotly line chart showing:
1. Cumulative completed points (green, solid)
2. Total sprint scope (blue, solid, can fluctuate with adds/removes)
3. Ideal completion line (gray, dashed, diagonal from 0 to final scope)
4. Sprint start/end date markers

Used in Sprint Progress Tracker tab to visualize commitment vs actual delivery.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import plotly.graph_objects as go
from configuration import COLOR_PALETTE
from ui.tooltip_utils import create_hoverlabel_config, format_hover_template

logger = logging.getLogger(__name__)


def create_sprint_burnup_chart(
    daily_snapshots: List[Dict],
    sprint_name: str = "Sprint",
    sprint_start_date: Optional[str] = None,
    sprint_end_date: Optional[str] = None,
    height: int = 400,
) -> go.Figure:
    """Create sprint burnup chart showing cumulative completion vs scope.

    Args:
        daily_snapshots: List of daily sprint metrics from sprint_snapshot_calculator
            Each snapshot: {
                "date": "2026-02-03",
                "completed_points": 15,
                "total_scope": 45,
                "status_breakdown": {...},
                "completed_count": 5,
                "total_count": 10
            }
        sprint_name: Sprint name for title
        sprint_start_date: ISO format sprint start date (for markers)
        sprint_end_date: ISO format sprint end date (for markers)
        height: Chart height in pixels

    Returns:
        Plotly Figure with burnup chart
    """
    if not daily_snapshots:
        return _create_empty_chart("No sprint data available")

    # Extract data series
    dates = [snapshot["date"] for snapshot in daily_snapshots]
    completed_points = [snapshot["completed_points"] for snapshot in daily_snapshots]
    total_scope = [snapshot["total_scope"] for snapshot in daily_snapshots]

    # Calculate ideal line (straight diagonal from 0 to final scope)
    final_scope = total_scope[-1] if total_scope else 0
    ideal_line = [
        (i / (len(dates) - 1)) * final_scope if len(dates) > 1 else 0
        for i in range(len(dates))
    ]

    # Create figure
    fig = go.Figure()

    # Ideal completion line (show first - so it's behind other lines)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=ideal_line,
            mode="lines",
            name="Ideal Progress",
            line=dict(color="rgba(150, 150, 150, 0.5)", width=2, dash="dash"),
            hovertemplate=format_hover_template(
                title="Ideal Progress",
                fields={
                    "Date": "%{x}",
                    "Points": "%{y:.1f}",
                },
            ),
            hoverlabel=create_hoverlabel_config("default"),
        )
    )

    # Total scope line (can fluctuate with adds/removes)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=total_scope,
            mode="lines+markers",
            name="Sprint Scope",
            line=dict(color=COLOR_PALETTE.get("primary", "#007bff"), width=3),
            marker=dict(size=6, color=COLOR_PALETTE.get("primary", "#007bff")),
            hovertemplate=format_hover_template(
                title="Sprint Scope",
                fields={
                    "Date": "%{x}",
                    "Total Points": "%{y:.1f}",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        )
    )

    # Completed points line (cumulative)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=completed_points,
            mode="lines+markers",
            name="Completed Points",
            line=dict(color=COLOR_PALETTE.get("success", "#28a745"), width=3),
            marker=dict(size=7, color=COLOR_PALETTE.get("success", "#28a745")),
            hovertemplate=format_hover_template(
                title="Completed Points",
                fields={
                    "Date": "%{x}",
                    "Points": "%{y:.1f}",
                    "Delta from Ideal": "%{customdata[0]:+.1f}",
                },
            ),
            customdata=[[cp - il for cp, il in zip(completed_points, ideal_line)]],
            hoverlabel=create_hoverlabel_config("success"),
        )
    )

    # Add sprint start/end date markers if provided
    if sprint_start_date and sprint_end_date:
        try:
            # Parse dates
            start_dt = datetime.fromisoformat(sprint_start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(sprint_end_date.replace("Z", "+00:00"))

            start_str = start_dt.date().isoformat()
            end_str = end_dt.date().isoformat()

            # Add vertical lines for sprint boundaries
            if start_str in dates:
                max_y = max(total_scope) * 1.1 if total_scope else 100

                fig.add_trace(
                    go.Scatter(
                        x=[start_str, start_str],
                        y=[0, max_y],
                        mode="lines",
                        name="Sprint Start",
                        line=dict(color="rgba(0, 0, 0, 0.2)", width=2, dash="dot"),
                        hovertemplate=f"<b>Sprint Start</b><br>{start_str}<extra></extra>",
                        showlegend=False,
                    )
                )

            if end_str in dates:
                max_y = max(total_scope) * 1.1 if total_scope else 100

                fig.add_trace(
                    go.Scatter(
                        x=[end_str, end_str],
                        y=[0, max_y],
                        mode="lines",
                        name="Sprint End",
                        line=dict(color="rgba(0, 0, 0, 0.2)", width=2, dash="dot"),
                        hovertemplate=f"<b>Sprint End</b><br>{end_str}<extra></extra>",
                        showlegend=False,
                    )
                )
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to add sprint date markers: {e}")

    # Configure layout
    fig.update_layout(
        title=f"{sprint_name} - Burnup Chart",
        xaxis=dict(
            title="Date",
            showgrid=True,
            gridcolor="rgba(0, 0, 0, 0.1)",
            tickangle=-45,
        ),
        yaxis=dict(
            title="Story Points",
            showgrid=True,
            gridcolor="rgba(0, 0, 0, 0.1)",
            rangemode="tozero",
        ),
        height=height,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=60, r=40, t=80, b=80),
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        paper_bgcolor="white",
        template="plotly_white",
    )

    return fig


def _create_empty_chart(message: str = "No data available") -> go.Figure:
    """Create empty chart with message.

    Args:
        message: Message to display

    Returns:
        Empty Plotly figure
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
        height=400,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    return fig
