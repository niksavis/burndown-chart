"""
Unit tests for data/update_manager.py

Tests update checking, version comparison, and state management.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# Third-party library imports
import pytest
import requests

# Application imports
from data.update_manager import (
    UpdateProgress,
    UpdateState,
    check_for_updates,
    compare_versions,
    download_update,
    get_current_version,
    launch_updater,
)


#######################################################################
# TESTS: Version Comparison
#######################################################################


def test_compare_versions_update_available():
    """Test version comparison when update is available."""
    result = compare_versions("2.5.0", "2.6.0")
    assert result == -1, "Should detect newer version available"


def test_compare_versions_same_version():
    """Test version comparison when versions match."""
    result = compare_versions("2.5.0", "2.5.0")
    assert result == 0, "Should detect same version"


def test_compare_versions_current_newer():
    """Test version comparison when current version is newer."""
    result = compare_versions("2.6.0", "2.5.0")
    assert result == 1, "Should detect current version is newer"


def test_compare_versions_major_difference():
    """Test version comparison with major version difference."""
    result = compare_versions("1.9.9", "2.0.0")
    assert result == -1, "Should detect major version update"


def test_compare_versions_with_v_prefix():
    """Test version comparison handles 'v' prefix."""
    result = compare_versions("v2.5.0", "v2.6.0")
    assert result == -1, "Should handle v prefix correctly"


def test_compare_versions_mixed_prefix():
    """Test version comparison with mixed prefix usage."""
    result = compare_versions("2.5.0", "v2.6.0")
    assert result == -1, "Should handle mixed prefix usage"


def test_compare_versions_invalid_format():
    """Test version comparison raises error for invalid format."""
    with pytest.raises(ValueError, match="Invalid version format"):
        compare_versions("invalid", "2.6.0")


def test_compare_versions_missing_parts():
    """Test version comparison raises error for incomplete versions."""
    with pytest.raises(ValueError, match="Invalid version format"):
        compare_versions("2.5", "2.6.0")


#######################################################################
# TESTS: UpdateState Enum
#######################################################################


def test_update_state_enum_values():
    """Test UpdateState enum has expected values."""
    assert UpdateState.IDLE.value == "idle"
    assert UpdateState.CHECKING.value == "checking"
    assert UpdateState.AVAILABLE.value == "available"
    assert UpdateState.DOWNLOADING.value == "downloading"
    assert UpdateState.READY.value == "ready"
    assert UpdateState.INSTALLING.value == "installing"
    assert UpdateState.ERROR.value == "error"
    assert UpdateState.UP_TO_DATE.value == "up_to_date"


#######################################################################
# TESTS: UpdateProgress Dataclass
#######################################################################


def test_update_progress_creation():
    """Test UpdateProgress can be created with required fields."""
    progress = UpdateProgress(
        state=UpdateState.IDLE,
        current_version="2.5.0",
    )
    assert progress.state == UpdateState.IDLE
    assert progress.current_version == "2.5.0"
    assert progress.available_version is None
    assert progress.progress_percent == 0


def test_update_progress_with_optional_fields():
    """Test UpdateProgress with all optional fields."""
    now = datetime.now()
    progress = UpdateProgress(
        state=UpdateState.AVAILABLE,
        current_version="2.5.0",
        available_version="2.6.0",
        download_url="https://example.com/update.zip",
        progress_percent=50,
        last_checked=now,
        release_notes="Test notes",
        file_size=1024000,
    )
    assert progress.available_version == "2.6.0"
    assert progress.download_url == "https://example.com/update.zip"
    assert progress.progress_percent == 50
    assert progress.last_checked == now
    assert progress.release_notes == "Test notes"
    assert progress.file_size == 1024000


def test_update_progress_to_dict():
    """Test UpdateProgress serialization to dictionary."""
    now = datetime.now()
    progress = UpdateProgress(
        state=UpdateState.AVAILABLE,
        current_version="2.5.0",
        available_version="2.6.0",
        last_checked=now,
    )
    result = progress.to_dict()

    assert result["state"] == "available"
    assert result["current_version"] == "2.5.0"
    assert result["available_version"] == "2.6.0"
    assert result["last_checked"] == now.isoformat()
    assert result["progress_percent"] == 0


def test_update_progress_to_dict_with_path():
    """Test UpdateProgress serialization handles Path objects."""
    progress = UpdateProgress(
        state=UpdateState.READY,
        current_version="2.5.0",
        download_path=Path("C:/temp/update.zip"),
    )
    result = progress.to_dict()

    # Path objects use OS-specific separators
    assert result["download_path"] == str(Path("C:/temp/update.zip"))


def test_update_progress_to_dict_none_values():
    """Test UpdateProgress serialization handles None values."""
    progress = UpdateProgress(
        state=UpdateState.IDLE,
        current_version="2.5.0",
    )
    result = progress.to_dict()

    assert result["available_version"] is None
    assert result["download_url"] is None
    assert result["download_path"] is None
    assert result["error_message"] is None
    assert result["last_checked"] is None


#######################################################################
# TESTS: get_current_version
#######################################################################


def test_get_current_version():
    """Test get_current_version returns valid version string."""
    version = get_current_version()
    assert isinstance(version, str)
    assert len(version.split(".")) == 3, "Should be semantic version X.Y.Z"

    # Verify each part is numeric
    major, minor, patch = version.split(".")
    assert major.isdigit(), "Major version should be numeric"
    assert minor.isdigit(), "Minor version should be numeric"
    assert patch.isdigit(), "Patch version should be numeric"


#######################################################################
# TESTS: check_for_updates
#######################################################################


def test_check_for_updates_returns_progress():
    """Test check_for_updates returns UpdateProgress object."""
    with patch("data.update_manager.requests.get") as mock_get:
        # Mock API response - up to date
        mock_response = Mock()
        mock_response.json.return_value = {
            "tag_name": "v2.5.0",
            "prerelease": False,
            "assets": [],
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        progress = check_for_updates()

        assert isinstance(progress, UpdateProgress)
        assert progress.current_version is not None
        assert progress.last_checked is not None
        assert isinstance(progress.last_checked, datetime)


def test_check_for_updates_with_newer_version():
    """Test check_for_updates detects available update."""
    with patch("data.update_manager.requests.get") as mock_get:
        with patch("data.update_manager.sys") as mock_sys:
            # Mock frozen=True to simulate executable
            mock_sys.frozen = True

            # Mock API response with newer version
            mock_response = Mock()
            mock_response.json.return_value = {
                "tag_name": "v99.0.0",  # Much newer version
                "prerelease": False,
                "body": "## What's New\n\n- Feature X",
                "assets": [
                    {
                        "name": "burndown-windows-v99.0.0.zip",
                        "browser_download_url": "https://github.com/owner/repo/releases/download/v99.0.0/burndown-windows-v99.0.0.zip",
                        "size": 95420160,
                    }
                ],
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            progress = check_for_updates()

            assert progress.state == UpdateState.AVAILABLE
        assert progress.available_version == "99.0.0"
        assert progress.download_url is not None
        assert "github.com" in progress.download_url
        assert progress.file_size == 95420160
        assert progress.release_notes is not None


def test_check_for_updates_same_version():
    """Test check_for_updates when already up to date."""
    with patch("data.update_manager.requests.get") as mock_get:
        with patch("data.update_manager.get_current_version") as mock_version:
            mock_version.return_value = "2.5.0"

            # Mock API response with same version
            mock_response = Mock()
            mock_response.json.return_value = {
                "tag_name": "v2.5.0",
                "prerelease": False,
                "assets": [],
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            progress = check_for_updates()

            assert progress.state == UpdateState.UP_TO_DATE


def test_check_for_updates_skips_prerelease():
    """Test check_for_updates ignores prerelease versions."""
    with patch("data.update_manager.requests.get") as mock_get:
        # Mock API response with prerelease
        mock_response = Mock()
        mock_response.json.return_value = {
            "tag_name": "v99.0.0-beta",
            "prerelease": True,
            "assets": [],
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        progress = check_for_updates()

        assert progress.state == UpdateState.UP_TO_DATE


def test_check_for_updates_no_windows_asset():
    """Test check_for_updates when no Windows asset is available."""
    with patch("data.update_manager.requests.get") as mock_get:
        # Mock API response without Windows asset
        mock_response = Mock()
        mock_response.json.return_value = {
            "tag_name": "v99.0.0",
            "prerelease": False,
            "assets": [
                {
                    "name": "burndown-linux-v99.0.0.tar.gz",
                    "browser_download_url": "https://example.com/linux.tar.gz",
                }
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        progress = check_for_updates()

        # Running from source → MANUAL_UPDATE_REQUIRED (not ERROR)
        assert progress.state == UpdateState.MANUAL_UPDATE_REQUIRED


def test_check_for_updates_timeout():
    """Test check_for_updates handles timeout gracefully."""
    with patch("data.update_manager.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

        progress = check_for_updates()

        assert progress.state == UpdateState.ERROR
        assert progress.error_message is not None
        assert "timed out" in progress.error_message.lower()


def test_check_for_updates_network_error():
    """Test check_for_updates handles network errors."""
    with patch("data.update_manager.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError(
            "Network unreachable"
        )

        progress = check_for_updates()

        assert progress.state == UpdateState.ERROR
        assert progress.error_message is not None
        assert "No network connection available" in progress.error_message


def test_check_for_updates_http_error():
    """Test check_for_updates handles HTTP errors."""
    with patch("data.update_manager.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        progress = check_for_updates()

        assert progress.state == UpdateState.ERROR


def test_check_for_updates_invalid_json():
    """Test check_for_updates handles invalid JSON response."""
    with patch("data.update_manager.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        progress = check_for_updates()

        assert progress.state == UpdateState.ERROR
        assert progress.error_message is not None
        assert "Invalid update data" in progress.error_message


def test_check_for_updates_sends_user_agent():
    """Test check_for_updates sends proper User-Agent header."""
    with patch("data.update_manager.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            "tag_name": "v2.5.0",
            "prerelease": False,
            "assets": [],
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        check_for_updates()

        # Verify User-Agent header was sent
        call_kwargs = mock_get.call_args[1]
        assert "headers" in call_kwargs
        assert "User-Agent" in call_kwargs["headers"]
        assert "Burndown" in call_kwargs["headers"]["User-Agent"]


#######################################################################
# TESTS: download_update
#######################################################################


def test_download_update_requires_available_state():
    """Test download_update raises error if state is not AVAILABLE."""
    progress = UpdateProgress(
        state=UpdateState.IDLE,
        current_version="2.5.0",
    )

    with pytest.raises(ValueError, match="Cannot download update in state"):
        download_update(progress)


def test_download_update_requires_download_url():
    """Test download_update raises error if download_url is None."""
    progress = UpdateProgress(
        state=UpdateState.AVAILABLE,
        current_version="2.5.0",
        available_version="2.6.0",
        download_url=None,
    )

    with pytest.raises(ValueError, match="download_url is required"):
        download_update(progress)


def test_download_update_success(tmp_path):
    """Test download_update successfully downloads file with progress tracking."""
    # Mock file content
    file_content = b"fake zip content for testing" * 1000  # ~27KB

    with patch("data.update_manager.requests.get") as mock_get:
        with patch("data.update_manager.tempfile.gettempdir") as mock_tempdir:
            # Set temp directory to our test path
            mock_tempdir.return_value = str(tmp_path)

            # Mock streaming response
            mock_response = Mock()
            mock_response.headers = {"content-length": str(len(file_content))}
            mock_response.raise_for_status.return_value = None

            # Mock iter_content to return chunks
            chunk_size = 1024 * 1024  # 1MB
            chunks = [
                file_content[i : i + chunk_size]
                for i in range(0, len(file_content), chunk_size)
            ]
            mock_response.iter_content.return_value = chunks
            mock_get.return_value = mock_response

            progress = UpdateProgress(
                state=UpdateState.AVAILABLE,
                current_version="2.5.0",
                available_version="2.6.0",
                download_url="https://github.com/owner/repo/releases/download/v2.6.0/update.zip",
            )

            result = download_update(progress)

            assert result.state == UpdateState.READY
            assert result.progress_percent == 100
            assert result.download_path is not None
            assert result.download_path.exists()
            # Filename is extracted from URL (update.zip in this test)
            assert "update.zip" in str(result.download_path)

            # Verify file contents
            downloaded_content = result.download_path.read_bytes()
            assert downloaded_content == file_content


def test_download_update_progress_tracking():
    """Test download_update tracks progress correctly."""
    file_content = b"x" * (10 * 1024 * 1024)  # 10MB

    with patch("data.update_manager.requests.get") as mock_get:
        with patch("data.update_manager.tempfile.gettempdir") as mock_tempdir:
            with patch("builtins.open", mock_open()):
                mock_tempdir.return_value = "/tmp"

                mock_response = Mock()
                mock_response.headers = {"content-length": str(len(file_content))}
                mock_response.raise_for_status.return_value = None

                # Mock chunks to track progress
                chunk_size = 1024 * 1024  # 1MB
                chunks = [
                    file_content[i : i + chunk_size]
                    for i in range(0, len(file_content), chunk_size)
                ]
                mock_response.iter_content.return_value = chunks
                mock_get.return_value = mock_response

                progress = UpdateProgress(
                    state=UpdateState.AVAILABLE,
                    current_version="2.5.0",
                    available_version="2.6.0",
                    download_url="https://example.com/update.zip",
                )

                result = download_update(progress)

                # Progress should reach 100%
                assert result.progress_percent == 100


def test_download_update_large_file_warning(tmp_path):
    """Test download_update logs warning for large files."""
    # Create file larger than MAX_DOWNLOAD_SIZE (150MB)
    large_size = 160 * 1024 * 1024
    # Provide full content to match the size
    file_content = b"x" * large_size

    with patch("data.update_manager.requests.get") as mock_get:
        with patch("data.update_manager.tempfile.gettempdir") as mock_tempdir:
            mock_tempdir.return_value = str(tmp_path)

            mock_response = Mock()
            mock_response.headers = {"content-length": str(large_size)}
            mock_response.raise_for_status.return_value = None
            # Return in chunks to avoid memory issues in test
            chunk_size = 1024 * 1024
            chunks = [
                file_content[i : i + chunk_size]
                for i in range(0, len(file_content), chunk_size)
            ]
            mock_response.iter_content.return_value = chunks
            mock_get.return_value = mock_response

            progress = UpdateProgress(
                state=UpdateState.AVAILABLE,
                current_version="2.5.0",
                available_version="2.6.0",
                download_url="https://example.com/large-update.zip",
            )

            result = download_update(progress)

            # Should still succeed despite size
            assert result.state == UpdateState.READY


def test_download_update_incomplete_download(tmp_path):
    """Test download_update detects incomplete downloads."""
    expected_size = 10 * 1024 * 1024  # 10MB
    actual_content = b"incomplete" * 100  # Much smaller

    with patch("data.update_manager.requests.get") as mock_get:
        with patch("data.update_manager.tempfile.gettempdir") as mock_tempdir:
            mock_tempdir.return_value = str(tmp_path)

            mock_response = Mock()
            mock_response.headers = {"content-length": str(expected_size)}
            mock_response.raise_for_status.return_value = None
            mock_response.iter_content.return_value = [actual_content]
            mock_get.return_value = mock_response

            progress = UpdateProgress(
                state=UpdateState.AVAILABLE,
                current_version="2.5.0",
                available_version="2.6.0",
                download_url="https://example.com/update.zip",
            )

            result = download_update(progress)

            assert result.state == UpdateState.ERROR
            assert result.error_message is not None
            assert "incomplete" in result.error_message.lower()


def test_download_update_timeout():
    """Test download_update handles timeout gracefully."""
    with patch("data.update_manager.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

        progress = UpdateProgress(
            state=UpdateState.AVAILABLE,
            current_version="2.5.0",
            available_version="2.6.0",
            download_url="https://example.com/update.zip",
        )

        result = download_update(progress)

        assert result.state == UpdateState.ERROR
        assert result.error_message is not None
        assert "timed out" in result.error_message.lower()


def test_download_update_network_error():
    """Test download_update handles network errors."""
    with patch("data.update_manager.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError(
            "Network unreachable"
        )

        progress = UpdateProgress(
            state=UpdateState.AVAILABLE,
            current_version="2.5.0",
            available_version="2.6.0",
            download_url="https://example.com/update.zip",
        )

        result = download_update(progress)

        assert result.state == UpdateState.ERROR
        assert result.error_message is not None
        assert "failed" in result.error_message.lower()


def test_download_update_http_error():
    """Test download_update handles HTTP errors."""
    with patch("data.update_manager.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        progress = UpdateProgress(
            state=UpdateState.AVAILABLE,
            current_version="2.5.0",
            available_version="2.6.0",
            download_url="https://example.com/update.zip",
        )

        result = download_update(progress)

        assert result.state == UpdateState.ERROR


def test_download_update_file_write_error():
    """Test download_update handles file write errors."""
    with patch("data.update_manager.requests.get") as mock_get:
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            mock_response = Mock()
            mock_response.headers = {"content-length": "1000"}
            mock_response.raise_for_status.return_value = None
            mock_response.iter_content.return_value = [b"test"]
            mock_get.return_value = mock_response

            progress = UpdateProgress(
                state=UpdateState.AVAILABLE,
                current_version="2.5.0",
                available_version="2.6.0",
                download_url="https://example.com/update.zip",
            )

            result = download_update(progress)

            assert result.state == UpdateState.ERROR
            assert result.error_message is not None
            assert (
                "save" in result.error_message.lower()
                or "write" in result.error_message.lower()
            )


#######################################################################
# TESTS: launch_updater (Placeholder)
#######################################################################


def test_launch_updater_missing_file(tmp_path):
    """Test launch_updater returns False when update file doesn't exist."""
    nonexistent_path = tmp_path / "nonexistent.zip"
    result = launch_updater(nonexistent_path)

    assert result is False


def test_launch_updater_placeholder_behavior(tmp_path):
    """Test launch_updater returns False (placeholder behavior)."""
    # Create a temporary file
    update_file = tmp_path / "update.zip"
    update_file.write_text("placeholder content")

    result = launch_updater(update_file)

    # Current placeholder implementation returns False
    assert result is False
