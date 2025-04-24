from dash import Dash, html, callback, Input, Output
import dash_bootstrap_components as dbc
from ui.mobile_utils import create_mobile_checker, create_clientside_callback

# Initialize the app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Create your main application layout
app.layout = html.Div(
    [
        html.H1("My Dashboard"),
        # Your regular application content
        html.Div(
            [
                # ...your dashboard components...
            ]
        ),
        # Add the mobile checker - typically at the bottom of development layouts
        create_mobile_checker(id_prefix="my-mobile-checker"),
    ]
)

# Set up the clientside callback for the mobile checker
create_clientside_callback(app, id_prefix="my-mobile-checker")


# Add callback for toggling the mobile checker panel
@callback(
    Output("my-mobile-checker-collapse", "is_open"),
    Input("my-mobile-checker-toggle", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_mobile_checker(n_clicks):
    return True if n_clicks and n_clicks % 2 == 1 else False


# Add callback for the text truncation preview
@callback(
    Output("my-mobile-checker-truncate-preview", "children"),
    Input("my-mobile-checker-truncate-input", "value"),
)
def update_truncation_preview(text):
    return text or ""


if __name__ == "__main__":
    app.run_server(debug=True)
