"""
Status Configuration Form Component

Provides UI for configuring JIRA status lists with subset validation.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_status_config_form(
    flow_end_statuses=None,
    active_statuses=None,
    flow_start_statuses=None,
    wip_statuses=None,
    available_statuses=None,
):
    """
    Create status list configuration form.

    Args:
        flow_end_statuses: List of completion status names
        active_statuses: List of active status names
        flow_start_statuses: List of flow start status names
        wip_statuses: List of WIP status names
        available_statuses: List of available status dictionaries from JIRA

    Returns:
        Dash component with status configuration UI
    """
    flow_end_statuses = flow_end_statuses or []
    active_statuses = active_statuses or []
    flow_start_statuses = flow_start_statuses or []
    wip_statuses = wip_statuses or []
    available_statuses = available_statuses or []

    # Create options for dropdowns, grouped by category.
    # Include current values even if metadata has not been fetched yet.
    status_options = [
        {
            "label": f"{s.get('name', '')} ({s.get('category_name', 'Unknown')})",
            "value": s.get("name", ""),
        }
        for s in available_statuses
    ]

    # Add current values to options if not already present (ensures they display)
    existing_statuses = {s.get("name", "") for s in available_statuses}
    for status in (
        flow_end_statuses + active_statuses + flow_start_statuses + wip_statuses
    ):
        if status and status not in existing_statuses:
            status_options.append({"label": status, "value": status})

    return html.Div(
        [
            # Flow Metrics Status Classification Card
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H5("Flow Metrics Status Classification", className="mb-0"),
                        className="bg-light",
                    ),
                    dbc.CardBody(
                        [
                            html.P(
                                (
                                    "Configure status mappings for Flow metrics "
                                    "calculation. These statuses determine how "
                                    "issues flow through your workflow."
                                ),
                                className="text-muted small mb-3",
                            ),
                            # WIP Statuses (first - the superset)
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-spinner me-2 "
                                                            "text-warning"
                                                        )
                                                    ),
                                                    "Work In Progress (WIP) ",
                                                    html.Span(
                                                        "*",
                                                        className="text-danger",
                                                        title=(
                                                            "Required for Flow "
                                                            "Load, Flow Efficiency"
                                                        ),
                                                    ),
                                                ],
                                                className="form-label fw-bold",
                                            ),
                                            html.P(
                                                (
                                                    "All statuses where work is in "
                                                    "progress (superset for Flow "
                                                    "Start and Active)"
                                                ),
                                                className="text-muted small mb-2",
                                            ),
                                        ],
                                        width=12,
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Dropdown(
                                                id="wip-statuses-dropdown",
                                                # type: ignore  # Dash accepts list[dict]
                                                options=status_options,
                                                value=wip_statuses,
                                                multi=True,
                                                placeholder=(
                                                    "Type or select statuses..."
                                                ),
                                                className="mb-2",
                                                clearable=True,
                                                searchable=True,
                                                optionHeight=50,
                                                maxHeight=300,
                                            ),
                                        ],
                                        width=12,
                                        md=8,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Flow Start Statuses
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-flag me-2 text-info"
                                                        )
                                                    ),
                                                    "Flow Start ",
                                                    html.Span(
                                                        "*",
                                                        className="text-danger",
                                                        title="Required for Flow Time",
                                                    ),
                                                ],
                                                className="form-label fw-bold",
                                            ),
                                            html.P(
                                                (
                                                    "Flow Time measurement starts "
                                                    "when issues enter these "
                                                    "statuses (subset of WIP)"
                                                ),
                                                className="text-muted small mb-2",
                                            ),
                                            # Dynamic validation warning - shown only
                                            # when Flow Start has values not in WIP
                                            html.Div(
                                                id="flow-start-wip-subset-warning",
                                                className="mb-2",
                                            ),
                                        ],
                                        width=12,
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Dropdown(
                                                id="flow-start-statuses-dropdown",
                                                # type: ignore  # Dash accepts list[dict]
                                                options=status_options,
                                                value=flow_start_statuses,
                                                multi=True,
                                                placeholder=(
                                                    "Type or select statuses..."
                                                ),
                                                className="mb-2",
                                                clearable=True,
                                                searchable=True,
                                                optionHeight=50,
                                                maxHeight=300,
                                            ),
                                        ],
                                        width=12,
                                        md=8,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Active Statuses
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-play-circle me-2 "
                                                            "text-primary"
                                                        )
                                                    ),
                                                    "Active ",
                                                    html.Span(
                                                        "*",
                                                        className="text-danger",
                                                        title=(
                                                            "Required for "
                                                            "Flow Efficiency"
                                                        ),
                                                    ),
                                                ],
                                                className="form-label fw-bold",
                                            ),
                                            html.P(
                                                (
                                                    "Statuses indicating active "
                                                    "work (subset of WIP)"
                                                ),
                                                className="text-muted small mb-2",
                                            ),
                                            # Dynamic validation warning - shown only
                                            # when Active has values not in WIP
                                            html.Div(
                                                id="active-wip-subset-warning",
                                                className="mb-2",
                                            ),
                                        ],
                                        width=12,
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Dropdown(
                                                id="active-statuses-dropdown",
                                                # type: ignore  # Dash accepts list[dict]
                                                options=status_options,
                                                value=active_statuses,
                                                multi=True,
                                                placeholder=(
                                                    "Type or select statuses..."
                                                ),
                                                className="mb-2",
                                                clearable=True,
                                                searchable=True,
                                                optionHeight=50,
                                                maxHeight=300,
                                            ),
                                        ],
                                        width=12,
                                        md=8,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Flow End (Completion) Statuses
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-check-circle me-2 "
                                                            "text-success"
                                                        )
                                                    ),
                                                    "Flow End ",
                                                    html.Span(
                                                        "*",
                                                        className="text-danger",
                                                        title=(
                                                            "Required for Flow "
                                                            "Velocity, Flow Time, "
                                                            "Flow Efficiency, "
                                                            "Flow Distribution"
                                                        ),
                                                    ),
                                                ],
                                                className="form-label fw-bold",
                                            ),
                                            html.P(
                                                (
                                                    "Issues with these statuses are "
                                                    "counted as completed"
                                                ),
                                                className="text-muted small mb-2",
                                            ),
                                        ],
                                        width=12,
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Dropdown(
                                                id="completion-statuses-dropdown",
                                                # type: ignore  # Dash accepts list[dict]
                                                options=status_options,
                                                value=flow_end_statuses,
                                                multi=True,
                                                placeholder=(
                                                    "Type or select statuses..."
                                                ),
                                                className="mb-2",
                                                clearable=True,
                                                searchable=True,
                                                optionHeight=50,
                                                maxHeight=300,
                                            ),
                                        ],
                                        width=12,
                                        md=8,
                                    ),
                                ],
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            ),
            # Validation warnings
            html.Div(id="status-config-validation-warnings", className="mt-3"),
            # Auto-detection info
            html.Div(
                id="status-auto-detection-info",
                className="mt-3 alert alert-info",
                style={"display": "none"},
            ),
        ],
    )
