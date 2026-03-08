"""Multi-segment bar builder and per-issue bar processing for sprint progress bars."""

import logging
from datetime import datetime

from dash import html

from utils.jira_link_utils import create_jira_issue_link

from ._bar_single import _create_single_status_bar
from ._status import _get_issue_type_icon, _get_status_color

logger = logging.getLogger(__name__)


def _process_issue_bar(
    issue_key: str,
    state: dict,
    changelog_entries: list[dict],
    sprint_start: datetime | None,
    sprint_end: datetime | None,
    now: datetime,
    sprint_duration_seconds: float,
    show_points: bool,
    added_issues: set,
    removed_issues: set,
    flow_start_statuses: list[str],
    flow_wip_statuses: list[str],
    flow_end_statuses: list[str],
) -> tuple[html.Div, list[dict]]:
    """Process one sprint issue and return its bar component and time segments.

    Args:
        issue_key: JIRA issue key
        state: Issue state dict with status, summary, points, issue_type
        changelog_entries: Full status changelog (filtered internally per issue)
        sprint_start: Sprint start datetime
        sprint_end: Sprint end datetime
        now: Current datetime
        sprint_duration_seconds: Total sprint duration in seconds
        show_points: Whether to show story points
        added_issues: Set of issue keys added after sprint started
        removed_issues: Set of issue keys removed from sprint
        flow_start_statuses: Start statuses from flow config
        flow_wip_statuses: WIP statuses from flow config
        flow_end_statuses: End statuses from flow config

    Returns:
        Tuple of (bar_component, time_segments_for_legend).
        time_segments is empty for single-status bars.
    """
    summary = state.get("summary", "")
    points = state.get("points", 0) if show_points else None
    current_status = state.get("status", "Unknown")
    issue_type = state.get("issue_type", "Unknown")

    # Get status changes for this issue
    issue_changes = [
        entry for entry in changelog_entries if entry.get("issue_key") == issue_key
    ]

    logger.info(
        f"[SPRINT PROGRESS] Issue {issue_key}: "
        f"Found {len(issue_changes)} status changes"
    )

    is_added = issue_key in added_issues
    is_removed = issue_key in removed_issues
    is_initial = not is_added and not is_removed

    if not issue_changes:
        # No history - show full bar with current status
        bar = _create_single_status_bar(
            issue_key,
            summary,
            current_status,
            points,
            show_points,
            flow_start_statuses,
            flow_wip_statuses,
            flow_end_statuses,
            issue_type=issue_type,
            sprint_start=sprint_start,
            sprint_end=sprint_end,
            now=now,
            is_added=is_added,
            is_removed=is_removed,
            is_initial=is_initial,
        )
        return bar, []

    # Calculate time spent in each status
    sorted_changes = sorted(issue_changes, key=lambda x: x.get("change_date", ""))

    # Build time segments
    time_segments: list[dict] = []

    # Get first valid timestamp
    first_timestamp = None
    initial_status = None
    for change in sorted_changes:
        ts = change.get("change_date")
        if ts:
            first_timestamp = ts
            initial_status = change.get("old_value") or "To Do"
            break

    if not first_timestamp:
        # No valid timestamps - show current status
        logger.warning(f"Issue {issue_key} has changelog but no valid timestamps")
        bar = _create_single_status_bar(
            issue_key,
            summary,
            current_status,
            points,
            show_points,
            flow_start_statuses,
            flow_wip_statuses,
            flow_end_statuses,
            issue_type=issue_type,
            sprint_start=sprint_start,
            sprint_end=sprint_end,
            now=now,
            is_added=is_added,
            is_removed=is_removed,
            is_initial=is_initial,
        )
        return bar, []

    # Process status changes to build time segments
    # Include ALL statuses (even To Do) from sprint start
    first_time = datetime.fromisoformat(first_timestamp)

    # If sprint has a start date, use that as the beginning; otherwise use first change
    if sprint_start and sprint_start < first_time:
        timeline_start = sprint_start
        current_seg_status = initial_status or "To Do"
    else:
        timeline_start = first_time
        current_seg_status = initial_status

    current_seg_start = timeline_start

    for change in sorted_changes:
        ts = change.get("change_date")
        if not ts:
            continue

        change_time = datetime.fromisoformat(ts)
        new_status = change.get("new_value", "Unknown")

        # Close previous segment
        duration = (change_time - current_seg_start).total_seconds()
        if duration > 0:
            time_segments.append(
                {
                    "status": current_seg_status,
                    "start_time": current_seg_start,
                    "end_time": change_time,
                    "duration_seconds": duration,
                }
            )

        # Start new segment
        current_seg_status = new_status
        current_seg_start = change_time

    # Close final segment from last change to NOW
    final_duration = (now - current_seg_start).total_seconds()
    if final_duration > 0:
        time_segments.append(
            {
                "status": current_status,  # Use current_status from issue state
                "start_time": current_seg_start,
                "end_time": now,
                "duration_seconds": final_duration,
            }
        )
    logger.info(
        f"[SPRINT PROGRESS] Issue {issue_key}: Built {len(time_segments)} time segments"
    )

    # Calculate total time from sprint start (or first change) to now
    total_duration = sum(seg["duration_seconds"] for seg in time_segments)
    if total_duration == 0:
        bar = _create_single_status_bar(
            issue_key,
            summary,
            current_status,
            points,
            show_points,
            flow_start_statuses,
            flow_wip_statuses,
            flow_end_statuses,
            issue_type=issue_type,
            sprint_start=sprint_start,
            sprint_end=sprint_end,
            now=now,
            is_added=is_added,
            is_removed=is_removed,
            is_initial=is_initial,
        )
        return bar, []

    # Calculate elapsed time from sprint start to now
    if sprint_start:
        elapsed_time = (now - sprint_start).total_seconds()
    else:
        # If no sprint start, use time from first change to now
        elapsed_time = total_duration

    # Calculate what percentage of sprint has elapsed (0% at start, 100% at end)
    time_progress_percentage = min(100, (elapsed_time / sprint_duration_seconds) * 100)

    # Remaining sprint time (empty gray area)
    remaining_percentage = max(0, 100 - time_progress_percentage)

    # Create progress bar with segments
    bar = _create_multi_segment_bar(
        issue_key,
        summary,
        time_segments,
        total_duration,
        time_progress_percentage,
        remaining_percentage,
        sprint_duration_seconds,
        points,
        show_points,
        flow_start_statuses,
        flow_wip_statuses,
        flow_end_statuses,
        issue_type=issue_type,
        is_added=is_added,
        is_removed=is_removed,
        is_initial=is_initial,
    )
    return bar, time_segments


def _create_multi_segment_bar(
    issue_key: str,
    summary: str,
    time_segments: list[dict],
    total_duration: float,
    time_progress_percentage: float,
    remaining_percentage: float,
    sprint_duration_seconds: float,
    points: float | None,
    show_points: bool,
    flow_start_statuses: list[str],
    flow_wip_statuses: list[str],
    flow_end_statuses: list[str],
    issue_type: str = "Unknown",
    is_added: bool = False,
    is_removed: bool = False,
    is_initial: bool = False,
):
    """Create a multi-segment progress bar scaled to sprint timeline.

    Args:
        issue_key: JIRA issue key
        summary: Issue summary
        time_segments: Time spent in each status (from sprint start to now)
        total_duration: Total time from start to now in seconds
        time_progress_percentage: How much of sprint has elapsed (0-100%)
        remaining_percentage: Remaining sprint time percentage
        sprint_duration_seconds: Total sprint duration in seconds
        points: Story points
        show_points: Whether to show points
        flow_start_statuses: Start statuses
        flow_wip_statuses: WIP statuses
        flow_end_statuses: End statuses
        issue_type: Issue type (Bug, Task, Story, etc.)
        is_added: Whether issue was added to sprint after it started
        is_removed: Whether issue was removed from sprint
        is_initial: Whether issue was present at sprint start
    """
    # Get issue type icon and color
    icon_class, icon_color = _get_issue_type_icon(issue_type)

    # Truncate long summaries
    display_summary = summary[:80] + "..." if len(summary) > 80 else summary

    # Create sprint scope change indicator (circular icon before issue type icon)
    scope_indicator = None
    if is_added:
        scope_indicator = html.Span(
            [
                html.I(
                    className="fa-solid fa-circle-plus",
                    style={
                        "color": "#28a745",  # Green (bg-success)
                        "fontSize": "0.9rem",
                        "marginRight": "6px",
                    },
                    title="Added to sprint after it started",
                )
            ]
        )
    elif is_removed:
        scope_indicator = html.Span(
            [
                html.I(
                    className="fa-solid fa-circle-minus",
                    style={
                        "color": "#dc3545",  # Red (bg-danger)
                        "fontSize": "0.9rem",
                        "marginRight": "6px",
                    },
                    title="Removed from sprint",
                )
            ]
        )
    elif is_initial:
        scope_indicator = html.Span(
            [
                html.I(
                    className="fa-solid fa-circle-dot",
                    style={
                        "color": "#6c757d",  # Gray (bg-secondary)
                        "fontSize": "0.9rem",  # Same size as plus/minus icons
                        "marginRight": "6px",
                        "opacity": "0.7",
                    },
                    title="Present at sprint start",
                )
            ]
        )

    points_badge = (
        html.Span(
            f"{points}pt",
            className="badge bg-secondary ms-2",
            style={"fontSize": "0.75rem"},
        )
        if show_points and points
        else None
    )

    # Build segments scaled to elapsed sprint time
    segments = []
    total_rendered_percentage = 0  # Track actually rendered percentage

    for segment in time_segments:
        status = segment["status"]
        # Calculate percentage of TOTAL ELAPSED TIME (not sprint duration)
        duration_pct_of_elapsed = (segment["duration_seconds"] / total_duration) * 100
        # Scale to sprint timeline: elapsed time fills X% of sprint,
        # this segment is Y% of elapsed
        duration_pct_of_sprint = (
            duration_pct_of_elapsed / 100
        ) * time_progress_percentage
        duration_days = segment["duration_seconds"] / 86400

        if duration_pct_of_sprint < 0.3:  # Skip tiny segments
            continue

        # Track what we're actually rendering
        total_rendered_percentage += duration_pct_of_sprint

        # Use dynamic color based on flow configuration
        color = _get_status_color(
            status, flow_start_statuses, flow_wip_statuses, flow_end_statuses
        )

        # Format duration display
        if duration_days < 1:
            duration_str = f"{segment['duration_seconds'] / 3600:.1f}h"
        else:
            duration_str = f"{duration_days:.1f}d"

        # Show percentage of SPRINT DURATION (not elapsed time) - white text
        percentage_text = (
            f"{duration_pct_of_sprint:.0f}%" if duration_pct_of_sprint > 4 else ""
        )

        segments.append(
            html.Div(
                percentage_text,
                title=(
                    f"{status}: {duration_str} "
                    f"({duration_pct_of_sprint:.0f}% of sprint duration)"
                ),
                style={
                    "width": f"{duration_pct_of_sprint}%",
                    "backgroundColor": color,
                    "color": "white",  # Always white text
                    "textAlign": "center",
                    "padding": "8px 4px",
                    "fontSize": "0.75rem",
                    "fontWeight": "500",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                },
            )
        )

    # Calculate gap from skipped segments or issue starting after sprint start
    # This gap should be shown before the issue segments
    gap_before_issue = time_progress_percentage - total_rendered_percentage

    # If there's a gap, add it as a light segment at the beginning
    if gap_before_issue > 0.1:
        # Insert at beginning
        segments.insert(
            0,
            html.Div(
                "",
                title=f"Before issue activity: {gap_before_issue:.1f}%",
                style={
                    "width": f"{gap_before_issue}%",
                    "backgroundColor": "#f8f9fa",  # Very light gray
                    "borderRight": "1px solid #dee2e6",
                },
            ),
        )

    # Add remaining sprint time - use the ORIGINAL remaining_percentage
    # (based on sprint dates, same for all issues)
    if remaining_percentage > 0:
        segments.append(
            html.Div(
                "",
                title=f"Remaining sprint time: {remaining_percentage:.1f}%",
                style={
                    "width": f"{remaining_percentage}%",
                    "backgroundColor": "#e9ecef",  # Light gray for remaining time
                    "borderLeft": "1px solid #dee2e6",
                },
            )
        )

    return html.Div(
        [
            # Issue header
            html.Div(
                [
                    scope_indicator,  # Scope change indicator (before issue type)
                    html.I(
                        className=f"fas {icon_class} me-2",
                        style={
                            "color": icon_color,
                            "fontSize": "0.85rem",
                        },
                        title=issue_type,
                    ),
                    create_jira_issue_link(
                        issue_key,
                        className="fw-bold",
                        style={"fontSize": "0.9rem", "color": "#495057"},
                    ),
                    points_badge,
                    html.Span(
                        display_summary,
                        className="text-muted ms-2",
                        style={"fontSize": "0.85rem"},
                    ),
                ],
                className="mb-1",
            ),
            # Progress bar with segments
            html.Div(
                html.Div(
                    segments,
                    style={
                        "display": "flex",
                        "width": "100%",
                        "height": "32px",
                        "backgroundColor": "#e9ecef",
                        "borderRadius": "4px",
                        "overflow": "hidden",
                    },
                ),
                className="mb-3",
            ),
        ],
        className="progress-bar-item",
    )
