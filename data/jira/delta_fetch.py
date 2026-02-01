"""
Delta fetch optimization module.

This module provides incremental fetch optimization that only fetches issues
updated since the last fetch, reducing API calls and data transfer.
"""

import json
import logging
import hashlib
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
import requests

logger = logging.getLogger(__name__)


def get_affected_weeks_from_changed_issues(changed_keys: List[str]) -> set[str]:
    """
    Determine which ISO weeks are affected by the changed issues.

    Examines created date, resolved date, and changelog entries to find
    all weeks that might have different metrics due to these issue changes.

    Args:
        changed_keys: List of issue keys that changed (e.g., ["A953-123", "RI-456"])

    Returns:
        Set of ISO week labels (e.g., {"2025-W50", "2025-W51", "2026-W01"})
    """
    from data.iso_week_bucketing import get_week_label
    from data.profile_manager import get_active_query_workspace

    affected_weeks = set()

    try:
        # Load full issue data from cache
        query_workspace = get_active_query_workspace()
        cache_file = query_workspace / "jira_cache.json"

        if not cache_file.exists():
            logger.warning("[Delta Calculate] No cache file found")
            return affected_weeks

        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        issues = cache_data.get("issues", [])
        changed_keys_set = set(changed_keys)

        # Find changed issues and extract date-related weeks
        for issue in issues:
            if issue.get("key") not in changed_keys_set:
                continue

            fields = issue.get("fields", {})

            # Check created date
            if fields.get("created"):
                try:
                    created_dt = datetime.fromisoformat(
                        fields["created"].replace("Z", "+00:00")
                    )
                    week_label = get_week_label(created_dt)
                    affected_weeks.add(week_label)
                except Exception as e:
                    logger.debug(
                        f"[Delta Calculate] Could not parse created date for {issue.get('key')}: {e}"
                    )

            # Check resolved date
            if fields.get("resolutiondate"):
                try:
                    resolved_dt = datetime.fromisoformat(
                        fields["resolutiondate"].replace("Z", "+00:00")
                    )
                    week_label = get_week_label(resolved_dt)
                    affected_weeks.add(week_label)
                except Exception as e:
                    logger.debug(
                        f"[Delta Calculate] Could not parse resolved date for {issue.get('key')}: {e}"
                    )

            # TODO: Also check changelog entries for status transitions
            # For now, we'll handle most cases with created/resolved dates

        if affected_weeks:
            logger.info(
                f"[Delta Calculate] {len(changed_keys)} changed issues affect {len(affected_weeks)} weeks: {sorted(affected_weeks)}"
            )
        else:
            logger.info(
                f"[Delta Calculate] {len(changed_keys)} changed issues found but no affected weeks detected"
            )

        return affected_weeks

    except Exception as e:
        logger.warning(f"[Delta Calculate] Failed to determine affected weeks: {e}")
        return affected_weeks


def save_delta_fetch_result(
    merged_issues: List[Dict], changed_keys: List[str], jql: str, fields: str
) -> None:
    """
    Save delta fetch results to cache file with updated timestamp.

    This updates the cache file's last_updated timestamp so the next delta fetch
    will only fetch issues changed since now.

    Args:
        merged_issues: Merged issues (cached + delta)
        changed_keys: List of issue keys that changed
        jql: JQL query used
        fields: Fields requested
    """
    try:
        from data.profile_manager import get_active_query_workspace

        query_workspace = get_active_query_workspace()
        cache_file = query_workspace / "jira_cache.json"

        # Generate JQL hash for validation
        jql_hash = hashlib.sha256(jql.encode()).hexdigest()[:16]

        # Create updated cache with new timestamp
        cache_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),  # Updated timestamp
            "jql_hash": jql_hash,
            "jql_query": jql,
            "issues": merged_issues,
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

        logger.info(
            f"[Delta] Updated cache: {len(merged_issues)} issues, {len(changed_keys)} changed"
        )

    except Exception as e:
        logger.warning(f"[Delta] Failed to save cache: {e}")


def try_delta_fetch(
    jql: str,
    config: Dict,
    cached_data: List[Dict],
    api_endpoint: str,
    start_time: float,
) -> Tuple[bool, List[Dict], List[str]]:
    """
    Try to fetch only issues updated since last cache timestamp.

    Args:
        jql: Original JQL query
        config: JIRA configuration
        cached_data: Cached issues from previous fetch
        api_endpoint: JIRA API endpoint
        start_time: Operation start time for timing

    Returns:
        Tuple of (success: bool, merged_issues: List[Dict], changed_keys: List[str])
    """
    try:
        # Get cache metadata from query workspace
        from data.profile_manager import get_active_query_workspace

        query_workspace = get_active_query_workspace()
        cache_file = query_workspace / "jira_cache.json"

        if not cache_file.exists():
            logger.debug("[Delta] No cache file found")
            return False, [], []

        with open(cache_file, "r") as f:
            cache_metadata = json.load(f)

        last_updated = cache_metadata.get("last_updated")
        cached_jql_hash = cache_metadata.get("jql_hash", "")

        if not last_updated:
            logger.warning(
                "[Delta] No last_updated timestamp in cache - full fetch required"
            )
            return False, [], []

        # Check if JQL query changed
        current_jql_hash = hashlib.sha256(jql.encode()).hexdigest()[:16]
        if current_jql_hash != cached_jql_hash:
            logger.warning(
                f"[Delta] JQL query changed (hash: {cached_jql_hash} -> {current_jql_hash}), full fetch required"
            )
            return False, [], []

        # Build delta JQL with updated filter
        # Add 1 second to last_updated to avoid precision issues (JIRA only supports minute precision)
        # This ensures we don't miss issues updated in the same second, but also don't re-fetch everything
        cache_dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        # Add 1 second to ensure we don't re-fetch issues from the exact same timestamp
        query_dt = cache_dt + timedelta(seconds=1)
        # JIRA expects YYYY-MM-DD HH:mm format (minute precision)
        jira_timestamp = query_dt.strftime("%Y-%m-%d %H:%M")

        delta_jql = f"({jql}) AND updated >= '{jira_timestamp}'"

        logger.info(
            f"[Delta] Fetching issues updated since {jira_timestamp} (cache time: {cache_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC + 1s)"
        )

        # Fetch delta issues using direct API call
        token = config.get("token", "")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Get fields from config
        fields = config.get("fields", "")
        if not fields:
            # Use base fields
            base_fields = "key,summary,project,created,updated,resolutiondate,status,issuetype,assignee,priority,resolution,labels,components,fixVersions"
            fields = base_fields

        params = {
            "jql": delta_jql,
            "fields": fields,
            "maxResults": 1000,
            "startAt": 0,
        }

        response = requests.get(
            api_endpoint,
            headers=headers,
            params=params,
            timeout=30,
        )

        if response.status_code != 200:
            logger.warning(
                f"[Delta] Fetch failed with status {response.status_code}: {response.text[:200]}"
            )
            return False, [], []

        result = response.json()
        delta_issues = result.get("issues", [])

        logger.info(
            f"[Delta] Fetched {len(delta_issues)} changed issues (query: updated >= '{jira_timestamp}')"
        )

        # If delta is too large (>20% of cache), fall back to full fetch
        if len(delta_issues) > len(cached_data) * 0.2:
            logger.info(
                f"[Delta] Too many changes ({len(delta_issues)} > 20% of {len(cached_data)}), full fetch recommended"
            )
            return False, [], []

        # Merge delta with cached data
        # Build dict for O(1) lookup and updates
        merged_dict = {issue["key"]: issue for issue in cached_data}

        # Update or add delta issues
        changed_keys = []
        for delta_issue in delta_issues:
            merged_dict[delta_issue["key"]] = delta_issue
            changed_keys.append(delta_issue["key"])

        merged_issues = list(merged_dict.values())

        elapsed_time = time.time() - start_time
        logger.info(
            f"[Delta] Merge complete: {len(merged_issues)} total issues ({len(delta_issues)} updated) in {elapsed_time:.2f}s"
        )

        return True, merged_issues, changed_keys

    except Exception as e:
        logger.warning(f"[Delta] Delta fetch failed: {e}, falling back to full fetch")
        return False, [], []
