"""
fixVersion Matching Module

This module provides functionality to match operational tasks with development issues
based on fixVersion fields. Used for DORA metrics calculations (Lead Time, MTTR).

Matching Strategy:
1. Try ID matching first (most reliable)
2. Fall back to name matching if IDs don't align
3. Handle multiple fixVersions per issue (use earliest deployment)
"""

#######################################################################
# IMPORTS
#######################################################################
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import logging

#######################################################################
# LOGGING
#######################################################################
logger = logging.getLogger("burndown_chart")

#######################################################################
# FIXVERSION EXTRACTION FUNCTIONS
#######################################################################


def get_fixversions(issue: Dict) -> List[Dict]:
    """
    Extract fixVersions from a JIRA issue.

    Args:
        issue: JIRA issue dictionary

    Returns:
        List of fixVersion dictionaries with structure:
        [
            {
                "id": "12345",
                "name": "Release_20251021_ProductionDeploy",
                "releaseDate": "2025-10-21",
                "released": true,
                "archived": false
            },
            ...
        ]
    """
    try:
        return issue.get("fields", {}).get("fixVersions", [])
    except Exception as e:
        logger.error(
            f"Error getting fixVersions for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return []


def extract_fixversion_ids(issue: Dict) -> set:
    """
    Extract fixVersion IDs from a JIRA issue.

    Args:
        issue: JIRA issue dictionary

    Returns:
        Set of fixVersion ID strings
    """
    try:
        fixversions = get_fixversions(issue)
        return {fv.get("id") for fv in fixversions if fv.get("id")}
    except Exception as e:
        logger.error(
            f"Error extracting fixVersion IDs for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return set()


def extract_fixversion_names(issue: Dict) -> set:
    """
    Extract fixVersion names from a JIRA issue (normalized for matching).

    Normalization includes:
    - Convert to lowercase for case-insensitive matching
    - Replace spaces with underscores
    - Replace hyphens with underscores

    Args:
        issue: JIRA issue dictionary

    Returns:
        Set of normalized fixVersion name strings
    """
    try:
        fixversions = get_fixversions(issue)
        normalized_names = set()

        for fv in fixversions:
            name = fv.get("name")
            if name:
                # Normalize: lowercase, spaces/hyphens to underscores
                normalized = name.lower().replace(" ", "_").replace("-", "_")
                normalized_names.add(normalized)

        return normalized_names
    except Exception as e:
        logger.error(
            f"Error extracting fixVersion names for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return set()


def get_earliest_release_date(
    fixversions: List[Dict], today: Optional[date] = None
) -> Optional[date]:
    """
    Get the earliest releaseDate from a list of fixVersions that is NOT in the future.

    Args:
        fixversions: List of fixVersion dictionaries
        today: Optional date for "today" comparison (defaults to date.today())

    Returns:
        Earliest releaseDate as date object, or None if no valid dates found
    """
    if today is None:
        today = date.today()

    try:
        # Filter to versions with releaseDate in the past or today
        valid_dates = []
        for fv in fixversions:
            release_date_str = fv.get("releaseDate")
            if not release_date_str:
                continue

            try:
                # Parse date string (format: "2025-10-21")
                release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()

                # Only include if not in the future
                if release_date <= today:
                    valid_dates.append(release_date)
            except ValueError as e:
                logger.warning(f"Invalid releaseDate format: {release_date_str} - {e}")
                continue

        if not valid_dates:
            return None

        return min(valid_dates)

    except Exception as e:
        logger.error(f"Error getting earliest release date: {e}")
        return None


def get_fallback_release_date(issue: Dict) -> Optional[date]:
    """
    Get fallback release date from issue's resolutiondate.

    Used when operational task has valid fixVersion but no releaseDate.

    Args:
        issue: JIRA issue dictionary

    Returns:
        Resolution date as date object, or None if not available
    """
    try:
        resolution_date_str = issue.get("fields", {}).get("resolutiondate")
        if not resolution_date_str:
            return None

        # Parse ISO 8601 timestamp (e.g., "2025-10-31T18:00:00.000+0200")
        resolution_datetime = datetime.fromisoformat(
            resolution_date_str.replace("Z", "+00:00")
        )
        return resolution_datetime.date()

    except Exception as e:
        logger.error(
            f"Error getting fallback release date for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return None


#######################################################################
# FIXVERSION MATCHING FUNCTIONS
#######################################################################


def find_matching_operational_tasks(
    dev_issue: Dict,
    operational_tasks: List[Dict],
    match_by: str = "auto",
) -> List[Tuple[Dict, str]]:
    """
    Find operational tasks that match a development issue by fixVersion.

    Matching Strategy:
    - Priority 1: Match by fixVersion ID (most reliable)
    - Priority 2: Fallback to fixVersion name matching

    Args:
        dev_issue: Development issue dictionary
        operational_tasks: List of operational task dictionaries
        match_by: Matching strategy - "id", "name", or "auto" (try ID first, fallback to name)

    Returns:
        List of tuples: (operational_task, match_method)
        - operational_task: Matching operational task dictionary
        - match_method: "id" or "name" indicating how match was found
    """
    try:
        dev_fixversion_ids = extract_fixversion_ids(dev_issue)
        dev_fixversion_names = extract_fixversion_names(dev_issue)

        if not dev_fixversion_ids and not dev_fixversion_names:
            logger.debug(
                f"Development issue {dev_issue.get('key', 'UNKNOWN')} has no fixVersions"
            )
            return []

        matching_tasks = []

        for op_task in operational_tasks:
            op_fixversion_ids = extract_fixversion_ids(op_task)
            op_fixversion_names = extract_fixversion_names(op_task)

            # Priority 1: Match by ID (most reliable)
            if match_by in ("id", "auto"):
                if dev_fixversion_ids & op_fixversion_ids:  # Set intersection
                    matching_tasks.append((op_task, "id"))
                    logger.debug(
                        f"fixVersion ID match: {dev_issue.get('key')} <-> {op_task.get('key')} "
                        f"(IDs: {dev_fixversion_ids & op_fixversion_ids})"
                    )
                    continue  # Found ID match, skip name matching

            # Priority 2: Fallback to name matching
            if match_by in ("name", "auto"):
                if dev_fixversion_names & op_fixversion_names:  # Set intersection
                    matching_tasks.append((op_task, "name"))
                    logger.debug(
                        f"fixVersion name match: {dev_issue.get('key')} <-> {op_task.get('key')} "
                        f"(Names: {dev_fixversion_names & op_fixversion_names})"
                    )
                    # Log warning if matched by name in "auto" mode
                    if match_by == "auto":
                        logger.warning(
                            f"fixVersion matched by name for {dev_issue.get('key')} <-> {op_task.get('key')} "
                            f"(consider verifying ID alignment)"
                        )

        return matching_tasks

    except Exception as e:
        logger.error(
            f"Error finding matching operational tasks for issue {dev_issue.get('key', 'UNKNOWN')}: {e}"
        )
        return []


def get_deployment_date_from_operational_task(
    op_task: Dict,
    matching_fixversion_ids: Optional[set] = None,
    matching_fixversion_names: Optional[set] = None,
) -> Optional[date]:
    """
    Get deployment date from operational task's fixVersion.releaseDate.

    If multiple fixVersions match, returns EARLIEST releaseDate that's not in the future.

    Args:
        op_task: Operational task dictionary
        matching_fixversion_ids: Optional set of fixVersion IDs to filter by
        matching_fixversion_names: Optional set of fixVersion names to filter by

    Returns:
        Earliest deployment date, or None if no valid dates found
    """
    try:
        all_fixversions = get_fixversions(op_task)

        # Filter to matching fixVersions if specified
        if matching_fixversion_ids or matching_fixversion_names:
            matching_fixversions = []
            for fv in all_fixversions:
                fv_id = fv.get("id")
                fv_name = fv.get("name")

                # Include if ID matches (highest priority)
                if matching_fixversion_ids and fv_id in matching_fixversion_ids:
                    matching_fixversions.append(fv)
                # Or if name matches (fallback) - MUST normalize name for comparison
                elif matching_fixversion_names and fv_name:
                    # Normalize: lowercase, spaces/hyphens to underscores (same as extract_fixversion_names)
                    normalized_name = (
                        fv_name.lower().replace(" ", "_").replace("-", "_")
                    )
                    if normalized_name in matching_fixversion_names:
                        matching_fixversions.append(fv)
        else:
            matching_fixversions = all_fixversions

        if not matching_fixversions:
            logger.debug(
                f"Operational task {op_task.get('key', 'UNKNOWN')} has no matching fixVersions"
            )
            return None

        # Get earliest releaseDate from matching fixVersions
        earliest_date = get_earliest_release_date(matching_fixversions)

        if earliest_date:
            logger.debug(
                f"Operational task {op_task.get('key', 'UNKNOWN')}: Earliest deployment date = {earliest_date}"
            )
            return earliest_date

        # Fallback: Use resolutiondate if no releaseDate available
        fallback_date = get_fallback_release_date(op_task)
        if fallback_date:
            logger.info(
                f"Operational task {op_task.get('key', 'UNKNOWN')}: No releaseDate, using resolutiondate = {fallback_date}"
            )
            return fallback_date

        logger.warning(
            f"Operational task {op_task.get('key', 'UNKNOWN')}: No valid deployment date found "
            f"(no releaseDate or resolutiondate)"
        )
        return None

    except Exception as e:
        logger.error(
            f"Error getting deployment date from operational task {op_task.get('key', 'UNKNOWN')}: {e}"
        )
        return None


def get_relevant_deployment_date(
    dev_issue: Dict,
    operational_tasks: List[Dict],
    deployment_ready_time: Optional[datetime] = None,
) -> Optional[Tuple[date, Dict, str]]:
    """
    Get the MOST RELEVANT deployment date for Lead Time calculation.

    For Lead Time, we want the deployment that happened AFTER the code was ready,
    and is closest to the ready time (not necessarily the absolute earliest deployment).

    Args:
        dev_issue: Development issue dictionary
        operational_tasks: List of operational task dictionaries
        deployment_ready_time: When the code was ready for deployment (e.g., "In Deployment" status)

    Returns:
        Tuple of (deployment_date, operational_task, match_method) or None if no match
        - deployment_date: Most relevant deployment date (date object)
        - operational_task: Operational task with relevant deployment
        - match_method: "id" or "name" indicating how match was found
    """
    dev_key = dev_issue.get("key", "UNKNOWN")
    logger.info(
        f"[RELEVANT_DEPLOY] {dev_key}: Starting search, ready_time={deployment_ready_time}"
    )

    try:
        # Find all matching operational tasks
        matching_tasks = find_matching_operational_tasks(dev_issue, operational_tasks)
        logger.info(
            f"[RELEVANT_DEPLOY] {dev_key}: Found {len(matching_tasks)} matching operational tasks"
        )

        if not matching_tasks:
            logger.debug(
                f"Development issue {dev_issue.get('key', 'UNKNOWN')}: No matching operational tasks found"
            )
            return None

        # Get deployment dates for all matching tasks
        deployment_dates = []
        for op_task, match_method in matching_tasks:
            # Get matching fixVersion IDs/names for filtering
            dev_fixversion_ids = extract_fixversion_ids(dev_issue)
            dev_fixversion_names = extract_fixversion_names(dev_issue)

            logger.info(
                f"[RELEVANT_DEPLOY] {dev_key}: Getting deployment date from {op_task.get('key')}, match_method={match_method}"
            )

            deployment_date = get_deployment_date_from_operational_task(
                op_task,
                matching_fixversion_ids=dev_fixversion_ids
                if match_method == "id"
                else None,
                matching_fixversion_names=dev_fixversion_names
                if match_method == "name"
                else None,
            )

            logger.info(
                f"[RELEVANT_DEPLOY] {dev_key}: Deployment date from {op_task.get('key')} = {deployment_date}"
            )

            if deployment_date:
                deployment_dates.append((deployment_date, op_task, match_method))

        if not deployment_dates:
            logger.warning(
                f"[RELEVANT_DEPLOY] {dev_key}: [X] Found {len(matching_tasks)} matching operational tasks, but NONE have valid deployment dates!"
            )
            return None

        # If deployment_ready_time provided, filter to deployments AFTER ready time
        if deployment_ready_time:
            ready_date = deployment_ready_time.date()
            logger.info(
                f"[RELEVANT_DEPLOY] {dev_key}: Ready date = {ready_date}, checking {len(deployment_dates)} deployment dates"
            )

            for dep_date, op_task, method in deployment_dates:
                logger.info(
                    f"[RELEVANT_DEPLOY] {dev_key}:   - {op_task.get('key')}: deployment={dep_date}, after_ready={dep_date >= ready_date}"
                )

            after_ready = [d for d in deployment_dates if d[0] >= ready_date]
            logger.info(
                f"[RELEVANT_DEPLOY] {dev_key}: {len(after_ready)} deployments after ready time"
            )

            if after_ready:
                # Return the earliest deployment after ready time (closest to ready)
                relevant = min(after_ready, key=lambda x: x[0])
                logger.warning(
                    f"[RELEVANT_DEPLOY] {dev_key}: [OK] USING deployment = {relevant[0]} from {relevant[1].get('key')} "
                    f"(after ready time {ready_date}, matched by {relevant[2]})"
                )
                return relevant
            else:
                # No deployments after ready time - this is suspicious but return earliest anyway
                logger.warning(
                    f"[RELEVANT_DEPLOY] {dev_key}: [X] All {len(deployment_dates)} deployments are BEFORE ready time {ready_date}. "
                    f"Using earliest anyway."
                )

        # No ready time provided OR all deployments before ready - use earliest
        earliest = min(deployment_dates, key=lambda x: x[0])
        logger.debug(
            f"Development issue {dev_issue.get('key', 'UNKNOWN')}: "
            f"Earliest deployment = {earliest[0]} from {earliest[1].get('key')} (matched by {earliest[2]})"
        )

        return earliest

    except Exception as e:
        logger.error(
            f"Error getting relevant deployment date for issue {dev_issue.get('key', 'UNKNOWN')}: {e}"
        )
        return None


def get_earliest_deployment_date(
    dev_issue: Dict,
    operational_tasks: List[Dict],
) -> Optional[Tuple[date, Dict, str]]:
    """
    Get the EARLIEST deployment date for a development issue from matching operational tasks.

    DEPRECATED: Use get_relevant_deployment_date() for Lead Time calculations instead.
    This function is kept for backward compatibility with MTTR calculations.

    Args:
        dev_issue: Development issue dictionary
        operational_tasks: List of operational task dictionaries

    Returns:
        Tuple of (deployment_date, operational_task, match_method) or None if no match
        - deployment_date: Earliest deployment date (date object)
        - operational_task: Operational task with earliest deployment
        - match_method: "id" or "name" indicating how match was found
    """
    try:
        # Find all matching operational tasks
        matching_tasks = find_matching_operational_tasks(dev_issue, operational_tasks)

        if not matching_tasks:
            logger.debug(
                f"Development issue {dev_issue.get('key', 'UNKNOWN')}: No matching operational tasks found"
            )
            return None

        # Get deployment dates for all matching tasks
        deployment_dates = []
        for op_task, match_method in matching_tasks:
            # Get matching fixVersion IDs/names for filtering
            dev_fixversion_ids = extract_fixversion_ids(dev_issue)
            dev_fixversion_names = extract_fixversion_names(dev_issue)

            deployment_date = get_deployment_date_from_operational_task(
                op_task,
                matching_fixversion_ids=dev_fixversion_ids
                if match_method == "id"
                else None,
                matching_fixversion_names=dev_fixversion_names
                if match_method == "name"
                else None,
            )

            if deployment_date:
                deployment_dates.append((deployment_date, op_task, match_method))

        if not deployment_dates:
            logger.debug(
                f"Development issue {dev_issue.get('key', 'UNKNOWN')}: "
                f"Found {len(matching_tasks)} matching operational tasks, but none have valid deployment dates"
            )
            return None

        # Return earliest deployment
        earliest = min(deployment_dates, key=lambda x: x[0])
        logger.debug(
            f"Development issue {dev_issue.get('key', 'UNKNOWN')}: "
            f"Earliest deployment = {earliest[0]} from {earliest[1].get('key')} (matched by {earliest[2]})"
        )

        return earliest

    except Exception as e:
        logger.error(
            f"Error getting earliest deployment date for issue {dev_issue.get('key', 'UNKNOWN')}: {e}"
        )
        return None


#######################################################################
# OPERATIONAL TASK FILTERING FUNCTIONS
#######################################################################


def filter_operational_tasks_by_fixversion(
    operational_tasks: List[Dict],
    dev_fixversion_ids: set,
    dev_fixversion_names: set,
) -> List[Dict]:
    """
    Filter operational tasks to only those with fixVersions matching development issues.

    This is used to reduce the operational task dataset for performance.

    Args:
        operational_tasks: List of operational task dictionaries
        dev_fixversion_ids: Set of all fixVersion IDs from development issues
        dev_fixversion_names: Set of all fixVersion names from development issues

    Returns:
        Filtered list of operational tasks with matching fixVersions
    """
    try:
        filtered_tasks = []

        for op_task in operational_tasks:
            op_fixversion_ids = extract_fixversion_ids(op_task)
            op_fixversion_names = extract_fixversion_names(op_task)

            # Include if ANY fixVersion matches (ID or name)
            if (dev_fixversion_ids & op_fixversion_ids) or (
                dev_fixversion_names & op_fixversion_names
            ):
                filtered_tasks.append(op_task)

        logger.info(
            f"Filtered operational tasks: {len(filtered_tasks)} of {len(operational_tasks)} "
            f"match development issue fixVersions"
        )

        return filtered_tasks

    except Exception as e:
        logger.error(f"Error filtering operational tasks by fixVersion: {e}")
        return operational_tasks  # Return all on error to avoid losing data


#######################################################################
# SHARED DORA DEPLOYMENT LOOKUP
#######################################################################


def build_fixversion_release_map(
    operational_tasks: List[Dict],
    valid_fix_versions: Optional[set] = None,
    flow_end_statuses: Optional[List[str]] = None,
) -> Dict[str, datetime]:
    """Build a map of fixVersion name → releaseDate from Operational Tasks.

    This provides a shared lookup for all DORA metrics that need to find
    when a fixVersion was deployed to production.

    Args:
        operational_tasks: List of Operational Task issues
        valid_fix_versions: Optional set of fixVersion names to filter by
            (typically collected from development project issues)
        flow_end_statuses: Optional list of completion statuses to filter by
            (e.g., ["Done", "Resolved", "Closed"])

    Returns:
        Dict mapping fixVersion name → releaseDate (datetime)
        Only includes fixVersions with valid releaseDates.

    Example:
        >>> op_tasks = [{"fields": {"fixVersions": [{"name": "v1.0", "releaseDate": "2025-01-15"}]}}]
        >>> build_fixversion_release_map(op_tasks)
        {"v1.0": datetime(2025, 1, 15, 0, 0)}
    """
    release_map: Dict[str, datetime] = {}

    for issue in operational_tasks:
        # Filter by completion status if provided
        if flow_end_statuses:
            status = issue.get("fields", {}).get("status", {}).get("name", "")
            if status not in flow_end_statuses:
                continue

        fix_versions = issue.get("fields", {}).get("fixVersions", [])
        for fv in fix_versions:
            fv_name = fv.get("name")
            release_date_str = fv.get("releaseDate")

            if not fv_name or not release_date_str:
                continue

            # Filter by valid fixVersions if provided
            if valid_fix_versions and fv_name not in valid_fix_versions:
                continue

            try:
                release_date = datetime.fromisoformat(release_date_str)
                # Keep earliest releaseDate if multiple Operational Tasks have same fixVersion
                if fv_name not in release_map or release_date < release_map[fv_name]:
                    release_map[fv_name] = release_date
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid releaseDate for fixVersion {fv_name}: {e}")
                continue

    logger.info(
        f"Built fixVersion release map: {len(release_map)} versions with release dates"
    )
    if release_map:
        sample = list(release_map.items())[:3]
        logger.debug(f"Sample: {sample}")

    return release_map


def get_deployment_date_for_issue(
    issue: Dict,
    fixversion_release_map: Dict[str, datetime],
) -> Optional[datetime]:
    """Get the deployment date for an issue from its fixVersions.

    Looks up the issue's fixVersions in the release map and returns
    the earliest releaseDate among matching versions.

    This is the shared function for all DORA metrics that need to
    determine when an issue was deployed to production.

    Args:
        issue: JIRA issue dictionary (development issue or bug)
        fixversion_release_map: Map of fixVersion name → releaseDate
            (built from Operational Tasks via build_fixversion_release_map)

    Returns:
        Earliest deployment datetime for this issue, or None if no match

    Example:
        >>> issue = {"fields": {"fixVersions": [{"name": "v1.0"}, {"name": "v2.0"}]}}
        >>> release_map = {"v1.0": datetime(2025, 1, 15), "v2.0": datetime(2025, 2, 1)}
        >>> get_deployment_date_for_issue(issue, release_map)
        datetime(2025, 1, 15, 0, 0)  # Returns earliest
    """
    fix_versions = issue.get("fields", {}).get("fixVersions", [])

    deployment_dates = []
    for fv in fix_versions:
        fv_name = fv.get("name")
        if fv_name and fv_name in fixversion_release_map:
            deployment_dates.append(fixversion_release_map[fv_name])

    if not deployment_dates:
        return None

    # Return earliest deployment date
    return min(deployment_dates)


def filter_issues_deployed_in_week(
    issues: List[Dict],
    fixversion_release_map: Dict[str, datetime],
    week_start: datetime,
    week_end: datetime,
) -> List[Dict]:
    """Filter issues to only those deployed in the specified week.

    Uses the fixVersion → releaseDate map to determine deployment dates.
    This is used to get issues relevant to a specific week for DORA metrics.

    Args:
        issues: List of issues (development issues or bugs)
        fixversion_release_map: Map of fixVersion name → releaseDate
        week_start: Start of week (datetime, inclusive)
        week_end: End of week (datetime, exclusive)

    Returns:
        Filtered list of issues deployed in the week
    """
    filtered = []
    for issue in issues:
        deployment_date = get_deployment_date_for_issue(issue, fixversion_release_map)
        if deployment_date and week_start <= deployment_date < week_end:
            filtered.append(issue)

    logger.debug(
        f"Filtered {len(filtered)} of {len(issues)} issues deployed in week "
        f"{week_start.date()} to {week_end.date()}"
    )
    return filtered
