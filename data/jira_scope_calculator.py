"""
JIRA Scope Calculator Module

This module calculates project scope based on JIRA issue statuses using
status categories and configurable status name mapping.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_jira_project_scope(
    issues_data: List[Dict[str, Any]],
    points_field: str = "votes",
    status_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculate project scope based on JIRA issue statuses.

    Args:
        issues_data: List of JIRA issues from API response
        points_field: Field name for story points (e.g., 'votes', 'customfield_10002')
        status_config: Configuration for status mapping (optional)

    Returns:
        Dict containing:
        - total_items: Total number of issues
        - total_points: Total story points
        - completed_items: Number of completed issues
        - completed_points: Story points for completed issues
        - remaining_items: Number of remaining issues
        - remaining_points: Story points for remaining issues
        - status_breakdown: Detailed breakdown by status
    """

    # Initialize counters
    completed_items = completed_points = 0
    remaining_items = remaining_points = 0
    status_breakdown = {}

    for issue in issues_data:
        try:
            # Extract issue data
            status_name = issue["fields"]["status"]["name"]
            status_category = issue["fields"]["status"]["statusCategory"]["key"]
            points = _extract_story_points(issue["fields"], points_field)

            # Classify status
            classification = _classify_issue_status(
                status_name, status_category, status_config
            )

            # Update counters
            if classification == "COMPLETED":
                completed_items += 1
                completed_points += points
            else:  # IN_PROGRESS or TODO both count as remaining
                remaining_items += 1
                remaining_points += points

            # Track status breakdown for reporting
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

    result = {
        "total_items": total_items,
        "total_points": total_points,
        "completed_items": completed_items,
        "completed_points": completed_points,
        "remaining_items": remaining_items,
        "remaining_points": remaining_points,
        "estimated_items": total_items,  # For compatibility
        "estimated_points": total_points,  # For compatibility
        "status_breakdown": status_breakdown,
        "calculation_metadata": {
            "method": status_config.get("method", "status_category")
            if status_config
            else "status_category",
            "calculated_at": datetime.now().isoformat(),
            "total_issues_processed": len(issues_data),
            "points_field": points_field,
        },
    }

    logger.info(
        f"📊 JIRA Scope Calculated: {completed_items}/{total_items} items completed, "
        f"{completed_points}/{total_points} points completed"
    )

    return result


def _classify_issue_status(
    status_name: str, status_category: str, status_config: Optional[Dict[str, Any]]
) -> str:
    """
    Classify issue status as COMPLETED, IN_PROGRESS, or TODO.

    Args:
        status_name: JIRA status name (e.g., "Done", "In Progress")
        status_category: JIRA status category key (e.g., "done", "indeterminate", "new")
        status_config: Configuration for status mapping

    Returns:
        str: 'COMPLETED', 'IN_PROGRESS', or 'TODO'
    """

    # Method 1: Use configuration overrides if available
    if status_config and status_config.get("method") == "status_names":
        completed_statuses = status_config.get("completed_statuses", [])
        in_progress_statuses = status_config.get("in_progress_statuses", [])

        if status_name in completed_statuses:
            return "COMPLETED"
        elif status_name in in_progress_statuses:
            return "IN_PROGRESS"
        else:
            return "TODO"

    # Method 2: Check for specific status name overrides
    if status_config and "status_name_overrides" in status_config:
        override = status_config["status_name_overrides"].get(status_name)
        if override:
            return override

    # Method 3: Default to status category (recommended)
    if status_category == "done":
        return "COMPLETED"
    elif status_category == "indeterminate":
        return "IN_PROGRESS"
    else:  # 'new'
        return "TODO"


def _extract_story_points(fields: Dict[str, Any], points_field: str) -> int:
    """
    Extract story points from issue fields.

    Args:
        fields: JIRA issue fields dictionary
        points_field: Field name to extract points from

    Returns:
        int: Story points value (defaults to 1 if not found or invalid)
    """
    try:
        if points_field == "votes":
            # Use votes field as fallback
            votes_data = fields.get("votes")
            if votes_data is None:
                return 1  # Default when no votes data
            return votes_data.get("votes", 1)
        elif points_field.startswith("customfield_"):
            # Use custom field
            value = fields.get(points_field, 1)
            if value is None:
                return 1

            # Handle different data types for custom fields
            if isinstance(value, dict):
                # Complex object - try common keys
                return int(
                    value.get("value", value.get("count", value.get("total", 1)))
                )
            elif isinstance(value, str):
                # String representation
                return int(float(value))  # Handle "8.0" -> 8
            else:
                # Direct numeric value
                return int(value)
        else:
            # Try to find in other fields
            value = fields.get(points_field, 1)
            return int(value) if value is not None else 1

    except (ValueError, TypeError, KeyError):
        # If points value is invalid, default to 1
        return 1


def get_status_breakdown_summary(status_breakdown: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a summary of status breakdown for display.

    Args:
        status_breakdown: Status breakdown from calculate_jira_project_scope

    Returns:
        Dict: Summary with totals by classification
    """
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


def validate_status_config(status_config: Dict[str, Any]) -> bool:
    """
    Validate status configuration structure.

    Args:
        status_config: Status configuration dictionary

    Returns:
        bool: True if configuration is valid
    """
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
