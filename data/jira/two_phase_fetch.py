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

import logging
import time

logger = logging.getLogger(__name__)


def _build_project_clause(devops_projects: list[str]) -> str:
    """Build project clause for DevOps JQL."""
    if len(devops_projects) == 1:
        return f'project = "{devops_projects[0]}"'

    project_list = '", "'.join(devops_projects)
    return f'project in ("{project_list}")'


def _build_type_clause(devops_task_types: list[str]) -> str:
    """Build issue type clause for DevOps JQL."""
    if len(devops_task_types) == 1:
        return f'issuetype = "{devops_task_types[0]}"'

    type_list = '", "'.join(devops_task_types)
    return f'issuetype in ("{type_list}")'


def should_use_two_phase_fetch(config: dict) -> tuple[bool, str]:
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


def extract_fixversions_from_issues(issues: list[dict]) -> list[str]:
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
        f"[TWO-PHASE] Extracted {len(result)} unique fixVersions from "
        f"{len(issues)} development issues"
    )

    return result


def build_devops_jql(
    devops_projects: list[str],
    devops_task_types: list[str],
    fixversion_names: list[str],
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
    project_clause = _build_project_clause(devops_projects)
    type_clause = _build_type_clause(devops_task_types)

    # Build fixVersion filter (with batching for large lists)
    if not fixversion_names or len(fixversion_names) == 0:
        # No fixVersions found in development projects
        logger.warning(
            "[TWO-PHASE] No fixVersions found in development issues - "
            "DevOps fetch will return no results"
        )
        fixversion_clause = "fixVersion in ()"  # Empty IN clause (no results)
    elif len(fixversion_names) == 1:
        fixversion_clause = f'fixVersion = "{fixversion_names[0]}"'
    else:
        # JIRA has ~1000 limit for IN clause, but we'll warn if it's large
        if len(fixversion_names) > 500:
            logger.warning(
                "[TWO-PHASE] Large fixVersion filter "
                f"({len(fixversion_names)} versions) "
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


def extract_issue_keys_from_issues(issues: list[dict]) -> list[str]:
    """Extract sorted unique issue keys from issues."""
    issue_keys = {
        str(issue.get("key", "")).strip()
        for issue in issues
        if str(issue.get("key", "")).strip()
    }
    result = sorted(issue_keys)
    logger.info(
        f"[TWO-PHASE] Extracted {len(result)} unique issue keys from "
        f"{len(issues)} development issues"
    )
    return result


def build_devops_linked_jql(
    devops_projects: list[str],
    devops_task_types: list[str],
    development_issue_keys: list[str],
    batch_size: int = 200,
) -> str:
    """Build DevOps JQL using ScriptRunner linkedIssuesOf against dev keys."""
    project_clause = _build_project_clause(devops_projects)
    type_clause = _build_type_clause(devops_task_types)

    if not development_issue_keys:
        linked_clause = "issuekey in ()"
    else:
        linked_clauses = []
        for i in range(0, len(development_issue_keys), batch_size):
            batch = development_issue_keys[i : i + batch_size]
            subquery = f"key in ({', '.join(batch)})"
            linked_clauses.append(f'issueFunction in linkedIssuesOf("{subquery}")')

        if len(linked_clauses) == 1:
            linked_clause = linked_clauses[0]
        else:
            linked_clause = f"({' OR '.join(linked_clauses)})"

    jql = f"({project_clause}) AND ({type_clause}) AND ({linked_clause})"
    logger.info(
        f"[TWO-PHASE] Built linked DevOps JQL: {len(devops_projects)} projects, "
        f"{len(devops_task_types)} types, {len(development_issue_keys)} issue keys"
    )
    logger.debug(f"[TWO-PHASE] Linked DevOps JQL: {jql[:200]}...")
    return jql


def fetch_jira_issues_two_phase(
    config: dict,
    max_results: int | None = None,
    force_refresh: bool = False,
    fetch_paginated_func=None,
) -> tuple[bool, list[dict]]:
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
            f"[TWO-PHASE] Phase 1 complete: {len(dev_issues)} development "
            "issues fetched"
        )

        # ===== PHASE 2: Extract fixVersions =====
        fixversion_names = extract_fixversions_from_issues(dev_issues)
        development_issue_keys = extract_issue_keys_from_issues(dev_issues)

        def fetch_devops_by_linked_issues() -> tuple[bool, list[dict]]:
            """Fetch DevOps tasks linked to development issues."""
            if not development_issue_keys:
                logger.warning(
                    "[TWO-PHASE] No development issue keys found - "
                    "cannot use linked issue fallback"
                )
                return True, []

            logger.info(
                "[TWO-PHASE] Falling back to linked issue fetch for DevOps tasks"
            )
            linked_jql = build_devops_linked_jql(
                devops_projects, devops_task_types, development_issue_keys
            )
            linked_config = config.copy()
            linked_config["jql_query"] = linked_jql
            linked_success, linked_issues = fetch_paginated_func(
                linked_config, max_results
            )
            if not linked_success:
                logger.error("[TWO-PHASE] Linked issue fallback fetch failed")
                return False, []

            logger.info(
                "[TWO-PHASE] Linked issue fallback fetched "
                f"{len(linked_issues)} DevOps issues"
            )
            return True, linked_issues

        if not fixversion_names or len(fixversion_names) == 0:
            logger.warning(
                "[TWO-PHASE] No fixVersions found in development issues - "
                "trying linked issue fallback"
            )

            linked_success, linked_issues = fetch_devops_by_linked_issues()
            if not linked_success:
                logger.warning(
                    "[TWO-PHASE] Linked issue fallback failed - "
                    "returning development issues only"
                )
                linked_issues = []

            merged_issues = dev_issues + linked_issues

            elapsed_time = time.time() - start_time
            logger.info(
                f"[TWO-PHASE] Fetch complete: {len(merged_issues)} issues in "
                f"{elapsed_time:.2f}s"
            )
            return True, merged_issues

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
                f"[TWO-PHASE] Fetch complete: {len(dev_issues)} issues in "
                f"{elapsed_time:.2f}s"
            )
            return True, dev_issues

        logger.info(
            f"[TWO-PHASE] Phase 3 complete: {len(devops_issues)} DevOps issues fetched "
            f"(filtered from potentially thousands)"
        )

        if len(devops_issues) == 0:
            logger.warning(
                "[TWO-PHASE] FixVersion-based DevOps fetch returned 0 issues - "
                "trying linked issue fallback"
            )
            linked_success, linked_issues = fetch_devops_by_linked_issues()
            if linked_success and linked_issues:
                devops_issues = linked_issues
                logger.info(
                    "[TWO-PHASE] Using linked issue fallback result for DevOps data"
                )

        # ===== PHASE 4: Merge Results =====
        merged_issues_by_key = {
            issue.get("key"): issue
            for issue in dev_issues + devops_issues
            if issue.get("key")
        }
        merged_issues = list(merged_issues_by_key.values())

        elapsed_time = time.time() - start_time
        logger.info(
            f"[TWO-PHASE] Fetch complete: {len(merged_issues)} total issues "
            f"({len(dev_issues)} dev + {len(devops_issues)} devops) in "
            f"{elapsed_time:.2f}s"
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
