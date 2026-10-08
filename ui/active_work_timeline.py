import dash_bootstrap_components as dbc
from dash import html

from ui.jira_link_helper import create_jira_issue_link


def create_active_work_timeline_tab() -> html.Div:

    return html.Div(id="active-work-timeline-tab-content", children=html.Div())


def create_timeline_visualization(
    timeline: list[dict], show_points: bool = False
) -> html.Div:

    if not timeline:
        return html.Div(
            [
                html.H5("Epic Timeline", className="mb-3"),
                html.P("No epics found", className="text-muted"),
            ]
        )

    epic_bars = []
    for epic in timeline:
        epic_key = epic.get("epic_key", "Unknown")
        epic_summary = epic.get("epic_summary", epic_key)
        completion_pct = epic.get("completion_pct", 0.0)
        total_issues = epic.get("total_issues", 0)
        completed_issues = epic.get("completed_issues", 0)
        total_points = epic.get("total_points", 0.0)
        completed_points = epic.get("completed_points", 0.0)

        if completion_pct >= 75:
            bar_color = "success"
        elif completion_pct >= 50:
            bar_color = "info"
        elif completion_pct >= 25:
            bar_color = "warning"
        else:
            bar_color = "danger"

        metrics_text = f"{completed_issues}/{total_issues} issues"
        if show_points and total_points > 0:
            metrics_text += f" • {completed_points:.0f}/{total_points:.0f} pts"

        epic_key_link = create_jira_issue_link(
            epic_key,
            text=epic_key,
            className="fw-bold",
            style={"fontSize": "0.9rem", "color": "#495057"},
        )

        epic_bars.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-flag me-2",
                                title="Epic",
                                style={"color": "#6f42c1", "fontSize": "0.85rem"},
                            ),
                            epic_key_link,
                            html.Span(
                                epic_summary,
                                className="text-muted ms-2",
                                style={"fontSize": "0.85rem"},
                            ),
                        ],
                        className="mb-1",
                    ),
                    dbc.Progress(
                        value=completion_pct,
                        label=f"{completion_pct:.0f}%",
                        color=bar_color,
                        className="mb-1",
                        style={"height": "25px"},
                    ),
                    html.Small(metrics_text, className="text-muted"),
                ],
                className="mb-3",
            )
        )

    return html.Div(
        [
            html.H5(
                [html.I(className="fas fa-chart-line me-2"), "Epic Timeline"],
                className="mb-3",
            ),
            html.Div(epic_bars),
        ],
        className="timeline-section",
    )


def create_issue_list_section(
    title: str, issues: list[dict], show_points: bool = False
) -> html.Div:

    if not issues:
        return html.Div(
            [
                html.H5(title, className="mb-3"),
                html.P(f"No issues for {title.lower()}", className="text-muted"),
            ]
        )

    issue_cards = [create_issue_card(issue, show_points) for issue in issues]

    return html.Div(
        [
            html.H5(
                [
                    html.I(className="fas fa-tasks me-2"),
                    title,
                    html.Span(
                        f" ({len(issues)} issues)",
                        className="text-muted ms-2",
                        style={"fontSize": "0.9rem"},
                    ),
                ],
                className="mb-3",
            ),
            html.Div(issue_cards, className="issue-list"),
        ],
        className="issue-list-section",
    )


def create_issue_card(issue: dict, show_points: bool = False) -> html.Div | dbc.Card:

    issue_key = issue.get("issue_key", "Unknown")
    summary = issue.get("summary", "No summary")
    status = issue.get("status", "Unknown")
    issue_type = issue.get("issue_type", "Task")
    points = issue.get("points", 0.0) or 0.0
    assignee = issue.get("assignee")
    health = issue.get("health_indicators", {})

    parent = issue.get("parent")
    if not parent:
        custom_fields = issue.get("custom_fields", {})
        parent = custom_fields.get("customfield_10006")

    parent_key = None
    parent_summary = None
    if parent:
        if isinstance(parent, dict):
            parent_key = parent.get("key")
            parent_summary = parent.get("summary", parent_key)
        elif isinstance(parent, str):
            parent_key = parent
            parent_summary = parent

    badges = []
    if health.get("is_completed"):
        badges.append(
            html.Span(
                [html.I(className="fas fa-check-circle me-1"), "Completed"],
                className="badge bg-success me-2",
            )
        )
    if health.get("is_blocked"):
        badges.append(
            html.Span(
                [html.I(className="fas fa-exclamation-triangle me-1"), "Blocked"],
                className="badge bg-danger me-2",
            )
        )
    if health.get("is_aging"):
        badges.append(
            html.Span(
                [html.I(className="fas fa-clock me-1"), "Aging"],
                className="badge bg-warning me-2",
            )
        )

    issue_type_lower = issue_type.lower()
    if "bug" in issue_type_lower or "defect" in issue_type_lower:
        type_icon = "fas fa-bug text-danger"
    elif "task" in issue_type_lower or "sub-task" in issue_type_lower:
        type_icon = "fas fa-tasks text-primary"
    elif "story" in issue_type_lower or "user story" in issue_type_lower:
        type_icon = "fas fa-book text-success"
    elif "epic" in issue_type_lower:
        type_icon = "fas fa-flag"
    else:
        type_icon = "fas fa-circle text-secondary"

    points_badge = None
    if show_points and points > 0:
        points_badge = html.Span(
            f"{points:.0f} pts",
            className="badge bg-secondary ms-2",
        )

    issue_key_link = create_jira_issue_link(
        issue_key,
        className="fw-bold text-primary",
    )

    parent_indicator = None
    card_classes = "mb-2"
    card_data_attrs = {}

    if parent_key:
        link_text = parent_summary if parent_summary else parent_key
        parent_link = create_jira_issue_link(
            parent_key,
            text=link_text,
            className="badge bg-light text-dark border",
            style={"fontSize": "0.7rem"},
        )
        parent_indicator = html.Div(
            [
                html.I(
                    className="fas fa-level-up-alt me-1", style={"fontSize": "0.7rem"}
                ),
                parent_link,
            ],
            className="mb-2",
        )
        card_data_attrs["data-parent-key"] = parent_key
    else:
        parent_indicator = html.Div(
            [
                html.Span(
                    [html.I(className="fas fa-unlink me-1"), "No Epic"],
                    className="badge bg-light text-muted border",
                    style={"fontSize": "0.7rem"},
                    title="This issue is not linked to any epic/parent",
                ),
            ],
            className="mb-2",
        )
        card_classes += " orphaned-issue"

    card = dbc.Card(
        dbc.CardBody(
            [
                parent_indicator,
                html.Div(
                    [
                        html.Div(
                            [
                                html.I(
                                    className=f"{type_icon} me-2",
                                    style={"color": "#6f42c1"}
                                    if "epic" in issue_type.lower()
                                    else {},
                                ),
                                issue_key_link,
                                html.Span(summary, className="ms-2"),
                            ],
                            className="flex-grow-1",
                        ),
                        html.Div(
                            [
                                html.Div(badges, className="d-flex align-items-center"),
                                html.Span(
                                    status,
                                    className="badge bg-info ms-2",
                                ),
                                points_badge,
                            ],
                            className="d-flex align-items-center",
                        ),
                    ],
                    className="d-flex align-items-center justify-content-between",
                ),
                html.Div(
                    [
                        html.Small(
                            [
                                html.I(className="fas fa-user me-1"),
                                assignee or "Unassigned",
                            ],
                            className="text-muted",
                        ),
                    ],
                    className="mt-2",
                )
                if assignee
                else None,
            ]
        ),
        className=card_classes,
    )

    if card_data_attrs:
        return html.Div(card, **card_data_attrs)
    else:
        return card
