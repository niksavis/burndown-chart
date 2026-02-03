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


def create_nested_epic_timeline(
    timeline: List[Dict], show_points: bool = False, parent_field_configured: bool = True
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
    
    # Legend explaining status groups with colored badges
    legend = dbc.Alert(
        [
            html.Strong("Status Groups: ", className="me-3"),
            html.Span("Blocked", className="badge bg-danger me-2", title="Status unchanged for 5+ days"),
            html.Span("Aging", className="badge bg-warning text-dark me-2", title="Status unchanged for 3-5 days"),
            html.Span("In Progress", className="badge bg-info text-dark me-2", title="In WIP status, changed in last 2 days"),
            html.Span("To Do", className="badge bg-secondary me-2", title="Not yet in WIP or completed status"),
            html.Span("Done", className="badge bg-success", title="In completed status"),
        ],
        color="light",
        className="mb-3 py-2",
    )
    
    epic_sections: List = [legend]  # Type hint to avoid type checker confusion
    
    for epic_idx, epic in enumerate(timeline):
        epic_key = epic.get("epic_key", "Unknown")
        epic_summary = epic.get("epic_summary", epic_key)
        total_issues = epic.get("total_issues", 0)
        completed_issues = epic.get("completed_issues", 0)
        total_points = epic.get("total_points", 0.0)
        completed_points = epic.get("completed_points", 0.0)
        child_issues = epic.get("child_issues", [])
        
        # Calculate completion based on VISIBLE issues (honest representation)
        visible_completed = sum(1 for issue in child_issues if issue.get("health_indicators", {}).get("is_completed"))
        visible_total = len(child_issues)
        completion_pct = (visible_completed / visible_total * 100) if visible_total > 0 else 0
        
        # Group issues by status category (blocked, aging, wip, todo, done)
        blocked_issues = [i for i in child_issues if i.get("health_indicators", {}).get("is_blocked")]
        aging_issues = [i for i in child_issues if not i.get("health_indicators", {}).get("is_blocked")
                        and not i.get("health_indicators", {}).get("is_completed")
                        and i.get("health_indicators", {}).get("is_aging")]
        wip_issues = [i for i in child_issues if not i.get("health_indicators", {}).get("is_blocked") 
                      and not i.get("health_indicators", {}).get("is_completed")
                      and not i.get("health_indicators", {}).get("is_aging")
                      and i.get("health_indicators", {}).get("is_wip")]
        todo_issues = [i for i in child_issues if not i.get("health_indicators", {}).get("is_blocked")
                       and not i.get("health_indicators", {}).get("is_completed")
                       and not i.get("health_indicators", {}).get("is_aging")
                       and not i.get("health_indicators", {}).get("is_wip")]
        done_issues = [i for i in child_issues if i.get("health_indicators", {}).get("is_completed")]
        
        # Epic status indicator
        if completion_pct == 100:
            status_icon = "✓"
            status_color = "#28a745"
            default_open = False
        elif len(blocked_issues) > 0:
            status_icon = "⚠"
            status_color = "#dc3545"
            default_open = True
        elif len(aging_issues) > 0:
            status_icon = "◐"
            status_color = "#ffc107"
            default_open = True
        elif len(wip_issues) > 0:
            status_icon = "◐"
            status_color = "#007bff"
            default_open = True
        else:
            status_icon = "○"
            status_color = "#6c757d"
            default_open = True
        
        # Create JIRA link for epic key (badge style)
        epic_key_link = create_jira_issue_link(
            epic_key,
            text=epic_key,
            className="badge bg-light text-dark text-decoration-none",
            style={"fontSize": "0.75rem"}
        )
        
        # Create status-grouped issue sections (blocked → aging → wip → todo → done)
        issue_sections = []
        if blocked_issues:
            issue_sections.append(_create_status_section("Blocked", blocked_issues, show_points, "danger"))
        if aging_issues:
            issue_sections.append(_create_status_section("Aging", aging_issues, show_points, "warning"))
        if wip_issues:
            issue_sections.append(_create_status_section("In Progress", wip_issues, show_points, "info"))
        if todo_issues:
            issue_sections.append(_create_status_section("To Do", todo_issues, show_points, "secondary"))
        if done_issues:
            issue_sections.append(_create_status_section("Done", done_issues, show_points, "success"))
        
        epic_sections.append(
            dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            html.Div(
                                [
                                    html.Span(
                                        status_icon,
                                        className="me-2",
                                        style={"fontSize": "1.2rem", "color": status_color}
                                    ),
                                    epic_key_link,
                                    html.Span(
                                        epic_summary,
                                        className="fw-bold text-dark ms-2",
                                        style={"fontSize": "1rem"}
                                    ),
                                    html.Small(
                                        f" ({visible_total} issues" + (f", {total_points:.0f}pts" if show_points and total_points > 0 else "") + ")",
                                        className="text-muted ms-2",
                                    ),
                                ],
                                className="d-flex align-items-center mb-2",
                            ),
                            # Progress bar for visible issues (taller for readability)
                            dbc.Progress(
                                value=completion_pct,
                                label=f"{completion_pct:.0f}%",
                                color="success" if completion_pct == 100 else "primary",
                                style={"height": "20px", "fontSize": "0.85rem"},
                                className="mb-2",
                            ),
                            # Summary metrics (show counts for each status as badges)
                            html.Div(
                                [
                                    html.Span(
                                        f"{len(blocked_issues)} Blocked",
                                        className="badge bg-danger me-2"
                                    ) if blocked_issues else None,
                                    html.Span(
                                        f"{len(aging_issues)} Aging",
                                        className="badge bg-warning text-dark me-2"
                                    ) if aging_issues else None,
                                    html.Span(
                                        f"{len(wip_issues)} WIP",
                                        className="badge bg-info text-dark me-2"
                                    ) if wip_issues else None,
                                    html.Span(
                                        f"{len(todo_issues)} To Do",
                                        className="badge bg-secondary me-2"
                                    ) if todo_issues else None,
                                    html.Span(
                                        f"{len(done_issues)} Done",
                                        className="badge bg-success"
                                    ) if done_issues else None,
                                ],
                                className="d-flex",
                            ),
                        ],
                        className="p-3",
                    ),
                    dbc.CardBody(
                        issue_sections if issue_sections else html.P("No issues", className="text-muted"),
                        className="p-3 pt-0",
                    ),
                ],
                className="mb-3 shadow-sm",
            )
        )
    
    return html.Div(epic_sections)


def _is_wip_status(status: str) -> bool:
    """Check if status is work-in-progress."""
    status_lower = status.lower()
    wip_keywords = ["progress", "review", "testing", "development", "deployment", "deploying"]
    return any(kw in status_lower for kw in wip_keywords)


def _create_status_section(title: str, issues: List[Dict], show_points: bool, color: str) -> html.Div:
    """Create a section for a group of issues by status.
    
    Args:
        title: Section title (e.g., "● Blocked")
        issues: List of issues in this status
        show_points: Whether to show story points
        color: Bootstrap color for section
        
    Returns:
        Section div with issues
    """
    if not issues:
        return html.Div()
    
    issue_rows = [_create_compact_issue_row(issue, show_points) for issue in issues]
    
    return html.Div(
        [
            html.H6(title, className=f"text-{color} mb-2 mt-2", style={"fontSize": "0.9rem"}),
            html.Div(issue_rows, className="ms-3"),
        ],
        className="mb-3",
    )


def _create_compact_issue_row(issue: Dict, show_points: bool = False) -> html.Div:
    """Create single-line compact issue row.
    
    Args:
        issue: Issue dict with health_indicators
        show_points: Whether to show story points
        
    Returns:
        Single-line issue row
    """
    issue_key = issue.get("issue_key", "Unknown")
    summary = issue.get("summary", "No summary")
    status = issue.get("status", "Unknown")
    issue_type = issue.get("issue_type", "Task")
    points = issue.get("points", 0.0) or 0.0
    health = issue.get("health_indicators", {})
    
    # Truncate summary
    max_len = 80
    display_summary = summary[:max_len] + "..." if len(summary) > max_len else summary
    
    # Issue type icon (Sprint Tracker pattern)
    issue_type_lower = issue_type.lower()
    if "bug" in issue_type_lower or "defect" in issue_type_lower:
        icon = "fas fa-bug text-danger"
    elif "task" in issue_type_lower or "sub-task" in issue_type_lower:
        icon = "fas fa-check-square text-info"  # Changed to check-square with info color
    elif "story" in issue_type_lower:
        icon = "fas fa-book text-success"
    elif "epic" in issue_type_lower:
        icon = "fas fa-flag"
        icon_style = {"color": "#6f42c1"}
    else:
        icon = "fas fa-circle text-secondary"
    
    icon_style = {"color": "#6f42c1"} if "epic" in issue_type_lower else {}
    
    # Issue key link
    issue_link = create_jira_issue_link(
        issue_key,
        className="fw-bold",
        style={"fontSize": "0.85rem"}
    )
    
    return html.Div(
        [
            html.I(className=icon + " me-1", style={**icon_style, "fontSize": "0.75rem"}),
            issue_link,
            html.Span(display_summary, className="text-muted ms-2", style={"fontSize": "0.85rem"}),
            html.Span(
                f" ({points:.0f}pts)" if show_points and points > 0 else "",
                className="text-muted ms-1",
                style={"fontSize": "0.75rem"}
            ),
        ],
        className="mb-1",
        style={"fontSize": "0.85rem"}
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
        epic_summary = epic.get("epic_summary", epic_key)  # Fallback to key if no summary
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

        # Create clickable JIRA link for epic key (matches Sprint Tracker format)
        epic_key_link = create_jira_issue_link(
            epic_key, 
            text=epic_key,
            className="fw-bold",
            style={"fontSize": "0.9rem", "color": "#495057"}
        )

        epic_bars.append(
            html.Div(
                [
                    html.Div(
                        [
                            # Epic icon (purple flag like Sprint Tracker)
                            html.I(
                                className="fas fa-flag me-2",
                                title="Epic",
                                style={"color": "#6f42c1", "fontSize": "0.85rem"}
                            ),
                            # Clickable epic key
                            epic_key_link,
                            # Epic summary
                            html.Span(
                                epic_summary,
                                className="text-muted ms-2",
                                style={"fontSize": "0.85rem"}
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


def create_issue_card(issue: Dict, show_points: bool = False) -> html.Div | dbc.Card:
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
    
    # Try to get parent from top level or custom_fields
    parent = issue.get("parent")
    if not parent:
        custom_fields = issue.get("custom_fields", {})
        parent = custom_fields.get("customfield_10006")  # Common epic link field

    # Extract parent key and summary
    parent_key = None
    parent_summary = None
    if parent:
        if isinstance(parent, dict):
            parent_key = parent.get("key")
            parent_summary = parent.get("summary", parent_key)
        elif isinstance(parent, str):
            parent_key = parent
            parent_summary = parent

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

    # Issue type icon (matches Sprint Tracker pattern from visualization/sprint_charts.py)
    issue_type_lower = issue_type.lower()
    if "bug" in issue_type_lower or "defect" in issue_type_lower:
        type_icon = "fas fa-bug text-danger"  # Red for bugs
    elif "task" in issue_type_lower or "sub-task" in issue_type_lower:
        type_icon = "fas fa-tasks text-primary"  # Blue for tasks
    elif "story" in issue_type_lower or "user story" in issue_type_lower:
        type_icon = "fas fa-book text-success"  # Green for stories
    elif "epic" in issue_type_lower:
        type_icon = "fas fa-flag"  # Purple for epics (color set inline below)
    else:
        type_icon = "fas fa-circle text-secondary"  # Gray for unknown

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
        # Has parent - show connection with summary
        link_text = parent_summary if parent_summary else parent_key
        parent_link = create_jira_issue_link(
            parent_key,            text=link_text,            className="badge bg-light text-dark border",
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

    # Build card
    card = dbc.Card(
        dbc.CardBody(
            [
                # Parent epic indicator at top
                parent_indicator,
                html.Div(
                    [
                        # Left: Type icon + Key (clickable) + Summary
                        html.Div(
                            [
                                html.I(
                                    className=f"{type_icon} me-2",
                                    style={"color": "#6f42c1"} if "epic" in issue_type.lower() else {}
                                ),
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
    )
    
    # Wrap with div that has data attributes (dbc.Card doesn't accept data-* kwargs)
    if card_data_attrs:
        return html.Div(card, **card_data_attrs)
    else:
        return card
