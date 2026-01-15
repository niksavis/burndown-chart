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
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

# Third-party library imports
# None yet (will add requests for GitHub API)

# Application imports
from configuration import __version__

#######################################################################
# CONSTANTS
#######################################################################

# GitHub API configuration
GITHUB_API_URL = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
UPDATE_CHECK_TIMEOUT = 10  # seconds
DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB chunks

# File size limits
MAX_DOWNLOAD_SIZE = 100 * 1024 * 1024  # 100MB warning threshold

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
    """

    IDLE = "idle"
    CHECKING = "checking"
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    READY = "ready"
    INSTALLING = "installing"
    ERROR = "error"
    UP_TO_DATE = "up_to_date"


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
        current_parts = tuple(int(x) for x in current.lstrip("v").split("."))
        available_parts = tuple(int(x) for x in available.lstrip("v").split("."))

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

    Returns:
        UpdateProgress with state AVAILABLE, UP_TO_DATE, or ERROR

    Note:
        This function should be called from a background thread to avoid blocking
        the UI. Network errors are caught and returned as ERROR state.
    """
    current_version = get_current_version()

    logger.info(
        "Starting update check",
        extra={"operation": "check_for_updates", "current_version": current_version},
    )

    progress = UpdateProgress(
        state=UpdateState.CHECKING,
        current_version=current_version,
        last_checked=datetime.now(),
    )

    # TODO: Implement GitHub API query (task t-043)
    # For now, return UP_TO_DATE as placeholder
    logger.info(
        "Update check placeholder - not yet implemented",
        extra={"operation": "check_for_updates", "state": "up_to_date"},
    )

    progress.state = UpdateState.UP_TO_DATE
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

    # TODO: Implement download with progress tracking (task t-045, t-046)
    # For now, return ERROR as placeholder
    logger.warning(
        "Update download placeholder - not yet implemented",
        extra={"operation": "download_update"},
    )

    progress.state = UpdateState.ERROR
    progress.error_message = "Download functionality not yet implemented"
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

    # TODO: Implement updater extraction and launch (task t-051)
    # For now, return False as placeholder
    logger.warning(
        "Updater launch placeholder - not yet implemented",
        extra={"operation": "launch_updater"},
    )

    return False
