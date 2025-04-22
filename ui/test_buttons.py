"""
Test script for the button_utils module.

This script demonstrates and validates the usage of the new button_utils module.
To run this script, execute: python ui/test_buttons.py
"""

# Add the project root to the path so we can import the ui module properly
# IMPORTANT: This must be done before any other imports
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now we can import from ui modules
from dash import Dash, html
import dash_bootstrap_components as dbc

from ui.button_utils import (
    create_button,
    create_button_group,
    create_action_buttons,
    create_icon_button,
    create_close_button,
    create_menu_button,
    create_segmented_button_group,
    create_pill_button,
)

app = Dash(
    __name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME]
)

# Create examples of all button types
app.layout = html.Div(
    [
        html.H1("Button Utils Demo"),
        html.H2("Standard Buttons", className="mt-4"),
        html.Div(
            [
                create_button("Primary Button", id="primary-btn", className="me-2"),
                create_button(
                    "Secondary",
                    id="secondary-btn",
                    variant="secondary",
                    className="me-2",
                ),
                create_button(
                    "Success", id="success-btn", variant="success", className="me-2"
                ),
                create_button(
                    "Danger", id="danger-btn", variant="danger", className="me-2"
                ),
                create_button(
                    "Warning", id="warning-btn", variant="warning", className="me-2"
                ),
                create_button("Info", id="info-btn", variant="info", className="me-2"),
            ],
            className="mb-4",
        ),
        html.H2("Outline Buttons", className="mt-4"),
        html.Div(
            [
                create_button(
                    "Primary Outline",
                    id="primary-outline",
                    outline=True,
                    className="me-2",
                ),
                create_button(
                    "Secondary",
                    id="secondary-outline",
                    variant="secondary",
                    outline=True,
                    className="me-2",
                ),
                create_button(
                    "Success",
                    id="success-outline",
                    variant="success",
                    outline=True,
                    className="me-2",
                ),
                create_button(
                    "Danger",
                    id="danger-outline",
                    variant="danger",
                    outline=True,
                    className="me-2",
                ),
            ],
            className="mb-4",
        ),
        html.H2("Button Sizes", className="mt-4"),
        html.Div(
            [
                create_button("Large Button", id="lg-btn", size="lg", className="me-2"),
                create_button("Medium Button", id="md-btn", className="me-2"),
                create_button("Small Button", id="sm-btn", size="sm", className="me-2"),
            ],
            className="mb-4",
        ),
        html.H2("Icon Buttons", className="mt-4"),
        html.Div(
            [
                create_button(
                    "With Left Icon",
                    id="left-icon",
                    icon_class="fas fa-download",
                    className="me-2",
                ),
                create_button(
                    "With Right Icon",
                    id="right-icon",
                    icon_class="fas fa-arrow-right",
                    icon_position="right",
                    className="me-2",
                ),
                create_icon_button(
                    "fas fa-trash",
                    id="icon-only",
                    variant="danger",
                    className="me-2",
                    tooltip="Delete",
                ),
                create_icon_button(
                    "fas fa-edit", id="edit-icon", variant="info", className="me-2"
                ),
                create_icon_button(
                    "fas fa-save", id="save-icon", variant="success", className="me-2"
                ),
            ],
            className="mb-4",
        ),
        html.H2("Special Button Types", className="mt-4"),
        html.Div(
            [
                create_close_button(id="close-btn", tooltip="Close dialog"),
                create_menu_button(
                    id="menu-btn", tooltip="Open menu", className="ms-3"
                ),
            ],
            className="mb-4",
            style={
                "position": "relative",
                "height": "50px",
                "border": "1px dashed #ccc",
                "borderRadius": "4px",
            },
        ),
        html.H2("Button Groups", className="mt-4"),
        create_button_group(
            [
                create_button("Left", id="group-left-btn", className=""),
                create_button("Middle", id="group-middle-btn", className=""),
                create_button("Right", id="group-right-btn", className=""),
            ],
            className="mb-4",
        ),
        html.H2("Segmented Buttons", className="mt-4"),
        create_segmented_button_group(
            options=[
                {"label": "Day", "value": "day", "icon_class": "fas fa-calendar-day"},
                {
                    "label": "Week",
                    "value": "week",
                    "icon_class": "fas fa-calendar-week",
                },
                {
                    "label": "Month",
                    "value": "month",
                    "icon_class": "fas fa-calendar-alt",
                },
            ],
            id="time-period",
            value="week",
            variant="outline-primary",
            className="mb-4",
        ),
        html.H2("Pill Buttons", className="mt-4"),
        html.Div(
            [
                create_pill_button(
                    "Tag 1", id="pill-1", selected=True, className="me-2"
                ),
                create_pill_button("Tag 2", id="pill-2", className="me-2"),
                create_pill_button("Tag 3", id="pill-3", className="me-2"),
                create_pill_button(
                    icon_class="fas fa-plus",
                    text="Add Tag",
                    id="add-pill",
                    variant="outline-secondary",
                    className="me-2",
                ),
            ],
            className="mb-4",
        ),
        html.H2("Action Buttons", className="mt-4"),
        create_action_buttons(
            primary_action={"text": "Save", "id": "save-action", "icon": "fas fa-save"},
            secondary_action={"text": "Cancel", "id": "cancel-action"},
            tertiary_action={
                "text": "Delete",
                "id": "delete-action",
                "icon": "fas fa-trash-alt",
            },
            alignment="right",
        ),
        html.H2("Disabled Buttons", className="mt-4"),
        html.Div(
            [
                create_button(
                    "Disabled", id="disabled-btn", disabled=True, className="me-2"
                ),
                create_button(
                    "Disabled Icon",
                    id="disabled-icon",
                    icon_class="fas fa-ban",
                    disabled=True,
                    className="me-2",
                ),
                create_icon_button(
                    "fas fa-trash",
                    id="disabled-icon-only",
                    disabled=True,
                    className="me-2",
                ),
            ],
            className="mb-4",
        ),
        html.H2("Tooltips", className="mt-4"),
        html.Div(
            [
                create_button(
                    "With Tooltip",
                    id="tooltip-btn",
                    tooltip="This is a helpful tooltip",
                    className="me-2",
                ),
                create_icon_button(
                    "fas fa-info-circle",
                    id="info-tooltip",
                    tooltip="Information",
                    className="me-2",
                ),
            ],
            className="mb-4",
        ),
    ],
    style={"maxWidth": "800px", "margin": "0 auto", "padding": "20px"},
)


if __name__ == "__main__":
    print("Starting Button Utils Demo server on http://127.0.0.1:8050/")
    app.run_server(debug=True)
