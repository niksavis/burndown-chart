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
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import requests

from configuration import logger

#######################################################################
# CONFIGURATION
#######################################################################

JIRA_CACHE_FILE = "jira_cache.json"
JIRA_CHANGELOG_CACHE_FILE = "jira_changelog_cache.json"
DEFAULT_CACHE_MAX_SIZE_MB = 100

# Cache version - increment when cache format changes or pagination logic changes
CACHE_VERSION = "2.0"  # v2.0: Pagination support added
CHANGELOG_CACHE_VERSION = "1.0"  # v1.0: Initial changelog cache implementation

# Cache expiration - invalidate cache after this duration
CACHE_EXPIRATION_HOURS = 24  # Cache expires after 24 hours

#######################################################################
# CORE JIRA FUNCTIONS
#######################################################################


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
            logger.info(f"✓ Issue count check: {total_count} issues for JQL query")
            return True, total_count
        else:
            logger.warning(f"Issue count check failed: HTTP {response.status_code}")
            return False, 0

    except Exception as e:
        logger.warning(f"Issue count check failed: {e}")
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
            logger.info(
                f"🗑️  Invalidated changelog cache: {cache_file} (issue cache refreshed)"
            )
            return True
        else:
            logger.info("✓ Changelog cache doesn't exist, no invalidation needed")
            return True
    except Exception as e:
        logger.error(f"Error invalidating changelog cache: {e}")
        return False


def get_jira_config(settings_jql_query: str | None = None) -> Dict:
    """
    Load JIRA configuration with priority hierarchy: jira_config → Environment → Default.

    This function reads from the jira_config structure in app_settings.json (managed via
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
        logger.warning(scriptrunner_warning)

    return True, "Configuration valid"


def fetch_jira_issues(
    config: Dict, max_results: int | None = None
) -> Tuple[bool, List[Dict]]:
    """
    Execute JQL query and return ALL issues using pagination.

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
    try:
        # Use max_results as page size (per API call), not total limit
        # JIRA API hard limit is 1000 per call
        page_size = (
            max_results if max_results is not None else config.get("max_results", 1000)
        )

        # Enforce JIRA API hard limit
        if page_size > 1000:
            logger.warning(
                f"Page size {page_size} exceeds JIRA API limit of 1000, using 1000"
            )
            page_size = 1000

        # Use the JQL query directly from configuration
        jql = config["jql_query"]

        # Get JIRA API endpoint (full URL)
        api_endpoint = config.get("api_endpoint", "")
        if not api_endpoint:
            logger.error("JIRA API endpoint not configured")
            return False, []

        # Use the full API endpoint directly
        url = api_endpoint

        # Headers
        headers = {"Accept": "application/json"}
        if config["token"]:
            headers["Authorization"] = f"Bearer {config['token']}"

        # Parameters - fetch required fields including field mappings for DORA/Flow
        # Base fields: always fetch these standard fields
        # CRITICAL: Include 'project' to enable filtering DevOps vs Development projects
        base_fields = "key,project,created,resolutiondate,status,issuetype"

        # Add story points field if specified
        additional_fields = []
        if config.get("story_points_field") and config["story_points_field"].strip():
            additional_fields.append(config["story_points_field"])

        # Add field mappings for DORA and Flow metrics
        field_mappings = config.get("field_mappings", {})
        for field_name, field_id in field_mappings.items():
            if field_id and field_id.strip() and field_id not in base_fields:
                # Add both custom fields (customfield_*) and standard fields
                # Skip if already in base_fields to avoid duplicates
                additional_fields.append(field_id)

        # Combine base fields with additional fields
        if additional_fields:
            fields = f"{base_fields},{','.join(set(additional_fields))}"
        else:
            fields = base_fields

        # Pagination: Fetch ALL issues in batches
        all_issues = []
        start_at = 0
        total_issues = None  # Will be set from first API response

        logger.info(f"Fetching JIRA issues from: {url}")
        logger.info(f"Using JQL: {jql}")
        logger.info(f"Page size: {page_size} per call, Fields: {fields}")

        while True:
            params = {
                "jql": jql,
                "maxResults": page_size,
                "startAt": start_at,
                "fields": fields,
            }

            logger.info(
                f"Fetching page starting at {start_at} (fetched {len(all_issues)} so far)"
            )
            response = requests.get(url, headers=headers, params=params, timeout=30)

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
                        f"JIRA ScriptRunner function error - JQL: {jql[:100]}..."
                    )
                    logger.error(
                        "ScriptRunner functions (issueFunction, etc.) may not be available on this JIRA instance"
                    )
                    logger.error(f"JIRA API Error Details: {error_details}")
                else:
                    logger.error(
                        f"JIRA API Error ({response.status_code}): {error_details}"
                    )

                return False, []

            data = response.json()
            issues_in_page = data.get("issues", [])

            # Get total from first response
            if total_issues is None:
                total_issues = data.get("total", 0)
                logger.info(
                    f"Query matches {total_issues} total issues, fetching all with pagination..."
                )

            # Add this page's issues to our collection
            all_issues.extend(issues_in_page)

            # Check if we've fetched everything
            if (
                len(issues_in_page) < page_size
                or start_at + len(issues_in_page) >= total_issues
            ):
                logger.info(
                    f"✓ Pagination complete: Fetched all {len(all_issues)} of {total_issues} JIRA issues"
                )
                break

            # Move to next page
            start_at += page_size

        return True, all_issues

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching JIRA issues: {e}")
        return False, []
    except Exception as e:
        logger.error(f"Unexpected error fetching JIRA issues: {e}")
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
        # Use smaller page size for changelog fetching (it's more expensive)
        page_size = (
            max_results
            if max_results is not None
            else min(config.get("max_results", 100), 100)
        )

        # Build JQL query
        if issue_keys:
            # Fetch specific issues by key
            keys_str = ", ".join(issue_keys)
            jql = f"key IN ({keys_str})"
            logger.info(f"Fetching changelog for {len(issue_keys)} specific issues")
        else:
            # Use base JQL + filter for completed issues only (performance optimization)
            base_jql = config["jql_query"]

            # Load completion statuses from configuration
            try:
                from configuration.dora_config import get_completion_status_names

                completion_statuses = get_completion_status_names()
                if completion_statuses:
                    statuses_str = ", ".join([f'"{s}"' for s in completion_statuses])
                    jql = f"({base_jql}) AND status IN ({statuses_str})"
                    logger.info(
                        f"Fetching changelog for completed issues only (statuses: {statuses_str})"
                    )
                else:
                    # Fallback: Use common completion statuses
                    jql = f'({base_jql}) AND status IN ("Done", "Resolved", "Closed")'
                    logger.warning(
                        "No completion statuses in config, using fallback: Done, Resolved, Closed"
                    )
            except Exception as e:
                logger.warning(f"Could not load completion statuses from config: {e}")
                jql = f'({base_jql}) AND status IN ("Done", "Resolved", "Closed")'

        # Get JIRA API endpoint
        api_endpoint = config.get("api_endpoint", "")
        if not api_endpoint:
            logger.error("JIRA API endpoint not configured")
            return False, []

        # Headers
        headers = {"Accept": "application/json"}
        if config["token"]:
            headers["Authorization"] = f"Bearer {config['token']}"

        # Fields to fetch (same as regular fetch + changelog)
        base_fields = "key,created,resolutiondate,status,issuetype,resolution"

        # Add story points field if specified
        additional_fields = []
        if config.get("story_points_field") and config["story_points_field"].strip():
            additional_fields.append(config["story_points_field"])

        # Add field mappings for DORA and Flow metrics
        field_mappings = config.get("field_mappings", {})
        for field_name, field_id in field_mappings.items():
            if field_id and field_id.strip() and field_id not in base_fields:
                # Add both custom fields and standard fields (no filtering)
                additional_fields.append(field_id)

        # Combine base fields with additional fields
        if additional_fields:
            fields = f"{base_fields},{','.join(set(additional_fields))}"
        else:
            fields = base_fields

        # Pagination: Fetch ALL issues with changelog in batches
        all_issues = []
        start_at = 0
        total_issues = None

        logger.info(f"Fetching JIRA issues WITH changelog from: {api_endpoint}")
        logger.info(f"Using JQL: {jql}")
        logger.info(
            f"Page size: {page_size} per call, Fields: {fields}, Expand: changelog"
        )

        while True:
            params = {
                "jql": jql,
                "maxResults": page_size,
                "startAt": start_at,
                "fields": fields,
                "expand": "changelog",  # THIS IS THE KEY: Expand changelog
            }

            # Progress reporting
            progress_msg = f"Fetching changelog page starting at {start_at} (fetched {len(all_issues)} so far)"
            logger.info(progress_msg)
            if progress_callback:
                if total_issues:
                    progress_callback(
                        f"📥 Downloading changelog: {len(all_issues)}/{total_issues} issues"
                    )
                else:
                    progress_callback(
                        f"📥 Downloading changelog: {len(all_issues)} issues"
                    )

            response = requests.get(
                api_endpoint, headers=headers, params=params, timeout=30
            )

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
                    f"JIRA API Error ({response.status_code}): {error_details}"
                )
                return False, []

            data = response.json()
            issues_in_page = data.get("issues", [])

            # Get total from first response
            if total_issues is None:
                total_issues = data.get("total", 0)
                logger.info(
                    f"Query matches {total_issues} total issues (with changelog), fetching all with pagination..."
                )

            # Add this page's issues to our collection
            all_issues.extend(issues_in_page)

            # Check if we've fetched everything
            if (
                len(issues_in_page) < page_size
                or start_at + len(issues_in_page) >= total_issues
            ):
                logger.info(
                    f"✓ Changelog pagination complete: Fetched all {len(all_issues)} of {total_issues} JIRA issues with changelog"
                )
                break

            # Move to next page
            start_at += page_size

        return True, all_issues

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching JIRA issues with changelog: {e}")
        return False, []
    except Exception as e:
        logger.error(f"Unexpected error fetching JIRA issues with changelog: {e}")
        return False, []


def cache_jira_response(
    data: List[Dict],
    jql_query: str = "",
    fields_requested: str = "",
    cache_file: str = JIRA_CACHE_FILE,
) -> bool:
    """Save raw JIRA JSON response to cache file with version, timestamp, and query tracking."""
    try:
        cache_data = {
            "cache_version": CACHE_VERSION,  # Track cache format version
            "timestamp": datetime.now().isoformat(),
            "jql_query": jql_query,  # Track which JQL query was used
            "fields_requested": fields_requested,  # Track which fields were requested
            "issues": data,
            "total_issues": len(data),
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        logger.info(
            f"Cached {len(data)} JIRA issues to {cache_file} (v{CACHE_VERSION}, JQL: {jql_query}, Fields: {fields_requested})"
        )
        return True

    except Exception as e:
        logger.error(f"Error caching JIRA response: {e}")
        return False


def load_jira_cache(
    current_jql_query: str = "",
    current_fields: str = "",
    cache_file: str = JIRA_CACHE_FILE,
) -> Tuple[bool, List[Dict]]:
    """
    Load cached JIRA JSON response from file with version and expiration validation.

    Cache is invalidated if:
    - Cache version doesn't match current version
    - Cache is older than CACHE_EXPIRATION_HOURS
    - JQL query doesn't match
    - Fields requested don't match
    """
    try:
        if not os.path.exists(cache_file):
            return False, []

        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        # Check cache version (invalidate if version mismatch)
        cached_version = cache_data.get("cache_version", "1.0")
        if cached_version != CACHE_VERSION:
            logger.info(
                f"Cache version mismatch. Cached: v{cached_version}, Current: v{CACHE_VERSION}. "
                f"Cache invalidated (pagination or format changed)."
            )
            return False, []

        # Check cache age (invalidate if too old)
        cache_timestamp_str = cache_data.get("timestamp", "")
        if cache_timestamp_str:
            try:
                cache_timestamp = datetime.fromisoformat(cache_timestamp_str)
                cache_age = datetime.now() - cache_timestamp
                if cache_age > timedelta(hours=CACHE_EXPIRATION_HOURS):
                    logger.info(
                        f"Cache expired. Age: {cache_age.total_seconds() / 3600:.1f} hours "
                        f"(max: {CACHE_EXPIRATION_HOURS} hours). Cache invalidated."
                    )
                    return False, []
            except ValueError:
                logger.warning(f"Invalid cache timestamp format: {cache_timestamp_str}")
                return False, []

        # Check if the cached query matches the current query
        cached_jql = cache_data.get("jql_query", "")
        if cached_jql != current_jql_query:
            logger.info(
                f"Cache JQL query mismatch. Cached: '{cached_jql}', Current: '{current_jql_query}'. Cache invalidated."
            )
            return False, []

        # Check if the cached fields match the current fields
        cached_fields = cache_data.get("fields_requested", "")
        if cached_fields and current_fields and cached_fields != current_fields:
            logger.info(
                f"Cache fields mismatch. Cached: '{cached_fields}', Current: '{current_fields}'. Cache invalidated."
            )
            return False, []

        # If no field info in old cache, check if current config needs story points field
        if not cached_fields and current_fields:
            # Extract story points field from current fields
            base_fields = "key,created,resolutiondate,status,issuetype"
            if current_fields != base_fields:  # User has story points field configured
                logger.info(
                    "Cache has no field info, but story points field is configured. Cache invalidated for field compatibility."
                )
                return False, []

        issues = cache_data.get("issues", [])
        cache_age_str = (
            f"{(datetime.now() - datetime.fromisoformat(cache_timestamp_str)).total_seconds() / 3600:.1f}h old"
            if cache_timestamp_str
            else "unknown age"
        )
        logger.info(
            f"✓ Loaded {len(issues)} JIRA issues from cache (v{cached_version}, {cache_age_str}, JQL: {cached_jql}, Fields: {cached_fields or 'base'})"
        )
        return True, issues

    except Exception as e:
        logger.error(f"Error loading JIRA cache: {e}")
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
                f"Cache file size ({file_size_mb:.2f} MB) exceeds limit ({max_size_mb} MB)"
            )
            return False

        # Check file integrity
        with open(cache_file, "r") as f:
            json.load(f)

        return True

    except Exception as e:
        logger.error(f"Cache file validation failed: {e}")
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
        logger.error(f"Error getting cache status: {e}")
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

        logger.info(
            f"Cached {len(issues_with_changelog)} JIRA issues WITH changelog to {cache_file} "
            f"(v{CHANGELOG_CACHE_VERSION}, JQL: {jql_query})"
        )
        return True

    except Exception as e:
        logger.error(f"Error caching changelog response: {e}")
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
            logger.info(
                f"Changelog cache version mismatch. Cached: v{cached_version}, Current: v{CHANGELOG_CACHE_VERSION}. "
                f"Cache invalidated."
            )
            return False, []

        # Check cache age
        cache_timestamp_str = cache_data.get("timestamp", "")
        if cache_timestamp_str:
            try:
                cache_timestamp = datetime.fromisoformat(cache_timestamp_str)
                cache_age = datetime.now() - cache_timestamp
                if cache_age > timedelta(hours=CACHE_EXPIRATION_HOURS):
                    logger.info(
                        f"Changelog cache expired. Age: {cache_age.total_seconds() / 3600:.1f} hours "
                        f"(max: {CACHE_EXPIRATION_HOURS} hours). Cache invalidated."
                    )
                    return False, []
            except ValueError:
                logger.warning(
                    f"Invalid changelog cache timestamp format: {cache_timestamp_str}"
                )
                return False, []

        # Check if the cached query matches the current query
        cached_jql = cache_data.get("jql_query", "")
        if cached_jql != current_jql_query:
            logger.info(
                f"Changelog cache JQL query mismatch. Cached: '{cached_jql}', Current: '{current_jql_query}'. "
                f"Cache invalidated."
            )
            return False, []

        # Check if the cached fields match the current fields (optional check)
        cached_fields = cache_data.get("fields_requested", "")
        if cached_fields and current_fields and cached_fields != current_fields:
            logger.info(
                f"Changelog cache fields mismatch. Cached: '{cached_fields}', Current: '{current_fields}'. "
                f"Cache invalidated."
            )
            return False, []

        issues = cache_data.get("issues", [])
        cache_age_str = (
            f"{(datetime.now() - datetime.fromisoformat(cache_timestamp_str)).total_seconds() / 3600:.1f}h old"
            if cache_timestamp_str
            else "unknown age"
        )
        logger.info(
            f"✓ Loaded {len(issues)} JIRA issues WITH changelog from cache "
            f"(v{cached_version}, {cache_age_str}, JQL: {cached_jql})"
        )
        return True, issues

    except Exception as e:
        logger.error(f"Error loading changelog cache: {e}")
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
            f"Complex field '{field_name}' has no extractable numeric value: {story_points_value}"
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
                f"Field '{field_name}' contains non-numeric string: '{story_points_value}'"
            )
            return 0.0

    # Unknown type
    logger.warning(
        f"Field '{field_name}' has unexpected type {type(story_points_value)}: {story_points_value}"
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
            logger.warning("No valid dates found in JIRA issues")
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

        logger.info(f"Generated {len(weekly_data)} weekly data points from JIRA")
        return weekly_data

    except Exception as e:
        logger.error(f"Error transforming JIRA data: {e}")
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
        if config.get("story_points_field") and config["story_points_field"].strip():
            additional_fields.append(config["story_points_field"])

        # Add field mappings for DORA and Flow metrics
        field_mappings = config.get("field_mappings", {})
        for field_name, field_id in field_mappings.items():
            if field_id and field_id.strip() and field_id not in base_fields:
                additional_fields.append(field_id)

        # Build final fields string (must match fetch_jira_issues exactly)
        if additional_fields:
            current_fields = f"{base_fields},{','.join(set(additional_fields))}"
        else:
            current_fields = base_fields

        # SMART CACHING LOGIC
        # Step 1: Check if force refresh is requested
        if force_refresh:
            logger.info("🔄 Force refresh requested - bypassing cache")
            cache_loaded = False
            issues = []
        else:
            # Step 2: Try to load from cache (checks version, age, JQL, fields)
            cache_loaded, issues = load_jira_cache(config["jql_query"], current_fields)

            # Step 3: If cache is valid, do a quick count check to detect changes
            if cache_loaded and issues:
                logger.info(
                    f"Cache loaded: {len(issues)} issues. Checking if count changed..."
                )
                count_success, current_count = check_jira_issue_count(
                    config["jql_query"], config
                )

                if count_success and current_count != len(issues):
                    logger.info(
                        f"🔄 Issue count changed: {len(issues)} → {current_count}. "
                        f"Cache invalidated, fetching fresh data."
                    )
                    cache_loaded = False  # Force refresh due to count mismatch
                elif count_success:
                    logger.info(
                        f"✓ Issue count unchanged ({current_count} issues). Using cache."
                    )
                else:
                    logger.warning("Count check failed. Using cache anyway (fallback).")

        # Step 4: Fetch from JIRA if cache is invalid or force refresh
        if not cache_loaded or not issues:
            # Fetch fresh data from JIRA
            fetch_success, issues = fetch_jira_issues(config)
            if not fetch_success:
                return False, "Failed to fetch JIRA data", {}

            # Cache the response with the JQL query and fields used
            if not cache_jira_response(issues, config["jql_query"], current_fields):
                logger.warning("Failed to cache JIRA response")

            # CRITICAL: Invalidate changelog cache when issue cache is refreshed
            # Changelog must stay in sync with issues
            invalidate_changelog_cache()

        # PHASE 2: Changelog data fetch (OPTIONAL - don't block app)
        # Changelog is only needed for Flow Time and DORA metrics
        # Skip it for now - it will be fetched in background if needed
        logger.info(
            "⚡ Skipping changelog fetch for fast startup. "
            "Changelog will be loaded on-demand for Flow/DORA metrics."
        )

        # CRITICAL: Filter out DevOps project issues for burndown/velocity/statistics
        # DevOps issues are ONLY used for DORA metrics metadata extraction
        devops_projects = config.get("devops_projects", [])
        logger.info(f"DEBUG: Config keys available: {list(config.keys())}")
        logger.info(f"DEBUG: devops_projects from config: {devops_projects}")
        if devops_projects:
            from data.project_filter import filter_development_issues

            total_issues_count = len(issues)
            issues_for_metrics = filter_development_issues(issues, devops_projects)
            filtered_count = total_issues_count - len(issues_for_metrics)

            if filtered_count > 0:
                logger.info(
                    f"Filtered out {filtered_count} DevOps project issues from {total_issues_count} total issues. "
                    f"Using {len(issues_for_metrics)} development project issues for burndown/velocity/statistics."
                )
        else:
            # No DevOps projects configured, use all issues
            issues_for_metrics = issues

        # Calculate JIRA-based project scope (using ONLY development project issues)
        # Only use story_points_field if it's configured and not empty
        points_field = config.get("story_points_field", "").strip()
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
            logger.info("JIRA scope calculation and data sync completed successfully")
            return (
                True,
                "JIRA sync and scope calculation completed successfully",
                scope_data,
            )
        else:
            return False, "Failed to save JIRA data to unified structure", {}

    except Exception as e:
        logger.error(f"Error in JIRA scope sync: {e}")
        return False, f"JIRA scope sync failed: {e}", {}


def sync_jira_data(
    jql_query: str | None = None, ui_config: Dict | None = None
) -> Tuple[bool, str]:
    """Legacy sync function - calls new scope sync and returns just success/message."""
    try:
        success, message, scope_data = sync_jira_scope_and_data(jql_query, ui_config)
        return success, message
    except Exception as e:
        logger.error(f"Error in JIRA data sync: {e}")
        return False, f"JIRA sync failed: {e}"


def fetch_changelog_on_demand(config: Dict, progress_callback=None) -> Tuple[bool, str]:
    """
    Fetch changelog data separately for Flow Time and DORA metrics.
    This is a background operation that doesn't block the main app.

    Args:
        config: JIRA configuration dictionary with API endpoint, token, etc.
        progress_callback: Optional callback function(message: str) for progress updates

    Returns:
        Tuple of (success, message)
    """
    try:
        logger.info("📊 Fetching changelog data for Flow Time and DORA metrics...")
        if progress_callback:
            progress_callback("📊 Starting changelog download...")

        changelog_fetch_success, issues_with_changelog = (
            fetch_jira_issues_with_changelog(
                config, progress_callback=progress_callback
            )
        )

        if changelog_fetch_success:
            # CRITICAL OPTIMIZATION: Filter changelog to ONLY status transitions
            # This dramatically reduces cache file size (from 1M+ lines to ~50K)
            try:
                import json
                from datetime import datetime

                # Build optimized changelog cache: Keep ONLY status change histories
                changelog_cache = {}
                total_histories_before = 0
                total_histories_after = 0

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
                        changelog_cache[issue_key] = {
                            "changelog": {
                                "histories": status_histories,
                                "total": len(status_histories),
                            },
                            "last_updated": datetime.now().isoformat(),
                        }

                # Progress update: Processing/optimizing
                if progress_callback:
                    progress_callback(
                        f"💾 Optimizing changelog data for {len(changelog_cache)} issues..."
                    )

                # Save optimized changelog to jira_changelog_cache.json
                changelog_cache_file = "jira_changelog_cache.json"
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

                optimization_msg = f"✅ Optimized changelog cache: {total_histories_before} → {total_histories_after} histories ({reduction_pct:.1f}% reduction) for {len(changelog_cache)} issues"
                logger.info(optimization_msg)
                logger.info(f"✅ Saved optimized changelog to {changelog_cache_file}")

                if progress_callback:
                    progress_callback(
                        f"✅ Changelog saved: {len(changelog_cache)} issues ({reduction_pct:.0f}% optimized)"
                    )

                return (
                    True,
                    f"Changelog data fetched for {len(changelog_cache)} issues (optimized: {reduction_pct:.0f}% size reduction)",
                )
            except Exception as e:
                logger.warning(f"Failed to cache changelog data: {e}")
                return False, f"Failed to cache changelog: {e}"
        else:
            logger.warning(
                "Failed to fetch changelog data. Flow Time and Flow Efficiency metrics may be limited."
            )
            return False, "Failed to fetch changelog data from JIRA"

    except Exception as e:
        logger.error(f"Error fetching changelog on demand: {e}")
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

        logger.info(f"Testing JQL query: {jql[:100]}...")
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
            logger.info(f"JQL query valid - would return {total} issues")
            return True, f"JQL query is valid (would return {total} issues)"
        except ValueError as json_error:
            # Response was 200 OK but body is not valid JSON - API version likely not supported
            logger.error(f"JIRA returned HTTP 200 but invalid JSON: {json_error}")
            logger.error(f"Response body (first 200 chars): {response.text[:200]}")
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

        # Construct serverInfo endpoint (use API v2 as it's more universally supported)
        server_info_url = f"{clean_url}/rest/api/2/serverInfo"

        # Prepare headers with authentication
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Make request with timeout
        logger.info(f"Testing JIRA connection to: {server_info_url}")
        response = requests.get(server_info_url, headers=headers, timeout=10)

        response_time_ms = int((time.time() - start_time) * 1000)

        # Check response status
        if response.status_code == 200:
            server_info = response.json()

            # Additional check: Verify the search endpoint with specified API version
            search_endpoint = construct_jira_endpoint(base_url, api_version)
            logger.info(f"Verifying search endpoint: {search_endpoint}")

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
                    f"API version check: {api_version_name} NOT available (status {search_response.status_code})"
                )
                try:
                    error_data = search_response.json()
                    logger.warning(f"Search endpoint error details: {error_data}")
                except Exception:
                    logger.warning(
                        f"Search endpoint returned {search_response.status_code} without JSON body"
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
                            f"API version check: {api_version} VERIFIED (status 200, valid JSON)"
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
                            f"API {api_version} returned JSON but unexpected structure: {list(search_data.keys())}"
                        )
                except ValueError as json_error:
                    # Status 200 but body is not JSON - API version doesn't work
                    logger.warning(
                        f"API {api_version} returned 200 but invalid JSON: {json_error}"
                    )
                    logger.warning(
                        f"Response body (first 200 chars): {search_response.text[:200]}"
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
                f"API version check: {api_version_name} NOT available (unexpected status {search_response.status_code})"
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
