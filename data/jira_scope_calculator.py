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
        - remaining_items: Number of remaining issues (all non-completed)
        - remaining_points: Story points for remaining issues (sum of all remaining)
        - estimated_items: Number of remaining issues WITH point values
        - estimated_points: Story points only from issues WITH point values
        - remaining_total_points: Calculated total remaining points (estimated + extrapolated)
        - status_breakdown: Detailed breakdown by status
        - points_field_available: Whether meaningful point data was found
    """

    # Initialize counters
    completed_items = completed_points = 0
    remaining_items = remaining_points = 0
    estimated_items = estimated_points = 0  # Items/points with actual point values
    status_breakdown = {}

    # Check if points field has meaningful data and get detailed stats
    points_field_available, field_stats = (
        _validate_points_field_availability_with_stats(issues_data, points_field)
    )

    logger.info(f"[SCOPE] Starting calculation for {len(issues_data)} issues")

    for issue in issues_data:
        try:
            # Extract issue data - handle both nested (JIRA API) and flat (database) formats
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                # Nested format (JIRA API)
                status_name = issue["fields"]["status"]["name"]
                status_category = issue["fields"]["status"]["statusCategory"]["key"]
                points = _extract_story_points(issue["fields"], points_field)
                has_real_points = _issue_has_real_points(issue["fields"], points_field)
            else:
                # Flat format (database) - fields at root level
                status_name = issue.get("status", "")
                # Database stores status_category as string, not nested object
                status_category = issue.get("status_category", "")
                points = _extract_story_points(issue, points_field)
                has_real_points = _issue_has_real_points(issue, points_field)

            # Classify status
            classification = _classify_issue_status(
                status_name, status_category, status_config
            )

            # Update counters based on classification
            if classification == "COMPLETED":
                completed_items += 1
                completed_points += points
            else:  # IN_PROGRESS or TODO both count as remaining
                remaining_items += 1
                remaining_points += points

                # Only count as "estimated" if it has real point values
                if has_real_points and points_field_available:
                    estimated_items += 1
                    estimated_points += points

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

    logger.info(
        f"[SCOPE] Calculation complete - Total: {total_items}, Completed: {completed_items}, Remaining: {remaining_items}"
    )
    logger.info(
        f"[SCOPE] Points - Total: {total_points}, Completed: {completed_points}, Remaining: {remaining_points}"
    )

    # Calculate remaining_total_points using the specified formula
    # Only calculate if points field is available, otherwise return 0
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
        "remaining_items": remaining_items,  # All non-completed items
        "remaining_points": remaining_points,  # Sum of all remaining item points
        "estimated_items": estimated_items
        if points_field_available
        else 0,  # No items have point values when field is empty
        "estimated_points": estimated_points
        if points_field_available
        else 0,  # No points from estimated items when field is empty
        "remaining_total_points": remaining_total_points,  # Calculated total remaining points
        "points_field_available": points_field_available,  # Flag for UI
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
        f"[Stats] JIRA Scope Calculated: {completed_items}/{total_items} items completed, "
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
        int: Story points value (returns 0 if field is missing/empty/invalid)
    """
    try:
        # First check if points field is valid (not empty/whitespace)
        if not points_field or points_field.strip() == "":
            return 0  # No points field configured

        if points_field == "votes":
            # votes field returns dict: {"votes": 5, "hasVoted": false}
            votes_data = fields.get("votes")
            if votes_data is None:
                return 0  # No votes data = no estimate
            vote_count = votes_data.get("votes", 0)
            # votes can be 0 (valid), so return actual value
            return int(vote_count) if vote_count is not None else 0

        elif points_field.startswith("customfield_"):
            # Custom field - check custom_fields dict first (flat format), then root level (nested format)
            value = None
            if "custom_fields" in fields and isinstance(
                fields.get("custom_fields"), dict
            ):
                value = fields["custom_fields"].get(points_field)
            if value is None:
                value = fields.get(points_field)
            if value is None:
                return 0  # No value = no estimate

            # Handle different data types for custom fields
            if isinstance(value, dict):
                # Complex object - try common keys
                point_val = value.get("value", value.get("count", value.get("total")))
                return int(point_val) if point_val is not None else 0
            elif isinstance(value, str):
                # String representation
                try:
                    return int(float(value))  # Handle "8.0" -> 8
                except (ValueError, TypeError):
                    return 0
            elif isinstance(value, (int, float)):
                # Direct numeric value
                return int(value)
            else:
                # Unknown type
                return 0

        else:
            # Handle standard JIRA fields (timeoriginalestimate, timespent, etc.)
            value = fields.get(points_field)

            # If field doesn't exist or is None, return 0 (no estimate)
            if value is None:
                return 0

            # Time fields return integer seconds or None
            if isinstance(value, (int, float)):
                return int(value)

            # Handle dict format (shouldn't happen for time fields, but be safe)
            if isinstance(value, dict):
                point_val = value.get("value", value.get("count", value.get("total")))
                return int(point_val) if point_val is not None else 0

            # Handle string representations
            if isinstance(value, str):
                try:
                    return int(float(value))
                except (ValueError, TypeError):
                    return 0

            # Unknown type
            return 0

    except (ValueError, TypeError, KeyError) as e:
        logger.debug(f"Error extracting points from field '{points_field}': {e}")
        return 0


def _validate_points_field_availability(
    issues_data: List[Dict[str, Any]], points_field: str
) -> bool:
    """
    Check if points field exists and has meaningful data in the issues.

    Args:
        issues_data: List of JIRA issues
        points_field: Field name to check

    Returns:
        bool: True if points field has meaningful data
    """
    if not points_field or points_field.strip() == "":
        return False

    if not issues_data:
        return False

    # Check if the points field exists in the JIRA data structure (even if some values are null)
    field_exists_count = 0
    valid_points_count = 0
    sample_size = min(10, len(issues_data))  # Sample first 10 issues or all if fewer

    for issue in issues_data[:sample_size]:
        try:
            fields = issue.get("fields", {})

            # Check if field exists in the data structure
            if points_field in fields:
                field_exists_count += 1

                # Also count if it has a valid value
                if points_field == "votes":
                    votes_data = fields.get("votes")
                    if (
                        votes_data and votes_data.get("votes", -1) >= 0
                    ):  # 0 and positive votes are valid
                        valid_points_count += 1
                elif points_field.startswith("customfield_"):
                    value = fields.get(points_field)
                    if value is not None:
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
                                point_val = None  # Invalid string
                        else:
                            point_val = None  # Unknown type

                        if (
                            point_val is not None and point_val >= 0
                        ):  # 0 and positive values are valid
                            valid_points_count += 1
                else:
                    # Other field types
                    value = fields.get(points_field)
                    if (
                        value is not None and value >= 0
                    ):  # 0 and positive values are valid
                        valid_points_count += 1
        except Exception:
            continue

    # Return True if valid point values exist in at least 50% of issues
    # This indicates meaningful data exists (not just None values)
    return valid_points_count > 0 and (valid_points_count / sample_size) >= 0.5


def _validate_points_field_availability_with_stats(
    issues_data: List[Dict[str, Any]], points_field: str
) -> tuple[bool, Dict[str, Any]]:
    """
    Check if points field exists and has meaningful data, returning detailed statistics.

    Args:
        issues_data: List of JIRA issues
        points_field: Field name to check

    Returns:
        tuple: (is_available: bool, stats: Dict with detailed coverage information)
    """
    stats = {
        "field_exists_count": 0,
        "valid_points_count": 0,
        "sample_size": 0,
        "total_issues": len(issues_data),
        "field_coverage_percent": 0.0,
        "valid_coverage_percent": 0.0,
        "threshold_met": False,
        "threshold_required": 0.5,
    }

    if not points_field or points_field.strip() == "":
        return False, stats

    if not issues_data:
        return False, stats

    # Check if the points field exists in the JIRA data structure
    field_exists_count = 0
    valid_points_count = 0
    sample_size = min(10, len(issues_data))  # Sample first 10 issues or all if fewer
    stats["sample_size"] = sample_size

    for issue in issues_data[:sample_size]:
        try:
            # Handle both nested (JIRA API) and flat (database) formats
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                fields = issue["fields"]
            else:
                # Flat format - fields at root level
                fields = issue

            # Check if field exists in the data structure
            # For flat format, custom fields are in custom_fields dict
            field_exists = False
            if (
                points_field.startswith("customfield_")
                and "custom_fields" in fields
                and isinstance(fields.get("custom_fields"), dict)
            ):
                field_exists = points_field in fields["custom_fields"]
            else:
                field_exists = points_field in fields

            if field_exists:
                field_exists_count += 1

                # Also count if it has a valid value
                if points_field == "votes":
                    votes_data = fields.get("votes")
                    if (
                        votes_data and votes_data.get("votes", -1) >= 0
                    ):  # 0 and positive votes are valid
                        valid_points_count += 1
                elif points_field.startswith("customfield_"):
                    # Get value from custom_fields dict if available, otherwise root level
                    value = None
                    if "custom_fields" in fields and isinstance(
                        fields.get("custom_fields"), dict
                    ):
                        value = fields["custom_fields"].get(points_field)
                    if value is None:
                        value = fields.get(points_field)
                    if value is not None:
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
                                point_val = None  # Invalid string
                        else:
                            point_val = None  # Unknown type

                        if (
                            point_val is not None and point_val >= 0
                        ):  # 0 and positive values are valid
                            valid_points_count += 1
                else:
                    # Other field types
                    value = fields.get(points_field)
                    if (
                        value is not None and value >= 0
                    ):  # 0 and positive values are valid
                        valid_points_count += 1
        except Exception:
            continue

    # Update statistics
    stats["field_exists_count"] = field_exists_count
    stats["valid_points_count"] = valid_points_count
    stats["field_coverage_percent"] = (
        (field_exists_count / sample_size * 100) if sample_size > 0 else 0
    )
    stats["valid_coverage_percent"] = (
        (valid_points_count / sample_size * 100) if sample_size > 0 else 0
    )

    # Calculate threshold met (for informational display only - not used to disable features)
    stats["threshold_required"] = (
        0.3  # 30% threshold for quality indicator (informational only)
    )
    threshold_met = (
        valid_points_count > 0
        and (valid_points_count / sample_size) >= stats["threshold_required"]
    )
    stats["threshold_met"] = threshold_met

    # Return True if ANY issues have points (even if below threshold)
    # This lets users decide whether to enable points tracking based on coverage stats
    # Only return False if literally NO points exist or field isn't configured
    has_any_points = valid_points_count > 0
    return has_any_points, stats


def _issue_has_real_points(fields: Dict[str, Any], points_field: str) -> bool:
    """
    Check if a specific issue has real point values (non-null story points).

    Business Logic: An item is "estimated" ONLY if the story points field has a non-null value.
    Items with null story points are considered "not estimated" even if they get default
    points in calculations for extrapolation purposes.

    Args:
        fields: JIRA issue fields dictionary
        points_field: Field name to check

    Returns:
        bool: True if issue has non-null story points (estimated), False otherwise
    """
    try:
        # First check if points field is valid (not empty/whitespace)
        if not points_field or points_field.strip() == "":
            return False  # No points field configured

        if points_field == "votes":
            # votes are engagement metrics, not estimates
            # Only treat as "estimated" if votes > 0
            votes_data = fields.get(points_field)
            if votes_data is None:
                return False  # No votes data
            vote_count = votes_data.get("votes", 0)
            return vote_count > 0  # Only positive votes count as "estimated"
        elif points_field.startswith("customfield_"):
            # Check custom_fields dict first (flat format), then root level (nested format)
            value = None
            if "custom_fields" in fields and isinstance(
                fields.get("custom_fields"), dict
            ):
                value = fields["custom_fields"].get(points_field)
            if value is None:
                value = fields.get(points_field)
            # CORRECT LOGIC: Only non-null values are considered "estimated"
            if value is None:
                return False  # Null values are NOT estimated

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
                    return False  # Invalid string is NOT estimated
            else:
                return False  # Unknown type is NOT estimated

            return point_val >= 0  # 0 and positive values are meaningful
        else:
            # CORRECT LOGIC: Only non-null values are estimated
            value = fields.get(points_field)
            return (
                value is not None and value >= 0
            )  # Only non-null, non-negative values are estimated
    except Exception:
        return False  # On error, consider as NOT estimated


def _calculate_remaining_total_points(
    estimated_items: int,
    estimated_points: int,
    remaining_total_items: int,
    completed_items: int = 0,
    completed_points: int = 0,
) -> float:
    """
    Calculate remaining total points using the formula:
    Remaining Total Points = Remaining Estimated Points +
    (avg_points_per_item × (Remaining Total Items - Remaining Estimated Items))

    Args:
        estimated_items: Number of remaining items with point values
        estimated_points: Sum of points from estimated items
        remaining_total_items: Total number of remaining items
        completed_items: Number of completed items (for historical average)
        completed_points: Points from completed items (for historical average)

    Returns:
        float: Calculated remaining total points
    """
    # If no estimated items, use historical data or fallback
    if estimated_items <= 0:
        # Try to calculate from historical completion data
        if completed_items > 0:
            avg_points_per_item = completed_points / completed_items
        else:
            avg_points_per_item = 10  # Default fallback

        return remaining_total_items * avg_points_per_item

    # Calculate average points per item from estimated items
    avg_points_per_item = estimated_points / estimated_items

    # Apply the formula: estimated points + (avg × unestimated items)
    unestimated_items = max(0, remaining_total_items - estimated_items)
    remaining_total_points = estimated_points + (
        avg_points_per_item * unestimated_items
    )

    return remaining_total_points


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
