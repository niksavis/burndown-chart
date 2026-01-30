"""Sprint Tracker Visualization Module

This module provides functions to create sprint progress visualizations including:
- Simple horizontal bars showing issue status
- Sprint summary cards with completion metrics
- Timeline charts showing sprint composition changes

Uses Plotly with proper responsive configuration following app design patterns.
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
    """Create timeline bars showing status transitions for each issue over time.

    Each bar is horizontally stacked showing colored segments representing
    the percentage of time the issue spent in each status. This visualizes
    how issues progressed through the workflow.

    Args:
        sprint_data: Sprint snapshot from sprint_manager.get_sprint_snapshots()
        changelog_entries: Status change history (REQUIRED for timeline)
        show_points: Whether to show story points in labels

    Returns:
        Plotly Figure with stacked horizontal bars - fixed 400px height
    """
    logger.info(
        f"Creating timeline progress bars for sprint: {sprint_data.get('name', 'Unknown')}"
    )

    issue_states = sprint_data.get("issue_states", {})
    if not issue_states:
        return _create_empty_sprint_chart("No issues in sprint")

    if not changelog_entries:
        logger.warning("No changelog provided for timeline visualization")
        return _create_empty_sprint_chart(
            "No status history available - update data to fetch changelog"
        )

    # Import timeline calculation function
    from data.sprint_manager import calculate_issue_status_timeline

    # Build timeline data for each issue
    fig = go.Figure()

    issue_keys = sorted(issue_states.keys(), reverse=True)  # Newest at top

    for issue_key in issue_keys:
        state = issue_states[issue_key]
        summary = state.get("summary", "")

        # Calculate timeline segments
        timeline_segments = calculate_issue_status_timeline(
            issue_key, changelog_entries, include_current=True
        )

        if not timeline_segments:
            # No status history - show single bar with current status
            current_status = state.get("status", "Unknown")
            fig.add_trace(
                go.Bar(
                    name=current_status,
                    x=[100],  # 100% in current status
                    y=[issue_key],
                    orientation="h",
                    marker_color=STATUS_COLORS.get(
                        current_status, COLOR_PALETTE["muted"]
                    ),
                    text=[current_status],
                    textposition="inside",
                    hovertemplate=(
                        f"<b>{issue_key}</b><br>"
                        f"<b>Status:</b> {current_status}<br>"
                        f"<b>Summary:</b> {summary}<br>"
                        f"<b>Time:</b> No status history<br>"
                        "<extra></extra>"
                    ),
                    showlegend=True,
                )
            )
        else:
            # Show timeline segments
            for segment in timeline_segments:
                status = segment["status"]
                duration_pct = segment["duration_pct"]
                duration_hours = segment["duration_hours"]
                start_time = segment["start_time"]
                end_time = segment["end_time"]

                # Format time display
                duration_days = duration_hours / 24.0
                if duration_hours < 1:
                    time_str = f"{duration_hours * 60:.0f}min"
                elif duration_hours < 24:
                    time_str = f"{duration_hours:.1f}h"
                else:
                    time_str = f"{duration_days:.1f}d"

                # Create hover text
                hover_text = (
                    f"<b>{issue_key}</b><br>"
                    f"<b>Status:</b> {status}<br>"
                    f"<b>Duration:</b> {time_str} ({duration_pct:.1f}%)<br>"
                    f"<b>From:</b> {start_time.strftime('%Y-%m-%d %H:%M')}<br>"
                    f"<b>To:</b> {end_time.strftime('%Y-%m-%d %H:%M')}<br>"
                    f"<b>Summary:</b> {summary}<br>"
                    "<extra></extra>"
                )

                fig.add_trace(
                    go.Bar(
                        name=status,
                        x=[duration_pct],
                        y=[issue_key],
                        orientation="h",
                        marker_color=STATUS_COLORS.get(status, COLOR_PALETTE["muted"]),
                        text=[f"{duration_pct:.0f}%" if duration_pct > 5 else ""],
                        textposition="inside",
                        textangle=0,
                        hovertemplate=hover_text,
                        showlegend=True,
                        legendgroup=status,  # Group same statuses
                    )
                )

    # Fixed responsive layout
    fig.update_layout(
        autosize=False,  # Critical: disable autosize
        barmode="stack",  # Stack segments horizontally
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            title_text="Status",
        ),
        xaxis=dict(
            title="Time Distribution (%)",
            showticklabels=True,
            showgrid=True,
            zeroline=False,
            fixedrange=True,
            range=[0, 100],  # Percentage scale
        ),
        yaxis=dict(
            title="Issue",
            showgrid=False,
            fixedrange=True,  # Prevent zooming
        ),
        height=max(400, len(issue_keys) * 25),  # Dynamic height based on issue count
        width=None,  # Let width be responsive
        margin=dict(l=120, r=20, t=60, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="closest",
    )

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
    progress_data: Dict,
    show_points: bool = False,
    wip_statuses: Optional[List[str]] = None,
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
    """Create bar chart showing sprint composition changes.

    Args:
        sprint_changes: Sprint changes from sprint_manager.detect_sprint_changes()

    Returns:
        Plotly Figure with bar chart - fixed 350px height
    """
    added_count = len(sprint_changes.get("added", []))
    removed_count = len(sprint_changes.get("removed", []))
    moved_in_count = len(sprint_changes.get("moved_in", []))
    moved_out_count = len(sprint_changes.get("moved_out", []))

    if not any([added_count, removed_count, moved_in_count, moved_out_count]):
        return _create_empty_sprint_chart("No sprint changes detected")

    # Create simple bar chart
    fig = go.Figure()

    categories = []
    values = []
    colors_list = []

    if added_count > 0:
        categories.append("Added to Sprint")
        values.append(added_count)
        colors_list.append(COLOR_PALETTE["success"])

    if moved_in_count > 0:
        categories.append("Moved In")
        values.append(moved_in_count)
        colors_list.append(COLOR_PALETTE["info"])

    if moved_out_count > 0:
        categories.append("Moved Out")
        values.append(moved_out_count)
        colors_list.append(COLOR_PALETTE["warning"])

    if removed_count > 0:
        categories.append("Removed")
        values.append(removed_count)
        colors_list.append(COLOR_PALETTE["danger"])

    fig.add_trace(
        go.Bar(
            x=categories,
            y=values,
            marker_color=colors_list,
            text=values,
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
        )
    )

    fig.update_layout(
        autosize=False,  # Critical: disable autosize
        showlegend=False,
        xaxis_title="",
        yaxis_title="Issue Count",
        xaxis=dict(
            fixedrange=True,
        ),
        yaxis=dict(
            gridcolor="lightgray",
            fixedrange=True,
            range=[0, max(values) * 1.2]
            if values
            else [0, 10],  # Fixed range with 20% padding
        ),
        height=350,  # Fixed height
        width=None,  # Let width be responsive
        margin=dict(l=60, r=20, t=20, b=60),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    return fig


def create_status_distribution_pie(progress_data: Dict) -> go.Figure:
    """Create pie chart showing issue distribution by status.

    Args:
        progress_data: Progress metrics from sprint_manager.calculate_sprint_progress()

    Returns:
        Plotly Figure with pie chart - fixed 400px height
    """
    by_status = progress_data.get("by_status", {})

    if not by_status:
        return _create_empty_sprint_chart("No status data available")

    statuses = list(by_status.keys())
    counts = [by_status[s].get("count", 0) for s in statuses]
    colors_list = [STATUS_COLORS.get(s, COLOR_PALETTE["muted"]) for s in statuses]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=statuses,
                values=counts,
                marker=dict(colors=colors_list, line=dict(color="white", width=2)),
                hole=0.3,  # Donut chart
                textposition="auto",
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        autosize=False,  # CRITICAL: disable autosize
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
        height=400,  # Fixed height
        width=None,  # Let width be responsive
        margin=dict(l=20, r=100, t=20, b=20),
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
