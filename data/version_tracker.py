import logging

from configuration import __version__
from data.persistence.factory import get_backend

logger = logging.getLogger(__name__)


def check_and_update_version() -> tuple[bool, str | None, str]:

    try:
        backend = get_backend()
        current_version = __version__

        last_version = backend.get_app_state("last_run_version")

        version_changed = last_version is not None and last_version != current_version

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
        return False, None, __version__
