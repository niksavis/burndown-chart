"""Single-status bar builders for sprint issues with no status history."""

from datetime import datetime

from dash import html

from ui.jira_link_helper import create_jira_issue_link

from ._status import _get_issue_type_icon, _get_status_color


def _create_single_status_bar(
    issue_key: str,
    summary: str,
    status: str,
    points: float | None,
    show_points: bool,
    flow_start_statuses: list[str],
    flow_wip_statuses: list[str],
    flow_end_statuses: list[str],
    issue_type: str = "Unknown",
    sprint_start: datetime | None = None,
    sprint_end: datetime | None = None,
    now: datetime | None = None,
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
                title=(
                    f"{status}: {duration_str} ({elapsed_pct:.0f}% of sprint duration)"
                ),
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


def _create_simple_html_bars(
    issue_states: dict,
    show_points: bool = False,
    flow_start_statuses: list[str] | None = None,
    flow_wip_statuses: list[str] | None = None,
    flow_end_statuses: list[str] | None = None,
    sprint_start: datetime | None = None,
    sprint_end: datetime | None = None,
    now: datetime | None = None,
):
    """Fallback HTML bars when no changelog available."""
    # Default flow states if not provided
    if flow_start_statuses is None:
        flow_start_statuses = ["To Do", "Backlog", "Open"]
    if flow_wip_statuses is None:
        flow_wip_statuses = ["In Progress", "In Review", "Testing"]
    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed", "Resolved"]

    # Sort issues: non-completed first, completed last, then by issue key descending
    def simple_sort_key(issue_key):
        state = issue_states[issue_key]
        status = state.get("status", "Unknown")
        is_completed = 1 if status in flow_end_statuses else 0

        # Extract numeric part from issue key for proper sorting
        try:
            parts = issue_key.split("-")
            if len(parts) > 1:
                numeric_part = int(parts[-1])
                return (is_completed, -numeric_part)  # Negative for descending
        except (ValueError, AttributeError):
            pass
        return (is_completed, issue_key)

    sorted_issue_keys = sorted(issue_states.keys(), key=simple_sort_key)

    bars = []
    for issue_key in sorted_issue_keys:
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
    return html.Div(
        bars,
        className="p-3",
    )
