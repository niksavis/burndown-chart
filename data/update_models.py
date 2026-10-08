import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from configuration import __version__

logger = logging.getLogger(__name__)


GITHUB_OWNER = "niksavis"
GITHUB_REPO = "burndown-chart"

APP_NAME = "Burndown"
MAIN_EXE_NAME = "Burndown.exe"
LEGACY_MAIN_EXE_NAME = "BurndownChart.exe"
UPDATER_EXE_NAME = "BurndownUpdater.exe"
LEGACY_UPDATER_EXE_NAME = "BurndownChartUpdater.exe"
TEMP_UPDATER_PREFIX = "BurndownUpdater-temp-"
WINDOWS_ZIP_PREFIX = "burndown-windows-"
LEGACY_WINDOWS_ZIP_PREFIX = "burndownchart-windows-"

GITHUB_API_URL = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
UPDATE_CHECK_TIMEOUT_SECONDS = 10
DOWNLOAD_CHUNK_SIZE = 1024 * 1024

MAX_DOWNLOAD_SIZE = 150 * 1024 * 1024


class UpdateState(Enum):
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


def get_current_version() -> str:

    return __version__


def compare_versions(current: str, available: str) -> int:

    try:
        current_clean = current.lstrip("v").split("-")[0]
        available_clean = available.lstrip("v").split("-")[0]

        current_parts = tuple(int(x) for x in current_clean.split("."))
        available_parts = tuple(int(x) for x in available_clean.split("."))

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
