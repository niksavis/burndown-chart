"""Sprint Tracker UI Components

This module provides UI components for the Sprint Tracker tab including:
- Sprint selection dropdown
- Sprint summary cards
- Progress bar visualizations
- Empty state when no sprints detected

Follows Bug Analysis pattern for conditional tab display.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.jira_link_helper import create_jira_issue_link


def create_sprint_tracker_tab() -> html.Div:
    """Create Sprint Tracker tab container.

    This is an empty placeholder - content is rendered dynamically
    by visualization callback following Bug Analysis pattern.

    Returns:
        Empty div that will be populated by callback
    """
    return html.Div(id="sprint-tracker-tab-content", children=html.Div())


def create_sprint_summary_cards(
    sprint_name: str,
    summary_data: dict,
    show_points: bool = False,
    scope_change_summary: dict | None = None,
    sprint_state: str | None = None,
) -> html.Div:
    """Create sprint summary metric cards.

    Args:
        sprint_name: Name of the sprint
        summary_data: Summary metrics from sprint_manager.create_sprint_summary_card()
        show_points: Whether to show story points metrics
        scope_change_summary: Optional scope summary with added/removed counts
        sprint_state: Sprint state (ACTIVE/CLOSED/FUTURE)

    Returns:
        Row of metric cards showing sprint progress
    """
    total_issues = summary_data.get("total_issues", 0)
    completed = summary_data.get("completed", 0)
    in_progress = summary_data.get("in_progress", 0)
    todo = summary_data.get("todo", 0)
    scope_change_summary = scope_change_summary or {}
    added_after_start = scope_change_summary.get("added_after_start", 0)
    removed_after_start = scope_change_summary.get("removed_after_start", 0)
    added_points_after_start = scope_change_summary.get("added_points_after_start", 0.0)
    removed_points_after_start = scope_change_summary.get(
        "removed_points_after_start", 0.0
    )

    def _metric_card(
        value: str,
        label: str,
        icon_class: str,
        text_class: str,
        background_color: str,
    ) -> dbc.Col:
        return dbc.Col(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.I(className=icon_class),
                            ],
                            className="mb-2",
                        ),
                        html.H2(value, className=f"mb-1 {text_class}"),
                        html.P(label, className="text-muted mb-0 small"),
                    ],
                    className="text-center p-3 rounded h-100",
                    style={"backgroundColor": background_color},
                )
            ],
            xs=12,
            md=2,
            className="mb-3",
        )

    issue_cards = [
        _metric_card(
            str(total_issues),
            "Total",
            "fas fa-tasks fa-2x text-info",
            "text-info",
            "rgba(23, 162, 184, 0.1)",
        ),
        _metric_card(
            str(todo),
            "To Do",
            "fas fa-list fa-2x text-secondary",
            "text-secondary",
            "rgba(108, 117, 125, 0.1)",
        ),
        _metric_card(
            str(in_progress),
            "Work in Progress",
            "fas fa-spinner fa-2x text-warning",
            "text-warning",
            "rgba(255, 193, 7, 0.1)",
        ),
        _metric_card(
            str(completed),
            "Completed",
            "fas fa-check fa-2x text-success",
            "text-success",
            "rgba(40, 167, 69, 0.1)",
        ),
        _metric_card(
            str(added_after_start),
            "Added After Start",
            "fas fa-arrow-up-right-dots fa-2x text-success",
            "text-success",
            "rgba(40, 167, 69, 0.1)",
        ),
        _metric_card(
            str(removed_after_start),
            "Removed After Start",
            "fas fa-arrow-down-short-wide fa-2x text-danger",
            "text-danger",
            "rgba(220, 53, 69, 0.1)",
        ),
    ]

    points_section: list = []
    if show_points:
        total_points = summary_data.get("total_points", 0.0)
        completed_points = summary_data.get("completed_points", 0.0)
        wip_points = summary_data.get("wip_points", 0.0)
        todo_points = summary_data.get("todo_points", 0.0)

        points_cards = [
            _metric_card(
                f"{total_points:.0f}",
                "Total",
                "fas fa-chart-pie fa-2x text-info",
                "text-info",
                "rgba(23, 162, 184, 0.1)",
            ),
            _metric_card(
                f"{todo_points:.0f}",
                "To Do",
                "fas fa-list fa-2x text-secondary",
                "text-secondary",
                "rgba(108, 117, 125, 0.1)",
            ),
            _metric_card(
                f"{wip_points:.0f}",
                "Work in Progress",
                "fas fa-spinner fa-2x text-warning",
                "text-warning",
                "rgba(255, 193, 7, 0.1)",
            ),
            _metric_card(
                f"{completed_points:.0f}",
                "Completed",
                "fas fa-check fa-2x text-success",
                "text-success",
                "rgba(40, 167, 69, 0.1)",
            ),
            _metric_card(
                f"{added_points_after_start:.0f}",
                "Added After Start",
                "fas fa-arrow-up-right-dots fa-2x text-success",
                "text-success",
                "rgba(40, 167, 69, 0.1)",
            ),
            _metric_card(
                f"{removed_points_after_start:.0f}",
                "Removed After Start",
                "fas fa-arrow-down-short-wide fa-2x text-danger",
                "text-danger",
                "rgba(220, 53, 69, 0.1)",
            ),
        ]

        points_section = [
            html.Small(
                "Points",
                className="text-muted text-uppercase fw-semibold d-block mb-2",
            ),
            dbc.Row(points_cards, className="g-3"),
        ]

    header_suffix = ""
    if sprint_state == "CLOSED":
        header_suffix = " [Closed Snapshot]"
    elif sprint_state == "ACTIVE":
        header_suffix = " [Current Snapshot]"

    return html.Div(
        [
            html.H5(f"Sprint: {sprint_name}{header_suffix}", className="mb-3"),
            html.Small(
                "Issues",
                className="text-muted text-uppercase fw-semibold d-block mb-2",
            ),
            dbc.Row(issue_cards, className="g-3"),
            *points_section,
        ],
        className="mb-4",
    )


def create_sprint_scope_changes_view(
    scope_change_issues: dict[str, list[str]],
    sprint_state: str | None = None,
    issue_states: dict[str, dict] | None = None,
) -> html.Div | dbc.Card:
    """Create a sprint scope changes section with rich issue rows.

    Args:
        scope_change_issues: Dict with issue key lists for added and removed
        sprint_state: Sprint state (ACTIVE/CLOSED/FUTURE)
        issue_states: Optional mapping of issue_key to state dict
            (issue_type, summary, status, story_points)

    Returns:
        Scope changes section, or empty div when not applicable
    """
    if sprint_state not in {"ACTIVE", "CLOSED"}:
        return html.Div()

    added_issues = scope_change_issues.get("added", [])
    removed_issues = scope_change_issues.get("removed", [])

    if not added_issues and not removed_issues:
        return html.Div()

    states = issue_states or {}

    def _type_icon(issue_type: str) -> tuple[str, str]:
        t = issue_type.lower()
        if "bug" in t or "defect" in t:
            return ("fa-bug", "#dc3545")
        if "task" in t:
            return ("fa-tasks", "#0d6efd")
        if "story" in t:
            return ("fa-book", "#198754")
        if "epic" in t:
            return ("fa-flag", "#6f42c1")
        return ("fa-circle", "#6c757d")

    def _scope_row(key: str, is_added: bool) -> html.Div:
        state = states.get(key, {})
        issue_type = state.get("issue_type", "Unknown")
        summary = state.get("summary", "")
        if not summary:
            display_summary = "No summary available"
        else:
            display_summary = summary[:60] + "..." if len(summary) > 60 else summary
        icon_class, icon_color = _type_icon(issue_type)
        scope_cls = (
            "fa-solid fa-circle-plus text-success"
            if is_added
            else "fa-solid fa-circle-minus text-danger"
        )
        return html.Div(
            [
                html.I(
                    className=f"{scope_cls} me-1",
                    style={"fontSize": "0.75rem", "flexShrink": "0"},
                ),
                html.I(
                    className=f"fas {icon_class} me-1",
                    style={
                        "color": icon_color,
                        "fontSize": "0.8rem",
                        "flexShrink": "0",
                    },
                    title=issue_type,
                ),
                create_jira_issue_link(
                    key,
                    className="fw-semibold me-1",
                    style={
                        "fontSize": "0.85rem",
                        "color": "#495057",
                        "flexShrink": "0",
                    },
                ),
                html.Span(
                    display_summary,
                    className="text-muted text-truncate",
                    style={"fontSize": "0.82rem"},
                ),
            ],
            className="d-flex align-items-center py-1",
            style={"borderBottom": "1px solid #f0f0f0", "minWidth": "0"},
        )

    def _scope_list(keys: list[str], is_added: bool, empty_text: str) -> html.Div:
        if not keys:
            return html.Div(empty_text, className="text-muted small fst-italic")
        return html.Div([_scope_row(k, is_added) for k in keys])

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.I(className="fas fa-shuffle me-2"),
                    html.Strong(
                        "Scope Changes During Sprint"
                        if sprint_state == "CLOSED"
                        else "Scope Changes During Sprint (So Far)"
                    ),
                    html.Span(
                        " — see Issue Progress below for outcomes",
                        className="text-muted ms-1",
                        style={"fontSize": "0.82rem", "fontWeight": "normal"},
                    ),
                ]
            ),
            dbc.CardBody(
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H6(
                                    [
                                        html.I(
                                            className="fas fa-circle-plus text-success me-1"
                                        ),
                                        f"Added After Start ({len(added_issues)})",
                                    ],
                                    className="text-success mb-2",
                                ),
                                _scope_list(
                                    added_issues,
                                    is_added=True,
                                    empty_text="No issues were added after sprint start.",
                                ),
                            ],
                            xs=12,
                            md=6,
                        ),
                        dbc.Col(
                            [
                                html.H6(
                                    [
                                        html.I(
                                            className="fas fa-circle-minus text-danger me-1"
                                        ),
                                        f"Removed After Start ({len(removed_issues)})",
                                    ],
                                    className="text-danger mb-2",
                                ),
                                _scope_list(
                                    removed_issues,
                                    is_added=False,
                                    empty_text="No issues were removed after sprint start.",
                                ),
                            ],
                            xs=12,
                            md=6,
                        ),
                    ],
                    className="g-3",
                )
            ),
        ],
        className="mb-4",
    )


def create_sprint_selector(
    available_sprints: list[str],
    selected_sprint: str | None = None,
    sprint_metadata: dict[str, dict] | None = None,
) -> html.Div:
    """Create sprint selection dropdown with status indicators.

    Args:
        available_sprints: List of sprint names/IDs
        selected_sprint: Currently selected sprint (to set as dropdown value)
        sprint_metadata: Dict mapping sprint name to
            {"state": "ACTIVE/CLOSED/FUTURE", ...}

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
    available_sprints: list[str],
    selected_sprint: str | None = None,
    sprint_metadata: dict[str, dict] | None = None,
) -> html.Div:
    """Create combined sprint selector and issue type filter in one styled container.

    Args:
        available_sprints: List of sprint names/IDs
        selected_sprint: Currently selected sprint
        sprint_metadata: Dict mapping sprint name to
            {"state": "ACTIVE/CLOSED/FUTURE", ...}

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
                        md=4,
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
                        md=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Label(
                                "\u00a0",
                                html_for="toggle-sprint-charts",
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-chart-line me-2"),
                                    html.Span("Show Charts", id="toggle-charts-text"),
                                ],
                                id="toggle-sprint-charts",
                                color="primary",
                                outline=True,
                                className="w-100",
                                n_clicks=0,
                            ),
                        ],
                        xs=12,
                        md=4,
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
                trigger="click",
                autohide=True,
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
                trigger="click",
                autohide=True,
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
                trigger="click",
                autohide=True,
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


def create_sprint_charts_section() -> html.Div:
    """Create collapsible charts section for sprint burnup chart.

    Returns:
        Collapsible container with burnup chart (full width)
    """
    return html.Div(
        [
            # Collapsible charts container (button moved to combined controls)
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        [
                            # Burnup chart with loading spinner
                            dcc.Loading(
                                id="loading-sprint-chart",
                                type="circle",
                                children=[
                                    dcc.Graph(
                                        id="sprint-burnup-chart",
                                        config={"displayModeBar": False},
                                        style={"height": "450px"},
                                    )
                                ],
                            ),
                        ]
                    ),
                    className="shadow-sm",
                ),
                id="sprint-charts-collapse",
                is_open=False,
            ),
        ],
        className="mb-4",
    )
