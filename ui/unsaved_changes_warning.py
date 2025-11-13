"""
Unsaved Changes Warning Component

Provides visual feedback when users have unsaved changes in the JQL editor
to prevent data loss when switching profiles or making other changes.
"""

import dash_bootstrap_components as dbc
from dash import html


def create_unsaved_changes_warning():
    """Create an unsaved changes warning component."""
    return dbc.Alert(
        [
            html.I(className="fas fa-exclamation-triangle me-2"),
            html.Strong("Unsaved Changes"),
            " - Your JQL query changes will be saved when you click Update Data.",
        ],
        id="unsaved-changes-warning",
        color="warning",
        className="d-none mt-2 mb-0",
        style={"fontSize": "0.875rem"},
    )


def create_query_status_indicator():
    """Create a query status indicator showing saved/unsaved state."""
    return html.Div(
        [
            html.Span(
                [
                    html.I(className="fas fa-check-circle me-1"),
                    "Query saved",
                ],
                id="query-saved-indicator",
                className="text-success small",
                style={"display": "none"},
            ),
            html.Span(
                [
                    html.I(className="fas fa-edit me-1"),
                    "Unsaved changes",
                ],
                id="query-unsaved-indicator",
                className="text-warning small",
                style={"display": "none"},
            ),
        ],
        id="query-status-container",
        className="mt-1",
    )
