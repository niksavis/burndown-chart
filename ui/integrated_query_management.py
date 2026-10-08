import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.jql_editor import create_jql_editor


def create_integrated_query_management() -> dbc.Card:

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(className="fas fa-code me-2"),
                                    "JQL Query Editor",
                                ],
                                className="mb-0 d-inline-block",
                            ),
                            html.Span(
                                [
                                    html.I(className="fas fa-exclamation-circle me-1"),
                                    "Unsaved changes",
                                ],
                                id="query-unsaved-badge",
                                className="badge bg-warning text-dark ms-3",
                                style={"display": "none"},
                            ),
                        ],
                        className="d-flex align-items-center",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.Label(
                                "JQL Query:",
                                html_for="integrated-jql-editor",
                                className="form-label fw-bold mb-2",
                            ),
                            create_jql_editor(
                                editor_id="integrated-jql-editor",
                                initial_value="",
                                placeholder=(
                                    "Enter JQL query (e.g., project = KAFKA "
                                    "AND status = Done ORDER BY created DESC)"
                                ),
                                rows=5,
                            ),
                            html.Div(
                                [
                                    html.I(className="fas fa-rocket text-success me-2"),
                                    html.Strong(
                                        "Performance Tip: ",
                                        className="text-success",
                                    ),
                                    html.Span(
                                        (
                                            "For faster queries, query only "
                                            "development projects here. "
                                            "Configure DevOps projects in "
                                            "Field Mappings → Environment → "
                                            "DevOps Projects, and they'll be "
                                            "fetched automatically with "
                                            "optimized filtering."
                                        ),
                                        className="text-muted",
                                    ),
                                ],
                                className=(
                                    "alert alert-success border-success "
                                    "mt-2 mb-2 py-2 px-3"
                                ),
                                style={"fontSize": "0.875rem"},
                            ),
                            html.Small(
                                [
                                    html.I(className="fas fa-keyboard me-1"),
                                    "Tip: Ctrl+S to save, Ctrl+Z to revert",
                                ],
                                className="text-muted d-block mt-1",
                            ),
                        ],
                        className="mb-3",
                    ),
                    html.Div(
                        [
                            html.Small(
                                [
                                    html.I(className="fas fa-lightbulb me-1"),
                                    "Suggested name: ",
                                    html.Span(
                                        id="query-name-suggestion",
                                        className="fw-bold",
                                    ),
                                ],
                                className="text-muted",
                            ),
                        ],
                        id="query-name-suggestion-container",
                        className="mb-3",
                        style={"display": "none"},
                    ),
                    html.Hr(className="my-3"),
                    html.Div(
                        [
                            html.Label(
                                "Saved Queries:",
                                html_for="integrated-query-selector",
                                className="form-label fw-bold mb-2",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dcc.Dropdown(
                                                id="integrated-query-selector",
                                                options=[],
                                                value=None,
                                                placeholder=(
                                                    "Select a saved query to load..."
                                                ),
                                                clearable=False,
                                                searchable=True,
                                                className="mb-2",
                                            ),
                                            html.Small(
                                                "Select a query to load its "
                                                "JQL into the editor above",
                                                className="text-muted",
                                            ),
                                        ],
                                        xs=12,
                                        lg=8,
                                        className="mb-3 mb-lg-0",
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Button(
                                                [
                                                    html.I(
                                                        className="fas fa-trash me-2"
                                                    ),
                                                    "Delete",
                                                ],
                                                id="integrated-delete-query-button",
                                                color="danger",
                                                outline=True,
                                                size="md",
                                                className="w-100",
                                                disabled=True,
                                            ),
                                        ],
                                        xs=12,
                                        lg=4,
                                    ),
                                ],
                                className="g-2",
                            ),
                        ],
                        className="mb-3",
                    ),
                    html.Hr(className="my-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-save me-2"),
                                            "Save Query",
                                        ],
                                        id="integrated-save-query-button",
                                        color="primary",
                                        size="lg",
                                        className="w-100",
                                        disabled=True,
                                    ),
                                ],
                                xs=12,
                                md=6,
                                className="mb-2 mb-md-0",
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-undo me-2"),
                                            "Revert Changes",
                                        ],
                                        id="integrated-revert-query-button",
                                        color="secondary",
                                        outline=True,
                                        size="lg",
                                        className="w-100",
                                        style={"display": "none"},
                                    ),
                                ],
                                xs=12,
                                md=6,
                            ),
                        ],
                        className="g-2 mb-3",
                    ),
                    html.Div(
                        [
                            html.Small(
                                [
                                    html.I(
                                        className=(
                                            "fas fa-check-circle text-success me-1"
                                        )
                                    ),
                                    "Last saved: ",
                                    html.Span(id="query-last-saved-time"),
                                ],
                                id="query-last-saved-indicator",
                                className="text-muted",
                                style={"display": "none"},
                            ),
                        ],
                        className="text-center",
                    ),
                    dcc.Store(
                        id="query-state-store",
                        data={
                            "activeQueryId": None,
                            "activeQueryName": None,
                            "savedJql": "",
                            "currentJql": "",
                            "hasUnsavedChanges": False,
                            "lastModified": None,
                            "suggestedName": "",
                        },
                    ),
                    dcc.Store(id="pending-query-switch-store", data=None),
                ]
            ),
        ],
        className="mb-3",
    )
