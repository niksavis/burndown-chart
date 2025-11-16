"""
Delete Query Confirmation Modal

Confirms query deletion with clear warnings about data loss.
Shows what will be permanently deleted.
"""

import dash_bootstrap_components as dbc
from dash import html


def create_delete_query_modal() -> dbc.Modal:
    """
    Create modal for confirming query deletion.

    Shows:
    - Query name and JQL being deleted
    - Explicit warning about data loss
    - Cannot undo message

    Returns:
        dbc.Modal component
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(
                    [
                        html.I(className="fas fa-trash text-danger me-2"),
                        "Delete Query",
                    ]
                ),
                close_button=True,
            ),
            dbc.ModalBody(
                [
                    html.P(
                        "Are you sure you want to delete this query?",
                        className="mb-3",
                    ),
                    # Query Details
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Strong("Query: "),
                                    html.Span(
                                        id="delete-query-name",
                                        className="text-primary",
                                    ),
                                ],
                                className="mb-2",
                            ),
                        ],
                        className="p-3 bg-light border rounded mb-3",
                    ),
                    # Data Loss Warning
                    dbc.Alert(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-exclamation-triangle me-2"
                                    ),
                                    html.Strong("This will permanently delete:"),
                                ],
                                className="mb-2",
                            ),
                            html.Ul(
                                [
                                    html.Li("Cached JIRA data"),
                                    html.Li("Calculated metrics"),
                                    html.Li("Burndown statistics"),
                                    html.Li("All query-specific files"),
                                ],
                                className="mb-2",
                            ),
                            html.Div(
                                [
                                    html.I(className="fas fa-ban me-2"),
                                    html.Strong("This action cannot be undone."),
                                ],
                                className="text-danger",
                            ),
                        ],
                        color="danger",
                        className="mb-0",
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="cancel-delete-query-button",
                        color="secondary",
                        outline=True,
                        className="me-auto",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-trash me-2"), "Delete Query"],
                        id="confirm-delete-query-button",
                        color="danger",
                    ),
                ]
            ),
        ],
        id="delete-jql-query-modal",
        size="md",
        is_open=False,
        backdrop="static",
        centered=True,
    )
