from __future__ import annotations

from dash import html

from ui.active_work_components import (
    create_compact_issue_row,
    create_issue_count_badge,
    create_points_badge,
    create_status_indicator_badge,
)
from ui.jira_link_helper import create_jira_issue_link


def create_completed_items_section(
    completed_by_week: dict[str, dict], show_points: bool = False
) -> html.Div:

    if not completed_by_week:
        return html.Div(
            className="completed-items-section mb-3",
            id="completed-items-section",
        )

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
    issues: list[dict],
    total_issues: int,
    total_epics_closed: int,
    total_epics_linked: int,
    total_points: float,
    is_current: bool,
    epic_groups: list[dict],
    show_points: bool = False,
) -> html.Details:

    assignees = set()
    for issue in issues:
        assignee = issue.get("assignee")
        if assignee:
            assignees.add(assignee)
    assignee_count = len(assignees)

    status_badge = create_status_indicator_badge("done", "#28a745")
    epic_count_badge = html.Span(
        f"{total_epics_closed}",
        className="active-work-count-badge completed-epic-count-badge",
    )
    issue_count_badge = create_issue_count_badge(total_issues)
    points_badge = create_points_badge(total_points, show_points)

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

    epic_label_suffix = "s" if total_epics_linked != 1 else ""

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
                            className=(
                                "d-flex align-items-center mb-2 "
                                "active-work-epic-title-row"
                            ),
                        ),
                        html.Div(
                            [
                                html.Span(
                                    [
                                        html.I(className="fas fa-flag me-1"),
                                        (
                                            f"{total_epics_linked} "
                                            f"Epic{epic_label_suffix}"
                                        ),
                                    ],
                                    className="badge bg-secondary me-2",
                                ),
                                html.Span(
                                    [
                                        html.I(className="fas fa-check me-1"),
                                        (
                                            f"{total_issues} "
                                            f"Issue{'s' if total_issues != 1 else ''}"
                                        ),
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
                            (
                                f"Completed ({total_issues} issues, "
                                f"{total_epics_closed} epics)"
                            ),
                        ],
                        className="text-success mb-2 mt-2",
                        style={"fontSize": "0.9rem"},
                    ),
                    html.Div(issue_rows, className="ms-3"),
                ],
                className="card-body p-3 pt-0",
            ),
        ],
        open=False,
        className=(
            "card mb-3 shadow-sm active-work-epic-card "
            f"week-container week-{'current' if is_current else 'last'}"
        ),
        id=f"week-{week_label}",
    )


def _create_epic_group_section(group: dict, show_points: bool) -> html.Div:

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

    header_children = [
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
        html.Span(
            f"{item_count} item{'s' if item_count != 1 else ''}",
            className="ms-2",
            style={
                "fontSize": "0.8rem",
                "fontStyle": "italic",
                "color": "#17a2b8",
            },
        ),
    ]

    return html.Div(
        [
            html.Div(
                header_children,
                className="completed-epic-header",
            ),
            html.Div(issue_rows, className="ms-4"),
        ],
        className="completed-epic-group",
    )
