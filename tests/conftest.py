"""
Configuration file for pytest.
This file helps pytest discover and properly import modules from the project.

CRITICAL: Test Isolation Strategy
---------------------------------
All tests MUST run in isolation without modifying real application data.
This is achieved through:
1. Patching PROFILES_DIR, PROFILES_FILE to temp directories
2. Patching data file paths (PROJECT_DATA_FILE, etc.) to temp files
3. Never creating files in project root during tests

The `isolate_test_data` fixture (autouse=True) ensures this for every test.
"""

import sys
import time
import threading
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
import shutil

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="function")
def temp_database():
    """
    Create temporary SQLite database for testing.

    Initializes a fresh database with all tables and indexes.
    Automatically cleaned up after test completes.

    Usage:
        def test_something(temp_database):
            # backend will automatically use temp database
            ...
    """
    temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db_path = Path(temp_db_file.name)
    temp_db_file.close()

    # Initialize database schema
    from data.migration.schema_manager import initialize_schema

    initialize_schema(db_path=temp_db_path)

    # Patch database path for all modules
    db_patches = [
        patch("data.database.DB_PATH", temp_db_path),
        patch("data.persistence.factory.DEFAULT_SQLITE_PATH", str(temp_db_path)),
    ]

    for p in db_patches:
        p.start()

    # Clear backend singleton to force recreation with new path
    import data.persistence.factory as factory

    factory._backend_instance = None

    yield temp_db_path

    for p in db_patches:
        p.stop()

    # Cleanup
    if temp_db_path.exists():
        temp_db_path.unlink()


@pytest.fixture(scope="function")
def isolate_test_data(temp_database):
    """
    Isolate tests from real application data.

    Creates temporary directories and patches all data file paths to use them.
    This ensures tests NEVER modify:
    - profiles/ directory
    - Database (uses temp_database)
    - project_data.json (legacy)
    - metrics_snapshots.json (legacy)
    - app_settings.json (legacy)
    - Any other application data files

    **NOT autouse** - tests must explicitly request this fixture when they need
    to write to data files. Tests that only READ from config will use real data.
    Integration tests and tests that CREATE/MODIFY data should use this fixture.

    Usage:
        def test_something(isolate_test_data):
            # This test runs in isolated temp directory
            ...
    """
    # Create temporary root directory for all test data
    temp_root = tempfile.mkdtemp(prefix="burndown_test_")
    temp_profiles_dir = Path(temp_root) / "profiles"
    temp_profiles_dir.mkdir(parents=True, exist_ok=True)
    temp_profiles_file = temp_profiles_dir / "profiles.json"

    # Temp files for various data (LEGACY - most now in database)
    temp_project_data = Path(temp_root) / "project_data.json"
    temp_jira_cache = Path(temp_root) / "jira_cache.json"  # LEGACY fallback only
    temp_metrics_snapshots = Path(temp_root) / "metrics_snapshots.json"
    temp_app_settings = Path(temp_root) / "app_settings.json"
    temp_app_settings = Path(temp_root) / "app_settings.json"

    # Apply ALL patches to redirect data to temp locations
    patches = [
        # Profile manager patches
        patch("data.profile_manager.PROFILES_DIR", temp_profiles_dir),
        # Persistence patches (try multiple possible locations)
    ]

    # Try to patch persistence module if it has these constants
    try:
        from data import persistence

        if hasattr(persistence, "PROJECT_DATA_FILE"):
            patches.append(
                patch("data.persistence.PROJECT_DATA_FILE", temp_project_data)
            )
        if hasattr(persistence, "SETTINGS_FILE"):
            patches.append(patch("data.persistence.SETTINGS_FILE", temp_app_settings))
    except ImportError:
        pass

    # Try to patch metrics_snapshots module - use function patch
    try:
        from data import metrics_snapshots  # noqa: F401 - import needed for hasattr check

        # metrics_snapshots uses _get_snapshots_file_path() function, not a constant
        # So we patch the function to return our temp file
        patches.append(
            patch(
                "data.metrics_snapshots._get_snapshots_file_path",
                return_value=temp_metrics_snapshots,
            )
        )
    except ImportError:
        pass

    # Start all patches
    for p in patches:
        p.start()

    yield {
        "temp_root": temp_root,
        "profiles_dir": temp_profiles_dir,
        "profiles_file": temp_profiles_file,
        "project_data": temp_project_data,
        "jira_cache": temp_jira_cache,
        "metrics_snapshots": temp_metrics_snapshots,
        "app_settings": temp_app_settings,
    }

    # Stop all patches
    for p in patches:
        p.stop()

    # Cleanup temp directory
    shutil.rmtree(temp_root, ignore_errors=True)


@pytest.fixture(scope="function")
def live_server(isolate_test_data):
    """
    Start Dash app server for Playwright integration tests.

    This fixture:
    1. Isolates data (via isolate_test_data fixture)
    2. Starts app in isolated thread
    3. Waits for server to be ready
    4. Yields server URL for tests
    5. Shuts down server gracefully
    6. Cleans up temp data (via isolate_test_data fixture)

    Scope is 'function' to ensure complete isolation between tests.
    """
    # Import app directly (avoid dash.testing utilities)
    import app as dash_app

    app = dash_app.app
    server_port = 8051
    server_url = f"http://127.0.0.1:{server_port}"

    def run_server():
        """Run server in background thread"""
        import waitress

        # Use waitress.serve which blocks until server stops
        waitress.serve(
            app.server,
            host="127.0.0.1",
            port=server_port,
            threads=1,
            channel_timeout=30,
            _quiet=True,  # Suppress logging
        )

    # Start server in daemon thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("127.0.0.1", server_port))
            sock.close()
            if result == 0:
                time.sleep(1)  # Extra time for full initialization
                break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        raise RuntimeError(f"Server failed to start after {max_retries * 0.5} seconds")

    yield server_url

    # Note: Daemon thread will be terminated automatically when test ends
    # Config restoration happens via backup_configs fixture


@pytest.fixture(scope="function")
def temp_log_dir():
    """
    Create temporary directory for log files in tests.

    This ensures test isolation - logs don't pollute project directory.
    Cleanup happens automatically even if test fails.

    CRITICAL: Tests MUST call shutdown_logging() before fixture teardown
    to release file handles on Windows. Otherwise, cleanup will fail with
    PermissionError on file deletion.

    Usage:
        def test_logging(temp_log_dir):
            from configuration.logging_config import setup_logging, shutdown_logging

            setup_logging(log_dir=temp_log_dir)
            # Test logging...
            shutdown_logging()  # MUST call before test ends
            # temp_log_dir will be cleaned up automatically
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir
        # Cleanup is automatic when context exits
        # Note: Tests must call shutdown_logging() to release file handles


@pytest.fixture(scope="function")
def temp_cache_dir():
    """
    Create temporary directory for cache files in tests.

    This ensures test isolation - cache files don't pollute project directory.
    Cleanup happens automatically even if test fails.

    Usage:
        def test_caching(temp_cache_dir):
            cache_file = os.path.join(temp_cache_dir, "test_cache.json")
            save_cache(cache_file, data)
            # Test caching...
            # temp_cache_dir will be cleaned up automatically
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir
        # Cleanup is automatic when context exits


# Import dashboard test fixtures to make them available to all tests
pytest_plugins = ["tests.utils.dashboard_test_fixtures"]
