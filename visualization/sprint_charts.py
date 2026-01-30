"""Sprint Tracker Visualization Module

This module provides functions to create sprint progress visualizations including:
- Horizontal stacked progress bars showing issue state transitions
- Sprint summary cards with completion metrics
- Timeline charts showing sprint composition changes

Uses Plotly for interactive charts following app design patterns.
"""

import logging
from typing import Dict, List, Optional
import plotly.graph_objects as go
from configuration import COLOR_PALETTE

logger = logging.getLogger(__name__)


# Status color mapping following Flow metrics pattern
STATUS_COLORS = {
    "To Do": COLOR_PALETTE["info"],  # Blue
    "In Progress": COLOR_PALETTE["warning"],  # Yellow
    "In Review": COLOR_PALETTE["secondary"],  # Orange
    "Code Review": COLOR_PALETTE["secondary"],  # Orange
    "Testing": COLOR_PALETTE["secondary"],  # Orange
    "Done": COLOR_PALETTE["success"],  # Green
    "Closed": COLOR_PALETTE["success"],  # Green
    "Resolved": COLOR_PALETTE["success"],  # Green
}


def create_sprint_progress_bars(
    sprint_data: Dict,
    changelog_entries: Optional[List[Dict]] = None,
    show_points: bool = False,
) -> go.Figure:
    """Create horizontal stacked progress bars for sprint issues.

    Each issue is represented as a horizontal stacked bar showing time spent
    in different statuses. Width is proportional to duration.

    Args:
        sprint_data: Sprint snapshot from sprint_manager.get_sprint_snapshots()
        changelog_entries: Status change history for time-in-status calculation
        show_points: Whether to show story points in labels

    Returns:
        Plotly Figure with stacked horizontal bars
    """
    logger.info(
        f"Creating progress bars for sprint: {sprint_data.get('name', 'Unknown')}"
    )

    issue_states = sprint_data.get("issue_states", {})
    if not issue_states:
        return _create_empty_sprint_chart("No issues in sprint")

    # Build progress bar data
    issue_keys = []
    bar_data = []

    for issue_key, state in issue_states.items():
        summary = state.get("summary", "")
        story_points = state.get("story_points", 0)
        current_status = state.get("status", "Unknown")

        # Build issue label
        if show_points and story_points:
            label = f"{issue_key} ({story_points}pts): {summary[:40]}"
        else:
            label = f"{issue_key}: {summary[:50]}"

        issue_keys.append(label)

        # Calculate time segments from changelog
        if changelog_entries:
            segments = _calculate_state_segments(issue_key, changelog_entries)
        else:
            # Fallback: show current status only
            segments = [
                {
                    "status": current_status,
                    "duration_hours": 1,  # Placeholder duration
                    "color": STATUS_COLORS.get(current_status, COLOR_PALETTE["muted"]),
                }
            ]

        bar_data.append(segments)

    # Create figure
    fig = go.Figure()

    # Add trace for each status (for legend grouping)
    status_traces_added = set()

    for idx, segments in enumerate(bar_data):
        for segment in segments:
            status = segment["status"]
            duration = segment["duration_hours"]
            color = segment["color"]

            # Add trace with legend only once per status
            show_legend = status not in status_traces_added
            if show_legend:
                status_traces_added.add(status)

            fig.add_trace(
                go.Bar(
                    name=status,
                    y=[issue_keys[idx]],
                    x=[duration],
                    orientation="h",
                    marker_color=color,
                    showlegend=show_legend,
                    hovertemplate=f"<b>{status}</b><br>"
                    + f"Duration: {duration:.1f}h<br>"
                    + "<extra></extra>",
                    legendgroup=status,
                )
            )

    # Update layout
    fig.update_layout(
        barmode="stack",
        title=f"Sprint Progress: {sprint_data.get('name', 'Sprint')}",
        xaxis_title="Time Spent (hours)",
        yaxis_title="Issues",
        height=max(
            400, min(len(issue_keys) * 25, 800)
        ),  # Dynamic height, capped at 800px
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="closest",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.update_xaxes(showgrid=True, gridcolor="lightgray")
    fig.update_yaxes(showgrid=False)

    return fig


def _calculate_state_segments(
    issue_key: str, changelog_entries: List[Dict]
) -> List[Dict]:
    """Calculate time spent in each status for an issue.

    Args:
        issue_key: JIRA issue key
        changelog_entries: Status change history

    Returns:
        List of segments with status, duration, and color
    """
    from datetime import datetime

    # Filter changelog to this issue and status field
    issue_changes = [
        entry
        for entry in changelog_entries
        if entry.get("issue_key") == issue_key and entry.get("field_name") == "status"
    ]

    if not issue_changes:
        return []

    # Sort by change date
    issue_changes.sort(key=lambda x: x.get("change_date", ""))

    segments = []
    for i, change in enumerate(issue_changes):
        status = change.get("new_value", "Unknown")
        start_time = datetime.fromisoformat(
            change.get("change_date", "").replace("Z", "+00:00")
        )

        # Calculate duration until next change or now
        if i < len(issue_changes) - 1:
            end_time = datetime.fromisoformat(
                issue_changes[i + 1].get("change_date", "").replace("Z", "+00:00")
            )
        else:
            end_time = datetime.now(start_time.tzinfo)

        duration_hours = (end_time - start_time).total_seconds() / 3600

        segments.append(
            {
                "status": status,
                "duration_hours": duration_hours,
                "color": STATUS_COLORS.get(status, COLOR_PALETTE["muted"]),
                "start_date": start_time.isoformat(),
                "end_date": end_time.isoformat(),
            }
        )

    return segments


def create_sprint_summary_card(
    progress_data: Dict, show_points: bool = False, wip_statuses: List[str] = None
) -> Dict:
    """Create summary statistics card data for sprint.

    Args:
        progress_data: Progress metrics from sprint_manager.calculate_sprint_progress()
        show_points: Whether to include story points metrics
        wip_statuses: List of WIP statuses from flow mappings (default: ["In Progress"])

    Returns:
        Dict with card display data:
        {
            "total_issues": 10,
            "completed": 7,
            "in_progress": 2,
            "completion_pct": 70.0,
            "total_points": 50.0,
            "completed_points": 35.0
        }
    """
    if wip_statuses is None:
        wip_statuses = ["In Progress"]

    card_data = {
        "total_issues": progress_data.get("total_issues", 0),
        "completed": progress_data.get("completed_issues", 0),
        "completion_pct": progress_data.get("completion_percentage", 0.0),
    }

    # Calculate in-progress count using WIP status mappings
    by_status = progress_data.get("by_status", {})
    in_progress_count = sum(
        status_data.get("count", 0)
        for status, status_data in by_status.items()
        if status in wip_statuses
    )
    card_data["in_progress"] = in_progress_count

    if show_points:
        card_data["total_points"] = progress_data.get("total_points", 0.0)
        card_data["completed_points"] = progress_data.get("completed_points", 0.0)
        card_data["points_completion_pct"] = progress_data.get(
            "points_completion_percentage", 0.0
        )

    return card_data


def create_sprint_timeline_chart(sprint_changes: Dict) -> go.Figure:
    """Create timeline showing when issues were added/removed from sprint.

    Args:
        sprint_changes: Sprint changes from sprint_manager.detect_sprint_changes()

    Returns:
        Plotly Figure with timeline markers
    """
    from datetime import datetime

    added_issues = sprint_changes.get("added", [])
    removed_issues = sprint_changes.get("removed", [])
    moved_in = sprint_changes.get("moved_in", [])
    moved_out = sprint_changes.get("moved_out", [])

    if not any([added_issues, removed_issues, moved_in, moved_out]):
        return _create_empty_sprint_chart("No sprint changes detected")

    fig = go.Figure()

    # Add "Added" events
    if added_issues:
        dates = [
            datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
            for e in added_issues
        ]
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[1] * len(dates),
                mode="markers",
                name="Added to Sprint",
                marker=dict(
                    size=12,
                    color=COLOR_PALETTE["success"],
                    symbol="circle",
                    line=dict(width=2, color="white"),
                ),
                text=[e["issue_key"] for e in added_issues],
                hovertemplate="<b>Added:</b> %{text}<br>"
                + "<b>Date:</b> %{x}<br>"
                + "<extra></extra>",
            )
        )

    # Add "Removed" events
    if removed_issues:
        dates = [
            datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
            for e in removed_issues
        ]
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[2] * len(dates),
                mode="markers",
                name="Removed from Sprint",
                marker=dict(
                    size=12,
                    color=COLOR_PALETTE["danger"],
                    symbol="x",
                    line=dict(width=2, color="white"),
                ),
                text=[e["issue_key"] for e in removed_issues],
                hovertemplate="<b>Removed:</b> %{text}<br>"
                + "<b>Date:</b> %{x}<br>"
                + "<extra></extra>",
            )
        )

    # Add "Moved In" events
    if moved_in:
        dates = [
            datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
            for e in moved_in
        ]
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[1.5] * len(dates),
                mode="markers",
                name="Moved In",
                marker=dict(
                    size=10,
                    color=COLOR_PALETTE["info"],
                    symbol="triangle-up",
                    line=dict(width=2, color="white"),
                ),
                text=[f"{e['issue_key']} (from {e['from']})" for e in moved_in],
                hovertemplate="<b>Moved In:</b> %{text}<br>"
                + "<b>Date:</b> %{x}<br>"
                + "<extra></extra>",
            )
        )

    # Add "Moved Out" events
    if moved_out:
        dates = [
            datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
            for e in moved_out
        ]
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=[2.5] * len(dates),
                mode="markers",
                name="Moved Out",
                marker=dict(
                    size=10,
                    color=COLOR_PALETTE["warning"],
                    symbol="triangle-down",
                    line=dict(width=2, color="white"),
                ),
                text=[f"{e['issue_key']} (to {e['to']})" for e in moved_out],
                hovertemplate="<b>Moved Out:</b> %{text}<br>"
                + "<b>Date:</b> %{x}<br>"
                + "<extra></extra>",
            )
        )

    # Update layout
    fig.update_layout(
        title="Sprint Composition Changes",
        xaxis_title="Date",
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[0.5, 3],
        ),
        height=300,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="closest",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.update_xaxes(showgrid=True, gridcolor="lightgray")

    return fig


def create_status_distribution_pie(progress_data: Dict) -> go.Figure:
    """Create pie chart showing issue distribution by status.

    Args:
        progress_data: Progress metrics from sprint_manager.calculate_sprint_progress()

    Returns:
        Plotly Figure with pie chart
    """
    by_status = progress_data.get("by_status", {})

    if not by_status:
        return _create_empty_sprint_chart("No status data available")

    statuses = list(by_status.keys())
    counts = [by_status[s].get("count", 0) for s in statuses]
    colors = [STATUS_COLORS.get(s, COLOR_PALETTE["muted"]) for s in statuses]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=statuses,
                values=counts,
                marker=dict(colors=colors, line=dict(color="white", width=2)),
                textposition="inside",
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>"
                + "Count: %{value}<br>"
                + "Percentage: %{percent}<br>"
                + "<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title="Issue Distribution by Status",
        height=400,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
    )

    return fig


def _create_empty_sprint_chart(message: str) -> go.Figure:
    """Create empty chart with informational message.

    Args:
        message: Message to display

    Returns:
        Plotly Figure with text annotation
    """
    fig = go.Figure()

    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color=COLOR_PALETTE["muted"]),
    )

    fig.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        height=300,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    return fig
