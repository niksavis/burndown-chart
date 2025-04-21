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
from waitress import serve  # Import Waitress for production server

# Import UI components
from ui import serve_layout

# Import callback registration
from callbacks import register_all_callbacks

# Import server configuration
from configuration.server import get_server_config

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
    # Get server configuration
    server_config = get_server_config()

    if server_config["debug"]:
        print(
            f"Starting development server in DEBUG mode on {server_config['host']}:{server_config['port']}..."
        )
        app.run_server(
            debug=True, host=server_config["host"], port=server_config["port"]
        )
    else:
        print(
            f"Starting Waitress production server on {server_config['host']}:{server_config['port']}..."
        )
        serve(app.server, host=server_config["host"], port=server_config["port"])
