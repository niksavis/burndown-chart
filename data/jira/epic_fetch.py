"""
JIRA Parent Issue Fetch Module.

This module fetches parent issues from JIRA for display purposes ONLY.
Parents are stored in the database but EXCLUDED from all calculations.

Architecture:
- User's JQL fetches child issues: issuesInEpics(...) AND issuetype in (Story, Task, Bug)
- Children have parent field pointing to parent keys (e.g., "A942-3406")
- This module fetches those parents: key in (parent1, parent2, ...)
- Parents stored in database - filtered from metrics using parent_filter.py
- Works with any parent type: Epic, Feature, Initiative, Portfolio Epic, etc.
"""

import logging
from typing import Dict, List, Set
import requests

logger = logging.getLogger(__name__)


def extract_epic_keys_from_issues(issues: List[Dict], parent_field: str) -> Set[str]:
    """
    Extract unique parent keys from issues' parent field.
    
    Args:
        issues: List of JIRA issues (Story/Task/Bug)
        parent_field: Parent field name (e.g., "parent" or "customfield_10008")
    
    Returns:
        Set of unique parent keys (e.g., {"A942-3406", "A942-3408"})
    """
    epic_keys = set()
    
    for issue in issues:
        fields = issue.get("fields", {})
        parent_data = fields.get(parent_field)
        
        if not parent_data:
            continue
        
        # Parent can be:
        # 1. String: "A942-3406" (direct key)
        # 2. Dict: {"key": "A942-3406", "fields": {...}} (object reference)
        if isinstance(parent_data, str):
            epic_key = parent_data.strip()
            if epic_key:
                epic_keys.add(epic_key)
        elif isinstance(parent_data, dict):
            epic_key = parent_data.get("key", "").strip()
            if epic_key:
                epic_keys.add(epic_key)
    
    logger.info(f"[PARENT] Found {len(epic_keys)} unique parent keys referenced by issues")
    return epic_keys


def fetch_epics_from_jira(
    epic_keys: Set[str],
    config: Dict,
) -> List[Dict]:
    """
    Fetch parent issues from JIRA for display purposes.
    
    IMPORTANT: Parents are stored in database but NEVER counted in calculations.
    All metrics/statistics code must filter out parent issues dynamically.
    
    Args:
        epic_keys: Set of parent keys to fetch (e.g., {"A942-3406"})
        config: JIRA configuration with api_endpoint, auth_token, etc.
    
    Returns:
        List of parent issue dicts (same format as regular issues)
    """
    if not epic_keys:
        logger.debug("[PARENT] No parent keys to fetch")
        return []
    
    # Build JQL: key in (A942-3406, A942-3408, ...)
    # Don't hardcode "issuetype = Epic" - parent type varies across JIRA systems
    # (could be Epic, Feature, Initiative, Portfolio Epic, etc.)
    keys_csv = ", ".join(sorted(epic_keys))
    jql = f"key in ({keys_csv})"
    
    logger.info(f"[PARENT] Fetching {len(epic_keys)} parent issues from JIRA")
    logger.debug(f"[PARENT] JQL: {jql[:100]}...")
    
    api_endpoint = config.get("api_endpoint", "")
    auth_token = config.get("auth_token", "")
    
    if not api_endpoint or not auth_token:
        logger.error("[PARENT] Missing API endpoint or auth token")
        return []
    
    # Use same fields as main fetch for consistency
    base_fields = "key,summary,project,created,updated,resolutiondate,status,issuetype,assignee,priority,resolution,labels,components,fixVersions"
    
    # Add parent field if configured (epics can also have parents/portfolios)
    parent_field = config.get("field_mappings", {}).get("general", {}).get("parent_field")
    if parent_field:
        base_fields += f",{parent_field}"
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }
    
    epics = []
    start_at = 0
    max_results = 100  # JIRA pagination
    
    try:
        while True:
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": base_fields,
            }
            
            response = requests.get(
                f"{api_endpoint}/search",
                headers=headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            
            data = response.json()
            batch = data.get("issues", [])
            epics.extend(batch)
            
            total = data.get("total", 0)
            logger.debug(f"[PARENT] Fetched {len(epics)}/{total} parent issues")
            
            # Check if we have all results
            if len(epics) >= total:
                break
            
            start_at += max_results
    
    except requests.exceptions.RequestException as e:
        logger.error(f"[PARENT] Failed to fetch parent issues: {e}")
        return []
    
    logger.info(f"[PARENT] Successfully fetched {len(epics)} parent issues")
    return epics


def fetch_epics_for_display(
    issues: List[Dict],
    config: Dict,
) -> List[Dict]:
    """
    Main entry point: Extract parent keys from issues and fetch parents from JIRA.
    
    Args:
        issues: Regular issues (Story/Task/Bug) that may reference parents
        config: JIRA configuration
    
    Returns:
        List of parent issues (to be stored in database, filtered from calculations)
    """
    # Get parent field from config
    parent_field = config.get("field_mappings", {}).get("general", {}).get("parent_field")
    
    if not parent_field:
        logger.debug("[PARENT] No parent field configured - skipping parent fetch")
        return []
    
    # Extract parent keys from issues
    epic_keys = extract_epic_keys_from_issues(issues, parent_field)
    
    if not epic_keys:
        logger.debug("[PARENT] No parent keys referenced in issues")
        return []
    
    # Fetch parents from JIRA
    epics = fetch_epics_from_jira(epic_keys, config)
    
    return epics
