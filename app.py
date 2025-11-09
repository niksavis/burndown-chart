"""
Project Burndown Forecast Application - Main Application Entry Point

Initializes the Dash application, imports and registers all callbacks,
and serves as the main entry point for running the server.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports

# Third-party library imports
import dash
import dash_bootstrap_components as dbc
from dash import DiskcacheManager
from waitress import serve
import diskcache

from callbacks import register_all_callbacks
from configuration.server import get_server_config

# Application imports
from ui import serve_layout

#######################################################################
# APPLICATION SETUP
#######################################################################

# Configure background callback manager for long-running tasks
cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

# Initialize the Dash app with PWA support
app = dash.Dash(
    __name__,
    title="Burndown Chart Generator",  # Custom browser tab title
    assets_folder="assets",  # Explicitly set assets folder
    background_callback_manager=background_callback_manager,  # Enable background callbacks
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://use.fontawesome.com/releases/v5.15.4/css/all.css",  # Font Awesome for icons
        "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css",  # CodeMirror base styles
        "/assets/custom.css",  # Our custom CSS for standardized styling (includes CodeMirror theme overrides)
        "/assets/help_system.css",  # Help system CSS for progressive disclosure
    ],
    external_scripts=[
        # CodeMirror 5 (legacy) - Better script tag support than CM6
        # CM6 requires ES modules which don't work well with Dash script loading
        # CM5 provides adequate syntax highlighting for our use case
        "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/sql/sql.min.js",  # Base for query language
        "/assets/jql_language_mode.js",  # JQL tokenizer for syntax highlighting
        "/assets/jql_editor_init.js",  # Editor initialization - progressive enhancement
        "/assets/mobile_navigation.js",  # Mobile navigation JavaScript for swipe gestures
    ],
    suppress_callback_exceptions=True,  # Suppress exceptions for components created by callbacks
    meta_tags=[
        # PWA Meta Tags for Mobile-First Design
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes",
        },
        {"name": "theme-color", "content": "#0d6efd"},
        {"name": "apple-mobile-web-app-capable", "content": "yes"},
        {"name": "apple-mobile-web-app-status-bar-style", "content": "default"},
        {"name": "apple-mobile-web-app-title", "content": "Burndown Chart"},
        {"name": "mobile-web-app-capable", "content": "yes"},
        # Performance and SEO
        {
            "name": "description",
            "content": "Modern mobile-first agile project forecasting with JIRA integration",
        },
        {
            "name": "keywords",
            "content": "burndown chart, agile, project management, JIRA, forecasting",
        },
        {"property": "og:title", "content": "Burndown Chart Generator"},
        {"property": "og:type", "content": "website"},
        {
            "property": "og:description",
            "content": "Modern mobile-first agile project forecasting with JIRA integration",
        },
    ],
)

# Add PWA manifest link to app index
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <!-- Custom Favicon -->
        <link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
        <link rel="shortcut icon" href="/assets/favicon.svg">
        {%css%}
        <!-- PWA Manifest -->
        <link rel="manifest" href="/assets/manifest.json">
        <!-- Apple Touch Icons -->
        <link rel="apple-touch-icon" href="/assets/icon-192.svg">
        <link rel="apple-touch-icon" sizes="512x512" href="/assets/icon-512.svg">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

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
        app.run(debug=True, host=server_config["host"], port=server_config["port"])
    else:
        print(
            f"Starting Waitress production server on {server_config['host']}:{server_config['port']}..."
        )
        serve(app.server, host=server_config["host"], port=server_config["port"])
