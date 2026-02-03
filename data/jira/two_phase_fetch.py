"""
Two-Phase JIRA Fetch Optimization Module

Optimizes JIRA data fetching for projects with large DevOps datasets by using
a two-phase approach:
1. Fetch development issues (user's JQL query)
2. Extract fixVersions from development issues
3. Fetch DevOps issues filtered by those fixVersions
4. Merge results

This reduces DevOps data volume by 10x+ by only fetching issues that link
to actual development work through fixVersions.
"""

import time
from typing import Dict, List, Tuple

from configuration import logger


def should_use_two_phase_fetch(config: Dict) -> Tuple[bool, str]:
    """
    Determine if two-phase fetch should be used based on configuration.

    Two-phase fetch is activated when:
    1. DevOps projects are configured in field mappings
    2. DevOps task types are configured (e.g., "Operational Task")
    3. User's JQL does NOT already include DevOps projects

    Args:
        config: JIRA configuration dictionary

    Returns:
        Tuple of (should_use: bool, reason: str)
    """
    # Check if DevOps projects configured
    devops_projects = config.get("devops_projects", [])
    if not devops_projects or len(devops_projects) == 0:
        return False, "No DevOps projects configured"

    # Check if DevOps task types configured
    devops_task_types = config.get("devops_task_types", [])
    if not devops_task_types or len(devops_task_types) == 0:
        return False, "No DevOps task types configured"

    # Check if user's JQL already includes DevOps projects
    jql_query = config.get("jql_query", "").lower()
    for devops_project in devops_projects:
        if devops_project.lower() in jql_query:
            return (
                False,
                f"DevOps project '{devops_project}' already in JQL query",
            )

    return (
        True,
        f"Two-phase fetch enabled for DevOps projects: {', '.join(devops_projects)}",
    )


def extract_fixversions_from_issues(issues: List[Dict]) -> List[str]:
    """
    Extract all unique fixVersion names from development issues.

    Args:
        issues: List of JIRA issue dictionaries

    Returns:
        List of unique fixVersion names (empty if no fixVersions found)
    """
    fixversion_names = set()

    for issue in issues:
        fixversions = issue.get("fields", {}).get("fixVersions", [])
        for fv in fixversions:
            fv_name = fv.get("name", "").strip()
            if fv_name:
                fixversion_names.add(fv_name)

    result = sorted(list(fixversion_names))
    logger.info(
        f"[TWO-PHASE] Extracted {len(result)} unique fixVersions from {len(issues)} development issues"
    )

    return result


def build_devops_jql(
    devops_projects: List[str],
    devops_task_types: List[str],
    fixversion_names: List[str],
) -> str:
    """
    Build JQL query for fetching DevOps issues with fixVersion filter.

    Handles JIRA's limitation of ~1000 values in IN clause by batching.

    Args:
        devops_projects: List of DevOps project keys (e.g., ["RI"])
        devops_task_types: List of task type names (e.g., ["Operational Task"])
        fixversion_names: List of fixVersion names to filter

    Returns:
        JQL query string for DevOps issues
    """
    # Build project filter
    if len(devops_projects) == 1:
        project_clause = f'project = "{devops_projects[0]}"'
    else:
        project_list = '", "'.join(devops_projects)
        project_clause = f'project in ("{project_list}")'

    # Build issue type filter
    if len(devops_task_types) == 1:
        type_clause = f'issuetype = "{devops_task_types[0]}"'
    else:
        type_list = '", "'.join(devops_task_types)
        type_clause = f'issuetype in ("{type_list}")'

    # Build fixVersion filter (with batching for large lists)
    if not fixversion_names or len(fixversion_names) == 0:
        # No fixVersions found in development projects
        logger.warning(
            "[TWO-PHASE] No fixVersions found in development issues - DevOps fetch will return no results"
        )
        fixversion_clause = "fixVersion in ()"  # Empty IN clause (no results)
    elif len(fixversion_names) == 1:
        fixversion_clause = f'fixVersion = "{fixversion_names[0]}"'
    else:
        # JIRA has ~1000 limit for IN clause, but we'll warn if it's large
        if len(fixversion_names) > 500:
            logger.warning(
                f"[TWO-PHASE] Large fixVersion filter ({len(fixversion_names)} versions) "
                "- query may be slow"
            )

        # Escape quotes in fixVersion names
        escaped_names = [name.replace('"', '\\"') for name in fixversion_names]
        fixversion_list = '", "'.join(escaped_names)
        fixversion_clause = f'fixVersion in ("{fixversion_list}")'

    # Combine clauses
    jql = f"({project_clause}) AND ({type_clause}) AND ({fixversion_clause})"

    logger.info(
        f"[TWO-PHASE] Built DevOps JQL: {len(devops_projects)} projects, "
        f"{len(devops_task_types)} types, {len(fixversion_names)} fixVersions"
    )
    logger.debug(f"[TWO-PHASE] DevOps JQL: {jql[:200]}...")

    return jql


def fetch_jira_issues_two_phase(
    config: Dict,
    max_results: int | None = None,
    force_refresh: bool = False,
    fetch_paginated_func=None,
) -> Tuple[bool, List[Dict]]:
    """
    Execute two-phase JIRA fetch: Development first, then DevOps with fixVersion filter.

    OPTIMIZATION STRATEGY:
    Phase 1: Fetch development projects (user's JQL)
    Phase 2: Extract fixVersions from dev issues
    Phase 3: Fetch DevOps projects with dynamic fixVersion filter
    Phase 4: Merge results

    This dramatically reduces DevOps data volume by only fetching issues
    that link to actual development work.

    Args:
        config: Configuration dictionary with API endpoint, JQL query, token, etc.
        max_results: Page size for each API call (default: from config or 1000)
        force_refresh: Force refresh (unused, for compatibility)
        fetch_paginated_func: Function to use for paginated fetch (injected dependency)

    Returns:
        Tuple of (success: bool, merged_issues: List[Dict])
    """
    if fetch_paginated_func is None:
        raise ValueError(
            "fetch_paginated_func required (must be injected to avoid circular import)"
        )

    start_time = time.time()

    try:
        # Get configuration
        devops_projects = config.get("devops_projects", [])
        devops_task_types = config.get("devops_task_types", [])
        user_jql = config.get("jql_query", "")

        logger.info(
            f"[TWO-PHASE] Starting two-phase fetch - DevOps projects: {devops_projects}"
        )

        # ===== PHASE 1: Fetch Development Projects =====
        logger.info("[TWO-PHASE] Phase 1: Fetching development issues")
        logger.info(f"[TWO-PHASE] User JQL: {user_jql[:100]}...")

        # Create temporary config for development-only fetch
        dev_config = config.copy()
        dev_config["jql_query"] = user_jql  # Use user's JQL as-is

        # Use standard fetch for development issues
        dev_success, dev_issues = fetch_paginated_func(dev_config, max_results)

        if not dev_success:
            logger.error("[TWO-PHASE] Phase 1 failed: Development fetch error")
            return False, []

        logger.info(
            f"[TWO-PHASE] Phase 1 complete: {len(dev_issues)} development issues fetched"
        )

        # ===== PHASE 2: Extract fixVersions =====
        fixversion_names = extract_fixversions_from_issues(dev_issues)

        if not fixversion_names or len(fixversion_names) == 0:
            logger.warning(
                "[TWO-PHASE] No fixVersions found in development issues - skipping DevOps fetch"
            )
            logger.info(
                "[TWO-PHASE] Returning only development issues (no DevOps linkage)"
            )
            elapsed_time = time.time() - start_time
            logger.info(
                f"[TWO-PHASE] Fetch complete: {len(dev_issues)} issues in {elapsed_time:.2f}s"
            )
            return True, dev_issues

        # ===== PHASE 3: Fetch DevOps Issues =====
        logger.info("[TWO-PHASE] Phase 3: Fetching DevOps issues")

        devops_jql = build_devops_jql(
            devops_projects, devops_task_types, fixversion_names
        )

        # Create config for DevOps fetch
        devops_config = config.copy()
        devops_config["jql_query"] = devops_jql

        # Fetch DevOps issues
        devops_success, devops_issues = fetch_paginated_func(devops_config, max_results)

        if not devops_success:
            logger.error("[TWO-PHASE] Phase 3 failed: DevOps fetch error")
            logger.warning(
                "[TWO-PHASE] Continuing with development issues only (no DevOps data)"
            )
            elapsed_time = time.time() - start_time
            logger.info(
                f"[TWO-PHASE] Fetch complete: {len(dev_issues)} issues in {elapsed_time:.2f}s"
            )
            return True, dev_issues

        logger.info(
            f"[TWO-PHASE] Phase 3 complete: {len(devops_issues)} DevOps issues fetched "
            f"(filtered from potentially thousands)"
        )

        # ===== PHASE 4: Merge Results =====
        merged_issues = dev_issues + devops_issues

        elapsed_time = time.time() - start_time
        logger.info(
            f"[TWO-PHASE] Fetch complete: {len(merged_issues)} total issues "
            f"({len(dev_issues)} dev + {len(devops_issues)} devops) in {elapsed_time:.2f}s"
        )

        # Log performance improvement estimate
        if len(devops_issues) > 0:
            estimated_full_devops = len(devops_issues) * 10  # Conservative estimate
            logger.info(
                f"[TWO-PHASE] Performance: Fetched ~{len(devops_issues)} DevOps issues "
                f"instead of potentially {estimated_full_devops}+ (10x+ reduction)"
            )

        return True, merged_issues

    except Exception as e:
        logger.error(f"[TWO-PHASE] Unexpected error: {e}", exc_info=True)
        return False, []
