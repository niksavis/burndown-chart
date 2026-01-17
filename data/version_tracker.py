"""
Version Tracker

Detects version changes on app startup and manages version history
in the database for displaying "Successfully updated" notifications.
"""

import logging
from typing import Optional, Tuple

from configuration import __version__
from data.persistence.factory import get_backend

logger = logging.getLogger(__name__)


def check_and_update_version() -> Tuple[bool, Optional[str], str]:
    """Check if app version has changed since last run and update stored version.

    This function:
    1. Retrieves the last run version from app_state table
    2. Compares it to the current version
    3. Updates the stored version to current
    4. Returns whether version changed

    Returns:
        Tuple of (version_changed, previous_version, current_version)
        - version_changed: True if version differs from last run
        - previous_version: Last run version string or None if first run
        - current_version: Current application version
    """
    try:
        backend = get_backend()
        current_version = __version__

        # Get last run version from database
        last_version = backend.get_app_state("last_run_version")

        # Determine if version changed
        version_changed = last_version is not None and last_version != current_version

        # Update stored version to current
        backend.set_app_state("last_run_version", current_version)

        if version_changed:
            logger.info(
                f"Version change detected: {last_version} -> {current_version}",
                extra={
                    "operation": "version_check",
                    "previous_version": last_version,
                    "current_version": current_version,
                },
            )
        elif last_version is None:
            logger.info(
                f"First run detected, storing version: {current_version}",
                extra={
                    "operation": "version_check",
                    "current_version": current_version,
                },
            )
        else:
            logger.debug(
                f"No version change (running {current_version})",
                extra={
                    "operation": "version_check",
                    "current_version": current_version,
                },
            )

        return version_changed, last_version, current_version

    except Exception as e:
        logger.error(
            f"Failed to check version: {e}",
            exc_info=True,
            extra={"operation": "version_check"},
        )
        # Return no change on error to avoid disrupting app startup
        return False, None, __version__
