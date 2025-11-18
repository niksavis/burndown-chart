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
from configuration.metrics_config import get_metrics_config
from data.performance_utils import log_performance
from data.variable_mapping.extractor import VariableExtractor
from configuration.metric_variables import DEFAULT_VARIABLE_COLLECTION

logger = logging.getLogger(__name__)


def _extract_variables_from_issue(
    issue: Dict[str, Any],
    variable_names: List[str],
    extractor: Optional[VariableExtractor] = None,
) -> Dict[str, Any]:
    """Extract variables from a JIRA issue using VariableExtractor.

    Args:
        issue: JIRA issue dictionary
        variable_names: List of variable names to extract
        extractor: Optional VariableExtractor instance (creates default if None)

    Returns:
        Dictionary mapping variable names to extracted values
    """
    if extractor is None:
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

    # Extract changelog if present in issue
    changelog = issue.get("changelog", {}).get("histories", [])

    results = {}
    for var_name in variable_names:
        extraction_result = extractor.extract_variable(var_name, issue, changelog)
        if extraction_result["found"]:
            results[var_name] = extraction_result["value"]

    return results


def _map_issue_to_flow_type(
    issue: Dict[str, Any],
    flow_type_field: str,
    effort_category_field: Optional[str] = None,
) -> Optional[str]:
    """Classify issue to Flow type using user-configured AND-filter mappings.

    Uses two-tier classification system:
    1. Primary: Issue type must match configured issue_types
    2. Secondary: If effort_categories configured, effort category must also match
    3. Empty effort_categories = no filter (all issues of that type qualify)

    Args:
        issue: JIRA issue dictionary
        flow_type_field: Field ID for issue type (e.g., "issuetype")
        effort_category_field: Optional field ID for effort category

    Returns:
        Flow type ("Feature", "Defect", "Technical_Debt", "Risk") or None if no match

    Examples:
        Feature config: issue_types=["Story"], effort_categories=["New feature"]
        - Story with "New feature" → Feature ✓
        - Story with "Bug Fix" → None ✗

        Defect config: issue_types=["Bug"], effort_categories=[]
        - Bug with any effort category → Defect ✓
    """
    fields = issue.get("fields", {})

    # Extract issue type
    issue_type_value = fields.get(flow_type_field)
    if isinstance(issue_type_value, dict):
        issue_type = issue_type_value.get("name") or issue_type_value.get("value", "")
    else:
        issue_type = str(issue_type_value) if issue_type_value else ""

    if not issue_type:
        return None

    # Extract effort category (optional)
    effort_category = None
    if effort_category_field:
        effort_value = fields.get(effort_category_field)
        if isinstance(effort_value, dict):
            effort_category = effort_value.get("value") or effort_value.get("name")
        else:
            effort_category = str(effort_value) if effort_value else None

    # Use configured classification
    config = get_metrics_config()
    flow_type = config.classify_issue_to_flow_type(issue_type, effort_category)

    return flow_type


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


@log_performance
def calculate_flow_velocity(
    issues: List[Dict],
    field_mappings: Optional[Dict[str, str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    previous_period_value: Optional[float] = None,
    use_variable_extraction: bool = False,
    variable_extractor: Optional[VariableExtractor] = None,
) -> Dict[str, Any]:
    """Calculate Flow Velocity - number of completed items per period.

    Supports both legacy field_mappings and new variable extraction modes.

    Args:
        issues: List of Jira issues
        field_mappings: (Legacy) Field mappings for flow_item_type and completed_date
        start_date: Start of measurement period
        end_date: End of measurement period
        previous_period_value: Previous period's metric value for trend calculation
        use_variable_extraction: If True, use VariableExtractor instead of field_mappings
        variable_extractor: Optional VariableExtractor instance (uses DEFAULT if None)

    Returns:
        Metric dictionary with velocity value, trend data, and breakdown by type
    """
    # Input validation
    if not issues or not isinstance(issues, list):
        logger.warning("[Flow] Velocity: No issues provided")
        return _create_error_response(
            "flow_velocity",
            "no_data",
            "No issues provided for calculation",
            total_issue_count=0,
        )

    # Validate configuration based on mode
    if not use_variable_extraction:
        # Legacy mode: require field_mappings
        if not isinstance(field_mappings, dict):
            logger.error("[Flow] Velocity: Invalid field mappings")
            return _create_error_response(
                "flow_velocity",
                "calculation_error",
                "Invalid field mappings configuration",
                total_issue_count=len(issues),
            )
    else:
        # Variable extraction mode: create extractor if not provided
        if variable_extractor is None:
            variable_extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

    # Validate date parameters
    if start_date is not None and end_date is not None:
        if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
            logger.error("[Flow] Velocity: Invalid date parameters")
            return _create_error_response(
                "flow_velocity",
                "calculation_error",
                "Invalid date parameters",
                total_issue_count=len(issues),
            )

        if start_date >= end_date:
            logger.error(
                f"[Flow] Velocity: Invalid date range: {start_date} to {end_date}"
            )
            return _create_error_response(
                "flow_velocity",
                "calculation_error",
                "Start date must be before end date",
                total_issue_count=len(issues),
            )

    try:
        # Check required configuration based on mode
        # Initialize field variables for legacy mode
        flow_type_field: Optional[str] = None
        completed_field: Optional[str] = None
        effort_category_field: Optional[str] = None

        if not use_variable_extraction:
            # Legacy mode: Check for required field mappings
            if (
                field_mappings is None
                or "flow_item_type" not in field_mappings
                or "completed_date" not in field_mappings
            ):
                return _create_error_response(
                    "flow_velocity",
                    "missing_mapping",
                    "Missing required field mappings: flow_item_type or completed_date",
                )

            flow_type_field = field_mappings["flow_item_type"]
            completed_field = field_mappings["completed_date"]
            effort_category_field = field_mappings.get("effort_category")  # Optional

        # Count completed items by type
        type_counts = {"Feature": 0, "Defect": 0, "Risk": 0, "Technical_Debt": 0}
        total_count = 0

        for issue in issues:
            if use_variable_extraction:
                # NEW: Variable extraction mode
                variables = _extract_variables_from_issue(
                    issue,
                    ["work_completed_timestamp", "work_type_category"],
                    variable_extractor,
                )

                # Get completion timestamp
                completed_date_str = variables.get("work_completed_timestamp")
                if not completed_date_str:
                    continue

                # Parse completion date
                try:
                    completed_date = datetime.fromisoformat(
                        completed_date_str.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    continue

                # Check if in period (only if dates provided)
                if start_date and end_date:
                    if not (start_date <= completed_date <= end_date):
                        continue

                # Get work type from variable
                work_type = variables.get("work_type_category")

            else:
                # LEGACY: Field mappings mode
                # These are guaranteed to be set by validation above
                assert completed_field is not None
                assert flow_type_field is not None

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

                # Check if in period (only if dates provided)
                if start_date and end_date:
                    if not (start_date <= completed_date <= end_date):
                        continue

                # Classify issue to Flow type using configured mappings
                work_type = _map_issue_to_flow_type(
                    issue, flow_type_field, effort_category_field
                )

            if work_type and work_type in type_counts:
                type_counts[work_type] += 1
                total_count += 1

        if total_count == 0:
            date_range_msg = ""
            if start_date and end_date:
                date_range_msg = f" between {start_date.date()} and {end_date.date()}"
            return _create_error_response(
                "flow_velocity",
                "no_data",
                f"No completed items found{date_range_msg}",
                total_issue_count=len(issues),
            )

        # Calculate period in days for unit display
        if start_date and end_date:
            period_days = (end_date - start_date).days
            unit = "items/week" if period_days <= 14 else "items/month"
        else:
            unit = "items"

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
        logger.error(f"[Flow] Error calculating velocity: {e}", exc_info=True)
        return _create_error_response("flow_velocity", "calculation_error", str(e))


@log_performance
def calculate_flow_time(
    issues: List[Dict],
    field_mappings: Optional[Dict[str, str]] = None,
    previous_period_value: Optional[float] = None,
    wip_statuses: Optional[List[str]] = None,
    completion_statuses: Optional[List[str]] = None,
    use_variable_extraction: bool = False,
    variable_extractor: Optional[VariableExtractor] = None,
) -> Dict[str, Any]:
    """Calculate Flow Time - average time from WIP start to completion.

    Supports both legacy field_mappings and new variable extraction modes.

    Work Started: First transition into ANY wip_statuses (from changelog)
    Work Completed: From work_completed_date field (resolutiondate)

    Args:
        issues: List of Jira issues (with changelog data)
        field_mappings: (Legacy) Field mappings for work_completed_date
        previous_period_value: Previous period's metric value for trend calculation
        wip_statuses: List of WIP status names (e.g., ["Selected", "In Progress", ...])
                     If None, loads from configuration
        completion_statuses: List of completion status names (optional, for validation)
        use_variable_extraction: If True, use VariableExtractor instead of field_mappings
        variable_extractor: Optional VariableExtractor instance (uses DEFAULT if None)

    Returns:
        Metric dictionary with average flow time in days and trend data
    """
    # Input validation
    if not issues or not isinstance(issues, list):
        logger.warning("[Flow] Flow time: No issues provided")
        return _create_error_response(
            "flow_time",
            "no_data",
            "No issues provided for calculation",
            total_issue_count=0,
        )

    # Validate configuration based on mode
    if not use_variable_extraction:
        # Legacy mode: require field_mappings
        if not isinstance(field_mappings, dict):
            logger.error("[Flow] Flow time: Invalid field mappings")
            return _create_error_response(
                "flow_time",
                "calculation_error",
                "Invalid field mappings configuration",
                total_issue_count=len(issues),
            )
    else:
        # Variable extraction mode: create extractor if not provided
        if variable_extractor is None:
            variable_extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

    try:
        # Import changelog processor (used in legacy mode)
        from data.changelog_processor import get_first_status_transition_from_list

        # Initialize field variable for legacy mode
        complete_field: Optional[str] = None

        # Check required configuration based on mode
        if not use_variable_extraction:
            # Legacy mode: Check for required field mappings
            if field_mappings is None or "work_completed_date" not in field_mappings:
                return _create_error_response(
                    "flow_time",
                    "missing_mapping",
                    "Missing required field mapping: work_completed_date",
                )

            complete_field = field_mappings["work_completed_date"]

            # Load wip_statuses from configuration if not provided
            if wip_statuses is None:
                from configuration.metrics_config import get_metrics_config

                config = get_metrics_config()
                wip_statuses = config.get_wip_included_statuses()
                if not wip_statuses:
                    return _create_error_response(
                        "flow_time",
                        "missing_config",
                        "Configure 'wip_statuses' in app_settings.json",
                    )

        flow_times = []
        excluded_count = 0
        no_wip_transition_count = 0

        for issue in issues:
            if use_variable_extraction:
                # NEW: Variable extraction mode
                variables = _extract_variables_from_issue(
                    issue,
                    ["work_started_timestamp", "work_completed_timestamp"],
                    variable_extractor,
                )

                # Get work started timestamp
                start_date_str = variables.get("work_started_timestamp")
                if not start_date_str:
                    no_wip_transition_count += 1
                    excluded_count += 1
                    continue

                # Get work completed timestamp
                complete_date_str = variables.get("work_completed_timestamp")
                if not complete_date_str:
                    excluded_count += 1
                    continue

                # Parse dates
                try:
                    start_date = datetime.fromisoformat(
                        start_date_str.replace("Z", "+00:00")
                    )
                    complete_date = datetime.fromisoformat(
                        complete_date_str.replace("Z", "+00:00")
                    )

                    flow_time_days = (
                        complete_date - start_date
                    ).total_seconds() / 86400
                    if flow_time_days >= 0:
                        flow_times.append(flow_time_days)
                    else:
                        excluded_count += 1
                except (ValueError, AttributeError):
                    excluded_count += 1
                    continue

            else:
                # LEGACY: Field mappings mode
                # complete_field is guaranteed to be set by validation above
                assert complete_field is not None
                assert wip_statuses is not None

                fields = issue.get("fields", {})

                # Get work started date from CHANGELOG - first transition to any wip_statuses
                work_started_result = get_first_status_transition_from_list(
                    issue, wip_statuses, case_sensitive=False
                )

                if not work_started_result:
                    # Issue never entered WIP statuses
                    no_wip_transition_count += 1
                    excluded_count += 1
                    continue

                _, start_date = work_started_result  # Unpack (status_name, timestamp)

                # Get completion date from field
                complete_date_str = fields.get(complete_field)

                if not complete_date_str:
                    excluded_count += 1
                    continue

                try:
                    complete_date = datetime.fromisoformat(
                        complete_date_str.replace("Z", "+00:00")
                    )

                    flow_time_days = (
                        complete_date - start_date
                    ).total_seconds() / 86400
                    if flow_time_days >= 0:
                        flow_times.append(flow_time_days)
                    else:
                        excluded_count += 1
                except (ValueError, AttributeError):
                    excluded_count += 1
                    continue

        if not flow_times:
            error_details = []
            if no_wip_transition_count > 0:
                error_details.append(
                    f"{no_wip_transition_count} never entered WIP statuses"
                )

            error_msg = "No issues with valid start and completion dates"
            if error_details:
                error_msg += f" ({', '.join(error_details)})"

            return _create_error_response(
                "flow_time",
                "no_data",
                error_msg,
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
        logger.error(f"[Flow] Error calculating flow time: {e}", exc_info=True)
        return _create_error_response("flow_time", "calculation_error", str(e))


@log_performance
def calculate_flow_efficiency(
    issues: List[Dict],
    field_mappings: Optional[Dict[str, str]] = None,
    previous_period_value: Optional[float] = None,
    active_statuses: Optional[List[str]] = None,
    wip_statuses: Optional[List[str]] = None,
    use_variable_extraction: bool = False,
    variable_extractor: Optional[VariableExtractor] = None,
) -> Dict[str, Any]:
    """Calculate Flow Efficiency - ratio of active work time to total WIP time.

    Supports both legacy field_mappings and new variable extraction modes.

    Flow Efficiency = (time in active_statuses / time in wip_statuses) × 100

    Uses changelog to calculate:
    - Active time: Total time spent in active_statuses (actual work)
    - WIP time: Total time spent in wip_statuses (includes waiting)

    Args:
        issues: List of Jira issues (with changelog data)
        field_mappings: (Legacy) Field mappings (not used for changelog-based calculation)
        previous_period_value: Previous period's metric value for trend calculation
        active_statuses: List of active status names (e.g., ["In Progress", "In Review", "Testing"])
                        If None, loads from configuration
        wip_statuses: List of WIP status names (e.g., ["Selected", "In Progress", ...])
                     If None, loads from configuration
        use_variable_extraction: If True, use VariableExtractor instead of field_mappings
        variable_extractor: Optional VariableExtractor instance (uses DEFAULT if None)

    Returns:
        Metric dictionary with efficiency percentage and trend data

    Note:
        Variable extraction mode requires T009 (changelog analysis support) for
        active_time and total_time CalculatedSource variables. Currently returns
        error_state='not_implemented' in variable extraction mode.
    """
    # Input validation
    if not issues or not isinstance(issues, list):
        logger.warning("[Flow] Efficiency: No issues provided")
        return _create_error_response(
            "flow_efficiency",
            "no_data",
            "No issues provided for calculation",
            total_issue_count=0,
        )

    # Validate configuration based on mode
    if not use_variable_extraction:
        # Legacy mode: require field_mappings
        if not isinstance(field_mappings, dict):
            logger.error("[Flow] Efficiency: Invalid field mappings")
            return _create_error_response(
                "flow_efficiency",
                "calculation_error",
                "Invalid field mappings configuration",
                total_issue_count=len(issues),
            )
    else:
        # Variable extraction mode: create extractor if not provided
        if variable_extractor is None:
            variable_extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

        # NOTE: Flow efficiency requires CalculatedSource support (T009)
        # active_time and total_time need changelog duration calculations
        logger.warning(
            "[Flow] Efficiency: Variable extraction mode requires T009 (changelog analysis)"
        )
        return _create_error_response(
            "flow_efficiency",
            "not_implemented",
            "Variable extraction mode requires changelog analysis support (T009)",
            total_issue_count=len(issues),
        )

    try:
        # Import changelog processor
        from data.changelog_processor import calculate_time_in_status

        # Load statuses from configuration if not provided
        if active_statuses is None or wip_statuses is None:
            from configuration.metrics_config import get_metrics_config

            config = get_metrics_config()

            if active_statuses is None:
                active_statuses = config.get_active_statuses()
            if wip_statuses is None:
                wip_statuses = config.get_wip_included_statuses()

            if not active_statuses:
                return _create_error_response(
                    "flow_efficiency",
                    "missing_config",
                    "Configure 'active_statuses' in app_settings.json",
                )
            if not wip_statuses:
                return _create_error_response(
                    "flow_efficiency",
                    "missing_config",
                    "Configure 'wip_statuses' in app_settings.json",
                )

        total_active_hours = 0
        total_wip_hours = 0
        excluded_count = 0
        no_changelog_count = 0

        for issue in issues:
            # LEGACY: Changelog-based calculation (no variable extraction yet)
            # Calculate time in active statuses (working)
            active_hours = calculate_time_in_status(
                issue, active_statuses, case_sensitive=False
            )

            # Calculate time in all WIP statuses (total flow time)
            wip_hours = calculate_time_in_status(
                issue, wip_statuses, case_sensitive=False
            )

            if wip_hours == 0:
                # Issue never entered WIP or no changelog data
                if not issue.get("changelog"):
                    no_changelog_count += 1
                excluded_count += 1
                continue

            # Accumulate totals
            total_active_hours += active_hours
            total_wip_hours += wip_hours

        if total_wip_hours == 0:
            error_details = []
            if no_changelog_count > 0:
                error_details.append(f"{no_changelog_count} missing changelog data")

            error_msg = "No issues with valid WIP time data"
            if error_details:
                error_msg += f" ({', '.join(error_details)})"

            return _create_error_response(
                "flow_efficiency",
                "no_data",
                error_msg,
                total_issue_count=len(issues),
                excluded_issue_count=excluded_count,
            )

        efficiency_percentage = (total_active_hours / total_wip_hours) * 100

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
        logger.error(f"[Flow] Error calculating efficiency: {e}", exc_info=True)
        return _create_error_response("flow_efficiency", "calculation_error", str(e))


@log_performance
def calculate_flow_load(
    issues: List[Dict],
    field_mappings: Optional[Dict[str, str]] = None,
    previous_period_value: Optional[float] = None,
    use_variable_extraction: bool = False,
    variable_extractor: Optional[VariableExtractor] = None,
) -> Dict[str, Any]:
    """Calculate Flow Load - current work-in-progress count.

    Supports both legacy field_mappings and new variable extraction modes.

    Args:
        issues: List of Jira issues
        field_mappings: (Legacy) Field mappings for status and flow_item_type
        previous_period_value: Previous period's metric value for trend calculation
        use_variable_extraction: If True, use VariableExtractor instead of field_mappings
        variable_extractor: Optional VariableExtractor instance (uses DEFAULT if None)

    Returns:
        Metric dictionary with WIP count, trend data, and breakdown by type
    """
    # Input validation
    if not issues or not isinstance(issues, list):
        logger.warning("[Flow] Load: No issues provided")
        return _create_error_response(
            "flow_load",
            "no_data",
            "No issues provided for calculation",
            total_issue_count=0,
        )

    # Validate configuration based on mode
    if not use_variable_extraction:
        # Legacy mode: require field_mappings
        if not isinstance(field_mappings, dict):
            logger.error("[Flow] Load: Invalid field mappings")
            return _create_error_response(
                "flow_load",
                "calculation_error",
                "Invalid field mappings configuration",
                total_issue_count=len(issues),
            )
    else:
        # Variable extraction mode: create extractor if not provided
        if variable_extractor is None:
            variable_extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

    try:
        # Initialize field variables for legacy mode
        status_field: Optional[str] = None
        type_field: Optional[str] = None
        effort_category_field: Optional[str] = None

        # Check required configuration based on mode
        if not use_variable_extraction:
            # Legacy mode: Check for required field mappings
            if field_mappings is None or "status" not in field_mappings:
                return _create_error_response(
                    "flow_load",
                    "missing_mapping",
                    "Missing required field mapping: status",
                )

            status_field = field_mappings["status"]
            type_field = field_mappings.get("flow_item_type")
            effort_category_field = field_mappings.get("effort_category")  # Optional

        # Count in-progress items by type
        type_counts = {"Feature": 0, "Defect": 0, "Risk": 0, "Technical_Debt": 0}
        wip_count = 0

        for issue in issues:
            if use_variable_extraction:
                # NEW: Variable extraction mode
                variables = _extract_variables_from_issue(
                    issue,
                    ["is_in_progress", "work_type_category"],
                    variable_extractor,
                )

                # Check if issue is in progress
                is_wip = variables.get("is_in_progress")
                if not is_wip:
                    continue

                wip_count += 1

                # Get work type from variable
                work_type = variables.get("work_type_category")
                if work_type and work_type in type_counts:
                    type_counts[work_type] += 1

            else:
                # LEGACY: Field mappings mode
                assert status_field is not None

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

                    # Classify work type if available
                    if type_field:
                        work_type = _map_issue_to_flow_type(
                            issue, type_field, effort_category_field
                        )

                        if work_type and work_type in type_counts:
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
        logger.error(f"[Flow] Error calculating load: {e}", exc_info=True)
        return _create_error_response("flow_load", "calculation_error", str(e))


@log_performance
def calculate_flow_distribution(
    issues: List[Dict],
    field_mappings: Optional[Dict[str, str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    previous_period_value: Optional[float] = None,
    use_variable_extraction: bool = False,
    variable_extractor: Optional[VariableExtractor] = None,
) -> Dict[str, Any]:
    """Calculate Flow Distribution - percentage breakdown by work type.

    Supports both legacy field_mappings and new variable extraction modes.

    Args:
        issues: List of Jira issues
        field_mappings: (Legacy) Field mappings for flow_item_type and completed_date
        start_date: Start of measurement period (optional in variable extraction mode)
        end_date: End of measurement period (optional in variable extraction mode)
        previous_period_value: Previous period's metric value for trend calculation
        use_variable_extraction: If True, use VariableExtractor instead of field_mappings
        variable_extractor: Optional VariableExtractor instance (uses DEFAULT if None)

    Returns:
        Metric dictionary with distribution breakdown, trend data, and recommended range validation
    """
    # Input validation
    if not issues or not isinstance(issues, list):
        logger.warning("[Flow] Distribution: No issues provided")
        return _create_error_response(
            "flow_distribution",
            "no_data",
            "No issues provided for calculation",
            total_issue_count=0,
        )

    # Validate configuration based on mode
    if not use_variable_extraction:
        # Legacy mode: require field_mappings
        if not isinstance(field_mappings, dict):
            logger.error("[Flow] Distribution: Invalid field mappings")
            return _create_error_response(
                "flow_distribution",
                "calculation_error",
                "Invalid field mappings configuration",
                total_issue_count=len(issues),
            )
    else:
        # Variable extraction mode: create extractor if not provided
        if variable_extractor is None:
            variable_extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

    # Validate date parameters (only if provided)
    if start_date is not None and end_date is not None:
        if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
            logger.error("[Flow] Distribution: Invalid date parameters")
            return _create_error_response(
                "flow_distribution",
                "calculation_error",
                "Invalid date parameters",
                total_issue_count=len(issues),
            )

        if start_date >= end_date:
            logger.error(
                f"[Flow] Distribution: Invalid date range: {start_date} to {end_date}"
            )
            return _create_error_response(
                "flow_distribution",
                "calculation_error",
                "Start date must be before end date",
                total_issue_count=len(issues),
            )

    try:
        # Initialize field variables for legacy mode
        flow_type_field: Optional[str] = None
        completed_field: Optional[str] = None
        effort_category_field: Optional[str] = None

        # Check required configuration based on mode
        if not use_variable_extraction:
            # Legacy mode: Check for required field mappings
            if (
                field_mappings is None
                or "flow_item_type" not in field_mappings
                or "completed_date" not in field_mappings
            ):
                return _create_error_response(
                    "flow_distribution",
                    "missing_mapping",
                    "Missing required field mappings: flow_item_type or completed_date",
                )

            flow_type_field = field_mappings["flow_item_type"]
            completed_field = field_mappings["completed_date"]
            effort_category_field = field_mappings.get("effort_category")  # Optional

        # Count items by type
        type_counts = {"Feature": 0, "Defect": 0, "Risk": 0, "Technical_Debt": 0}

        for issue in issues:
            if use_variable_extraction:
                # NEW: Variable extraction mode
                variables = _extract_variables_from_issue(
                    issue,
                    ["work_completed_timestamp", "work_type_category"],
                    variable_extractor,
                )

                # Get completion timestamp
                completed_date_str = variables.get("work_completed_timestamp")
                if not completed_date_str:
                    continue

                # Parse completion date
                try:
                    completed_date = datetime.fromisoformat(
                        completed_date_str.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    continue

                # Check if in period (only if dates provided)
                if start_date and end_date:
                    if not (start_date <= completed_date <= end_date):
                        continue

                # Get work type from variable
                work_type = variables.get("work_type_category")

            else:
                # LEGACY: Field mappings mode
                assert completed_field is not None
                assert flow_type_field is not None
                assert start_date is not None
                assert end_date is not None

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

                # Classify issue to Flow type using configured mappings
                work_type = _map_issue_to_flow_type(
                    issue, flow_type_field, effort_category_field
                )

            if work_type and work_type in type_counts:
                type_counts[work_type] += 1

        total_count = sum(type_counts.values())

        if total_count == 0:
            date_range_msg = ""
            if start_date and end_date:
                date_range_msg = f" between {start_date.date()} and {end_date.date()}"
            return _create_error_response(
                "flow_distribution",
                "no_data",
                f"No completed items found{date_range_msg}",
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
        logger.error(f"[Flow] Error calculating distribution: {e}", exc_info=True)
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
    import time

    calc_start = time.time()

    period_days = (end_date - start_date).days
    logger.info(
        f"[Flow] Starting calculation: {len(issues)} issues, {period_days}d period"
    )

    results = {
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

    elapsed_time = time.time() - calc_start
    logger.info(f"[Flow] Calculated 5 metrics in {elapsed_time:.2f}s")
    return results


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


# ==============================================================================
# DORA & FLOW METRICS v2 (Configuration-Driven)
# ==============================================================================
# New functions using workflow configuration and field mappings
# Updated: November 7, 2025


def calculate_flow_velocity_v2(
    issues: List[Any],
    completion_statuses: List[str],
    start_date: datetime,
    end_date: datetime,
    effort_category_field: str = "customfield_10003",
) -> Dict[str, Any]:
    """
    Calculate Flow Velocity v2 - Count completed issues by Flow type.

    Uses two-tier classification from flow_type_classifier:
    - Primary: Issue type → Flow type (Bug always = Defect)
    - Secondary: Effort category → Flow type (Task/Story only)

    Args:
        issues: List of JIRA issue objects (not dicts)
        completion_statuses: List of completion status names from config (e.g., ["Done", "Resolved", "Closed"])
        start_date: Start of measurement period (timezone-aware)
        end_date: End of measurement period (timezone-aware)
        effort_category_field: Custom field ID for effort category (default: customfield_10003)

    Returns:
        Dictionary with:
        {
            "metric_name": "flow_velocity",
            "total_completed": 70,
            "by_flow_type": {
                "Feature": 45,
                "Defect": 12,
                "Technical Debt": 8,
                "Risk": 5
            },
            "unit": "items/week",
            "error_state": "success",
            "error_message": None,
            "excluded_issue_count": 15,
            "total_issue_count": 85,
            "exclusion_reasons": {
                "not_in_completion_status": 10,
                "outside_date_range": 5
            }
        }

    Example:
        >>> from datetime import datetime, timezone
        >>> from data.jira_simple import fetch_all_issues
        >>> from configuration.flow_config import FlowConfig
        >>>
        >>> config = FlowConfig()
        >>> issues = fetch_all_issues()
        >>> start = datetime(2025, 10, 1, tzinfo=timezone.utc)
        >>> end = datetime(2025, 10, 31, 23, 59, 59, tzinfo=timezone.utc)
        >>>
        >>> result = calculate_flow_velocity_v2(
        ...     issues,
        ...     config.get_completion_statuses(),
        ...     start,
        ...     end
        ... )
        >>> print(f"Completed: {result['total_completed']}")
        >>> print(f"Features: {result['by_flow_type']['Feature']}")
    """
    from data.flow_type_classifier import (
        count_by_flow_type,
        FLOW_TYPE_FEATURE,
        FLOW_TYPE_DEFECT,
        FLOW_TYPE_TECHNICAL_DEBT,
        FLOW_TYPE_RISK,
    )

    logger.info(
        f"[Flow] Velocity v2: {len(issues)} issues between {start_date.date()} and {end_date.date()}"
    )

    # Exclusion tracking
    exclusion_reasons = {
        "not_in_completion_status": 0,
        "outside_date_range": 0,
        "missing_completion_date": 0,
    }

    # Filter to completed issues in date range
    completed_issues = []

    for issue in issues:
        # Check completion status (case-insensitive)
        fields = issue.get("fields", {})
        status_obj = fields.get("status", {})
        status_name = status_obj.get("name") if isinstance(status_obj, dict) else None

        if not status_name:
            exclusion_reasons["not_in_completion_status"] += 1
            continue

        # Case-insensitive status matching
        status_matched = any(
            status_name.lower() == cs.lower() for cs in completion_statuses
        )

        if not status_matched:
            exclusion_reasons["not_in_completion_status"] += 1
            continue

        # Get completion date (resolutiondate)
        completion_date_str = fields.get("resolutiondate")
        if not completion_date_str:
            exclusion_reasons["missing_completion_date"] += 1
            issue_key = issue.get("key", "unknown")
            logger.debug(
                f"[Flow] {issue_key}: No resolutiondate despite completion status"
            )
            continue

        # Parse completion date
        try:
            # JIRA format: "2025-10-31T15:30:45.123+0200"
            completion_date = datetime.fromisoformat(
                completion_date_str.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError) as e:
            exclusion_reasons["missing_completion_date"] += 1
            issue_key = issue.get("key", "unknown")
            logger.warning(
                f"[Flow] {issue_key}: Invalid resolutiondate format: {completion_date_str} - {e}"
            )
            continue

        # Check if in date range
        if not (start_date <= completion_date <= end_date):
            exclusion_reasons["outside_date_range"] += 1
            continue

        # Issue is completed in period
        completed_issues.append(issue)

    logger.info(
        f"[Flow] {len(completed_issues)} completed issues in period (excluded {sum(exclusion_reasons.values())})"
    )

    # No completed issues
    if len(completed_issues) == 0:
        logger.warning(
            f"[Flow] No completed issues between {start_date.date()} and {end_date.date()}"
        )
        return {
            "metric_name": "flow_velocity",
            "total_completed": 0,
            "by_flow_type": {
                FLOW_TYPE_FEATURE: 0,
                FLOW_TYPE_DEFECT: 0,
                FLOW_TYPE_TECHNICAL_DEBT: 0,
                FLOW_TYPE_RISK: 0,
            },
            "unit": "items/week",
            "error_state": "no_data",
            "error_message": f"No completed issues found between {start_date.date()} and {end_date.date()}",
            "excluded_issue_count": sum(exclusion_reasons.values()),
            "total_issue_count": len(issues),
            "exclusion_reasons": exclusion_reasons,
        }

    # Classify by Flow type
    flow_type_counts = count_by_flow_type(completed_issues, effort_category_field)
    total_completed = sum(flow_type_counts.values())

    # Calculate period for unit display
    period_days = (end_date - start_date).days
    unit = "items/week" if period_days <= 14 else "items/month"

    logger.info(
        f"[Flow] Velocity: {total_completed} items - Feature={flow_type_counts[FLOW_TYPE_FEATURE]}, Defect={flow_type_counts[FLOW_TYPE_DEFECT]}, Tech Debt={flow_type_counts[FLOW_TYPE_TECHNICAL_DEBT]}, Risk={flow_type_counts[FLOW_TYPE_RISK]}"
    )

    return {
        "metric_name": "flow_velocity",
        "total_completed": total_completed,
        "by_flow_type": flow_type_counts,
        "unit": unit,
        "error_state": "success",
        "error_message": None,
        "excluded_issue_count": sum(exclusion_reasons.values()),
        "total_issue_count": len(issues),
        "exclusion_reasons": exclusion_reasons,
    }


def calculate_flow_time_v2(
    issues: List[Any],
    start_statuses: List[str],
    completion_statuses: List[str],
    active_statuses: Optional[List[str]] = None,
    case_sensitive: bool = False,
) -> Dict[str, Any]:
    """
    Calculate Flow Time v2 - Time from work start to completion.

    Two calculation methods:
    1. Total Flow Time: Time from first "In Progress" to completion (includes waiting)
    2. Active Time Only: Time spent in active statuses (excludes waiting)

    Uses changelog_processor.calculate_flow_time() for time calculations.

    Args:
        issues: List of JIRA issue objects (not dicts) with expanded changelog
        start_statuses: Statuses that mark flow start (e.g., ["In Progress"])
        completion_statuses: Statuses that mark completion (e.g., ["Done", "Resolved", "Closed"])
        active_statuses: Optional list of active statuses for active-time calculation
                        (e.g., ["In Progress", "In Review", "Testing"])
        case_sensitive: Whether to match status names case-sensitively (default: False)

    Returns:
        Dictionary with:
        {
            "metric_name": "flow_time",
            "total_flow_time": {
                "median_hours": 48.5,
                "mean_hours": 52.3,
                "p75_hours": 72.0,
                "p90_hours": 96.0,
                "p95_hours": 120.0,
                "count": 45
            },
            "active_time": {
                "median_hours": 24.0,
                "mean_hours": 28.5,
                "p75_hours": 36.0,
                "p90_hours": 48.0,
                "p95_hours": 60.0,
                "count": 45
            },
            "flow_efficiency": {
                "median_percent": 42.5,
                "mean_percent": 45.2,
                "count": 45
            },
            "unit": "hours",
            "error_state": "success",
            "error_message": None,
            "excluded_issue_count": 15,
            "total_issue_count": 60,
            "exclusion_reasons": {
                "never_entered_start_status": 10,
                "not_yet_completed": 5
            }
        }

    Example:
        >>> from datetime import datetime, timezone
        >>> from data.jira_simple import fetch_all_issues_with_changelog
        >>> from configuration.flow_config import FlowConfig
        >>>
        >>> config = FlowConfig()
        >>> issues = fetch_all_issues_with_changelog()  # Includes changelog
        >>>
        >>> result = calculate_flow_time_v2(
        ...     issues,
        ...     start_statuses=["In Progress"],
        ...     completion_statuses=["Done", "Resolved", "Closed"],
        ...     active_statuses=["In Progress", "In Review", "Testing"]
        ... )
        >>> print(f"Median Flow Time: {result['total_flow_time']['median_hours']:.1f}h")
        >>> print(f"Median Active Time: {result['active_time']['median_hours']:.1f}h")
        >>> print(f"Median Flow Efficiency: {result['flow_efficiency']['median_percent']:.1f}%")
    """
    from data.changelog_processor import calculate_flow_time
    import statistics

    logger.info(f"[Flow] Flow time v2: {len(issues)} issues")

    # Exclusion tracking
    exclusion_reasons = {
        "never_entered_start_status": 0,
        "not_yet_completed": 0,
        "missing_changelog": 0,
    }

    # Collect flow time data
    total_flow_times = []
    active_times = []
    flow_efficiencies = []

    for issue in issues:
        # Handle both dict and object formats
        if isinstance(issue, dict):
            issue_key = issue.get("key", "unknown")
            issue_dict = {"key": issue_key, "changelog": issue.get("changelog")}
        else:
            issue_key = getattr(issue, "key", "unknown")
            issue_dict = {
                "key": issue_key,
                "changelog": getattr(issue, "changelog", None),
            }

        # Check if issue has changelog
        if not issue_dict["changelog"]:
            exclusion_reasons["missing_changelog"] += 1
            logger.debug(f"[Flow] {issue_key}: Missing changelog data")
            continue

        # Calculate flow time using changelog_processor
        flow_time_result = calculate_flow_time(
            issue_dict,
            start_statuses=start_statuses,
            completion_statuses=completion_statuses,
            active_statuses=active_statuses,
            case_sensitive=case_sensitive,
        )

        # Check if issue never entered flow
        if flow_time_result["start_timestamp"] is None:
            exclusion_reasons["never_entered_start_status"] += 1
            continue

        # Check if issue not yet completed
        if flow_time_result["completion_timestamp"] is None:
            exclusion_reasons["not_yet_completed"] += 1
            continue

        # Collect metrics
        if flow_time_result["total_flow_time_hours"] is not None:
            total_flow_times.append(flow_time_result["total_flow_time_hours"])

        if flow_time_result["active_time_hours"] is not None:
            active_times.append(flow_time_result["active_time_hours"])

        if flow_time_result["flow_efficiency_percent"] is not None:
            flow_efficiencies.append(flow_time_result["flow_efficiency_percent"])

    logger.info(
        f"[Flow] Flow time calculated for {len(total_flow_times)} issues (excluded {sum(exclusion_reasons.values())})"
    )

    # No flow time data
    if len(total_flow_times) == 0:
        logger.warning("[Flow] No flow time data available")
        return {
            "metric_name": "flow_time",
            "total_flow_time": {
                "median_hours": None,
                "mean_hours": None,
                "p75_hours": None,
                "p90_hours": None,
                "p95_hours": None,
                "count": 0,
            },
            "active_time": {
                "median_hours": None,
                "mean_hours": None,
                "p75_hours": None,
                "p90_hours": None,
                "p95_hours": None,
                "count": 0,
            },
            "flow_efficiency": {
                "median_percent": None,
                "mean_percent": None,
                "count": 0,
            },
            "unit": "hours",
            "error_state": "no_data",
            "error_message": "No completed issues with flow time data",
            "excluded_issue_count": sum(exclusion_reasons.values()),
            "total_issue_count": len(issues),
            "exclusion_reasons": exclusion_reasons,
        }

    # Calculate total flow time statistics
    total_flow_time_stats = {
        "median_hours": statistics.median(total_flow_times),
        "mean_hours": statistics.mean(total_flow_times),
        "p75_hours": statistics.quantiles(total_flow_times, n=4)[2]
        if len(total_flow_times) >= 4
        else None,
        "p90_hours": statistics.quantiles(total_flow_times, n=10)[8]
        if len(total_flow_times) >= 10
        else None,
        "p95_hours": statistics.quantiles(total_flow_times, n=20)[18]
        if len(total_flow_times) >= 20
        else None,
        "count": len(total_flow_times),
    }

    # Calculate active time statistics (if available)
    active_time_stats = {
        "median_hours": None,
        "mean_hours": None,
        "p75_hours": None,
        "p90_hours": None,
        "p95_hours": None,
        "count": 0,
    }

    if len(active_times) > 0:
        active_time_stats = {
            "median_hours": statistics.median(active_times),
            "mean_hours": statistics.mean(active_times),
            "p75_hours": statistics.quantiles(active_times, n=4)[2]
            if len(active_times) >= 4
            else None,
            "p90_hours": statistics.quantiles(active_times, n=10)[8]
            if len(active_times) >= 10
            else None,
            "p95_hours": statistics.quantiles(active_times, n=20)[18]
            if len(active_times) >= 20
            else None,
            "count": len(active_times),
        }

    # Calculate flow efficiency statistics (if available)
    flow_efficiency_stats = {"median_percent": None, "mean_percent": None, "count": 0}

    if len(flow_efficiencies) > 0:
        flow_efficiency_stats = {
            "median_percent": statistics.median(flow_efficiencies),
            "mean_percent": statistics.mean(flow_efficiencies),
            "count": len(flow_efficiencies),
        }

    logger.info(
        f"[Flow] Time stats: Median Total={total_flow_time_stats['median_hours']:.1f}h, Active={active_time_stats['median_hours']:.1f}h, Efficiency={flow_efficiency_stats['median_percent']:.1f}%"
        if active_time_stats["median_hours"] and flow_efficiency_stats["median_percent"]
        else f"[Flow] Time stats: Median Total={total_flow_time_stats['median_hours']:.1f}h"
    )

    return {
        "metric_name": "flow_time",
        "total_flow_time": total_flow_time_stats,
        "active_time": active_time_stats,
        "flow_efficiency": flow_efficiency_stats,
        "unit": "hours",
        "error_state": "success",
        "error_message": None,
        "excluded_issue_count": sum(exclusion_reasons.values()),
        "total_issue_count": len(issues),
        "exclusion_reasons": exclusion_reasons,
    }


def calculate_flow_load_v2(
    issues: List[Any],
    wip_statuses: List[str],
    wip_issue_types: Optional[List[str]] = None,
    case_sensitive: bool = False,
) -> Dict[str, Any]:
    """
    Calculate Flow Load v2 (WIP) - Current number of items in active work.

    Uses positive status inclusion mapping (NOT exclusion).
    Counts issues in WIP statuses with resolution = "Unresolved".

    Args:
        issues: List of JIRA issue objects (not dicts)
        wip_statuses: List of WIP status names from config (positive mapping)
                     e.g., ["In Progress", "In Review", "Ready for Testing", "Testing", "In Deployment"]
        wip_issue_types: Optional list of issue types to include (e.g., ["Task", "Story", "Bug"])
                        If None, all issue types are included
        case_sensitive: Whether to match status names case-sensitively (default: False)

    Returns:
        Dictionary with:
        {
            "metric_name": "flow_load",
            "wip_count": 25,
            "by_status": {
                "In Progress": 10,
                "In Review": 5,
                "Ready for Testing": 3,
                "Testing": 4,
                "In Deployment": 3
            },
            "by_issue_type": {
                "Task": 12,
                "Story": 8,
                "Bug": 5
            },
            "unit": "items",
            "error_state": "success",
            "error_message": None,
            "excluded_issue_count": 35,
            "total_issue_count": 60,
            "exclusion_reasons": {
                "not_in_wip_status": 20,
                "resolved": 10,
                "excluded_issue_type": 5
            }
        }

    Example:
        >>> from data.jira_simple import fetch_all_issues
        >>> from configuration.flow_config import FlowConfig
        >>>
        >>> config = FlowConfig()
        >>> issues = fetch_all_issues()
        >>>
        >>> result = calculate_flow_load_v2(
        ...     issues,
        ...     wip_statuses=["In Progress", "In Review", "Ready for Testing", "Testing", "In Deployment"],
        ...     wip_issue_types=["Task", "Story", "Bug"]
        ... )
        >>> print(f"Current WIP: {result['wip_count']} items")
        >>> print(f"In Progress: {result['by_status']['In Progress']}")
    """
    logger.info(f"[Flow] Load v2 (WIP): {len(issues)} issues")

    # Normalize WIP statuses for matching
    wip_statuses_normalized = [s if case_sensitive else s.lower() for s in wip_statuses]

    # Normalize issue types for matching (if provided)
    wip_issue_types_normalized = None
    if wip_issue_types:
        wip_issue_types_normalized = [
            t if case_sensitive else t.lower() for t in wip_issue_types
        ]

    # Exclusion tracking
    exclusion_reasons = {
        "not_in_wip_status": 0,
        "resolved": 0,
        "excluded_issue_type": 0,
    }

    # Count WIP issues
    wip_issues = []
    by_status = {}
    by_issue_type = {}

    for issue in issues:
        # Get status name - handle dict format
        fields = issue.get("fields", {})
        status_obj = fields.get("status", {})
        status_name = status_obj.get("name") if isinstance(status_obj, dict) else None

        if not status_name:
            exclusion_reasons["not_in_wip_status"] += 1
            continue

        # Normalize status for matching
        status_normalized = status_name if case_sensitive else status_name.lower()

        # Check if in WIP statuses (positive inclusion)
        if status_normalized not in wip_statuses_normalized:
            exclusion_reasons["not_in_wip_status"] += 1
            continue

        # Check resolution status
        resolution = fields.get("resolution")
        if resolution and (isinstance(resolution, dict) and resolution.get("name")):
            # Issue is resolved (not in active work)
            exclusion_reasons["resolved"] += 1
            continue

        # Check issue type (if filtering by type)
        issuetype_obj = fields.get("issuetype", {})
        issue_type_name = (
            issuetype_obj.get("name") if isinstance(issuetype_obj, dict) else None
        )

        if wip_issue_types_normalized and issue_type_name:
            issue_type_normalized = (
                issue_type_name if case_sensitive else issue_type_name.lower()
            )
            if issue_type_normalized not in wip_issue_types_normalized:
                exclusion_reasons["excluded_issue_type"] += 1
                continue

        # Issue is in WIP
        wip_issues.append(issue)

        # Count by status
        by_status[status_name] = by_status.get(status_name, 0) + 1

        # Count by issue type
        if issue_type_name:
            by_issue_type[issue_type_name] = by_issue_type.get(issue_type_name, 0) + 1

    wip_count = len(wip_issues)

    logger.info(
        f"[Flow] Load (WIP): {wip_count} items in active work (excluded {sum(exclusion_reasons.values())})"
    )

    if wip_count == 0:
        logger.warning("[Flow] No WIP issues found")
        return {
            "metric_name": "flow_load",
            "wip_count": 0,
            "by_status": {},
            "by_issue_type": {},
            "unit": "items",
            "error_state": "no_data",
            "error_message": "No issues found in WIP statuses",
            "excluded_issue_count": sum(exclusion_reasons.values()),
            "total_issue_count": len(issues),
            "exclusion_reasons": exclusion_reasons,
        }

    logger.info(f"[Flow] WIP by status: {by_status}")
    logger.info(f"[Flow] WIP by issue type: {by_issue_type}")

    return {
        "metric_name": "flow_load",
        "wip_count": wip_count,
        "by_status": by_status,
        "by_issue_type": by_issue_type,
        "unit": "items",
        "error_state": "success",
        "error_message": None,
        "excluded_issue_count": sum(exclusion_reasons.values()),
        "total_issue_count": len(issues),
        "exclusion_reasons": exclusion_reasons,
    }


def calculate_flow_efficiency_v2(
    issues: List[Any],
    start_statuses: List[str],
    completion_statuses: List[str],
    active_statuses: List[str],
    case_sensitive: bool = False,
) -> Dict[str, Any]:
    """
    Calculate Flow Efficiency v2 - Percentage of time actively working vs waiting.

    Flow Efficiency = (Active Time / Total Flow Time) * 100

    - Active Time: Time spent in active statuses (e.g., "In Progress", "In Review", "Testing")
    - Total Flow Time: Time from first "In Progress" to completion (includes waiting)
    - Target: > 40% (industry benchmark)

    Uses changelog_processor for time-in-status calculations.

    Args:
        issues: List of JIRA issue objects (not dicts) with expanded changelog
        start_statuses: Statuses that mark flow start (e.g., ["In Progress"])
        completion_statuses: Statuses that mark completion (e.g., ["Done", "Resolved", "Closed"])
        active_statuses: List of active statuses (e.g., ["In Progress", "In Review", "Testing"])
        case_sensitive: Whether to match status names case-sensitively (default: False)

    Returns:
        Dictionary with:
        {
            "metric_name": "flow_efficiency",
            "median_percent": 42.5,
            "mean_percent": 45.2,
            "p25_percent": 35.0,
            "p75_percent": 55.0,
            "count": 45,
            "target_percent": 40.0,
            "meets_target_count": 28,
            "below_target_count": 17,
            "unit": "percentage",
            "error_state": "success",
            "error_message": None,
            "excluded_issue_count": 15,
            "total_issue_count": 60,
            "exclusion_reasons": {
                "never_entered_start_status": 10,
                "not_yet_completed": 5
            }
        }

    Example:
        >>> from data.jira_simple import fetch_all_issues_with_changelog
        >>> from configuration.flow_config import FlowConfig
        >>>
        >>> config = FlowConfig()
        >>> issues = fetch_all_issues_with_changelog()
        >>>
        >>> result = calculate_flow_efficiency_v2(
        ...     issues,
        ...     start_statuses=["In Progress"],
        ...     completion_statuses=["Done", "Resolved", "Closed"],
        ...     active_statuses=["In Progress", "In Review", "Testing"]
        ... )
        >>> print(f"Median Flow Efficiency: {result['median_percent']:.1f}%")
        >>> print(f"Meets 40% target: {result['meets_target_count']}/{result['count']}")
    """
    from data.changelog_processor import calculate_flow_time
    import statistics

    logger.info(f"[Flow] Efficiency v2: {len(issues)} issues")

    # Exclusion tracking
    exclusion_reasons = {
        "never_entered_start_status": 0,
        "not_yet_completed": 0,
        "missing_changelog": 0,
    }

    # Collect flow efficiency data
    flow_efficiencies = []

    TARGET_EFFICIENCY = 40.0  # Industry benchmark
    meets_target_count = 0
    below_target_count = 0

    for issue in issues:
        # Handle both dict and object formats
        if isinstance(issue, dict):
            issue_key = issue.get("key", "unknown")
            issue_dict = {"key": issue_key, "changelog": issue.get("changelog")}
        else:
            issue_key = getattr(issue, "key", "unknown")
            issue_dict = {
                "key": issue_key,
                "changelog": getattr(issue, "changelog", None),
            }

        # Check if issue has changelog
        if not issue_dict["changelog"]:
            exclusion_reasons["missing_changelog"] += 1
            logger.debug(f"[Flow] {issue_key}: Missing changelog data")
            continue

        # Calculate flow time (includes efficiency)
        flow_time_result = calculate_flow_time(
            issue_dict,
            start_statuses=start_statuses,
            completion_statuses=completion_statuses,
            active_statuses=active_statuses,
            case_sensitive=case_sensitive,
        )

        # Check if issue never entered flow
        if flow_time_result["start_timestamp"] is None:
            exclusion_reasons["never_entered_start_status"] += 1
            continue

        # Check if issue not yet completed
        if flow_time_result["completion_timestamp"] is None:
            exclusion_reasons["not_yet_completed"] += 1
            continue

        # Collect flow efficiency
        if flow_time_result["flow_efficiency_percent"] is not None:
            efficiency = flow_time_result["flow_efficiency_percent"]
            flow_efficiencies.append(efficiency)

            # Track against target
            if efficiency >= TARGET_EFFICIENCY:
                meets_target_count += 1
            else:
                below_target_count += 1

    logger.info(
        f"[Flow] Efficiency calculated for {len(flow_efficiencies)} issues (excluded {sum(exclusion_reasons.values())})"
    )

    # No flow efficiency data
    if len(flow_efficiencies) == 0:
        logger.warning("[Flow] No efficiency data available")
        return {
            "metric_name": "flow_efficiency",
            "median_percent": None,
            "mean_percent": None,
            "p25_percent": None,
            "p75_percent": None,
            "count": 0,
            "target_percent": TARGET_EFFICIENCY,
            "meets_target_count": 0,
            "below_target_count": 0,
            "unit": "percentage",
            "error_state": "no_data",
            "error_message": "No completed issues with flow efficiency data",
            "excluded_issue_count": sum(exclusion_reasons.values()),
            "total_issue_count": len(issues),
            "exclusion_reasons": exclusion_reasons,
        }

    # Calculate statistics
    median_efficiency = statistics.median(flow_efficiencies)
    mean_efficiency = statistics.mean(flow_efficiencies)
    p25_efficiency = (
        statistics.quantiles(flow_efficiencies, n=4)[0]
        if len(flow_efficiencies) >= 4
        else None
    )
    p75_efficiency = (
        statistics.quantiles(flow_efficiencies, n=4)[2]
        if len(flow_efficiencies) >= 4
        else None
    )

    logger.info(
        f"[Flow] Efficiency: Median={median_efficiency:.1f}%, Mean={mean_efficiency:.1f}%, Target={TARGET_EFFICIENCY}% (Meets: {meets_target_count}, Below: {below_target_count})"
    )

    return {
        "metric_name": "flow_efficiency",
        "median_percent": median_efficiency,
        "mean_percent": mean_efficiency,
        "p25_percent": p25_efficiency,
        "p75_percent": p75_efficiency,
        "count": len(flow_efficiencies),
        "target_percent": TARGET_EFFICIENCY,
        "meets_target_count": meets_target_count,
        "below_target_count": below_target_count,
        "unit": "percentage",
        "error_state": "success",
        "error_message": None,
        "excluded_issue_count": sum(exclusion_reasons.values()),
        "total_issue_count": len(issues),
        "exclusion_reasons": exclusion_reasons,
    }


def calculate_flow_distribution_v2(
    issues: List[Any],
    completion_statuses: List[str],
    start_date: datetime,
    end_date: datetime,
    effort_category_field: str = "customfield_10003",
    recommended_ranges: Optional[Dict[str, tuple]] = None,
) -> Dict[str, Any]:
    """
    Calculate Flow Distribution v2 - Percentage of work by Flow type.

    Uses same classification as Flow Velocity (two-tier classification).
    Compares actual distribution against recommended ranges.

    Recommended ranges (from Flow Framework):
    - Feature: 40-60%
    - Defect: 10-20%
    - Technical Debt: 10-20%
    - Risk: 10-20%

    Args:
        issues: List of JIRA issue objects (not dicts)
        completion_statuses: List of completion status names from config
        start_date: Start of measurement period (timezone-aware)
        end_date: End of measurement period (timezone-aware)
        effort_category_field: Custom field ID for effort category (default: customfield_10003)
        recommended_ranges: Optional dict of (min_percent, max_percent) tuples per flow type

    Returns:
        Dictionary with:
        {
            "metric_name": "flow_distribution",
            "total_count": 70,
            "distribution": {
                "Feature": {
                    "count": 45,
                    "percent": 64.3,
                    "recommended_min": 40.0,
                    "recommended_max": 60.0,
                    "in_range": False
                },
                "Defect": {
                    "count": 12,
                    "percent": 17.1,
                    "recommended_min": 10.0,
                    "recommended_max": 20.0,
                    "in_range": True
                },
                "Technical Debt": {
                    "count": 8,
                    "percent": 11.4,
                    "recommended_min": 10.0,
                    "recommended_max": 20.0,
                    "in_range": True
                },
                "Risk": {
                    "count": 5,
                    "percent": 7.1,
                    "recommended_min": 10.0,
                    "recommended_max": 20.0,
                    "in_range": False
                }
            },
            "unit": "percentage",
            "error_state": "success",
            "error_message": None,
            "excluded_issue_count": 15,
            "total_issue_count": 85,
            "exclusion_reasons": {
                "not_in_completion_status": 10,
                "outside_date_range": 5
            }
        }

    Example:
        >>> from datetime import datetime, timezone
        >>> from data.jira_simple import fetch_all_issues
        >>>
        >>> issues = fetch_all_issues()
        >>> start = datetime(2025, 10, 1, tzinfo=timezone.utc)
        >>> end = datetime(2025, 10, 31, 23, 59, 59, tzinfo=timezone.utc)
        >>>
        >>> result = calculate_flow_distribution_v2(
        ...     issues,
        ...     completion_statuses=["Done", "Resolved", "Closed"],
        ...     start_date=start,
        ...     end_date=end
        ... )
        >>> print(f"Feature work: {result['distribution']['Feature']['percent']:.1f}%")
        >>> print(f"In recommended range: {result['distribution']['Feature']['in_range']}")
    """
    from data.flow_type_classifier import (
        get_flow_distribution,
        FLOW_TYPE_FEATURE,
        FLOW_TYPE_DEFECT,
        FLOW_TYPE_TECHNICAL_DEBT,
        FLOW_TYPE_RISK,
    )

    logger.info(
        f"[Flow] Distribution v2: {len(issues)} issues between {start_date.date()} and {end_date.date()}"
    )

    # Default recommended ranges (from Flow Framework)
    if recommended_ranges is None:
        recommended_ranges = {
            FLOW_TYPE_FEATURE: (40.0, 60.0),
            FLOW_TYPE_DEFECT: (10.0, 20.0),
            FLOW_TYPE_TECHNICAL_DEBT: (10.0, 20.0),
            FLOW_TYPE_RISK: (10.0, 20.0),
        }

    # Exclusion tracking
    exclusion_reasons = {
        "not_in_completion_status": 0,
        "outside_date_range": 0,
        "missing_completion_date": 0,
    }

    # Filter to completed issues in date range (same logic as Flow Velocity)
    completed_issues = []

    for issue in issues:
        # Check completion status (case-insensitive) - handle dict format
        fields = issue.get("fields", {})
        status_obj = fields.get("status", {})
        status_name = status_obj.get("name") if isinstance(status_obj, dict) else None
        issue_key = issue.get("key", "unknown")

        if not status_name:
            exclusion_reasons["not_in_completion_status"] += 1
            continue

        status_matched = any(
            status_name.lower() == cs.lower() for cs in completion_statuses
        )

        if not status_matched:
            exclusion_reasons["not_in_completion_status"] += 1
            continue

        # Get completion date
        completion_date_str = fields.get("resolutiondate")
        if not completion_date_str:
            exclusion_reasons["missing_completion_date"] += 1
            continue

        # Parse completion date
        try:
            completion_date = datetime.fromisoformat(
                completion_date_str.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            exclusion_reasons["missing_completion_date"] += 1
            logger.warning(
                f"[Flow] {issue_key}: Invalid resolutiondate: {completion_date_str}"
            )
            continue

        # Check if in date range
        if not (start_date <= completion_date <= end_date):
            exclusion_reasons["outside_date_range"] += 1
            continue

        completed_issues.append(issue)

    logger.info(f"[Flow] {len(completed_issues)} completed issues in period")

    # No completed issues
    if len(completed_issues) == 0:
        logger.warning("[Flow] No completed issues for distribution")
        return {
            "metric_name": "flow_distribution",
            "total_count": 0,
            "distribution": {
                FLOW_TYPE_FEATURE: {
                    "count": 0,
                    "percent": 0.0,
                    "recommended_min": recommended_ranges[FLOW_TYPE_FEATURE][0],
                    "recommended_max": recommended_ranges[FLOW_TYPE_FEATURE][1],
                    "in_range": False,
                },
                FLOW_TYPE_DEFECT: {
                    "count": 0,
                    "percent": 0.0,
                    "recommended_min": recommended_ranges[FLOW_TYPE_DEFECT][0],
                    "recommended_max": recommended_ranges[FLOW_TYPE_DEFECT][1],
                    "in_range": False,
                },
                FLOW_TYPE_TECHNICAL_DEBT: {
                    "count": 0,
                    "percent": 0.0,
                    "recommended_min": recommended_ranges[FLOW_TYPE_TECHNICAL_DEBT][0],
                    "recommended_max": recommended_ranges[FLOW_TYPE_TECHNICAL_DEBT][1],
                    "in_range": False,
                },
                FLOW_TYPE_RISK: {
                    "count": 0,
                    "percent": 0.0,
                    "recommended_min": recommended_ranges[FLOW_TYPE_RISK][0],
                    "recommended_max": recommended_ranges[FLOW_TYPE_RISK][1],
                    "in_range": False,
                },
            },
            "unit": "percentage",
            "error_state": "no_data",
            "error_message": "No completed issues in date range",
            "excluded_issue_count": sum(exclusion_reasons.values()),
            "total_issue_count": len(issues),
            "exclusion_reasons": exclusion_reasons,
        }

    # Calculate distribution using flow_type_classifier
    distribution_percentages = get_flow_distribution(
        completed_issues, effort_category_field
    )

    # Get counts (calculate from percentages and total)
    total_count = len(completed_issues)
    from data.flow_type_classifier import count_by_flow_type

    flow_type_counts = count_by_flow_type(completed_issues, effort_category_field)

    # Build distribution with range checking
    distribution = {}
    for flow_type in [
        FLOW_TYPE_FEATURE,
        FLOW_TYPE_DEFECT,
        FLOW_TYPE_TECHNICAL_DEBT,
        FLOW_TYPE_RISK,
    ]:
        percent = distribution_percentages[flow_type]
        count = flow_type_counts[flow_type]
        min_range, max_range = recommended_ranges.get(flow_type, (0.0, 100.0))

        in_range = min_range <= percent <= max_range

        distribution[flow_type] = {
            "count": count,
            "percent": percent,
            "recommended_min": min_range,
            "recommended_max": max_range,
            "in_range": in_range,
        }

    logger.info(
        f"[Flow] Distribution: Feature={distribution[FLOW_TYPE_FEATURE]['percent']:.1f}% ({distribution[FLOW_TYPE_FEATURE]['in_range']}), Defect={distribution[FLOW_TYPE_DEFECT]['percent']:.1f}% ({distribution[FLOW_TYPE_DEFECT]['in_range']}), Tech Debt={distribution[FLOW_TYPE_TECHNICAL_DEBT]['percent']:.1f}% ({distribution[FLOW_TYPE_TECHNICAL_DEBT]['in_range']}), Risk={distribution[FLOW_TYPE_RISK]['percent']:.1f}% ({distribution[FLOW_TYPE_RISK]['in_range']})"
    )

    return {
        "metric_name": "flow_distribution",
        "total_count": total_count,
        "distribution": distribution,
        "unit": "percentage",
        "error_state": "success",
        "error_message": None,
        "excluded_issue_count": sum(exclusion_reasons.values()),
        "total_issue_count": len(issues),
        "exclusion_reasons": exclusion_reasons,
    }


# ==============================================================================
# Weekly Aggregation Functions
# ==============================================================================


def aggregate_flow_velocity_weekly(
    issues: List,
    completion_statuses: List[str],
    effort_category_field: str,
    week_labels: List[str],
    case_sensitive: bool = False,
) -> Dict[str, Dict]:
    """
    Aggregate Flow Velocity by ISO week (sum aggregation).

    Counts number of completed items per week by Flow type.

    Args:
        issues: List of issue objects
        completion_statuses: List of completion status names
        effort_category_field: Custom field ID for effort category
        week_labels: List of year-week labels to aggregate
        case_sensitive: Whether to match status names case-sensitively

    Returns:
        Dictionary mapping week labels to Flow type counts

    Example:
        >>> aggregate_flow_velocity_weekly(issues, ["Done"], "customfield_10003", ["2025-43"])
        {
            "2025-43": {
                "total": 25,
                "Feature": 15,
                "Defect": 6,
                "Technical Debt": 3,
                "Risk": 1
            }
        }
    """
    from data.time_period_calculator import get_year_week_label
    from data.flow_type_classifier import count_by_flow_type
    from datetime import datetime
    from collections import defaultdict

    logger.info(f"[Flow] Aggregating velocity for {len(week_labels)} weeks")

    # Initialize result
    weekly_counts = {
        label: {"total": 0, "Feature": 0, "Defect": 0, "Technical Debt": 0, "Risk": 0}
        for label in week_labels
    }

    if not issues or not completion_statuses:
        logger.warning("[Flow] Velocity aggregation: No issues or completion statuses")
        return weekly_counts

    # Convert statuses for case-insensitive matching
    completion_statuses_lower = (
        [s.lower() for s in completion_statuses] if not case_sensitive else []
    )

    # Group issues by week
    week_groups = defaultdict(list)

    for issue in issues:
        try:
            # Check completion status (dict format)
            issue_status = issue.get("fields", {}).get("status")
            if not issue_status:
                continue

            issue_status_name = (
                issue_status.get("name", "")
                if isinstance(issue_status, dict)
                else issue_status.name
            )
            status_match = (
                issue_status_name in completion_statuses
                if case_sensitive
                else issue_status_name.lower() in completion_statuses_lower
            )

            if not status_match:
                continue

            # Get completion date (resolutiondate) - dict format
            resolution_date_str = issue.get("fields", {}).get("resolutiondate")
            if not resolution_date_str:
                continue

            resolution_dt = datetime.fromisoformat(
                resolution_date_str.replace("Z", "+00:00")
            )
            week_label = get_year_week_label(resolution_dt)

            if week_label in weekly_counts:
                week_groups[week_label].append(issue)

        except (AttributeError, ValueError, KeyError):
            continue

    # Count by Flow type for each week
    for week_label in week_labels:
        week_issues = week_groups.get(week_label, [])
        if not week_issues:
            continue

        flow_counts = count_by_flow_type(week_issues, effort_category_field)

        weekly_counts[week_label]["Feature"] = flow_counts.get("Feature", 0)
        weekly_counts[week_label]["Defect"] = flow_counts.get("Defect", 0)
        weekly_counts[week_label]["Technical Debt"] = flow_counts.get(
            "Technical Debt", 0
        )
        weekly_counts[week_label]["Risk"] = flow_counts.get("Risk", 0)
        weekly_counts[week_label]["total"] = sum(flow_counts.values())

    logger.info(
        f"[Flow] Weekly velocity aggregated for {sum(1 for c in weekly_counts.values() if c['total'] > 0)} weeks"
    )
    return weekly_counts


def aggregate_flow_time_weekly(
    flow_times: List[Dict], week_labels: List[str]
) -> Dict[str, Dict]:
    """
    Aggregate Flow Time by ISO week using median.

    Groups flow times by week and calculates median, mean, and percentiles
    for both total flow time and active time.

    Args:
        flow_times: List of flow time dictionaries from calculate_flow_time_v2
        week_labels: List of year-week labels to aggregate

    Returns:
        Dictionary mapping week labels to statistics

    Example:
        >>> aggregate_flow_time_weekly(flow_times, ["2025-43", "2025-44"])
        {
            "2025-43": {
                "median_total_hours": 72.5,
                "median_active_hours": 42.1,
                "median_efficiency_percent": 58.1,
                "count": 15
            }
        }
    """
    from data.time_period_calculator import get_year_week_label
    from datetime import datetime
    import statistics
    from collections import defaultdict

    logger.info(f"[Flow] Aggregating flow time for {len(week_labels)} weeks")

    # Initialize result
    weekly_stats = {
        label: {
            "median_total_hours": None,
            "mean_total_hours": None,
            "median_active_hours": None,
            "mean_active_hours": None,
            "median_efficiency_percent": None,
            "mean_efficiency_percent": None,
            "count": 0,
        }
        for label in week_labels
    }

    if not flow_times:
        logger.warning("[Flow] Time aggregation: No flow times provided")
        return weekly_stats

    # Group by week (use completion date)
    week_groups = defaultdict(lambda: {"total": [], "active": [], "efficiency": []})

    for ft in flow_times:
        completion_date_str = ft.get("completion_date")
        if not completion_date_str:
            continue

        try:
            completion_dt = datetime.fromisoformat(
                completion_date_str.replace("Z", "+00:00")
            )
            week_label = get_year_week_label(completion_dt)

            if week_label in weekly_stats:
                week_groups[week_label]["total"].append(ft["total_flow_time_hours"])
                week_groups[week_label]["active"].append(ft["active_time_hours"])
                week_groups[week_label]["efficiency"].append(
                    ft["flow_efficiency_percent"]
                )
        except (ValueError, KeyError):
            continue

    # Calculate statistics for each week
    for week_label in week_labels:
        group = week_groups.get(week_label)
        if not group or not group["total"]:
            continue

        total_list = group["total"]
        active_list = group["active"]
        efficiency_list = group["efficiency"]

        weekly_stats[week_label]["count"] = len(total_list)

        # Total flow time statistics
        weekly_stats[week_label]["median_total_hours"] = round(
            statistics.median(total_list), 2
        )
        weekly_stats[week_label]["mean_total_hours"] = round(
            statistics.mean(total_list), 2
        )

        # Active time statistics
        weekly_stats[week_label]["median_active_hours"] = round(
            statistics.median(active_list), 2
        )
        weekly_stats[week_label]["mean_active_hours"] = round(
            statistics.mean(active_list), 2
        )

        # Flow efficiency statistics
        weekly_stats[week_label]["median_efficiency_percent"] = round(
            statistics.median(efficiency_list), 1
        )
        weekly_stats[week_label]["mean_efficiency_percent"] = round(
            statistics.mean(efficiency_list), 1
        )

    logger.info(
        f"[Flow] Weekly flow time aggregated for {sum(1 for s in weekly_stats.values() if s['count'] > 0)} weeks"
    )
    return weekly_stats


def aggregate_flow_distribution_weekly(
    issues: List,
    completion_statuses: List[str],
    effort_category_field: str,
    week_labels: List[str],
    case_sensitive: bool = False,
) -> Dict[str, Dict]:
    """
    Aggregate Flow Distribution by ISO week (percentage).

    Calculates percentage of work by Flow type per week.

    Args:
        issues: List of issue objects
        completion_statuses: List of completion status names
        effort_category_field: Custom field ID for effort category
        week_labels: List of year-week labels to aggregate
        case_sensitive: Whether to match status names case-sensitively

    Returns:
        Dictionary mapping week labels to Flow type percentages

    Example:
        >>> aggregate_flow_distribution_weekly(issues, ["Done"], "customfield_10003", ["2025-43"])
        {
            "2025-43": {
                "total_count": 25,
                "Feature": 60.0,
                "Defect": 24.0,
                "Technical Debt": 12.0,
                "Risk": 4.0
            }
        }
    """
    from data.time_period_calculator import get_year_week_label
    from data.flow_type_classifier import get_flow_distribution
    from datetime import datetime
    from collections import defaultdict

    logger.info(f"[Flow] Aggregating distribution for {len(week_labels)} weeks")

    # Initialize result
    weekly_distribution = {
        label: {
            "total_count": 0,
            "Feature": 0.0,
            "Defect": 0.0,
            "Technical Debt": 0.0,
            "Risk": 0.0,
        }
        for label in week_labels
    }

    if not issues or not completion_statuses:
        logger.warning(
            "[Flow] Distribution aggregation: No issues or completion statuses"
        )
        return weekly_distribution

    # Convert statuses for case-insensitive matching
    completion_statuses_lower = (
        [s.lower() for s in completion_statuses] if not case_sensitive else []
    )

    # Group issues by week
    week_groups = defaultdict(list)

    for issue in issues:
        try:
            # Check completion status (dict format)
            issue_status = issue.get("fields", {}).get("status")
            if not issue_status:
                continue

            issue_status_name = (
                issue_status.get("name", "")
                if isinstance(issue_status, dict)
                else issue_status.name
            )
            status_match = (
                issue_status_name in completion_statuses
                if case_sensitive
                else issue_status_name.lower() in completion_statuses_lower
            )

            if not status_match:
                continue

            # Get completion date (resolutiondate) - dict format
            resolution_date_str = issue.get("fields", {}).get("resolutiondate")
            if not resolution_date_str:
                continue

            resolution_dt = datetime.fromisoformat(
                resolution_date_str.replace("Z", "+00:00")
            )
            week_label = get_year_week_label(resolution_dt)

            if week_label in weekly_distribution:
                week_groups[week_label].append(issue)

        except (AttributeError, ValueError, KeyError):
            continue

    # Calculate distribution for each week
    for week_label in week_labels:
        week_issues = week_groups.get(week_label, [])
        if not week_issues:
            continue

        distribution = get_flow_distribution(week_issues, effort_category_field)

        weekly_distribution[week_label]["total_count"] = len(week_issues)
        weekly_distribution[week_label]["Feature"] = distribution.get("Feature", 0.0)
        weekly_distribution[week_label]["Defect"] = distribution.get("Defect", 0.0)
        weekly_distribution[week_label]["Technical Debt"] = distribution.get(
            "Technical Debt", 0.0
        )
        weekly_distribution[week_label]["Risk"] = distribution.get("Risk", 0.0)

    logger.info(
        f"[Flow] Weekly distribution aggregated for {sum(1 for d in weekly_distribution.values() if d['total_count'] > 0)} weeks"
    )
    return weekly_distribution


def calculate_wip_thresholds_from_history(
    velocity_snapshots: List[Dict[str, Any]],
    flow_time_snapshots: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Calculate WIP thresholds using Little's Law and historical percentiles.

    Little's Law: L = λ × W
    - L (WIP) = Average work in progress
    - λ (Throughput) = Items completed per time period (Flow Velocity)
    - W (Cycle Time) = Average time to complete item (Flow Time)

    Methodology:
    1. For each historical week, calculate optimal WIP = velocity × (flow_time_days / 7)
    2. Compute percentiles from distribution (P25, P50, P75, P90)
    3. Add 20% buffer to P25, P50, P75 for stability zones
    4. Use P90 as critical threshold (no buffer - danger zone)

    Args:
        velocity_snapshots: List of weekly Flow Velocity data with 'completed_count'
        flow_time_snapshots: List of weekly Flow Time data with 'median_days'

    Returns:
        Dictionary with threshold values:
        {
            "healthy": float,     # P25 + 20% buffer (green)
            "warning": float,     # P50 + 20% buffer (yellow)
            "high": float,        # P75 + 20% buffer (orange)
            "critical": float,    # P90 (red - danger zone)
            "method": "Little's Law (percentile-based)"
        }

    Example:
        Week 1: velocity=20, flow_time=5d → optimal_wip = 20 × (5/7) ≈ 14
        Week 2: velocity=18, flow_time=6d → optimal_wip = 18 × (6/7) ≈ 15
        ...
        P25=12, P50=15, P75=18, P90=22
        → healthy=14, warning=18, high=22, critical=22
    """
    try:
        import numpy as np
    except ImportError:
        logger.warning("[Flow] NumPy not available, using hardcoded WIP thresholds")
        return {
            "healthy": 10,
            "warning": 20,
            "high": 30,
            "critical": 40,
            "method": "hardcoded (fallback)",
        }

    # Calculate optimal WIP for each week using Little's Law
    optimal_wips = []

    for vel_snapshot, time_snapshot in zip(velocity_snapshots, flow_time_snapshots):
        velocity = vel_snapshot.get("completed_count", 0)
        flow_time_days = time_snapshot.get("median_days", 0)

        if velocity > 0 and flow_time_days > 0:
            # Little's Law: WIP = Throughput × Cycle Time
            cycle_time_weeks = flow_time_days / 7.0
            optimal_wip = velocity * cycle_time_weeks
            optimal_wips.append(optimal_wip)

    if len(optimal_wips) < 4:
        # Need at least 4 data points for meaningful percentiles
        logger.warning(
            f"[Flow] Insufficient WIP data ({len(optimal_wips)} weeks), using hardcoded thresholds"
        )
        return {
            "healthy": 10,
            "warning": 20,
            "high": 30,
            "critical": 40,
            "method": "hardcoded (insufficient data)",
        }

    # Calculate percentile-based thresholds
    p25 = float(np.percentile(optimal_wips, 25))
    p50 = float(np.percentile(optimal_wips, 50))  # Median
    p75 = float(np.percentile(optimal_wips, 75))
    p90 = float(np.percentile(optimal_wips, 90))

    # Apply 20% buffer to lower thresholds for stability zones
    # Critical threshold has no buffer - it's the danger zone
    thresholds = {
        "healthy": round(p25 * 1.2, 1),  # Green zone: below 25th percentile + buffer
        "warning": round(p50 * 1.2, 1),  # Yellow zone: below median + buffer
        "high": round(p75 * 1.2, 1),  # Orange zone: below 75th percentile + buffer
        "critical": round(p90, 1),  # Red zone: at/above 90th percentile
        "method": "Little's Law (percentile-based)",
        "data_points": len(optimal_wips),
        "p25": round(p25, 1),
        "p50": round(p50, 1),
        "p75": round(p75, 1),
        "p90": round(p90, 1),
    }

    logger.info(
        f"[Flow] WIP thresholds from {len(optimal_wips)} weeks: Healthy<{thresholds['healthy']}, Warning<{thresholds['warning']}, High<{thresholds['high']}, Critical≥{thresholds['critical']}"
    )

    return thresholds
