"""
Example of how to use aria_utils.py to enhance accessibility in Dash components.
"""

from dash import Dash, html
import dash_bootstrap_components as dbc

# Import the aria utilities
from ui.aria_utils import (
    add_aria_label_to_icon_button,
    enhance_checkbox,
    create_screen_reader_only,
    enhance_data_table,
)

# Create a simple layout with accessible components
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Example 1: Add aria label and tooltip to an icon button
edit_button = html.Button(
    html.I(className="fas fa-edit"), id="edit-button", className="btn btn-link p-0"
)
# Make it accessible
accessible_edit = add_aria_label_to_icon_button(edit_button, "Edit item")

# Example 2: Add hidden text for screen readers
add_button = html.Button(
    [html.I(className="fas fa-plus me-1"), create_screen_reader_only("Add new item")],
    className="btn btn-primary",
)

# Example 3: Enhance a custom checkbox
custom_checkbox = html.Div(
    [html.Span(className="custom-checkbox"), "Remember me"], id="remember-checkbox"
)
accessible_checkbox = enhance_checkbox(custom_checkbox, "Remember login preferences")

# Example 4: Make a data table accessible
data_table = html.Table(
    [
        html.Thead([html.Tr([html.Th("Name"), html.Th("Value")])]),
        html.Tbody(
            [
                html.Tr([html.Td("Item 1"), html.Td("100")]),
                html.Tr([html.Td("Item 2"), html.Td("200")]),
            ]
        ),
    ],
    className="table table-striped",
)

accessible_table = enhance_data_table(
    data_table, {"caption": "Summary of items and their values"}
)

# Put everything together
app.layout = dbc.Container(
    [
        html.H1("Accessibility Examples"),
        html.Hr(),
        html.H2("Icon Button with ARIA Label"),
        html.Div(
            [
                accessible_edit,
                html.Span(
                    "Try hovering over the edit icon", className="ms-3 text-muted"
                ),
            ],
            className="mb-4",
        ),
        html.H2("Button with Screen Reader Text"),
        html.Div(
            [
                add_button,
                html.Span(
                    "This button has hidden text for screen readers",
                    className="ms-3 text-muted",
                ),
            ],
            className="mb-4",
        ),
        html.H2("Enhanced Checkbox"),
        html.Div(
            [
                accessible_checkbox,
                html.Span(
                    "This custom checkbox has proper ARIA attributes",
                    className="ms-3 text-muted",
                ),
            ],
            className="mb-4",
        ),
        html.H2("Accessible Data Table"),
        html.Div(
            [
                accessible_table,
                html.Span(
                    "This table has appropriate ARIA roles and a caption",
                    className="mt-3 d-block text-muted",
                ),
            ]
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
