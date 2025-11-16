"""
Integrated Query Management Component

Unified UI for JQL editing and query management. Combines JQL editor (primary)
with query selector and management actions (secondary). Implements JQL-first
workflow with smart naming and clear state management.

Features:
- Always-visible JQL editor with syntax highlighting
- Query dropdown for loading saved queries
- Unsaved changes indicator
- Save/Revert action buttons
- Delete query action
- Real-time name suggestion
- Keyboard shortcuts (Ctrl+S, Ctrl+Z)
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from ui.jql_editor import create_jql_editor


def create_integrated_query_management() -> dbc.Card:
    """
    Create integrated query management component.

    Layout hierarchy:
    1. JQL Editor (top, prominent, always editable)
    2. Real-time name suggestion (below editor)
    3. Query selector dropdown (load saved queries)
    4. Action buttons (Save, Revert, Delete)
    5. State indicators (unsaved changes badge, last saved time)

    Returns:
        dbc.Card containing complete query management UI
    """
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
                            # Unsaved changes badge
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
                    # 1. JQL Editor (Primary)
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
                                placeholder="Enter JQL query (e.g., project = KAFKA AND status = Done ORDER BY created DESC)",
                                rows=5,
                            ),
                            # Keyboard shortcuts hint
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
                    # 2. Real-time Name Suggestion
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
                    # 3. Query Selector (Secondary)
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
                                                placeholder="Select a saved query to load...",
                                                clearable=False,
                                                searchable=True,
                                                className="mb-2",
                                            ),
                                            html.Small(
                                                "Select a query to load its JQL into the editor above",
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
                                                disabled=True,  # Enabled when query loaded
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
                    # 4. Action Buttons
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
                                        disabled=True,  # Enabled when JQL has content
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
                                        style={
                                            "display": "none"
                                        },  # Shown when has unsaved changes
                                    ),
                                ],
                                xs=12,
                                md=6,
                            ),
                        ],
                        className="g-2 mb-3",
                    ),
                    # 5. State Indicators
                    html.Div(
                        [
                            html.Small(
                                [
                                    html.I(
                                        className="fas fa-check-circle text-success me-1"
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
                    # Hidden stores for state management
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
                    # Store for pending query switch (when unsaved changes exist)
                    dcc.Store(id="pending-query-switch-store", data=None),
                ]
            ),
        ],
        className="mb-3",
    )
