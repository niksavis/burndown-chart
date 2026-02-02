"""Sprint Tracker UI Components

This module provides UI components for the Sprint Tracker tab including:
- Sprint selection dropdown
- Sprint summary cards
- Progress bar visualizations
- Empty state when no sprints detected

Follows Bug Analysis pattern for conditional tab display.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import Dict, List, Optional


def create_sprint_tracker_tab() -> html.Div:
    """Create Sprint Tracker tab container.

    This is an empty placeholder - content is rendered dynamically
    by visualization callback following Bug Analysis pattern.

    Returns:
        Empty div that will be populated by callback
    """
    return html.Div(id="sprint-tracker-tab-content", children=html.Div())


def create_no_sprints_state() -> html.Div:
    """Create empty state when no sprint data is detected.

    Returns:
        Centered empty state with icon and message
    """
    return html.Div(
        [
            html.Div(
                [
                    html.I(className="fas fa-info-circle fa-4x text-info mb-3"),
                    html.H4("No Sprint Data Found", className="text-center mb-3"),
                    html.P(
                        [
                            "Sprint tracking requires your JIRA instance to have Agile/Scrum boards with active sprints. ",
                            "The sprint field (typically ",
                            html.Code("customfield_10020"),
                            ") should be auto-detected, or you can configure it manually.",
                        ],
                        className="text-center text-muted mb-3",
                    ),
                    html.P(
                        [
                            "To configure: Go to ",
                            html.Strong(
                                "Configure JIRA Mappings → Fields → General Fields → Sprint"
                            ),
                            ". After configuration, click ",
                            html.Strong("Update Data"),
                            " to fetch sprint changelog from JIRA.",
                        ],
                        className="text-center text-muted",
                    ),
                ],
                className="d-flex flex-column align-items-center justify-content-center",
                style={"minHeight": "400px"},
            )
        ],
        className="container-fluid",
    )


def create_sprint_summary_cards(
    sprint_name: str, summary_data: Dict, show_points: bool = False
) -> html.Div:
    """Create sprint summary metric cards.

    Args:
        sprint_name: Name of the sprint
        summary_data: Summary metrics from sprint_manager.create_sprint_summary_card()
        show_points: Whether to show story points metrics

    Returns:
        Row of metric cards showing sprint progress
    """
    total_issues = summary_data.get("total_issues", 0)
    completed = summary_data.get("completed", 0)
    in_progress = summary_data.get("in_progress", 0)
    todo = summary_data.get("todo", 0)

    cards = [
        # Total Issues Card
        dbc.Col(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-tasks fa-2x text-info",
                                ),
                            ],
                            className="mb-2",
                        ),
                        html.H2(str(total_issues), className="mb-1 text-info"),
                        html.P("Total Issues", className="text-muted mb-0 small"),
                    ],
                    className="text-center p-3 rounded h-100",
                    style={"backgroundColor": "rgba(23, 162, 184, 0.1)"},
                )
            ],
            xs=12,
            md=3,
            className="mb-3",
        ),
        # To Do Card
        dbc.Col(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-list fa-2x text-secondary",
                                ),
                            ],
                            className="mb-2",
                        ),
                        html.H2(str(todo), className="mb-1 text-secondary"),
                        html.P("To Do", className="text-muted mb-0 small"),
                    ],
                    className="text-center p-3 rounded h-100",
                    style={"backgroundColor": "rgba(108, 117, 125, 0.1)"},
                )
            ],
            xs=12,
            md=3,
            className="mb-3",
        ),
        # Work in Progress Card
        dbc.Col(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-spinner fa-2x text-warning",
                                ),
                            ],
                            className="mb-2",
                        ),
                        html.H2(str(in_progress), className="mb-1 text-warning"),
                        html.P("Work in Progress", className="text-muted mb-0 small"),
                    ],
                    className="text-center p-3 rounded h-100",
                    style={"backgroundColor": "rgba(255, 193, 7, 0.1)"},
                )
            ],
            xs=12,
            md=3,
            className="mb-3",
        ),
        # Completed Card
        dbc.Col(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-check fa-2x text-success",
                                ),
                            ],
                            className="mb-2",
                        ),
                        html.H2(str(completed), className="mb-1 text-success"),
                        html.P("Completed", className="text-muted mb-0 small"),
                    ],
                    className="text-center p-3 rounded h-100",
                    style={"backgroundColor": "rgba(40, 167, 69, 0.1)"},
                )
            ],
            xs=12,
            md=3,
            className="mb-3",
        ),
    ]

    # Add story points cards if enabled
    if show_points:
        total_points = summary_data.get("total_points", 0.0)
        completed_points = summary_data.get("completed_points", 0.0)
        wip_points = summary_data.get("wip_points", 0.0)
        todo_points = summary_data.get("todo_points", 0.0)

        cards.extend(
            [
                # Total Points Card
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-chart-pie fa-2x text-info",
                                        ),
                                    ],
                                    className="mb-2",
                                ),
                                html.H2(
                                    f"{total_points:.0f}",
                                    className="mb-1 text-info",
                                ),
                                html.P(
                                    "Total Points", className="text-muted mb-0 small"
                                ),
                            ],
                            className="text-center p-3 rounded h-100",
                            style={"backgroundColor": "rgba(23, 162, 184, 0.1)"},
                        )
                    ],
                    xs=12,
                    md=3,
                    className="mb-3",
                ),
                # To Do Points Card
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-list fa-2x text-secondary",
                                        ),
                                    ],
                                    className="mb-2",
                                ),
                                html.H2(
                                    f"{todo_points:.0f}",
                                    className="mb-1 text-secondary",
                                ),
                                html.P(
                                    "Points To Do",
                                    className="text-muted mb-0 small",
                                ),
                            ],
                            className="text-center p-3 rounded h-100",
                            style={"backgroundColor": "rgba(108, 117, 125, 0.1)"},
                        )
                    ],
                    xs=12,
                    md=3,
                    className="mb-3",
                ),
                # WIP Points Card
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-spinner fa-2x text-warning",
                                        ),
                                    ],
                                    className="mb-2",
                                ),
                                html.H2(
                                    f"{wip_points:.0f}",
                                    className="mb-1 text-warning",
                                ),
                                html.P(
                                    "Points in Progress",
                                    className="text-muted mb-0 small",
                                ),
                            ],
                            className="text-center p-3 rounded h-100",
                            style={"backgroundColor": "rgba(255, 193, 7, 0.1)"},
                        )
                    ],
                    xs=12,
                    md=3,
                    className="mb-3",
                ),
                # Completed Points Card
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-check fa-2x text-success",
                                        ),
                                    ],
                                    className="mb-2",
                                ),
                                html.H2(
                                    f"{completed_points:.0f}",
                                    className="mb-1 text-success",
                                ),
                                html.P(
                                    "Points Completed",
                                    className="text-muted mb-0 small",
                                ),
                            ],
                            className="text-center p-3 rounded h-100",
                            style={"backgroundColor": "rgba(40, 167, 69, 0.1)"},
                        )
                    ],
                    xs=12,
                    md=3,
                    className="mb-3",
                ),
            ]
        )

    return html.Div(
        [
            html.H5(f"Sprint: {sprint_name}", className="mb-3"),
            dbc.Row(cards, className="g-3"),
        ],
        className="mb-4",
    )


def create_sprint_selector(
    available_sprints: List[str],
    selected_sprint: Optional[str] = None,
    sprint_metadata: Optional[Dict[str, Dict]] = None,
) -> html.Div:
    """Create sprint selection dropdown with status indicators.

    Args:
        available_sprints: List of sprint names/IDs
        selected_sprint: Currently selected sprint (to set as dropdown value)
        sprint_metadata: Dict mapping sprint name to {"state": "ACTIVE/CLOSED/FUTURE", ...}

    Returns:
        Dropdown component for sprint selection with status badges
    """
    if not available_sprints:
        return html.Div()

    # Use selected sprint if provided, otherwise default to first
    dropdown_value = (
        selected_sprint
        if selected_sprint in available_sprints
        else (available_sprints[0] if available_sprints else None)
    )

    # Create dropdown options with status suffixes
    options = []
    for sprint in available_sprints:
        label = sprint
        if sprint_metadata and sprint in sprint_metadata:
            state = sprint_metadata[sprint].get("state", "")
            if state == "ACTIVE":
                label = f"{sprint} [Active]"
            elif state == "CLOSED":
                label = f"{sprint} [Closed]"
            elif state == "FUTURE":
                label = f"{sprint} [Future]"
        options.append({"label": label, "value": sprint})

    return html.Div(
        [
            dbc.Label("Select Sprint:", html_for="sprint-selector-dropdown"),
            dcc.Dropdown(
                id="sprint-selector-dropdown",
                options=options,
                value=dropdown_value,
                clearable=False,
            ),
        ]
    )


def create_sprint_filters() -> html.Div:
    """Create filter controls for sprint view (issue type only).

    Returns:
        Filter controls (issue type dropdown)
    """
    return html.Div(
        [
            dbc.Label("Select Issue Type:", html_for="sprint-issue-type-filter"),
            dcc.Dropdown(
                id="sprint-issue-type-filter",
                options=[
                    {"label": "All", "value": "all"},
                    {"label": "Story", "value": "Story"},
                    {"label": "Task", "value": "Task"},
                    {"label": "Bug", "value": "Bug"},
                ],
                value="all",
                clearable=False,
            ),
        ]
    )


def create_combined_sprint_controls(
    available_sprints: List[str],
    selected_sprint: Optional[str] = None,
    sprint_metadata: Optional[Dict[str, Dict]] = None,
) -> html.Div:
    """Create combined sprint selector and issue type filter in one styled container.

    Args:
        available_sprints: List of sprint names/IDs
        selected_sprint: Currently selected sprint
        sprint_metadata: Dict mapping sprint name to {"state": "ACTIVE/CLOSED/FUTURE", ...}

    Returns:
        Styled container with both dropdowns in one row
    """
    if not available_sprints:
        return html.Div()

    # Use selected sprint if provided, otherwise default to first
    dropdown_value = (
        selected_sprint
        if selected_sprint in available_sprints
        else (available_sprints[0] if available_sprints else None)
    )

    # Create sprint dropdown options with status suffixes
    sprint_options = []
    for sprint in available_sprints:
        label = sprint
        if sprint_metadata and sprint in sprint_metadata:
            state = sprint_metadata[sprint].get("state", "")
            if state == "ACTIVE":
                label = f"{sprint} [Active]"
            elif state == "CLOSED":
                label = f"{sprint} [Closed]"
            elif state == "FUTURE":
                label = f"{sprint} [Future]"
        sprint_options.append({"label": label, "value": sprint})

    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label(
                                "Select Sprint:", html_for="sprint-selector-dropdown"
                            ),
                            dcc.Dropdown(
                                id="sprint-selector-dropdown",
                                options=sprint_options,
                                value=dropdown_value,
                                clearable=False,
                            ),
                        ],
                        xs=12,
                        md=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Label(
                                "Select Issue Type:",
                                html_for="sprint-issue-type-filter",
                            ),
                            dcc.Dropdown(
                                id="sprint-issue-type-filter",
                                options=[
                                    {"label": "All", "value": "all"},
                                    {"label": "Story", "value": "Story"},
                                    {"label": "Task", "value": "Task"},
                                    {"label": "Bug", "value": "Bug"},
                                ],
                                value="all",
                                clearable=False,
                            ),
                        ],
                        xs=12,
                        md=6,
                    ),
                ],
                className="g-2",
            )
        ],
        className="mb-4 p-3 bg-light rounded",
    )


def create_sprint_change_indicators(
    added_count: int, removed_count: int, net_change: int
) -> html.Div:
    """Create badge indicators for sprint scope changes with tooltips.

    Args:
        added_count: Number of issues added after sprint start
        removed_count: Number of issues removed after sprint start
        net_change: Net scope change (added - removed)

    Returns:
        Row of badge indicators with tooltips
    """
    badges = []

    # Added badge
    if added_count > 0:
        badges.append(
            dbc.Tooltip(
                "Issues added to this sprint after it started",
                target="badge-added",
                placement="top",
            )
        )
        badges.append(
            dbc.Badge(
                [html.I(className="fas fa-plus me-1"), f"{added_count} Added"],
                color="success",
                className="me-2",
                id="badge-added",
            )
        )

    # Removed badge
    if removed_count > 0:
        badges.append(
            dbc.Tooltip(
                "Issues removed from this sprint after it started",
                target="badge-removed",
                placement="top",
            )
        )
        badges.append(
            dbc.Badge(
                [html.I(className="fas fa-minus me-1"), f"{removed_count} Removed"],
                color="danger",
                className="me-2",
                id="badge-removed",
            )
        )

    # Net change badge
    if net_change != 0:
        net_icon = "fa-arrow-up" if net_change > 0 else "fa-arrow-down"
        net_color = "info" if net_change > 0 else "warning"
        net_sign = "+" if net_change > 0 else ""

        badges.append(
            dbc.Tooltip(
                "Overall change in sprint scope (Added - Removed)",
                target="badge-net-change",
                placement="top",
            )
        )
        badges.append(
            dbc.Badge(
                [
                    html.I(className=f"fas {net_icon} me-1"),
                    f"{net_sign}{net_change} Net Change",
                ],
                color=net_color,
                className="me-2",
                id="badge-net-change",
            )
        )

    if not badges:
        return html.Div()

    return html.Div(
        [
            html.H6("Sprint Scope Changes:", className="d-inline me-2"),
            html.Div(badges, className="d-inline"),
        ],
        className="mb-3 p-2 bg-light rounded",
    )
