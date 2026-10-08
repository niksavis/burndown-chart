import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def cleanup_orphaned_temp_updaters() -> None:

    import tempfile  # noqa: PLC0415

    try:
        temp_dir = Path(tempfile.gettempdir())
        cutoff_time = time.time() - (60 * 60)

        cleaned_count = 0
        temp_updater_patterns = [
            "BurndownUpdater-temp-*.exe",
            "BurndownChartUpdater-temp-*.exe",
        ]
        for pattern in temp_updater_patterns:
            for temp_updater in temp_dir.glob(pattern):
                try:
                    if temp_updater.stat().st_mtime < cutoff_time:
                        temp_updater.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up orphaned updater: {temp_updater.name}")
                except (PermissionError, OSError) as e:
                    logger.debug(f"Could not delete {temp_updater.name}: {e}")

        extract_dir_patterns = ["burndown_update_*", "burndown_chart_update_*"]
        for pattern in extract_dir_patterns:
            for extract_dir in temp_dir.glob(pattern):
                if extract_dir.is_dir():
                    try:
                        if extract_dir.stat().st_mtime < cutoff_time:
                            import shutil  # noqa: PLC0415

                            shutil.rmtree(extract_dir)
                            cleaned_count += 1
                            logger.info(
                                "Cleaned up orphaned extraction dir: "
                                f"{extract_dir.name}"
                            )
                    except (PermissionError, OSError) as e:
                        logger.debug(f"Could not delete {extract_dir.name}: {e}")

        if cleaned_count > 0:
            logger.info(
                f"Cleanup complete: removed {cleaned_count} orphaned file(s)/folder(s)"
            )
        else:
            logger.debug("No orphaned temp files found")

    except (OSError, ValueError, TypeError) as e:
        logger.warning(f"Temp file cleanup failed: {e}")
