"""Status color mapping and legend utilities for sprint progress bars."""

from dash import html

from configuration import COLOR_PALETTE

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
    flow_start_statuses: list[str],
    flow_wip_statuses: list[str],
    flow_end_statuses: list[str],
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
    # Flow config takes priority to match calculate_sprint_progress categorization
    if status in flow_end_statuses:
        return COLOR_PALETTE["success"]  # Green for done states
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
    elif status in flow_start_statuses:
        return "#6c757d"  # Gray for start states

    # Fall back to STATUS_COLORS for statuses not in any configured flow list
    if status in STATUS_COLORS:
        return STATUS_COLORS[status]

    # Final fallback
    return COLOR_PALETTE["secondary"]


def _create_status_legend(
    time_segments: list[dict],
    flow_start_statuses: list[str],
    flow_wip_statuses: list[str],
    flow_end_statuses: list[str],
    changelog_entries: list[dict] | None = None,
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
    # Start -> WIP -> End, with remaining alphabetically
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
