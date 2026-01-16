"""
Update Manager for Standalone Executable

This module handles checking for updates, downloading new versions, and launching
the updater executable to replace the running application.

Architecture:
- UpdateState: Enum tracking update lifecycle
- UpdateProgress: Dataclass with current state and metadata
- check_for_updates(): Query GitHub releases API
- download_update(): Download ZIP from GitHub
- launch_updater(): Extract and launch updater executable

Update Flow:
    IDLE → CHECKING → AVAILABLE → DOWNLOADING → READY → INSTALLING → IDLE

    At any stage, ERROR can occur and transition back to IDLE.
    UP_TO_DATE is terminal state until next check.

Constants:
    GITHUB_API_URL: GitHub releases API endpoint
    UPDATE_CHECK_TIMEOUT: Timeout for API requests (seconds)
    DOWNLOAD_CHUNK_SIZE: Size of download chunks (bytes)

Functions:
    check_for_updates() -> UpdateProgress: Check for available updates
    download_update(progress: UpdateProgress) -> UpdateProgress: Download update ZIP
    launch_updater(update_path: Path) -> bool: Launch updater and exit app
    get_current_version() -> str: Get current app version
    compare_versions(current: str, available: str) -> int: Compare semantic versions

Usage:
    # Background thread in app.py
    progress = check_for_updates()
    if progress.state == UpdateState.AVAILABLE:
        # Show notification to user
        # On user action:
        progress = download_update(progress)
        if progress.state == UpdateState.READY:
            launch_updater(progress.download_path)
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import logging
import os
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

# Third-party library imports
import requests

# Application imports
from configuration import __version__

#######################################################################
# CONSTANTS
#######################################################################

# GitHub repository configuration
GITHUB_OWNER = "niksavis"  # Repository owner
GITHUB_REPO = "burndown-chart"  # Repository name

# GitHub API configuration
GITHUB_API_URL = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
UPDATE_CHECK_TIMEOUT = 10  # seconds
DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB chunks

# File size limits
MAX_DOWNLOAD_SIZE = 150 * 1024 * 1024  # 150MB warning threshold (current exe ~102MB)

#######################################################################
# LOGGING
#######################################################################

logger = logging.getLogger(__name__)

#######################################################################
# DATA CLASSES
#######################################################################


class UpdateState(Enum):
    """Update lifecycle states.

    Represents the current stage of update checking, downloading, and installation.

    States:
        IDLE: No update activity
        CHECKING: Querying GitHub API for latest release
        AVAILABLE: Update found, ready to download
        DOWNLOADING: Downloading update ZIP from GitHub
        READY: Downloaded successfully, ready to install
        INSTALLING: Updater launched, app will exit
        ERROR: Download or installation failed
        UP_TO_DATE: No update needed (current version is latest)
        MANUAL_UPDATE_REQUIRED: Running from source, manual update needed
    """

    IDLE = "idle"
    CHECKING = "checking"
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    READY = "ready"
    INSTALLING = "installing"
    ERROR = "error"
    UP_TO_DATE = "up_to_date"
    MANUAL_UPDATE_REQUIRED = "manual_update_required"


@dataclass
class UpdateProgress:
    """Update progress tracking.

    Tracks the current state of update checking and downloading, with metadata
    for displaying progress to the user.

    Attributes:
        state: Current update state
        current_version: Version string of running application
        available_version: Version string of available update (if any)
        download_url: URL to download update ZIP (if available)
        download_path: Local path where update ZIP is saved (if downloaded)
        progress_percent: Download progress (0-100)
        error_message: Human-readable error description (if state == ERROR)
        last_checked: Timestamp of last update check
        release_notes: Markdown release notes from GitHub (if available)
        file_size: Size of download in bytes (if available)
    """

    state: UpdateState
    current_version: str
    available_version: Optional[str] = None
    download_url: Optional[str] = None
    download_path: Optional[Path] = None
    progress_percent: int = 0
    error_message: Optional[str] = None
    last_checked: Optional[datetime] = None
    release_notes: Optional[str] = None
    file_size: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of update progress
        """
        return {
            "state": self.state.value,
            "current_version": self.current_version,
            "available_version": self.available_version,
            "download_url": self.download_url,
            "download_path": str(self.download_path) if self.download_path else None,
            "progress_percent": self.progress_percent,
            "error_message": self.error_message,
            "last_checked": self.last_checked.isoformat()
            if self.last_checked
            else None,
            "release_notes": self.release_notes,
            "file_size": self.file_size,
        }


#######################################################################
# DEPLOYMENT DETECTION
#######################################################################


def is_frozen() -> bool:
    """Check if running as frozen executable (PyInstaller).

    Returns:
        True if running as executable, False if running from source
    """
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_deployment_type() -> str:
    """Get deployment type for logging and user guidance.

    Returns:
        "executable" if frozen, "source" if running from Python
    """
    return "executable" if is_frozen() else "source"


def is_git_repository() -> bool:
    """Check if running from a git repository (for developers).

    Returns:
        True if .git directory exists
    """
    try:
        if is_frozen():
            return False
        # Check for .git in current directory or parents
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return True
            current = current.parent
        return False
    except Exception:
        return False


#######################################################################
# CORE FUNCTIONS
#######################################################################


def get_current_version() -> str:
    """Get current application version.

    Reads version from configuration module.

    Returns:
        Version string in format "X.Y.Z"
    """
    return __version__


def compare_versions(current: str, available: str) -> int:
    """Compare two semantic version strings.

    Args:
        current: Current version string (e.g., "2.5.0")
        available: Available version string (e.g., "2.6.0")

    Returns:
        -1 if current < available (update available)
         0 if current == available (same version)
         1 if current > available (current is newer)

    Raises:
        ValueError: If version strings are not valid semantic versions
    """
    try:
        # Strip 'v' prefix and any suffix after hyphen (e.g., '-test', '-rc1', '-beta')
        current_clean = current.lstrip("v").split("-")[0]
        available_clean = available.lstrip("v").split("-")[0]

        current_parts = tuple(int(x) for x in current_clean.split("."))
        available_parts = tuple(int(x) for x in available_clean.split("."))

        # Validate version format (must be X.Y.Z)
        if len(current_parts) != 3 or len(available_parts) != 3:
            raise ValueError("Version must have exactly 3 parts (X.Y.Z)")

        if current_parts < available_parts:
            return -1
        elif current_parts > available_parts:
            return 1
        else:
            return 0
    except (ValueError, AttributeError) as e:
        logger.error(
            "Invalid version format",
            extra={
                "operation": "compare_versions",
                "current": current,
                "available": available,
                "error": str(e),
            },
        )
        raise ValueError(
            f"Invalid version format: current={current}, available={available}"
        ) from e


def check_for_updates() -> UpdateProgress:
    """Check for available updates from GitHub releases.

    Queries the GitHub releases API for the latest version. Compares with current
    version using semantic versioning. Non-blocking operation with timeout.

    For source code deployments (non-frozen), returns MANUAL_UPDATE_REQUIRED state
    with guidance on how to update.

    Returns:
        UpdateProgress with state AVAILABLE, UP_TO_DATE, MANUAL_UPDATE_REQUIRED, or ERROR

    Note:
        This function should be called from a background thread to avoid blocking
        the UI. Network errors are caught and returned as ERROR state.
    """
    current_version = get_current_version()
    deployment_type = get_deployment_type()
    is_git_repo = is_git_repository()

    logger.info(
        "Starting update check",
        extra={
            "operation": "check_for_updates",
            "current_version": current_version,
            "deployment_type": deployment_type,
            "is_git_repo": is_git_repo,
        },
    )

    progress = UpdateProgress(
        state=UpdateState.CHECKING,
        current_version=current_version,
        last_checked=datetime.now(),
    )

    try:
        # Query GitHub releases API
        api_url = GITHUB_API_URL.format(owner=GITHUB_OWNER, repo=GITHUB_REPO)

        logger.debug(
            "Querying GitHub releases API",
            extra={"operation": "check_for_updates", "url": api_url},
        )

        response = requests.get(
            api_url,
            timeout=UPDATE_CHECK_TIMEOUT,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"BurndownChart/{current_version}",
            },
        )

        # Check for HTTP errors
        response.raise_for_status()

        release_data = response.json()

        # Extract version information
        tag_name = release_data.get("tag_name", "")
        available_version = tag_name.lstrip("v")  # Remove 'v' prefix if present

        logger.info(
            "GitHub API query successful",
            extra={
                "operation": "check_for_updates",
                "available_version": available_version,
                "prerelease": release_data.get("prerelease", False),
            },
        )

        # Skip prereleases
        if release_data.get("prerelease", False):
            logger.info(
                "Skipping prerelease version",
                extra={"operation": "check_for_updates", "version": available_version},
            )
            progress.state = UpdateState.UP_TO_DATE
            return progress

        # Compare versions
        version_comparison = compare_versions(current_version, available_version)

        if version_comparison < 0:
            # Update available
            logger.info(
                "Update available",
                extra={
                    "operation": "check_for_updates",
                    "current": current_version,
                    "available": available_version,
                    "deployment_type": deployment_type,
                },
            )

            # Check if running from source (not frozen executable)
            if not is_frozen():
                logger.info(
                    "Running from source - manual update required",
                    extra={
                        "operation": "check_for_updates",
                        "is_git_repo": is_git_repo,
                    },
                )

                # Provide appropriate guidance based on deployment type
                if is_git_repo:
                    update_instructions = (
                        "You are running from a git repository. To update:\n\n"
                        "1. Save your work and close the app\n"
                        "2. Run: git pull\n"
                        "3. Run: pip install -r requirements.txt\n"
                        "4. Restart the app"
                    )
                else:
                    update_instructions = (
                        "You are running from source code. To update:\n\n"
                        "1. Download the new source code ZIP from GitHub releases\n"
                        "2. Extract and replace the existing files\n"
                        "3. Run: pip install -r requirements.txt\n"
                        "4. Restart the app\n\n"
                        f"Download from: https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/tag/v{available_version}"
                    )

                progress.state = UpdateState.MANUAL_UPDATE_REQUIRED
                progress.available_version = available_version
                progress.release_notes = update_instructions
                progress.error_message = update_instructions  # For compatibility
                return progress

            # Find Windows ZIP asset (only for executable mode)
            assets = release_data.get("assets", [])
            windows_asset = None

            for asset in assets:
                asset_name = asset.get("name", "")
                if "windows" in asset_name.lower() and asset_name.endswith(".zip"):
                    windows_asset = asset
                    break

            if not windows_asset:
                logger.warning(
                    "No Windows ZIP asset found in release",
                    extra={
                        "operation": "check_for_updates",
                        "version": available_version,
                        "assets": [a.get("name") for a in assets],
                    },
                )
                progress.state = UpdateState.ERROR
                progress.error_message = (
                    f"No Windows installer found for version {available_version}"
                )
                return progress

            # Update progress with available version info
            progress.state = UpdateState.AVAILABLE
            progress.available_version = available_version
            progress.download_url = windows_asset.get("browser_download_url")
            progress.file_size = windows_asset.get("size")
            progress.release_notes = release_data.get("body", "")

            return progress

        else:
            # Up to date or current is newer
            logger.info(
                "App is up to date",
                extra={
                    "operation": "check_for_updates",
                    "current": current_version,
                    "latest": available_version,
                },
            )
            progress.state = UpdateState.UP_TO_DATE
            return progress

    except requests.exceptions.Timeout:
        logger.warning(
            "GitHub API request timed out",
            extra={"operation": "check_for_updates", "timeout": UPDATE_CHECK_TIMEOUT},
        )
        progress.state = UpdateState.ERROR
        progress.error_message = f"Update check timed out after {UPDATE_CHECK_TIMEOUT}s"
        return progress

    except requests.exceptions.HTTPError as e:
        # HTTP errors (4xx, 5xx)
        status_code = e.response.status_code if e.response else "unknown"
        logger.warning(
            "GitHub API HTTP error",
            extra={
                "operation": "check_for_updates",
                "status_code": status_code,
                "error": str(e),
            },
        )
        progress.state = UpdateState.ERROR
        progress.error_message = f"Update check failed (HTTP {status_code})"
        return progress

    except requests.exceptions.ConnectionError as e:
        # Network connectivity issues
        logger.info(
            "Cannot connect to GitHub API (network offline or unavailable)",
            extra={"operation": "check_for_updates", "error": str(e)},
        )
        progress.state = UpdateState.ERROR
        progress.error_message = "No network connection available"
        return progress

    except requests.exceptions.RequestException as e:
        # Other request errors
        logger.warning(
            "GitHub API request failed",
            extra={
                "operation": "check_for_updates",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress.state = UpdateState.ERROR
        progress.error_message = f"Failed to check for updates: {str(e)}"
        return progress

    except (ValueError, KeyError) as e:
        logger.error(
            "Failed to parse GitHub API response",
            extra={
                "operation": "check_for_updates",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress.state = UpdateState.ERROR
        progress.error_message = f"Invalid update data: {str(e)}"
        return progress


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
    download_path: Optional[Path] = None

    try:
        # Create temporary file for download
        temp_dir = Path(tempfile.gettempdir()) / "burndown_updates"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from version
        filename = f"burndown-chart-v{progress.available_version}.zip"
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
                "User-Agent": f"BurndownChart/{progress.current_version}",
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
            progress.error_message = f"Download incomplete: expected {total_size} bytes, got {downloaded_size}"
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
        # Create temporary extraction directory
        extract_dir = Path(tempfile.gettempdir()) / "burndown_updater"
        extract_dir.mkdir(parents=True, exist_ok=True)

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

        # Find updater executable
        updater_exe = extract_dir / "BurndownChartUpdater.exe"

        if not updater_exe.exists():
            # Try alternate location (might be in subdirectory)
            possible_paths = list(extract_dir.glob("**/BurndownChartUpdater.exe"))
            if possible_paths:
                updater_exe = possible_paths[0]
            else:
                logger.error(
                    "Updater executable not found in ZIP",
                    extra={
                        "operation": "launch_updater",
                        "extract_dir": str(extract_dir),
                        "files": [str(p) for p in extract_dir.rglob("*")],
                    },
                )
                return False

        logger.info(
            "Found updater executable",
            extra={"operation": "launch_updater", "updater_path": str(updater_exe)},
        )

        # Get current executable path
        if getattr(sys, "frozen", False):
            # Running as frozen executable
            current_exe = Path(sys.executable)
        else:
            # Running as script - use placeholder
            # In dev mode, updater won't actually work, but we can test the logic
            current_exe = Path(__file__).parent.parent / "BurndownChart.exe"
            logger.warning(
                "Running in development mode - updater may not work correctly",
                extra={"operation": "launch_updater"},
            )

        logger.info(
            "Preparing to launch updater",
            extra={
                "operation": "launch_updater",
                "current_exe": str(current_exe),
                "update_zip": str(update_path),
            },
        )

        # Launch updater with arguments:
        # 1. Path to current executable (to be replaced)
        # 2. Path to update ZIP (contains new version)
        # 3. Process ID (so updater can wait for app to exit)
        args = [
            str(updater_exe),
            str(current_exe),
            str(update_path),
            str(os.getpid()),
        ]

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
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            # Unix-like systems
            subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        logger.info(
            "Updater launched successfully - application will exit",
            extra={"operation": "launch_updater"},
        )

        # Exit the application to allow updater to replace files
        # The updater will restart the app after update completes
        sys.exit(0)

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
