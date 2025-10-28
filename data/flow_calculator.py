"""Flow metrics calculator.

Calculates all five Flow metrics from Jira issues:
- Flow Velocity: Number of completed items per period
- Flow Time: Average time from start to completion
- Flow Efficiency: Ratio of active work time to total time
- Flow Load: Current work-in-progress count
- Flow Distribution: Percentage breakdown by work type

Reference: DORA_Flow_Jira_Mapping.md, Flow Framework (Mik Kersten)
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from configuration.flow_config import RECOMMENDED_FLOW_DISTRIBUTION

logger = logging.getLogger(__name__)


def _calculate_trend(
    current_value: Optional[float], previous_period_value: Optional[float]
) -> Dict[str, Any]:
    """Calculate trend direction and percentage change.

    Args:
        current_value: Current period metric value
        previous_period_value: Previous period metric value

    Returns:
        Dictionary with trend_direction ('up'/'down'/'stable') and trend_percentage
    """
    if (
        current_value is None
        or previous_period_value is None
        or previous_period_value == 0
    ):
        return {"trend_direction": "stable", "trend_percentage": 0.0}

    percentage_change = (
        (current_value - previous_period_value) / previous_period_value
    ) * 100

    # Consider changes less than 5% as stable
    if abs(percentage_change) < 5:
        return {
            "trend_direction": "stable",
            "trend_percentage": round(percentage_change, 1),
        }

    direction = "up" if percentage_change > 0 else "down"
    return {
        "trend_direction": direction,
        "trend_percentage": round(percentage_change, 1),
    }


def calculate_flow_velocity(
    issues: List[Dict],
    field_mappings: Dict[str, str],
    start_date: datetime,
    end_date: datetime,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate Flow Velocity - number of completed items per period.

    Args:
        issues: List of Jira issues
        field_mappings: Field mappings for flow_item_type and completed_date
        start_date: Start of measurement period
        end_date: End of measurement period
        previous_period_value: Previous period's metric value for trend calculation

    Returns:
        Metric dictionary with velocity value, trend data, and breakdown by type
    """
    try:
        # Check required mappings
        if (
            "flow_item_type" not in field_mappings
            or "completed_date" not in field_mappings
        ):
            return _create_error_response(
                "flow_velocity",
                "missing_mapping",
                "Missing required field mappings: flow_item_type or completed_date",
            )

        flow_type_field = field_mappings["flow_item_type"]
        completed_field = field_mappings["completed_date"]

        # Count completed items by type
        type_counts = {"Feature": 0, "Defect": 0, "Risk": 0, "Technical_Debt": 0}
        total_count = 0

        for issue in issues:
            fields = issue.get("fields", {})

            # Get completion date
            completed_date_str = fields.get(completed_field)
            if not completed_date_str:
                continue

            # Parse completion date
            try:
                completed_date = datetime.fromisoformat(
                    completed_date_str.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                continue

            # Check if in period
            if not (start_date <= completed_date <= end_date):
                continue

            # Get work type
            work_type_value = fields.get(flow_type_field)
            if isinstance(work_type_value, dict):
                work_type = work_type_value.get("value", "Unknown")
            else:
                work_type = work_type_value

            if work_type in type_counts:
                type_counts[work_type] += 1
                total_count += 1

        if total_count == 0:
            return _create_error_response(
                "flow_velocity",
                "no_data",
                f"No completed items found between {start_date.date()} and {end_date.date()}",
                total_issue_count=len(issues),
            )

        # Calculate period in days for unit display
        period_days = (end_date - start_date).days
        unit = "items/week" if period_days <= 14 else "items/month"

        # Calculate trend if previous period value is provided
        trend_data = _calculate_trend(float(total_count), previous_period_value)

        return {
            "metric_name": "flow_velocity",
            "value": total_count,
            "unit": unit,
            "error_state": "success",
            "error_message": None,
            "excluded_issue_count": 0,
            "total_issue_count": len(issues),
            "trend_direction": trend_data["trend_direction"],
            "trend_percentage": trend_data["trend_percentage"],
            "details": {
                "by_type": type_counts,
            },
        }

    except Exception as e:
        logger.error(f"Error calculating flow velocity: {e}", exc_info=True)
        return _create_error_response("flow_velocity", "calculation_error", str(e))


def calculate_flow_time(
    issues: List[Dict],
    field_mappings: Dict[str, str],
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate Flow Time - average time from start to completion.

    Args:
        issues: List of Jira issues
        field_mappings: Field mappings for work_started_date and work_completed_date
        previous_period_value: Previous period's metric value for trend calculation

    Returns:
        Metric dictionary with average flow time in days and trend data
    """
    try:
        # Check required mappings
        if (
            "work_started_date" not in field_mappings
            or "work_completed_date" not in field_mappings
        ):
            return _create_error_response(
                "flow_time",
                "missing_mapping",
                "Missing required field mappings: work_started_date or work_completed_date",
            )

        start_field = field_mappings["work_started_date"]
        complete_field = field_mappings["work_completed_date"]

        flow_times = []
        excluded_count = 0

        for issue in issues:
            fields = issue.get("fields", {})

            start_date_str = fields.get(start_field)
            complete_date_str = fields.get(complete_field)

            if not start_date_str or not complete_date_str:
                excluded_count += 1
                continue

            try:
                start_date = datetime.fromisoformat(
                    start_date_str.replace("Z", "+00:00")
                )
                complete_date = datetime.fromisoformat(
                    complete_date_str.replace("Z", "+00:00")
                )

                flow_time_days = (complete_date - start_date).total_seconds() / 86400
                if flow_time_days >= 0:
                    flow_times.append(flow_time_days)
                else:
                    excluded_count += 1
            except (ValueError, AttributeError):
                excluded_count += 1
                continue

        if not flow_times:
            return _create_error_response(
                "flow_time",
                "no_data",
                "No issues with valid start and completion dates",
                total_issue_count=len(issues),
                excluded_issue_count=excluded_count,
            )

        average_flow_time = sum(flow_times) / len(flow_times)

        # Calculate trend if previous period value is provided
        trend_data = _calculate_trend(average_flow_time, previous_period_value)

        return {
            "metric_name": "flow_time",
            "value": round(average_flow_time, 1),
            "unit": "days",
            "error_state": "success",
            "error_message": None,
            "excluded_issue_count": excluded_count,
            "total_issue_count": len(issues),
            "trend_direction": trend_data["trend_direction"],
            "trend_percentage": trend_data["trend_percentage"],
        }

    except Exception as e:
        logger.error(f"Error calculating flow time: {e}", exc_info=True)
        return _create_error_response("flow_time", "calculation_error", str(e))


def calculate_flow_efficiency(
    issues: List[Dict],
    field_mappings: Dict[str, str],
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate Flow Efficiency - ratio of active work time to total time.

    Args:
        issues: List of Jira issues
        field_mappings: Field mappings for active_work_hours and flow_time_days
        previous_period_value: Previous period's metric value for trend calculation

    Returns:
        Metric dictionary with efficiency percentage and trend data
    """
    try:
        # Check required mappings
        if (
            "active_work_hours" not in field_mappings
            or "flow_time_days" not in field_mappings
        ):
            return _create_error_response(
                "flow_efficiency",
                "missing_mapping",
                "Missing required field mappings: active_work_hours or flow_time_days",
            )

        active_hours_field = field_mappings["active_work_hours"]
        flow_time_field = field_mappings["flow_time_days"]

        total_active_hours = 0
        total_flow_hours = 0
        excluded_count = 0

        for issue in issues:
            fields = issue.get("fields", {})

            active_hours = fields.get(active_hours_field)
            flow_time_days = fields.get(flow_time_field)

            if active_hours is None or flow_time_days is None:
                excluded_count += 1
                continue

            try:
                active_hours = float(active_hours)
                flow_time_days = float(flow_time_days)

                if active_hours >= 0 and flow_time_days > 0:
                    total_active_hours += active_hours
                    total_flow_hours += flow_time_days * 24  # Convert days to hours
                else:
                    excluded_count += 1
            except (ValueError, TypeError):
                excluded_count += 1
                continue

        if total_flow_hours == 0:
            return _create_error_response(
                "flow_efficiency",
                "no_data",
                "No issues with valid active hours and flow time data",
                total_issue_count=len(issues),
                excluded_issue_count=excluded_count,
            )

        efficiency_percentage = (total_active_hours / total_flow_hours) * 100

        # Calculate trend if previous period value is provided
        trend_data = _calculate_trend(efficiency_percentage, previous_period_value)

        return {
            "metric_name": "flow_efficiency",
            "value": round(efficiency_percentage, 1),
            "unit": "percentage",
            "error_state": "success",
            "error_message": None,
            "excluded_issue_count": excluded_count,
            "total_issue_count": len(issues),
            "trend_direction": trend_data["trend_direction"],
            "trend_percentage": trend_data["trend_percentage"],
        }

    except Exception as e:
        logger.error(f"Error calculating flow efficiency: {e}", exc_info=True)
        return _create_error_response("flow_efficiency", "calculation_error", str(e))


def calculate_flow_load(
    issues: List[Dict],
    field_mappings: Dict[str, str],
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate Flow Load - current work-in-progress count.

    Args:
        issues: List of Jira issues
        field_mappings: Field mappings for status and flow_item_type
        previous_period_value: Previous period's metric value for trend calculation

    Returns:
        Metric dictionary with WIP count, trend data, and breakdown by type
    """
    try:
        # Check required mappings
        if "status" not in field_mappings:
            return _create_error_response(
                "flow_load",
                "missing_mapping",
                "Missing required field mapping: status",
            )

        status_field = field_mappings["status"]
        type_field = field_mappings.get("flow_item_type")

        # Count in-progress items by type
        type_counts = {"Feature": 0, "Defect": 0, "Risk": 0, "Technical_Debt": 0}
        wip_count = 0

        for issue in issues:
            fields = issue.get("fields", {})

            # Get status
            status_value = fields.get(status_field)
            if isinstance(status_value, dict):
                status_name = status_value.get("name", "")
            else:
                status_name = status_value or ""

            # Consider "In Progress" statuses (not Done, not To Do)
            if status_name.lower() not in [
                "done",
                "closed",
                "resolved",
                "to do",
                "open",
            ]:
                wip_count += 1

                # Get work type if available
                if type_field:
                    work_type_value = fields.get(type_field)
                    if isinstance(work_type_value, dict):
                        work_type = work_type_value.get("value", "Unknown")
                    else:
                        work_type = work_type_value

                    if work_type in type_counts:
                        type_counts[work_type] += 1

        # Calculate trend if previous period value is provided
        trend_data = _calculate_trend(float(wip_count), previous_period_value)

        return {
            "metric_name": "flow_load",
            "value": wip_count,
            "unit": "items",
            "error_state": "success",
            "error_message": None,
            "excluded_issue_count": 0,
            "total_issue_count": len(issues),
            "trend_direction": trend_data["trend_direction"],
            "trend_percentage": trend_data["trend_percentage"],
            "details": {
                "by_type": type_counts if type_field else {},
            },
        }

    except Exception as e:
        logger.error(f"Error calculating flow load: {e}", exc_info=True)
        return _create_error_response("flow_load", "calculation_error", str(e))


def calculate_flow_distribution(
    issues: List[Dict],
    field_mappings: Dict[str, str],
    start_date: datetime,
    end_date: datetime,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate Flow Distribution - percentage breakdown by work type.

    Args:
        issues: List of Jira issues
        field_mappings: Field mappings for flow_item_type and completed_date
        start_date: Start of measurement period
        end_date: End of measurement period
        previous_period_value: Previous period's metric value for trend calculation

    Returns:
        Metric dictionary with distribution breakdown, trend data, and recommended range validation
    """
    try:
        # Check required mappings
        if (
            "flow_item_type" not in field_mappings
            or "completed_date" not in field_mappings
        ):
            return _create_error_response(
                "flow_distribution",
                "missing_mapping",
                "Missing required field mappings: flow_item_type or completed_date",
            )

        flow_type_field = field_mappings["flow_item_type"]
        completed_field = field_mappings["completed_date"]

        # Count items by type
        type_counts = {"Feature": 0, "Defect": 0, "Risk": 0, "Technical_Debt": 0}

        for issue in issues:
            fields = issue.get("fields", {})

            # Get completion date
            completed_date_str = fields.get(completed_field)
            if not completed_date_str:
                continue

            # Parse completion date
            try:
                completed_date = datetime.fromisoformat(
                    completed_date_str.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                continue

            # Check if in period
            if not (start_date <= completed_date <= end_date):
                continue

            # Get work type
            work_type_value = fields.get(flow_type_field)
            if isinstance(work_type_value, dict):
                work_type = work_type_value.get("value", "Unknown")
            else:
                work_type = work_type_value

            if work_type in type_counts:
                type_counts[work_type] += 1

        total_count = sum(type_counts.values())

        if total_count == 0:
            return _create_error_response(
                "flow_distribution",
                "no_data",
                f"No completed items found between {start_date.date()} and {end_date.date()}",
                total_issue_count=len(issues),
            )

        # Calculate percentages and check against recommended ranges
        distribution_breakdown = {}
        feature_percentage = 0  # Track feature % for trend calculation
        for work_type, count in type_counts.items():
            percentage = (count / total_count) * 100
            if work_type == "Feature":
                feature_percentage = percentage

            recommended = RECOMMENDED_FLOW_DISTRIBUTION[work_type]

            within_range = (
                recommended["min_percentage"]
                <= percentage
                <= recommended["max_percentage"]
            )

            distribution_breakdown[work_type] = {
                "count": count,
                "percentage": round(percentage, 1),
                "recommended_min": recommended["min_percentage"],
                "recommended_max": recommended["max_percentage"],
                "within_range": within_range,
            }

        # Calculate trend based on Feature percentage
        trend_data = _calculate_trend(feature_percentage, previous_period_value)

        return {
            "metric_name": "flow_distribution",
            "value": 100,  # Total percentage
            "unit": "percentage",
            "error_state": "success",
            "error_message": None,
            "excluded_issue_count": 0,
            "total_issue_count": len(issues),
            "distribution_breakdown": distribution_breakdown,
            "trend_direction": trend_data["trend_direction"],
            "trend_percentage": trend_data["trend_percentage"],
        }

    except Exception as e:
        logger.error(f"Error calculating flow distribution: {e}", exc_info=True)
        return _create_error_response("flow_distribution", "calculation_error", str(e))


def calculate_all_flow_metrics(
    issues: List[Dict],
    field_mappings: Dict[str, str],
    start_date: datetime,
    end_date: datetime,
) -> Dict[str, Dict[str, Any]]:
    """Calculate all five Flow metrics at once.

    Args:
        issues: List of Jira issues
        field_mappings: All required field mappings
        start_date: Start of measurement period
        end_date: End of measurement period

    Returns:
        Dictionary with all five Flow metrics:
        {
            "flow_velocity": {...},
            "flow_time": {...},
            "flow_efficiency": {...},
            "flow_load": {...},
            "flow_distribution": {...}
        }
    """
    return {
        "flow_velocity": calculate_flow_velocity(
            issues, field_mappings, start_date, end_date
        ),
        "flow_time": calculate_flow_time(issues, field_mappings),
        "flow_efficiency": calculate_flow_efficiency(issues, field_mappings),
        "flow_load": calculate_flow_load(issues, field_mappings),
        "flow_distribution": calculate_flow_distribution(
            issues, field_mappings, start_date, end_date
        ),
    }


def _create_error_response(
    metric_name: str,
    error_state: str,
    error_message: str,
    total_issue_count: int = 0,
    excluded_issue_count: int = 0,
) -> Dict[str, Any]:
    """Create a standard error response for metrics.

    Args:
        metric_name: Name of the metric
        error_state: Error state identifier
        error_message: User-friendly error message
        total_issue_count: Total issues considered
        excluded_issue_count: Issues excluded from calculation

    Returns:
        Error response dictionary
    """
    return {
        "metric_name": metric_name,
        "value": None,
        "unit": _get_default_unit(metric_name),
        "error_state": error_state,
        "error_message": error_message,
        "excluded_issue_count": excluded_issue_count,
        "total_issue_count": total_issue_count,
        "trend_direction": "stable",
        "trend_percentage": 0.0,
    }


def _get_default_unit(metric_name: str) -> str:
    """Get default unit for a metric."""
    units = {
        "flow_velocity": "items/period",
        "flow_time": "days",
        "flow_efficiency": "percentage",
        "flow_load": "items",
        "flow_distribution": "percentage",
    }
    return units.get(metric_name, "")
