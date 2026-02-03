"""Active Work Timeline UI Components

This module provides UI components for the Active Work Timeline tab showing:
- Timeline visualization of active epics/features
- Issue lists for last week and this week (2-week window)
- Health indicators on individual issues (blocked, aging, completed)

Focuses on items being actively worked on (WIP + recent completions).

Follows Sprint Tracker pattern for consistent layout and behavior.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import Dict, List, Optional
from ui.jira_link_helper import create_jira_issue_link


def create_active_work_timeline_tab() -> html.Div:
    """Create Active Work Timeline tab container.

    This is an empty placeholder - content is rendered dynamically
    by visualization callback following Sprint Tracker pattern.

    Returns:
        Empty div that will be populated by callback
    """
    return html.Div(id="active-work-timeline-tab-content", children=html.Div())


def create_no_issues_state(parent_field_configured: bool = True) -> html.Div:
    """Create empty state when no active issues found.

    Args:
        parent_field_configured: Whether parent field is configured

    Returns:
        Div with informational message and setup instructions
    """
    if not parent_field_configured:
        # Parent field not configured - show guidance
        return html.Div(
            [
                dbc.Container(
                    [
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-info-circle fa-4x text-info mb-3"
                                ),
                                html.H4(
                                    "Configure Parent/Epic Field",
                                    className="text-info mb-3",
                                ),
                                dbc.Alert(
                                    [
                                        html.I(className="fas fa-lightbulb me-2"),
                                        "To see epic timeline, configure the ",
                                        html.Strong("Parent/Epic Link"),
                                        " field in Settings.",
                                    ],
                                    color="info",
                                    className="mb-4",
                                ),
                                html.P(
                                    "Issues will still be displayed below, but without epic grouping.",
                                    className="text-muted mb-4",
                                ),
                                html.H6("Setup Steps:", className="text-muted mb-2"),
                                html.Ol(
                                    [
                                        html.Li("Go to Settings → Fields tab"),
                                        html.Li("Click General Fields section"),
                                        html.Li(
                                            [
                                                "Set ",
                                                html.Strong("Parent Field"),
                                                " to your epic/parent field name",
                                            ]
                                        ),
                                        html.Li(
                                            "Common values: 'parent', 'Epic Link', 'customfield_10006'"
                                        ),
                                        html.Li("Click Update Data to refresh"),
                                    ],
                                    className="text-muted text-start",
                                    style={"maxWidth": "600px", "margin": "0 auto"},
                                ),
                            ],
                            className="d-flex flex-column align-items-center justify-content-center",
                            style={"minHeight": "400px"},
                        )
                    ],
                    className="container-fluid",
                )
            ],
            className="container-fluid",
        )

    # Parent field configured but no issues found
    return html.Div(
        [
            dbc.Container(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-project-diagram fa-4x text-muted mb-3"
                            ),
                            html.H4(
                                "No Active Work Found", className="text-muted mb-3"
                            ),
                            html.P(
                                [
                                    "Active Work Timeline shows WIP issues and recent completions. ",
                                    "No active work detected in the last 2 weeks.",
                                ],
                                className="text-muted",
                            ),
                        ],
                        className="d-flex flex-column align-items-center justify-content-center",
                        style={"minHeight": "400px"},
                    )
                ],
                className="container-fluid",
            )
        ],
        className="container-fluid",
    )


def create_timeline_visualization(
    timeline: List[Dict], show_points: bool = False
) -> html.Div:
    """Create timeline visualization showing epic progress bars.

    Args:
        timeline: List of epic summaries from get_active_work_data()
        show_points: Whether to show story points

    Returns:
        Div with timeline visualization
    """
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
        epic_summary = epic.get("epic_summary", "Unknown")
        completion_pct = epic.get("completion_pct", 0.0)
        total_issues = epic.get("total_issues", 0)
        completed_issues = epic.get("completed_issues", 0)
        total_points = epic.get("total_points", 0.0)
        completed_points = epic.get("completed_points", 0.0)

        # Progress bar color based on completion
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

        epic_bars.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Strong(epic_summary, className="me-2"),
                            html.Small(f"({epic_key})", className="text-muted"),
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
    title: str, issues: List[Dict], show_points: bool = False
) -> html.Div:
    """Create issue list section with health indicators.

    Args:
        title: Section title ("Last Week" or "This Week")
        issues: List of issues with health_indicators
        show_points: Whether to show story points

    Returns:
        Div with issue list section
    """
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


def create_issue_card(issue: Dict, show_points: bool = False) -> dbc.Card:
    """Create card for single issue with health indicators.

    Health badges:
    - Blocked (red): No update in 5+ days
    - Aging (yellow): 14+ days old
    - Completed (green): In completion status

    Visual connection:
    - Displays parent epic key if available
    - Shows as orphaned if no parent

    Args:
        issue: Issue dict with health_indicators
        show_points: Whether to show story points

    Returns:
        Bootstrap card component
    """
    issue_key = issue.get("issue_key", "Unknown")
    summary = issue.get("summary", "No summary")
    status = issue.get("status", "Unknown")
    issue_type = issue.get("issue_type", "Task")
    points = issue.get("points", 0.0) or 0.0
    assignee = issue.get("assignee")
    health = issue.get("health_indicators", {})
    parent = issue.get("parent")  # Get parent for visual connection

    # Extract parent key
    parent_key = None
    if parent:
        if isinstance(parent, dict):
            parent_key = parent.get("key")
        else:
            parent_key = parent

    # Health badges
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

    # Issue type icon
    type_icons = {
        "Story": "fas fa-book",
        "Task": "fas fa-tasks",
        "Bug": "fas fa-bug",
        "Epic": "fas fa-bolt",
        "Sub-task": "fas fa-list-ul",
    }
    type_icon = type_icons.get(issue_type, "fas fa-circle")

    # Points badge
    points_badge = None
    if show_points and points > 0:
        points_badge = html.Span(
            f"{points:.0f} pts",
            className="badge bg-secondary ms-2",
        )

    # Create clickable issue key link
    issue_key_link = create_jira_issue_link(
        issue_key,
        className="fw-bold text-primary",
    )

    # Create parent epic indicator (visual connection)
    parent_indicator = None
    card_classes = "mb-2"
    card_data_attrs = {}

    if parent_key:
        # Has parent - show connection
        parent_link = create_jira_issue_link(
            parent_key,
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
        card_data_attrs["data-parent-key"] = parent_key  # For visual connection
    else:
        # Orphaned issue - show indicator
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

    return dbc.Card(
        dbc.CardBody(
            [
                # Parent epic indicator at top
                parent_indicator,
                html.Div(
                    [
                        # Left: Type icon + Key (clickable) + Summary
                        html.Div(
                            [
                                html.I(className=f"{type_icon} me-2 text-primary"),
                                issue_key_link,
                                html.Span(summary, className="ms-2"),
                            ],
                            className="flex-grow-1",
                        ),
                        # Right: Health badges + Status
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
                # Assignee row
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
        **card_data_attrs,
    )
