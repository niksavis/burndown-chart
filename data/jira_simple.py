"""
JIRA API Integration Module

This module provides minimal JIRA API integration for the burndown chart application.
It fetches JIRA issues and transforms them to match the existing CSV statistics format.
"""

#######################################################################
# IMPORTS
#######################################################################
from datetime import timedelta
from typing import Dict, List, Tuple

import requests

from configuration import logger
from data.jira import (
    get_jira_config,
    validate_jira_config,
    generate_config_hash,
    extract_jira_field_id,
    validate_cache_file,
    invalidate_changelog_cache,
    check_jira_issue_count,
    jira_to_csv_format,
    CACHE_EXPIRATION_HOURS,
)

# Two-phase fetch optimization
from data.jira.two_phase_fetch import (
    should_use_two_phase_fetch,
    fetch_jira_issues_two_phase,
)

# Changelog fetching
from data.jira.changelog_fetcher import fetch_jira_issues_with_changelog

# Delta fetch optimization
from data.jira.delta_fetch import (
    save_delta_fetch_result,
    try_delta_fetch,
)

# Cache operations
from data.jira.cache_operations import cache_jira_response

# Aliasing for backward compatibility within this file
_extract_jira_field_id = extract_jira_field_id
_generate_config_hash = generate_config_hash
_try_delta_fetch = try_delta_fetch
_save_delta_fetch_result = save_delta_fetch_result

#######################################################################
# Removed duplicate function definitions - now using imports from data.jira module
# Functions imported and available:
# - get_jira_config, validate_jira_config
# - generate_config_hash, extract_jira_field_id
# - validate_cache_file, invalidate_changelog_cache, check_jira_issue_count
# - jira_to_csv_format (data transformation)
# - should_use_two_phase_fetch, fetch_jira_issues_two_phase (two-phase optimization)
#######################################################################


def _fetch_jira_paginated(
    config: Dict, max_results: int | None = None
) -> Tuple[bool, List[Dict]]:
    """
    Internal helper: Execute paginated JIRA fetch without caching or count checks.

    This is a stripped-down version of fetch_jira_issues that only does the core
    API pagination logic. Used by two-phase fetch to avoid cache interference.

    Args:
        config: Configuration dictionary with API endpoint, JQL query, token, etc.
        max_results: Page size for each API call (default: from config or 1000)

    Returns:
        Tuple of (success: bool, issues: List[Dict])
    """
    import requests
    from data.jira_query_manager import get_rate_limiter, retry_with_backoff

    try:
        # Get configuration
        jql = config["jql_query"]
        api_endpoint = config.get("api_endpoint", "")
        if not api_endpoint:
            logger.error("[FETCH] API endpoint not configured")
            return False, []

        # Determine fields to fetch (reuse logic from main fetch function)
        if config.get("fields"):
            fields = config["fields"]
        else:
            # CRITICAL: Include fixVersions in base fields for DORA metrics
            # fixVersions needed for:
            # - Two-phase fetch filtering (extract from dev, use in DevOps query)
            # - Deployment Frequency (fixVersion.releaseDate)
            # - Lead Time for Changes (link dev issues to deployments via fixVersion)
            base_fields = "key,summary,project,created,updated,resolutiondate,status,issuetype,assignee,priority,resolution,labels,components,fixVersions"
            additional_fields = []

            if (
                config.get("story_points_field")
                and config["story_points_field"].strip()
            ):
                additional_fields.append(config["story_points_field"])

            field_mappings = config.get("field_mappings", {})
            for category, mappings in field_mappings.items():
                if isinstance(mappings, dict):
                    for field_name, field_id in mappings.items():
                        clean_field_id = _extract_jira_field_id(field_id)
                        if clean_field_id and clean_field_id not in base_fields:
                            additional_fields.append(clean_field_id)

            if additional_fields:
                fields = f"{base_fields},{','.join(sorted(set(additional_fields)))}"
            else:
                fields = base_fields

        # Pagination settings
        page_size = max_results or config.get("max_results", 1000)
        if page_size > 1000:
            page_size = 1000

        # Prepare request
        headers = {
            "Authorization": f"Bearer {config['token']}",
            "Content-Type": "application/json",
        }

        all_issues = []
        start_at = 0
        total_issues = None
        rate_limiter = get_rate_limiter()

        # Pagination loop
        while True:
            # Rate limiting
            rate_limiter.wait_for_token()

            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": page_size,
                "fields": fields,
            }

            # Make request with retry logic
            success, response = retry_with_backoff(
                requests.get,
                api_endpoint,
                headers=headers,
                params=params,
                timeout=30,
            )

            if not success or response.status_code != 200:
                error_msg = (
                    f"HTTP {response.status_code}"
                    if hasattr(response, "status_code")
                    else "Network error"
                )
                logger.error(f"[FETCH] API error: {error_msg}")

                # Log JIRA error details if available
                if hasattr(response, "text"):
                    try:
                        error_data = response.json()
                        logger.error(f"[FETCH] JIRA error: {error_data}")
                    except Exception:
                        logger.error(f"[FETCH] Response: {response.text[:500]}")

                # Log the JQL that caused the error
                jql_preview = jql[:200] + "..." if len(jql) > 200 else jql
                logger.error(f"[FETCH] Failed JQL: {jql_preview}")

                return False, []

            data = response.json()
            issues_in_page = data.get("issues", [])

            if total_issues is None:
                total_issues = data.get("total", 0)
                logger.debug(f"[FETCH] Query matched {total_issues} issues")

            all_issues.extend(issues_in_page)

            # Check if pagination complete
            if (
                len(issues_in_page) < page_size
                or start_at + len(issues_in_page) >= total_issues
            ):
                break

            start_at += page_size

        logger.debug(f"[FETCH] Fetched {len(all_issues)} issues")
        return True, all_issues

    except Exception as e:
        logger.error(f"[FETCH] Error: {e}", exc_info=True)
        return False, []


def fetch_jira_issues(
    config: Dict, max_results: int | None = None, force_refresh: bool = False
) -> Tuple[bool, List[Dict]]:
    """
    Execute JQL query and return ALL issues using pagination with incremental fetch optimization.

    TWO-PHASE FETCH OPTIMIZATION (NEW):
    - If DevOps projects configured, automatically uses two-phase fetch
    - Phase 1: Fetch development projects (user's JQL)
    - Phase 2: Extract fixVersions, build dynamic DevOps query
    - Phase 3: Fetch only DevOps issues matching development fixVersions
    - Phase 4: Merge results
    - Result: 10x+ faster for large DevOps projects

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
        force_refresh: If True, bypass cache and force fresh fetch from JIRA API

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
            # Include summary, assignee, priority, resolution, labels, components for Sprint Tracker and Portfolio view
            base_fields = "key,summary,project,created,updated,resolutiondate,status,issuetype,assignee,priority,resolution,labels,components,fixVersions"

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

        # ===== TWO-PHASE FETCH CHECK =====
        # Determine if we should use two-phase fetch, but don't execute yet
        # We'll use it in the fetch logic below after checking cache/delta
        use_two_phase, two_phase_reason = should_use_two_phase_fetch(config)

        if use_two_phase:
            logger.info(f"[JIRA] Two-phase fetch activated: {two_phase_reason}")
        else:
            logger.debug(f"[JIRA] Using standard fetch: {two_phase_reason}")

        # ===== T051: INCREMENTAL FETCH OPTIMIZATION =====
        # Check if data has changed before doing expensive full fetch
        # Generate cache key and config hash regardless of force_refresh
        from data.cache_manager import generate_jira_data_cache_key

        cache_key = generate_jira_data_cache_key(
            jql_query=jql,
            time_period_days=30,  # Default time period
        )
        config_hash = _generate_config_hash(config, fields)

        # Skip cache check if force_refresh is True
        if force_refresh:
            logger.info(
                "[JIRA] Force refresh requested - bypassing incremental fetch cache"
            )
            is_valid = False
            cached_data = None
        else:
            logger.info("[JIRA] Checking if data has changed (incremental fetch)")

            # Try to load cached data from profile-based cache
            # Use the same cache file that delta fetch saves to
            from data.profile_manager import get_active_query_workspace

            query_workspace = get_active_query_workspace()
            cache_file = query_workspace / "jira_cache.json"

            is_valid = False
            cached_data = None

            if cache_file.exists():
                try:
                    import json

                    with open(cache_file, "r") as f:
                        cache_metadata = json.load(f)

                    # Validate cache structure
                    if "timestamp" in cache_metadata and "issues" in cache_metadata:
                        # Check age
                        from datetime import datetime, timezone

                        cache_timestamp = datetime.fromisoformat(
                            cache_metadata["timestamp"]
                        )
                        if cache_timestamp.tzinfo is None:
                            cache_timestamp = cache_timestamp.replace(
                                tzinfo=timezone.utc
                            )

                        now_utc = datetime.now(timezone.utc)
                        age_hours = (now_utc - cache_timestamp).total_seconds() / 3600

                        if age_hours <= CACHE_EXPIRATION_HOURS:
                            cached_data = cache_metadata["issues"]
                            is_valid = True
                            logger.info(
                                f"[JIRA] Cache valid: {len(cached_data)} issues ({age_hours:.1f}h old)"
                            )
                        else:
                            logger.debug(
                                f"[JIRA] Cache expired: {age_hours:.1f}h old (max: {CACHE_EXPIRATION_HOURS}h)"
                            )
                    else:
                        logger.warning("[JIRA] Cache invalid: missing required fields")
                except Exception as e:
                    logger.warning(f"[JIRA] Cache read error: {e}")
            else:
                logger.debug("[JIRA] No cache file found")

        if is_valid and cached_data:
            logger.info(
                f"[JIRA] Cache valid, checking for changes ({len(cached_data)} cached issues)"
            )

            # CRITICAL: When two-phase fetch is active, skip count check
            # The count check uses user's JQL (dev issues only), but two-phase fetches dev+devops
            # This causes false "count mismatch" and unnecessary full fetches
            if use_two_phase:
                logger.info(
                    "[JIRA] Two-phase fetch active, skipping count check, trying delta fetch"
                )
                delta_success, merged_issues, changed_keys = _try_delta_fetch(
                    jql, config, cached_data, api_endpoint, start_time
                )
                if delta_success:
                    _save_delta_fetch_result(merged_issues, changed_keys, jql, fields)
                    # CRITICAL: Update database timestamp
                    cache_jira_response(
                        data=merged_issues,
                        jql_query=jql,
                        fields_requested=fields,
                        config=config,
                    )
                    return True, merged_issues
                # Delta fetch failed, fall through to full fetch
            else:
                # We have valid cache, now check if JIRA data changed
                # Use fast count check (maxResults=0, returns only total count)
                success, current_count = check_jira_issue_count(jql, config)

                if success:
                    cached_count = len(cached_data)
                    count_diff = abs(current_count - cached_count)

                    # If count differs by more than 5%, likely deletions or major changes
                    if count_diff > max(cached_count * 0.05, 5):
                        logger.info(
                            f"[JIRA] Significant count change: {cached_count} -> {current_count} ({count_diff} diff), full fetch"
                        )
                    elif current_count == cached_count:
                        # Try delta fetch - only get issues updated since last cache
                        delta_success, merged_issues, changed_keys = _try_delta_fetch(
                            jql, config, cached_data, api_endpoint, start_time
                        )
                        if delta_success:
                            # Save merged issues with changed keys metadata
                            _save_delta_fetch_result(
                                merged_issues, changed_keys, jql, fields
                            )
                            # CRITICAL: Update database timestamp even if 0 issues changed
                            # This ensures "last checked" timestamp reflects when Update Data was clicked,
                            # not just when data last changed
                            cache_jira_response(
                                data=merged_issues,
                                jql_query=jql,
                                fields_requested=fields,
                                config=config,
                            )
                            return True, merged_issues
                        # Delta fetch failed, fall through to full fetch
                    else:
                        # Small count difference, might be few new/deleted issues
                        # Try delta fetch first
                        logger.info(
                            f"[JIRA] Small count change: {cached_count} -> {current_count}, trying delta fetch"
                        )
                        delta_success, merged_issues, changed_keys = _try_delta_fetch(
                            jql, config, cached_data, api_endpoint, start_time
                        )
                        if delta_success:
                            # Save merged issues with changed keys metadata
                            _save_delta_fetch_result(
                                merged_issues, changed_keys, jql, fields
                            )
                            # CRITICAL: Update database timestamp even if few issues changed
                            cache_jira_response(
                                data=merged_issues,
                                jql_query=jql,
                                fields_requested=fields,
                                config=config,
                            )
                            return True, merged_issues
                        # Delta fetch failed, fall through to full fetch
                else:
                    # Count check failed - but we can still try delta fetch with cached data
                    logger.warning(
                        "[JIRA] Count check failed, trying delta fetch anyway"
                    )
                    delta_success, merged_issues, changed_keys = _try_delta_fetch(
                        jql, config, cached_data, api_endpoint, start_time
                    )
                    if delta_success:
                        # Save merged issues with changed keys metadata
                        _save_delta_fetch_result(
                            merged_issues, changed_keys, jql, fields
                        )
                        # CRITICAL: Update database timestamp even if count check failed
                        cache_jira_response(
                            data=merged_issues,
                            jql_query=jql,
                            fields_requested=fields,
                            config=config,
                        )
                        logger.info(
                            "[JIRA] Delta fetch succeeded despite count check failure"
                        )
                        return True, merged_issues
                    # Delta fetch also failed, fall through to full fetch
                    logger.warning(
                        "[JIRA] Count check and delta fetch failed, proceeding with full fetch"
                    )
        else:
            if not is_valid:
                logger.warning(
                    f"[JIRA] Cache invalid (is_valid={is_valid}, has_data={cached_data is not None}), fetching from API"
                )
            else:
                logger.info("[JIRA] Cache miss, fetching from API")

        # ===== PROCEED WITH FULL FETCH (cache miss or data changed) =====

        # Use two-phase fetch if applicable, otherwise standard fetch
        if use_two_phase:
            logger.info("[JIRA] Executing two-phase fetch...")
            success, all_issues = fetch_jira_issues_two_phase(
                config,
                max_results,
                force_refresh,
                fetch_paginated_func=_fetch_jira_paginated,
            )
            if not success:
                logger.error("[JIRA] Two-phase fetch failed")
                return False, []

            # Cache the two-phase results to profile-specific location
            from data.profile_manager import get_active_query_workspace

            query_workspace = get_active_query_workspace()
            jira_cache_file = str(query_workspace / "jira_cache.json")
            cache_jira_response(
                data=all_issues,
                jql_query=jql,
                fields_requested=fields,
                cache_file=jira_cache_file,
                config=config,
            )
            return True, all_issues

        # Standard fetch for non-two-phase scenarios
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

            # Check for cancellation BEFORE making API call
            try:
                from data.task_progress import TaskProgress

                # Check if task was cancelled
                is_cancelled = TaskProgress.is_task_cancelled()
                logger.debug(f"[JIRA] Cancellation check: is_cancelled={is_cancelled}")
                if is_cancelled:
                    logger.info(
                        f"[JIRA] Fetch cancelled by user after {len(all_issues)} issues"
                    )
                    TaskProgress.fail_task("update_data", "Operation cancelled by user")
                    return False, []

                # Report progress
                if total_issues:
                    TaskProgress.update_progress(
                        "update_data",
                        "fetch",
                        current=len(all_issues),
                        total=total_issues,
                        message="Fetching issues from JIRA",
                    )
                else:
                    # First batch or unknown total
                    msg = (
                        "Connecting to JIRA..."
                        if start_at == 0
                        else f"Fetching issues ({len(all_issues)} so far)..."
                    )
                    TaskProgress.update_progress(
                        "update_data",
                        "fetch",
                        current=len(all_issues),
                        total=0,
                        message=msg,
                    )
            except Exception as e:
                logger.debug(f"Progress update/cancellation check failed: {e}")

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
        # CRITICAL: Save with metadata needed for delta fetch
        from data.profile_manager import get_active_query_workspace
        from datetime import datetime, timezone
        import hashlib
        import json

        query_workspace = get_active_query_workspace()
        cache_file_path = query_workspace / "jira_cache.json"

        # Generate JQL hash for delta fetch validation
        jql_hash = hashlib.sha256(jql.encode()).hexdigest()[:16]

        # Create cache with metadata including last_updated for delta fetch
        cache_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),  # For delta fetch
            "jql_hash": jql_hash,  # For delta fetch validation
            "jql_query": jql,
            "cache_key": cache_key,
            "config_hash": config_hash,
            "issues": all_issues,
        }

        try:
            with open(cache_file_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
            logger.info(
                f"[Cache] Saved {len(all_issues)} issues with delta fetch metadata"
            )
        except Exception as e:
            logger.warning(f"[Cache] Failed to save cache file: {e}")

        elapsed_time = time.time() - start_time
        logger.info(
            f"[JIRA] Fetch complete: {len(all_issues)} issues in {elapsed_time:.2f}s"
        )

        # CRITICAL FIX: Save issues to database for standard fetch path
        # Previously only two-phase fetch saved to DB, causing changelog fetch to fail
        # because it couldn't find any issues in the database
        cache_jira_response(
            data=all_issues,
            jql_query=jql,
            fields_requested=fields,
            cache_file=str(cache_file_path),
            config=config,
        )

        return True, all_issues

    except requests.exceptions.RequestException as e:
        logger.error(f"[JIRA] Network error: {e}")
        return False, []
    except Exception as e:
        logger.error(f"[JIRA] Unexpected error: {e}")
        return False, []


# cache_jira_response, load_jira_cache, load_changelog_cache moved to cache_operations.py


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
    # Import TaskProgress at function level to avoid "possibly unbound" errors
    from data.task_progress import TaskProgress

    try:
        # Update progress to show we're starting
        try:
            TaskProgress.update_progress(
                "update_data",
                "fetch",
                0,
                0,
                "Connecting to JIRA...",
            )
        except Exception:
            pass  # Progress update is optional

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
        base_fields = "key,summary,project,created,updated,resolutiondate,status,issuetype,assignee,priority,resolution,labels,components,fixVersions"
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
            logger.debug("[JIRA] Force refresh - bypassing cache and clearing database")

            # CRITICAL: Clear database cache for this query on force refresh
            # This ensures old issues that no longer match the JQL are removed
            try:
                from data.persistence.factory import get_backend
                from data.database import get_db_connection
                from pathlib import Path

                backend = get_backend()
                active_profile_id = backend.get_app_state("active_profile_id")
                active_query_id = backend.get_app_state("active_query_id")

                if active_profile_id and active_query_id:
                    # Delete all data for this query ATOMICALLY (single transaction)
                    # This prevents intermediate states where UI reads partial data
                    db_path = getattr(backend, "db_path", Path("profiles/burndown.db"))
                    with get_db_connection(Path(db_path)) as conn:
                        cursor = conn.cursor()

                        # Execute all deletions in one transaction
                        cursor.execute(
                            "DELETE FROM jira_issues WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        deleted_count = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM project_statistics WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        stats_deleted = cursor.rowcount

                        # Note: jira_cache table removed - cache metadata derived from jira_issues

                        cursor.execute(
                            "DELETE FROM jira_changelog_entries WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        changelog_deleted = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM metrics_data_points WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        metrics_deleted = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM project_scope WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        scope_deleted = cursor.rowcount

                        cursor.execute(
                            "DELETE FROM task_progress WHERE profile_id = ? AND query_id = ?",
                            (active_profile_id, active_query_id),
                        )
                        task_deleted = cursor.rowcount

                        # Single commit for all deletions (atomic operation)
                        conn.commit()

                        logger.info(
                            f"[JIRA] Force refresh atomically deleted: {deleted_count} issues, "
                            f"{stats_deleted} statistics, "
                            f"{changelog_deleted} changelog entries, {metrics_deleted} metrics, "
                            f"{scope_deleted} scope, {task_deleted} tasks from database"
                        )

            except Exception as e:
                logger.warning(f"[JIRA] Failed to clear database cache: {e}")

        # Step 2: Fetch from JIRA (includes built-in delta fetch optimization)
        # fetch_jira_issues() handles all caching logic internally:
        # - Loads cache and checks if data changed
        # - Does delta fetch (fetch only updated issues) if count unchanged
        # - Does full fetch only if cache invalid or delta fetch fails
        logger.debug(
            "[JIRA] Calling fetch_jira_issues (handles cache/delta internally)"
        )

        fetch_success, issues = fetch_jira_issues(config, force_refresh=force_refresh)
        if not fetch_success:
            return False, "Failed to fetch JIRA data", {}

        logger.info(f"[JIRA] Fetch complete: {len(issues)} issues")

        # Update progress: Issues fetched, now starting changelog
        try:
            TaskProgress.update_progress(
                "update_data",
                "fetch",
                current=len(issues),
                total=len(issues),
                message="Issues fetched, preparing changelog download...",
            )
        except Exception:
            pass

        # CRITICAL: Invalidate changelog cache when we fetch from JIRA
        # Changelog must stay in sync with issue cache
        invalidate_changelog_cache()

        # PHASE 2: Changelog data fetch
        # Changelog is needed for Flow Time and DORA metrics
        # No need to delete file cache - using database exclusively

        # Fetch it now so metrics calculation has the data it needs
        # CRITICAL: Get profile/query IDs before calling fetch to avoid race condition
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        logger.info("[JIRA] Fetching changelog data for Flow/DORA metrics...")
        changelog_success, changelog_message = fetch_changelog_on_demand(
            config,
            profile_id=active_profile_id,
            query_id=active_query_id,
            progress_callback=None,
        )
        if changelog_success:
            logger.info(f"[JIRA] Changelog fetch successful: {changelog_message}")
        else:
            logger.warning(
                f"[JIRA] Changelog fetch failed (non-critical): {changelog_message}"
            )

        # Update progress: Changelog done, now calculating scope
        try:
            TaskProgress.update_progress(
                "update_data",
                "fetch",
                current=len(issues),
                total=len(issues),
                message="Processing issues and calculating scope...",
            )
        except Exception:
            pass

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

        # Update progress: Scope calculated, now saving to database
        try:
            TaskProgress.update_progress(
                "update_data",
                "fetch",
                current=len(issues),
                total=len(issues),
                message="Saving data to database...",
            )
        except Exception:
            pass

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


def fetch_changelog_on_demand(
    config: Dict,
    profile_id: str | None = None,
    query_id: str | None = None,
    progress_callback=None,
) -> Tuple[bool, str]:
    """
    Fetch changelog data separately for Flow Time and DORA metrics with incremental saving.

    OPTIMIZATION: Only fetches changelog for issues NOT already in cache.
    This dramatically improves performance on subsequent "Update Data" operations.

    RESILIENCE FEATURES:
    - Saves progress after each page (prevents data loss on timeout)
    - Retries failed requests up to 3 times
    - Returns partial results if download incomplete
    - Uses 90-second timeout for large changelog payloads

    Args:
        config: JIRA configuration dictionary with API endpoint, token, etc.
        profile_id: Profile ID to fetch changelog for (if None, reads from app_state)
        query_id: Query ID to fetch changelog for (if None, reads from app_state)
        progress_callback: Optional callback function(message: str) for progress updates

    Returns:
        Tuple of (success, message)
    """
    from datetime import datetime

    logger.info("Fetching changelog for profile/query: %s/%s", profile_id, query_id)

    try:
        logger.info("[JIRA] Fetching changelog data for Flow Time and DORA metrics")
        if progress_callback:
            progress_callback("[Stats] Starting changelog download...")

        # Get active profile and query from database if not provided
        from data.persistence.factory import get_backend

        backend = get_backend()

        if not profile_id:
            profile_id = backend.get_app_state("active_profile_id")
        if not query_id:
            query_id = backend.get_app_state("active_query_id")

        if not profile_id or not query_id:
            logger.error("[Database] No active profile/query - cannot fetch changelog")
            return False, "No active profile/query"

        # Load existing changelog from database to determine what's already cached
        cached_issue_keys = set()
        try:
            existing_entries = backend.get_changelog_entries(
                profile_id=profile_id, query_id=query_id
            )
            # Get unique issue keys from existing entries
            cached_issue_keys = set(
                entry.get("issue_key")
                for entry in existing_entries
                if entry.get("issue_key")
            )
            logger.info(
                f"[Database] Loaded {len(cached_issue_keys)} unique issues with changelog from database"
            )
        except Exception as e:
            logger.warning(f"[Database] Could not load existing changelog: {e}")
            cached_issue_keys = set()

        # Get all issues from database to determine which need changelog fetching
        issues_needing_changelog: list[str] | None = []
        try:
            all_issues = backend.get_issues(profile_id=profile_id, query_id=query_id)
            # Database returns flat format with issue_key column
            all_issue_keys: list[str] = [
                str(issue.get("issue_key"))
                for issue in all_issues
                if issue.get("issue_key")
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
                    f"[Database] Optimized fetch: Only {len(issues_needing_changelog)} new issues"
                )
                if progress_callback:
                    progress_callback(
                        f"Smart fetch: {len(issues_needing_changelog)} new issues "
                        f"({len(cached_issue_keys)} already cached)"
                    )
            else:
                logger.info(
                    "[Database] All issues have changelog cached, skipping fetch"
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
                f"[Database] Could not analyze issues from database: {e}, fetching all changelog"
            )
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
                issues_processed = 0
                changelog_entries_batch = []  # Collect entries for batch database insert

                for issue in issues_with_changelog:
                    issue_key = issue.get("key", "")
                    if not issue_key:
                        continue

                    changelog_full = issue.get("changelog", {})
                    histories = changelog_full.get("histories", [])
                    total_histories_before += len(histories)

                    # Filter to ONLY histories that contain tracked field changes
                    # TRACKED FIELDS: status (for Flow metrics), sprint field ID (for Sprint Tracker)
                    # Note: Sprint is a custom field (typically customfield_10020) that varies by instance
                    tracked_fields = ["status"]  # Always track status

                    # Add sprint field if detected (from field mappings)
                    # CRITICAL: JIRA uses field display name in changelog, not custom field ID
                    # E.g., changelog has "Sprint", not "customfield_10005"
                    sprint_field_id = (
                        config.get("field_mappings", {})
                        .get("general", {})
                        .get("sprint_field")
                    )
                    if sprint_field_id:
                        tracked_fields.append(
                            sprint_field_id
                        )  # Track custom field ID (for fallback)
                        tracked_fields.append(
                            "Sprint"
                        )  # Track display name (JIRA default)
                        logger.info(
                            f"[JIRA] Tracking sprint field: {sprint_field_id} and 'Sprint'"
                        )

                    # DEBUG: Log unique field names from first issue to diagnose sprint field mismatch
                    if issues_processed == 0 and histories:
                        unique_fields = set()
                        for hist in histories[:5]:  # Check first 5 histories
                            for item in hist.get("items", []):
                                unique_fields.add(item.get("field"))
                        logger.info(
                            f"[JIRA] Sample changelog field names for {issue_key}: {sorted(unique_fields)}"
                        )

                    filtered_histories = []
                    for history in histories:
                        items = history.get("items", [])

                        # Keep only tracked field change items
                        # JIRA changelog items have BOTH:
                        #   "field": "Sprint" (display name)
                        #   "fieldId": "customfield_10005" (actual field ID)
                        # We must check BOTH to catch all changes
                        tracked_items = [
                            item
                            for item in items
                            if item.get("field") in tracked_fields
                            or item.get("fieldId") in tracked_fields
                        ]

                        if tracked_items:
                            # Build minimal history entry with only what we need
                            filtered_histories.append(
                                {
                                    "created": history.get("created"),
                                    "items": [
                                        {
                                            "field": item.get("field"),
                                            "fromString": item.get("fromString"),
                                            "toString": item.get("toString"),
                                        }
                                        for item in tracked_items
                                    ],
                                }
                            )

                    total_histories_after += len(filtered_histories)

                    # CRITICAL: Include ALL fields needed for DORA, Flow, and Sprint metrics
                    # - project: Filter Development vs DevOps projects
                    # - fixVersions: Match dev issues with operational tasks
                    # - status: Filter completed/deployed issues, track state transitions
                    # - sprint: Track sprint assignment changes (Sprint Tracker feature)
                    # - issuetype: Filter "Operational Task" issues
                    # - created: Used in some calculations
                    # - resolutiondate: Fallback for deployment dates
                    # Prepare changelog entries for database batch insert
                    for history in filtered_histories:
                        change_date = history.get("created", "")
                        items = history.get("items", [])
                        for item in items:
                            # Check both field name and fieldId
                            field_name = item.get("field")
                            field_id = item.get("fieldId")

                            # Use fieldId if it matches tracked fields (for custom fields like sprint)
                            # Otherwise use field name (for standard fields like status)
                            if field_id and field_id in tracked_fields:
                                final_field_name = field_id
                            elif field_name and field_name in tracked_fields:
                                final_field_name = field_name
                            else:
                                continue  # Skip if neither matches

                            changelog_entries_batch.append(
                                {
                                    "issue_key": issue_key,
                                    "change_date": change_date,
                                    "author": "",  # Not stored in optimized cache
                                    "field_name": final_field_name,
                                    "field_type": "jira",
                                    "old_value": item.get("fromString"),
                                    "new_value": item.get("toString"),
                                }
                            )

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

                # Final save: Save to DATABASE only
                if progress_callback:
                    progress_callback(
                        f"Finalizing changelog data for {issues_processed} issues..."
                    )

                # Calculate optimization percentage (used in logging and return value)
                reduction_pct = (
                    (
                        100
                        * (total_histories_before - total_histories_after)
                        / total_histories_before
                    )
                    if total_histories_before > 0
                    else 0
                )

                # Save all collected changelog entries to database in single batch
                try:
                    from datetime import timezone
                    from data.persistence.factory import get_backend

                    backend = get_backend()
                    utc_now = datetime.now(timezone.utc)
                    expires_at = utc_now + timedelta(hours=24)

                    if changelog_entries_batch:
                        # Save to database using batch insert
                        backend.save_changelog_batch(
                            profile_id=profile_id,
                            query_id=query_id,
                            entries=changelog_entries_batch,
                            expires_at=expires_at,
                        )

                        logger.info(
                            f"[Database] Saved {len(changelog_entries_batch)} changelog entries to database for {profile_id}/{query_id}"
                        )
                        logger.info(
                            f"[Database] Optimized changelog: {total_histories_before} → {total_histories_after} histories ({reduction_pct:.1f}% reduction)"
                        )
                    else:
                        logger.info(
                            "[Database] No changelog entries to save (no status changes found)"
                        )

                except Exception as db_error:
                    logger.error(
                        f"[Database] Failed to save changelog to database: {db_error}",
                        exc_info=True,
                    )
                    return False, f"Failed to save changelog to database: {db_error}"

                # Calculate how many were newly fetched vs already cached
                newly_fetched = len(issues_with_changelog)
                total_cached = len(cached_issue_keys) + newly_fetched
                previously_cached = len(cached_issue_keys)

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


#######################################################################
# JIRA CONFIGURATION FUNCTIONS (Feature 003-jira-config-separation)
#######################################################################

# All configuration functions now imported from data.jira module
# (get_jira_config, validate_jira_config, construct_jira_endpoint, test_jira_connection)
