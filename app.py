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
import signal
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

# Third-party library imports
import dash
import dash_bootstrap_components as dbc
from dash import DiskcacheManager
import atexit
import diskcache

# Application imports (after third-party, before usage)
from callbacks import register_all_callbacks
from configuration.server import get_server_config
from configuration.logging_config import setup_logging, cleanup_old_logs
from ui import serve_layout
from data.profile_manager import (
    get_active_profile,
    switch_profile,
    list_profiles,
)
from data.query_manager import list_queries_for_profile, get_active_query_id
from data.installation_context import get_installation_context
from data.update_manager import check_for_updates, UpdateProgress, UpdateState
from utils.license_extractor import extract_license_on_first_run

# Global reference to server for clean shutdown
_server = None


def shutdown_server():
    """Shutdown the Waitress server gracefully."""
    if _server:
        logger.info("Shutting down Waitress server...")
        try:
            _server.close()
        except Exception as e:
            logger.warning(f"Error closing server: {e}")


#######################################################################
# APPLICATION SETUP
#######################################################################

# Detect installation context (frozen/source, paths)
installation_context = get_installation_context()
logger_init = logging.getLogger(__name__)
logger_init.info(f"Installation context: {installation_context}")

# Extract LICENSE.txt on first run (frozen executable only)
extract_license_on_first_run()

# Initialize logging first (before any other operations)
setup_logging(log_dir=str(installation_context.logs_path), log_level="INFO")
cleanup_old_logs(log_dir=str(installation_context.logs_path), max_age_days=30)

# Get logger for this module
logger = logging.getLogger(__name__)
logger.info("Starting Burndown Chart application")

#######################################################################
# TEMP FILE CLEANUP
#######################################################################


def cleanup_orphaned_temp_updaters() -> None:
    """Remove orphaned temp updater files from previous sessions.

    Temp updater copies (BurndownChartUpdater-temp-*.exe) are created during
    updates but cannot delete themselves while running. This function cleans
    up any leftover files from previous update sessions.

    Only deletes files older than 1 hour to avoid interfering with any
    running update process.
    """
    import tempfile

    try:
        temp_dir = Path(tempfile.gettempdir())
        cutoff_time = time.time() - (60 * 60)  # 1 hour ago

        # Cleanup temp updater executables
        cleaned_count = 0
        for temp_updater in temp_dir.glob("BurndownChartUpdater-temp-*.exe"):
            try:
                # Only delete if older than 1 hour (safety margin)
                if temp_updater.stat().st_mtime < cutoff_time:
                    temp_updater.unlink()
                    cleaned_count += 1
                    logger.info(f"Cleaned up orphaned updater: {temp_updater.name}")
            except (PermissionError, OSError) as e:
                # File might be in use, skip silently
                logger.debug(f"Could not delete {temp_updater.name}: {e}")

        # Cleanup orphaned extraction directories (burndown_chart_update_*)
        for extract_dir in temp_dir.glob("burndown_chart_update_*"):
            if extract_dir.is_dir():
                try:
                    # Only delete if older than 1 hour (safety margin)
                    if extract_dir.stat().st_mtime < cutoff_time:
                        import shutil

                        shutil.rmtree(extract_dir)
                        cleaned_count += 1
                        logger.info(
                            f"Cleaned up orphaned extraction dir: {extract_dir.name}"
                        )
                except (PermissionError, OSError) as e:
                    # Directory might be in use, skip silently
                    logger.debug(f"Could not delete {extract_dir.name}: {e}")

        if cleaned_count > 0:
            logger.info(
                f"Cleanup complete: removed {cleaned_count} orphaned file(s)/folder(s)"
            )
        else:
            logger.debug("No orphaned temp files found")

    except Exception as e:
        # Don't let cleanup failures block app startup
        logger.warning(f"Temp file cleanup failed: {e}")


# Clean up orphaned temp updaters from previous sessions
cleanup_orphaned_temp_updaters()

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

# Global variable to store update check result
# Accessed by UI components to show update notifications
VERSION_CHECK_RESULT: Optional[UpdateProgress] = None


def _restore_pending_update() -> None:
    """Restore pending update state from database.

    If app was closed or crashed after downloading an update but before
    installation, this restores the download state. Handles graceful
    fallback if temp files were deleted by Windows.
    """
    global VERSION_CHECK_RESULT
    try:
        from data.update_manager import _restore_download_state

        restored_progress = _restore_download_state()
        if restored_progress:
            VERSION_CHECK_RESULT = restored_progress
            logger.info(
                "Restored pending update from previous session",
                extra={
                    "operation": "restore_pending_update",
                    "state": restored_progress.state.value,
                    "version": restored_progress.available_version,
                },
            )
    except Exception as e:
        logger.warning(f"Failed to restore pending update: {e}")


# Restore pending update state (if any)
_restore_pending_update()


def _check_for_updates_background() -> None:
    """Background thread function to check for updates.

    Runs update check without blocking app startup. Result is stored
    in global VERSION_CHECK_RESULT for UI components to display.

    This is a daemon thread, so it will be terminated when the app exits.
    """
    global VERSION_CHECK_RESULT

    # Skip check if we already have a pending update
    if VERSION_CHECK_RESULT and VERSION_CHECK_RESULT.state in (
        UpdateState.READY,
        UpdateState.AVAILABLE,
    ):
        logger.info("Skipping update check - pending update already available")
        return

    try:
        logger.info("Starting background update check")
        VERSION_CHECK_RESULT = check_for_updates()
        logger.info(
            "Update check complete",
            extra={
                "operation": "update_check",
                "state": VERSION_CHECK_RESULT.state.value,
                "current_version": VERSION_CHECK_RESULT.current_version,
                "available_version": VERSION_CHECK_RESULT.available_version,
            },
        )
    except Exception as e:
        logger.error(
            f"Update check failed: {e}",
            exc_info=True,
            extra={"operation": "update_check"},
        )
        # Set error state so UI knows check failed
        VERSION_CHECK_RESULT = UpdateProgress(
            state=UpdateState.ERROR,
            current_version="unknown",
            error_message=str(e),
        )


# Launch update check in background thread (daemon=True)
# App UI will appear immediately without waiting for check to complete
update_check_thread = threading.Thread(
    target=_check_for_updates_background,
    daemon=True,
    name="UpdateCheckThread",
)
update_check_thread.start()
logger.info("Update check thread started")

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
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/brands.min.css",  # Brand icons (GitHub, etc.)
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


def setup_graceful_shutdown():
    """
    Setup graceful shutdown handlers for SIGINT (Ctrl+C) and SIGTERM.

    This ensures clean termination when the executable is closed.
    """

    def shutdown_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        sig_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        logger.info(f"Received {sig_name}, shutting down gracefully...")
        print("\nShutting down server...", flush=True)
        sys.exit(0)

    # Register handlers for both SIGINT (Ctrl+C) and SIGTERM (process termination)
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)


# Run the app
if __name__ == "__main__":
    # Setup graceful shutdown handlers
    setup_graceful_shutdown()

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

    # Initialize system tray icon (frozen executable only)
    if installation_context.is_frozen:
        try:
            import pystray
            from PIL import Image

            def on_open(icon, item):
                """Open the application in the default browser."""
                url = f"http://{server_config['host']}:{server_config['port']}"
                try:
                    webbrowser.open(url, new=2, autoraise=True)
                    logger.info("Browser opened from tray icon")
                except Exception as e:
                    logger.error(f"Failed to open browser from tray: {e}")

            def on_quit(icon, item):
                """Quit the application gracefully."""
                logger.info("Quit requested from tray icon")
                # Stop the tray icon first
                icon.stop()
                # Shutdown the Waitress server
                shutdown_server()
                # Exit the application
                os._exit(0)  # Force exit all threads

            # Load icon file from PyInstaller bundle (_MEIPASS)
            # PyInstaller unpacks bundled files to _MEIPASS at runtime
            meipass = Path(sys._MEIPASS)  # type: ignore[attr-defined]
            icon_path = meipass / "assets" / "icon.ico"

            if icon_path.exists():
                tray_icon = pystray.Icon(
                    "burndown-chart",
                    Image.open(str(icon_path)),
                    f"Burndown Chart - Running on http://{server_config['host']}:{server_config['port']}",
                    menu=pystray.Menu(
                        pystray.MenuItem("Open in Browser", on_open),
                        pystray.MenuItem("Quit", on_quit),
                    ),
                )

                # Run tray icon in separate daemon thread so it doesn't block server
                tray_thread = threading.Thread(
                    target=tray_icon.run, daemon=True, name="TrayIconThread"
                )
                tray_thread.start()
                logger.info(f"System tray icon initialized from {icon_path}")
            else:
                logger.warning(
                    f"Icon file not found at {icon_path}, skipping tray icon"
                )
        except ImportError:
            logger.warning(
                "pystray not available, skipping tray icon (install with: pip install pystray)"
            )
        except Exception as e:
            logger.error(f"Failed to initialize tray icon: {e}", exc_info=True)

    # Determine if browser should auto-launch
    # Only auto-launch when running as frozen executable (not in dev mode)
    # and when BURNDOWN_NO_BROWSER environment variable is not set
    # Skip auto-launch if post_update_relaunch flag is set (updater will reload existing tabs)
    should_launch_browser = (
        installation_context.is_frozen
        and not server_config["debug"]
        and os.environ.get("BURNDOWN_NO_BROWSER", "0") != "1"
    )

    # Check database flag for post-update relaunch
    if should_launch_browser:
        try:
            from data.persistence.factory import get_backend

            backend = get_backend()
            post_update_flag = backend.get_app_state("post_update_relaunch")

            if post_update_flag:
                logger.info(
                    "Skipping browser auto-launch after update (update_reconnect.js will reload existing tabs)"
                )
                print(
                    "Detected post-update restart - reconnecting existing browser tabs...",
                    flush=True,
                )
                should_launch_browser = False

                # Clear flag after reading (one-time use)
                backend.set_app_state("post_update_relaunch", "")
                logger.debug("Cleared post_update_relaunch flag")
        except Exception as e:
            logger.warning(
                f"Failed to check post_update_relaunch flag: {e} - proceeding with normal launch"
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
                        # Try to reuse existing tab by opening with new=2 (new tab if possible)
                        # This still may open a new tab but at least tries to reuse window
                        webbrowser.open(url, new=2, autoraise=True)
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

        # Start server in a way that allows graceful shutdown
        from waitress.server import create_server

        _server = create_server(
            app.server,
            host=server_config["host"],
            port=server_config["port"],
            threads=4,
        )

        # Register shutdown handler
        atexit.register(shutdown_server)

        logger.info("Waitress server starting...")
        _server.run()
