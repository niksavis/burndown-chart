from dash import html

from configuration import COLOR_PALETTE

STATUS_COLORS = {
    "To Do": "#6c757d",
    "Backlog": "#6c757d",
    "Open": "#6c757d",
    "Analysis": "#0dcaf0",
    "In Progress": "#0d6efd",
    "In Review": "#9b59b6",
    "Code Review": "#9b59b6",
    "Ready for Testing": "#f39c12",
    "Testing": "#e67e22",
    "In Deployment": "#d63384",
    "Done": "#28a745",
    "Closed": "#28a745",
    "Resolved": "#28a745",
}


def _get_issue_type_icon(issue_type: str) -> tuple:

    issue_type_lower = issue_type.lower()

    if "bug" in issue_type_lower or "defect" in issue_type_lower:
        return ("fa-bug", "#dc3545")
    elif "task" in issue_type_lower or "sub-task" in issue_type_lower:
        return ("fa-tasks", "#0d6efd")
    elif "story" in issue_type_lower or "user story" in issue_type_lower:
        return ("fa-book", "#198754")
    elif "epic" in issue_type_lower:
        return ("fa-flag", "#6f42c1")
    else:
        return ("fa-circle", "#6c757d")


def _get_status_color(
    status: str,
    flow_start_statuses: list[str],
    flow_wip_statuses: list[str],
    flow_end_statuses: list[str],
) -> str:

    if status in flow_end_statuses:
        return COLOR_PALETTE["success"]
    elif status in flow_wip_statuses:
        wip_colors = [
            "#0d6efd",
            "#9b59b6",
            "#f39c12",
            "#e67e22",
            "#0dcaf0",
            "#d63384",
        ]
        wip_index = flow_wip_statuses.index(status) % len(wip_colors)
        return wip_colors[wip_index]
    elif status in flow_start_statuses:
        return "#6c757d"

    if status in STATUS_COLORS:
        return STATUS_COLORS[status]

    return COLOR_PALETTE["secondary"]


def _create_status_legend(
    time_segments: list[dict],
    flow_start_statuses: list[str],
    flow_wip_statuses: list[str],
    flow_end_statuses: list[str],
    changelog_entries: list[dict] | None = None,
) -> html.Div:

    unique_statuses = set([seg["status"] for seg in time_segments])

    statuses = []
    seen = set()

    start_statuses = flow_start_statuses or []
    wip_statuses = flow_wip_statuses or []
    end_statuses = flow_end_statuses or []

    common_start = ["To Do", "Backlog", "Open", "New", "Selected for Development"]
    for status in common_start:
        if status in unique_statuses and status not in seen:
            statuses.append(status)
            seen.add(status)

    for status in start_statuses:
        if status in unique_statuses and status not in seen:
            statuses.append(status)
            seen.add(status)

    for status in wip_statuses:
        if status in unique_statuses and status not in seen:
            statuses.append(status)
            seen.add(status)

    for status in end_statuses:
        if status in unique_statuses and status not in seen:
            statuses.append(status)
            seen.add(status)

    common_end = ["Done", "Closed", "Resolved", "Cancelled", "Rejected"]
    remaining = sorted(
        [s for s in unique_statuses if s not in seen and s not in common_end]
    )
    statuses.extend(remaining)
    seen.update(remaining)

    for status in common_end:
        if status in unique_statuses and status not in seen:
            statuses.append(status)
            seen.add(status)

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
