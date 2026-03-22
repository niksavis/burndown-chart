"""Issue health priority calculations and sorting for sprint progress bars."""

import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


def _calculate_issue_health_priority(
    issue_key: str,
    issue_state: dict,
    changelog_entries: list[dict],
    flow_end_statuses: list[str],
    flow_wip_statuses: list[str],
) -> tuple[int, int, float]:
    """Calculate completion bucket and health priority for issue sorting.

    Matches Active Work page logic:
    - Completion bucket 0 (active): Non-completed items
    - Completion bucket 1 (completed): Completed items
    - Health priority 1-5: blocked, aging, active wip, todo, completed

    Args:
        issue_key: Issue identifier
        issue_state: Issue state dict with status, summary, etc.
        changelog_entries: Status changelog for all issues
        flow_end_statuses: List of completion statuses
        flow_wip_statuses: List of work-in-progress statuses

    Returns:
        Tuple of (completion_bucket, health_priority, days_in_completed):
        - completion_bucket: 0=active, 1=completed
        - health_priority: 1=blocked, 2=aging, 3=wip, 4=todo, 5=completed
        - days_in_completed: For completed items,
            days since completion (used for sorting)
    """
    now = datetime.now(UTC)
    status = issue_state.get("status", "Unknown")

    # Check if completed
    is_completed = status in flow_end_statuses
    if is_completed:
        # Calculate when the issue transitioned to completed status
        days_in_completed = (
            999999.0  # Default to very high (treat as completed long ago)
        )

        issue_changes = [
            entry for entry in changelog_entries if entry.get("issue_key") == issue_key
        ]

        # Find the most recent transition TO a completed status
        for change in issue_changes:
            new_status = change.get("new_value", "")
            if new_status in flow_end_statuses:
                change_date_str = change.get("change_date")
                if change_date_str:
                    try:
                        if change_date_str.endswith("Z"):
                            change_date_str = change_date_str[:-1] + "+00:00"
                        change_dt = datetime.fromisoformat(change_date_str)
                        if change_dt.tzinfo is None:
                            change_dt = change_dt.replace(tzinfo=UTC)

                        days_in_completed = (now - change_dt).total_seconds() / 86400
                        break  # Found most recent transition, stop
                    except (ValueError, AttributeError) as e:
                        logger.debug(
                            f"Could not parse completion date for {issue_key}: {e}"
                        )

        return (1, 5, days_in_completed)  # Completion bucket 1, priority 5

    # Check if in WIP status
    is_in_wip_status = status in flow_wip_statuses

    # Get last status change from changelog
    days_since_status_change = None
    issue_changes = [
        entry for entry in changelog_entries if entry.get("issue_key") == issue_key
    ]

    if issue_changes:
        # Changelog is sorted by change_date DESC (most recent first)
        latest_change = issue_changes[0]
        change_date_str = latest_change.get("change_date")

        if change_date_str:
            try:
                if change_date_str.endswith("Z"):
                    change_date_str = change_date_str[:-1] + "+00:00"
                change_dt = datetime.fromisoformat(change_date_str)
                if change_dt.tzinfo is None:
                    change_dt = change_dt.replace(tzinfo=UTC)

                days_since_status_change = (now - change_dt).days
            except (ValueError, AttributeError) as e:
                logger.debug(f"Could not parse status change date for {issue_key}: {e}")

    # If no changelog, use created date as fallback
    if days_since_status_change is None:
        created_str = issue_state.get("created")
        if created_str:
            try:
                if created_str.endswith("Z"):
                    created_str = created_str[:-1] + "+00:00"
                created_dt = datetime.fromisoformat(created_str)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=UTC)
                days_since_status_change = (now - created_dt).days
            except ValueError, AttributeError:
                pass

    # Calculate health priority based on WIP status and velocity
    if is_in_wip_status and days_since_status_change is not None:
        if days_since_status_change >= 5:
            return (0, 1, 0.0)  # Blocked (highest priority)
        elif days_since_status_change >= 3:
            return (0, 2, 0.0)  # Aging (approaching blocked)
        else:
            return (0, 3, 0.0)  # Active WIP (healthy progress)
    elif is_in_wip_status:
        # In WIP but no change date info - treat as active WIP
        return (0, 3, 0.0)
    else:
        # Not WIP, not completed = To Do
        return (0, 4, 0.0)


def _calculate_completion_percentage(
    issue_key: str,
    changelog_entries: list[dict],
    flow_end_statuses: list[str],
    sprint_start: datetime | None,
    sprint_end: datetime | None,
    now: datetime,
) -> float:
    """Calculate what percentage of sprint time the issue spent in completed status.

    Args:
        issue_key: Issue identifier
        changelog_entries: Status changelog for all issues
        flow_end_statuses: List of completion statuses
        sprint_start: Sprint start datetime
        sprint_end: Sprint end datetime
        now: Current datetime

    Returns:
        Percentage of sprint time spent in completed status (0-100)
    """
    if not sprint_start or not sprint_end:
        return 0.0

    sprint_duration = (sprint_end - sprint_start).total_seconds()
    if sprint_duration <= 0:
        return 0.0

    # Find when issue transitioned to completed status
    issue_changes = [
        entry
        for entry in changelog_entries
        if entry.get("issue_key") == issue_key and entry.get("field") == "status"
    ]

    completion_time = None
    for change in issue_changes:
        new_status = change.get("new_value", "")
        if new_status in flow_end_statuses:
            change_date_str = change.get("change_date")
            if change_date_str:
                try:
                    if change_date_str.endswith("Z"):
                        change_date_str = change_date_str[:-1] + "+00:00"
                    change_dt = datetime.fromisoformat(change_date_str)
                    if change_dt.tzinfo is None:
                        change_dt = change_dt.replace(tzinfo=UTC)
                    completion_time = change_dt
                    break  # Use first transition to completed status
                except ValueError, AttributeError:
                    pass

    if not completion_time:
        return 0.0

    # Calculate time in completed status (from completion to now, bounded by sprint)
    effective_end = min(now, sprint_end)
    time_in_completed = max(0, (effective_end - completion_time).total_seconds())

    # Return as percentage of sprint duration
    return (time_in_completed / sprint_duration) * 100


def _sort_issues_by_health_priority(
    issue_states: dict[str, dict],
    changelog_entries: list[dict],
    flow_end_statuses: list[str] | None,
    flow_wip_statuses: list[str] | None,
    sprint_start_date: str | None = None,
    sprint_end_date: str | None = None,
) -> list[str]:
    """Sort issues by completion bucket, health priority,
    completion percentage, and issue key.

    Sorting order:
    1. Completion bucket (0=active first, 1=completed last)
    2. Health priority (1=blocked first, 5=completed last)
    3. For completed items: completion percentage ascending (recently completed first)
    4. Issue key descending (PROJ-200 before PROJ-199)

    Args:
        issue_states: Dict of issue_key -> issue_state
        changelog_entries: Status changelog entries
        flow_end_statuses: List of completion statuses
        flow_wip_statuses: List of WIP statuses
        sprint_start_date: Sprint start date ISO string
        sprint_end_date: Sprint end date ISO string

    Returns:
        Sorted list of issue keys
    """
    if not issue_states:
        return []

    # Ensure flow statuses are lists
    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed", "Resolved"]
    if flow_wip_statuses is None:
        flow_wip_statuses = ["In Progress"]

    # Parse sprint dates
    sprint_start = None
    sprint_end = None

    if sprint_start_date:
        try:
            sprint_start = datetime.fromisoformat(sprint_start_date)
            if sprint_start.tzinfo is None:
                sprint_start = sprint_start.replace(tzinfo=UTC)
        except ValueError, AttributeError:
            pass

    if sprint_end_date:
        try:
            sprint_end = datetime.fromisoformat(sprint_end_date)
            if sprint_end.tzinfo is None:
                sprint_end = sprint_end.replace(tzinfo=UTC)
        except ValueError, AttributeError:
            pass

    # Calculate priority and completion percentage for each issue
    issue_priorities = []
    for issue_key, issue_state in issue_states.items():
        completion_bucket, health_priority, days_in_completed = (
            _calculate_issue_health_priority(
                issue_key,
                issue_state,
                changelog_entries,
                flow_end_statuses,
                flow_wip_statuses,
            )
        )

        # For completed items, use days_in_completed for sorting
        # (lower value = completed more recently = should appear first)
        issue_priorities.append(
            (completion_bucket, health_priority, days_in_completed, issue_key)
        )

    # Sort by completion bucket, health priority,
    # days_in_completed (for completed), then issue key
    def sort_key(item):
        completion_bucket, health_priority, days_in_completed, issue_key = item
        # Try to extract numeric part from issue key (e.g., "PROJ-123" -> 123)
        try:
            # Split by dash and get last part as number
            parts = issue_key.split("-")
            if len(parts) > 1:
                numeric_part = int(parts[-1])
                return (
                    completion_bucket,
                    health_priority,
                    # Ascending: fewer days (recently completed) first
                    days_in_completed,
                    -numeric_part,  # Negative for descending
                )
        except ValueError, AttributeError:
            pass
        # Fallback to string comparison (reverse for descending)
        return (completion_bucket, health_priority, days_in_completed, issue_key)

    sorted_items = sorted(issue_priorities, key=sort_key)

    # Return just the issue keys
    return [item[3] for item in sorted_items]
