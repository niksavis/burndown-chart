import dash_bootstrap_components as dbc
from dash import html

from ui.icon_utils import create_icon, create_icon_text


def create_pert_table_header():
    return html.Thead(
        html.Tr(
            [
                html.Th("Type", style={"width": "25%"}),
                html.Th(
                    create_icon_text(
                        "success", "Optimistic", size="sm", color="#28a745"
                    )
                ),
                html.Th(
                    create_icon_text(
                        "forecast", "Most Likely", size="sm", color="#0d6efd"
                    )
                ),
                html.Th(
                    create_icon_text(
                        "warning", "Pessimistic", size="sm", color="#dc3545"
                    )
                ),
                html.Th(
                    create_icon_text("info", "Expected", size="sm", color="#17a2b8")
                ),
            ]
        )
    )


def create_help_button_with_tooltip(
    id_prefix, tooltip_text="Click for more information"
):

    button_id = f"{id_prefix}-help-button"

    help_button = dbc.Button(
        create_icon("help", size="sm"),
        id=button_id,
        color="link",
        className="text-muted p-0 ms-1",
        style={"boxShadow": "none"},
    )

    help_tooltip = dbc.Tooltip(
        tooltip_text,
        target=button_id,
        placement="top",
        trigger="click",
        autohide=True,
    )

    return [help_button, help_tooltip]


def create_export_button_group(id_prefix):

    export_img_btn = dbc.Button(
        create_icon_text("export", "Export as PNG", size="sm", spacing="0.5rem"),
        id=f"{id_prefix}-export-img-btn",
        color="outline-primary",
        className="me-2",
    )

    export_img_tooltip = dbc.Tooltip(
        "Export the chart as a PNG image",
        target=f"{id_prefix}-export-img-btn",
        placement="top",
        trigger="click",
        autohide=True,
    )

    export_data_btn = dbc.Button(
        create_icon_text("download", "Export Data", size="sm", spacing="0.5rem"),
        id=f"{id_prefix}-export-data-btn",
        color="outline-secondary",
    )

    export_data_tooltip = dbc.Tooltip(
        "Export the data as JSON",
        target=f"{id_prefix}-export-data-btn",
        placement="top",
        trigger="click",
        autohide=True,
    )

    export_container = html.Div(
        [export_img_btn, export_img_tooltip, export_data_btn, export_data_tooltip],
        className="d-flex align-items-center justify-content-end mt-2",
    )

    return export_container
