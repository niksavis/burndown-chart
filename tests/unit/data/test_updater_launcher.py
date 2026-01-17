"""
Tests for updater launcher functionality.

Verifies ZIP extraction and updater launch logic.
"""

import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def test_launch_updater_file_not_found():
    """Test that launch_updater returns False when ZIP file doesn't exist."""
    from data.update_manager import launch_updater

    non_existent_path = Path("/nonexistent/update.zip")

    result = launch_updater(non_existent_path)

    assert result is False


def test_launch_updater_invalid_zip():
    """Test that launch_updater handles invalid ZIP files gracefully."""
    from data.update_manager import launch_updater

    # Create a temporary file that's not a valid ZIP
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".zip") as f:
        f.write("This is not a ZIP file")
        temp_file = Path(f.name)

    try:
        result = launch_updater(temp_file)
        assert result is False
    finally:
        if temp_file.exists():
            temp_file.unlink()


def test_launch_updater_missing_executable():
    """Test that launch_updater returns False when updater.exe not in ZIP."""
    from data.update_manager import launch_updater

    # Create a valid ZIP without the updater executable
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as f:
        temp_zip = Path(f.name)

    try:
        with zipfile.ZipFile(temp_zip, "w") as zf:
            zf.writestr("README.txt", "This ZIP doesn't contain the updater")

        result = launch_updater(temp_zip)
        assert result is False
    finally:
        if temp_zip.exists():
            temp_zip.unlink()


def test_launch_updater_extracts_zip():
    """Test that launch_updater successfully extracts ZIP contents."""
    from data.update_manager import launch_updater

    # Create a valid ZIP with a mock updater executable
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as f:
        temp_zip = Path(f.name)

    try:
        with zipfile.ZipFile(temp_zip, "w") as zf:
            # Add a fake updater executable
            zf.writestr("BurndownChartUpdater.exe", "mock updater content")

        # Mock subprocess.Popen and sys.exit to prevent actual execution
        with (
            patch("data.update_manager.subprocess.Popen") as mock_popen,
            patch("data.update_manager.sys.exit") as mock_exit,
        ):
            mock_popen.return_value = MagicMock()
            # sys.exit raises SystemExit, so we need to mock it
            mock_exit.side_effect = SystemExit(0)

            # This should succeed and call sys.exit
            with pytest.raises(SystemExit):
                launch_updater(temp_zip)

            # Verify that Popen was called
            assert mock_popen.called
            # Verify that sys.exit was called with 0
            mock_exit.assert_called_once_with(0)

    finally:
        if temp_zip.exists():
            temp_zip.unlink()


def test_launch_updater_passes_correct_arguments():
    """Test that launch_updater passes correct arguments to updater."""
    from data.update_manager import launch_updater
    import os

    # Create a valid ZIP with a mock updater executable
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as f:
        temp_zip = Path(f.name)

    try:
        with zipfile.ZipFile(temp_zip, "w") as zf:
            zf.writestr("BurndownChartUpdater.exe", "mock updater content")

        # Mock subprocess.Popen and sys.exit
        with (
            patch("data.update_manager.subprocess.Popen") as mock_popen,
            patch("data.update_manager.sys.exit") as mock_exit,
            patch("data.update_manager.sys.frozen", False, create=True),
        ):
            mock_popen.return_value = MagicMock()
            mock_exit.side_effect = SystemExit(0)

            # This should succeed and call sys.exit
            with pytest.raises(SystemExit):
                launch_updater(temp_zip)

            # Verify that Popen was called with correct arguments
            assert mock_popen.called
            call_args = mock_popen.call_args[0][0]  # Get positional args list

            # Should have 4 arguments: updater_exe, current_exe, update_zip, pid
            assert len(call_args) == 4
            assert "BurndownChartUpdater.exe" in call_args[0]
            assert str(temp_zip) == call_args[2]
            assert call_args[3] == str(os.getpid())

    finally:
        if temp_zip.exists():
            temp_zip.unlink()


def test_launch_updater_finds_updater_in_subdirectory():
    """Test that launch_updater can find updater.exe in subdirectories."""
    from data.update_manager import launch_updater

    # Create a ZIP with updater in a subdirectory
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as f:
        temp_zip = Path(f.name)

    try:
        with zipfile.ZipFile(temp_zip, "w") as zf:
            # Add updater in a subdirectory
            zf.writestr("subdir/BurndownChartUpdater.exe", "mock updater content")

        # Mock subprocess.Popen and sys.exit
        with (
            patch("data.update_manager.subprocess.Popen") as mock_popen,
            patch("data.update_manager.sys.exit") as mock_exit,
        ):
            mock_popen.return_value = MagicMock()
            mock_exit.side_effect = SystemExit(0)

            # This should succeed even though updater is in subdirectory
            with pytest.raises(SystemExit):
                launch_updater(temp_zip)

            # Verify that Popen was called
            assert mock_popen.called

    finally:
        if temp_zip.exists():
            temp_zip.unlink()
