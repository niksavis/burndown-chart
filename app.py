"""
Project Burndown Forecast Application - Main Application Entry Point

Initializes the Dash application, imports and registers all callbacks,
and serves as the main entry point for running the server.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import atexit
import logging
import os
import signal
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Third-party library imports
import dash
import diskcache
from dash import DiskcacheManager
from flask import jsonify
from waitress.server import create_server

# Application imports (after third-party, before usage)
from callbacks import register_all_callbacks
from configuration import __version__
from configuration.logging_config import cleanup_old_logs, setup_logging
from configuration.server import get_server_config
from data.installation_context import get_installation_context
from data.persistence.factory import get_backend
from data.task_progress import TaskProgress
from data.update_cleanup import cleanup_orphaned_temp_updaters
from data.update_manager import UpdateProgress
from data.update_startup import restore_pending_update, start_update_check
from data.workspace_manager import ensure_valid_workspace
from ui import serve_layout
from ui.app_config import (
    EXTERNAL_SCRIPTS,
    EXTERNAL_STYLESHEETS,
    INDEX_STRING,
    META_TAGS,
)
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
logger.info("Starting Burndown application")

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

VERSION_CHECK_RESULT: UpdateProgress | None = restore_pending_update()


def _set_version_check_result(result: UpdateProgress) -> None:
    global VERSION_CHECK_RESULT
    VERSION_CHECK_RESULT = result


update_check_thread = start_update_check(
    _set_version_check_result, VERSION_CHECK_RESULT
)

# Validate workspace before app initialization
ensure_valid_workspace()

# Configure background callback manager for long-running tasks
cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

# Initialize the Dash app with PWA support
app = dash.Dash(
    __name__,
    serve_locally=True,
    # Serve all Dash/Plotly assets locally (no CDN) for offline operation
    title="Burndown",  # Custom browser tab title
    update_title="",  # Disable update title to prevent flicker
    assets_folder="assets",  # Explicitly set assets folder
    assets_ignore=r"^vendor/.*",
    # Prevent auto-loading vendor CSS/JS to preserve order
    background_callback_manager=background_callback_manager,
    # Enable background callbacks
    external_stylesheets=EXTERNAL_STYLESHEETS,
    external_scripts=EXTERNAL_SCRIPTS,
    suppress_callback_exceptions=True,
    # Suppress errors for components in dynamic layouts
    # (Settings flyout, modals)
    meta_tags=META_TAGS,
)

# Add PWA manifest link to app index
app.index_string = INDEX_STRING

# Set the layout function as the app's layout
app.layout = serve_layout

#######################################################################
# REGISTER CALLBACKS
#######################################################################

# Register all callbacks from the modular callback system
register_all_callbacks(app)

#######################################################################
# FLASK API ENDPOINTS
#######################################################################


def get_version():
    """API endpoint to get current application version and post-update state.

    Returns:
        JSON response with current version string and post_update flag

    Example:
        GET /api/version
        Response: {"version": "2.7.2", "post_update": true}
    """

    # Check post_update_show_toast flag from database (for JavaScript toast display)
    try:
        backend = get_backend()
        post_update_value = backend.get_app_state("post_update_show_toast")
        post_update = post_update_value == "true" if post_update_value else False
    except Exception as e:
        logger.warning(f"Failed to load post_update_show_toast flag: {e}")
        post_update = False

    return jsonify({"version": __version__, "post_update": post_update})


@app.server.route("/api/clear-post-update", methods=["POST"])
def clear_post_update():
    """API endpoint to clear the post_update_show_toast flag.

    Called by JavaScript after successfully showing the update success toast.
    Separate from post_update_no_browser flag (cleared at app startup).

    Returns:
        JSON response with success status

    Example:
        POST /api/clear-post-update
        Response: {"success": true}
    """

    try:
        backend = get_backend()
        backend.set_app_state("post_update_show_toast", "")  # Clear the flag
        logger.info(
            "Cleared post_update_show_toast flag via API",
            extra={"operation": "clear_post_update_flag"},
        )
        return jsonify({"success": True})
    except Exception as e:
        logger.error(
            f"Failed to clear post_update_relaunch flag: {e}",
            extra={"operation": "clear_post_update_flag"},
        )
        return jsonify({"success": False, "error": str(e)}), 500


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
        except OSError:
            time.sleep(0.1)
    return False


#######################################################################
# MAIN
#######################################################################


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
        import time

        active_task = TaskProgress.get_active_task()
        if active_task and active_task.get("status") == "in_progress":
            task_id = active_task.get("task_id", "unknown")
            phase = active_task.get("phase", "unknown")
            logger.warning(
                "[Startup] Found stale in-progress task "
                f"'{task_id}' (phase={phase}) from previous session "
                "- marking as failed"
            )

            # Add app restart marker so recovery callback knows not to trigger actions
            import json

            restart_marker = Path("task_progress.json.restart")
            restart_marker.write_text(json.dumps({"restart_time": time.time()}))

            TaskProgress.fail_task(
                task_id,
                "Operation interrupted "
                f"(app restarted during {phase} phase). "
                "Click Update Data to restart.",
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
                    f"Burndown - Running on http://{server_config['host']}:{server_config['port']}",
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
                "pystray not available, skipping tray icon "
                "(install with: pip install pystray)"
            )
        except Exception as e:
            logger.error(f"Failed to initialize tray icon: {e}", exc_info=True)

    # Determine if browser should auto-launch
    # Only auto-launch when running as frozen executable (not in dev mode)
    # and when BURNDOWN_NO_BROWSER environment variable is not set
    # Skip auto-launch if post_update_relaunch flag is set
    # (updater will reload existing tabs)
    should_launch_browser = (
        installation_context.is_frozen
        and not server_config["debug"]
        and os.environ.get("BURNDOWN_NO_BROWSER", "0") != "1"
    )

    # Check database flag for post-update relaunch (separate from toast display flag)
    if should_launch_browser:
        try:
            backend = get_backend()
            no_browser_flag = backend.get_app_state("post_update_no_browser")

            if no_browser_flag:
                logger.info(
                    "Skipping browser auto-launch after update "
                    "(update_reconnect.js will reload existing tabs)"
                )
                print(
                    "Detected post-update restart - reconnecting "
                    "existing browser tabs...",
                    flush=True,
                )
                should_launch_browser = False

                # Clear no-browser flag immediately (one-time use for this startup)
                backend.set_app_state("post_update_no_browser", "")
                logger.debug("Cleared post_update_no_browser flag")

                # Note: post_update_show_toast flag remains
                # for JavaScript to read and clear

                # Clear VERSION_CHECK_RESULT to prevent "Update Available" toast
                # after update completes (update was just installed,
                # no need to show again)
                VERSION_CHECK_RESULT = None
                logger.debug("Cleared VERSION_CHECK_RESULT after update completion")
        except Exception as e:
            logger.warning(
                "Failed to check post_update_relaunch flag: "
                f"{e} - proceeding with normal launch"
            )

    if server_config["debug"]:
        logger.info(
            "Starting development server in DEBUG mode on "
            f"{server_config['host']}:{server_config['port']}"
        )
        print(
            "Starting development server in DEBUG mode on "
            f"{server_config['host']}:{server_config['port']}..."
        )
        app.run(debug=True, host=server_config["host"], port=server_config["port"])  # nosec B201 -- debug branch is only reached when server_config["debug"] is True (dev env, never production)
    else:
        logger.info(
            "Starting Waitress production server on "
            f"{server_config['host']}:{server_config['port']}"
        )
        url = f"http://{server_config['host']}:{server_config['port']}"
        print(
            "Starting Waitress production server on "
            f"{server_config['host']}:{server_config['port']}..."
        )
        print("\nOpen your browser at:", flush=True)
        print(f"  {url}", flush=True)
        print("", flush=True)  # Empty line for better visibility

        # Launch browser in separate thread if running as executable
        # (unless disabled by env var)
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
                        # Try to reuse existing tab by opening with new=2
                        # (new tab if possible)
                        # This still may open a new tab but at least tries
                        # to reuse window
                        webbrowser.open(url, new=2, autoraise=True)
                    except Exception as e:
                        logger.warning(f"Failed to auto-launch browser: {e}")
                        print(f"Could not auto-launch browser: {e}", flush=True)
                else:
                    logger.warning(
                        "Server readiness check timed out after 3s, "
                        "browser not launched"
                    )
                    print(
                        "Server startup took longer than expected. "
                        "Please open browser manually.",
                        flush=True,
                    )

            browser_thread = threading.Thread(target=launch_browser, daemon=True)
            browser_thread.start()

        # Start server in a way that allows graceful shutdown

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
