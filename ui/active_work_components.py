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


def create_active_work_legend() -> dbc.Alert:
    """Create legend for Active Work badges and status groups.

    Returns:
        Alert containing legend badges and tooltips
    """
    legend_tooltips = [
        dbc.Tooltip(
            "Status unchanged for 5+ days - needs immediate attention",
            target="legend-blocked",
            placement="top",
        ),
        dbc.Tooltip(
            "Status unchanged for 3-5 days - approaching blocked",
            target="legend-aging",
            placement="top",
        ),
        dbc.Tooltip(
            "In WIP status and status changed in last 2 days - actively being worked",
            target="legend-wip",
            placement="top",
        ),
        dbc.Tooltip(
            "Not yet in WIP or completed status - ready to start",
            target="legend-todo",
            placement="top",
        ),
        dbc.Tooltip(
            "In completed status",
            target="legend-done",
            placement="top",
        ),
        dbc.Tooltip(
            "Total number of issues in the epic",
            target="legend-issue-count",
            placement="top",
        ),
        dbc.Tooltip(
            "Story points for the epic or issue",
            target="legend-points",
            placement="top",
        ),
        dbc.Tooltip(
            "Issue key for quick navigation",
            target="legend-issue-key",
            placement="top",
        ),
    ]

    return dbc.Alert(
        legend_tooltips
        + [
            html.Strong("Status Groups:", className="me-3"),
            html.Span("Blocked", className="badge bg-danger me-2", id="legend-blocked"),
            html.Span(
                "Aging",
                className="badge bg-warning text-dark me-2",
                id="legend-aging",
            ),
            html.Span(
                "In Progress",
                className="badge bg-info text-dark me-2",
                id="legend-wip",
            ),
            html.Span(
                "To Do",
                className="badge bg-secondary me-2",
                id="legend-todo",
            ),
            html.Span("Done", className="badge bg-success me-4", id="legend-done"),
            html.Strong("Signals:", className="me-3"),
            html.Span(
                "12",
                className="active-work-count-badge me-2",
                id="legend-issue-count",
            ),
            html.Span(
                "5",
                className="active-work-points-badge me-2",
                id="legend-points",
            ),
            create_issue_key_badge("ABC-123", badge_id="legend-issue-key"),
        ],
        color="light",
        className="mb-3 py-2 active-work-legend",
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

    issue_link = create_jira_issue_link(
        issue_key,
        className="active-work-issue-key",
    )

    points_badge = create_points_badge(points, show_points)

    return html.Div(
        [
            html.I(
                className=icon + " me-1",
                style={**icon_style, "fontSize": "0.75rem"},
            ),
            points_badge,
            issue_link,
            html.Span(summary, className="active-work-summary"),
        ],
        className="active-work-issue-row",
    )
