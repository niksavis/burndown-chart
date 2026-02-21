"""
Enhanced Save Query Modal

Modal for saving JQL queries with smart naming and clear update vs. save-as-new options.
Shows data loss warnings when updating existing queries.
"""

import dash_bootstrap_components as dbc
from dash import html


def create_save_query_modal() -> dbc.Modal:
    """
    Create enhanced save query modal with update/save-as-new options.

    Features:
    - JQL preview
    - Auto-suggested name (editable)
    - Radio buttons: Update existing vs Save as new
    - Prominent data loss warning for updates
    - Data preservation message for save-as-new

    Returns:
        dbc.Modal component
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle([html.I(className="fas fa-save me-2"), "Save Query"]),
                close_button=True,
            ),
            dbc.ModalBody(
                [
                    # JQL Preview
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
                    # Query Name Input
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
                    # Save Options (Update vs. Save as New)
                    html.Div(
                        [
                            html.H6("Save Options:", className="mb-3 fw-bold"),
                            # Update Existing Option
                            dbc.RadioItems(
                                id="save-query-mode-radio",
                                options=[
                                    {
                                        "label": "",
                                        "value": "update",
                                    },  # Label added dynamically
                                    {"label": "", "value": "new"},
                                ],
                                value="update",  # Default to update
                                className="mb-0",
                            ),
                            # Dynamic labels and warnings container
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
    """
    Create content for save mode radio options with warnings.

    Args:
        mode: Current mode ("update" or "new")
        query_name: Name of query being updated (if applicable)
        is_new_query: Whether this is a new query (no update option)

    Returns:
        html.Div with radio labels and warning messages
    """
    if is_new_query:
        # New query - only "Save as new" option
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

    # Existing query - show both options
    return html.Div(
        [
            # Update Existing Option
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
                    # Data Loss Warning (shown when update selected)
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
            # Save as New Option
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
                    # Data Preservation Message (shown when new selected)
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
