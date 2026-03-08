"""Update download and installation delivery.

Handles downloading the update ZIP from GitHub, extracting the updater
executable, and launching it to replace the running application.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path

import requests

from data.update_models import (
    APP_NAME,
    DOWNLOAD_CHUNK_SIZE,
    LEGACY_MAIN_EXE_NAME,
    LEGACY_UPDATER_EXE_NAME,
    MAIN_EXE_NAME,
    MAX_DOWNLOAD_SIZE,
    TEMP_UPDATER_PREFIX,
    UPDATE_CHECK_TIMEOUT,
    UPDATER_EXE_NAME,
    UpdateProgress,
    UpdateState,
)
from data.update_platform import _persist_download_state

logger = logging.getLogger(__name__)


def download_update(progress: UpdateProgress) -> UpdateProgress:
    """Download update ZIP from GitHub.

    Downloads the update ZIP file and tracks progress. Updates the progress object
    with download percentage and file path.

    Args:
        progress: UpdateProgress with state AVAILABLE and download_url set

    Returns:
        UpdateProgress with state READY or ERROR

    Raises:
        ValueError: If progress.state is not AVAILABLE or download_url is None
    """
    if progress.state != UpdateState.AVAILABLE:
        raise ValueError(f"Cannot download update in state {progress.state}")

    if not progress.download_url:
        raise ValueError("download_url is required for downloading update")

    logger.info(
        "Starting update download",
        extra={
            "operation": "download_update",
            "url": progress.download_url,
            "version": progress.available_version,
        },
    )

    progress.state = UpdateState.DOWNLOADING
    progress.progress_percent = 0
    download_path: Path | None = None

    try:
        # Create temporary file for download
        temp_dir = Path(tempfile.gettempdir()) / "burndown_updates"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Extract filename from download URL to preserve actual asset name
        # URL format: https://github.com/.../releases/download/v2.5.4-test/Burndown-Windows-2.5.4.zip
        filename = progress.download_url.split("/")[-1]
        download_path = temp_dir / filename

        logger.debug(
            "Downloading to temp location",
            extra={
                "operation": "download_update",
                "path": str(download_path),
                "url": progress.download_url,
            },
        )

        # Stream download with progress tracking
        response = requests.get(
            progress.download_url,
            stream=True,
            timeout=UPDATE_CHECK_TIMEOUT,
            headers={
                "User-Agent": f"{APP_NAME}/{progress.current_version}",
            },
        )

        response.raise_for_status()

        # Get total file size
        total_size = int(response.headers.get("content-length", 0))

        if total_size > MAX_DOWNLOAD_SIZE:
            logger.warning(
                "Large update file detected",
                extra={
                    "operation": "download_update",
                    "size_mb": total_size / (1024 * 1024),
                    "threshold_mb": MAX_DOWNLOAD_SIZE / (1024 * 1024),
                },
            )

        # Download with progress tracking
        downloaded_size = 0

        with open(download_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # Update progress percentage
                    if total_size > 0:
                        progress.progress_percent = int(
                            (downloaded_size / total_size) * 100
                        )

                        # Log progress at 25% intervals
                        if (
                            progress.progress_percent % 25 == 0
                            and downloaded_size > DOWNLOAD_CHUNK_SIZE
                        ):
                            logger.info(
                                "Download progress",
                                extra={
                                    "operation": "download_update",
                                    "progress": progress.progress_percent,
                                    "downloaded_mb": downloaded_size / (1024 * 1024),
                                    "total_mb": total_size / (1024 * 1024),
                                },
                            )

        # Verify download completed
        if total_size > 0 and downloaded_size != total_size:
            logger.error(
                "Download incomplete",
                extra={
                    "operation": "download_update",
                    "expected": total_size,
                    "received": downloaded_size,
                },
            )
            progress.state = UpdateState.ERROR
            progress.error_message = (
                "Download incomplete: "
                f"expected {total_size} bytes, got {downloaded_size}"
            )
            return progress

        logger.info(
            "Download completed successfully",
            extra={
                "operation": "download_update",
                "path": str(download_path),
                "size_mb": downloaded_size / (1024 * 1024),
            },
        )

        progress.state = UpdateState.READY
        progress.download_path = download_path
        progress.progress_percent = 100

        # Persist download state to database for crash recovery
        _persist_download_state(progress)

        return progress

    except requests.exceptions.Timeout:
        logger.warning(
            "Download timed out",
            extra={
                "operation": "download_update",
                "url": progress.download_url,
            },
        )
        progress.state = UpdateState.ERROR
        progress.error_message = "Download timed out"
        return progress

    except requests.exceptions.RequestException as e:
        logger.error(
            "Download failed",
            extra={
                "operation": "download_update",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress.state = UpdateState.ERROR
        progress.error_message = f"Download failed: {str(e)}"
        return progress

    except OSError as e:
        logger.error(
            "Failed to write download file",
            extra={
                "operation": "download_update",
                "error": str(e),
                "path": str(download_path) if download_path else None,
            },
        )
        progress.state = UpdateState.ERROR
        progress.error_message = f"Failed to save update file: {str(e)}"
        return progress


def _find_executable_in_extract(
    extract_dir: Path,
    names: list[str],
) -> Path | None:
    """Find a matching executable in an extracted update directory.

    Args:
        extract_dir: Directory containing extracted update files.
        names: Candidate executable names to search for.

    Returns:
        Path to the first matching executable, or None if not found.
    """
    for name in names:
        direct_path = extract_dir / name
        if direct_path.exists():
            return direct_path
        matches = list(extract_dir.glob(f"**/{name}"))
        if matches:
            return matches[0]
    return None


def launch_updater(update_path: Path) -> bool:
    """Launch updater executable and exit application.

    Extracts the updater from the ZIP, launches it with appropriate arguments,
    and exits the current application to allow file replacement.

    Args:
        update_path: Path to downloaded update ZIP file

    Returns:
        True if updater was launched successfully, False otherwise

    Note:
        This function will terminate the application if successful. The updater
        will replace the running executable and restart the application.
    """
    if not update_path.exists():
        logger.error(
            "Update file not found",
            extra={"operation": "launch_updater", "path": str(update_path)},
        )
        return False

    logger.info(
        "Launching updater",
        extra={"operation": "launch_updater", "update_path": str(update_path)},
    )

    try:
        # Create directory for updater if needed
        updater_dir = Path(tempfile.gettempdir()) / "burndown_updater"
        updater_dir.mkdir(parents=True, exist_ok=True)
        extract_dir = updater_dir

        logger.debug(
            "Extracting updater ZIP",
            extra={
                "operation": "launch_updater",
                "zip_path": str(update_path),
                "extract_dir": str(extract_dir),
            },
        )

        # Extract ZIP file
        with zipfile.ZipFile(update_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find updater executable (prefer new name, fallback to legacy)
        updater_exe = _find_executable_in_extract(
            extract_dir,
            [UPDATER_EXE_NAME, LEGACY_UPDATER_EXE_NAME],
        )

        if not updater_exe:
            logger.error(
                "Updater executable not found in ZIP",
                extra={
                    "operation": "launch_updater",
                    "extract_dir": str(extract_dir),
                    "files": [str(p) for p in extract_dir.rglob("*")],
                    "expected_names": [UPDATER_EXE_NAME, LEGACY_UPDATER_EXE_NAME],
                },
            )
            return False

        logger.info(
            "Found updater executable",
            extra={"operation": "launch_updater", "updater_path": str(updater_exe)},
        )

        # Get current executable paths
        if getattr(sys, "frozen", False):
            # Running as frozen executable
            current_exe = Path(sys.executable)
            # Find current updater executable (same directory as app)
            current_updater_exe = current_exe.parent / UPDATER_EXE_NAME
            if not current_updater_exe.exists():
                current_updater_exe = current_exe.parent / LEGACY_UPDATER_EXE_NAME
        else:
            # Running as script - use placeholder
            # In dev mode, updater won't actually work, but we can test the logic
            project_root = Path(__file__).parent.parent
            current_exe = project_root / MAIN_EXE_NAME
            if not current_exe.exists():
                current_exe = project_root / LEGACY_MAIN_EXE_NAME
            current_updater_exe = project_root / UPDATER_EXE_NAME
            if not current_updater_exe.exists():
                current_updater_exe = project_root / LEGACY_UPDATER_EXE_NAME
            logger.warning(
                "Running in development mode - updater may not work correctly",
                extra={"operation": "launch_updater"},
            )

        logger.info(
            "Preparing to launch updater",
            extra={
                "operation": "launch_updater",
                "current_exe": str(current_exe),
                "current_updater": str(current_updater_exe),
                "update_zip": str(update_path),
            },
        )

        # SELF-UPDATING MECHANISM:
        # Copy NEW updater to temp location with unique name
        # This temp copy will replace BOTH executables, then self-terminate
        temp_updater_name = f"{TEMP_UPDATER_PREFIX}{uuid.uuid4().hex[:8]}.exe"
        temp_updater_path = Path(tempfile.gettempdir()) / temp_updater_name

        logger.info(
            "Creating temporary updater copy for self-update",
            extra={
                "operation": "launch_updater",
                "source": str(updater_exe),
                "temp_copy": str(temp_updater_path),
            },
        )

        try:
            shutil.copy2(updater_exe, temp_updater_path)
        except Exception as e:
            logger.error(
                "Failed to create temporary updater copy",
                extra={
                    "operation": "launch_updater",
                    "error": str(e),
                },
            )
            # Fall back to original updater (won't update itself, but app will update)
            temp_updater_path = updater_exe
            logger.warning(
                "Falling back to original updater - updater will not self-update"
            )

        # Launch temp updater with arguments:
        # 1. Path to current app executable (to be replaced)
        # 2. Path to update ZIP (contains new versions)
        # 3. Process ID (so updater can wait for app to exit)
        # 4. --updater-exe flag with path to current updater (for self-update)
        args = [
            str(temp_updater_path),
            str(current_exe),
            str(update_path),
            str(os.getpid()),
        ]

        # Add self-update flag if we successfully created temp copy
        if temp_updater_path != updater_exe:
            args.extend(["--updater-exe", str(current_updater_exe)])
            logger.info(
                "Self-update enabled: temp updater will replace both executables"
            )
        else:
            logger.info("Self-update disabled: only app will be updated")

        # Create log file for updater output (for debugging update failures)
        updater_log_path = Path(tempfile.gettempdir()) / "burndown_updater.log"
        try:
            updater_log_file = open(updater_log_path, "w", encoding="utf-8")
            logger.info(
                "Updater output will be logged to file",
                extra={
                    "operation": "launch_updater",
                    "log_path": str(updater_log_path),
                },
            )
        except Exception as e:
            logger.warning(
                "Failed to create updater log file",
                extra={"operation": "launch_updater", "error": str(e)},
            )
            updater_log_file = subprocess.DEVNULL

        logger.info(
            "Launching updater process",
            extra={"operation": "launch_updater", "command_args": args},
        )

        # Launch updater as detached process
        # Use DETACHED_PROCESS on Windows to prevent console window
        if sys.platform == "win32":
            # Windows-specific: detached process
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(
                args,
                creationflags=DETACHED_PROCESS,
                stdout=updater_log_file,
                stderr=updater_log_file,
            )
        else:
            # Unix-like systems
            subprocess.Popen(
                args,
                stdout=updater_log_file,
                stderr=updater_log_file,
                start_new_session=True,
            )

        # Close parent's fd - subprocess has its own copy
        if not isinstance(updater_log_file, int):
            updater_log_file.close()

        logger.info(
            "Updater launched successfully - application will exit",
            extra={"operation": "launch_updater"},
        )

        # Force immediate exit to allow updater to replace files
        # The updater will restart the app after update completes
        # Use os._exit() to bypass all cleanup and exit immediately
        logger.info("Forcing immediate application exit for update...")
        os._exit(0)  # Immediate termination, no cleanup

        # This line should never be reached
        return True

    except zipfile.BadZipFile as e:
        logger.error(
            "Invalid ZIP file",
            extra={
                "operation": "launch_updater",
                "error": str(e),
                "path": str(update_path),
            },
        )
        return False

    except OSError as e:
        logger.error(
            "Failed to extract or launch updater",
            extra={
                "operation": "launch_updater",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        return False

    except Exception as e:
        logger.error(
            "Unexpected error launching updater",
            exc_info=True,
            extra={
                "operation": "launch_updater",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        return False
