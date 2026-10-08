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


def _persist_download_state(progress: UpdateProgress) -> None:

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
        logger.warning(f"Failed to persist download state: {e}")


def _restore_download_state() -> UpdateProgress | None:

    try:
        backend = get_backend()
        version = backend.get_app_state("pending_update_version")
        path_str = backend.get_app_state("pending_update_path")
        url = backend.get_app_state("pending_update_url")

        if not version or not path_str:
            return None

        download_path = Path(path_str)

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
            logger.warning(
                "Pending update file missing, clearing stale state",
                extra={
                    "operation": "restore_download_state",
                    "version": version,
                    "expected_path": str(download_path),
                },
            )

            backend.set_app_state("pending_update_path", None)

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

    try:
        backend = get_backend()
        backend.set_app_state("pending_update_version", None)
        backend.set_app_state("pending_update_path", None)
        backend.set_app_state("pending_update_url", None)
        backend.set_app_state("pending_update_checked_at", None)

        logger.debug("Cleared download state from database")
    except Exception as e:
        logger.warning(f"Failed to clear download state: {e}")


def is_frozen() -> bool:

    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_deployment_type() -> str:

    return "executable" if is_frozen() else "source"


def is_git_repository() -> bool:

    try:
        if is_frozen():
            return False
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return True
            current = current.parent
        return False
    except Exception:
        return False


def _is_legacy_install() -> bool:
    if not is_frozen():
        return False
    try:
        return Path(sys.executable).name.lower() == LEGACY_MAIN_EXE_NAME.lower()
    except Exception:
        return False


def _find_windows_asset(assets: list[dict], prefix: str) -> dict | None:
    for asset in assets:
        name = asset.get("name", "")
        lower_name = name.lower()
        if prefix in lower_name and lower_name.endswith(".zip"):
            return asset
    return None
