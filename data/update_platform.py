"""Platform detection and update state persistence.

Provides helpers for detecting the execution environment (frozen vs source,
git repo, legacy install) and for persisting/restoring download state across
app restarts.
"""

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

from data.persistence.factory import get_backend
from data.update_models import (
    LEGACY_MAIN_EXE_NAME,
    UpdateProgress,
    UpdateState,
    get_current_version,
)

logger = logging.getLogger(__name__)

#######################################################################
# PERSISTENCE HELPERS
#######################################################################


def _persist_download_state(progress: UpdateProgress) -> None:
    """Persist download state to database for crash recovery.

    Saves download metadata to app_state table so that if the app crashes
    or is closed, the download state can be restored on next startup.

    Args:
        progress: UpdateProgress with completed download information
    """
    try:
        backend = get_backend()
        backend.set_app_state("pending_update_version", progress.available_version)
        backend.set_app_state("pending_update_path", str(progress.download_path))
        backend.set_app_state("pending_update_url", progress.download_url)
        backend.set_app_state(
            "pending_update_checked_at", datetime.now(UTC).isoformat()
        )

        logger.debug(
            "Persisted download state to database",
            extra={
                "operation": "persist_download_state",
                "version": progress.available_version,
                "path": str(progress.download_path),
            },
        )
    except Exception as e:
        # Don't fail download if persistence fails
        logger.warning(f"Failed to persist download state: {e}")


def _restore_download_state() -> UpdateProgress | None:
    """Restore pending update state from database.

    Called during app startup to restore download state if app was closed
    or crashed after download but before installation.

    Returns:
        UpdateProgress if valid pending update found, None otherwise
    """
    try:
        backend = get_backend()
        version = backend.get_app_state("pending_update_version")
        path_str = backend.get_app_state("pending_update_path")
        url = backend.get_app_state("pending_update_url")

        if not version or not path_str:
            return None

        download_path = Path(path_str)

        # Check if file still exists (Windows might have cleaned %TEMP%)
        if download_path.exists():
            logger.info(
                "Restored pending update from database",
                extra={
                    "operation": "restore_download_state",
                    "version": version,
                    "path": str(download_path),
                },
            )

            current_version = get_current_version()
            return UpdateProgress(
                state=UpdateState.READY,
                current_version=current_version,
                available_version=version,
                download_path=download_path,
                download_url=url,
                progress_percent=100,
            )
        else:
            # File deleted - fall back to AVAILABLE state
            logger.warning(
                "Pending update file missing, clearing stale state",
                extra={
                    "operation": "restore_download_state",
                    "version": version,
                    "expected_path": str(download_path),
                },
            )

            # Clear stale download path
            backend.set_app_state("pending_update_path", None)

            # Return AVAILABLE state if we still have the URL
            if url:
                current_version = get_current_version()
                return UpdateProgress(
                    state=UpdateState.AVAILABLE,
                    current_version=current_version,
                    available_version=version,
                    download_url=url,
                )

            return None

    except Exception as e:
        logger.warning(f"Failed to restore download state: {e}")
        return None


def clear_download_state() -> None:
    """Clear persisted download state after successful update.

    Should be called after update installation completes successfully.
    """
    try:
        backend = get_backend()
        backend.set_app_state("pending_update_version", None)
        backend.set_app_state("pending_update_path", None)
        backend.set_app_state("pending_update_url", None)
        backend.set_app_state("pending_update_checked_at", None)

        logger.debug("Cleared download state from database")
    except Exception as e:
        logger.warning(f"Failed to clear download state: {e}")


#######################################################################
# DEPLOYMENT DETECTION
#######################################################################


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


def _is_legacy_install() -> bool:
    """Check if running from a legacy executable name."""
    if not is_frozen():
        return False
    try:
        return Path(sys.executable).name.lower() == LEGACY_MAIN_EXE_NAME.lower()
    except Exception:
        return False


def _find_windows_asset(assets: list[dict], prefix: str) -> dict | None:
    """Find a Windows ZIP asset by name prefix."""
    for asset in assets:
        name = asset.get("name", "")
        lower_name = name.lower()
        if prefix in lower_name and lower_name.endswith(".zip"):
            return asset
    return None


#######################################################################
# CORE FUNCTIONS
#######################################################################
