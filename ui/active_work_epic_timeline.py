"""Active Work epic timeline UI components."""

from __future__ import annotations

from typing import Dict, List

import dash_bootstrap_components as dbc
from dash import html

from ui.active_work_components import (
    create_active_work_legend,
    create_compact_issue_row,
    create_issue_count_badge,
    create_issue_key_badge,
    create_points_badge,
    create_status_indicator_badge,
)


def create_nested_epic_timeline(
    timeline: List[Dict],
    show_points: bool = False,
    parent_field_configured: bool = True,
) -> html.Div:
    """Create nested epic timeline with compact issue lists under each epic.

    Args:
        timeline: List of epic dicts with child_issues
        show_points: Whether to show story points
        parent_field_configured: Whether parent field is configured

    Returns:
        Nested timeline div
    """
    if not timeline:
        return html.Div(
            [
                html.H5("Epic Timeline", className="mb-3"),
                html.P("No epics found", className="text-muted"),
            ]
        )

    legend = create_active_work_legend()

    epic_sections: List = [legend]

    for epic in timeline:
        epic_key = epic.get("epic_key", "Unknown")
        epic_summary = epic.get("epic_summary", epic_key)

        if epic_key == "No Parent":
            epic_summary = "Other"

        total_points = epic.get("total_points", 0.0)
        child_issues = epic.get("child_issues", [])

        visible_completed = sum(
            1
            for issue in child_issues
            if issue.get("health_indicators", {}).get("is_completed")
        )
        visible_total = len(child_issues)
        completion_pct = (
            (visible_completed / visible_total * 100) if visible_total > 0 else 0
        )

        blocked_issues = [
            i for i in child_issues if i.get("health_indicators", {}).get("is_blocked")
        ]
        aging_issues = [
            i
            for i in child_issues
            if not i.get("health_indicators", {}).get("is_blocked")
            and not i.get("health_indicators", {}).get("is_completed")
            and i.get("health_indicators", {}).get("is_aging")
        ]
        wip_issues = [
            i
            for i in child_issues
            if not i.get("health_indicators", {}).get("is_blocked")
            and not i.get("health_indicators", {}).get("is_completed")
            and not i.get("health_indicators", {}).get("is_aging")
            and i.get("health_indicators", {}).get("is_wip")
        ]
        todo_issues = [
            i
            for i in child_issues
            if not i.get("health_indicators", {}).get("is_blocked")
            and not i.get("health_indicators", {}).get("is_completed")
            and not i.get("health_indicators", {}).get("is_aging")
            and not i.get("health_indicators", {}).get("is_wip")
        ]
        done_issues = [
            i
            for i in child_issues
            if i.get("health_indicators", {}).get("is_completed")
        ]

        default_open = False

        if epic_key == "No Parent":
            status_key = "idle"
            status_color = "#c65f5f"
        elif completion_pct == 100:
            status_key = "done"
            status_color = "#28a745"
        elif blocked_issues:
            status_key = "idle"
            status_color = "#c65f5f"
        elif aging_issues:
            status_key = "aging"
            status_color = "#ffc107"
        elif wip_issues:
            status_key = "wip"
            status_color = "#007bff"
        else:
            status_key = "idle"
            status_color = "#c65f5f"

        epic_key_badge = (
            create_issue_key_badge(epic_key) if epic_key != "No Parent" else None
        )
        count_badge = create_issue_count_badge(visible_total)
        points_badge = create_points_badge(total_points, show_points)
        status_badge = create_status_indicator_badge(status_key, status_color)

        issue_sections = []
        if blocked_issues:
            issue_sections.append(
                _create_status_section("Idle", blocked_issues, show_points, "danger")
            )
        if aging_issues:
            issue_sections.append(
                _create_status_section("Aging", aging_issues, show_points, "warning")
            )
        if wip_issues:
            issue_sections.append(
                _create_status_section("In Progress", wip_issues, show_points, "info")
            )
        if todo_issues:
            issue_sections.append(
                _create_status_section("To Do", todo_issues, show_points, "secondary")
            )
        if done_issues:
            issue_sections.append(
                _create_status_section("Done", done_issues, show_points, "success")
            )

        epic_sections.append(
            html.Details(
                [
                    html.Summary(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        status_badge,
                                        count_badge,
                                        points_badge,
                                        epic_key_badge,
                                        html.Span(
                                            epic_summary,
                                            className="active-work-epic-summary",
                                        ),
                                        html.Span(
                                            "▾",
                                            className="active-work-epic-arrow",
                                        ),
                                    ],
                                    className="d-flex align-items-center mb-2 active-work-epic-title-row",
                                ),
                                dbc.Progress(
                                    value=completion_pct,
                                    label=f"{completion_pct:.0f}%",
                                    color="success"
                                    if completion_pct == 100
                                    else "primary",
                                    style={"height": "20px", "fontSize": "0.85rem"},
                                    className="mb-2",
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            f"{len(blocked_issues)} Idle",
                                            className="badge bg-danger me-2",
                                        )
                                        if blocked_issues
                                        else None,
                                        html.Span(
                                            f"{len(aging_issues)} Aging",
                                            className="badge bg-warning text-dark me-2",
                                        )
                                        if aging_issues
                                        else None,
                                        html.Span(
                                            f"{len(wip_issues)} In Progress",
                                            className="badge bg-info text-dark me-2",
                                        )
                                        if wip_issues
                                        else None,
                                        html.Span(
                                            f"{len(todo_issues)} To Do",
                                            className="badge bg-secondary me-2",
                                        )
                                        if todo_issues
                                        else None,
                                        html.Span(
                                            f"{len(done_issues)} Done",
                                            className="badge bg-success",
                                        )
                                        if done_issues
                                        else None,
                                    ],
                                    className="d-flex",
                                ),
                            ],
                            className="card-header p-3",
                        ),
                        className="active-work-epic-toggle",
                    ),
                    html.Div(
                        issue_sections
                        if issue_sections
                        else html.P("No issues", className="text-muted"),
                        className="card-body p-3 pt-0",
                    ),
                ],
                open=default_open,
                className="card mb-3 shadow-sm active-work-epic-card",
            )
        )

    return html.Div(epic_sections)


def _create_status_section(
    title: str, issues: List[Dict], show_points: bool, color: str
) -> html.Div:
    """Create a section for a group of issues by status.

    Args:
        title: Section title
        issues: List of issues in this status
        show_points: Whether to show story points
        color: Bootstrap color for section

    Returns:
        Section div with issues
    """
    if not issues:
        return html.Div()

    issue_rows = [create_compact_issue_row(issue, show_points) for issue in issues]

    return html.Div(
        [
            html.H6(
                title, className=f"text-{color} mb-2 mt-2", style={"fontSize": "0.9rem"}
            ),
            html.Div(issue_rows, className="ms-3"),
        ],
        className="mb-3",
    )
