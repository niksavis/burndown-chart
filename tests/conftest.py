"""
Configuration file for pytest.
This file helps pytest discover and properly import modules from the project.
"""

import sys
import time
import threading
import tempfile
import os
from pathlib import Path
import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="function", autouse=True)
def backup_configs():
    """
    Backup configuration files and profiles directory before test and restore after test.

    This ensures tests that modify configs don't affect other tests.
    Restoration happens even if test fails.

    **autouse=True** ensures this runs for EVERY test automatically,
    even if the test doesn't explicitly request this fixture.
    """
    import shutil

    config_files = [
        "app_settings.json",
        "jira_query_profiles.json",
        "project_data.json",
        "jira_cache.json",
        "jira_changelog_cache.json",
        "metrics_snapshots.json",
    ]

    backups = {}
    file_states = {}  # Track which files existed before test
    profiles_backup = None
    profiles_existed = False

    # Create backups and track file states for config files
    for config_file in config_files:
        config_path = project_root / config_file
        file_states[config_file] = config_path.exists()

        if config_path.exists():
            # Read content into memory
            with open(config_path, "r", encoding="utf-8") as f:
                backups[config_file] = f.read()

    # Backup profiles directory if it exists
    profiles_dir = project_root / "profiles"
    if profiles_dir.exists():
        profiles_existed = True
        profiles_backup = tempfile.mkdtemp(prefix="profiles_backup_")
        shutil.copytree(
            profiles_dir, Path(profiles_backup) / "profiles", dirs_exist_ok=True
        )

    yield backups

    # Restore profiles directory first (happens even if test fails)
    if profiles_existed and profiles_backup:
        # Remove current profiles directory
        if profiles_dir.exists():
            shutil.rmtree(profiles_dir, ignore_errors=True)
        # Restore from backup
        shutil.copytree(
            Path(profiles_backup) / "profiles", profiles_dir, dirs_exist_ok=True
        )
        # Cleanup backup
        shutil.rmtree(profiles_backup, ignore_errors=True)
    else:
        # Profiles didn't exist before test - remove if created
        if profiles_dir.exists():
            shutil.rmtree(profiles_dir, ignore_errors=True)

    # Restore config file backups
    for config_file in config_files:
        config_path = project_root / config_file

        if file_states[config_file]:
            # File existed before test - restore it
            if config_file in backups:
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(backups[config_file])
        else:
            # File didn't exist before test - delete it if created
            if config_path.exists():
                config_path.unlink()


@pytest.fixture(scope="function")
def live_server(backup_configs):
    """
    Start Dash app server for Playwright integration tests.

    This fixture:
    1. Backs up configs (via backup_configs fixture)
    2. Starts app in isolated thread
    3. Waits for server to be ready
    4. Yields server URL for tests
    5. Shuts down server gracefully
    6. Restores configs (via backup_configs fixture)

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
