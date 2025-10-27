"""
Configuration file for pytest.
This file helps pytest discover and properly import modules from the project.
"""

import sys
import time
import threading
from pathlib import Path
import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="class")
def live_server():
    """
    Start Dash app server for Playwright integration tests.

    This fixture starts the app in a background thread using waitress
    and yields the server URL for tests to use.
    """
    # Import app directly (avoid dash.testing utilities)
    import app as dash_app

    app = dash_app.app
    server_port = 8051
    server_url = f"http://127.0.0.1:{server_port}"

    def run_server():
        """Run server in background thread"""
        import waitress

        waitress.serve(app.server, host="127.0.0.1", port=server_port, threads=1)

    # Start server in daemon thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Allow server startup time
    time.sleep(3)

    yield server_url

    # Server thread will be cleaned up automatically as it's a daemon thread
