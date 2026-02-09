"""Active Work Completed Items UI components.

Provides UI components for displaying recently completed items grouped by week.
Extracted from active_work_components to maintain file size limits.
"""

from __future__ import annotations

from typing import Dict, List

from dash import html

from ui.active_work_components import (
    create_issue_count_badge,
    create_points_badge,
    create_compact_issue_row,
    create_status_indicator_badge,
)
from ui.jira_link_helper import create_jira_issue_link


def create_completed_items_section(
    completed_by_week: Dict[str, Dict], show_points: bool = False
) -> html.Div:
    """Create completed items section with week containers.

    Shows recently completed items grouped by ISO weeks (current week first).
    Each week is a collapsible container matching epic container styling.

    Args:
        completed_by_week: OrderedDict from get_completed_items_by_week()
        show_points: Whether to show story points

    Returns:
        Section div with week containers
    """
    if not completed_by_week:
        return html.Div()

    week_containers = []

    for week_label, week_data in completed_by_week.items():
        container = create_week_container(
            week_label=week_label,
            display_label=week_data["display_label"],
            issues=week_data["issues"],
            total_issues=week_data["total_issues"],
            total_epics_closed=week_data.get("total_epics_closed", 0),
            total_epics_linked=week_data.get("total_epics_linked", 0),
            total_points=week_data["total_points"],
            is_current=week_data["is_current"],
            epic_groups=week_data.get("epic_groups", []),
            show_points=show_points,
        )
        week_containers.append(container)

    return html.Div(
        week_containers,
        className="completed-items-section mb-3",
        id="completed-items-section",
    )


def create_week_container(
    week_label: str,
    display_label: str,
    issues: List[Dict],
    total_issues: int,
    total_epics_closed: int,
    total_epics_linked: int,
    total_points: float,
    is_current: bool,
    epic_groups: List[Dict],
    show_points: bool = False,
) -> html.Details:
    """Create collapsible week container for completed items.

    Follows epic container pattern with status indicators, counts, and
    collapsible issue list.

    Args:
        week_label: ISO week label (e.g., "2026-W06")
        display_label: Formatted display label (e.g., "Current Week (Feb 3-9)")
        issues: List of completed issues in this week
        total_issues: Total issue count
        total_epics_closed: Total completed epic count
        total_epics_linked: Total linked epic count
        total_points: Total story points
        is_current: Whether this is the current week
        epic_groups: Grouped issues by epic
        show_points: Whether to show story points

    Returns:
        Details element with collapsible week content
    """
    # Calculate assignee count
    assignees = set()
    for issue in issues:
        assignee = issue.get("assignee")
        if assignee:
            assignees.add(assignee)
    assignee_count = len(assignees)

    # Badges
    status_badge = create_status_indicator_badge("done", "#28a745")
    epic_count_badge = html.Span(
        f"{total_epics_closed}",
        className="active-work-count-badge completed-epic-count-badge",
    )
    issue_count_badge = create_issue_count_badge(total_issues)
    points_badge = create_points_badge(total_points, show_points)

    # Create issue rows
    issue_rows = []
    if issues:
        if epic_groups:
            issue_rows = [
                _create_epic_group_section(group, show_points) for group in epic_groups
            ]
        else:
            issue_rows = [
                create_compact_issue_row(issue, show_points) for issue in issues
            ]
    else:
        issue_rows = [html.P("No items completed this week", className="text-muted")]

    # Week container (collapsible, closed by default)
    return html.Details(
        [
            html.Summary(
                html.Div(
                    [
                        html.Div(
                            [
                                status_badge,
                                epic_count_badge,
                                issue_count_badge,
                                points_badge,
                                html.Span(
                                    display_label,
                                    className="active-work-epic-summary",
                                ),
                                # Assignee count badge (if more than 1 person)
                                html.Span(
                                    [
                                        html.I(className="fas fa-users me-1"),
                                        str(assignee_count),
                                    ],
                                    className="badge bg-info text-dark me-2",
                                    style={"fontSize": "0.75rem"},
                                )
                                if assignee_count > 0
                                else None,
                                html.Span(
                                    "▾",
                                    className="active-work-epic-arrow",
                                ),
                            ],
                            className="d-flex align-items-center mb-2 active-work-epic-title-row",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    [
                                        html.I(className="fas fa-flag me-1"),
                                        f"{total_epics_linked} Epic{'s' if total_epics_linked != 1 else ''}",
                                    ],
                                    className="badge bg-secondary me-2",
                                ),
                                html.Span(
                                    [
                                        html.I(className="fas fa-check me-1"),
                                        f"{total_issues} Issue{'s' if total_issues != 1 else ''}",
                                    ],
                                    className="badge bg-success",
                                ),
                            ],
                            className="d-flex",
                        ),
                    ],
                    className="card-header p-3",
                ),
                className="active-work-epic-toggle week-toggle",
            ),
            html.Div(
                [
                    html.H6(
                        [
                            html.I(className="fas fa-check me-1"),
                            f"Completed ({total_issues} issues, {total_epics_closed} epics)",
                        ],
                        className="text-success mb-2 mt-2",
                        style={"fontSize": "0.9rem"},
                    ),
                    html.Div(issue_rows, className="ms-3"),
                ],
                className="card-body p-3 pt-0",
            ),
        ],
        open=False,  # Collapsed by default
        className=f"card mb-3 shadow-sm active-work-epic-card week-container week-{'current' if is_current else 'last'}",
        id=f"week-{week_label}",
    )


def _create_epic_group_section(group: Dict, show_points: bool) -> html.Div:
    """Create a mini epic header with child issues.

    Args:
        group: Epic group dict with epic_key, epic_summary, issues
        show_points: Whether to show story points

    Returns:
        Div containing epic header and its issues
    """
    epic_key = group.get("epic_key")
    epic_summary = group.get("epic_summary", "Other")
    issues = group.get("issues", [])
    item_count = len(issues)

    epic_key_badge = None
    if epic_key and epic_key != "No Parent":
        epic_key_badge = create_jira_issue_link(
            epic_key,
            text=epic_key,
            className="active-work-key-badge",
        )

    issue_rows = [create_compact_issue_row(issue, show_points) for issue in issues]

    return html.Div(
        [
            html.Div(
                [
                    # Purple epic flag icon
                    html.I(
                        className="fas fa-flag me-2",
                        style={"color": "#6f42c1", "fontSize": "0.85rem"},
                    ),
                    epic_key_badge
                    if epic_key_badge
                    else html.Span(
                        epic_key or "No Parent",
                        className="active-work-key-badge",
                    ),
                    html.Span(
                        epic_summary,
                        className="completed-epic-summary",
                    ),
                    # Item count
                    html.Span(
                        f"{item_count} item{'s' if item_count != 1 else ''}",
                        className="ms-2",
                        style={
                            "fontSize": "0.8rem",
                            "fontStyle": "italic",
                            "color": "#17a2b8",
                        },
                    ),
                ],
                className="completed-epic-header",
            ),
            html.Div(issue_rows, className="ms-3"),
        ],
        className="completed-epic-group",
    )
