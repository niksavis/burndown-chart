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
    UPDATE_CHECK_TIMEOUT_SECONDS,
    UPDATER_EXE_NAME,
    UpdateProgress,
    UpdateState,
)
from data.update_platform import _persist_download_state

logger = logging.getLogger(__name__)


def download_update(progress: UpdateProgress) -> UpdateProgress:

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
        temp_dir = Path(tempfile.gettempdir()) / "burndown_updates"
        temp_dir.mkdir(parents=True, exist_ok=True)

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

        response = requests.get(
            progress.download_url,
            stream=True,
            timeout=UPDATE_CHECK_TIMEOUT_SECONDS,
            headers={
                "User-Agent": f"{APP_NAME}/{progress.current_version}",
            },
        )

        response.raise_for_status()

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

        downloaded_size = 0

        with open(download_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    if total_size > 0:
                        progress.progress_percent = int(
                            (downloaded_size / total_size) * 100
                        )

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

    for name in names:
        direct_path = extract_dir / name
        if direct_path.exists():
            return direct_path
        matches = list(extract_dir.glob(f"**/{name}"))
        if matches:
            return matches[0]
    return None


def launch_updater(update_path: Path) -> bool:

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

        with zipfile.ZipFile(update_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

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

        if getattr(sys, "frozen", False):
            current_exe = Path(sys.executable)
            current_updater_exe = current_exe.parent / UPDATER_EXE_NAME
            if not current_updater_exe.exists():
                current_updater_exe = current_exe.parent / LEGACY_UPDATER_EXE_NAME
        else:
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
            temp_updater_path = updater_exe
            logger.warning(
                "Falling back to original updater - updater will not self-update"
            )

        args = [
            str(temp_updater_path),
            str(current_exe),
            str(update_path),
            str(os.getpid()),
        ]

        if temp_updater_path != updater_exe:
            args.extend(["--updater-exe", str(current_updater_exe)])
            logger.info(
                "Self-update enabled: temp updater will replace both executables"
            )
        else:
            logger.info("Self-update disabled: only app will be updated")

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

        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(
                args,
                creationflags=DETACHED_PROCESS,
                stdout=updater_log_file,
                stderr=updater_log_file,
            )
        else:
            subprocess.Popen(
                args,
                stdout=updater_log_file,
                stderr=updater_log_file,
                start_new_session=True,
            )

        if not isinstance(updater_log_file, int):
            updater_log_file.close()

        logger.info(
            "Updater launched successfully - application will exit",
            extra={"operation": "launch_updater"},
        )

        logger.info("Forcing immediate application exit for update...")
        os._exit(0)

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
