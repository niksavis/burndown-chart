"""Update system startup utilities.

Provides helpers for restoring pending update state on app startup and
launching the background update check thread.
"""

import logging
import threading
from collections.abc import Callable

from data.update_manager import (
    UpdateProgress,
    UpdateState,
    _restore_download_state,
    check_for_updates,
    clear_download_state,
    compare_versions,
)

logger = logging.getLogger(__name__)


def restore_pending_update() -> UpdateProgress | None:
    """Restore pending update state from database.

    If the app was closed or crashed after downloading an update but before
    installation, this restores the download state. Handles graceful fallback
    if temp files were deleted by Windows.

    Also invalidates stale state if current version >= pending version
    (e.g., after manual upgrade or development version bump).

    Returns:
        Restored UpdateProgress or None if nothing to restore.
    """
    try:
        from configuration import __version__

        restored_progress = _restore_download_state()
        if restored_progress:
            # Invalidate stale state if current version >= pending version
            if not restored_progress.available_version:
                logger.warning("Restored state missing available_version, clearing")
                clear_download_state()
                return None

            try:
                comparison = compare_versions(
                    __version__, restored_progress.available_version
                )
                if comparison >= 0:
                    logger.info(
                        "Invalidating stale update state - already at or past "
                        "that version",
                        extra={
                            "operation": "restore_pending_update",
                            "current_version": __version__,
                            "pending_version": restored_progress.available_version,
                        },
                    )
                    clear_download_state()
                    return None
            except Exception as e:
                logger.warning(
                    f"Failed to compare versions, clearing state to be safe: {e}"
                )
                clear_download_state()
                return None

            # Valid pending update - restore state
            logger.info(
                "Restored pending update from previous session",
                extra={
                    "operation": "restore_pending_update",
                    "state": restored_progress.state.value,
                    "version": restored_progress.available_version,
                },
            )
            return restored_progress

        return None

    except Exception as e:
        logger.warning(f"Failed to restore pending update: {e}")
        return None


def start_update_check(
    result_setter: Callable[[UpdateProgress], None],
    current_result: UpdateProgress | None = None,
) -> threading.Thread:
    """Start background update check thread.

    Spawns a daemon thread to query GitHub releases API. Calls result_setter
    with the UpdateProgress result when complete. Skips the check if
    current_result already indicates a pending or available update.

    Args:
        result_setter: Callback invoked with the UpdateProgress result.
        current_result: Current VERSION_CHECK_RESULT to decide whether
            to skip the check.
    """

    def _background() -> None:
        if current_result and current_result.state in (
            UpdateState.READY,
            UpdateState.AVAILABLE,
        ):
            logger.info("Skipping update check - pending update already available")
            return

        try:
            logger.info("Starting background update check")
            result = check_for_updates()
            result_setter(result)
            logger.info(
                "Update check complete",
                extra={
                    "operation": "update_check",
                    "state": result.state.value,
                    "current_version": result.current_version,
                    "available_version": result.available_version,
                },
            )
        except Exception as e:
            logger.error(
                f"Update check failed: {e}",
                exc_info=True,
                extra={"operation": "update_check"},
            )
            result_setter(
                UpdateProgress(
                    state=UpdateState.ERROR,
                    current_version="unknown",
                    error_message=str(e),
                )
            )

    thread = threading.Thread(target=_background, daemon=True, name="UpdateCheckThread")
    thread.start()
    logger.info("Update check thread started")
    return thread
