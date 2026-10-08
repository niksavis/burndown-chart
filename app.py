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

import dash
import diskcache
from dash import DiskcacheManager
from flask import jsonify
from waitress.server import create_server

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

_server = None


def shutdown_server():
    if _server:
        logger.info("Shutting down Waitress server...")
        try:
            _server.close()
        except Exception as e:
            logger.warning(f"Error closing server: {e}")


installation_context = get_installation_context()
logger_init = logging.getLogger(__name__)
logger_init.info(f"Installation context: {installation_context}")

extract_license_on_first_run()

setup_logging(log_dir=str(installation_context.logs_path), log_level="INFO")
cleanup_old_logs(log_dir=str(installation_context.logs_path), max_age_days=30)

logger = logging.getLogger(__name__)
logger.info("Starting Burndown application")

cleanup_orphaned_temp_updaters()


try:
    from data.migration.migrator import run_migration_if_needed

    logger.info("Checking if database migration needed...")
    migration_success = run_migration_if_needed()

    if migration_success:
        logger.info("Database ready (migration complete or not needed)")
    else:
        logger.error("Database migration failed - app may not function correctly")
        print("ERROR: Database migration failed. Check logs/app.log for details.")

except Exception as e:
    logger.error(f"Migration check failed: {e}", exc_info=True)
    print(f"WARNING: Migration check failed - {e}. App will attempt to continue.")


VERSION_CHECK_RESULT: UpdateProgress | None = restore_pending_update()


def _set_version_check_result(result: UpdateProgress) -> None:
    global VERSION_CHECK_RESULT
    VERSION_CHECK_RESULT = result


update_check_thread = start_update_check(
    _set_version_check_result, VERSION_CHECK_RESULT
)

ensure_valid_workspace()

cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

app = dash.Dash(
    __name__,
    serve_locally=True,
    title="Burndown",
    update_title="",
    assets_folder="assets",
    assets_ignore=r"^vendor/.*",
    background_callback_manager=background_callback_manager,
    external_stylesheets=EXTERNAL_STYLESHEETS,
    external_scripts=EXTERNAL_SCRIPTS,
    suppress_callback_exceptions=True,
    meta_tags=META_TAGS,
)

app.index_string = INDEX_STRING

app.layout = serve_layout


register_all_callbacks(app)


def get_version():

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

    try:
        backend = get_backend()
        backend.set_app_state("post_update_show_toast", "")
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


def wait_for_server_ready(host: str, port: int, timeout: float = 3.0) -> bool:

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def setup_graceful_shutdown():

    def shutdown_handler(signum, frame):
        sig_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        logger.info(f"Received {sig_name}, shutting down gracefully...")
        print("\nShutting down server...", flush=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)


if __name__ == "__main__":
    setup_graceful_shutdown()

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

            import json

            restart_marker = Path("task_progress.json.restart")
            restart_marker.write_text(json.dumps({"restart_time": time.time()}))

            TaskProgress.fail_task(
                task_id,
                "Operation interrupted "
                f"(app restarted during {phase} phase). "
                "Click Update Data to restart.",
            )

            time.sleep(0.1)
    except Exception as e:
        logger.error(f"[Startup] Failed to clean up stale tasks: {e}")

    server_config = get_server_config()

    if installation_context.is_frozen:
        try:
            import pystray
            from PIL import Image

            def on_open(icon, item):
                url = f"http://{server_config['host']}:{server_config['port']}"
                try:
                    webbrowser.open(url, new=2, autoraise=True)
                    logger.info("Browser opened from tray icon")
                except Exception as e:
                    logger.error(f"Failed to open browser from tray: {e}")

            def on_quit(icon, item):
                logger.info("Quit requested from tray icon")
                icon.stop()
                shutdown_server()
                os._exit(0)

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

    should_launch_browser = (
        installation_context.is_frozen
        and not server_config["debug"]
        and os.environ.get("BURNDOWN_NO_BROWSER", "0") != "1"
    )

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

                backend.set_app_state("post_update_no_browser", "")
                logger.debug("Cleared post_update_no_browser flag")

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
        print("", flush=True)

        if should_launch_browser:

            def launch_browser():
                logger.info("Waiting for server to be ready...")
                if wait_for_server_ready(
                    server_config["host"], server_config["port"], timeout=3.0
                ):
                    logger.info(f"Server ready, launching browser at {url}")
                    print("Server ready! Launching browser...", flush=True)
                    try:
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

        _server = create_server(
            app.server,
            host=server_config["host"],
            port=server_config["port"],
            threads=4,
        )

        atexit.register(shutdown_server)

        logger.info("Waitress server starting...")
        _server.run()
