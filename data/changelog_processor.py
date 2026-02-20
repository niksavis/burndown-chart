"""
Changelog Processor Module

This module provides functionality to extract status transition timestamps
and calculate time-in-status metrics from JIRA issue changelog data.

Used for:
- Flow Time calculations (active time vs total time)
- Flow Efficiency calculations (active time percentage)
- Lead Time for Changes (deployment readiness to production)
"""

#######################################################################
# IMPORTS
#######################################################################
import logging
from datetime import UTC, datetime

#######################################################################
# LOGGING
#######################################################################
logger = logging.getLogger("burndown_chart")

#######################################################################
# CHANGELOG EXTRACTION FUNCTIONS
#######################################################################


def get_first_status_transition_timestamp(
    issue: dict, target_status: str, case_sensitive: bool = False
) -> datetime | None:
    """
    Extract the FIRST timestamp when an issue entered a specific status.

    This is used for:
    - Flow Time start: First "In Progress" timestamp
    - Lead Time start: First "In Deployment" timestamp
    - Completion: First "Done"/"Resolved"/"Closed" timestamp

    Args:
        issue: JIRA issue dictionary with expanded changelog
        target_status: Status name to search for (e.g., "In Progress", "Done")
        case_sensitive: Whether to match status names case-sensitively (default: False)

    Returns:
        datetime object of first transition to target status, or None if never reached
    """
    try:
        # Check if issue has changelog
        changelog = issue.get("changelog", {})
        if not changelog:
            logger.debug(f"Issue {issue.get('key', 'UNKNOWN')} has no changelog data")
            return None

        histories = changelog.get("histories", [])
        if not histories:
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')} has empty changelog histories"
            )
            return None

        # Normalize target status for comparison
        target_status_normalized = (
            target_status if case_sensitive else target_status.lower()
        )

        # Search changelog for first transition TO target status
        # Changelog is in chronological order (oldest first)
        for history in histories:
            created_timestamp = history.get("created")
            if not created_timestamp:
                continue

            items = history.get("items", [])
            for item in items:
                # Check if this is a status change
                if item.get("field") != "status":
                    continue

                # Check if status changed TO our target status
                to_status = item.get("toString", "")
                if not to_status:
                    continue

                # Compare status names (case-insensitive by default)
                to_status_normalized = (
                    to_status if case_sensitive else to_status.lower()
                )

                if to_status_normalized == target_status_normalized:
                    # Found first transition to target status
                    timestamp = datetime.fromisoformat(
                        created_timestamp.replace("Z", "+00:00")
                    )
                    logger.debug(
                        f"Issue {issue.get('key', 'UNKNOWN')}: First '{target_status}' at {timestamp}"
                    )
                    return timestamp

        # Never reached target status
        logger.debug(
            f"Issue {issue.get('key', 'UNKNOWN')}: Never reached status '{target_status}'"
        )
        return None

    except Exception as e:
        logger.error(
            f"Error extracting status transition timestamp for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return None


def get_first_status_transition_from_list(
    issue: dict, target_statuses: list[str], case_sensitive: bool = False
) -> tuple[str, datetime] | None:
    """
    Extract the FIRST timestamp when an issue entered ANY of the target statuses.

    This is useful for completion detection where multiple statuses indicate completion
    (e.g., "Done", "Resolved", "Closed").

    Args:
        issue: JIRA issue dictionary with expanded changelog
        target_statuses: List of status names to search for
        case_sensitive: Whether to match status names case-sensitively (default: False)

    Returns:
        Tuple of (status_name, timestamp) for first match, or None if never reached any
    """
    try:
        # Check if issue has changelog
        changelog = issue.get("changelog", {})
        if not changelog:
            return None

        histories = changelog.get("histories", [])
        if not histories:
            return None

        # Normalize target statuses for comparison
        target_statuses_normalized = [
            s if case_sensitive else s.lower() for s in target_statuses
        ]

        # Search changelog for first transition TO any target status
        for history in histories:
            created_timestamp = history.get("created")
            if not created_timestamp:
                continue

            items = history.get("items", [])
            for item in items:
                # Check if this is a status change
                if item.get("field") != "status":
                    continue

                # Check if status changed TO one of our target statuses
                to_status = item.get("toString", "")
                if not to_status:
                    continue

                # Compare status names
                to_status_normalized = (
                    to_status if case_sensitive else to_status.lower()
                )

                if to_status_normalized in target_statuses_normalized:
                    # Found first transition to a target status
                    timestamp = datetime.fromisoformat(
                        created_timestamp.replace("Z", "+00:00")
                    )
                    logger.debug(
                        f"Issue {issue.get('key', 'UNKNOWN')}: First completion status '{to_status}' at {timestamp}"
                    )
                    return to_status, timestamp

        # Never reached any target status
        return None

    except Exception as e:
        logger.error(
            f"Error extracting status transition from list for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return None


def calculate_time_in_status(
    issue: dict, target_statuses: list[str], case_sensitive: bool = False
) -> float:
    """
    Calculate total time (in hours) spent in specific statuses.

    This is used for:
    - Flow Efficiency: Time in active statuses vs total time
    - Active time calculations: Sum of time in "In Progress", "In Review", "Testing"

    Args:
        issue: JIRA issue dictionary with expanded changelog
        target_statuses: List of status names to track (e.g., ["In Progress", "In Review", "Testing"])
        case_sensitive: Whether to match status names case-sensitively (default: False)

    Returns:
        Total hours spent in target statuses (0.0 if no time or no changelog)
    """
    try:
        # Check if issue has changelog
        changelog = issue.get("changelog", {})
        if not changelog:
            return 0.0

        histories = changelog.get("histories", [])
        if not histories:
            return 0.0

        # Normalize target statuses for comparison
        target_statuses_normalized = [
            s if case_sensitive else s.lower() for s in target_statuses
        ]

        # Track time in each status segment
        total_time_hours = 0.0
        current_status = None
        status_entry_time = None

        # Process changelog in chronological order
        for history in histories:
            timestamp_str = history.get("created")
            if not timestamp_str:
                continue

            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

            items = history.get("items", [])
            for item in items:
                # Check if this is a status change
                if item.get("field") != "status":
                    continue

                from_status = item.get("fromString", "")
                to_status = item.get("toString", "")

                # Normalize status names
                from_status_normalized = (
                    from_status if case_sensitive else from_status.lower()
                )
                to_status_normalized = (
                    to_status if case_sensitive else to_status.lower()
                )

                # If we were tracking a status, calculate time spent
                if (
                    current_status
                    and status_entry_time
                    and from_status_normalized in target_statuses_normalized
                ):
                    time_diff = timestamp - status_entry_time
                    hours = time_diff.total_seconds() / 3600
                    total_time_hours += hours
                    logger.debug(
                        f"Issue {issue.get('key', 'UNKNOWN')}: Spent {hours:.2f}h in '{from_status}'"
                    )

                # If entering a target status, start tracking
                if to_status_normalized in target_statuses_normalized:
                    current_status = to_status
                    status_entry_time = timestamp
                else:
                    current_status = None
                    status_entry_time = None

        # If issue is CURRENTLY in a target status, calculate time until now
        if current_status and status_entry_time:
            time_diff = datetime.now(status_entry_time.tzinfo) - status_entry_time
            hours = time_diff.total_seconds() / 3600
            total_time_hours += hours
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')}: Currently in '{current_status}' for {hours:.2f}h"
            )

        return total_time_hours

    except Exception as e:
        logger.error(
            f"Error calculating time in status for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return 0.0


def calculate_flow_time(
    issue: dict,
    start_statuses: list[str],
    flow_end_statuses: list[str],
    active_statuses: list[str] | None = None,
    case_sensitive: bool = False,
) -> dict:
    """
    Calculate Flow Time metrics for an issue using changelog data.

    Flow Time has two calculation methods:
    1. Total Flow Time: Time from first "In Progress" to completion (includes waiting)
    2. Active Time Only: Time spent in active statuses (excludes waiting)

    Args:
        issue: JIRA issue dictionary with expanded changelog
        start_statuses: Statuses that mark start of flow (e.g., ["In Progress"])
        flow_end_statuses: Statuses that mark completion (e.g., ["Done", "Resolved", "Closed"])
        active_statuses: Optional list of active statuses for active-time-only calculation
        case_sensitive: Whether to match status names case-sensitively (default: False)

    Returns:
        Dictionary with flow time metrics:
        {
            "total_flow_time_hours": float or None,  # Total time from start to completion
            "active_time_hours": float or None,       # Time in active statuses only
            "flow_efficiency_percent": float or None, # (active_time / total_time) * 100
            "start_timestamp": datetime or None,      # When flow started
            "completion_timestamp": datetime or None, # When flow completed
            "completion_status": str or None          # Which status marked completion
        }
    """
    try:
        # Find flow start timestamp (first entry to any start status)
        start_result = get_first_status_transition_from_list(
            issue, start_statuses, case_sensitive
        )
        if not start_result:
            # Issue never entered flow
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')}: Never entered start statuses {start_statuses}"
            )
            return {
                "total_flow_time_hours": None,
                "active_time_hours": None,
                "flow_efficiency_percent": None,
                "start_timestamp": None,
                "completion_timestamp": None,
                "completion_status": None,
            }

        start_status, start_timestamp = start_result

        # Find completion timestamp (first entry to any completion status)
        completion_result = get_first_status_transition_from_list(
            issue, flow_end_statuses, case_sensitive
        )
        if not completion_result:
            # Issue not yet completed
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')}: Started flow but not yet completed"
            )
            return {
                "total_flow_time_hours": None,
                "active_time_hours": None,
                "flow_efficiency_percent": None,
                "start_timestamp": start_timestamp,
                "completion_timestamp": None,
                "completion_status": None,
            }

        completion_status, completion_timestamp = completion_result

        # Calculate total flow time
        total_flow_time = completion_timestamp - start_timestamp
        total_flow_time_hours = total_flow_time.total_seconds() / 3600

        # Calculate active time if active statuses provided
        active_time_hours = None
        flow_efficiency_percent = None

        if active_statuses:
            active_time_hours = calculate_time_in_status(
                issue, active_statuses, case_sensitive
            )

            # Calculate flow efficiency
            if total_flow_time_hours > 0:
                flow_efficiency_percent = (
                    active_time_hours / total_flow_time_hours
                ) * 100

                # Cap at 100% - efficiency cannot exceed 100% by definition
                # This handles cases where:
                # - Issue moves backward in workflow (Done → In Progress → Done)
                # - Multiple transitions through active statuses cause time overlap
                # - Changelog data anomalies create impossible time calculations
                if flow_efficiency_percent > 100:
                    logger.warning(
                        f"Issue {issue.get('key', 'UNKNOWN')}: Flow Efficiency capped at 100% "
                        f"(calculated {flow_efficiency_percent:.1f}% from {active_time_hours:.2f}h active / "
                        f"{total_flow_time_hours:.2f}h total). This indicates workflow backtracking or data anomalies."
                    )
                    flow_efficiency_percent = 100.0

        logger.debug(
            f"Issue {issue.get('key', 'UNKNOWN')}: Flow Time = {total_flow_time_hours:.2f}h, "
            f"Active Time = {active_time_hours:.2f}h, "
            f"Efficiency = {flow_efficiency_percent:.1f}%"
            if active_time_hours and flow_efficiency_percent
            else f"Issue {issue.get('key', 'UNKNOWN')}: Flow Time = {total_flow_time_hours:.2f}h"
        )

        return {
            "total_flow_time_hours": total_flow_time_hours,
            "active_time_hours": active_time_hours,
            "flow_efficiency_percent": flow_efficiency_percent,
            "start_timestamp": start_timestamp,
            "completion_timestamp": completion_timestamp,
            "completion_status": completion_status,
        }

    except Exception as e:
        logger.error(
            f"Error calculating flow time for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return {
            "total_flow_time_hours": None,
            "active_time_hours": None,
            "flow_efficiency_percent": None,
            "start_timestamp": None,
            "completion_timestamp": None,
            "completion_status": None,
        }


def get_current_status(issue: dict) -> str:
    """
    Get the current status of an issue.

    Args:
        issue: JIRA issue dictionary

    Returns:
        Current status name, or empty string if not found
    """
    try:
        return issue.get("fields", {}).get("status", {}).get("name", "")
    except Exception as e:
        logger.error(
            f"Error getting current status for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return ""


def has_changelog_data(issue: dict) -> bool:
    """
    Check if an issue has changelog data available.

    Args:
        issue: JIRA issue dictionary

    Returns:
        True if issue has changelog with at least one history entry, False otherwise
    """
    try:
        changelog = issue.get("changelog", {})
        if not changelog:
            return False

        histories = changelog.get("histories", [])
        return len(histories) > 0

    except Exception:
        return False


def get_status_at_point_in_time(
    issue: dict, target_time: datetime, case_sensitive: bool = False
) -> str | None:
    """
    Determine what status an issue was in at a specific point in time.

    This reconstructs historical status by:
    1. Finding the LAST status change BEFORE target_time
    2. If no changelog or no changes before target_time, uses current status
    3. Checks if issue existed at target_time (created before target_time)

    Args:
        issue: JIRA issue dictionary with expanded changelog
        target_time: Point in time to check (timezone-naive UTC datetime)
        case_sensitive: Whether to match status names case-sensitively (default: False)

    Returns:
        Status name at that point in time, or None if issue didn't exist yet

    Example:
        >>> # Check status on October 20, 2025
        >>> target = datetime(2025, 10, 20, 23, 59, 59)
        >>> status = get_status_at_point_in_time(issue, target)
        >>> print(f"Issue was in '{status}' on Oct 20")
    """
    try:
        # Check if issue existed at target time
        # Handle both nested JIRA API format and flat database format
        if "fields" in issue and isinstance(issue.get("fields"), dict):
            created_str = issue["fields"].get("created")
        else:
            created_str = issue.get("created")

        if not created_str:
            return None

        # Parse creation date
        from dateutil import parser

        created_date = parser.parse(created_str)
        # Convert to UTC and strip timezone for comparison

        created_date = created_date.astimezone(UTC).replace(tzinfo=None)

        # Issue didn't exist yet
        if created_date > target_time:
            return None

        # Get current status as fallback
        # Handle both nested JIRA API format and flat database format
        if "fields" in issue and isinstance(issue.get("fields"), dict):
            current_status = issue["fields"].get("status", {})
            if isinstance(current_status, dict):
                current_status_name = current_status.get("name", "")
            else:
                current_status_name = current_status or ""
        else:
            # Flat format: status at top level
            current_status_name = issue.get("status", "")

        # Check if issue has changelog
        changelog = issue.get("changelog", {})
        if not changelog:
            # No changelog: assume current status
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')}: No changelog, using current status '{current_status_name}'"
            )
            return current_status_name

        histories = changelog.get("histories", [])
        if not histories:
            # No history entries: assume current status
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')}: No history entries, using current status '{current_status_name}'"
            )
            return current_status_name

        # Find LAST status change BEFORE target_time
        last_status_before_target = None
        last_change_time = None

        for history in histories:
            created_timestamp = history.get("created")
            if not created_timestamp:
                continue

            # Parse changelog timestamp
            change_time = parser.parse(created_timestamp)
            # Convert to UTC and strip timezone
            change_time = change_time.astimezone(UTC).replace(tzinfo=None)

            # Skip changes AFTER target time
            if change_time >= target_time:
                continue

            # Look for status field changes
            items = history.get("items", [])
            for item in items:
                if item.get("field") == "status":
                    to_status = item.get("toString", "")

                    # Track the LAST status change before target_time
                    if last_change_time is None or change_time > last_change_time:
                        last_change_time = change_time
                        last_status_before_target = to_status

        # If we found a status change before target time, use it
        if last_status_before_target:
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')}: Status at {target_time.date()} was '{last_status_before_target}' (from changelog)"
            )
            return last_status_before_target

        # No status changes before target time: use current status
        # (issue was created before target_time but never changed status)
        logger.debug(
            f"Issue {issue.get('key', 'UNKNOWN')}: No status changes before {target_time.date()}, using current status '{current_status_name}'"
        )
        return current_status_name

    except Exception as e:
        logger.error(
            f"Error determining status at point in time for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return None
