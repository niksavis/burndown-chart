"""
Project Burndown Forecast Application - Main Application Entry Point

Initializes the Dash application, imports and registers all callbacks,
and serves as the main entry point for running the server.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import logging

# Third-party library imports
import dash
import dash_bootstrap_components as dbc
from dash import DiskcacheManager
from waitress import serve
import diskcache

from callbacks import register_all_callbacks
from configuration.server import get_server_config
from configuration.logging_config import setup_logging, cleanup_old_logs

# Application imports
from ui import serve_layout
from data.migration import migrate_to_profiles
from data.auto_migrate_profiles import auto_migrate_on_startup
from data.profile_manager import (
    get_active_profile,
    switch_profile,
    list_profiles,
)
from data.query_manager import list_queries_for_profile, get_active_query_id

#######################################################################
# APPLICATION SETUP
#######################################################################

# Initialize logging first (before any other operations)
setup_logging(log_level="INFO")
cleanup_old_logs(max_age_days=30)

# Get logger for this module
logger = logging.getLogger(__name__)
logger.info("Starting Burndown Chart application")

# Run one-time migration to profiles structure (if needed)
# This protects existing users by automatically migrating their data
# to the new profiles/default/queries/main/ structure on first startup.
# Migration is idempotent - safe to run multiple times.
try:
    logger.info("Checking for migration requirements...")
    migration_performed = migrate_to_profiles()

    if migration_performed:
        logger.info(
            "Migration completed successfully - data moved to profiles/default/queries/main/"
        )
    else:
        logger.info("No migration needed - profiles structure already exists")

except Exception as e:
    # Log error but don't crash - allow app to continue
    # Users can manually migrate or continue in legacy mode
    logger.error(
        f"Migration failed: {e}. Application will continue in legacy mode. "
        "You can manually run migration or continue with root-level data files.",
        exc_info=True,
    )
    print(f"WARNING: Migration failed - {e}. See logs/app.log for details.")


# Run automatic migration from field_mappings to variable_mappings
# This upgrades existing profiles to use the new rule-based variable mapping system.
# Migration is idempotent - safe to run multiple times.
# Runs AFTER profile structure migration to ensure profiles exist.
try:
    logger.info("Running automatic variable mapping migration...")
    auto_migrate_on_startup()
    logger.info("Variable mapping migration completed successfully")
except Exception as e:
    # Log error but don't crash - profiles with field_mappings will still work
    # via backward compatibility in the metric calculators
    logger.error(
        f"Variable mapping migration failed: {e}. "
        "Profiles with field_mappings will continue to work via backward compatibility.",
        exc_info=True,
    )
    print(
        f"WARNING: Variable mapping migration failed - {e}. See logs/app.log for details."
    )


#######################################################################
# WORKSPACE VALIDATION
#######################################################################


def ensure_valid_workspace() -> None:
    """
    Validate application workspace on startup.

    This function checks the workspace state and ensures:
    1. If profiles exist, active profile is set
    2. If active profile exists, it has at least one query
    3. If queries exist, active query is set

    Unlike previous versions, this does NOT create a default profile.
    The app starts with a clean slate - users create their first profile via UI.

    Called during app initialization (after migration).
    """
    try:
        logger.info("[Workspace] Starting workspace validation...")

        # Step 1: Check if any profiles exist
        all_profiles = list_profiles()
        if not all_profiles:
            logger.info(
                "[Workspace] No profiles found - fresh installation. "
                "User will create first profile via UI."
            )
            logger.info("[Workspace] Workspace validation complete [OK]")
            return

        # Step 2: Ensure active profile is set (if profiles exist)
        active_profile = get_active_profile()
        if not active_profile:
            logger.warning(
                "[Workspace] Profiles exist but no active profile set. "
                f"Switching to first profile: {all_profiles[0]['name']}"
            )
            switch_profile(all_profiles[0]["id"])
            active_profile = get_active_profile()

        logger.info(
            f"[Workspace] Active profile: {active_profile.name if active_profile else 'None'}"
        )

        # Step 3: Ensure profile has at least one query
        if active_profile:
            queries = list_queries_for_profile(active_profile.id)
            if not queries:
                logger.info(
                    f"[Workspace] No queries in profile '{active_profile.name}' - "
                    "User will need to create a query before using JIRA integration"
                )
                # Note: We don't auto-create queries here because they require
                # JIRA configuration. The UI will enforce creating queries
                # after JIRA config is complete.

            # Step 4: Ensure active query is set (if queries exist)
            active_query_id = get_active_query_id()
            if queries and not active_query_id:
                logger.info("[Workspace] No active query, switching to first query")
                from data.profile_manager import switch_query

                switch_query(active_profile.id, queries[0]["id"])

        logger.info("[Workspace] Workspace validation complete [OK]")

    except Exception as e:
        # Log error but don't crash - allow app to continue
        logger.error(f"[Workspace] Validation failed: {e}", exc_info=True)
        print(
            f"WARNING: Workspace validation failed - {e}. See logs/app.log for details."
        )


# Validate workspace before app initialization
ensure_valid_workspace()

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
        "/assets/jql_editor_native.js",  # Native CodeMirror editors (no textarea transformation)
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
        logger.info(
            f"Starting development server in DEBUG mode on {server_config['host']}:{server_config['port']}"
        )
        print(
            f"Starting development server in DEBUG mode on {server_config['host']}:{server_config['port']}..."
        )
        app.run(debug=True, host=server_config["host"], port=server_config["port"])
    else:
        logger.info(
            f"Starting Waitress production server on {server_config['host']}:{server_config['port']}"
        )
        print(
            f"Starting Waitress production server on {server_config['host']}:{server_config['port']}..."
        )
        serve(app.server, host=server_config["host"], port=server_config["port"])
