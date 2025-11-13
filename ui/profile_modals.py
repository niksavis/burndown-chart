"""
Profile creation and management modals.

Contains modals for creating, duplicating, and confirming deletion of profiles.
"""

from dash import html
import dash_bootstrap_components as dbc


def create_profile_creation_modal() -> dbc.Modal:
    """Create modal for profile creation.

    Returns:
        Bootstrap modal for creating new profiles
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Create New Profile")),
            dbc.ModalBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Profile Name", html_for="new-profile-name"
                                    ),
                                    dbc.Input(
                                        id="new-profile-name",
                                        type="text",
                                        placeholder="Enter profile name...",
                                        className="mb-3",
                                        maxLength=100,
                                    ),
                                    dbc.FormFeedback(
                                        "", id="profile-name-feedback", type="invalid"
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Description (Optional)",
                                        html_for="new-profile-description",
                                    ),
                                    dbc.Textarea(
                                        id="new-profile-description",
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
                    html.Div(
                        id="create-profile-error",
                        className="alert alert-danger d-none",
                        role="alert",
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="cancel-create-profile",
                        color="secondary",
                        className="me-2",
                        n_clicks=0,
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-plus me-2"), "Create Profile"],
                        id="confirm-create-profile",
                        color="primary",
                        n_clicks=0,
                    ),
                ]
            ),
        ],
        id="create-profile-modal",
        is_open=False,
        size="md",
        backdrop="static",
        keyboard=False,
        centered=True,
    )


def create_profile_duplication_modal() -> dbc.Modal:
    """Create modal for profile duplication.

    Returns:
        Bootstrap modal for duplicating existing profiles
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Duplicate Profile")),
            dbc.ModalBody(
                [
                    html.P(
                        id="duplicate-profile-info",
                        className="mb-3 text-muted",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "New Profile Name",
                                        html_for="duplicate-profile-name",
                                    ),
                                    dbc.Input(
                                        id="duplicate-profile-name",
                                        type="text",
                                        placeholder="Enter new profile name...",
                                        className="mb-3",
                                        maxLength=100,
                                    ),
                                    dbc.FormFeedback(
                                        "", id="duplicate-name-feedback", type="invalid"
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Description (Optional)",
                                        html_for="duplicate-profile-description",
                                    ),
                                    dbc.Textarea(
                                        id="duplicate-profile-description",
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
                    html.Div(
                        id="duplicate-profile-error",
                        className="alert alert-danger d-none",
                        role="alert",
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="cancel-duplicate-profile",
                        color="secondary",
                        className="me-2",
                        n_clicks=0,
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-copy me-2"), "Duplicate Profile"],
                        id="confirm-duplicate-profile",
                        color="primary",
                        n_clicks=0,
                    ),
                ]
            ),
        ],
        id="duplicate-profile-modal",
        is_open=False,
        size="md",
        backdrop="static",
        keyboard=False,
        centered=True,
    )


def create_profile_deletion_modal() -> dbc.Modal:
    """Create modal for profile deletion confirmation.

    Returns:
        Bootstrap modal for confirming profile deletion
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("⚠️ Delete Profile")),
            dbc.ModalBody(
                [
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
        keyboard=False,
        centered=True,
    )
