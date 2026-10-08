import logging
from datetime import datetime

import requests

from data.update_delivery import (
    download_update,
    launch_updater,
)
from data.update_models import (
    APP_NAME,
    GITHUB_API_URL,
    GITHUB_OWNER,
    GITHUB_REPO,
    LEGACY_WINDOWS_ZIP_PREFIX,
    UPDATE_CHECK_TIMEOUT_SECONDS,
    WINDOWS_ZIP_PREFIX,
    UpdateProgress,
    UpdateState,
    compare_versions,
    get_current_version,
)
from data.update_platform import (
    _find_windows_asset,
    _is_legacy_install,
    _persist_download_state,
    _restore_download_state,
    clear_download_state,
    get_deployment_type,
    is_frozen,
    is_git_repository,
)

logger = logging.getLogger(__name__)


def check_for_updates() -> UpdateProgress:

    current_version = get_current_version()
    deployment_type = get_deployment_type()
    is_git_repo = is_git_repository()

    logger.info(
        "Starting update check",
        extra={
            "operation": "check_for_updates",
            "current_version": current_version,
            "deployment_type": deployment_type,
            "is_git_repo": is_git_repo,
        },
    )

    progress = UpdateProgress(
        state=UpdateState.CHECKING,
        current_version=current_version,
        last_checked=datetime.now(),
    )

    try:
        api_url = GITHUB_API_URL.format(owner=GITHUB_OWNER, repo=GITHUB_REPO)

        logger.debug(
            "Querying GitHub releases API",
            extra={"operation": "check_for_updates", "url": api_url},
        )

        response = requests.get(
            api_url,
            timeout=UPDATE_CHECK_TIMEOUT_SECONDS,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"{APP_NAME}/{current_version}",
            },
        )

        response.raise_for_status()

        release_data = response.json()

        tag_name = release_data.get("tag_name", "")
        available_version = tag_name.lstrip("v")

        logger.info(
            "GitHub API query successful",
            extra={
                "operation": "check_for_updates",
                "available_version": available_version,
                "prerelease": release_data.get("prerelease", False),
            },
        )

        if release_data.get("prerelease", False):
            logger.info(
                "Skipping prerelease version",
                extra={"operation": "check_for_updates", "version": available_version},
            )
            progress.state = UpdateState.UP_TO_DATE
            return progress

        version_comparison = compare_versions(current_version, available_version)

        if version_comparison < 0:
            logger.info(
                "Update available",
                extra={
                    "operation": "check_for_updates",
                    "current": current_version,
                    "available": available_version,
                    "deployment_type": deployment_type,
                },
            )

            if not is_frozen():
                logger.info(
                    "Running from source - manual update required",
                    extra={
                        "operation": "check_for_updates",
                        "is_git_repo": is_git_repo,
                    },
                )

                if is_git_repo:
                    update_instructions = (
                        "You are running from a git repository. To update:\n\n"
                        "1. Save your work and close the app\n"
                        "2. Run: git pull\n"
                        "3. Run: pip install -r requirements.txt\n"
                        "4. Restart the app"
                    )
                else:
                    update_instructions = (
                        "You are running from source code. To update:\n\n"
                        "1. Download the new source code ZIP from GitHub releases\n"
                        "2. Extract and replace the existing files\n"
                        "3. Run: pip install -r requirements.txt\n"
                        "4. Restart the app\n\n"
                        f"Download from: https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/tag/v{available_version}"
                    )

                progress.state = UpdateState.MANUAL_UPDATE_REQUIRED
                progress.available_version = available_version
                progress.release_notes = update_instructions
                progress.error_message = update_instructions
                return progress

            assets = release_data.get("assets", [])
            prefer_legacy = _is_legacy_install()
            preferred_prefix = (
                LEGACY_WINDOWS_ZIP_PREFIX if prefer_legacy else WINDOWS_ZIP_PREFIX
            )
            fallback_prefix = (
                WINDOWS_ZIP_PREFIX if prefer_legacy else LEGACY_WINDOWS_ZIP_PREFIX
            )

            windows_asset = _find_windows_asset(assets, preferred_prefix)
            if not windows_asset:
                windows_asset = _find_windows_asset(assets, fallback_prefix)

            if not windows_asset:
                logger.warning(
                    "No Windows ZIP asset found in release",
                    extra={
                        "operation": "check_for_updates",
                        "version": available_version,
                        "assets": [a.get("name") for a in assets],
                        "preferred_prefix": preferred_prefix,
                        "fallback_prefix": fallback_prefix,
                    },
                )
                progress.state = UpdateState.ERROR
                progress.error_message = (
                    f"No Windows installer found for version {available_version}"
                )
                return progress

            progress.state = UpdateState.AVAILABLE
            progress.available_version = available_version
            progress.download_url = windows_asset.get("browser_download_url")
            progress.file_size = windows_asset.get("size")
            progress.release_notes = release_data.get("body", "")

            return progress

        else:
            logger.info(
                "App is up to date",
                extra={
                    "operation": "check_for_updates",
                    "current": current_version,
                    "latest": available_version,
                },
            )
            progress.state = UpdateState.UP_TO_DATE
            return progress

    except requests.exceptions.Timeout:
        logger.warning(
            "GitHub API request timed out",
            extra={
                "operation": "check_for_updates",
                "timeout": UPDATE_CHECK_TIMEOUT_SECONDS,
            },
        )
        progress.state = UpdateState.ERROR
        progress.error_message = (
            f"Update check timed out after {UPDATE_CHECK_TIMEOUT_SECONDS}s"
        )
        return progress

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else "unknown"
        logger.warning(
            "GitHub API HTTP error",
            extra={
                "operation": "check_for_updates",
                "status_code": status_code,
                "error": str(e),
            },
        )
        progress.state = UpdateState.ERROR
        progress.error_message = f"Update check failed (HTTP {status_code})"
        return progress

    except requests.exceptions.ConnectionError as e:
        logger.info(
            "Cannot connect to GitHub API (network offline or unavailable)",
            extra={"operation": "check_for_updates", "error": str(e)},
        )
        progress.state = UpdateState.ERROR
        progress.error_message = "No network connection available"
        return progress

    except requests.exceptions.RequestException as e:
        logger.warning(
            "GitHub API request failed",
            extra={
                "operation": "check_for_updates",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress.state = UpdateState.ERROR
        progress.error_message = f"Failed to check for updates: {str(e)}"
        return progress

    except (ValueError, KeyError) as e:
        logger.error(
            "Failed to parse GitHub API response",
            extra={
                "operation": "check_for_updates",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress.state = UpdateState.ERROR
        progress.error_message = f"Invalid update data: {str(e)}"
        return progress


__all__ = [
    "UpdateState",
    "UpdateProgress",
    "check_for_updates",
    "download_update",
    "launch_updater",
    "get_current_version",
    "compare_versions",
    "is_frozen",
    "get_deployment_type",
    "clear_download_state",
    "_restore_download_state",
    "_persist_download_state",
]
