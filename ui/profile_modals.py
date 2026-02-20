"""
Profile creation and management modals.

Contains unified modal for create/duplicate/rename and deletion confirmation modal.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_profile_form_modal() -> dbc.Modal:
    """Create unified modal for profile create/duplicate/rename operations.

    Modal behavior controlled by dcc.Store component with mode value:
    - "create": Empty fields, "Create Profile" button
    - "duplicate": Pre-filled with source profile, "Duplicate Profile" button
    - "rename": Pre-filled with current name, "Rename Profile" button

    Returns:
        Bootstrap modal with dynamic title and button based on mode
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(id="profile-form-modal-title")),
            dbc.ModalBody(
                [
                    # Hidden store to track operation mode
                    dcc.Store(id="profile-form-mode", data="create"),
                    # Hidden store to track source profile ID for duplicate/rename
                    dcc.Store(id="profile-form-source-id", data=None),
                    # Context info (visible for duplicate/rename only)
                    html.Div(
                        id="profile-form-context-info",
                        className="mb-3 text-muted",
                    ),
                    # Name input (shared across all modes)
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        id="profile-form-name-label",
                                        html_for="profile-form-name-input",
                                    ),
                                    dbc.Input(
                                        id="profile-form-name-input",
                                        type="text",
                                        placeholder="Enter profile name...",
                                        className="mb-3",
                                        maxLength=100,
                                        valid=False,
                                        invalid=False,
                                    ),
                                    dbc.FormFeedback(
                                        "Profile name is available",
                                        id="profile-form-name-feedback-valid",
                                        type="valid",
                                    ),
                                    dbc.FormFeedback(
                                        "",
                                        id="profile-form-name-feedback-invalid",
                                        type="invalid",
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                    # Description textarea (visible for create/duplicate only)
                    html.Div(
                        id="profile-form-description-container",
                        children=[
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Description (Optional)",
                                                html_for="profile-form-description-input",
                                            ),
                                            dbc.Textarea(
                                                id="profile-form-description-input",
                                                placeholder="Describe this profile's purpose...",
                                                rows=3,
                                                maxLength=500,
                                                className="mb-3",
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ]
                            ),
                        ],
                    ),
                    # Error alert (shared)
                    html.Div(
                        id="profile-form-error",
                        className="alert alert-danger d-none",
                        role="alert",
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="profile-form-cancel-btn",
                        color="secondary",
                        className="me-2",
                        n_clicks=0,
                    ),
                    dbc.Button(
                        id="profile-form-confirm-btn",
                        color="primary",
                        n_clicks=0,
                    ),
                ]
            ),
        ],
        id="profile-form-modal",
        is_open=False,
        size="md",
        backdrop="static",
        centered=True,
    )


def create_profile_deletion_modal() -> dbc.Modal:
    """Create modal for profile deletion confirmation.

    Returns:
        Bootstrap modal for confirming profile deletion
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("[!] Delete Profile")),
            dbc.ModalBody(
                [
                    # Store profile ID when modal opens to prevent wrong profile deletion
                    dcc.Store(id="delete-profile-target-id", data=None),
                    html.P(
                        id="delete-profile-warning",
                        className="mb-3",
                    ),
                    dbc.Alert(
                        [
                            html.Strong("Warning: "),
                            "This action cannot be undone. All queries, data, and settings for this profile will be permanently deleted.",
                        ],
                        color="danger",
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        'Type "DELETE" to confirm:',
                                        html_for="delete-confirmation-input",
                                    ),
                                    dbc.Input(
                                        id="delete-confirmation-input",
                                        type="text",
                                        placeholder="Type DELETE here...",
                                        className="mb-3",
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                    html.Div(
                        id="delete-profile-error",
                        className="alert alert-danger d-none",
                        role="alert",
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="cancel-delete-profile",
                        color="secondary",
                        className="me-2",
                        n_clicks=0,
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-trash me-2"), "Delete Profile"],
                        id="confirm-delete-profile",
                        color="danger",
                        disabled=True,  # Disabled until confirmation typed
                        n_clicks=0,
                    ),
                ]
            ),
        ],
        id="delete-profile-modal",
        is_open=False,
        size="md",
        backdrop="static",
        centered=True,
    )
