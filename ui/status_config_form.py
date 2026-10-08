import dash_bootstrap_components as dbc
from dash import dcc, html


def create_status_config_form(
    flow_end_statuses=None,
    active_statuses=None,
    flow_start_statuses=None,
    wip_statuses=None,
    available_statuses=None,
):

    flow_end_statuses = flow_end_statuses or []
    active_statuses = active_statuses or []
    flow_start_statuses = flow_start_statuses or []
    wip_statuses = wip_statuses or []
    available_statuses = available_statuses or []

    status_options = [
        {
            "label": f"{s.get('name', '')} ({s.get('category_name', 'Unknown')})",
            "value": s.get("name", ""),
        }
        for s in available_statuses
    ]

    existing_statuses = {s.get("name", "") for s in available_statuses}
    for status in (
        flow_end_statuses + active_statuses + flow_start_statuses + wip_statuses
    ):
        if status and status not in existing_statuses:
            status_options.append({"label": status, "value": status})

    return html.Div(
        [
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
                                                options=status_options,  # type: ignore[arg-type]
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
                                                options=status_options,  # type: ignore[arg-type]
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
                                                options=status_options,  # type: ignore[arg-type]
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
                                                options=status_options,  # type: ignore[arg-type]
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
            html.Div(id="status-config-validation-warnings", className="mt-3"),
            html.Div(
                id="status-auto-detection-info",
                className="mt-3 alert alert-info",
                style={"display": "none"},
            ),
        ],
    )
