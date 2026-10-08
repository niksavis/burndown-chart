import dash_bootstrap_components as dbc
from dash import html


def create_confirmation_modal(
    modal_id: str,
    title: str,
    warning_message: str,
    confirmation_type: str = "DELETE",
    confirmation_placeholder: str | None = None,
    danger_alert: bool = True,
    cancel_button_id: str = "",
    confirm_button_id: str = "",
    confirmation_input_id: str = "",
    item_name_id: str = "",
    icon: str = "fas fa-trash",
    confirm_button_text: str = "Delete",
    confirm_button_color: str = "danger",
) -> dbc.Modal:

    if confirmation_type == "DELETE":
        confirmation_label = 'Type "DELETE" to confirm:'
        confirmation_default_placeholder = "Type DELETE here..."
    else:
        confirmation_label = f"Type the {confirmation_type} to confirm:"
        confirmation_default_placeholder = f"Type {confirmation_type} here..."

    placeholder = confirmation_placeholder or confirmation_default_placeholder

    item_display = []
    if item_name_id:
        item_display = [
            html.Div(
                [
                    html.Strong(f"{confirmation_type.title()}: ", className="me-2"),
                    html.Span(id=item_name_id, className="text-primary"),
                ],
                className="p-3 bg-light border rounded mb-3",
            )
        ]

    alert_content = []
    if danger_alert:
        alert_content = [
            dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "This action cannot be undone.",
                ],
                color="danger" if confirm_button_color == "danger" else "warning",
                className="mb-3",
            )
        ]

    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle([html.I(className=f"{icon} me-2"), title])),
            dbc.ModalBody(
                [
                    html.P(warning_message, className="mb-3"),
                    *item_display,
                    *alert_content,
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        confirmation_label,
                                        html_for=confirmation_input_id,
                                    ),
                                    dbc.Input(
                                        id=confirmation_input_id,
                                        type="text",
                                        placeholder=placeholder,
                                        className="mb-3",
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                    html.Div(
                        id=f"{modal_id}-error",
                        className="alert alert-danger d-none",
                        role="alert",
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id=cancel_button_id,
                        color="secondary",
                        className="me-2",
                        n_clicks=0,
                    ),
                    dbc.Button(
                        [html.I(className=f"{icon} me-2"), confirm_button_text],
                        id=confirm_button_id,
                        color=confirm_button_color,
                        disabled=True,
                        n_clicks=0,
                    ),
                ]
            ),
        ],
        id=modal_id,
        is_open=False,
        size="md",
        backdrop="static",
        centered=True,
    )


def create_profile_deletion_modal() -> dbc.Modal:

    return create_confirmation_modal(
        modal_id="delete-profile-modal",
        title="Delete Profile",
        warning_message=(
            "This profile and all its queries, data, and settings will be "
            "permanently deleted."
        ),
        confirmation_type="DELETE",
        cancel_button_id="cancel-delete-profile",
        confirm_button_id="confirm-delete-profile",
        confirmation_input_id="delete-confirmation-input",
        icon="fas fa-trash",
        confirm_button_text="Delete Profile",
    )


def create_query_deletion_modal() -> dbc.Modal:

    return create_confirmation_modal(
        modal_id="delete-jql-query-modal",
        title="Delete JQL Query",
        warning_message=(
            "Are you sure you want to delete this saved query? "
            "This action cannot be undone."
        ),
        confirmation_type="DELETE",
        cancel_button_id="cancel-delete-query-button",
        confirm_button_id="confirm-delete-query-button",
        confirmation_input_id="delete-query-confirmation-input",
        icon="fas fa-trash",
        confirm_button_text="Delete Query",
    )
