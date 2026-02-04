"""
JIRA main fetch module.

This module handles the primary JIRA API fetch operation with:
- Incremental fetch optimization (delta fetch)
- Two-phase fetch for DevOps projects
- Rate limiting and retry logic
- Smart caching with validation
- Progress tracking and cancellation support
"""

import logging
import time
from typing import Dict, List, Tuple
from datetime import datetime, timezone
import requests

from data.jira.config import CACHE_EXPIRATION_HOURS

logger = logging.getLogger(__name__)


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
    from data.jira.rate_limiter import get_rate_limiter, retry_with_backoff
    from utils.datetime_utils import parse_iso_datetime
    from data.jira.field_utils import extract_jira_field_id
    from data.jira.issue_counter import check_jira_issue_count
    from data.jira.two_phase_fetch import (
        should_use_two_phase_fetch,
        fetch_jira_issues_two_phase,
    )
    from data.jira.delta_fetch import try_delta_fetch
    from data.jira.cache_operations import cache_jira_response

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

            # Add parent field if configured (either standard 'parent' or Epic Link custom field)
            parent_field = (
                config.get("field_mappings", {}).get("general", {}).get("parent_field")
            )
            if parent_field:
                base_fields += f",{parent_field}"

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
                        clean_field_id = extract_jira_field_id(field_id)
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

        # Initialize backend and cache keys BEFORE conditional checks (fix unbound variable errors)
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")
        last_fetch_key = None
        last_delta_key = None

        if active_profile_id and active_query_id:
            last_fetch_key = f"last_fetch_time:{active_profile_id}:{active_query_id}"
            last_delta_key = (
                f"last_delta_changed_count:{active_profile_id}:{active_query_id}"
            )

        # Skip cache check if force_refresh is True
        if force_refresh:
            logger.info(
                "[JIRA] Force refresh requested - bypassing incremental fetch cache"
            )
            is_valid = False
            cached_data = None
        else:
            logger.info("[JIRA] Checking if data has changed (incremental fetch)")

            is_valid = False
            cached_data = None

            if active_profile_id and active_query_id:
                try:
                    # Load issues from database
                    db_issues = backend.get_issues(active_profile_id, active_query_id)

                    if db_issues and len(db_issues) > 0:
                        # Check cache age from first issue's fetched_at timestamp
                        first_issue = db_issues[0]
                        cache_timestamp = None
                        if last_fetch_key:
                            last_fetch_time = backend.get_app_state(last_fetch_key)
                            cache_timestamp = parse_iso_datetime(last_fetch_time)

                        if not cache_timestamp and "fetched_at" in first_issue:
                            cache_timestamp = parse_iso_datetime(
                                first_issue["fetched_at"]
                            )
                            if cache_timestamp and cache_timestamp.tzinfo is None:
                                cache_timestamp = cache_timestamp.replace(
                                    tzinfo=timezone.utc
                                )

                        if cache_timestamp:
                            now_utc = datetime.now(timezone.utc)
                            age_hours = (
                                now_utc - cache_timestamp
                            ).total_seconds() / 3600

                            if age_hours <= CACHE_EXPIRATION_HOURS:
                                cached_data = db_issues
                                is_valid = True
                                logger.info(
                                    f"[JIRA] Cache valid: {len(cached_data)} issues ({age_hours:.1f}h old)"
                                )
                            else:
                                logger.debug(
                                    f"[JIRA] Cache expired: {age_hours:.1f}h old (max: {CACHE_EXPIRATION_HOURS}h)"
                                )
                        else:
                            logger.warning(
                                "[JIRA] Issues in database missing fetched_at timestamp"
                            )
                    else:
                        logger.info(
                            "[JIRA] No issues found in database - will perform full fetch"
                        )
                except Exception as e:
                    logger.warning(f"[JIRA] Database cache read error: {e}")
            else:
                logger.warning(
                    "[JIRA] No active profile/query - cannot check database cache"
                )

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
                delta_success, merged_issues, changed_keys, delta_issues = (
                    try_delta_fetch(jql, config, cached_data, api_endpoint, start_time)
                )
                if delta_success:
                    # Update database with raw delta issues
                    cache_jira_response(
                        data=delta_issues,
                        jql_query=jql,
                        fields_requested=fields,
                        config=config,
                    )
                    if last_fetch_key and last_delta_key:
                        backend.set_app_state(
                            last_fetch_key,
                            datetime.now(timezone.utc).isoformat(),
                        )
                        backend.set_app_state(
                            last_delta_key,
                            str(len(delta_issues)),
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
                        delta_success, merged_issues, changed_keys, delta_issues = (
                            try_delta_fetch(
                                jql, config, cached_data, api_endpoint, start_time
                            )
                        )
                        if delta_success:
                            # Update database with raw delta issues
                            cache_jira_response(
                                data=delta_issues,
                                jql_query=jql,
                                fields_requested=fields,
                                config=config,
                            )
                            if last_fetch_key and last_delta_key:
                                backend.set_app_state(
                                    last_fetch_key,
                                    datetime.now(timezone.utc).isoformat(),
                                )
                                backend.set_app_state(
                                    last_delta_key,
                                    str(len(delta_issues)),
                                )
                            return True, merged_issues
                        # Delta fetch failed, fall through to full fetch
                    else:
                        # Small count difference, might be few new/deleted issues
                        # Try delta fetch first
                        logger.info(
                            f"[JIRA] Small count change: {cached_count} -> {current_count}, trying delta fetch"
                        )
                        delta_success, merged_issues, changed_keys, delta_issues = (
                            try_delta_fetch(
                                jql, config, cached_data, api_endpoint, start_time
                            )
                        )
                        if delta_success:
                            # Update database with raw delta issues
                            cache_jira_response(
                                data=delta_issues,
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
                    delta_success, merged_issues, changed_keys, delta_issues = (
                        try_delta_fetch(
                            jql, config, cached_data, api_endpoint, start_time
                        )
                    )
                    if delta_success:
                        # Update database with raw delta issues
                        cache_jira_response(
                            data=delta_issues,
                            jql_query=jql,
                            fields_requested=fields,
                            config=config,
                        )
                        if last_fetch_key and last_delta_key:
                            backend.set_app_state(
                                last_fetch_key,
                                datetime.now(timezone.utc).isoformat(),
                            )
                            backend.set_app_state(
                                last_delta_key,
                                str(len(delta_issues)),
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
            # Import paginated function from fetch utilities module
            from data.jira.fetch_utils import fetch_jira_paginated

            success, all_issues = fetch_jira_issues_two_phase(
                config,
                max_results,
                force_refresh,
                fetch_paginated_func=fetch_jira_paginated,
            )
            if not success:
                logger.error("[JIRA] Two-phase fetch failed")
                return False, []

            # Cache the two-phase results to profile-specific location
            from data.persistence.factory import get_backend

            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")
            active_query_id = backend.get_app_state("active_query_id")
            cache_jira_response(
                data=all_issues,
                jql_query=jql,
                fields_requested=fields,
                config=config,
            )
            if active_profile_id and active_query_id:
                backend.set_app_state(
                    f"last_fetch_time:{active_profile_id}:{active_query_id}",
                    datetime.now(timezone.utc).isoformat(),
                )
                backend.set_app_state(
                    f"last_delta_changed_count:{active_profile_id}:{active_query_id}",
                    "-1",
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

        elapsed_time = time.time() - start_time
        logger.info(
            f"[JIRA] Fetch complete: {len(all_issues)} issues in {elapsed_time:.2f}s"
        )

        # Save issues to database
        cache_jira_response(
            data=all_issues,
            jql_query=jql,
            fields_requested=fields,
            config=config,
        )
        try:
            from data.persistence.factory import get_backend

            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")
            active_query_id = backend.get_app_state("active_query_id")
            if active_profile_id and active_query_id:
                backend.set_app_state(
                    f"last_fetch_time:{active_profile_id}:{active_query_id}",
                    datetime.now(timezone.utc).isoformat(),
                )
                backend.set_app_state(
                    f"last_delta_changed_count:{active_profile_id}:{active_query_id}",
                    "-1",
                )
        except Exception as e:
            logger.debug(f"[JIRA] Failed to update last_fetch_time: {e}")

        return True, all_issues

    except requests.exceptions.RequestException as e:
        logger.error(f"[JIRA] Network error: {e}")
        return False, []
    except Exception as e:
        logger.error(f"[JIRA] Unexpected error: {e}")
        return False, []
