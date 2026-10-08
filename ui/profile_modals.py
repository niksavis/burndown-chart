import dash_bootstrap_components as dbc
from dash import dcc, html


def create_profile_form_modal() -> dbc.Modal:

    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(id="profile-form-modal-title")),
            dbc.ModalBody(
                [
                    dcc.Store(id="profile-form-mode", data="create"),
                    dcc.Store(id="profile-form-source-id", data=None),
                    html.Div(
                        id="profile-form-context-info",
                        className="mb-3 text-muted",
                    ),
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
                                                placeholder=(
                                                    "Describe this profile's purpose..."
                                                ),
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

    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("[!] Delete Profile")),
            dbc.ModalBody(
                [
                    dcc.Store(id="delete-profile-target-id", data=None),
                    html.P(
                        id="delete-profile-warning",
                        className="mb-3",
                    ),
                    dbc.Alert(
                        [
                            html.Strong("Warning: "),
                            (
                                "This action cannot be undone. All queries, "
                                "data, and settings for this profile will be "
                                "permanently deleted."
                            ),
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
                        disabled=True,
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
