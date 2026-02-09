"""Active Work Timeline UI helpers.

Provides shared components for badges, legend, and compact issue rows.
"""

from __future__ import annotations

from typing import Dict, Optional

import dash_bootstrap_components as dbc
from dash import html

from ui.jira_link_helper import create_jira_issue_link


def create_issue_key_badge(
    issue_key: str, badge_id: Optional[str] = None
) -> html.A | html.Span:
    """Create a clickable issue key badge.

    Args:
        issue_key: Issue key to link
        badge_id: Optional DOM id for tooltip targeting

    Returns:
        Clickable badge link
    """
    link = create_jira_issue_link(
        issue_key,
        text=issue_key,
        className="active-work-key-badge",
    )

    if badge_id:
        return html.Span(link, id=badge_id, className="d-inline-flex")

    return link


def create_points_badge(points: float, show_points: bool) -> Optional[html.Span]:
    """Create points badge when points should be shown.

    Args:
        points: Issue or epic points
        show_points: Whether points display is enabled

    Returns:
        Badge span or None
    """
    if not show_points or points <= 0:
        return None

    return html.Span(
        f"{points:.0f}",
        className="active-work-points-badge",
    )


def create_issue_count_badge(count: int) -> html.Span:
    """Create badge for issue count.

    Args:
        count: Number of issues

    Returns:
        Badge span
    """
    return html.Span(
        f"{count}",
        className="active-work-count-badge",
    )


def create_status_indicator_badge(
    status_key: str, color: str, badge_id: Optional[str] = None
) -> html.Span:
    """Create badge for epic status indicator.

    Args:
        status_key: Status key for icon selection
        color: Icon color for the badge
        badge_id: Optional DOM id for tooltip targeting

    Returns:
        Badge span
    """
    icon_class = _get_status_icon_class(status_key)
    badge_kwargs = {
        "className": "active-work-status-badge",
        "style": {"color": color},
    }
    if badge_id:
        badge_kwargs["id"] = badge_id

    return html.Span(
        html.I(className=icon_class),
        **badge_kwargs,
    )


def _get_status_icon_class(status_key: str) -> str:
    """Map status key to a font-awesome icon class.

    Args:
        status_key: Status key used by active work logic.

    Returns:
        Font Awesome class string.
    """
    status_map = {
        "blocked": "fas fa-xmark",
        "aging": "fas fa-clock",
        "wip": "fas fa-spinner",
        "done": "fas fa-check",
        "idle": "fas fa-minus",
        "todo": "fas fa-circle",
    }
    return status_map.get(status_key, "fas fa-minus")


def create_active_work_legend(
    summary_text: Optional[str] = None, include_toggle: bool = True
) -> html.Div:
    """Create legend for Active Work badges and status groups.

    Returns:
        Div containing legend badges and tooltips
    """
    legend_tooltips = [
        dbc.Tooltip(
            "Idle issues: status unchanged for 5+ days",
            target="legend-blocked",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "Aging issues: status unchanged for 3-5 days",
            target="legend-aging",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "In progress issues: status changed in last 2 days",
            target="legend-wip",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "To do issues: not yet started",
            target="legend-todo",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "Done issues: completed status",
            target="legend-done",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "Total number of issues in the epic",
            target="legend-issue-count",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "Closed epics in the completed items weeks",
            target="legend-epic-closed-count",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "Story points for the epic or issue",
            target="legend-points",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "Issue key for quick navigation",
            target="legend-issue-key",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "Epic is aging when any child issue is aging (3-5 days unchanged) and none are idle",
            target="legend-epic-aging",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "Epic is in progress when any child issue is in progress (changed in last 2 days) and none are idle or aging",
            target="legend-epic-wip",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "Epic is done when 100% of child issues are completed",
            target="legend-epic-done",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "Epic is idle when any child issue is idle (5+ days unchanged)",
            target="legend-epic-idle",
            placement="top",
            trigger="click",
            autohide=True,
        ),
        dbc.Tooltip(
            "Epic is to do when all issues are not in progress, aging, idle, or done",
            target="legend-epic-todo",
            placement="top",
            trigger="click",
            autohide=True,
        ),
    ]

    status_badges = [
        html.Span("Status Groups:", className="active-work-legend-section"),
        html.Div(
            [
                html.Span(
                    [html.I(className="fas fa-minus me-1"), "Idle"],
                    className="badge bg-danger me-2",
                    id="legend-blocked",
                ),
                html.Span(
                    [html.I(className="fas fa-clock me-1"), "Aging"],
                    className="badge bg-warning text-dark me-2",
                    id="legend-aging",
                ),
                html.Span(
                    [html.I(className="fas fa-spinner me-1"), "In Progress"],
                    className="badge bg-info text-dark me-2",
                    id="legend-wip",
                ),
                html.Span(
                    [html.I(className="fas fa-circle me-1"), "To Do"],
                    className="badge bg-secondary me-2",
                    id="legend-todo",
                ),
                html.Span(
                    [html.I(className="fas fa-check me-1"), "Done"],
                    className="badge bg-success me-2",
                    id="legend-done",
                ),
            ],
            className="d-inline",
        ),
    ]

    signal_badges = [
        html.Span("Signals:", className="active-work-legend-section"),
        html.Div(
            [
                html.Span(
                    [
                        html.I(
                            className=f"{_get_status_icon_class('idle')} me-1",
                            style={"color": "#c65f5f"},
                        ),
                        "Idle",
                    ],
                    className="badge bg-light text-dark me-2 active-work-legend-signal",
                    id="legend-epic-idle",
                ),
                html.Span(
                    [
                        html.I(
                            className=f"{_get_status_icon_class('aging')} me-1",
                            style={"color": "#ffc107"},
                        ),
                        "Aging",
                    ],
                    className="badge bg-light text-dark me-2 active-work-legend-signal",
                    id="legend-epic-aging",
                ),
                html.Span(
                    [
                        html.I(
                            className=f"{_get_status_icon_class('wip')} me-1",
                            style={"color": "#007bff"},
                        ),
                        "In Progress",
                    ],
                    className="badge bg-light text-dark me-2 active-work-legend-signal",
                    id="legend-epic-wip",
                ),
                html.Span(
                    [
                        html.I(
                            className=f"{_get_status_icon_class('todo')} me-1",
                            style={"color": "#6c757d"},
                        ),
                        "To Do",
                    ],
                    className="badge bg-light text-dark me-2 active-work-legend-signal",
                    id="legend-epic-todo",
                ),
                html.Span(
                    [
                        html.I(
                            className=f"{_get_status_icon_class('done')} me-1",
                            style={"color": "#28a745"},
                        ),
                        "Done",
                    ],
                    className="badge bg-light text-dark me-2 active-work-legend-signal",
                    id="legend-epic-done",
                ),
                html.Span(
                    "12",
                    className=(
                        "active-work-count-badge completed-epic-count-badge "
                        "me-2 active-work-legend-muted"
                    ),
                    id="legend-epic-closed-count",
                ),
                html.Span(
                    "12",
                    className="active-work-count-badge me-2 active-work-legend-muted",
                    id="legend-issue-count",
                ),
                html.Span(
                    "25",
                    className="active-work-points-badge me-2 active-work-legend-muted",
                    id="legend-points",
                ),
                html.Span(
                    "ABC-123",
                    className="active-work-key-badge active-work-legend-muted",
                    id="legend-issue-key",
                ),
            ],
            className="d-inline",
        ),
    ]

    header_row = None
    if summary_text:
        header_row = html.Div(
            [
                html.Span(summary_text, className="active-work-legend-summary"),
                html.Button(
                    [
                        html.I(className="fas fa-expand-arrows-alt me-2"),
                        html.Span("Expand all", id="active-work-toggle-label"),
                    ],
                    id="active-work-toggle-all",
                    className=(
                        "btn btn-sm btn-outline-secondary active-work-toggle-btn"
                    ),
                    type="button",
                )
                if include_toggle
                else None,
            ],
            className="active-work-legend-header",
        )

    return html.Div(
        legend_tooltips
        + [
            html.Div(
                [
                    header_row,
                    html.Div(status_badges, className="active-work-legend-row"),
                    html.Div(signal_badges, className="active-work-legend-row"),
                ],
                className="active-work-legend",
            )
        ]
    )


def create_compact_issue_row(issue: Dict, show_points: bool = False) -> html.Div:
    """Create single-line compact issue row.

    Args:
        issue: Issue dict with health_indicators
        show_points: Whether to show story points

    Returns:
        Single-line issue row
    """
    issue_key = issue.get("issue_key", "Unknown")
    summary = issue.get("summary", "No summary")
    issue_type = issue.get("issue_type", "Task")
    points = issue.get("points", 0.0) or 0.0

    issue_type_lower = issue_type.lower()
    if "bug" in issue_type_lower or "defect" in issue_type_lower:
        icon = "fas fa-bug text-danger"
    elif "task" in issue_type_lower or "sub-task" in issue_type_lower:
        icon = "fas fa-check-square text-info"
    elif "story" in issue_type_lower:
        icon = "fas fa-book text-success"
    elif "epic" in issue_type_lower:
        icon = "fas fa-flag"
    else:
        icon = "fas fa-circle text-secondary"

    icon_style = {"color": "#6f42c1"} if "epic" in issue_type_lower else {}

    issue_key_badge = create_issue_key_badge(issue_key)

    points_badge = create_points_badge(points, show_points)

    return html.Div(
        [
            html.I(
                className=icon + " me-1",
                style={**icon_style, "fontSize": "0.75rem"},
            ),
            points_badge,
            issue_key_badge,
            html.Span(summary, className="active-work-summary"),
        ],
        className="active-work-issue-row",
    )
