"""Update system data models, constants, and version utilities.

Defines the UpdateState enum, UpdateProgress dataclass, application constants,
and version comparison functions used across the update system.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from configuration import __version__

logger = logging.getLogger(__name__)

#######################################################################
# CONSTANTS
#######################################################################

# GitHub repository configuration
GITHUB_OWNER = "niksavis"
GITHUB_REPO = "burndown-chart"

# Application identity and executable names
APP_NAME = "Burndown"
MAIN_EXE_NAME = "Burndown.exe"
LEGACY_MAIN_EXE_NAME = "BurndownChart.exe"
UPDATER_EXE_NAME = "BurndownUpdater.exe"
LEGACY_UPDATER_EXE_NAME = "BurndownChartUpdater.exe"
TEMP_UPDATER_PREFIX = "BurndownUpdater-temp-"
WINDOWS_ZIP_PREFIX = "burndown-windows-"
LEGACY_WINDOWS_ZIP_PREFIX = "burndownchart-windows-"

# GitHub API configuration
GITHUB_API_URL = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
UPDATE_CHECK_TIMEOUT = 10  # seconds
DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB chunks

# File size limits
MAX_DOWNLOAD_SIZE = 150 * 1024 * 1024  # 150MB warning threshold (current exe ~102MB)


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
    available_version: str | None = None
    download_url: str | None = None
    download_path: Path | None = None
    progress_percent: int = 0
    error_message: str | None = None
    last_checked: datetime | None = None
    release_notes: str | None = None
    file_size: int | None = None

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
            "last_checked": (
                self.last_checked.isoformat() if self.last_checked else None
            ),
            "release_notes": self.release_notes,
            "file_size": self.file_size,
        }


#######################################################################
# PERSISTENCE HELPERS
#######################################################################


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
