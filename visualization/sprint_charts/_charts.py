"""Sprint chart builders: timeline, status pie, summary card, and empty placeholder."""

import plotly.graph_objects as go

from configuration import COLOR_PALETTE

from ._status import STATUS_COLORS


def _create_empty_sprint_chart(message: str) -> go.Figure:
    """Create empty placeholder chart."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="gray"),
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=300,
    )
    return fig


def create_sprint_timeline_chart(sprint_changes: dict) -> go.Figure:
    """Create timeline visualization showing sprint composition changes.

    Args:
        sprint_changes: Dict with 'added', 'removed', 'moved_in', 'moved_out' lists

    Returns:
        Plotly Figure (empty placeholder for now)
    """
    # TODO: Implement sprint timeline chart
    return _create_empty_sprint_chart("Sprint timeline chart (coming soon)")


def create_status_distribution_pie(progress_data: dict) -> go.Figure:
    """Create pie chart showing status distribution.

    Args:
        progress_data: Dict with status counts

    Returns:
        Plotly Figure with pie chart
    """
    status_counts = progress_data.get("status_counts", {})

    if not status_counts:
        return _create_empty_sprint_chart("No status data available")

    labels = list(status_counts.keys())
    values = list(status_counts.values())
    colors = [
        STATUS_COLORS.get(status, COLOR_PALETTE["secondary"]) for status in labels
    ]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                marker=dict(colors=colors),
                textinfo="label+percent",
                hovertemplate=(
                    "<b>%{label}</b><br>Count: %{value}<br>"
                    "Percent: %{percent}<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    return fig


def create_sprint_summary_card(
    progress_data: dict, show_points: bool, flow_wip_statuses: list[str]
) -> dict:
    """Create summary card data for sprint.

    Args:
        progress_data: Sprint progress metrics
        show_points: Whether to show story points
        flow_wip_statuses: List of WIP status names

    Returns:
        Dict with summary metrics
    """
    return {
        "total_issues": progress_data.get("total_issues", 0),
        "completed": progress_data.get("completed_issues", 0),
        "in_progress": progress_data.get("wip_issues", 0),
        "todo": progress_data.get("todo_issues", 0),
        "completion_pct": progress_data.get("completion_pct", 0),
        "total_points": progress_data.get("total_points", 0) if show_points else None,
        "completed_points": progress_data.get("completed_points", 0)
        if show_points
        else None,
        "wip_points": progress_data.get("wip_points", 0) if show_points else None,
        "todo_points": progress_data.get("todo_points", 0) if show_points else None,
        "points_completion_pct": progress_data.get("points_completion_pct", 0)
        if show_points
        else None,
    }
