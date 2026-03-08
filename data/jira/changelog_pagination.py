"""JIRA changelog paginated issue fetcher.

Fetches all JIRA issues matching a given JQL query with changelog expansion
enabled. Handles pagination, progress reporting, and cancellation.
"""

import logging
from collections.abc import Callable

import requests

from data.jira.changelog_http import (
    _build_headers,
    _extract_error_details,
    _fetch_with_retry,
)
from data.jira.changelog_request import _build_changelog_jql, _build_fields_string

logger = logging.getLogger(__name__)


def fetch_jira_issues_with_changelog(
    config: dict,
    issue_keys: list[str] | None = None,
    max_results: int | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> tuple[bool, list[dict]]:
    """
    Fetch JIRA issues WITH changelog expansion.

    This is an expensive operation and should only be used for issues that need
    status transition history (Flow Time, Flow Efficiency, Lead Time calculations).

    PERFORMANCE OPTIMIZATION:
    - Only fetch changelog for completed issues (reduces volume ~60%)
    - Use separate cache file (jira_changelog_cache.json)
    - Provide transparent loading feedback to user

    Args:
        config: Configuration dictionary with API endpoint, JQL query, token, etc.
        issue_keys: Optional list of specific issue keys to fetch (for targeted
        fetching)
        max_results: Page size for each API call (default: from config or 100)
        progress_callback: Optional callback function(message: str) for progress updates

    Returns:
        Tuple of (success: bool, issues_with_changelog: List[Dict])
    """
    try:
        # Use SMALLER page size for changelog fetching (50 instead of 100)
        # Changelog includes full history - very large payloads that timeout easily
        page_size = (
            max_results
            if max_results is not None
            else min(config.get("max_results", 100), 50)  # Reduced from 100 to 50
        )

        # Build JQL query
        if issue_keys:
            # Fetch specific issues by key
            keys_str = ", ".join(issue_keys)
            jql = f"key IN ({keys_str})"
            logger.info(f"[JIRA] Fetching changelog for {len(issue_keys)} issues")

            # Show prominent progress message for large fetches
            if progress_callback and len(issue_keys) > 50:
                estimated_time = (
                    len(issue_keys) / page_size
                ) * 60  # ~60 seconds per page estimate
                progress_callback(
                    f"[Pending] Fetching changelog for {len(issue_keys)} issues "
                    f"(~{int(estimated_time / 60)} minutes, please wait...)"
                )
        else:
            # Use base JQL + filter for completed issues only (performance optimization)
            jql = _build_changelog_jql(config)

        # Get JIRA API endpoint
        api_endpoint = config.get("api_endpoint", "")
        if not api_endpoint:
            logger.error("[JIRA] API endpoint not configured")
            return False, []

        # Headers for POST request
        headers = _build_headers(config)

        # Fields to fetch (same as regular fetch + changelog)
        fields = _build_fields_string(config)

        # Pagination: Fetch ALL issues with changelog in batches
        all_issues = []
        start_at = 0
        total_issues = None
        max_retries = 3  # Retry failed requests up to 3 times

        logger.debug(f"[JIRA] Fetching with changelog from: {api_endpoint}")
        logger.debug(f"[JIRA] JQL: {jql}")
        logger.debug(
            f"[JIRA] Page size: {page_size}, Fields: {fields}, Expand: changelog"
        )

        # Progress tracking for terminal/logs (every 50 issues)
        last_progress_log = 0
        progress_interval = 50

        while True:
            # Use POST method with body parameters to avoid HTTP 414 "Request-URI Too
            # Long" errors
            # POST /search is read-only (same as GET) - documented by Atlassian for
            # complex queries
            # Convert fields string to list for proper JSON formatting
            fields_list = [f.strip() for f in fields.split(",")]

            body = {
                "jql": jql,
                "maxResults": page_size,
                "startAt": start_at,
                "fields": fields_list,
                "expand": ["changelog"],  # THIS IS THE KEY: Expand changelog
            }

            # Progress reporting
            progress_msg = (
                f"[JIRA] Changelog page at {start_at} (fetched {len(all_issues)})"
            )
            logger.debug(progress_msg)

            # Check for cancellation BEFORE making API call
            try:
                from data.task_progress import TaskProgress

                # Check if task was cancelled
                is_cancelled = TaskProgress.is_task_cancelled()
                logger.debug(
                    f"[JIRA] Changelog cancellation check: is_cancelled={is_cancelled}"
                )
                if is_cancelled:
                    logger.info(
                        "[JIRA] Changelog fetch cancelled by user after"
                        f" {len(all_issues)} issues"
                    )
                    TaskProgress.fail_task("update_data", "Operation cancelled by user")
                    return False, []

                # Update progress bar if we know total
                if total_issues:
                    TaskProgress.update_progress(
                        "update_data",
                        "fetch",
                        current=len(all_issues),
                        total=total_issues,
                        message="Fetching changelog",
                    )
            except Exception as e:
                logger.debug(f"Progress update/cancellation check failed: {e}")

            if progress_callback:
                if total_issues:
                    progress_callback(
                        f"Downloading changelog:"
                        f" {len(all_issues)}/{total_issues} issues"
                    )
                else:
                    progress_callback(
                        f"📥 Downloading changelog: {len(all_issues)} issues"
                    )

            # Retry logic for network failures
            response = _fetch_with_retry(
                api_endpoint,
                headers,
                body,
                max_retries,
                start_at,
                all_issues,
                total_issues,
                progress_callback,
            )

            if response is None:
                # All retries failed, return partial results
                logger.error(
                    f"[JIRA] All retries exhausted for changelog at {start_at}"
                )
                return True, all_issues

            # Error handling
            if not response.ok:
                error_details = _extract_error_details(response)
                logger.error(
                    f"[JIRA] API error ({response.status_code}): {error_details}"
                )
                return False, []

            data = response.json()
            issues_in_page = data.get("issues", [])

            # Get total from first response
            if total_issues is None:
                total_issues = data.get("total", 0)
                logger.info(
                    f"[JIRA] Query matched {total_issues} issues, "
                    "fetching with changelog"
                )
                if progress_callback:
                    progress_callback(
                        f"📥 Downloading changelog for {total_issues} issues "
                        f"(page 1/{(total_issues + page_size - 1) // page_size})..."
                    )

            # Add this page's issues to our collection
            all_issues.extend(issues_in_page)

            # Show progress update for each page
            current_page = (start_at // page_size) + 1
            total_pages = (total_issues + page_size - 1) // page_size
            if progress_callback and current_page > 1:
                progress_callback(
                    f"📥 Downloading changelog page {current_page}/{total_pages} "
                    f"({len(all_issues)}/{total_issues} issues)..."
                )

            # Terminal/log progress: Log every 50 issues to show progress without
            # flooding logs
            issues_fetched = len(all_issues)
            if issues_fetched - last_progress_log >= progress_interval:
                percent_complete = (
                    (issues_fetched / total_issues * 100) if total_issues > 0 else 0
                )
                logger.info(
                    f"[JIRA] Changelog download progress: "
                    f"{issues_fetched}/{total_issues} issues "
                    f"({percent_complete:.0f}%) - Page {current_page}/{total_pages}"
                )
                last_progress_log = issues_fetched

            # Check if we've fetched everything
            if (
                len(issues_in_page) < page_size
                or start_at + len(issues_in_page) >= total_issues
            ):
                logger.info(
                    "[JIRA] Changelog fetch complete:"
                    f" {len(all_issues)}/{total_issues} issues"
                )
                break

            # Move to next page
            start_at += page_size

        # Final progress update to show 100% completion
        if total_issues:
            try:
                from data.task_progress import TaskProgress

                TaskProgress.update_progress(
                    "update_data",
                    "fetch",
                    current=len(all_issues),
                    total=total_issues,
                    message="Fetching changelog",
                )
            except Exception as e:
                logger.debug(f"Final progress update failed: {e}")

        return True, all_issues

    except requests.exceptions.RequestException as e:
        logger.error(f"[JIRA] Network error fetching changelog: {e}")
        return False, []
    except Exception as e:
        logger.error(f"[JIRA] Unexpected error fetching changelog: {e}")
        return False, []
