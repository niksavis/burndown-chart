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

# Third-party library imports
import pytest

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
# TESTS: check_for_updates (Placeholder)
#######################################################################


def test_check_for_updates_returns_progress():
    """Test check_for_updates returns UpdateProgress object."""
    progress = check_for_updates()

    assert isinstance(progress, UpdateProgress)
    assert progress.current_version is not None
    assert progress.last_checked is not None
    assert isinstance(progress.last_checked, datetime)


def test_check_for_updates_placeholder_state():
    """Test check_for_updates returns UP_TO_DATE (placeholder behavior)."""
    progress = check_for_updates()

    # Current placeholder implementation returns UP_TO_DATE
    assert progress.state == UpdateState.UP_TO_DATE


#######################################################################
# TESTS: download_update (Placeholder)
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


def test_download_update_placeholder_returns_error():
    """Test download_update returns ERROR state (placeholder behavior)."""
    progress = UpdateProgress(
        state=UpdateState.AVAILABLE,
        current_version="2.5.0",
        available_version="2.6.0",
        download_url="https://example.com/update.zip",
    )

    result = download_update(progress)

    # Current placeholder implementation returns ERROR
    assert result.state == UpdateState.ERROR
    assert result.error_message is not None


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
