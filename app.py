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
import os
import socket
import threading
import time
import webbrowser

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
from data.profile_manager import (
    get_active_profile,
    switch_profile,
    list_profiles,
)
from data.query_manager import list_queries_for_profile, get_active_query_id
from data.installation_context import get_installation_context
from utils.version_checker import check_for_updates

#######################################################################
# APPLICATION SETUP
#######################################################################

# Detect installation context (frozen/source, paths)
installation_context = get_installation_context()
logger_init = logging.getLogger(__name__)
logger_init.info(f"Installation context: {installation_context}")

# Initialize logging first (before any other operations)
setup_logging(log_dir=str(installation_context.logs_path), log_level="INFO")
cleanup_old_logs(log_dir=str(installation_context.logs_path), max_age_days=30)

# Get logger for this module
logger = logging.getLogger(__name__)
logger.info("Starting Burndown Chart application")

#######################################################################
# DATABASE MIGRATION
#######################################################################

# Run JSON-to-SQLite migration if needed (T029)
# This must happen before any workspace operations
try:
    from data.migration.migrator import run_migration_if_needed

    logger.info("Checking if database migration needed...")
    migration_success = run_migration_if_needed()

    if migration_success:
        logger.info("Database ready (migration complete or not needed)")
    else:
        logger.error("Database migration failed - app may not function correctly")
        print("ERROR: Database migration failed. Check logs/app.log for details.")
        # Continue anyway - app will try to use existing data

except Exception as e:
    logger.error(f"Migration check failed: {e}", exc_info=True)
    print(f"WARNING: Migration check failed - {e}. App will attempt to continue.")

#######################################################################
# VERSION CHECK
#######################################################################

# Check for updates on startup (once, not on page refresh)
# Store result globally for footer to access
VERSION_CHECK_RESULT = check_for_updates()

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
        # SECURITY: Font Awesome 6.x from cdnjs (no tracking, no checkout popup injection)
        # Using free version CSS-only (no kit system) to prevent checkout code injection
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/fontawesome.min.css",  # Font Awesome core (CSS only)
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/solid.min.css",  # Solid icons
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
        "/assets/conflict_resolution_clientside.js",  # Conflict resolution clientside callbacks (import/export)
    ],
    suppress_callback_exceptions=True,  # Suppress errors for components in dynamic layouts (Settings flyout, modals)
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
        # SECURITY: Content Security Policy to prevent unauthorized script injection
        # Prevents Font Awesome and other CDNs from injecting tracking/checkout scripts
        {
            "http-equiv": "Content-Security-Policy",
            "content": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com data:; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://cdn.jsdelivr.net"
            ),
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


def wait_for_server_ready(host: str, port: int, timeout: float = 3.0) -> bool:
    """
    Wait for server to be ready to accept connections.

    Args:
        host: Server host address
        port: Server port number
        timeout: Maximum time to wait in seconds

    Returns:
        True if server is ready, False if timeout occurred
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except (socket.error, OSError):
            time.sleep(0.1)
    return False


# Run the app
if __name__ == "__main__":
    # Clean up stale task progress from previous crashed/killed processes
    # CRITICAL: This must run BEFORE Dash app starts accepting requests
    try:
        from data.task_progress import TaskProgress
        import time

        active_task = TaskProgress.get_active_task()
        if active_task and active_task.get("status") == "in_progress":
            task_id = active_task.get("task_id", "unknown")
            phase = active_task.get("phase", "unknown")
            logger.warning(
                f"[Startup] Found stale in-progress task '{task_id}' (phase={phase}) from previous session - marking as failed"
            )

            # Add app restart marker so recovery callback knows not to trigger actions
            import json
            from pathlib import Path

            restart_marker = Path("task_progress.json.restart")
            restart_marker.write_text(json.dumps({"restart_time": time.time()}))

            TaskProgress.fail_task(
                task_id,
                f"Operation interrupted (app restarted during {phase} phase). Click Update Data to restart.",
            )

            # Keep marker for 5 seconds so page load callbacks can detect it
            time.sleep(0.1)  # Small delay to ensure file is written
    except Exception as e:
        logger.error(f"[Startup] Failed to clean up stale tasks: {e}")

    # Get server configuration
    server_config = get_server_config()

    # Determine if browser should auto-launch
    # Only auto-launch when running as frozen executable (not in dev mode)
    # and when BURNDOWN_NO_BROWSER environment variable is not set
    should_launch_browser = (
        installation_context.is_frozen
        and not server_config["debug"]
        and os.environ.get("BURNDOWN_NO_BROWSER", "0") != "1"
    )

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
        url = f"http://{server_config['host']}:{server_config['port']}"
        print(
            f"Starting Waitress production server on {server_config['host']}:{server_config['port']}..."
        )
        print("\nOpen your browser at:", flush=True)
        print(f"  {url}", flush=True)
        print("", flush=True)  # Empty line for better visibility

        # Launch browser in separate thread if running as executable (unless disabled by env var)
        if should_launch_browser:

            def launch_browser():
                """Wait for server to be ready, then launch browser."""
                logger.info("Waiting for server to be ready...")
                if wait_for_server_ready(
                    server_config["host"], server_config["port"], timeout=3.0
                ):
                    logger.info(f"Server ready, launching browser at {url}")
                    print("Server ready! Launching browser...", flush=True)
                    try:
                        webbrowser.open(url)
                    except Exception as e:
                        logger.warning(f"Failed to auto-launch browser: {e}")
                        print(f"Could not auto-launch browser: {e}", flush=True)
                else:
                    logger.warning(
                        "Server readiness check timed out after 3s, browser not launched"
                    )
                    print(
                        "Server startup took longer than expected. Please open browser manually.",
                        flush=True,
                    )

            browser_thread = threading.Thread(target=launch_browser, daemon=True)
            browser_thread.start()

        serve(app.server, host=server_config["host"], port=server_config["port"])
