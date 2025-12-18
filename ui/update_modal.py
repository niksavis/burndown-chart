"""
Modal component for application auto-update functionality.

Shows update progress, status messages, and handles user interaction
during the git pull update process.
"""

import dash_bootstrap_components as dbc
from dash import html


def create_update_modal() -> dbc.Modal:
    """
    Create modal dialog for application update workflow.

    Shows different states:
    - Checking: Verifying git status and requirements
    - Stashing: Saving uncommitted changes
    - Pulling: Fetching and applying updates
    - Success: Update complete, prompt to restart
    - Error: Update failed with details

    Returns:
        dbc.Modal component with update UI
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(
                html.H5(
                    "Application Update",
                    className="mb-0",
                ),
            ),
            dbc.ModalBody(
                [
                    # Progress section (shown during update)
                    html.Div(
                        [
                            dbc.Spinner(
                                size="lg",
                                color="primary",
                                spinner_class_name="mb-3",
                            ),
                            html.P(
                                id="update-status-text",
                                className="text-center text-muted mb-0",
                            ),
                        ],
                        id="update-progress-section",
                        className="text-center py-4",
                        style={"display": "none"},
                    ),
                    # Result section (shown after completion)
                    html.Div(
                        [
                            html.Div(
                                id="update-result-icon",
                                className="text-center mb-3",
                            ),
                            html.P(
                                id="update-result-message",
                                className="mb-2",
                            ),
                            html.Div(
                                id="update-commit-details",
                                className="mt-3",
                            ),
                        ],
                        id="update-result-section",
                        className="py-3",
                        style={"display": "none"},
                    ),
                ],
            ),
            dbc.ModalFooter(
                [
                    # Cancel button (shown during pre-update)
                    dbc.Button(
                        "Cancel",
                        id="update-cancel-btn",
                        color="secondary",
                        className="me-2",
                    ),
                    # Confirm button (shown before update starts)
                    dbc.Button(
                        "Update Now",
                        id="update-confirm-btn",
                        color="primary",
                    ),
                    # Close button (shown after completion)
                    dbc.Button(
                        "Close",
                        id="update-close-btn",
                        color="secondary",
                        style={"display": "none"},
                    ),
                ],
            ),
        ],
        id="update-modal",
        is_open=False,
        backdrop="static",  # Prevent closing during update
        keyboard=False,  # Prevent ESC key closing during update
        centered=True,
        size="lg",
    )
