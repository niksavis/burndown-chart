"""
JIRA Fetch Utilities Module

This module provides low-level JIRA pagination utilities.
Core fetch operations have been moved to focused modules:
- Main fetch: data.jira.main_fetch
- Sync operations: data.jira.scope_sync
- Changelog: data.jira.changelog_fetcher

This module contains only the paginated fetch helper used by two-phase fetch.
"""

#######################################################################
# IMPORTS
#######################################################################
from typing import Dict, List, Tuple

import requests

from configuration import logger
from data.jira import (
    generate_config_hash,
    extract_jira_field_id,
)

# Main fetch with caching and optimization

# Scope sync and data sync

# Changelog fetching

# Aliasing for backward compatibility within this file
_extract_jira_field_id = extract_jira_field_id
_generate_config_hash = generate_config_hash

#######################################################################
# Removed functions - now in focused modules:
# - fetch_jira_issues → data.jira.main_fetch
# - sync_jira_scope_and_data, sync_jira_data → data.jira.scope_sync
# - fetch_changelog_on_demand → data.jira.changelog_fetcher
#######################################################################


def fetch_jira_paginated(
    config: Dict, max_results: int | None = None
) -> Tuple[bool, List[Dict]]:
    """
    Public version of _fetch_jira_paginated for use by two-phase fetch.

    Internal helper: Execute paginated JIRA fetch without caching or count checks.

    This is a stripped-down version of fetch_jira_issues that only does the core
    API pagination logic. Used by two-phase fetch to avoid cache interference.

    Args:
        config: Configuration dictionary with API endpoint, JQL query, token, etc.
        max_results: Page size for each API call (default: from config or 1000)

    Returns:
        Tuple of (success: bool, issues: List[Dict])
    """
    return _fetch_jira_paginated(config, max_results)


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
    from data.jira.rate_limiter import get_rate_limiter, retry_with_backoff

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
            # CRITICAL: Include parent for epic/feature tracking (Active Work Timeline feature)
            base_fields = "key,summary,project,created,updated,resolutiondate,status,issuetype,assignee,priority,resolution,labels,components,fixVersions,parent"
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


#######################################################################
# MAIN FUNCTIONS NOW IN FOCUSED MODULES
#######################################################################

# All major JIRA operations have been extracted to focused modules:
# - fetch_jira_issues → data.jira.main_fetch (550 lines)
# - sync_jira_scope_and_data, sync_jira_data → data.jira.scope_sync (319 lines)
# - fetch_changelog_on_demand → data.jira.changelog_fetcher (351 lines)

# Import them from data.jira package:
#   from data.jira import fetch_jira_issues, sync_jira_scope_and_data, etc.


#######################################################################
# JIRA CONFIGURATION FUNCTIONS (Feature 003-jira-config-separation)
#######################################################################

# All configuration functions now imported from data.jira module
# (get_jira_config, validate_jira_config, construct_jira_endpoint, test_jira_connection)
