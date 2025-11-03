"""Project filtering utilities for multi-project Jira setups.

This module provides functions to filter issues based on project type (Development vs DevOps)
to ensure metrics are calculated correctly across multiple projects.

Architecture:
- Single JQL query fetches issues from multiple projects (e.g., DEV1, DEV2, OPS)
- Projects are classified as either "Development" or "DevOps"
- Metrics filter issues based on their purpose:
  * Burndown/Velocity: Development projects only (exclude DevOps)
  * DORA Deployments: DevOps projects only (Operational Tasks)
  * DORA Incidents: Development projects only (Bugs)
  * Flow Metrics: Development projects only (Stories, Tasks)
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def get_issue_project_key(issue: Dict[str, Any]) -> str:
    """Extract project key from Jira issue.

    Args:
        issue: Jira issue dictionary

    Returns:
        Project key (e.g., "DEVPROJ", "DEVOPS")
    """
    try:
        # Try to get from fields.project.key first
        project_key = issue.get("fields", {}).get("project", {}).get("key", "")
        if project_key:
            return project_key

        # Fallback: parse from issue key (e.g., "RI-8957" → "RI")
        issue_key = issue.get("key", "")
        if issue_key and "-" in issue_key:
            return issue_key.split("-")[0]

        return ""
    except (AttributeError, KeyError) as e:
        logger.warning(f"Failed to extract project key from issue: {e}")
        return ""


def get_issue_type(issue: Dict[str, Any]) -> str:
    """Extract issue type name from Jira issue.

    Args:
        issue: Jira issue dictionary

    Returns:
        Issue type name (e.g., "Story", "Bug", "Operational Task")
    """
    try:
        return issue.get("fields", {}).get("issuetype", {}).get("name", "")
    except (AttributeError, KeyError) as e:
        logger.warning(f"Failed to extract issue type from issue: {e}")
        return ""


def is_devops_issue(issue: Dict[str, Any], devops_projects: List[str]) -> bool:
    """Check if issue belongs to a DevOps project.

    Args:
        issue: Jira issue dictionary
        devops_projects: List of DevOps project keys (e.g., ["DEVOPS"])

    Returns:
        True if issue is from a DevOps project
    """
    if not devops_projects:
        return False

    project_key = get_issue_project_key(issue)
    return project_key in devops_projects


def is_development_issue(issue: Dict[str, Any], devops_projects: List[str]) -> bool:
    """Check if issue belongs to a Development project (not DevOps).

    Args:
        issue: Jira issue dictionary
        devops_projects: List of DevOps project keys to exclude

    Returns:
        True if issue is from a development project
    """
    return not is_devops_issue(issue, devops_projects)


def filter_development_issues(
    issues: List[Dict[str, Any]], devops_projects: List[str]
) -> List[Dict[str, Any]]:
    """Filter to only development project issues (exclude DevOps).

    Use this for: Burndown charts, velocity metrics, scope metrics.

    Args:
        issues: List of Jira issues
        devops_projects: List of DevOps project keys to exclude

    Returns:
        Filtered list containing only development project issues
    """
    if not devops_projects:
        return issues

    filtered = [i for i in issues if is_development_issue(i, devops_projects)]

    excluded_count = len(issues) - len(filtered)
    if excluded_count > 0:
        logger.info(
            f"Filtered out {excluded_count} DevOps project issues "
            f"(projects: {', '.join(devops_projects)})"
        )

    return filtered


def filter_devops_issues(
    issues: List[Dict[str, Any]], devops_projects: List[str]
) -> List[Dict[str, Any]]:
    """Filter to only DevOps project issues.

    Use this for: Deployment tracking in DORA metrics.

    Args:
        issues: List of Jira issues
        devops_projects: List of DevOps project keys to include

    Returns:
        Filtered list containing only DevOps project issues
    """
    if not devops_projects:
        return []

    filtered = [i for i in issues if is_devops_issue(i, devops_projects)]

    logger.info(
        f"Filtered to {len(filtered)} DevOps project issues "
        f"(projects: {', '.join(devops_projects)})"
    )

    return filtered


def filter_deployment_issues(
    issues: List[Dict[str, Any]], devops_projects: List[str]
) -> List[Dict[str, Any]]:
    """Filter to deployment tracking issues (Operational Tasks in DevOps projects).

    Use this for: DORA Deployment Frequency, Change Failure Rate.

    Args:
        issues: List of Jira issues
        devops_projects: List of DevOps project keys

    Returns:
        Filtered list containing only Operational Task issues from DevOps projects
    """
    deployments = [
        i
        for i in issues
        if is_devops_issue(i, devops_projects)
        and get_issue_type(i) == "Operational Task"
    ]

    logger.info(
        f"Found {len(deployments)} deployment issues (Operational Tasks in DevOps projects)"
    )

    return deployments


def filter_incident_issues(
    issues: List[Dict[str, Any]],
    devops_projects: List[str],
    production_environment_field: Optional[str] = None,
    production_value: str = "PROD",
) -> List[Dict[str, Any]]:
    """Filter to production incident issues (Bugs in Development projects).

    Use this for: DORA Mean Time to Recovery, Change Failure Rate.

    Args:
        issues: List of Jira issues
        devops_projects: List of DevOps project keys to exclude
        production_environment_field: Field ID for environment (e.g., from field_mappings["affected_environment"])
        production_value: Value indicating production (default: "PROD")

    Returns:
        Filtered list containing only production Bug issues from development projects
    """
    # If no production environment field configured, return all bugs in dev projects
    if production_environment_field is None:
        incidents = [
            i
            for i in issues
            if is_development_issue(i, devops_projects) and get_issue_type(i) == "Bug"
        ]
        logger.info(
            f"Found {len(incidents)} incidents (all Bugs in dev projects - no environment filter configured)"
        )
    else:
        incidents = [
            i
            for i in issues
            if is_development_issue(i, devops_projects)
            and get_issue_type(i) == "Bug"
            and _is_production_incident(
                i, production_environment_field, production_value
            )
        ]
        logger.info(
            f"Found {len(incidents)} production incidents "
            f"(Bugs with {production_environment_field}={production_value} in dev projects)"
        )

    return incidents


def _is_production_incident(
    issue: Dict[str, Any], environment_field: str, production_value: str
) -> bool:
    """Check if bug is a production incident.

    Args:
        issue: Jira issue dictionary
        environment_field: Field ID for affected environment
        production_value: Value indicating production environment

    Returns:
        True if bug affected production
    """
    try:
        affected_env = issue.get("fields", {}).get(environment_field)

        # Handle select field (returns dict with 'value' key)
        if isinstance(affected_env, dict):
            affected_env = affected_env.get("value", "")

        # Handle string value
        if isinstance(affected_env, str):
            return affected_env.upper() == production_value.upper()

        return False
    except (AttributeError, KeyError) as e:
        logger.warning(f"Failed to check production environment on issue: {e}")
        return False


def filter_work_items(
    issues: List[Dict[str, Any]],
    devops_projects: List[str],
    work_item_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Filter to work items (Stories, Tasks) in Development projects.

    Use this for: Flow metrics, cycle time, throughput.

    Args:
        issues: List of Jira issues
        devops_projects: List of DevOps project keys to exclude
        work_item_types: Issue types to include (default: ["Story", "Task"])

    Returns:
        Filtered list containing only work items from development projects
    """
    if work_item_types is None:
        work_item_types = ["Story", "Task"]

    work_items = [
        i
        for i in issues
        if is_development_issue(i, devops_projects)
        and get_issue_type(i) in work_item_types
    ]

    logger.info(
        f"Found {len(work_items)} work items "
        f"(types: {', '.join(work_item_types)} in dev projects)"
    )

    return work_items


def get_project_summary(
    issues: List[Dict[str, Any]], devops_projects: List[str]
) -> Dict[str, Any]:
    """Get summary statistics of issues by project type.

    Args:
        issues: List of Jira issues
        devops_projects: List of DevOps project keys

    Returns:
        Dictionary with counts by project and type
    """
    summary = {
        "total_issues": len(issues),
        "development_issues": 0,
        "devops_issues": 0,
        "projects": {},
        "issue_types": {},
    }

    for issue in issues:
        project_key = get_issue_project_key(issue)
        issue_type = get_issue_type(issue)

        # Count by project
        if project_key not in summary["projects"]:
            summary["projects"][project_key] = 0
        summary["projects"][project_key] += 1

        # Count by issue type
        if issue_type not in summary["issue_types"]:
            summary["issue_types"][issue_type] = 0
        summary["issue_types"][issue_type] += 1

        # Count by project type
        if is_devops_issue(issue, devops_projects):
            summary["devops_issues"] += 1
        else:
            summary["development_issues"] += 1

    summary["devops_projects"] = devops_projects

    return summary


def filter_operational_tasks(
    issues: List[Dict[str, Any]],
    operational_projects: List[str],
    development_fixversions: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Filter operational tasks with fixVersion matching and validation.

    This function implements aggressive filtering to reduce the operational task dataset:
    1. Filter by operational projects AND issue type "Operational Task"
    2. Remove operational tasks with NO fixVersion
    3. If development_fixversions provided, filter by matching fixVersion

    Args:
        issues: List of Jira issues
        operational_projects: List of operational project keys (e.g., ["RI"])
        development_fixversions: Optional list of fixVersion IDs/names from development issues.
                                If provided, only operational tasks with matching fixVersions are kept.

    Returns:
        Filtered list of operational tasks with valid fixVersions

    Example:
        >>> dev_fixversions = extract_all_fixversions(development_issues)
        >>> op_tasks = filter_operational_tasks(all_issues, ["RI"], dev_fixversions)
        >>> # Result: Only operational tasks that link to development work
    """
    if not operational_projects:
        logger.warning("No operational projects configured, returning empty list")
        return []

    # Step 1: Filter by operational projects AND issue type
    operational_tasks = [
        issue
        for issue in issues
        if get_issue_project_key(issue) in operational_projects
        and get_issue_type(issue) == "Operational Task"
    ]

    if not operational_tasks:
        logger.info("No Operational Tasks found in operational projects")
        return []

    logger.info(
        f"Found {len(operational_tasks)} Operational Tasks in projects: "
        f"{', '.join(operational_projects)}"
    )

    # Step 2: Remove tasks with no fixVersion
    tasks_with_fixversion = []
    no_fixversion_count = 0

    for task in operational_tasks:
        fixversions = task.get("fields", {}).get("fixVersions", [])

        if fixversions and len(fixversions) > 0:
            tasks_with_fixversion.append(task)
        else:
            no_fixversion_count += 1

    if no_fixversion_count > 0:
        logger.info(
            f"Removed {no_fixversion_count} operational tasks with no fixVersion "
            f"(not linked to development work)"
        )

    # Step 3: Filter by matching fixVersions (if provided)
    if development_fixversions is not None and len(development_fixversions) > 0:
        # Convert to set for faster lookup
        dev_fixversion_set = set(development_fixversions)

        matched_tasks = []
        no_match_count = 0

        for task in tasks_with_fixversion:
            fixversions = task.get("fields", {}).get("fixVersions", [])

            # Check if any fixVersion matches development fixVersions
            has_match = False
            for fv in fixversions:
                # Try matching by ID first
                fv_id = fv.get("id", "")
                if fv_id and fv_id in dev_fixversion_set:
                    has_match = True
                    break

                # Fallback: match by name
                fv_name = fv.get("name", "")
                if fv_name and fv_name in dev_fixversion_set:
                    has_match = True
                    break

            if has_match:
                matched_tasks.append(task)
            else:
                no_match_count += 1

        if no_match_count > 0:
            logger.info(
                f"Removed {no_match_count} operational tasks with fixVersions "
                f"that don't match any development issue"
            )

        logger.info(
            f"Final count: {len(matched_tasks)} operational tasks with matching fixVersions"
        )

        return matched_tasks

    # No development fixVersions filter - return all tasks with fixVersion
    logger.info(
        f"No development fixVersion filter applied, returning {len(tasks_with_fixversion)} "
        f"operational tasks with fixVersions"
    )

    return tasks_with_fixversion


def extract_all_fixversions(issues: List[Dict[str, Any]]) -> List[str]:
    """Extract all unique fixVersion IDs and names from a list of issues.

    This helper function collects all fixVersion identifiers (both IDs and names)
    from development issues to use as a filter for operational tasks.

    Args:
        issues: List of Jira issues

    Returns:
        List of unique fixVersion identifiers (IDs and names combined)

    Example:
        >>> dev_issues = filter_development_issues(all_issues, ["RI"])
        >>> fixversions = extract_all_fixversions(dev_issues)
        >>> # Result: ["12345", "12346", "R_20251021_www.example.com", ...]
    """
    fixversion_identifiers = set()

    for issue in issues:
        fixversions = issue.get("fields", {}).get("fixVersions", [])

        for fv in fixversions:
            # Add ID if available
            fv_id = fv.get("id")
            if fv_id:
                fixversion_identifiers.add(fv_id)

            # Add name if available
            fv_name = fv.get("name")
            if fv_name:
                fixversion_identifiers.add(fv_name)

    result = list(fixversion_identifiers)

    if result:
        logger.info(
            f"Extracted {len(result)} unique fixVersion identifiers from {len(issues)} issues"
        )
    else:
        logger.warning(f"No fixVersions found in {len(issues)} issues")

    return result
