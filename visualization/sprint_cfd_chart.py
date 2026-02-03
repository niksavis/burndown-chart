"""Sprint Cumulative Flow Diagram (CFD) Visualization.

Creates a stacked area chart showing status distribution over time to identify
bottlenecks in the sprint workflow. Wide horizontal bands indicate WIP limit issues.

Stack order (bottom to top): Done → Testing → In Progress → To Do
"""

import logging
from typing import Dict, List, Optional

import plotly.graph_objects as go
from configuration import COLOR_PALETTE
from ui.tooltip_utils import create_hoverlabel_config, format_hover_template

logger = logging.getLogger(__name__)

# Status color mapping (matches sprint progress bars)
STATUS_COLORS = {
    "To Do": "#6c757d",  # Gray (start state)
    "Backlog": "#6c757d",  # Gray (start state)
    "Open": "#6c757d",  # Gray (start state)
    "In Progress": "#0d6efd",  # Blue (WIP)
    "In Review": "#9b59b6",  # Purple (WIP)
    "Testing": "#0dcaf0",  # Cyan (WIP)
    "Done": "#28a745",  # Green (end state)
    "Closed": "#28a745",  # Green (end state)
    "Resolved": "#28a745",  # Green (end state)
}


def create_sprint_cfd_chart(
    daily_snapshots: List[Dict],
    sprint_name: str = "Sprint",
    status_order: Optional[List[str]] = None,
    height: int = 400,
    use_points: bool = False,
) -> go.Figure:
    """Create cumulative flow diagram showing status distribution over time.

    Args:
        daily_snapshots: List of daily sprint metrics from sprint_snapshot_calculator
            Each snapshot: {
                "date": "2026-02-03",
                "completed_points": 15,
                "total_scope": 45,
                "status_breakdown": {
                    "To Do": {"count": 3, "points": 10},
                    "In Progress": {"count": 2, "points": 8},
                    "Done": {"count": 5, "points": 15}
                },
                "completed_count": 5,
                "total_count": 10
            }
        sprint_name: Sprint name for title
        status_order: Custom status order (bottom to top). If None, uses standard order.
        height: Chart height in pixels
        use_points: Use story points instead of issue count

    Returns:
        Plotly Figure with stacked area chart
    """
    if not daily_snapshots:
        return _create_empty_chart("No sprint data available")

    # Extract dates
    dates = [snapshot["date"] for snapshot in daily_snapshots]

    # Collect all statuses across all snapshots
    all_statuses = set()
    for snapshot in daily_snapshots:
        status_breakdown = snapshot.get("status_breakdown", {})
        all_statuses.update(status_breakdown.keys())

    # Define standard stack order (bottom to top - Done first so it's at bottom)
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

    # Use custom order if provided, otherwise filter default order by actual statuses
    if status_order:
        ordered_statuses = [s for s in status_order if s in all_statuses]
    else:
        ordered_statuses = [s for s in default_order if s in all_statuses]

    # Add any remaining statuses not in the ordered list
    remaining = all_statuses - set(ordered_statuses)
    ordered_statuses.extend(sorted(remaining))

    # Build data series for each status
    status_data = {}
    for status in ordered_statuses:
        values = []
        for snapshot in daily_snapshots:
            status_breakdown = snapshot.get("status_breakdown", {})
            status_info = status_breakdown.get(status, {"count": 0, "points": 0})
            value = status_info.get("points" if use_points else "count", 0)
            values.append(value)
        status_data[status] = values

    # Create figure
    fig = go.Figure()

    # Add traces in reverse order (so Done is first trace = bottom of stack)
    for status in ordered_statuses:
        values = status_data[status]
        color = STATUS_COLORS.get(status, COLOR_PALETTE.get("secondary", "#6c757d"))

        # Calculate cumulative sums for hover info
        cumulative = []
        for i, val in enumerate(values):
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
                stackgroup="one",  # This creates the stacked area effect
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

    # Configure layout
    metric_label = "Story Points" if use_points else "Issue Count"

    fig.update_layout(
        title=f"{sprint_name} - Status Flow",
        xaxis=dict(
            title="Date",
            showgrid=True,
            gridcolor="rgba(0, 0, 0, 0.1)",
            tickangle=-45,
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
        margin=dict(l=60, r=120, t=80, b=80),  # Extra right margin for legend
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
