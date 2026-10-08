import dash_bootstrap_components as dbc
from dash import html


def create_unsaved_changes_modal() -> dbc.Modal:

    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(
                    [
                        html.I(
                            className="fas fa-exclamation-triangle text-warning me-2"
                        ),
                        "Unsaved Changes",
                    ]
                ),
                close_button=True,
            ),
            dbc.ModalBody(
                [
                    html.P(
                        [
                            "You have unsaved changes to ",
                            html.Strong(id="unsaved-changes-query-name"),
                            ".",
                        ],
                        className="mb-3",
                    ),
                    html.H6("Current Changes:", className="mb-2"),
                    html.Div(
                        id="unsaved-changes-jql-preview",
                        className=(
                            "p-3 mb-3 bg-light border rounded font-monospace small"
                        ),
                        style={
                            "maxHeight": "150px",
                            "overflowY": "auto",
                            "whiteSpace": "pre-wrap",
                            "wordBreak": "break-all",
                        },
                    ),
                    html.P(
                        "What would you like to do?",
                        className="mb-0 text-muted",
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Save Changes"],
                        id="unsaved-changes-save-button",
                        color="primary",
                        className="me-2",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-trash me-2"), "Discard"],
                        id="unsaved-changes-discard-button",
                        color="danger",
                        outline=True,
                        className="me-2",
                    ),
                    dbc.Button(
                        "Cancel",
                        id="unsaved-changes-cancel-button",
                        color="secondary",
                        outline=True,
                    ),
                ]
            ),
        ],
        id="unsaved-changes-modal",
        size="md",
        is_open=False,
        backdrop="static",
        centered=True,
    )
