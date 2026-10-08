import json
import logging
import os

from data.exceptions import CacheError
from data.jira.config import (
    DEFAULT_CACHE_MAX_SIZE_MB,
    JIRA_CACHE_FILE,
    JIRA_CHANGELOG_CACHE_FILE,
)

logger = logging.getLogger(__name__)


def validate_cache_file(
    cache_file: str = JIRA_CACHE_FILE, max_size_mb: int = DEFAULT_CACHE_MAX_SIZE_MB
) -> bool:

    try:
        if not os.path.exists(cache_file):
            return True

        file_size_mb = os.path.getsize(cache_file) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            logger.warning(
                f"[Cache] File too large: {file_size_mb:.2f}MB > {max_size_mb}MB"
            )
            return False

        with open(cache_file) as f:
            json.load(f)

        return True

    except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
        logger.exception("[Cache] Validation failed")
        cache_error = CacheError("Failed to validate cache file")
        logger.debug("[Cache] %s: %s", type(cache_error).__name__, e)
        return False


def get_cache_status(cache_file: str = JIRA_CACHE_FILE) -> str:

    try:
        if not os.path.exists(cache_file):
            return "No cache file found"

        file_size_mb = os.path.getsize(cache_file) / (1024 * 1024)

        with open(cache_file) as f:
            cache_data = json.load(f)

        timestamp = cache_data.get("timestamp", "Unknown")

        issues = cache_data.get("issues", [])
        project_counts = {}
        for issue in issues:
            project_key = issue.get("key", "").split("-")[0]
            if project_key:
                project_counts[project_key] = project_counts.get(project_key, 0) + 1

        project_status = ", ".join(
            [f"{proj}: {count} issues" for proj, count in project_counts.items()]
        )

        return (
            f"Cache: {file_size_mb:.2f} MB, Updated: {timestamp[:16]}, {project_status}"
        )

    except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
        logger.exception("[Cache] Error getting status")
        cache_error = CacheError("Failed to get cache status")
        logger.debug("[Cache] %s: %s", type(cache_error).__name__, e)
        return "Error reading cache status"


def invalidate_changelog_cache(cache_file: str = JIRA_CHANGELOG_CACHE_FILE) -> bool:

    try:
        if os.path.exists(cache_file):
            os.remove(cache_file)
            logger.info(f"[Cache] Invalidated changelog cache: {cache_file}")
            return True
        else:
            logger.debug("[Cache] Changelog cache does not exist")
            return True
    except OSError as e:
        logger.exception("[Cache] Failed to invalidate changelog cache")
        cache_error = CacheError("Failed to invalidate changelog cache")
        logger.debug("[Cache] %s: %s", type(cache_error).__name__, e)
        return False
