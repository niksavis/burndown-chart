"""
JIRA API Integration Module

This module provides minimal JIRA API integration for the burndown chart application.
It fetches JIRA issues and transforms them to match the existing CSV statistics format.
"""

#######################################################################
# IMPORTS
#######################################################################
import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import requests

from configuration import logger
from data.cache_manager import (
    generate_cache_key,
    load_cache_with_validation,
    save_cache,
)
from data.persistence import load_app_settings, save_app_settings

#######################################################################
# CONFIGURATION
#######################################################################

JIRA_CACHE_FILE = "jira_cache.json"
JIRA_CHANGELOG_CACHE_FILE = "jira_changelog_cache.json"
DEFAULT_CACHE_MAX_SIZE_MB = 100

# Cache version - increment when cache format changes or pagination logic changes
CACHE_VERSION = "2.0"  # v2.0: Pagination support added
CHANGELOG_CACHE_VERSION = "2.0"  # v2.0: Added critical fields (project, status, issuetype, etc.) for DORA metrics

# Cache expiration - invalidate cache after this duration
CACHE_EXPIRATION_HOURS = 24  # Cache expires after 24 hours

#######################################################################
# CORE JIRA FUNCTIONS
#######################################################################


def _extract_jira_field_id(field_mapping: str) -> str:
    """Extract clean JIRA field ID from a field mapping string.

    Field mappings may include filter syntax that JIRA API doesn't understand:
    - "customfield_11309=PROD" -> "customfield_11309" (strip =Value filter)
    - "status:In Progress.DateTime" -> "" (changelog extraction, not a field)
    - "customfield_10002" -> "customfield_10002" (no change needed)
    - "fixVersions" -> "fixVersions" (standard field)

    Args:
        field_mapping: Field mapping string from profile configuration

    Returns:
        Clean field ID for JIRA API, or empty string if not a fetchable field
    """
    if not field_mapping or not isinstance(field_mapping, str):
        return ""

    field_mapping = field_mapping.strip()

    # Skip changelog extraction syntax (e.g., "status:In Progress.DateTime")
    # These are extracted from changelog, not fetched as fields
    if ":" in field_mapping and ".DateTime" in field_mapping:
        return ""

    # Strip =Value filter syntax (e.g., "customfield_11309=PROD" -> "customfield_11309")
    # The =Value part is our internal filter syntax, not understood by JIRA
    if "=" in field_mapping:
        return field_mapping.split("=")[0].strip()

    return field_mapping


def check_jira_issue_count(jql_query: str, config: Dict) -> Tuple[bool, int]:
    """
    Fast check: Get issue count from JIRA without fetching full issue data.

    This is a lightweight query (< 1 second) that returns only the total count.
    Used to detect if cache is stale before doing a full refresh.

    Args:
        jql_query: JQL query to count issues for
        config: JIRA configuration with API endpoint and token

    Returns:
        Tuple of (success: bool, count: int)
    """
    try:
        url = f"{config['api_endpoint']}/search"

        headers = {"Accept": "application/json"}
        if config.get("token"):
            headers["Authorization"] = f"Bearer {config['token']}"

        # maxResults=0 returns only total count (no issue data)
        params = {
            "jql": jql_query,
            "maxResults": 0,  # Don't fetch issues, just count
            "fields": "key",  # Minimal field to reduce payload
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            total_count = data.get("total", 0)
            logger.info(f"[JIRA] Count check: {total_count} issues matched")
            return True, total_count
        else:
            logger.warning(f"[JIRA] Count check failed: HTTP {response.status_code}")
            return False, 0

    except Exception as e:
        logger.warning(f"[JIRA] Count check failed: {e}")
        return False, 0


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


def get_jira_config(settings_jql_query: str | None = None) -> Dict:
    """
    Load JIRA configuration with priority hierarchy: jira_config → Environment → Default.

    This function reads from the jira_config structure in profile.json (managed via
    the JIRA Configuration modal). Falls back to environment variables if config not found.

    Args:
        settings_jql_query: JQL query parameter (highest priority for JQL only)

    Returns:
        Dictionary containing JIRA configuration with keys:
        - jql_query: JQL query string
        - api_endpoint: Full JIRA API endpoint URL
        - token: JIRA authentication token
        - story_points_field: Custom field ID for story points
        - cache_max_size_mb: Maximum cache size in MB
        - max_results: Maximum results per API call
    """
    # Load app settings first
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
    except Exception:
        app_settings = {}

    # Load jira_config structure (new configuration system)
    try:
        from data.persistence import load_jira_configuration

        jira_config = load_jira_configuration()
    except Exception:
        jira_config = {}

    # Configuration hierarchy: Parameter → App settings → Environment → Default
    jql_query = (
        settings_jql_query  # JQL from parameter (highest priority)
        or app_settings.get("jql_query", "")  # App settings
        or os.getenv("JIRA_DEFAULT_JQL", "")  # Environment variable
        or "project = JRASERVER"  # Default fallback
    )

    # Build API endpoint from jira_config or environment
    base_url = jira_config.get("base_url") or os.getenv("JIRA_BASE_URL", "")
    api_version = jira_config.get("api_version") or os.getenv("JIRA_API_VERSION", "v2")

    if base_url:
        api_endpoint = construct_jira_endpoint(base_url, api_version)
    else:
        api_endpoint = os.getenv(
            "JIRA_API_ENDPOINT", "https://jira.atlassian.com/rest/api/2/search"
        )

    config = {
        "jql_query": jql_query,
        "api_endpoint": api_endpoint,
        "token": (
            jira_config.get("token", "")  # jira_config (new structure)
            or os.getenv("JIRA_TOKEN", "")  # Environment variable
            or ""  # Default
        ),
        "story_points_field": (
            jira_config.get("points_field", "")  # jira_config (new structure)
            or os.getenv("JIRA_STORY_POINTS_FIELD", "")  # Environment variable
            or ""  # Default
        ),
        "cache_max_size_mb": int(
            jira_config.get(
                "cache_size_mb", DEFAULT_CACHE_MAX_SIZE_MB
            )  # jira_config (new structure)
            or os.getenv(
                "JIRA_CACHE_MAX_SIZE_MB", DEFAULT_CACHE_MAX_SIZE_MB
            )  # Environment variable
        ),
        "max_results": int(
            jira_config.get("max_results_per_call", 1000)  # jira_config (new structure)
            or os.getenv("JIRA_MAX_RESULTS", 1000)  # Environment variable
        ),
        "devops_projects": app_settings.get(
            "devops_projects", []
        ),  # Load from app_settings
        "field_mappings": app_settings.get(
            "field_mappings", {}
        ),  # Load field mappings for DORA/Flow metrics
    }

    return config


def validate_jira_config(config: Dict) -> Tuple[bool, str]:
    """Validate JIRA configuration and custom fields."""
    api_endpoint = config.get("api_endpoint", "")
    if not api_endpoint:
        return False, "JIRA API endpoint is required"

    if not config["jql_query"]:
        return False, "JQL query is required"

    # Basic JQL validation (optional - JQL is complex, so we do minimal validation)
    jql_query = config["jql_query"].strip()
    if len(jql_query) < 5:  # Minimum reasonable JQL length
        return False, "JQL query is too short"

    # Basic URL validation for API endpoint
    if not api_endpoint.startswith(("http://", "https://")):
        return False, "JIRA API endpoint must be a valid URL (http:// or https://)"

    # Check for ScriptRunner compatibility issues
    is_compatible, scriptrunner_warning = validate_jql_for_scriptrunner(jql_query)
    if not is_compatible:
        # Return as warning, not blocking error - let user decide
        logger.warning(f"[JIRA] {scriptrunner_warning}")

    return True, "Configuration valid"


def _generate_config_hash(config: Dict, fields: str) -> str:
    """
    Generate hash of configuration for cache validation.

    This hash ensures cache is invalidated when configuration changes.
    Includes: JQL query, fields requested, field mappings, time period

    Args:
        config: JIRA configuration dictionary
        fields: Fields requested in API call

    Returns:
        MD5 hash string of configuration
    """
    config_str = json.dumps(
        {
            "jql": config.get("jql_query", ""),
            "fields": fields,
            "field_mappings": config.get("field_mappings", {}),
            "story_points_field": config.get("story_points_field", ""),
        },
        sort_keys=True,
    )

    return hashlib.md5(config_str.encode("utf-8")).hexdigest()


def fetch_jira_issues(
    config: Dict, max_results: int | None = None
) -> Tuple[bool, List[Dict]]:
    """
    Execute JQL query and return ALL issues using pagination with incremental fetch optimization.

    INCREMENTAL FETCH OPTIMIZATION (T051):
    - Checks issue count before full fetch to detect if data changed
    - If count unchanged: Returns cached data (skips expensive API calls)
    - If count changed: Fetches all issues (cache is stale)
    - Reduces API load and improves response time when data hasn't changed

    RATE LIMITING & RETRY (T052-T053):
    - Rate limiting: Token bucket algorithm (100 max tokens, 10/sec refill)
    - Retry logic: Exponential backoff for 429, 5xx, timeout, connection errors
    - Integrated with jira_query_manager rate limiter

    JIRA API Limits:
    - Maximum 1000 results per API call (JIRA hard limit)
    - Use pagination with startAt parameter to fetch all issues
    - Page size (maxResults) should be 100-1000 for optimal performance

    Args:
        config: Configuration dictionary with API endpoint, JQL query, token, etc.
        max_results: Page size for each API call (default: from config or 1000)

    Returns:
        Tuple of (success: bool, issues: List[Dict])
    """
    import time
    from data.jira_query_manager import get_rate_limiter, retry_with_backoff

    start_time = time.time()

    try:
        # Use the JQL query directly from configuration
        jql = config["jql_query"]

        # Get JIRA API endpoint (full URL)
        api_endpoint = config.get("api_endpoint", "")
        if not api_endpoint:
            logger.error("[JIRA] API endpoint not configured")
            return False, []

        # Parameters - fetch required fields including field mappings for DORA/Flow
        # Check if caller requested specific fields (e.g., "*all" for field detection)
        if config.get("fields"):
            fields = config["fields"]
            logger.debug(f"[JIRA] Using caller-specified fields: {fields}")
        else:
            # Base fields: always fetch these standard fields
            # CRITICAL: Include 'project' to enable filtering DevOps vs Development projects
            base_fields = "key,project,created,resolutiondate,status,issuetype"

            # Add story points field if specified
            additional_fields = []
            if (
                config.get("story_points_field")
                and config["story_points_field"].strip()
            ):
                additional_fields.append(config["story_points_field"])

            # Add field mappings for DORA and Flow metrics
            # field_mappings has structure: {"dora": {"field_name": "field_id"}, "flow": {...}}
            # CRITICAL: Strip =Value filter syntax (e.g., "customfield_11309=PROD" -> "customfield_11309")
            # The =Value part is our internal filter syntax, JIRA API doesn't understand it
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

        # ===== T051: INCREMENTAL FETCH OPTIMIZATION =====
        # Check if data has changed before doing expensive full fetch
        logger.info("[JIRA] Checking if data has changed (incremental fetch)")

        # Try to load cached data first
        # CRITICAL FIX: Use generate_jira_data_cache_key() which excludes field_mappings
        # This allows field mapping changes (like WIP states) to reuse cached JIRA data
        # without requiring expensive re-download
        from data.cache_manager import generate_jira_data_cache_key

        cache_key = generate_jira_data_cache_key(
            jql_query=jql,
            time_period_days=30,  # Default time period
        )

        # Still calculate config_hash for validation, but it doesn't affect cache key
        config_hash = _generate_config_hash(config, fields)

        is_valid, cached_data = load_cache_with_validation(
            cache_key=cache_key,
            config_hash=config_hash,
            max_age_hours=CACHE_EXPIRATION_HOURS,
            cache_dir="cache",
        )

        if is_valid and cached_data:
            # We have valid cache, now check if JIRA data changed
            # Use fast count check (maxResults=0, returns only total count)
            success, current_count = check_jira_issue_count(jql, config)

            if success:
                cached_count = len(cached_data)

                if current_count == cached_count:
                    # Data hasn't changed - use cache (skip expensive fetch)
                    elapsed_time = time.time() - start_time
                    logger.info(
                        f"[JIRA] Cache hit: {current_count} issues unchanged ({elapsed_time:.2f}s)"
                    )
                    return True, cached_data
                else:
                    # Data changed - need to fetch
                    logger.info(
                        f"[JIRA] Data changed: {cached_count} -> {current_count} issues, fetching"
                    )
            else:
                # Count check failed - proceed with fetch to be safe
                logger.warning("[JIRA] Count check failed, proceeding with full fetch")
        else:
            logger.info("[JIRA] Cache miss, fetching from API")

        # ===== PROCEED WITH FULL FETCH (cache miss or data changed) =====

        # Use max_results as TOTAL LIMIT (for field detection: 100 issues max)
        # Page size is separate (per API call), JIRA API hard limit is 1000 per call
        total_limit = (
            max_results if max_results is not None else None
        )  # None = fetch all
        page_size = min(total_limit or 1000, 1000)  # Use smaller of limit or 1000

        # Enforce JIRA API hard limit
        if page_size > 1000:
            logger.warning(
                f"[JIRA] Page size {page_size} exceeds API limit, using 1000"
            )
            page_size = 1000

        # Use the full API endpoint directly
        url = api_endpoint

        # Headers
        headers = {"Accept": "application/json"}
        if config["token"]:
            headers["Authorization"] = f"Bearer {config['token']}"

        # Pagination: Fetch ALL issues in batches
        all_issues = []
        start_at = 0
        total_issues = None  # Will be set from first API response

        logger.debug(f"[JIRA] Fetching from: {url}")
        logger.debug(f"[JIRA] JQL: {jql}")
        logger.debug(f"[JIRA] Page size: {page_size}, Fields: {fields}")

        # Get rate limiter for T052 integration
        rate_limiter = get_rate_limiter()

        while True:
            params = {
                "jql": jql,
                "maxResults": page_size,
                "startAt": start_at,
                "fields": fields,
            }

            logger.debug(
                f"[JIRA] Page at {start_at} (fetched {len(all_issues)} so far)"
            )

            # T052: Rate limiting - wait for token before request
            rate_limiter.wait_for_token()

            # T053: Retry with exponential backoff for resilience
            success, response = retry_with_backoff(
                requests.get, url, headers=headers, params=params, timeout=30
            )

            if not success:
                logger.error("[JIRA] Fetch failed after retries")
                return False, []

            # Enhanced error handling for ScriptRunner and JQL issues
            if not response.ok:
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
                    error_details = response.text[:500]  # First 500 chars of response

                # Check for common ScriptRunner/JQL function issues
                if (
                    "issueFunction" in jql.lower()
                    or "scriptrunner" in error_details.lower()
                ):
                    logger.error(
                        f"[JIRA] ScriptRunner function error in JQL: {jql[:50]}..."
                    )
                    logger.error("[JIRA] ScriptRunner functions may not be available")
                    logger.error(f"[JIRA] API error details: {error_details}")
                else:
                    logger.error(
                        f"[JIRA] API error ({response.status_code}): {error_details}"
                    )

                return False, []

            data = response.json()
            issues_in_page = data.get("issues", [])

            # Get total from first response
            if total_issues is None:
                total_issues = data.get("total", 0)
                logger.info(f"[JIRA] Query matched {total_issues} issues, paginating")

            # Determine how many issues to add (respect total_limit)
            if total_limit is not None:
                remaining_quota = total_limit - len(all_issues)
                issues_to_add = issues_in_page[:remaining_quota]  # Truncate if needed
            else:
                issues_to_add = issues_in_page

            # Add issues to collection
            all_issues.extend(issues_to_add)

            # Check if we've fetched everything OR reached total_limit
            if (
                len(issues_in_page) < page_size  # Last page (partial)
                or start_at + len(issues_in_page) >= total_issues  # All issues fetched
                or (
                    total_limit is not None and len(all_issues) >= total_limit
                )  # Limit reached
            ):
                logger.info(
                    f"[JIRA] Pagination complete: {len(all_issues)}/{total_issues} fetched"
                )
                break

            # Move to next page
            start_at += page_size

        # Save to cache for next time
        save_cache(
            cache_key=cache_key,
            data=all_issues,
            config_hash=config_hash,
            cache_dir="cache",
        )

        elapsed_time = time.time() - start_time
        logger.info(
            f"[JIRA] Fetch complete: {len(all_issues)} issues in {elapsed_time:.2f}s"
        )
        return True, all_issues

    except requests.exceptions.RequestException as e:
        logger.error(f"[JIRA] Network error: {e}")
        return False, []
    except Exception as e:
        logger.error(f"[JIRA] Unexpected error: {e}")
        return False, []


def fetch_jira_issues_with_changelog(
    config: Dict,
    issue_keys: List[str] | None = None,
    max_results: int | None = None,
    progress_callback=None,
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
                from configuration.dora_config import get_completion_status_names

                completion_statuses = get_completion_status_names()
                if completion_statuses:
                    statuses_str = ", ".join([f'"{s}"' for s in completion_statuses])
                    jql = (
                        f"({base_jql}) AND status IN ({statuses_str}){order_by_clause}"
                    )
                    logger.debug(f"[JIRA] Filtering completed issues: {statuses_str}")
                else:
                    # Fallback: Use common completion statuses
                    jql = f'({base_jql}) AND status IN ("Done", "Resolved", "Closed"){order_by_clause}'
                    logger.warning(
                        "[JIRA] No completion statuses in config, using defaults"
                    )
            except Exception as e:
                logger.warning(f"[JIRA] Failed to load completion statuses: {e}")
                jql = f'({base_jql}) AND status IN ("Done", "Resolved", "Closed"){order_by_clause}'

        # Get JIRA API endpoint
        api_endpoint = config.get("api_endpoint", "")
        if not api_endpoint:
            logger.error("[JIRA] API endpoint not configured")
            return False, []

        # Headers for POST request
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",  # Required for POST with JSON body
        }
        if config.get("token"):  # Use .get() to safely handle missing token
            headers["Authorization"] = f"Bearer {config['token']}"

        # Fields to fetch (same as regular fetch + changelog)
        # NOTE: fixVersions is critical for DORA Lead Time calculation (matching dev issues to operational tasks)
        # NOTE: project is critical for filtering DevOps vs Development projects in DORA metrics
        base_fields = (
            "key,project,created,resolutiondate,status,issuetype,resolution,fixVersions"
        )

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
                        return True, all_issues  # Return what we have so far
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
                        return True, all_issues  # Return what we have so far

            if response is None:
                # All retries failed
                logger.error(
                    f"[JIRA] All retries exhausted for changelog at {start_at}"
                )
                return True, all_issues  # Return partial results

            # Error handling
            if not response.ok:
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

        return True, all_issues

    except requests.exceptions.RequestException as e:
        logger.error(f"[JIRA] Network error fetching changelog: {e}")
        return False, []
    except Exception as e:
        logger.error(f"[JIRA] Unexpected error fetching changelog: {e}")

        return False, []


def cache_jira_response(
    data: List[Dict],
    jql_query: str = "",
    fields_requested: str = "",
    cache_file: str = JIRA_CACHE_FILE,
    config: Dict | None = None,
) -> bool:
    """
    Save JIRA response to cache using new cache_manager.

    Args:
        data: JIRA issues to cache
        jql_query: JQL query used
        fields_requested: Fields requested in API call
        cache_file: Legacy parameter (maintains backward compatibility)
        config: JIRA configuration for generating cache key and hash

    Returns:
        True if cached successfully
    """
    try:
        # Save to new cache system if config provided
        if config:
            field_mappings = config.get("field_mappings", {})
            cache_key = generate_cache_key(
                jql_query=jql_query,
                field_mappings=field_mappings,
                time_period_days=30,  # Default time period
            )

            config_hash = _generate_config_hash(config, fields_requested)

            save_cache(
                cache_key=cache_key,
                data=data,
                config_hash=config_hash,
                cache_dir="cache",
            )
            logger.info(f"[Cache] Saved {len(data)} issues (key: {cache_key[:8]}...)")

            # Save cache metadata to app settings for audit trail (Feature 008 - T057)
            try:
                current_settings = load_app_settings()
                cache_metadata = {
                    "last_cache_key": cache_key,
                    "last_cache_timestamp": datetime.now().isoformat(),
                    "cache_config_hash": config_hash,
                }
                save_app_settings(
                    pert_factor=current_settings.get("pert_factor", 3.0),
                    deadline=current_settings.get("deadline", "2025-12-31"),
                    data_points_count=current_settings.get("data_points_count"),
                    show_milestone=current_settings.get("show_milestone"),
                    milestone=current_settings.get("milestone"),
                    show_points=current_settings.get("show_points"),
                    jql_query=current_settings.get("jql_query"),
                    last_used_data_source=current_settings.get("last_used_data_source"),
                    active_jql_profile_id=current_settings.get("active_jql_profile_id"),
                    cache_metadata=cache_metadata,
                )
                logger.debug(f"[Cache] Metadata saved: {cache_key[:8]}...")
            except Exception as metadata_error:
                logger.warning(f"[Cache] Failed to save metadata: {metadata_error}")

        # Also save to legacy cache file for backward compatibility
        cache_data = {
            "cache_version": CACHE_VERSION,
            "timestamp": datetime.now().isoformat(),
            "jql_query": jql_query,
            "fields_requested": fields_requested,
            "issues": data,
            "total_issues": len(data),
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        logger.debug(
            f"[Cache] Saved {len(data)} issues to legacy cache (v{CACHE_VERSION})"
        )
        return True

    except Exception as e:
        logger.error(f"[Cache] Error saving response: {e}", exc_info=True)
        return False


def load_jira_cache(
    current_jql_query: str = "",
    current_fields: str = "",
    cache_file: str = JIRA_CACHE_FILE,
    config: Dict | None = None,
) -> Tuple[bool, List[Dict]]:
    """
    Load cached JIRA JSON response using new cache_manager.

    Args:
        current_jql_query: Current JQL query for cache validation
        current_fields: Current fields for cache validation
        cache_file: Legacy parameter (now uses cache/ directory)
        config: JIRA configuration for generating cache key and hash

    Returns:
        Tuple of (cache_hit: bool, issues: List[Dict])
    """
    # If no config provided, cannot validate cache
    if not config:
        logger.debug("[Cache] No config provided, cache miss")
        return False, []

    try:
        # Generate cache key from configuration
        # CRITICAL FIX: Use generate_jira_data_cache_key() which excludes field_mappings
        # This allows field mapping changes (like WIP states) to reuse cached JIRA data
        from data.cache_manager import generate_jira_data_cache_key

        cache_key = generate_jira_data_cache_key(
            jql_query=current_jql_query,
            time_period_days=30,  # Default time period for now
        )

        # Generate config hash for validation (but it doesn't affect cache key anymore)
        config_hash = _generate_config_hash(config, current_fields)

        # Try to load from new cache system
        is_valid, cached_data = load_cache_with_validation(
            cache_key=cache_key,
            config_hash=config_hash,
            max_age_hours=CACHE_EXPIRATION_HOURS,
            cache_dir="cache",
        )

        if is_valid and cached_data:
            logger.info(f"[Cache] Hit: Loaded {len(cached_data)} issues from new cache")
            return True, cached_data

        # Fallback: Try to load from legacy cache file for backward compatibility
        if os.path.exists(cache_file):
            logger.debug("[Cache] Checking legacy cache file")
            with open(cache_file, "r") as f:
                cache_data = json.load(f)

            # Validate legacy cache
            cached_version = cache_data.get("cache_version", "1.0")
            if cached_version != CACHE_VERSION:
                logger.debug(
                    f"[Cache] Legacy version mismatch: v{cached_version} != v{CACHE_VERSION}"
                )
                return False, []

            # Check timestamp
            cache_timestamp_str = cache_data.get("timestamp", "")
            if cache_timestamp_str:
                cache_timestamp = datetime.fromisoformat(cache_timestamp_str)
                cache_age = datetime.now() - cache_timestamp
                if cache_age > timedelta(hours=CACHE_EXPIRATION_HOURS):
                    logger.debug(
                        f"[Cache] Legacy cache expired ({cache_age.total_seconds() / 3600:.1f}h)"
                    )
                    return False, []

            # Check JQL/fields match
            if cache_data.get("jql_query") != current_jql_query:
                logger.debug("[Cache] Legacy JQL mismatch")
                return False, []

            issues = cache_data.get("issues", [])
            logger.info(f"[Cache] Loaded {len(issues)} issues from legacy cache")

            # Migrate to new cache system
            logger.debug("[Cache] Migrating to new system")
            save_cache(
                cache_key=cache_key,
                data=issues,
                config_hash=config_hash,
                cache_dir="cache",
            )

            return True, issues

        # No cache available
        logger.debug("[Cache] Miss: No valid cache found")
        return False, []

    except Exception as e:
        logger.error(f"[Cache] Error loading: {e}", exc_info=True)
        return False, []


def validate_cache_file(
    cache_file: str = JIRA_CACHE_FILE, max_size_mb: int = DEFAULT_CACHE_MAX_SIZE_MB
) -> bool:
    """Validate cache file size and integrity."""
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
    """Get detailed cache status information."""
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


def cache_changelog_response(
    issues_with_changelog: List[Dict],
    jql_query: str = "",
    fields_requested: str = "",
    cache_file: str = JIRA_CHANGELOG_CACHE_FILE,
) -> bool:
    """
    Save JIRA issues with changelog to separate cache file.

    This keeps changelog data separate from regular issue data for performance.
    Changelog is only needed for Flow Time, Flow Efficiency, and Lead Time calculations.

    Args:
        issues_with_changelog: List of JIRA issues with expanded changelog
        jql_query: JQL query used to fetch issues
        fields_requested: Fields that were requested
        cache_file: Path to changelog cache file

    Returns:
        True if caching successful, False otherwise
    """
    try:
        cache_data = {
            "cache_version": CHANGELOG_CACHE_VERSION,
            "timestamp": datetime.now().isoformat(),
            "jql_query": jql_query,
            "fields_requested": fields_requested,
            "issues": issues_with_changelog,
            "total_issues": len(issues_with_changelog),
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        logger.debug(
            f"[Cache] Saved {len(issues_with_changelog)} issues with changelog"
        )
        return True

    except Exception as e:
        logger.error(f"[Cache] Error saving changelog: {e}")
        return False


def load_changelog_cache(
    current_jql_query: str = "",
    current_fields: str = "",
    cache_file: str = JIRA_CHANGELOG_CACHE_FILE,
) -> Tuple[bool, List[Dict]]:
    """
    Load cached JIRA issues with changelog from file.

    Cache is invalidated if:
    - Cache version doesn't match current version
    - Cache is older than CACHE_EXPIRATION_HOURS
    - JQL query doesn't match
    - Fields requested don't match

    Args:
        current_jql_query: Current JQL query to compare against cached query
        current_fields: Current fields to compare against cached fields
        cache_file: Path to changelog cache file

    Returns:
        Tuple of (cache_loaded: bool, issues: List[Dict])
    """
    try:
        if not os.path.exists(cache_file):
            return False, []

        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        # Check cache version
        cached_version = cache_data.get("cache_version", "1.0")
        if cached_version != CHANGELOG_CACHE_VERSION:
            logger.debug(
                f"[Cache] Changelog version mismatch: v{cached_version} != v{CHANGELOG_CACHE_VERSION}"
            )
            return False, []

        # Check cache age
        cache_timestamp_str = cache_data.get("timestamp", "")
        if cache_timestamp_str:
            try:
                cache_timestamp = datetime.fromisoformat(cache_timestamp_str)
                cache_age = datetime.now() - cache_timestamp
                if cache_age > timedelta(hours=CACHE_EXPIRATION_HOURS):
                    logger.debug(
                        f"[Cache] Changelog expired: {cache_age.total_seconds() / 3600:.1f}h"
                    )
                    return False, []
            except ValueError:
                logger.warning(
                    f"[Cache] Invalid changelog timestamp: {cache_timestamp_str}"
                )
                return False, []

        # Check if the cached query matches the current query
        cached_jql = cache_data.get("jql_query", "")
        if cached_jql != current_jql_query:
            logger.debug("[Cache] Changelog JQL mismatch")
            return False, []

        # Check if the cached fields match the current fields (optional check)
        cached_fields = cache_data.get("fields_requested", "")
        if cached_fields and current_fields and cached_fields != current_fields:
            logger.debug("[Cache] Changelog fields mismatch")
            return False, []

        issues = cache_data.get("issues", [])
        cache_age_str = (
            f"{(datetime.now() - datetime.fromisoformat(cache_timestamp_str)).total_seconds() / 3600:.1f}h old"
            if cache_timestamp_str
            else "unknown age"
        )
        logger.info(
            f"[Cache] Loaded {len(issues)} issues with changelog ({cache_age_str})"
        )
        return True, issues

    except Exception as e:
        logger.error(f"[Cache] Error loading changelog: {e}")
        return False, []


def extract_story_points_value(story_points_value, field_name: str = "") -> float:
    """
    Extract numeric value from JIRA field, handling complex objects.

    Args:
        story_points_value: The raw value from JIRA field
        field_name: Name of the field (for logging/debugging)

    Returns:
        float: Numeric value to use for calculations
    """
    if not story_points_value:
        return 0.0

    # Handle complex objects (like votes field)
    if isinstance(story_points_value, dict):
        # For votes field: {"votes": 5, "hasVoted": false}
        if "votes" in story_points_value and isinstance(
            story_points_value["votes"], (int, float)
        ):
            return float(story_points_value["votes"])

        # For other complex fields, try common numeric properties
        for numeric_key in ["value", "points", "count", "total"]:
            if numeric_key in story_points_value and isinstance(
                story_points_value[numeric_key], (int, float)
            ):
                return float(story_points_value[numeric_key])

        # If no numeric value found in object, log warning and return 0
        logger.warning(
            f"[JIRA] Complex field '{field_name}' has no numeric value: {story_points_value}"
        )
        return 0.0

    # Handle simple numeric values
    if isinstance(story_points_value, (int, float)):
        return float(story_points_value)

    # Handle string representations of numbers
    if isinstance(story_points_value, str):
        try:
            return float(story_points_value)
        except ValueError:
            logger.warning(
                f"[JIRA] Field '{field_name}' non-numeric: '{story_points_value}'"
            )
            return 0.0

    # Unknown type
    logger.warning(
        f"[JIRA] Field '{field_name}' unexpected type {type(story_points_value)}"
    )
    return 0.0


def jira_to_csv_format(issues: List[Dict], config: Dict) -> List[Dict]:
    """Transform JIRA issues to CSV statistics format."""
    try:
        if not issues:
            return []

        # Determine date range from actual issues data
        all_dates = []
        for issue in issues:
            if issue.get("fields", {}).get("created"):
                created_date = datetime.strptime(
                    issue["fields"]["created"][:10], "%Y-%m-%d"
                )
                all_dates.append(created_date)
            if issue.get("fields", {}).get("resolutiondate"):
                resolution_date = datetime.strptime(
                    issue["fields"]["resolutiondate"][:10], "%Y-%m-%d"
                )
                all_dates.append(resolution_date)

        if not all_dates:
            logger.warning("[JIRA] No valid dates found in issues")
            return []

        # Use actual data range, extending to full weeks
        date_from = min(all_dates)
        date_to = max(all_dates)

        # Extend range to ensure we capture all activity
        date_from = date_from - timedelta(days=date_from.weekday())  # Start of week
        date_to = date_to + timedelta(days=6 - date_to.weekday())  # End of week

        weekly_data = []
        current_date = date_from

        while current_date <= date_to:
            week_end = current_date + timedelta(days=6)
            week_end = min(week_end, date_to)

            # Count completed and created items for this week
            completed_items = 0
            completed_points = 0
            created_items = 0
            created_points = 0

            for issue in issues:
                # Check if item was completed this week
                if issue.get("fields", {}).get("resolutiondate"):
                    resolution_date = datetime.strptime(
                        issue["fields"]["resolutiondate"][:10], "%Y-%m-%d"
                    )
                    if current_date <= resolution_date <= week_end:
                        completed_items += 1
                        # Add story points if available and field is specified
                        story_points = 0
                        if (
                            config.get("story_points_field")
                            and config["story_points_field"].strip()
                        ):
                            story_points_value = issue.get("fields", {}).get(
                                config["story_points_field"]
                            )
                            story_points = extract_story_points_value(
                                story_points_value, config["story_points_field"]
                            )
                        completed_points += story_points

                # Check if item was created this week
                if issue.get("fields", {}).get("created"):
                    created_date = datetime.strptime(
                        issue["fields"]["created"][:10], "%Y-%m-%d"
                    )
                    if current_date <= created_date <= week_end:
                        created_items += 1
                        # Add story points if available and field is specified
                        story_points = 0
                        if (
                            config.get("story_points_field")
                            and config["story_points_field"].strip()
                        ):
                            story_points_value = issue.get("fields", {}).get(
                                config["story_points_field"]
                            )
                            story_points = extract_story_points_value(
                                story_points_value, config["story_points_field"]
                            )
                        created_points += story_points

            weekly_data.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "completed_items": completed_items,
                    "completed_points": completed_points,
                    "created_items": created_items,
                    "created_points": created_points,
                }
            )

            current_date = week_end + timedelta(days=1)

        logger.info(f"[JIRA] Generated {len(weekly_data)} weekly data points")
        return weekly_data

    except Exception as e:
        logger.error(f"[JIRA] Transform failed: {e}")
        return []


def sync_jira_scope_and_data(
    jql_query: str | None = None,
    ui_config: Dict | None = None,
    force_refresh: bool = False,
) -> Tuple[bool, str, Dict]:
    """
    Main sync function to get JIRA scope calculation and replace CSV data.

    Args:
        jql_query: JQL query to use (overrides config)
        ui_config: UI configuration dictionary (overrides file config)
        force_refresh: If True, bypass cache and force fresh JIRA fetch

    Returns:
        Tuple of (success, message, scope_data)
    """
    try:
        # Import scope calculator here to avoid circular imports
        from data.jira_scope_calculator import calculate_jira_project_scope

        # Load configuration with JQL query from settings or use provided UI config
        if ui_config:
            config = ui_config.copy()
            # Ensure jql_query parameter takes precedence if provided
            if jql_query:
                config["jql_query"] = jql_query
        else:
            config = get_jira_config(jql_query)

        # Validate configuration
        is_valid, message = validate_jira_config(config)
        if not is_valid:
            return False, f"Configuration invalid: {message}", {}

        # Validate cache file
        if not validate_cache_file(max_size_mb=config["cache_max_size_mb"]):
            return False, "Cache file validation failed", {}

        # Calculate current fields that would be requested (MUST match fetch_jira_issues logic)
        base_fields = "key,created,resolutiondate,status,issuetype"
        additional_fields = []

        # Add story points field
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

        # Build final fields string (must match fetch_jira_issues exactly)
        # Sort additional fields to ensure consistent ordering for cache validation
        if additional_fields:
            current_fields = f"{base_fields},{','.join(sorted(set(additional_fields)))}"
        else:
            current_fields = base_fields

        # SMART CACHING LOGIC
        logger.debug(f"[JIRA] Sync starting: force_refresh={force_refresh}")
        logger.debug(f"[JIRA] JQL: {config['jql_query'][:50]}...")
        logger.debug(f"[JIRA] Fields: {current_fields}")

        # Step 1: Check if force refresh is requested
        if force_refresh:
            logger.debug("[JIRA] Force refresh - bypassing cache")
            cache_loaded = False
            issues = []
        else:
            # Get query-specific cache file path
            from data.profile_manager import get_active_query_workspace

            query_workspace = get_active_query_workspace()
            jira_cache_file = str(query_workspace / "jira_cache.json")

            # Step 2: Try to load from cache (checks version, age, JQL, fields)
            logger.debug("[JIRA] Attempting cache load")
            cache_loaded, issues = load_jira_cache(
                config["jql_query"],
                current_fields,
                jira_cache_file,
                config,  # Pass config for new cache system
            )
            logger.debug(
                f"[JIRA] Cache result: loaded={cache_loaded}, count={len(issues) if issues else 0}"
            )

            # Step 3: If cache is valid, do a quick count check to detect changes
            if cache_loaded and issues:
                logger.debug(
                    f"[JIRA] Cache loaded: {len(issues)} issues, checking count"
                )
                count_success, current_count = check_jira_issue_count(
                    config["jql_query"], config
                )

                if count_success and current_count != len(issues):
                    logger.info(
                        f"[JIRA] Count changed: {len(issues)} -> {current_count}, fetching"
                    )
                    cache_loaded = False  # Force refresh due to count mismatch
                elif count_success:
                    logger.debug(
                        f"[JIRA] Count unchanged ({current_count}), using cache"
                    )
                else:
                    logger.warning("[JIRA] Count check failed, using cache anyway")

        # Step 4: Fetch from JIRA if cache is invalid or force refresh
        if not cache_loaded or not issues:
            # Fetch fresh data from JIRA
            fetch_success, issues = fetch_jira_issues(config)
            if not fetch_success:
                return False, "Failed to fetch JIRA data", {}

            # Get query-specific cache file path
            from data.profile_manager import get_active_query_workspace

            query_workspace = get_active_query_workspace()
            jira_cache_file = str(query_workspace / "jira_cache.json")

            # Cache the response with the JQL query and fields used
            if not cache_jira_response(
                issues,
                config["jql_query"],
                current_fields,
                jira_cache_file,
                config,  # Pass config for new cache system
            ):
                logger.warning("[Cache] Failed to save response")

            # CRITICAL: Invalidate changelog cache ONLY when we fetch fresh data from JIRA
            # If we used the issue cache, changelog cache is still valid
            invalidate_changelog_cache()
        else:
            logger.info("[Cache] Using cached issues, changelog remains valid")

        # PHASE 2: Changelog data fetch
        # Changelog is needed for Flow Time and DORA metrics
        # Fetch it now so Calculate Metrics has the data it needs
        logger.info("[JIRA] Fetching changelog data for Flow/DORA metrics...")
        changelog_success, changelog_message = fetch_changelog_on_demand(config)
        if changelog_success:
            logger.info(f"[JIRA] Changelog fetch successful: {changelog_message}")
        else:
            logger.warning(
                f"[JIRA] Changelog fetch failed (non-critical): {changelog_message}"
            )

        # CRITICAL: Filter out DevOps project issues for burndown/velocity/statistics
        # DevOps issues are ONLY used for DORA metrics metadata extraction
        devops_projects = config.get("devops_projects", [])
        if devops_projects:
            from data.project_filter import filter_development_issues

            total_issues_count = len(issues)
            issues_for_metrics = filter_development_issues(issues, devops_projects)
            filtered_count = total_issues_count - len(issues_for_metrics)

            if filtered_count > 0:
                logger.info(
                    f"[JIRA] Filtered {filtered_count} DevOps issues, using {len(issues_for_metrics)} dev issues"
                )
        else:
            # No DevOps projects configured, use all issues
            issues_for_metrics = issues

        # Calculate JIRA-based project scope (using ONLY development project issues)
        # Only use story_points_field if it's configured and not empty
        points_field_raw = config.get("story_points_field", "")
        # Defensive: Ensure points_field is a string, not a dict
        if isinstance(points_field_raw, dict):
            logger.warning(
                f"[JIRA] story_points_field is a dict, using empty string: {points_field_raw}"
            )
            points_field = ""
        elif isinstance(points_field_raw, str):
            points_field = points_field_raw.strip()
        else:
            logger.warning(
                f"[JIRA] story_points_field has unexpected type {type(points_field_raw)}, using empty string"
            )
            points_field = ""

        if not points_field:
            # When no points field is configured, pass empty string instead of defaulting to "votes"
            points_field = ""
        scope_data = calculate_jira_project_scope(
            issues_for_metrics, points_field, config
        )
        if not scope_data:
            return False, "Failed to calculate JIRA project scope", {}

        # Transform to CSV format for statistics (using ONLY development project issues)
        csv_data = jira_to_csv_format(issues_for_metrics, config)
        # Note: Empty list is valid when there are no issues, only None indicates error

        # Save both statistics and project scope to unified data structure
        from data.persistence import save_jira_data_unified

        if save_jira_data_unified(csv_data, scope_data, config):
            logger.info("[JIRA] Scope calculation and data sync completed successfully")
            return (
                True,
                "JIRA sync and scope calculation completed successfully",
                scope_data,
            )
        else:
            return False, "Failed to save JIRA data to unified structure", {}

    except Exception as e:
        logger.error(f"[JIRA] Error in scope sync: {e}")
        return False, f"JIRA scope sync failed: {e}", {}


def sync_jira_data(
    jql_query: str | None = None, ui_config: Dict | None = None
) -> Tuple[bool, str]:
    """Legacy sync function - calls new scope sync and returns just success/message."""
    try:
        success, message, scope_data = sync_jira_scope_and_data(jql_query, ui_config)
        return success, message
    except Exception as e:
        logger.error(f"[JIRA] Error in data sync: {e}")
        return False, f"JIRA sync failed: {e}"


def fetch_changelog_on_demand(config: Dict, progress_callback=None) -> Tuple[bool, str]:
    """
    Fetch changelog data separately for Flow Time and DORA metrics with incremental saving.

    OPTIMIZATION: Only fetches changelog for issues NOT already in cache.
    This dramatically improves performance on subsequent "Calculate Metrics" clicks.

    RESILIENCE FEATURES:
    - Saves progress after each page (prevents data loss on timeout)
    - Retries failed requests up to 3 times
    - Returns partial results if download incomplete
    - Uses 90-second timeout for large changelog payloads

    Args:
        config: JIRA configuration dictionary with API endpoint, token, etc.
        progress_callback: Optional callback function(message: str) for progress updates

    Returns:
        Tuple of (success, message)
    """
    import json
    from datetime import datetime

    try:
        logger.info("[JIRA] Fetching changelog data for Flow Time and DORA metrics")
        if progress_callback:
            progress_callback("[Stats] Starting changelog download...")

        # Get query-specific cache file paths
        from data.profile_manager import get_active_query_workspace

        query_workspace = get_active_query_workspace()
        changelog_cache_file = str(query_workspace / "jira_changelog_cache.json")
        jira_cache_file = str(query_workspace / "jira_cache.json")

        # Load existing cache to merge with new data (resume capability)
        changelog_cache = {}
        cached_issue_keys = set()

        if os.path.exists(changelog_cache_file):
            try:
                with open(changelog_cache_file, "r", encoding="utf-8") as f:
                    changelog_cache = json.load(f)
                cached_issue_keys = set(changelog_cache.keys())
                logger.info(
                    f"[Cache] Loaded {len(changelog_cache)} changelog entries from cache"
                )
            except Exception as e:
                logger.warning(f"[Cache] Could not load changelog cache: {e}")
                changelog_cache = {}
                cached_issue_keys = set()

        # OPTIMIZATION: Determine which issues need changelog fetching
        # Only fetch issues that are NOT already in the cache
        issues_needing_changelog = []

        if os.path.exists(jira_cache_file):
            try:
                with open(jira_cache_file, "r", encoding="utf-8") as f:
                    jira_cache_data = json.load(f)
                all_issue_keys = [
                    issue.get("key")
                    for issue in jira_cache_data.get("issues", [])
                    if issue.get("key")
                ]

                # Find issues not in changelog cache
                issues_needing_changelog = [
                    key for key in all_issue_keys if key not in cached_issue_keys
                ]

                logger.info(
                    f"[JIRA] Changelog analysis: {len(all_issue_keys)} total, "
                    f"{len(cached_issue_keys)} cached, {len(issues_needing_changelog)} need fetch"
                )

                if issues_needing_changelog:
                    logger.info(
                        f"[Cache] Optimized fetch: Only {len(issues_needing_changelog)} new issues"
                    )
                    if progress_callback:
                        progress_callback(
                            f"Smart fetch: {len(issues_needing_changelog)} new issues "
                            f"({len(cached_issue_keys)} already cached)"
                        )
                else:
                    logger.info(
                        "[Cache] All issues have changelog cached, skipping fetch"
                    )
                    if progress_callback:
                        progress_callback(
                            f"[OK] All {len(cached_issue_keys)} issues already cached - skipping download"
                        )
                    return (
                        True,
                        f"[OK] Changelog already cached for all {len(cached_issue_keys)} issues",
                    )

            except Exception as e:
                logger.warning(
                    f"[JIRA] Could not analyze jira_cache.json: {e}, fetching all changelog"
                )
                issues_needing_changelog = None
        else:
            logger.warning("[JIRA] jira_cache.json not found, fetching all changelog")
            issues_needing_changelog = None

        # Fetch changelog (only for issues not in cache if we have the list)
        changelog_fetch_success, issues_with_changelog = (
            fetch_jira_issues_with_changelog(
                config,
                issue_keys=issues_needing_changelog,  # Only fetch missing issues
                progress_callback=progress_callback,
            )
        )

        if changelog_fetch_success:
            # CRITICAL OPTIMIZATION: Filter changelog to ONLY status transitions
            # This dramatically reduces cache file size (from 1M+ lines to ~50K)
            try:
                total_histories_before = 0
                total_histories_after = 0
                batch_size = 100  # Save every 100 issues for progress resilience
                issues_processed = 0

                for issue in issues_with_changelog:
                    issue_key = issue.get("key", "")
                    if not issue_key:
                        continue

                    changelog_full = issue.get("changelog", {})
                    histories = changelog_full.get("histories", [])
                    total_histories_before += len(histories)

                    # Filter to ONLY histories that contain status changes
                    status_histories = []
                    for history in histories:
                        items = history.get("items", [])

                        # Keep only status change items
                        status_items = [
                            item for item in items if item.get("field") == "status"
                        ]

                        if status_items:
                            # Build minimal history entry with only what we need
                            status_histories.append(
                                {
                                    "created": history.get("created"),
                                    "items": [
                                        {
                                            "field": "status",
                                            "fromString": item.get("fromString"),
                                            "toString": item.get("toString"),
                                        }
                                        for item in status_items
                                    ],
                                }
                            )

                    total_histories_after += len(status_histories)

                    if status_histories:
                        # CRITICAL: Include ALL fields needed for DORA and Flow metrics
                        # - project: Filter Development vs DevOps projects
                        # - fixVersions: Match dev issues with operational tasks
                        # - status: Filter completed/deployed issues
                        # - issuetype: Filter "Operational Task" issues
                        # - created: Used in some calculations
                        # - resolutiondate: Fallback for deployment dates
                        fields = issue.get("fields", {})
                        changelog_cache[issue_key] = {
                            "key": issue_key,
                            "fields": {
                                "project": fields.get("project"),
                                "fixVersions": fields.get("fixVersions"),
                                "status": fields.get("status"),
                                "issuetype": fields.get("issuetype"),
                                "created": fields.get("created"),
                                "resolutiondate": fields.get("resolutiondate"),
                            },
                            "changelog": {
                                "histories": status_histories,
                                "total": len(status_histories),
                            },
                            "last_updated": datetime.now().isoformat(),
                        }
                        issues_processed += 1

                    # LOG PROGRESS: Every 50 issues to show activity without impacting performance
                    if issues_processed > 0 and issues_processed % 50 == 0:
                        logger.info(
                            f"[JIRA] Processing changelog: {issues_processed}/{len(issues_with_changelog)} issues"
                        )
                        if progress_callback:
                            progress_callback(
                                f"Processing changelog: {issues_processed}/{len(issues_with_changelog)} issues"
                            )

                    # INCREMENTAL SAVE: Save every 100 issues to prevent data loss on timeout
                    if issues_processed > 0 and issues_processed % batch_size == 0:
                        try:
                            with open(changelog_cache_file, "w", encoding="utf-8") as f:
                                json.dump(changelog_cache, f, indent=2)
                            logger.info(
                                f"[Cache] Incremental save: {issues_processed}/{len(issues_with_changelog)} issues"
                            )
                            if progress_callback:
                                progress_callback(
                                    f"Saved progress: {issues_processed} issues"
                                )
                        except Exception as e:
                            logger.warning(
                                f"[Cache] Failed to save incremental progress: {e}"
                            )

                # Final save: Save all remaining issues
                if progress_callback:
                    progress_callback(
                        f"Finalizing changelog data for {len(changelog_cache)} issues..."
                    )

                with open(changelog_cache_file, "w", encoding="utf-8") as f:
                    json.dump(changelog_cache, f, indent=2)

                reduction_pct = (
                    (
                        100
                        * (total_histories_before - total_histories_after)
                        / total_histories_before
                    )
                    if total_histories_before > 0
                    else 0
                )

                optimization_msg = f"[Cache] Optimized changelog: {total_histories_before} → {total_histories_after} histories ({reduction_pct:.1f}% reduction)"
                logger.info(optimization_msg)
                logger.info(
                    f"[Cache] Saved optimized changelog to {changelog_cache_file}"
                )

                # Calculate how many were newly fetched vs already cached
                newly_fetched = len(issues_with_changelog)
                total_cached = len(changelog_cache)
                previously_cached = total_cached - newly_fetched

                if progress_callback:
                    progress_callback(
                        f"[OK] Changelog complete: {newly_fetched} fetched, {previously_cached} cached, {total_cached} total"
                    )

                return (
                    True,
                    f"[OK] Changelog: {newly_fetched} newly fetched + {previously_cached} already cached = {total_cached} total issues (saved {reduction_pct:.0f}% size)",
                )
            except Exception as e:
                logger.warning(f"[Cache] Failed to save changelog data: {e}")
                return False, f"Failed to cache changelog: {e}"
        else:
            logger.warning(
                "[JIRA] Failed to fetch changelog, Flow metrics may be limited"
            )
            return False, "Failed to fetch changelog data from JIRA"

    except Exception as e:
        logger.error(f"[JIRA] Error fetching changelog on demand: {e}")
        return False, f"Changelog fetch failed: {e}"


def validate_jql_for_scriptrunner(jql_query: str) -> Tuple[bool, str]:
    """
    Validate JQL query for potential ScriptRunner compatibility issues.

    ScriptRunner functions like issueFunction, subtasksOf, epicsOf, etc. are add-on
    functions that may not be available on all JIRA instances or may require special
    permissions/licensing.

    Args:
        jql_query: JQL query string to validate

    Returns:
        Tuple of (is_compatible, warning_message)
    """
    if not jql_query:
        return True, ""

    # List of common ScriptRunner functions that might cause issues
    scriptrunner_functions = [
        "issueFunction",
        "subtasksOf",
        "epicsOf",
        "linkedIssuesOf",
        "parentEpicsOf",
        "subtaskOf",
        "portfolioChildrenOf",
        "portfolioParentsOf",
        "portfolioSiblingsOf",
    ]

    query_lower = jql_query.lower()
    found_functions = []

    for func in scriptrunner_functions:
        if func.lower() in query_lower:
            found_functions.append(func)

    if found_functions:
        warning = (
            f"Warning: JQL query contains ScriptRunner functions: {', '.join(found_functions)}. "
            "These functions require the ScriptRunner add-on and may not be available on all JIRA instances. "
            "If you get 'failed to fetch jira data' errors, try simplifying the query or verify ScriptRunner is installed."
        )
        return False, warning

    return True, ""


def test_jql_query(config: Dict) -> Tuple[bool, str]:
    """
    Test JQL query validity by trying to fetch just 1 result.

    This is useful for validating complex queries with ScriptRunner functions
    without fetching all the data.

    Args:
        config: JIRA configuration dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Use the JQL query directly from configuration
        jql = config["jql_query"]
        api_endpoint = config.get("api_endpoint", "")

        if not api_endpoint:
            return False, "JIRA API endpoint not configured"

        # Headers
        headers = {"Accept": "application/json"}
        if config["token"]:
            headers["Authorization"] = f"Bearer {config['token']}"

        # Test with minimal parameters - just fetch 1 issue to validate query
        params = {
            "jql": jql,
            "maxResults": 1,
            "fields": "key",  # Only fetch key field for testing
        }

        logger.info(f"[JIRA] Testing JQL query: {jql[:100]}...")
        response = requests.get(
            api_endpoint, headers=headers, params=params, timeout=10
        )

        if not response.ok:
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
                error_details = response.text[:200]

            # Provide specific guidance for ScriptRunner issues
            if "issueFunction" in jql.lower() and (
                "function" in error_details.lower()
                or "scriptrunner" in error_details.lower()
            ):
                return (
                    False,
                    f"ScriptRunner function error: {error_details}. This JIRA instance may not have ScriptRunner installed or you may not have permission to use these functions.",
                )

            return False, f"JQL query invalid: {error_details}"

        # If we get here, the query returned 200 OK - try to parse response
        try:
            data = response.json()
            total = data.get("total", 0)
            logger.info(f"[JIRA] Query valid - would return {total} issues")
            return True, f"JQL query is valid (would return {total} issues)"
        except ValueError as json_error:
            # Response was 200 OK but body is not valid JSON - API version likely not supported
            logger.error(f"[JIRA] HTTP 200 but invalid JSON: {json_error}")
            logger.error(
                f"[JIRA] Response body (first 200 chars): {response.text[:200]}"
            )
            return (
                False,
                "JIRA API returned invalid response (HTTP 200 but not JSON). Your JIRA server may not support this API version. Try switching to API v2 in Configure JIRA.",
            )

    except requests.exceptions.RequestException as e:
        return False, f"Network error testing JQL query: {e}"
    except Exception as e:
        return False, f"Error testing JQL query: {e}"


#######################################################################
# JIRA CONFIGURATION FUNCTIONS (Feature 003-jira-config-separation)
#######################################################################


def construct_jira_endpoint(base_url: str, api_version: str = "v3") -> str:
    """
    Construct full JIRA API endpoint from base URL and version.

    Args:
        base_url: Base JIRA URL (e.g., "https://company.atlassian.net")
        api_version: API version ("v2" or "v3")

    Returns:
        Full endpoint URL (e.g., "https://company.atlassian.net/rest/api/3/search")

    Raises:
        ValueError: If URL format is invalid
    """
    # Remove trailing slashes
    clean_url = base_url.rstrip("/")

    # Validate URL format
    if not clean_url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    if not clean_url:
        raise ValueError("URL cannot be empty")

    # Construct endpoint based on API version
    api_path = "/rest/api/2/search" if api_version == "v2" else "/rest/api/3/search"

    return f"{clean_url}{api_path}"


def test_jira_connection(base_url: str, token: str, api_version: str = "v3") -> Dict:
    """
    Test JIRA connection by calling serverInfo endpoint.

    This validates the base URL and token without requiring a JQL query.
    Uses the serverInfo endpoint which is lightweight and doesn't require authentication
    for connectivity check, but we include the token to verify authentication.

    Args:
        base_url: Base JIRA URL (e.g., "https://company.atlassian.net")
        token: Personal access token
        api_version: API version ("v2" or "v3")

    Returns:
        Dictionary with test results:
        {
            "success": bool,
            "message": str,
            "response_time_ms": int,
            "server_info": dict (if successful),
            "error_code": str (if failed),
            "error_details": str (if failed),
            "timestamp": str (ISO 8601)
        }
    """
    import time

    timestamp = datetime.now().isoformat()
    start_time = time.time()

    try:
        # Validate base URL format first
        clean_url = base_url.rstrip("/")
        if not clean_url.startswith(("http://", "https://")):
            return {
                "success": False,
                "message": "Please enter a valid JIRA URL starting with https://",
                "timestamp": timestamp,
                "response_time_ms": None,
                "error_code": "invalid_url_format",
                "error_details": "URL must start with http:// or https://",
            }

        # Construct serverInfo endpoint using configured API version
        api_ver = api_version.replace("v", "")  # Normalize "v2" or "2" to "2"
        server_info_url = f"{clean_url}/rest/api/{api_ver}/serverInfo"

        # Prepare headers with authentication
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Make request with timeout
        logger.info(f"[JIRA] Testing connection to: {server_info_url}")
        response = requests.get(server_info_url, headers=headers, timeout=10)

        response_time_ms = int((time.time() - start_time) * 1000)

        # Check response status
        if response.status_code == 200:
            server_info = response.json()

            # Additional check: Verify the search endpoint with specified API version
            search_endpoint = construct_jira_endpoint(base_url, api_version)
            logger.info(f"[JIRA] Verifying search endpoint: {search_endpoint}")

            # Test with a minimal JQL query (just get 1 result)
            test_jql = "order by created DESC"
            search_headers = headers.copy()
            search_response = requests.get(
                search_endpoint,
                headers=search_headers,
                params={"jql": test_jql, "maxResults": 1},
                timeout=10,
            )

            # If search endpoint fails, provide specific guidance
            if search_response.status_code in (400, 404):
                api_version_name = "v3" if api_version == "v3" else "v2"
                opposite_version = "v2" if api_version == "v3" else "v3"

                # Log the actual error for debugging
                logger.warning(
                    f"[JIRA] API {api_version_name} not available (status {search_response.status_code})"
                )
                try:
                    error_data = search_response.json()
                    logger.warning(f"[JIRA] Search endpoint error: {error_data}")
                except Exception:
                    logger.warning(
                        f"[JIRA] Search endpoint returned {search_response.status_code} without JSON body"
                    )

                return {
                    "success": False,
                    "message": f"Server connected but API {api_version_name} not available",
                    "timestamp": timestamp,
                    "response_time_ms": response_time_ms,
                    "error_code": "api_version_mismatch",
                    "error_details": f"Your JIRA server does not support REST API {api_version_name}. The search endpoint returned {search_response.status_code}. Try switching to API {opposite_version} in the configuration.",
                }

            # If search works, return full success (only accept 200 OK with valid JSON)
            if search_response.status_code == 200:
                # Verify response body is valid JSON
                try:
                    search_data = search_response.json()
                    # Verify it has expected structure
                    if "issues" in search_data or "total" in search_data:
                        logger.info(
                            f"[JIRA] API {api_version} verified (status 200, valid JSON)"
                        )
                        return {
                            "success": True,
                            "message": f"Connection successful (API {api_version} verified)",
                            "timestamp": timestamp,
                            "response_time_ms": response_time_ms,
                            "server_info": {
                                "version": server_info.get("version", "unknown"),
                                "serverTitle": server_info.get(
                                    "serverTitle", "JIRA Server"
                                ),
                                "baseUrl": server_info.get("baseUrl", clean_url),
                            },
                        }
                    else:
                        # Got JSON but wrong structure
                        logger.warning(
                            f"[JIRA] API {api_version} returned JSON with unexpected structure: {list(search_data.keys())}"
                        )
                except ValueError as json_error:
                    # Status 200 but body is not JSON - API version doesn't work
                    logger.warning(
                        f"[JIRA] API {api_version} returned 200 but invalid JSON: {json_error}"
                    )
                    logger.warning(
                        f"[JIRA] Response body (first 200 chars): {search_response.text[:200]}"
                    )

                # If we get here, v3 returns 200 but doesn't work properly
                api_version_name = "v3" if api_version == "v3" else "v2"
                opposite_version = "v2" if api_version == "v3" else "v3"
                return {
                    "success": False,
                    "message": f"Server connected but API {api_version_name} not available",
                    "timestamp": timestamp,
                    "response_time_ms": response_time_ms,
                    "error_code": "api_version_mismatch",
                    "error_details": f"Your JIRA server does not properly support REST API {api_version_name} (returned 200 but invalid response). Try switching to API {opposite_version} in the configuration.",
                }

            # Search endpoint returned any other error - treat as API version issue
            api_version_name = "v3" if api_version == "v3" else "v2"
            opposite_version = "v2" if api_version == "v3" else "v3"

            logger.warning(
                f"[JIRA] API {api_version_name} not available (unexpected status {search_response.status_code})"
            )

            return {
                "success": False,
                "message": f"Server connected but API {api_version_name} not available",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "api_version_mismatch",
                "error_details": f"Your JIRA server does not support REST API {api_version_name}. The search endpoint returned {search_response.status_code}. Try switching to API {opposite_version} in the configuration.",
            }

        elif response.status_code == 401:
            return {
                "success": False,
                "message": "Authentication failed - invalid token",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "authentication_failed",
                "error_details": "401 Unauthorized: Invalid or expired token. Please verify your personal access token in JIRA settings.",
            }

        elif response.status_code == 403:
            return {
                "success": False,
                "message": "Access forbidden - insufficient permissions",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "authentication_failed",
                "error_details": "403 Forbidden: Token does not have sufficient permissions to access JIRA API.",
            }

        elif response.status_code == 404:
            return {
                "success": False,
                "message": "JIRA server not found - verify URL",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "server_unreachable",
                "error_details": "404 Not Found: The JIRA server could not be found at this URL. Please verify the base URL is correct.",
            }

        else:
            # Generic HTTP error
            error_text = response.text[:200] if response.text else "No error details"
            return {
                "success": False,
                "message": f"Connection failed: HTTP {response.status_code}",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "unexpected_error",
                "error_details": f"HTTP {response.status_code}: {error_text}",
            }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "Connection timeout - check network and try again",
            "timestamp": timestamp,
            "response_time_ms": None,
            "error_code": "connection_timeout",
            "error_details": "Request timed out after 10 seconds. Check network connection, firewall settings, or VPN.",
        }

    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "message": "Cannot reach JIRA server - verify URL",
            "timestamp": timestamp,
            "response_time_ms": None,
            "error_code": "server_unreachable",
            "error_details": f"Connection error: {str(e)}. Check if the URL is correct and the server is accessible.",
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": "Network error occurred",
            "timestamp": timestamp,
            "response_time_ms": None,
            "error_code": "unexpected_error",
            "error_details": f"Request error: {str(e)}",
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "timestamp": timestamp,
            "response_time_ms": None,
            "error_code": "unexpected_error",
            "error_details": f"Exception: {type(e).__name__}: {str(e)}",
        }
