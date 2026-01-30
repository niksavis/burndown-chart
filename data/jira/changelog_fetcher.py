"""
JIRA changelog fetching module.

This module handles fetching JIRA issues WITH changelog expansion, which is an
expensive operation. It includes optimizations:
- Only fetch changelog for completed issues (reduces volume ~60%)
- Smaller page size (50 instead of 100) to avoid timeouts
- Retry logic for network failures
- Progress reporting and cancellation support
"""

import logging
from typing import Dict, List, Tuple, Callable
import requests

logger = logging.getLogger(__name__)


def fetch_jira_issues_with_changelog(
    config: Dict,
    issue_keys: List[str] | None = None,
    max_results: int | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> Tuple[bool, List[Dict]]:
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
        issue_keys: Optional list of specific issue keys to fetch (for targeted fetching)
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
            # Use POST method with body parameters to avoid HTTP 414 "Request-URI Too Long" errors
            # POST /search is read-only (same as GET) - documented by Atlassian for complex queries
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
                        f"[JIRA] Changelog fetch cancelled by user after {len(all_issues)} issues"
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
                        f"📥 Downloading changelog: {len(all_issues)}/{total_issues} issues"
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
                    f"[JIRA] Query matched {total_issues} issues, fetching with changelog"
                )
                if progress_callback:
                    progress_callback(
                        f"📥 Downloading changelog for {total_issues} issues (page 1/{(total_issues + page_size - 1) // page_size})..."
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

            # Terminal/log progress: Log every 50 issues to show progress without flooding logs
            issues_fetched = len(all_issues)
            if issues_fetched - last_progress_log >= progress_interval:
                percent_complete = (
                    (issues_fetched / total_issues * 100) if total_issues > 0 else 0
                )
                logger.info(
                    f"[JIRA] Changelog download progress: {issues_fetched}/{total_issues} issues "
                    f"({percent_complete:.0f}%) - Page {current_page}/{total_pages}"
                )
                last_progress_log = issues_fetched

            # Check if we've fetched everything
            if (
                len(issues_in_page) < page_size
                or start_at + len(issues_in_page) >= total_issues
            ):
                logger.info(
                    f"[JIRA] Changelog fetch complete: {len(all_issues)}/{total_issues} issues"
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


def _build_changelog_jql(config: Dict) -> str:
    """
    Build JQL query for changelog fetch, filtering for completed issues only.

    This reduces data volume by ~60% compared to fetching all issues.

    Args:
        config: Configuration dictionary with base JQL query

    Returns:
        JQL query string filtered for completed issues
    """
    base_jql = config["jql_query"]

    # Extract ORDER BY clause if present (must come at end of final query)
    order_by_clause = ""
    if "ORDER BY" in base_jql.upper():
        # Find ORDER BY position (case-insensitive)
        import re

        match = re.search(r"\s+ORDER\s+BY\s+", base_jql, re.IGNORECASE)
        if match:
            order_by_start = match.start()
            order_by_clause = base_jql[order_by_start:]
            base_jql = base_jql[:order_by_start].strip()

    # Load completion statuses from configuration
    try:
        from configuration.dora_config import get_flow_end_status_names

        flow_end_statuses = get_flow_end_status_names()
        if flow_end_statuses:
            statuses_str = ", ".join([f'"{s}"' for s in flow_end_statuses])
            jql = f"({base_jql}) AND status IN ({statuses_str}){order_by_clause}"
            logger.debug(f"[JIRA] Filtering completed issues: {statuses_str}")
        else:
            # Fallback: Use common completion statuses
            jql = f'({base_jql}) AND status IN ("Done", "Resolved", "Closed"){order_by_clause}'
            logger.warning("[JIRA] No completion statuses in config, using defaults")
    except Exception as e:
        logger.warning(f"[JIRA] Failed to load completion statuses: {e}")
        jql = f'({base_jql}) AND status IN ("Done", "Resolved", "Closed"){order_by_clause}'

    return jql


def _build_headers(config: Dict) -> Dict[str, str]:
    """
    Build HTTP headers for JIRA API request.

    Args:
        config: Configuration dictionary with token

    Returns:
        Dictionary of HTTP headers
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",  # Required for POST with JSON body
    }
    if config.get("token"):  # Use .get() to safely handle missing token
        headers["Authorization"] = f"Bearer {config['token']}"
    return headers


def _build_fields_string(config: Dict) -> str:
    """
    Build fields string for JIRA API request.

    Includes base fields plus story points and field mappings.

    Args:
        config: Configuration dictionary with field mappings

    Returns:
        Comma-separated string of field names
    """
    from data.jira.field_utils import extract_jira_field_id as _extract_jira_field_id

    # Fields to fetch (same as regular fetch + changelog)
    # NOTE: fixVersions is critical for DORA Lead Time calculation (matching dev issues to operational tasks)
    # NOTE: project is critical for filtering DevOps vs Development projects in DORA metrics
    base_fields = "key,summary,project,created,updated,resolutiondate,status,issuetype,assignee,priority,resolution,labels,components,fixVersions"

    # Add story points field if specified
    additional_fields = []
    points_field = config.get("story_points_field", "")
    if points_field and isinstance(points_field, str) and points_field.strip():
        additional_fields.append(points_field)

    # Add field mappings for DORA and Flow metrics
    # field_mappings has structure: {"dora": {"field_name": "field_id"}, "flow": {...}}
    # CRITICAL: Strip =Value filter syntax (e.g., "customfield_11309=PROD" -> "customfield_11309")
    field_mappings = config.get("field_mappings", {})
    for category, mappings in field_mappings.items():
        if isinstance(mappings, dict):
            for field_name, field_id in mappings.items():
                # Extract clean field ID (strips =Value filter, skips changelog syntax)
                clean_field_id = _extract_jira_field_id(field_id)
                if clean_field_id and clean_field_id not in base_fields:
                    additional_fields.append(clean_field_id)

    # Combine base fields with additional fields
    # Sort additional fields to ensure consistent ordering for cache validation
    if additional_fields:
        fields = f"{base_fields},{','.join(sorted(set(additional_fields)))}"
    else:
        fields = base_fields

    return fields


def _fetch_with_retry(
    api_endpoint: str,
    headers: Dict[str, str],
    body: Dict,
    max_retries: int,
    start_at: int,
    all_issues: List[Dict],
    total_issues: int | None,
    progress_callback: Callable[[str], None] | None,
) -> requests.Response | None:
    """
    Fetch with retry logic for network failures.

    Args:
        api_endpoint: JIRA API endpoint
        headers: HTTP headers
        body: Request body
        max_retries: Maximum number of retries
        start_at: Current pagination offset
        all_issues: List of issues fetched so far
        total_issues: Total number of issues (if known)
        progress_callback: Optional progress callback

    Returns:
        Response object or None if all retries failed
    """
    retry_count = 0
    response = None

    while retry_count < max_retries:
        try:
            # POST method avoids URL length limits (HTTP 414 errors)
            # Parameters go in request body instead of URL
            response = requests.post(
                api_endpoint,
                headers=headers,
                json=body,  # Send parameters in body, not URL
                timeout=90,  # Increased from 30s to 90s
            )
            break  # Success, exit retry loop
        except requests.exceptions.Timeout as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"[JIRA] Timeout at {start_at}, retry {retry_count}/{max_retries}"
                )
                if progress_callback:
                    progress_callback(
                        f"[!] Timeout, retrying... (attempt {retry_count}/{max_retries})"
                    )
            else:
                logger.error(
                    f"[JIRA] Fetch failed at {start_at} after {max_retries} retries: {e}"
                )
                # Return partial results instead of complete failure
                logger.warning(
                    f"[JIRA] Returning partial results: {len(all_issues)}/{total_issues or 'unknown'}"
                )
                return None
        except requests.exceptions.RequestException as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"[JIRA] Network error at {start_at}, retry {retry_count}/{max_retries}: {e}"
                )
                if progress_callback:
                    progress_callback(
                        f"[!] Network error, retrying... (attempt {retry_count}/{max_retries})"
                    )
            else:
                logger.error(
                    f"[JIRA] Fetch failed at {start_at} after {max_retries} retries: {e}"
                )
                # Return partial results instead of complete failure
                logger.warning(
                    f"[JIRA] Returning partial results: {len(all_issues)}/{total_issues or 'unknown'}"
                )
                return None

    return response


def _extract_error_details(response: requests.Response) -> str:
    """
    Extract error details from JIRA API response.

    Args:
        response: Failed response object

    Returns:
        Error details string
    """
    error_details = ""
    try:
        error_json = response.json()
        if "errorMessages" in error_json:
            error_details = "; ".join(error_json["errorMessages"])
        elif "errors" in error_json:
            error_details = "; ".join(
                [f"{k}: {v}" for k, v in error_json["errors"].items()]
            )
        else:
            error_details = str(error_json)
    except Exception:
        error_details = response.text[:500]

    return error_details
