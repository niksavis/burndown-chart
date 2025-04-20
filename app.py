"""
Project Burndown Forecast Application - Main Application Entry Point

Initializes the Dash application, imports and registers all callbacks,
and serves as the main entry point for running the server.
"""

#######################################################################
# IMPORTS
#######################################################################
import dash
import dash_bootstrap_components as dbc

# Import UI components
from ui import serve_layout

# Import callback registration
from callbacks import register_all_callbacks

#######################################################################
# APPLICATION SETUP
#######################################################################

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css",  # Font Awesome for icons
        "/assets/custom.css",  # Our custom CSS for standardized styling
    ],
    suppress_callback_exceptions=True,  # Suppress exceptions for components created by callbacks
)

# Set the layout function as the app's layout
app.layout = serve_layout

#######################################################################
# REGISTER CALLBACKS
#######################################################################

# Register all callbacks from the modular callback system
register_all_callbacks(app)

#######################################################################
# MAIN
#######################################################################

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
