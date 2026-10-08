import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_launch_updater_file_not_found():
    from data.update_manager import launch_updater

    non_existent_path = Path("/nonexistent/update.zip")

    result = launch_updater(non_existent_path)

    assert result is False


def test_launch_updater_invalid_zip():
    from data.update_manager import launch_updater

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
    from data.update_manager import launch_updater

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
    from data.update_manager import launch_updater

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as f:
        temp_zip = Path(f.name)

    try:
        with zipfile.ZipFile(temp_zip, "w") as zf:
            zf.writestr("BurndownUpdater.exe", "mock updater content")

        with (
            patch("data.update_delivery.subprocess.Popen") as mock_popen,
            patch("data.update_delivery.os._exit") as mock_exit,
        ):
            mock_popen.return_value = MagicMock()
            mock_exit.side_effect = SystemExit(0)

            with pytest.raises(SystemExit):
                launch_updater(temp_zip)

            assert mock_popen.called
            mock_exit.assert_called_once_with(0)

    finally:
        if temp_zip.exists():
            temp_zip.unlink()


def test_launch_updater_passes_correct_arguments():
    import os

    from data.update_manager import launch_updater

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as f:
        temp_zip = Path(f.name)

    try:
        with zipfile.ZipFile(temp_zip, "w") as zf:
            zf.writestr("BurndownUpdater.exe", "mock updater content")

        with (
            patch("data.update_delivery.subprocess.Popen") as mock_popen,
            patch("data.update_delivery.os._exit") as mock_exit,
            patch("data.update_delivery.sys.frozen", False, create=True),
            patch("data.update_delivery.shutil.copy2", side_effect=OSError("test")),
        ):
            mock_popen.return_value = MagicMock()
            mock_exit.side_effect = SystemExit(0)

            with pytest.raises(SystemExit):
                launch_updater(temp_zip)

            assert mock_popen.called
            call_args = mock_popen.call_args[0][0]

            assert len(call_args) == 4
            assert "BurndownUpdater.exe" in call_args[0]
            assert str(temp_zip) == call_args[2]
            assert call_args[3] == str(os.getpid())

    finally:
        if temp_zip.exists():
            temp_zip.unlink()


def test_launch_updater_finds_updater_in_subdirectory():
    from data.update_manager import launch_updater

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as f:
        temp_zip = Path(f.name)

    try:
        with zipfile.ZipFile(temp_zip, "w") as zf:
            zf.writestr("subdir/BurndownUpdater.exe", "mock updater content")

        with (
            patch("data.update_delivery.subprocess.Popen") as mock_popen,
            patch("data.update_delivery.os._exit") as mock_exit,
        ):
            mock_popen.return_value = MagicMock()
            mock_exit.side_effect = SystemExit(0)

            with pytest.raises(SystemExit):
                launch_updater(temp_zip)

            assert mock_popen.called

    finally:
        if temp_zip.exists():
            temp_zip.unlink()
