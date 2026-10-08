import dash_bootstrap_components as dbc
from dash import html

from ui.button_utils import create_button
from ui.icon_utils import create_icon_text


def create_export_buttons(chart_id=None, statistics_data=None):

    buttons = []

    if chart_id:
        png_button = create_button(
            children=[html.I(className="fas fa-file-image me-2"), "Export Image"],
            id=f"{chart_id}-png-button",
            variant="secondary",
            size="sm",
            outline=True,
            tooltip="Export chart as image",
            className="me-2",
        )
        buttons.append(png_button)

    return html.Div(
        buttons,
        className="d-flex justify-content-end mb-3",
    )


def create_error_alert(
    message="An unexpected error occurred. Please try again later.",
    title="Error",
    error_details=None,
):

    children = [
        html.H4(
            create_icon_text("error", title, size="md"),
            className="alert-heading d-flex align-items-center",
        ),
        html.P(message),
    ]
    if error_details:
        children.extend(
            [
                html.Hr(),
                html.P(f"Details: {error_details}", className="mb-0 small text-muted"),
            ]
        )

    return dbc.Alert(
        children,
        color="danger",
        dismissable=True,
        className="error-alert",
    )
