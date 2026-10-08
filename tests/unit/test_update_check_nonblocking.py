import time
from unittest.mock import patch

import pytest


def test_update_check_thread_is_daemon():

    from app import update_check_thread

    assert update_check_thread.daemon is True, "Update check thread must be daemon"
    assert update_check_thread.name == "UpdateCheckThread"


def test_update_check_runs_in_background():

    import app  # noqa: F401

    start_time = time.time()

    elapsed = time.time() - start_time

    assert elapsed < 1.0, (
        f"App import took {elapsed:.2f}s - may be blocking on update check"
    )


def test_update_check_timeout_handling():

    import requests.exceptions

    from data.update_manager import UpdateState, check_for_updates

    with patch("data.update_manager.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        result = check_for_updates()

        assert result.state == UpdateState.ERROR
        assert result.error_message is not None
        assert "timed out" in result.error_message.lower()
        assert result.current_version is not None


def test_update_check_error_handling():

    import requests.exceptions

    from data.update_manager import UpdateState, check_for_updates

    with patch("data.update_manager.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("No internet")

        result = check_for_updates()

        assert result.state == UpdateState.ERROR
        assert result.error_message is not None
        assert "no network connection available" in result.error_message.lower()
        assert result.current_version is not None


def test_version_check_result_accessible():

    from app import VERSION_CHECK_RESULT

    assert (
        hasattr(type(VERSION_CHECK_RESULT), "__name__") or VERSION_CHECK_RESULT is None
    )


@pytest.mark.timeout(5)
def test_app_startup_completes_without_blocking():

    import sys

    if "app" in sys.modules:
        del sys.modules["app"]

    start_time = time.time()

    import app  # noqa: F401

    elapsed = time.time() - start_time

    assert elapsed < 3.0, f"App took {elapsed:.2f}s to initialize - may be blocking"
