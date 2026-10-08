import dash_bootstrap_components as dbc
from dash import html


def create_save_query_modal() -> dbc.Modal:

    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle([html.I(className="fas fa-save me-2"), "Save Query"]),
                close_button=True,
            ),
            dbc.ModalBody(
                [
                    html.H6("Query:", className="mb-2 fw-bold"),
                    html.Div(
                        id="save-query-jql-preview",
                        className=(
                            "p-3 mb-3 bg-light border rounded font-monospace small"
                        ),
                        style={
                            "maxHeight": "120px",
                            "overflowY": "auto",
                            "whiteSpace": "pre-wrap",
                            "wordBreak": "break-all",
                        },
                    ),
                    html.H6("Query Name:", className="mb-2 fw-bold"),
                    dbc.Input(
                        id="save-query-name-input",
                        type="text",
                        placeholder="Enter query name...",
                        className="mb-2",
                        maxLength=100,
                    ),
                    html.Div(
                        id="save-query-name-validation",
                        className="text-danger small mb-3",
                    ),
                    html.Div(
                        [
                            html.H6("Save Options:", className="mb-3 fw-bold"),
                            dbc.RadioItems(
                                id="save-query-mode-radio",
                                options=[
                                    {
                                        "label": "",
                                        "value": "update",
                                    },
                                    {"label": "", "value": "new"},
                                ],
                                value="update",
                                className="mb-0",
                            ),
                            html.Div(id="save-query-mode-labels"),
                        ],
                        id="save-query-mode-container",
                        className="mb-3",
                    ),
                ],
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="save-query-cancel-button",
                        color="secondary",
                        outline=True,
                        className="me-2",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Save Query"],
                        id="save-query-confirm-button",
                        color="primary",
                    ),
                ]
            ),
        ],
        id="save-query-modal",
        size="lg",
        is_open=False,
        backdrop="static",
        centered=True,
    )


def create_save_mode_content(
    mode: str,
    query_name: str = "",
    is_new_query: bool = True,
) -> html.Div:

    if is_new_query:
        return html.Div(
            [
                html.Div(
                    [
                        html.I(className="fas fa-plus-circle text-primary me-2"),
                        html.Strong("Save as new query"),
                    ],
                    className="mb-2",
                ),
                html.P(
                    "This will create a new query with its own data workspace.",
                    className="text-muted small ms-4",
                ),
            ]
        )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            dbc.RadioItems(
                                options=[{"label": "", "value": "update"}],
                                value="update" if mode == "update" else None,
                                id="save-query-update-radio",
                                inline=True,
                            ),
                            html.Strong(
                                f'Update "{query_name}"',
                                className="ms-2",
                            ),
                            html.Span(
                                " (recommended for iterating)",
                                className="text-muted small ms-1",
                            ),
                        ],
                        className="d-flex align-items-center mb-2",
                    ),
                    html.Div(
                        dbc.Alert(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-exclamation-triangle me-2"
                                        ),
                                        html.Strong("WARNING: This will:"),
                                    ],
                                    className="mb-2",
                                ),
                                html.Ul(
                                    [
                                        html.Li("Re-fetch all data from JIRA"),
                                        html.Li("Recalculate all metrics"),
                                        html.Li(
                                            "Overwrite existing cache & statistics"
                                        ),
                                        html.Li("Existing burndown data will be lost"),
                                    ],
                                    className="mb-0 small",
                                ),
                            ],
                            color="warning",
                            className="ms-4 mb-3",
                        ),
                        style={"display": "block" if mode == "update" else "none"},
                        id="save-query-update-warning",
                    ),
                ],
                className="mb-3",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            dbc.RadioItems(
                                options=[{"label": "", "value": "new"}],
                                value="new" if mode == "new" else None,
                                id="save-query-new-radio",
                                inline=True,
                            ),
                            html.Strong(
                                "Save as new query",
                                className="ms-2",
                            ),
                        ],
                        className="d-flex align-items-center mb-2",
                    ),
                    html.Div(
                        dbc.Alert(
                            [
                                html.Div(
                                    [
                                        html.I(className="fas fa-check-circle me-2"),
                                        html.Strong("Benefits:"),
                                    ],
                                    className="mb-2",
                                ),
                                html.Ul(
                                    [
                                        html.Li(
                                            f'Preserves "{query_name}" data unchanged'
                                        ),
                                        html.Li(
                                            "Creates separate workspace with new data"
                                        ),
                                        html.Li("Allows comparison between queries"),
                                    ],
                                    className="mb-0 small",
                                ),
                            ],
                            color="success",
                            className="ms-4",
                        ),
                        style={"display": "block" if mode == "new" else "none"},
                        id="save-query-new-info",
                    ),
                ],
            ),
        ]
    )
