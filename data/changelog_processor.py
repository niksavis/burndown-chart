import logging
from datetime import UTC, datetime

from dateutil import parser

logger = logging.getLogger("burndown_chart")


def get_first_status_transition_timestamp(
    issue: dict, target_status: str, case_sensitive: bool = False
) -> datetime | None:

    try:
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

        target_status_normalized = (
            target_status if case_sensitive else target_status.lower()
        )

        for history in histories:
            created_timestamp = history.get("created")
            if not created_timestamp:
                continue

            items = history.get("items", [])
            for item in items:
                if item.get("field") != "status":
                    continue

                to_status = item.get("toString", "")
                if not to_status:
                    continue

                to_status_normalized = (
                    to_status if case_sensitive else to_status.lower()
                )

                if to_status_normalized == target_status_normalized:
                    timestamp = datetime.fromisoformat(
                        created_timestamp.replace("Z", "+00:00")
                    )
                    logger.debug(
                        f"Issue {issue.get('key', 'UNKNOWN')}: "
                        f"First '{target_status}' at {timestamp}"
                    )
                    return timestamp

        logger.debug(
            f"Issue {issue.get('key', 'UNKNOWN')}: "
            f"Never reached status '{target_status}'"
        )
        return None

    except Exception as e:
        logger.error(
            "Error extracting status transition timestamp "
            f"for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return None


def get_first_status_transition_from_list(
    issue: dict, target_statuses: list[str], case_sensitive: bool = False
) -> tuple[str, datetime] | None:

    try:
        changelog = issue.get("changelog", {})
        if not changelog:
            return None

        histories = changelog.get("histories", [])
        if not histories:
            return None

        target_statuses_normalized = [
            s if case_sensitive else s.lower() for s in target_statuses
        ]

        for history in histories:
            created_timestamp = history.get("created")
            if not created_timestamp:
                continue

            items = history.get("items", [])
            for item in items:
                if item.get("field") != "status":
                    continue

                to_status = item.get("toString", "")
                if not to_status:
                    continue

                to_status_normalized = (
                    to_status if case_sensitive else to_status.lower()
                )

                if to_status_normalized in target_statuses_normalized:
                    timestamp = datetime.fromisoformat(
                        created_timestamp.replace("Z", "+00:00")
                    )
                    logger.debug(
                        f"Issue {issue.get('key', 'UNKNOWN')}: "
                        f"First completion status '{to_status}' at {timestamp}"
                    )
                    return to_status, timestamp

        return None

    except Exception as e:
        logger.error(
            "Error extracting status transition from list "
            f"for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return None


def calculate_time_in_status(
    issue: dict, target_statuses: list[str], case_sensitive: bool = False
) -> float:

    try:
        changelog = issue.get("changelog", {})
        if not changelog:
            return 0.0

        histories = changelog.get("histories", [])
        if not histories:
            return 0.0

        target_statuses_normalized = [
            s if case_sensitive else s.lower() for s in target_statuses
        ]

        total_time_hours = 0.0
        current_status = None
        status_entry_time = None

        for history in histories:
            timestamp_str = history.get("created")
            if not timestamp_str:
                continue

            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

            items = history.get("items", [])
            for item in items:
                if item.get("field") != "status":
                    continue

                from_status = item.get("fromString", "")
                to_status = item.get("toString", "")

                from_status_normalized = (
                    from_status if case_sensitive else from_status.lower()
                )
                to_status_normalized = (
                    to_status if case_sensitive else to_status.lower()
                )

                if (
                    current_status
                    and status_entry_time
                    and from_status_normalized in target_statuses_normalized
                ):
                    time_diff = timestamp - status_entry_time
                    hours = time_diff.total_seconds() / 3600
                    total_time_hours += hours
                    logger.debug(
                        f"Issue {issue.get('key', 'UNKNOWN')}: "
                        f"Spent {hours:.2f}h in '{from_status}'"
                    )

                if to_status_normalized in target_statuses_normalized:
                    current_status = to_status
                    status_entry_time = timestamp
                else:
                    current_status = None
                    status_entry_time = None

        if current_status and status_entry_time:
            time_diff = datetime.now(status_entry_time.tzinfo) - status_entry_time
            hours = time_diff.total_seconds() / 3600
            total_time_hours += hours
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')}: "
                f"Currently in '{current_status}' for {hours:.2f}h"
            )

        return total_time_hours

    except Exception as e:
        logger.error(
            "Error calculating time in status "
            f"for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return 0.0


def calculate_flow_time(
    issue: dict,
    start_statuses: list[str],
    flow_end_statuses: list[str],
    active_statuses: list[str] | None = None,
    case_sensitive: bool = False,
) -> dict:

    try:
        start_result = get_first_status_transition_from_list(
            issue, start_statuses, case_sensitive
        )
        if not start_result:
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')}: "
                f"Never entered start statuses {start_statuses}"
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

        completion_result = get_first_status_transition_from_list(
            issue, flow_end_statuses, case_sensitive
        )
        if not completion_result:
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')}: "
                "Started flow but not yet completed"
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

        total_flow_time = completion_timestamp - start_timestamp
        total_flow_time_hours = total_flow_time.total_seconds() / 3600

        active_time_hours = None
        flow_efficiency_percent = None

        if active_statuses:
            active_time_hours = calculate_time_in_status(
                issue, active_statuses, case_sensitive
            )

            if total_flow_time_hours > 0:
                flow_efficiency_percent = (
                    active_time_hours / total_flow_time_hours
                ) * 100

                if flow_efficiency_percent > 100:
                    logger.warning(
                        f"Issue {issue.get('key', 'UNKNOWN')}: "
                        "Flow Efficiency capped at 100% "
                        f"(calculated {flow_efficiency_percent:.1f}% from "
                        f"{active_time_hours:.2f}h active / "
                        f"{total_flow_time_hours:.2f}h total). "
                        "This indicates workflow backtracking "
                        "or data anomalies."
                    )
                    flow_efficiency_percent = 100.0

        logger.debug(
            f"Issue {issue.get('key', 'UNKNOWN')}: "
            f"Flow Time = {total_flow_time_hours:.2f}h, "
            f"Active Time = {active_time_hours:.2f}h, "
            f"Efficiency = {flow_efficiency_percent:.1f}%"
            if active_time_hours and flow_efficiency_percent
            else (
                f"Issue {issue.get('key', 'UNKNOWN')}: "
                f"Flow Time = {total_flow_time_hours:.2f}h"
            )
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

    try:
        return issue.get("fields", {}).get("status", {}).get("name", "")
    except Exception as e:
        logger.error(
            f"Error getting current status for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return ""


def has_changelog_data(issue: dict) -> bool:

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

    try:
        if "fields" in issue and isinstance(issue.get("fields"), dict):
            created_str = issue["fields"].get("created")
        else:
            created_str = issue.get("created")

        if not created_str:
            return None

        created_date = parser.parse(created_str)

        created_date = created_date.astimezone(UTC).replace(tzinfo=None)

        if created_date > target_time:
            return None

        if "fields" in issue and isinstance(issue.get("fields"), dict):
            current_status = issue["fields"].get("status", {})
            if isinstance(current_status, dict):
                current_status_name = current_status.get("name", "")
            else:
                current_status_name = current_status or ""
        else:
            current_status_name = issue.get("status", "")

        changelog = issue.get("changelog", {})
        if not changelog:
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')}: "
                "No changelog, using current status "
                f"'{current_status_name}'"
            )
            return current_status_name

        histories = changelog.get("histories", [])
        if not histories:
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')}: "
                "No history entries, using current status "
                f"'{current_status_name}'"
            )
            return current_status_name

        last_status_before_target = None
        last_change_time = None

        for history in histories:
            created_timestamp = history.get("created")
            if not created_timestamp:
                continue

            change_time = parser.parse(created_timestamp)
            change_time = change_time.astimezone(UTC).replace(tzinfo=None)

            if change_time >= target_time:
                continue

            items = history.get("items", [])
            for item in items:
                if item.get("field") == "status":
                    to_status = item.get("toString", "")

                    if last_change_time is None or change_time > last_change_time:
                        last_change_time = change_time
                        last_status_before_target = to_status

        if last_status_before_target:
            logger.debug(
                f"Issue {issue.get('key', 'UNKNOWN')}: "
                f"Status at {target_time.date()} was "
                f"'{last_status_before_target}' (from changelog)"
            )
            return last_status_before_target

        logger.debug(
            f"Issue {issue.get('key', 'UNKNOWN')}: "
            f"No status changes before {target_time.date()}, "
            f"using current status '{current_status_name}'"
        )
        return current_status_name

    except Exception as e:
        logger.error(
            "Error determining status at point in time "
            f"for issue {issue.get('key', 'UNKNOWN')}: {e}"
        )
        return None
