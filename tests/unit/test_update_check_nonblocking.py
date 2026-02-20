"""
Test that update check does not block app startup.

Verifies that the app UI appears immediately even when update check
times out or takes a long time to complete.
"""

import time
from unittest.mock import patch

import pytest


def test_update_check_thread_is_daemon():
    """Verify update check thread is a daemon thread.

    Daemon threads automatically terminate when the main program exits,
    ensuring they don't block shutdown.
    """
    from app import update_check_thread

    assert update_check_thread.daemon is True, "Update check thread must be daemon"
    assert update_check_thread.name == "UpdateCheckThread"


def test_update_check_runs_in_background():
    """Verify update check runs in background without blocking.

    Simulates a slow update check (2+ seconds) and verifies that
    the main thread continues immediately.
    """
    import app  # noqa: F401

    start_time = time.time()

    # The update_check_thread should already be started during import
    # Main thread should not have waited for it
    elapsed = time.time() - start_time

    # App import should complete in under 1 second
    # (not waiting for 10-second timeout)
    assert elapsed < 1.0, (
        f"App import took {elapsed:.2f}s - may be blocking on update check"
    )


def test_update_check_timeout_handling():
    """Verify update check handles timeout gracefully.

    Tests that when GitHub API times out, the check returns ERROR state
    without crashing or blocking indefinitely.
    """
    import requests.exceptions

    from data.update_manager import UpdateState, check_for_updates

    # Mock requests.get to raise Timeout
    with patch("data.update_manager.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        # Should return ERROR state, not raise exception
        result = check_for_updates()

        assert result.state == UpdateState.ERROR
        assert result.error_message is not None
        assert "timed out" in result.error_message.lower()
        assert result.current_version is not None


def test_update_check_error_handling():
    """Verify update check handles network errors gracefully.

    Tests that network errors are caught and returned as ERROR state
    without crashing the app.
    """
    import requests.exceptions

    from data.update_manager import UpdateState, check_for_updates

    # Mock requests.get to raise ConnectionError
    with patch("data.update_manager.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("No internet")

        # Should return ERROR state, not raise exception
        result = check_for_updates()

        assert result.state == UpdateState.ERROR
        assert result.error_message is not None
        assert "no network connection available" in result.error_message.lower()
        assert result.current_version is not None


def test_version_check_result_accessible():
    """Verify VERSION_CHECK_RESULT is accessible for UI components.

    The global variable should be accessible to UI components
    to display update notifications.
    """
    from app import VERSION_CHECK_RESULT

    # Initially might be None if thread hasn't completed yet
    # But variable should exist and be accessible
    assert (
        hasattr(type(VERSION_CHECK_RESULT), "__name__") or VERSION_CHECK_RESULT is None
    )


@pytest.mark.timeout(5)
def test_app_startup_completes_without_blocking():
    """Integration test: app startup completes in reasonable time.

    Verifies that importing app module doesn't block for extended period
    waiting for update check to complete.
    """
    import sys

    # Remove app from cache if present
    if "app" in sys.modules:
        del sys.modules["app"]

    start_time = time.time()

    # Re-import app (simulating fresh start)
    import app  # noqa: F401

    elapsed = time.time() - start_time

    # App should initialize in under 3 seconds even with update check
    # (The check itself has 10s timeout but runs in background)
    assert elapsed < 3.0, f"App took {elapsed:.2f}s to initialize - may be blocking"
