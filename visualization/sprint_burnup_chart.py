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
    show_points: bool = True,
) -> go.Figure:
    """Create sprint burnup chart with dual y-axis (items + points).

    Pattern: Always show items on left y-axis. Conditionally show points on right y-axis
    when show_points=True. This matches the "Forecast Based On Historical Data" burndown
    chart behavior for consistency.

    Args:
        daily_snapshots: List of daily sprint metrics from sprint_snapshot_calculator
            Each snapshot: {
                "date": "2026-02-03",
                "completed_points": 15,
                "total_scope": 45,
                "completed_count": 5,
                "total_count": 10,
                "status_breakdown": {...}
            }
        sprint_name: Sprint name for title
        sprint_start_date: ISO format sprint start date (for markers)
        sprint_end_date: ISO format sprint end date (for markers)
        height: Chart height in pixels
        show_points: If True, show both items and points; if False, show items only

    Returns:
        Plotly Figure with burnup chart (dual y-axis when points available)
    """
    if not daily_snapshots:
        return _create_empty_chart("No sprint data available")

    # Extract data series - always get both items and points
    dates = [snapshot["date"] for snapshot in daily_snapshots]

    # Items data (always shown on left y-axis)
    completed_items = [
        snapshot.get("completed_count", 0) for snapshot in daily_snapshots
    ]
    total_items = [snapshot.get("total_count", 0) for snapshot in daily_snapshots]

    # Points data (conditionally shown on right y-axis)
    completed_points = [snapshot["completed_points"] for snapshot in daily_snapshots]
    total_points = [snapshot["total_scope"] for snapshot in daily_snapshots]

    # Check if we have meaningful points data
    has_points_data = any(p > 0 for p in completed_points + total_points)

    # Calculate ideal lines for both metrics
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

    # Create figure
    fig = go.Figure()

    # === LEFT Y-AXIS (Items) - Always shown ===

    # Ideal progress (items) - background reference line
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

    # Total scope (items) - commitment line
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

    # Completed (items) - actual delivery line
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
            customdata=[[int(ci - ii) for ci, ii in zip(completed_items, ideal_items)]],
            hoverlabel=create_hoverlabel_config("primary"),
            showlegend=True,
        )
    )

    # === RIGHT Y-AXIS (Points) - Conditionally shown ===

    if show_points and has_points_data:
        # Ideal progress (points) - background reference line
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

        # Total scope (points) - commitment line
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

        # Completed (points) - actual delivery line
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
                    [cp - ip for cp, ip in zip(completed_points, ideal_points)]
                ],
                hoverlabel=create_hoverlabel_config("warning"),
                showlegend=True,
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
                max_y = max(total_items) * 1.1 if total_items else 100

                fig.add_trace(
                    go.Scatter(
                        x=[start_str, start_str],
                        y=[0, max_y],
                        mode="lines",
                        name="Sprint Start",
                        line=dict(color="rgba(0, 0, 0, 0.2)", width=2, dash="dot"),
                        hovertemplate=f"<b>Sprint Start</b><br>{start_str}<extra></extra>",
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

    # Configure layout with dual y-axis (like burndown chart)
    layout_config = {
        "title": f"{sprint_name} - Burnup Chart",
        "xaxis": dict(
            title="Date",
            showgrid=True,
            gridcolor="rgba(0, 0, 0, 0.1)",
            tickangle=-45,
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

    # Add right y-axis for points if shown
    if show_points and has_points_data:
        layout_config["yaxis2"] = dict(
            title="Story Points",
            showgrid=False,  # Don't draw grid on chart area (avoid overlap)
            rangemode="tozero",
            overlaying="y",
            side="right",
        )

    fig.update_layout(**layout_config)

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
