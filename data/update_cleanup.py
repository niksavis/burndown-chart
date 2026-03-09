"""Cleanup utilities for orphaned temp updater files.

Removes leftover temp updater executables and extraction directories
from previous update sessions on application startup.
"""

import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def cleanup_orphaned_temp_updaters() -> None:
    """Remove orphaned temp updater files from previous sessions.

    Temp updater copies (BurndownUpdater-temp-*.exe) are created during
    updates but cannot delete themselves while running. This function cleans
    up any leftover files from previous update sessions.

    Only deletes files older than 1 hour to avoid interfering with any
    running update process.
    """
    import tempfile  # noqa: PLC0415

    try:
        temp_dir = Path(tempfile.gettempdir())
        cutoff_time = time.time() - (60 * 60)  # 1 hour ago

        # Cleanup temp updater executables
        cleaned_count = 0
        temp_updater_patterns = [
            "BurndownUpdater-temp-*.exe",
            "BurndownChartUpdater-temp-*.exe",  # Legacy name for older releases.
        ]
        for pattern in temp_updater_patterns:
            for temp_updater in temp_dir.glob(pattern):
                try:
                    # Only delete if older than 1 hour (safety margin)
                    if temp_updater.stat().st_mtime < cutoff_time:
                        temp_updater.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up orphaned updater: {temp_updater.name}")
                except (PermissionError, OSError) as e:
                    # File might be in use, skip silently
                    logger.debug(f"Could not delete {temp_updater.name}: {e}")

        # Cleanup orphaned extraction directories (burndown_update_*)
        extract_dir_patterns = ["burndown_update_*", "burndown_chart_update_*"]
        for pattern in extract_dir_patterns:
            for extract_dir in temp_dir.glob(pattern):
                if extract_dir.is_dir():
                    try:
                        # Only delete if older than 1 hour (safety margin)
                        if extract_dir.stat().st_mtime < cutoff_time:
                            import shutil  # noqa: PLC0415

                            shutil.rmtree(extract_dir)
                            cleaned_count += 1
                            logger.info(
                                "Cleaned up orphaned extraction dir: "
                                f"{extract_dir.name}"
                            )
                    except (PermissionError, OSError) as e:
                        # Directory might be in use, skip silently
                        logger.debug(f"Could not delete {extract_dir.name}: {e}")

        if cleaned_count > 0:
            logger.info(
                f"Cleanup complete: removed {cleaned_count} orphaned file(s)/folder(s)"
            )
        else:
            logger.debug("No orphaned temp files found")

    except (OSError, ValueError, TypeError) as e:
        # Don't let cleanup failures block app startup
        logger.warning(f"Temp file cleanup failed: {e}")


# Clean up orphaned temp updaters from previous sessions
