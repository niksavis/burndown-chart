"""
Delta fetch optimization module.

This module provides incremental fetch optimization that only fetches issues
updated since the last fetch, reducing API calls and data transfer.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
import requests
from utils.datetime_utils import parse_iso_datetime

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
    from data.persistence.factory import get_backend

    affected_weeks = set()

    try:
        # Load issue data from database
        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.warning("[Delta Calculate] No active profile/query")
            return affected_weeks

        issues = backend.get_issues(active_profile_id, active_query_id)
        changed_keys_set = set(changed_keys)

        # Find changed issues and extract date-related weeks
        for issue in issues:
            issue_key = issue.get("issue_key") or issue.get("key")
            if issue_key not in changed_keys_set:
                continue

            fields = (
                issue.get("fields", {}) if isinstance(issue.get("fields"), dict) else {}
            )

            # Check created date (nested or flat)
            created_value = fields.get("created") or issue.get("created")
            if created_value:
                try:
                    created_dt = datetime.fromisoformat(
                        created_value.replace("Z", "+00:00")
                    )
                    week_label = get_week_label(created_dt)
                    affected_weeks.add(week_label)
                except Exception as e:
                    logger.debug(
                        f"[Delta Calculate] Could not parse created date for {issue_key}: {e}"
                    )

            # Check resolved date (nested or flat)
            resolved_value = fields.get("resolutiondate") or issue.get("resolved")
            if resolved_value:
                try:
                    resolved_dt = datetime.fromisoformat(
                        resolved_value.replace("Z", "+00:00")
                    )
                    week_label = get_week_label(resolved_dt)
                    affected_weeks.add(week_label)
                except Exception as e:
                    logger.debug(
                        f"[Delta Calculate] Could not parse resolved date for {issue_key}: {e}"
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


def _normalize_issue_for_cache(issue: Dict[str, Any], config: Dict) -> Dict[str, Any]:
    """Normalize JIRA issue to flat database-like structure for calculations."""
    from data.jira.field_utils import extract_story_points_value

    fields = issue.get("fields", {}) if isinstance(issue.get("fields"), dict) else {}
    status = fields.get("status", {}) if isinstance(fields.get("status"), dict) else {}
    status_category = status.get("statusCategory", {})
    if not isinstance(status_category, dict):
        status_category = {}

    story_points_field = config.get("story_points_field", "")
    story_points_field = (
        story_points_field.strip() if isinstance(story_points_field, str) else ""
    )
    story_points_value = fields.get(story_points_field) if story_points_field else None
    points = (
        extract_story_points_value(story_points_value, story_points_field)
        if story_points_field
        else None
    )

    assignee = fields.get("assignee")
    priority = fields.get("priority")
    resolution = fields.get("resolution")
    issuetype = fields.get("issuetype")
    project = fields.get("project")

    return {
        "issue_key": issue.get("key", ""),
        "summary": fields.get("summary", ""),
        "status": status.get("name", ""),
        "status_category": status_category.get("key", ""),
        "assignee": assignee.get("displayName") if isinstance(assignee, dict) else None,
        "issue_type": issuetype.get("name", "") if isinstance(issuetype, dict) else "",
        "priority": priority.get("name") if isinstance(priority, dict) else None,
        "resolution": resolution.get("name") if isinstance(resolution, dict) else None,
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "resolved": fields.get("resolutiondate"),
        "points": points,
        "project_key": project.get("key", "") if isinstance(project, dict) else "",
        "project_name": project.get("name", "") if isinstance(project, dict) else "",
        "fix_versions": fields.get("fixVersions"),
        "labels": fields.get("labels"),
        "components": fields.get("components"),
        "custom_fields": {
            k: v
            for k, v in fields.items()
            if isinstance(k, str) and k.startswith("customfield_")
        },
    }


def try_delta_fetch(
    jql: str,
    config: Dict,
    cached_data: List[Dict],
    api_endpoint: str,
    start_time: float,
) -> Tuple[bool, List[Dict], List[str], List[Dict]]:
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
        # Get cache metadata from database
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.debug("[Delta] No active profile/query")
            return False, [], [], []

        # Get query info from database to check if JQL changed
        query_info = backend.get_query(active_profile_id, active_query_id)
        if not query_info:
            logger.warning("[Delta] Query not found in database")
            return False, [], [], []

        stored_jql = query_info.get("jql", "")
        if stored_jql != jql:
            logger.warning("[Delta] JQL query changed, full fetch required")
            return False, [], [], []

        # Get issues from database to determine last fetch time
        cached_data = backend.get_issues(active_profile_id, active_query_id)
        if not cached_data:
            logger.warning("[Delta] No cached issues - full fetch required")
            return False, [], [], []

        # Get most recent fetched_at timestamp from issues
        last_updated = max(
            issue.get("fetched_at", "")
            for issue in cached_data
            if issue.get("fetched_at")
        )

        last_fetch_key = f"last_fetch_time:{active_profile_id}:{active_query_id}"
        last_fetch_time = backend.get_app_state(last_fetch_key)
        last_fetch_timestamp = parse_iso_datetime(last_fetch_time)

        if last_fetch_timestamp:
            last_updated = last_fetch_timestamp.isoformat()

        if not last_updated:
            logger.warning(
                "[Delta] No fetched_at timestamp in cached issues - full fetch required"
            )
            return False, [], [], []

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

            # Add parent field if configured (either standard 'parent' or Epic Link custom field)
            parent_field = (
                config.get("field_mappings", {}).get("general", {}).get("parent_field")
            )
            if parent_field:
                base_fields += f",{parent_field}"

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
            return False, [], [], []

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
            return False, [], [], []

        normalized_delta_issues = [
            _normalize_issue_for_cache(issue, config) for issue in delta_issues
        ]

        # Merge delta with cached data
        # Build dict for O(1) lookup and updates
        merged_dict = {
            issue.get("issue_key"): issue
            for issue in cached_data
            if issue.get("issue_key")
        }

        # Update or add delta issues
        changed_keys = []
        for delta_issue in normalized_delta_issues:
            issue_key = delta_issue.get("issue_key")
            if not issue_key:
                continue
            merged_dict[issue_key] = delta_issue
            changed_keys.append(issue_key)

        merged_issues = list(merged_dict.values())

        elapsed_time = time.time() - start_time
        logger.info(
            f"[Delta] Merge complete: {len(merged_issues)} total issues ({len(delta_issues)} updated) in {elapsed_time:.2f}s"
        )

        return True, merged_issues, changed_keys, delta_issues

    except Exception as e:
        logger.warning(f"[Delta] Delta fetch failed: {e}, falling back to full fetch")
        return False, [], [], []
