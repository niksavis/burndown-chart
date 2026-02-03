"""Sprint Tracker Visualization Module

This module provides functions to create sprint progress visualizations including:
- HTML progress bars showing time proportions in each status
- Sprint summary cards with completion metrics
- Timeline charts showing sprint composition changes

Uses HTML/CSS progress bars for better rendering and control.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from dash import html
from configuration import COLOR_PALETTE
import plotly.graph_objects as go
from ui.jira_link_helper import create_jira_issue_link

logger = logging.getLogger(__name__)


# Status color mapping (fallback only - prefer dynamic mapping from flow config)
STATUS_COLORS = {
    "To Do": "#6c757d",  # Gray (start state)
    "Backlog": "#6c757d",  # Gray (start state)
    "Open": "#6c757d",  # Gray (start state)
    "Analysis": "#0dcaf0",  # Cyan (WIP)
    "In Progress": "#0d6efd",  # Blue (WIP)
    "In Review": "#9b59b6",  # Purple (WIP)
    "Code Review": "#9b59b6",  # Purple (WIP)
    "Ready for Testing": "#f39c12",  # Amber (WIP)
    "Testing": "#e67e22",  # Orange (WIP)
    "In Deployment": "#d63384",  # Magenta/Pink (WIP - distinct from green Done)
    "Done": "#28a745",  # Green (end state)
    "Closed": "#28a745",  # Green (end state)
    "Resolved": "#28a745",  # Green (end state)
}


def _get_issue_type_icon(issue_type: str) -> tuple:
    """Get Font Awesome icon and color for issue type.

    Args:
        issue_type: Issue type (Bug, Task, Story, etc.)

    Returns:
        Tuple of (icon_class, color_hex)
    """
    issue_type_lower = issue_type.lower()

    if "bug" in issue_type_lower or "defect" in issue_type_lower:
        return ("fa-bug", "#dc3545")  # Red for bugs
    elif "task" in issue_type_lower or "sub-task" in issue_type_lower:
        return ("fa-tasks", "#0d6efd")  # Blue for tasks
    elif "story" in issue_type_lower or "user story" in issue_type_lower:
        return ("fa-book", "#198754")  # Green for stories
    elif "epic" in issue_type_lower:
        return ("fa-flag", "#6f42c1")  # Purple for epics
    else:
        return ("fa-circle", "#6c757d")  # Gray circle for unknown


def _get_status_color(
    status: str,
    flow_start_statuses: List[str],
    flow_wip_statuses: List[str],
    flow_end_statuses: List[str],
) -> str:
    """Get color for a status based on flow configuration.

    Args:
        status: Status name
        flow_start_statuses: Start statuses from flow config (e.g., To Do)
        flow_wip_statuses: WIP statuses from flow config (e.g., In Progress)
        flow_end_statuses: End statuses from flow config (e.g., Done)

    Returns:
        Hex color code
    """
    # Check if we have a specific color defined for this status first
    if status in STATUS_COLORS:
        return STATUS_COLORS[status]

    # Fall back to flow-based generic colors
    if status in flow_start_statuses:
        return "#6c757d"  # Gray for start states
    elif status in flow_wip_statuses:
        # Cycle through distinct WIP colors (never green or gray)
        wip_colors = [
            "#0d6efd",  # Blue
            "#9b59b6",  # Purple
            "#f39c12",  # Amber
            "#e67e22",  # Orange
            "#0dcaf0",  # Cyan
            "#d63384",  # Magenta/Pink
        ]
        wip_index = flow_wip_statuses.index(status) % len(wip_colors)
        return wip_colors[wip_index]
    elif status in flow_end_statuses:
        return COLOR_PALETTE["success"]  # Green for done states

    # Final fallback
    return COLOR_PALETTE["secondary"]


def _create_status_legend(
    time_segments: List[Dict],
    flow_start_statuses: List[str],
    flow_wip_statuses: List[str],
    flow_end_statuses: List[str],
    changelog_entries: Optional[List[Dict]] = None,
) -> html.Div:
    """Create a legend showing all statuses ordered by their position in workflow.

    Uses actual changelog data to determine natural status order by calculating
    the average position each status appears in issue lifecycles.

    Args:
        time_segments: List of time segments with status information
        flow_start_statuses: Start statuses from flow config
        flow_wip_statuses: WIP statuses from flow config
        flow_end_statuses: End statuses from flow config
        changelog_entries: Status change history for position analysis

    Returns:
        Dash HTML component with legend items
    """
    # Get unique statuses from all time segments
    unique_statuses = set([seg["status"] for seg in time_segments])

    # Build status order using flow configuration:
    # Start → WIP → End, with remaining alphabetically
    statuses = []
    seen = set()

    # Ensure flow lists are not None
    start_statuses = flow_start_statuses or []
    wip_statuses = flow_wip_statuses or []
    end_statuses = flow_end_statuses or []

    # Common start statuses that should always come first (if present)
    common_start = ["To Do", "Backlog", "Open", "New", "Selected for Development"]
    for status in common_start:
        if status in unique_statuses and status not in seen:
            statuses.append(status)
            seen.add(status)

    # Add start statuses first
    for status in start_statuses:
        if status in unique_statuses and status not in seen:
            statuses.append(status)
            seen.add(status)

    # Add WIP statuses next
    for status in wip_statuses:
        if status in unique_statuses and status not in seen:
            statuses.append(status)
            seen.add(status)

    # Add end statuses last
    for status in end_statuses:
        if status in unique_statuses and status not in seen:
            statuses.append(status)
            seen.add(status)

    # Add remaining statuses alphabetically (but exclude common end statuses for now)
    common_end = ["Done", "Closed", "Resolved", "Cancelled", "Rejected"]
    remaining = sorted(
        [s for s in unique_statuses if s not in seen and s not in common_end]
    )
    statuses.extend(remaining)
    seen.update(remaining)

    # Common end statuses always go last (if present)
    for status in common_end:
        if status in unique_statuses and status not in seen:
            statuses.append(status)
            seen.add(status)

    # Build legend items
    legend_items = []
    for status in statuses:
        color = _get_status_color(
            status, flow_start_statuses, flow_wip_statuses, flow_end_statuses
        )
        legend_items.append(
            html.Span(
                [
                    html.Span(
                        style={
                            "display": "inline-block",
                            "width": "16px",
                            "height": "16px",
                            "backgroundColor": color,
                            "borderRadius": "3px",
                            "marginRight": "6px",
                            "verticalAlign": "middle",
                        }
                    ),
                    html.Span(
                        status,
                        style={
                            "fontSize": "0.85rem",
                            "color": "#495057",
                            "verticalAlign": "middle",
                        },
                    ),
                ],
                style={"marginRight": "20px", "display": "inline-block"},
            )
        )

    return html.Div(
        legend_items,
        style={
            "marginBottom": "15px",
            "padding": "10px",
            "backgroundColor": "#f8f9fa",
            "borderRadius": "4px",
            "display": "flex",
            "flexWrap": "wrap",
            "gap": "10px",
        },
    )


def create_sprint_progress_bars(
    sprint_data: Dict,
    changelog_entries: Optional[List[Dict]] = None,
    show_points: bool = False,
    sprint_start_date: Optional[str] = None,
    sprint_end_date: Optional[str] = None,
    flow_start_statuses: Optional[List[str]] = None,
    flow_wip_statuses: Optional[List[str]] = None,
    flow_end_statuses: Optional[List[str]] = None,
    sprint_changes: Optional[Dict] = None,
    sprint_state: Optional[str] = None,
    scope_changes: Optional[Dict] = None,
):
    """Create HTML progress bars showing time proportion spent in each status.

    Each bar represents one issue with colored segments showing the PERCENTAGE
    of time the issue spent in each status (like a pie chart spread horizontally).

    Example: Issue spent 30% in To Do, 50% in Progress, 20% in Done
    Bar shows: [Gray 30%][Blue 50%][Green 20%]

    Args:
        sprint_data: Sprint snapshot from sprint_manager.get_sprint_snapshots()
        changelog_entries: Status change history (REQUIRED for time calculation)
        show_points: Whether to show story points
        sprint_start_date: Sprint start date (ISO format)
        sprint_end_date: Sprint end date (ISO format)
        flow_start_statuses: List of start statuses
        flow_wip_statuses: List of WIP statuses
        flow_end_statuses: List of end statuses
        sprint_changes: Dict with added/removed/moved_in/moved_out issue lists
        sprint_state: Sprint state (ACTIVE/CLOSED/FUTURE)
        scope_changes: Dict with added/removed/net_change counts for badges
        show_points: Whether to show story points in labels
        sprint_start_date: Sprint start date from JIRA (ISO string)
        sprint_end_date: Sprint end date from JIRA (ISO string)
        flow_start_statuses: Start statuses from flow config (e.g., ["To Do"])
        flow_wip_statuses: WIP statuses from flow config (e.g., ["In Progress"])
        flow_end_statuses: End statuses from flow config (e.g., ["Done", "Closed"])
        sprint_changes: Sprint changes dict with added/removed/moved_in/moved_out lists

    Returns:
        Dash HTML component with styled progress bars
    """
    # Default flow states if not provided or empty
    if not flow_start_statuses:
        flow_start_statuses = ["To Do", "Backlog", "Open"]
    if not flow_wip_statuses:
        flow_wip_statuses = ["In Progress", "In Review", "Testing"]
    if not flow_end_statuses:
        flow_end_statuses = ["Done", "Closed", "Resolved"]

    # Create sets for quick lookup of added/removed issues
    added_issues = set()
    removed_issues = set()
    if sprint_changes:
        added_issues = {item["issue_key"] for item in sprint_changes.get("added", [])}
        removed_issues = {
            item["issue_key"] for item in sprint_changes.get("removed", [])
        }
    logger.info(
        f"Creating sprint progress bars for: {sprint_data.get('name', 'Unknown')}"
    )

    issue_states = sprint_data.get("issue_states", {})
    if not issue_states:
        return html.Div("No issues in sprint", className="text-muted text-center p-4")

    if not changelog_entries:
        logger.warning("No status changelog - showing current status only")

        # Parse sprint dates even for simple bars
        sprint_start = None
        sprint_end = None
        now = datetime.now(timezone.utc)

        try:
            if sprint_start_date:
                sprint_start = datetime.fromisoformat(sprint_start_date)
                if sprint_start.tzinfo is None:
                    sprint_start = sprint_start.replace(tzinfo=timezone.utc)

            if sprint_end_date:
                sprint_end = datetime.fromisoformat(sprint_end_date)
                if sprint_end.tzinfo is None:
                    sprint_end = sprint_end.replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError) as e:
            logger.error(f"Failed to parse sprint dates: {e}")

        return _create_simple_html_bars(
            issue_states,
            show_points,
            flow_start_statuses,
            flow_wip_statuses,
            flow_end_statuses,
            sprint_start=sprint_start,
            sprint_end=sprint_end,
            now=now,
        )

    # Parse sprint dates to calculate sprint duration
    sprint_duration_seconds = None
    sprint_start = None
    sprint_end = None
    now = datetime.now(timezone.utc)

    try:
        if sprint_start_date:
            sprint_start = datetime.fromisoformat(sprint_start_date)
            if sprint_start.tzinfo is None:
                sprint_start = sprint_start.replace(tzinfo=timezone.utc)

        if sprint_end_date:
            sprint_end = datetime.fromisoformat(sprint_end_date)
            if sprint_end.tzinfo is None:
                sprint_end = sprint_end.replace(tzinfo=timezone.utc)

        # Calculate sprint duration
        if sprint_start and sprint_end:
            sprint_duration_seconds = (sprint_end - sprint_start).total_seconds()
            logger.info(
                f"[SPRINT PROGRESS] Sprint duration: {sprint_duration_seconds / 86400:.1f} days"
            )
        else:
            logger.warning("Sprint dates not provided - using default 14 days")
            sprint_duration_seconds = 14 * 86400  # Default 14 days

    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse sprint dates: {e}")
        sprint_duration_seconds = 14 * 86400  # Default 14 days

    # Build HTML progress bars for each issue
    issue_keys = sorted(issue_states.keys(), reverse=True)

    logger.info(
        f"[SPRINT PROGRESS] Building progress bars for {len(issue_keys)} issues"
    )
    logger.info(
        f"[SPRINT PROGRESS] Received {len(changelog_entries)} changelog entries"
    )

    progress_bars = []
    all_time_segments = []  # Collect all segments for legend

    for issue_key in issue_keys:
        state = issue_states[issue_key]
        summary = state.get("summary", "")
        points = state.get("points", 0) if show_points else None
        current_status = state.get("status", "Unknown")
        issue_type = state.get("issue_type", "Unknown")

        # Get status changes for this issue
        issue_changes = [
            entry for entry in changelog_entries if entry.get("issue_key") == issue_key
        ]

        logger.info(
            f"[SPRINT PROGRESS] Issue {issue_key}: Found {len(issue_changes)} status changes"
        )

        if not issue_changes:
            # No history - show full bar with current status
            is_added = issue_key in added_issues
            is_removed = issue_key in removed_issues
            progress_bars.append(
                _create_single_status_bar(
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
                    is_initial=not is_added and not is_removed,
                )
            )
            continue

        # Calculate time spent in each status
        sorted_changes = sorted(issue_changes, key=lambda x: x.get("change_date", ""))

        # Build time segments
        time_segments = []

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
            is_added = issue_key in added_issues
            is_removed = issue_key in removed_issues
            progress_bars.append(
                _create_single_status_bar(
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
                    is_initial=not is_added and not is_removed,
                )
            )
            continue

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
            is_added = issue_key in added_issues
            is_removed = issue_key in removed_issues
            progress_bars.append(
                _create_single_status_bar(
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
                    is_initial=not is_added and not is_removed,
                )
            )
            continue

        # Calculate elapsed time from sprint start to now
        if sprint_start:
            elapsed_time = (now - sprint_start).total_seconds()
        else:
            # If no sprint start, use time from first change to now
            elapsed_time = total_duration

        # Calculate what percentage of sprint has elapsed (0% at start, 100% at end)
        time_progress_percentage = min(
            100, (elapsed_time / sprint_duration_seconds) * 100
        )

        # Remaining sprint time (empty gray area)
        remaining_percentage = max(0, 100 - time_progress_percentage)

        # Create progress bar with segments
        all_time_segments.extend(time_segments)  # Collect for legend
        is_added = issue_key in added_issues
        is_removed = issue_key in removed_issues
        progress_bars.append(
            _create_multi_segment_bar(
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
                is_initial=not is_added and not is_removed,
            )
        )

    # Create legend if we have time segments
    legend = None
    if all_time_segments:
        legend = _create_status_legend(
            all_time_segments,
            flow_start_statuses,
            flow_wip_statuses,
            flow_end_statuses,
            changelog_entries,  # Pass changelog for position analysis
        )

    # Add sprint progress indicator
    sprint_progress_info = None
    if sprint_start and sprint_end:
        elapsed_time = (now - sprint_start).total_seconds()
        time_progress_pct = min(100, (elapsed_time / sprint_duration_seconds) * 100)

        # Determine time text based on sprint state
        if sprint_state == "CLOSED":
            # For closed sprints, show duration
            sprint_duration_days = (sprint_end - sprint_start).total_seconds() / 86400
            time_text = f"(Lasted {sprint_duration_days:.1f} days)"
        elif sprint_state == "FUTURE":
            # For future sprints, show not started
            time_text = "(Not started yet)"
        else:
            # For active sprints (or unknown state), show days remaining
            remaining_days = (sprint_end - now).total_seconds() / 86400
            time_text = f"({remaining_days:.1f} days remaining)"

        # Build children list for sprint_progress_info
        sprint_progress_children = [
            html.Div(
                [
                    html.Span(
                        f"Sprint Progress: {time_progress_pct:.0f}%",
                        style={
                            "fontSize": "0.9rem",
                            "fontWeight": "600",
                            "color": "#495057",
                            "marginRight": "15px",
                        },
                    ),
                    html.Span(
                        time_text,
                        style={
                            "fontSize": "0.85rem",
                            "color": "#6c757d",
                        },
                    ),
                ],
                style={"marginBottom": "8px"},
            ),
            # Today indicator visual guide
            html.Div(
                [
                    html.Div(
                        style={
                            "width": f"{time_progress_pct:.2f}%",
                            "height": "4px",
                            "backgroundColor": "#0d6efd",
                            "borderRadius": "2px",
                            "position": "relative",
                        },
                    ),
                    html.Div(
                        "TODAY",
                        style={
                            "position": "absolute",
                            "left": f"{time_progress_pct:.2f}%",
                            "top": "-2px",
                            "transform": "translateX(-50%)",
                            "fontSize": "0.7rem",
                            "fontWeight": "700",
                            "color": "#0d6efd",
                            "backgroundColor": "#fff",
                            "padding": "2px 6px",
                            "borderRadius": "3px",
                            "border": "1px solid #0d6efd",
                            "whiteSpace": "nowrap",
                        },
                    ),
                ],
                style={
                    "width": "100%",
                    "height": "20px",
                    "backgroundColor": "#e9ecef",
                    "borderRadius": "2px",
                    "position": "relative",
                    "marginBottom": "10px",
                },
            ),
        ]

        # Add scope changes badges if provided
        if scope_changes:
            import dash_bootstrap_components as dbc

            badges = []
            added_count = scope_changes.get("added", 0)
            removed_count = scope_changes.get("removed", 0)
            net_change = scope_changes.get("net_change", 0)

            # Calculate initial issue count (issues present at sprint start)
            total_issues = len(sprint_data.get("issue_states", {}))
            initial_issues = total_issues - net_change

            # Added badge
            if added_count > 0:
                badges.extend(
                    [
                        dbc.Tooltip(
                            f"Issues added to this sprint after it started ({added_count} issues)",
                            target="badge-added-inline",
                            placement="top",
                        ),
                        dbc.Badge(
                            [
                                html.I(className="fas fa-plus me-1"),
                                f"{added_count} Added",
                            ],
                            color="success",
                            className="me-2",
                            id="badge-added-inline",
                        ),
                    ]
                )

            # Removed badge
            if removed_count > 0:
                badges.extend(
                    [
                        dbc.Tooltip(
                            f"Issues removed from this sprint after it started ({removed_count} issues)",
                            target="badge-removed-inline",
                            placement="top",
                        ),
                        dbc.Badge(
                            [
                                html.I(className="fas fa-minus me-1"),
                                f"{removed_count} Removed",
                            ],
                            color="danger",
                            className="me-2",
                            id="badge-removed-inline",
                        ),
                    ]
                )

            # Net change badge
            if net_change != 0:
                net_icon = "fa-arrow-up" if net_change > 0 else "fa-arrow-down"
                net_color = "info" if net_change > 0 else "warning"
                net_sign = "+" if net_change > 0 else ""

                badges.extend(
                    [
                        dbc.Tooltip(
                            f"Net scope change after sprint start: {net_sign}{net_change} issues (Added - Removed). Note: Initial issues present at sprint start are not included in this count.",
                            target="badge-net-change-inline",
                            placement="top",
                        ),
                        dbc.Badge(
                            [
                                html.I(className=f"fas {net_icon} me-1"),
                                f"{net_sign}{net_change} Net Change",
                            ],
                            color=net_color,
                            className="me-2",
                            id="badge-net-change-inline",
                        ),
                    ]
                )

            # Initial issues badge (if any issues were present at sprint start)
            if initial_issues > 0:
                badges.extend(
                    [
                        dbc.Tooltip(
                            f"{initial_issues} issues were already in the sprint when it started. Total issues = {initial_issues} initial + {net_change} net change = {total_issues}",
                            target="badge-initial-inline",
                            placement="top",
                        ),
                        dbc.Badge(
                            [
                                html.I(className="fas fa-circle-dot me-1"),
                                f"{initial_issues} Initial",
                            ],
                            color="secondary",
                            className="me-2",
                            id="badge-initial-inline",
                        ),
                    ]
                )

            # Add badges to sprint_progress_children if any exist
            if badges:
                sprint_progress_children.append(
                    html.Div(
                        [
                            html.Span(
                                "Sprint Scope Changes: ",
                                style={
                                    "fontSize": "0.85rem",
                                    "fontWeight": "600",
                                    "color": "#495057",
                                    "marginRight": "8px",
                                },
                            ),
                            html.Div(badges, className="d-inline"),
                        ],
                        style={"marginTop": "8px"},
                    )
                )

        # Create the sprint_progress_info Div with all children
        sprint_progress_info = html.Div(
            sprint_progress_children,
            style={
                "marginBottom": "15px",
                "padding": "10px",
                "backgroundColor": "#f8f9fa",
                "borderRadius": "4px",
            },
        )

    # Return sprint progress + legend + progress bars (title added by callback)
    content = []
    if sprint_progress_info:
        content.append(sprint_progress_info)
    if legend:
        content.append(legend)
    content.extend(progress_bars)
    return html.Div(
        content,
        className="p-3",
    )


def _create_single_status_bar(
    issue_key: str,
    summary: str,
    status: str,
    points: Optional[float],
    show_points: bool,
    flow_start_statuses: List[str],
    flow_wip_statuses: List[str],
    flow_end_statuses: List[str],
    issue_type: str = "Unknown",
    sprint_start: Optional[datetime] = None,
    sprint_end: Optional[datetime] = None,
    now: Optional[datetime] = None,
    is_added: bool = False,
    is_removed: bool = False,
    is_initial: bool = False,
):
    """Create a single-color progress bar for issues with no history.

    Args:
        issue_key: JIRA issue key
        summary: Issue summary
        status: Current status
        points: Story points
        show_points: Whether to show points
        flow_start_statuses: Start statuses
        flow_wip_statuses: WIP statuses
        flow_end_statuses: End statuses
        issue_type: Issue type (Bug, Task, Story, etc.)
        sprint_start: Sprint start datetime
        sprint_end: Sprint end datetime
        now: Current datetime
        is_added: Whether issue was added to sprint after it started
        is_removed: Whether issue was removed from sprint
        is_initial: Whether issue was present at sprint start
    """
    # Get issue type icon and color
    icon_class, icon_color = _get_issue_type_icon(issue_type)

    # Use dynamic color based on flow configuration
    color = _get_status_color(
        status, flow_start_statuses, flow_wip_statuses, flow_end_statuses
    )

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

    # Calculate elapsed and remaining time as % of sprint duration
    if sprint_start and sprint_end and now:
        sprint_duration_seconds = (sprint_end - sprint_start).total_seconds()
        elapsed_seconds = (now - sprint_start).total_seconds()

        # Clamp elapsed time between 0 and sprint duration
        elapsed_seconds = max(0, min(elapsed_seconds, sprint_duration_seconds))

        elapsed_pct = (elapsed_seconds / sprint_duration_seconds) * 100
        remaining_pct = 100 - elapsed_pct

        # Format duration for tooltip
        elapsed_days = elapsed_seconds / 86400
        if elapsed_days >= 1:
            duration_str = f"{elapsed_days:.1f}d"
        else:
            duration_str = f"{elapsed_seconds / 3600:.1f}h"
    else:
        # Fallback: show full bar if no sprint dates
        elapsed_pct = 100
        remaining_pct = 0
        duration_str = "unknown"

    # Build segments
    segments = []

    # Elapsed time segment (colored)
    if elapsed_pct > 0:
        # Show percentage if segment is large enough (> 4% of sprint)
        percentage_text = f"{elapsed_pct:.0f}%" if elapsed_pct > 4 else ""

        segments.append(
            html.Div(
                percentage_text,
                title=f"{status}: {duration_str} ({elapsed_pct:.0f}% of sprint duration)",
                style={
                    "width": f"{elapsed_pct:.6f}%",
                    "backgroundColor": color,
                    "color": "white",
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

    # Remaining time segment (light gray)
    if remaining_pct > 0:
        segments.append(
            html.Div(
                title=f"Remaining sprint time: {remaining_pct:.0f}%",
                style={
                    "width": f"{remaining_pct:.6f}%",
                    "backgroundColor": "#e9ecef",
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
            # Progress bar with timeline scaling
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


def _create_multi_segment_bar(
    issue_key: str,
    summary: str,
    time_segments: List[Dict],
    total_duration: float,
    time_progress_percentage: float,
    remaining_percentage: float,
    sprint_duration_seconds: float,
    points: Optional[float],
    show_points: bool,
    flow_start_statuses: List[str],
    flow_wip_statuses: List[str],
    flow_end_statuses: List[str],
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
        sprint_duration_seconds: Total sprint duration in seconds
        points: Story points
        show_points: Whether to show points
        flow_start_statuses: Start statuses
        flow_wip_statuses: WIP statuses
        flow_end_statuses: End statuses
        issue_type: Issue type (Bug, Task, Story, etc.)
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

    # Create change badges for added/removed issues
    change_badges = []
    if is_added:
        change_badges.append(
            html.Span(
                [html.I(className="fas fa-plus me-1"), "Added"],
                className="badge bg-success ms-2",
                style={"fontSize": "0.7rem"},
                title="Issue added to sprint after it started",
            )
        )
    if is_removed:
        change_badges.append(
            html.Span(
                [html.I(className="fas fa-minus me-1"), "Removed"],
                className="badge bg-danger ms-2",
                style={"fontSize": "0.7rem"},
                title="Issue removed from sprint",
            )
        )

    # Build segments scaled to elapsed sprint time
    segments = []
    for segment in time_segments:
        status = segment["status"]
        # Calculate percentage of TOTAL ELAPSED TIME (not sprint duration)
        duration_pct_of_elapsed = (segment["duration_seconds"] / total_duration) * 100
        # Scale to sprint timeline: elapsed time fills X% of sprint, this segment is Y% of elapsed
        duration_pct_of_sprint = (
            duration_pct_of_elapsed / 100
        ) * time_progress_percentage
        duration_days = segment["duration_seconds"] / 86400

        if duration_pct_of_sprint < 0.3:  # Skip tiny segments
            continue

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
                title=f"{status}: {duration_str} ({duration_pct_of_sprint:.0f}% of sprint duration)",
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

    # Add remaining sprint time as light gray empty segment
    if remaining_percentage > 0.5:
        segments.append(
            html.Div(
                "",
                title=f"Remaining sprint time: {remaining_percentage:.0f}%",
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


def _create_simple_html_bars(
    issue_states: Dict,
    show_points: bool = False,
    flow_start_statuses: Optional[List[str]] = None,
    flow_wip_statuses: Optional[List[str]] = None,
    flow_end_statuses: Optional[List[str]] = None,
    sprint_start: Optional[datetime] = None,
    sprint_end: Optional[datetime] = None,
    now: Optional[datetime] = None,
):
    """Fallback HTML bars when no changelog available."""
    # Default flow states if not provided
    if flow_start_statuses is None:
        flow_start_statuses = ["To Do", "Backlog", "Open"]
    if flow_wip_statuses is None:
        flow_wip_statuses = ["In Progress", "In Review", "Testing"]
    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed", "Resolved"]

    bars = []
    for issue_key in sorted(issue_states.keys(), reverse=True):
        state = issue_states[issue_key]
        summary = state.get("summary", "")
        points = state.get("points", 0) if show_points else None
        status = state.get("status", "Unknown")
        issue_type = state.get("issue_type", "Unknown")

        bars.append(
            _create_single_status_bar(
                issue_key,
                summary,
                status,
                points,
                show_points,
                flow_start_statuses,
                flow_wip_statuses,
                flow_end_statuses,
                issue_type=issue_type,
                sprint_start=sprint_start,
                sprint_end=sprint_end,
                now=now,
                is_added=False,  # Snapshots don't show scope changes
                is_removed=False,
                is_initial=False,
            )
        )

    # Return just bars (title added by callback)
    # Return just bars (title added by callback)
    return html.Div(
        bars,
        className="p-3",
    )


# Keep timeline chart as Plotly (it works well for this use case)
def create_sprint_timeline_chart(sprint_changes: Dict) -> go.Figure:
    """Create timeline visualization showing sprint composition changes.

    Args:
        sprint_changes: Dict with 'added', 'removed', 'moved_in', 'moved_out' lists

    Returns:
        Plotly Figure (empty placeholder for now)
    """
    # TODO: Implement sprint timeline chart
    return _create_empty_sprint_chart("Sprint timeline chart (coming soon)")


def create_status_distribution_pie(progress_data: Dict) -> go.Figure:
    """Create pie chart showing status distribution.

    Args:
        progress_data: Dict with status counts

    Returns:
        Plotly Figure with pie chart
    """
    from plotly import graph_objects as go

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
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percent: %{percent}<extra></extra>",
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
    progress_data: Dict, show_points: bool, flow_wip_statuses: List[str]
) -> Dict:
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
