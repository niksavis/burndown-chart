"""
Query Creation Modal Component

Modal dialog for creating new queries within a profile.
Part of Feature 011 - Profile & Workspace Switching (Phase 4 - Query Switching).
"""

#######################################################################
# IMPORTS
#######################################################################
import dash_bootstrap_components as dbc
from dash import html

#######################################################################
# MODAL COMPONENT
#######################################################################


def create_query_creation_modal():
    """
    Create query creation modal dialog.

    Returns:
        dbc.Modal: Complete modal component with form fields for query creation
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Create New Query"), close_button=True),
            dbc.ModalBody(
                [
                    # Query Name
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Query Name",
                                        html_for="workspace-query-name-input",
                                        className="fw-bold",
                                    ),
                                    dbc.Input(
                                        id="workspace-query-name-input",
                                        type="text",
                                        placeholder=(
                                            "e.g., Current Sprint, Q1 Planning"
                                        ),
                                        maxLength=100,
                                        required=True,
                                    ),
                                    html.Small(
                                        (
                                            "A descriptive name for this query "
                                            "(1-100 characters)"
                                        ),
                                        className="text-muted",
                                    ),
                                ],
                                width=12,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # JQL Query
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "JQL Query",
                                        html_for="workspace-query-jql-input",
                                        className="fw-bold",
                                    ),
                                    dbc.Textarea(
                                        id="workspace-query-jql-input",
                                        placeholder=(
                                            "project = MYPROJECT "
                                            "AND sprint = currentSprint()"
                                        ),
                                        rows=4,
                                        required=True,
                                        style={
                                            "fontFamily": "monospace",
                                            "fontSize": "0.9rem",
                                        },
                                    ),
                                    html.Small(
                                        "JIRA Query Language (JQL) to filter issues",
                                        className="text-muted",
                                    ),
                                ],
                                width=12,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Feedback area
                    html.Div(
                        id="workspace-query-creation-feedback",
                        className="mt-2",
                    ),
                ],
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="workspace-cancel-create-query-button",
                        color="secondary",
                        outline=True,
                        className="me-2",
                    ),
                    dbc.Button(
                        [
                            html.I(className="fas fa-plus me-2"),
                            "Create Query",
                        ],
                        id="workspace-save-create-query-button",
                        color="primary",
                    ),
                ],
            ),
        ],
        id="workspace-create-query-modal",
        size="lg",
        is_open=False,
        backdrop="static",  # Prevent closing by clicking outside
        centered=True,
    )
