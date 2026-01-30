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
    sprint_start_date: Optional[str] = None,
    sprint_end_date: Optional[str] = None,
) -> go.Figure:
    """Create progress bars showing status history over sprint timeline.

    Each bar represents one issue. Bar shows stacked colored segments representing
    the status at different points in the sprint timeline (0-100%).

    Example: Issue starts To Do (blue 0-30%), moves to In Progress (yellow 30-80%),
    then Done (green 80-100%).

    Args:
        sprint_data: Sprint snapshot from sprint_manager.get_sprint_snapshots()
        changelog_entries: Status change history (REQUIRED for timeline)
        show_points: Whether to show story points in labels
        sprint_start_date: Sprint start date from JIRA (ISO string)
        sprint_end_date: Sprint end date from JIRA (ISO string)

    Returns:
        Plotly Figure with stacked horizontal bars showing status over time
    """
    logger.info(
        f"Creating sprint progress bars for: {sprint_data.get('name', 'Unknown')}"
    )

    issue_states = sprint_data.get("issue_states", {})
    if not issue_states:
        return _create_empty_sprint_chart("No issues in sprint")

    if not sprint_start_date or not sprint_end_date:
        logger.warning(
            "Sprint dates not available - showing current status only (no timeline)"
        )
        return _create_simple_status_bars(issue_states, show_points)

    if not changelog_entries:
        logger.warning("No status changelog - cannot show status history")
        return _create_simple_status_bars(issue_states, show_points)

    # Parse sprint dates
    from datetime import datetime, timezone

    try:
        sprint_start = datetime.fromisoformat(sprint_start_date)
        sprint_end = datetime.fromisoformat(sprint_end_date)
        now = datetime.now(timezone.utc)

        total_duration = (sprint_end - sprint_start).total_seconds()
        if total_duration <= 0:
            logger.warning("Invalid sprint duration - start >= end")
            return _create_simple_status_bars(issue_states, show_points)

        logger.info(
            f"Sprint timeline: {sprint_start.strftime('%Y-%m-%d')} → {sprint_end.strftime('%Y-%m-%d')} "
            f"({total_duration / 86400:.1f} days)"
        )

    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse sprint dates: {e}")
        return _create_simple_status_bars(issue_states, show_points)

    # Build status timeline for each issue
    fig = go.Figure()
    issue_keys = sorted(issue_states.keys(), reverse=True)

    for issue_key in issue_keys:
        state = issue_states[issue_key]
        summary = state.get("summary", "")
        points = state.get("points", 0) if show_points else None
        current_status = state.get("status", "Unknown")

        label = issue_key
        if show_points and points:
            label = f"{issue_key} ({points}pt)"

        # Get status changes for this issue
        issue_changes = [
            entry for entry in changelog_entries if entry.get("issue_key") == issue_key
        ]

        if not issue_changes:
            # No history - show full bar with current status
            color = STATUS_COLORS.get(current_status, COLOR_PALETTE["secondary"])
            fig.add_trace(
                go.Bar(
                    x=[100],
                    y=[label],
                    orientation="h",
                    marker_color=color,
                    text=[current_status],
                    textposition="inside",
                    hovertemplate=(
                        f"<b>{issue_key}</b><br>"
                        f"<b>Status:</b> {current_status}<br>"
                        f"<b>Timeline:</b> Entire sprint<br>"
                        f"<b>Summary:</b> {summary}<br>"
                        + (
                            f"<b>Points:</b> {points}<br>"
                            if show_points and points
                            else ""
                        )
                        + "<extra></extra>"
                    ),
                    showlegend=False,
                )
            )
            continue

        # Build timeline segments
        segments = []
        sorted_changes = sorted(issue_changes, key=lambda x: x.get("timestamp", ""))

        # Find initial status (before sprint or first change)
        initial_status = sorted_changes[0].get("from_value") or "To Do"

        # Add segment from sprint start to first change
        first_timestamp = sorted_changes[0].get("timestamp")
        if not first_timestamp:
            # No valid timestamp - fall back to showing current status for full sprint
            logger.warning(
                f"Issue {issue_key} has changelog but no valid timestamps, showing current status"
            )
            color = STATUS_COLORS.get(current_status, COLOR_PALETTE["secondary"])
            fig.add_trace(
                go.Bar(
                    x=[100],
                    y=[label],
                    orientation="h",
                    marker_color=color,
                    text=[current_status],
                    textposition="inside",
                    hovertemplate=(
                        f"<b>{issue_key}</b><br>"
                        f"<b>Status:</b> {current_status}<br>"
                        f"<b>Timeline:</b> Entire sprint (no timestamp data)<br>"
                        f"<b>Summary:</b> {summary}<br>"
                        + (
                            f"<b>Points:</b> {points}<br>"
                            if show_points and points
                            else ""
                        )
                        + "<extra></extra>"
                    ),
                    showlegend=False,
                )
            )
            continue

        first_change_time = datetime.fromisoformat(first_timestamp)
        first_change_pct = max(
            0, (first_change_time - sprint_start).total_seconds() / total_duration * 100
        )

        if first_change_pct > 0:
            segments.append(
                {
                    "status": initial_status,
                    "start_pct": 0,
                    "end_pct": first_change_pct,
                    "start_date": sprint_start,
                    "end_date": first_change_time,
                }
            )

        # Process each status change
        for i, change in enumerate(sorted_changes):
            change_timestamp = change.get("timestamp")
            if not change_timestamp:
                continue
            change_time = datetime.fromisoformat(change_timestamp)
            change_pct = (
                (change_time - sprint_start).total_seconds() / total_duration * 100
            )
            new_status = change.get("to_value", "Unknown")

            # Find next change or use sprint end
            if i + 1 < len(sorted_changes):
                next_timestamp = sorted_changes[i + 1].get("timestamp")
                if not next_timestamp:
                    next_change_time = min(now, sprint_end)
                    next_pct = min(
                        100,
                        (next_change_time - sprint_start).total_seconds()
                        / total_duration
                        * 100,
                    )
                else:
                    next_change_time = datetime.fromisoformat(next_timestamp)
                    next_pct = (
                        (next_change_time - sprint_start).total_seconds()
                        / total_duration
                        * 100
                    )
            else:
                # Last segment goes to sprint end (or now if sprint still active)
                next_change_time = min(now, sprint_end)
                next_pct = min(
                    100,
                    (next_change_time - sprint_start).total_seconds()
                    / total_duration
                    * 100,
                )

            segments.append(
                {
                    "status": new_status,
                    "start_pct": change_pct,
                    "end_pct": next_pct,
                    "start_date": change_time,
                    "end_date": next_change_time,
                }
            )

        # Create stacked bar from segments
        for segment in segments:
            width = segment["end_pct"] - segment["start_pct"]
            if width <= 0:
                continue

            status = segment["status"]
            color = STATUS_COLORS.get(status, COLOR_PALETTE["secondary"])

            duration_days = (
                segment["end_date"] - segment["start_date"]
            ).total_seconds() / 86400

            fig.add_trace(
                go.Bar(
                    x=[width],
                    y=[label],
                    orientation="h",
                    marker_color=color,
                    text=[status if width > 8 else ""],
                    textposition="inside",
                    textangle=0,
                    hovertemplate=(
                        f"<b>{issue_key}</b><br>"
                        f"<b>Status:</b> {status}<br>"
                        f"<b>Duration:</b> {duration_days:.1f} days ({width:.1f}%)<br>"
                        f"<b>From:</b> {segment['start_date'].strftime('%b %d')}<br>"
                        f"<b>To:</b> {segment['end_date'].strftime('%b %d')}<br>"
                        f"<b>Summary:</b> {summary}<br>"
                        + (
                            f"<b>Points:</b> {points}<br>"
                            if show_points and points
                            else ""
                        )
                        + "<extra></extra>"
                    ),
                    showlegend=False,
                )
            )

    # Layout
    fig.update_layout(
        autosize=False,
        barmode="stack",
        showlegend=False,
        xaxis=dict(
            title=f"Sprint Timeline: {sprint_start.strftime('%b %d')} → {sprint_end.strftime('%b %d, %Y')}",
            showticklabels=True,
            showgrid=True,
            zeroline=False,
            fixedrange=True,
            range=[0, 100],
            ticksuffix="%",
        ),
        yaxis=dict(
            title="Issue",
            showgrid=False,
            fixedrange=True,
            automargin=True,
        ),
        height=max(400, len(issue_keys) * 35),
        width=None,
        margin=dict(l=150, r=20, t=60, b=60),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="closest",
    )

    return fig


def _create_simple_status_bars(
    issue_states: Dict, show_points: bool = False
) -> go.Figure:
    """Fallback visualization when sprint dates unavailable.

    Shows simple bars colored by current status without timeline progression.

    Args:
        issue_states: Issue state dict from sprint snapshot
        show_points: Whether to show story points

    Returns:
        Plotly Figure with simple status bars
    """
    fig = go.Figure()

    issue_keys = sorted(issue_states.keys(), reverse=True)

    for issue_key in issue_keys:
        state = issue_states[issue_key]
        status = state.get("status", "Unknown")
        summary = state.get("summary", "")
        points = state.get("points", 0) if show_points else None

        label = issue_key
        if show_points and points:
            label = f"{issue_key} ({points}pt)"

        color = STATUS_COLORS.get(status, COLOR_PALETTE["muted"])

        fig.add_trace(
            go.Bar(
                x=[100],
                y=[label],
                orientation="h",
                marker_color=color,
                text=[status],
                textposition="inside",
                hovertemplate=(
                    f"<b>{issue_key}</b><br>"
                    f"<b>Status:</b> {status}<br>"
                    f"<b>Summary:</b> {summary}<br>"
                    + (f"<b>Points:</b> {points}<br>" if show_points and points else "")
                    + "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    fig.update_layout(
        autosize=False,
        barmode="overlay",
        showlegend=False,
        xaxis=dict(
            title="Current Status (Sprint dates unavailable)",
            showticklabels=False,
            showgrid=False,
            fixedrange=True,
            range=[0, 100],
        ),
        yaxis=dict(
            title="Issue",
            showgrid=False,
            fixedrange=True,
            automargin=True,
        ),
        height=max(400, len(issue_keys) * 35),
        width=None,
        margin=dict(l=150, r=20, t=60, b=60),
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
