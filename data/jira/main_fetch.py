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
import hashlib
import json
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
    from data.jira.field_utils import extract_jira_field_id
    from data.jira.issue_counter import check_jira_issue_count
    from data.jira.two_phase_fetch import (
        should_use_two_phase_fetch,
        fetch_jira_issues_two_phase,
    )
    from data.jira.delta_fetch import try_delta_fetch, save_delta_fetch_result
    from data.jira.cache_operations import cache_jira_response
    from data.cache_manager import generate_jira_data_cache_key
    from data.profile_manager import get_active_query_workspace

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
        # Generate cache key and config hash regardless of force_refresh
        cache_key = generate_jira_data_cache_key(
            jql_query=jql,
            time_period_days=30,  # Default time period
        )
        from data.jira.config import generate_config_hash

        config_hash = generate_config_hash(config, fields)

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
            query_workspace = get_active_query_workspace()
            cache_file = query_workspace / "jira_cache.json"

            is_valid = False
            cached_data = None

            if cache_file.exists():
                try:
                    with open(cache_file, "r") as f:
                        cache_metadata = json.load(f)

                    # Validate cache structure
                    if "timestamp" in cache_metadata and "issues" in cache_metadata:
                        # Check age
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
                logger.info("[JIRA] No cache file found - will perform full fetch")

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
                delta_success, merged_issues, changed_keys = try_delta_fetch(
                    jql, config, cached_data, api_endpoint, start_time
                )
                if delta_success:
                    save_delta_fetch_result(merged_issues, changed_keys, jql, fields)
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
                        delta_success, merged_issues, changed_keys = try_delta_fetch(
                            jql, config, cached_data, api_endpoint, start_time
                        )
                        if delta_success:
                            # Save merged issues with changed keys metadata
                            save_delta_fetch_result(
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
                        delta_success, merged_issues, changed_keys = try_delta_fetch(
                            jql, config, cached_data, api_endpoint, start_time
                        )
                        if delta_success:
                            # Save merged issues with changed keys metadata
                            save_delta_fetch_result(
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
                    delta_success, merged_issues, changed_keys = try_delta_fetch(
                        jql, config, cached_data, api_endpoint, start_time
                    )
                    if delta_success:
                        # Save merged issues with changed keys metadata
                        save_delta_fetch_result(
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
