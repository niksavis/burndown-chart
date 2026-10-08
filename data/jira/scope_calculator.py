import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def calculate_jira_project_scope(
    issues_data: list[dict[str, Any]],
    points_field: str = "votes",
    status_config: dict[str, Any] | None = None,
) -> dict[str, Any]:

    completed_items = completed_points = 0
    remaining_items = remaining_points = 0
    estimated_items = estimated_points = 0
    status_breakdown = {}

    points_field_available = bool(points_field and points_field.strip())
    field_stats = {
        "total_issues": len(issues_data),
        "validation_method": "user_configured"
        if points_field_available
        else "disabled",
    }

    logger.info(f"[SCOPE] Starting calculation for {len(issues_data)} issues")
    logger.info(
        "[SCOPE] Points tracking: "
        f"{'enabled' if points_field_available else 'disabled'} "
        f"(field: {points_field if points_field_available else 'not configured'})"
    )

    for issue in issues_data:
        try:
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                status_name = issue["fields"]["status"]["name"]
                status_category = issue["fields"]["status"]["statusCategory"]["key"]
                points = _extract_story_points(issue["fields"], points_field)
                has_real_points = _issue_has_real_points(issue["fields"], points_field)
            else:
                status_name = issue.get("status", "")
                status_category = issue.get("status_category", "")
                points = _extract_story_points(issue, points_field)
                has_real_points = _issue_has_real_points(issue, points_field)

            classification = _classify_issue_status(
                status_name, status_category, status_config
            )

            if classification == "COMPLETED":
                completed_items += 1
                completed_points += points
            else:
                remaining_items += 1
                remaining_points += points

                if has_real_points:
                    estimated_items += 1
                    estimated_points += points

            if status_name not in status_breakdown:
                status_breakdown[status_name] = {
                    "items": 0,
                    "points": 0,
                    "category": status_category,
                    "classification": classification,
                }
            status_breakdown[status_name]["items"] += 1
            status_breakdown[status_name]["points"] += points

        except Exception as e:
            logger.warning(f"Error processing issue {issue.get('key', 'unknown')}: {e}")
            continue

    total_items = completed_items + remaining_items
    total_points = completed_points + remaining_points

    logger.info(
        f"[SCOPE] Calculation complete - Total: {total_items}, "
        f"Completed: {completed_items}, Remaining: {remaining_items}"
    )
    logger.info(
        f"[SCOPE] Points - Total: {total_points}, Completed: {completed_points}, "
        f"Remaining: {remaining_points}"
    )

    if points_field_available:
        remaining_total_points = _calculate_remaining_total_points(
            estimated_items,
            estimated_points,
            remaining_items,
            completed_items,
            completed_points,
        )
    else:
        remaining_total_points = 0

    result = {
        "total_items": total_items,
        "total_points": total_points,
        "completed_items": completed_items,
        "completed_points": completed_points,
        "remaining_items": remaining_items,
        "remaining_points": remaining_points,
        "estimated_items": estimated_items,
        "estimated_points": estimated_points,
        "remaining_total_points": remaining_total_points,
        "points_field_available": points_field_available,
        "status_breakdown": status_breakdown,
        "calculation_metadata": {
            "method": status_config.get("method", "status_category")
            if status_config
            else "status_category",
            "calculated_at": datetime.now().isoformat(),
            "total_issues_processed": len(issues_data),
            "points_field": points_field,
            "points_field_valid": points_field_available,
            "field_stats": field_stats,
        },
    }

    logger.info(
        f"[Stats] JIRA Scope Calculated: {completed_items}/{total_items} "
        f"items completed, "
        f"{completed_points}/{total_points} points completed"
    )

    return result


def _classify_issue_status(
    status_name: str, status_category: str, status_config: dict[str, Any] | None
) -> str:

    if status_config and status_config.get("method") == "status_names":
        completed_statuses = status_config.get("completed_statuses", [])
        in_progress_statuses = status_config.get("in_progress_statuses", [])

        if status_name in completed_statuses:
            return "COMPLETED"
        elif status_name in in_progress_statuses:
            return "IN_PROGRESS"
        else:
            return "TODO"

    if status_config and "status_name_overrides" in status_config:
        override = status_config["status_name_overrides"].get(status_name)
        if override:
            return override

    if status_category == "done":
        return "COMPLETED"
    elif status_category == "indeterminate":
        return "IN_PROGRESS"
    else:
        return "TODO"


def _extract_story_points(fields: dict[str, Any], points_field: str) -> int:

    try:
        if not points_field or points_field.strip() == "":
            return 0

        if points_field == "votes":
            votes_data = fields.get("votes")
            if votes_data is None:
                return 0
            vote_count = votes_data.get("votes", 0)
            return int(vote_count) if vote_count is not None else 0

        elif points_field.startswith("customfield_"):
            value = None
            if "custom_fields" in fields and isinstance(
                fields.get("custom_fields"), dict
            ):
                value = fields["custom_fields"].get(points_field)
            if value is None:
                value = fields.get(points_field)
            if value is None:
                return 0

            if isinstance(value, dict):
                point_val = value.get("value", value.get("count", value.get("total")))
                return int(point_val) if point_val is not None else 0
            elif isinstance(value, str):
                try:
                    return int(float(value))
                except ValueError, TypeError:
                    return 0
            elif isinstance(value, (int, float)):
                return int(value)
            else:
                return 0

        else:
            value = fields.get(points_field)

            if value is None:
                return 0

            if isinstance(value, (int, float)):
                return int(value)

            if isinstance(value, dict):
                point_val = value.get("value", value.get("count", value.get("total")))
                return int(point_val) if point_val is not None else 0

            if isinstance(value, str):
                try:
                    return int(float(value))
                except ValueError, TypeError:
                    return 0

            return 0

    except (ValueError, TypeError, KeyError) as e:
        logger.debug(f"Error extracting points from field '{points_field}': {e}")
        return 0


def _issue_has_real_points(fields: dict[str, Any], points_field: str) -> bool:

    try:
        if not points_field or points_field.strip() == "":
            return False

        if points_field == "votes":
            votes_data = fields.get(points_field)
            if votes_data is None:
                return False
            vote_count = votes_data.get("votes", 0)
            return vote_count > 0
        elif points_field.startswith("customfield_"):
            value = None
            if "custom_fields" in fields and isinstance(
                fields.get("custom_fields"), dict
            ):
                value = fields["custom_fields"].get(points_field)
            if value is None:
                value = fields.get(points_field)
            if value is None:
                return False

            if isinstance(value, dict):
                point_val = value.get(
                    "value", value.get("count", value.get("total", 0))
                )
            elif isinstance(value, (int, float)):
                point_val = value
            elif isinstance(value, str):
                try:
                    point_val = float(value)
                except ValueError:
                    return False
            else:
                return False

            return point_val >= 0
        else:
            value = fields.get(points_field)
            return value is not None and value >= 0
    except Exception:
        return False


def _calculate_remaining_total_points(
    estimated_items: int,
    estimated_points: int,
    remaining_total_items: int,
    completed_items: int = 0,
    completed_points: int = 0,
) -> float:

    if estimated_items <= 0:
        if completed_items > 0 and completed_points > 0:
            avg_points_per_item = completed_points / completed_items
            return remaining_total_items * avg_points_per_item

        return 0

    avg_points_per_item = estimated_points / estimated_items

    unestimated_items = max(0, remaining_total_items - estimated_items)
    remaining_total_points = estimated_points + (
        avg_points_per_item * unestimated_items
    )

    return remaining_total_points


def get_status_breakdown_summary(status_breakdown: dict[str, Any]) -> dict[str, Any]:

    summary = {
        "COMPLETED": {"items": 0, "points": 0, "statuses": []},
        "IN_PROGRESS": {"items": 0, "points": 0, "statuses": []},
        "TODO": {"items": 0, "points": 0, "statuses": []},
    }

    for status_name, data in status_breakdown.items():
        classification = data["classification"]
        summary[classification]["items"] += data["items"]
        summary[classification]["points"] += data["points"]
        summary[classification]["statuses"].append(status_name)

    return summary


def validate_status_config(status_config: dict[str, Any]) -> bool:

    if not isinstance(status_config, dict):
        return False

    method = status_config.get("method", "status_category")
    if method not in ["status_category", "status_names", "hybrid"]:
        return False

    if method == "status_names":
        required_keys = ["completed_statuses", "in_progress_statuses"]
        if not all(key in status_config for key in required_keys):
            return False

        for key in required_keys:
            if not isinstance(status_config[key], list):
                return False

    return True
