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
    completion_pct = summary_data.get("completion_pct", 0.0)

    # Determine status colors
    if completion_pct >= 80:
        status_color = "#28a745"  # Green
        status_bg = "rgba(40, 167, 69, 0.1)"
        status_icon = "fa-check-circle"
    elif completion_pct >= 50:
        status_color = "#ffc107"  # Yellow
        status_bg = "rgba(255, 193, 7, 0.1)"
        status_icon = "fa-clock"
    else:
        status_color = "#dc3545"  # Red
        status_bg = "rgba(220, 53, 69, 0.1)"
        status_icon = "fa-exclamation-triangle"

    cards = [
        # Completion Card
        dbc.Col(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.I(
                                    className=f"fas {status_icon} fa-2x",
                                    style={"color": status_color},
                                ),
                            ],
                            className="mb-2",
                        ),
                        html.H2(
                            f"{completion_pct:.1f}%",
                            className="mb-1",
                            style={"color": status_color},
                        ),
                        html.P("Completion", className="text-muted mb-0 small"),
                    ],
                    className="text-center p-3 rounded h-100",
                    style={"backgroundColor": status_bg},
                )
            ],
            xs=12,
            md=3,
            className="mb-3",
        ),
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
        # In Progress Card
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
                        html.P("In Progress", className="text-muted mb-0 small"),
                    ],
                    className="text-center p-3 rounded h-100",
                    style={"backgroundColor": "rgba(255, 193, 7, 0.1)"},
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
        points_completion_pct = summary_data.get("points_completion_pct", 0.0)

        cards.extend(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-chart-pie fa-2x text-primary",
                                        ),
                                    ],
                                    className="mb-2",
                                ),
                                html.H2(
                                    f"{total_points:.0f}",
                                    className="mb-1 text-primary",
                                ),
                                html.P(
                                    "Total Points", className="text-muted mb-0 small"
                                ),
                            ],
                            className="text-center p-3 rounded h-100",
                            style={"backgroundColor": "rgba(0, 123, 255, 0.1)"},
                        )
                    ],
                    xs=12,
                    md=3,
                    className="mb-3",
                ),
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-medal fa-2x",
                                            style={"color": status_color},
                                        ),
                                    ],
                                    className="mb-2",
                                ),
                                html.H2(
                                    f"{points_completion_pct:.1f}%",
                                    className="mb-1",
                                    style={"color": status_color},
                                ),
                                html.P(
                                    "Points Completed",
                                    className="text-muted mb-0 small",
                                ),
                            ],
                            className="text-center p-3 rounded h-100",
                            style={"backgroundColor": status_bg},
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
    added_count: int, removed_count: int, moved_in: int, moved_out: int
) -> html.Div:
    """Create badge indicators for sprint composition changes with tooltips.

    Args:
        added_count: Number of issues added
        removed_count: Number of issues removed
        moved_in: Number of issues moved in from other sprints
        moved_out: Number of issues moved out to other sprints

    Returns:
        Row of badge indicators with tooltips
    """
    badges = []

    if added_count > 0:
        badges.append(
            dbc.Tooltip(
                "Issues that were added to this sprint after it started.",
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

    if removed_count > 0:
        badges.append(
            dbc.Tooltip(
                "Issues removed from this sprint (moved back to backlog).",
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

    if moved_in > 0:
        badges.append(
            dbc.Tooltip(
                "Issues transferred from another sprint to this sprint.",
                target="badge-moved-in",
                placement="top",
            )
        )
        badges.append(
            dbc.Badge(
                [
                    html.I(className="fas fa-arrow-right me-1"),
                    f"{moved_in} Moved In",
                ],
                color="info",
                className="me-2",
                id="badge-moved-in",
            )
        )

    if moved_out > 0:
        badges.append(
            dbc.Tooltip(
                "Issues moved from this sprint to a different sprint.",
                target="badge-moved-out",
                placement="top",
            )
        )
        badges.append(
            dbc.Badge(
                [
                    html.I(className="fas fa-arrow-left me-1"),
                    f"{moved_out} Moved Out",
                ],
                color="warning",
                className="me-2",
                id="badge-moved-out",
            )
        )

    if not badges:
        return html.Div()

    return html.Div(
        [
            html.H6("Sprint Changes:", className="d-inline me-2"),
            html.Div(badges, className="d-inline"),
        ],
        className="mb-3 p-2 bg-light rounded",
    )
