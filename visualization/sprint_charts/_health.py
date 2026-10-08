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

    now = datetime.now(UTC)
    status = issue_state.get("status", "Unknown")

    is_completed = status in flow_end_statuses
    if is_completed:
        days_in_completed = 999999.0

        issue_changes = [
            entry for entry in changelog_entries if entry.get("issue_key") == issue_key
        ]

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
                        break
                    except (ValueError, AttributeError) as e:
                        logger.debug(
                            f"Could not parse completion date for {issue_key}: {e}"
                        )

        return (1, 5, days_in_completed)

    is_in_wip_status = status in flow_wip_statuses

    days_since_status_change = None
    issue_changes = [
        entry for entry in changelog_entries if entry.get("issue_key") == issue_key
    ]

    if issue_changes:
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

    if is_in_wip_status and days_since_status_change is not None:
        if days_since_status_change >= 5:
            return (0, 1, 0.0)
        elif days_since_status_change >= 3:
            return (0, 2, 0.0)
        else:
            return (0, 3, 0.0)
    elif is_in_wip_status:
        return (0, 3, 0.0)
    else:
        return (0, 4, 0.0)


def _calculate_completion_percentage(
    issue_key: str,
    changelog_entries: list[dict],
    flow_end_statuses: list[str],
    sprint_start: datetime | None,
    sprint_end: datetime | None,
    now: datetime,
) -> float:

    if not sprint_start or not sprint_end:
        return 0.0

    sprint_duration = (sprint_end - sprint_start).total_seconds()
    if sprint_duration <= 0:
        return 0.0

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
                    break
                except ValueError, AttributeError:
                    pass

    if not completion_time:
        return 0.0

    effective_end = min(now, sprint_end)
    time_in_completed = max(0, (effective_end - completion_time).total_seconds())

    return (time_in_completed / sprint_duration) * 100


def _sort_issues_by_health_priority(
    issue_states: dict[str, dict],
    changelog_entries: list[dict],
    flow_end_statuses: list[str] | None,
    flow_wip_statuses: list[str] | None,
    sprint_start_date: str | None = None,
    sprint_end_date: str | None = None,
) -> list[str]:

    if not issue_states:
        return []

    if flow_end_statuses is None:
        flow_end_statuses = ["Done", "Closed", "Resolved"]
    if flow_wip_statuses is None:
        flow_wip_statuses = ["In Progress"]

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

        issue_priorities.append(
            (completion_bucket, health_priority, days_in_completed, issue_key)
        )

    def sort_key(item):
        completion_bucket, health_priority, days_in_completed, issue_key = item
        try:
            parts = issue_key.split("-")
            if len(parts) > 1:
                numeric_part = int(parts[-1])
                return (
                    completion_bucket,
                    health_priority,
                    days_in_completed,
                    -numeric_part,
                )
        except ValueError, AttributeError:
            pass
        return (completion_bucket, health_priority, days_in_completed, issue_key)

    sorted_items = sorted(issue_priorities, key=sort_key)

    return [item[3] for item in sorted_items]
