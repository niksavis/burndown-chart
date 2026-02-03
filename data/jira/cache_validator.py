"""
JIRA Cache Validation

Handles cache file validation, size checks, and status reporting.
"""

import json
import os

from configuration import logger
from data.jira.config import (
    JIRA_CACHE_FILE,
    JIRA_CHANGELOG_CACHE_FILE,
    DEFAULT_CACHE_MAX_SIZE_MB,
)


def validate_cache_file(
    cache_file: str = JIRA_CACHE_FILE, max_size_mb: int = DEFAULT_CACHE_MAX_SIZE_MB
) -> bool:
    """
    Validate cache file size and integrity.

    Args:
        cache_file: Path to cache file
        max_size_mb: Maximum allowed file size in MB

    Returns:
        True if cache is valid or doesn't exist
    """
    try:
        if not os.path.exists(cache_file):
            return True  # No cache file is valid

        # Check file size
        file_size_mb = os.path.getsize(cache_file) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            logger.warning(
                f"[Cache] File too large: {file_size_mb:.2f}MB > {max_size_mb}MB"
            )
            return False

        # Check file integrity
        with open(cache_file, "r") as f:
            json.load(f)

        return True

    except Exception as e:
        logger.error(f"[Cache] Validation failed: {e}")
        return False


def get_cache_status(cache_file: str = JIRA_CACHE_FILE) -> str:
    """
    Get detailed cache status information.

    Args:
        cache_file: Path to cache file

    Returns:
        Human-readable cache status string
    """
    try:
        if not os.path.exists(cache_file):
            return "No cache file found"

        file_size_mb = os.path.getsize(cache_file) / (1024 * 1024)

        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        timestamp = cache_data.get("timestamp", "Unknown")

        # Count issues per project
        issues = cache_data.get("issues", [])
        project_counts = {}
        for issue in issues:
            project_key = issue.get("key", "").split("-")[0]
            if project_key:
                project_counts[project_key] = project_counts.get(project_key, 0) + 1

        # Format project counts
        project_status = ", ".join(
            [f"{proj}: {count} issues" for proj, count in project_counts.items()]
        )

        return (
            f"Cache: {file_size_mb:.2f} MB, Updated: {timestamp[:16]}, {project_status}"
        )

    except Exception as e:
        logger.error(f"[Cache] Error getting status: {e}")
        return "Error reading cache status"


def invalidate_changelog_cache(cache_file: str = JIRA_CHANGELOG_CACHE_FILE) -> bool:
    """
    Invalidate (delete) changelog cache when issue cache is refreshed.

    This ensures changelog cache stays in sync with issue cache.
    When issues are refreshed, changelog must also be refreshed.

    Args:
        cache_file: Path to changelog cache file

    Returns:
        True if cache was invalidated (deleted or didn't exist)
    """
    try:
        if os.path.exists(cache_file):
            os.remove(cache_file)
            logger.info(f"[Cache] Invalidated changelog cache: {cache_file}")
            return True
        else:
            logger.debug("[Cache] Changelog cache does not exist")
            return True
    except Exception as e:
        logger.error(f"[Cache] Failed to invalidate changelog cache: {e}")
        return False
