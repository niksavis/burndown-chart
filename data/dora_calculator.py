"""DORA metrics calculator.

Calculates the four DORA metrics from Jira issue data:
- Deployment Frequency
- Lead Time for Changes
- Change Failure Rate
- Mean Time to Recovery

This module contains pure business logic with no UI dependencies.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import logging
import re

from data.project_filter import filter_deployment_issues, filter_incident_issues

logger = logging.getLogger(__name__)


def _extract_date_from_fixversions(fix_versions) -> Optional[str]:
    """Extract deployment date from Jira fixVersions field.

    The fixVersions field in Jira contains version objects with deployment information.
    This function extracts dates using the following priority:
    1. Use explicit 'releaseDate' if present and not empty
    2. Parse YYYYMMDD pattern from version name (e.g., "R_20251027_prod" → "20251027")
    3. Return None if no date found

    Args:
        fix_versions: fixVersions field value - can be:
                     - List of version dicts: [{"name": "R_20251027_prod", "releaseDate": "2025-10-27", ...}]
                     - Single version dict: {"name": "Release_20251112", "releaseDate": "", ...}
                     - None or empty

    Returns:
        ISO format date string (YYYY-MM-DD) or None if no valid date found

    Examples:
        >>> _extract_date_from_fixversions([{"name": "R_20251027_prod", "releaseDate": "2025-10-27"}])
        "2025-10-27"
        >>> _extract_date_from_fixversions([{"name": "Release_20251112", "releaseDate": ""}])
        "2025-11-12"
        >>> _extract_date_from_fixversions([{"name": "Release_v2.0"}])
        None
    """
    if not fix_versions:
        return None

    # Normalize to list if single dict
    if isinstance(fix_versions, dict):
        fix_versions = [fix_versions]

    if not isinstance(fix_versions, list):
        logger.warning(f"fixVersions field has unexpected type: {type(fix_versions)}")
        return None

    # Iterate through versions (most recent usually first)
    for version in fix_versions:
        if not isinstance(version, dict):
            continue

        # Priority 1: Use explicit releaseDate if present
        release_date = version.get("releaseDate", "")
        if release_date and release_date.strip():
            return release_date.strip()

        # Priority 2: Parse YYYYMMDD from version name
        version_name = version.get("name", "")
        if version_name:
            # Match 8-digit date pattern (YYYYMMDD)
            date_match = re.search(r"(\d{8})", version_name)
            if date_match:
                date_str = date_match.group(1)
                # Convert YYYYMMDD to YYYY-MM-DD
                try:
                    year = date_str[0:4]
                    month = date_str[4:6]
                    day = date_str[6:8]
                    return f"{year}-{month}-{day}"
                except (IndexError, ValueError) as e:
                    logger.warning(
                        f"Failed to parse date from version name '{version_name}': {e}"
                    )
                    continue

    return None


def _calculate_trend(
    current_value: Optional[float], previous_value: Optional[float]
) -> Dict[str, Any]:
    """Calculate trend direction and percentage change.

    Args:
        current_value: Current period metric value
        previous_value: Previous period metric value

    Returns:
        Dictionary with trend_direction ('up'/'down'/'stable') and trend_percentage
    """
    if current_value is None or previous_value is None or previous_value == 0:
        return {"trend_direction": "stable", "trend_percentage": 0.0}

    percentage_change = ((current_value - previous_value) / previous_value) * 100

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


# DORA Performance Tier Benchmarks (from dora_config.py)
DEPLOYMENT_FREQUENCY_TIERS = {
    "Elite": {
        "min": 999999,
        "unit": "per_day",
        "color": "green",
    },  # On-demand (multiple per day)
    "High": {"min": 1, "max": 999999, "unit": "per_week", "color": "yellow"},  # Weekly
    "Medium": {
        "min": 1,
        "max": 999999,
        "unit": "per_month",
        "color": "orange",
    },  # Monthly
    "Low": {
        "min": 0,
        "max": 1,
        "unit": "per_month",
        "color": "red",
    },  # Less than monthly
}

LEAD_TIME_TIERS = {
    "Elite": {"max": 1, "unit": "days", "color": "green"},  # Less than one day
    "High": {
        "min": 1,
        "max": 7,
        "unit": "days",
        "color": "yellow",
    },  # One day to one week
    "Medium": {
        "min": 7,
        "max": 30,
        "unit": "days",
        "color": "orange",
    },  # One week to one month
    "Low": {"min": 30, "unit": "days", "color": "red"},  # More than one month
}

CHANGE_FAILURE_RATE_TIERS = {
    "Elite": {"max": 15, "unit": "percentage", "color": "green"},  # 0-15%
    "High": {"min": 15, "max": 30, "unit": "percentage", "color": "yellow"},  # 15-30%
    "Medium": {"min": 30, "max": 45, "unit": "percentage", "color": "orange"},  # 30-45%
    "Low": {"min": 45, "unit": "percentage", "color": "red"},  # >45%
}

MTTR_TIERS = {
    "Elite": {"max": 1, "unit": "hours", "color": "green"},  # Less than one hour
    "High": {
        "min": 1,
        "max": 24,
        "unit": "hours",
        "color": "yellow",
    },  # One hour to one day
    "Medium": {
        "min": 24,
        "max": 168,
        "unit": "hours",
        "color": "orange",
    },  # One day to one week
    "Low": {"min": 168, "unit": "hours", "color": "red"},  # More than one week
}


def _get_date_field_value(fields: Dict[str, Any], field_id: str) -> Optional[str]:
    """Extract date value from Jira field, handling special field types.

    This function intelligently extracts date values from different Jira field types:
    - Regular datetime fields: Returns value directly
    - fixVersions: Extracts date from version array using _extract_date_from_fixversions
    - Other fields: Returns value as-is

    Args:
        fields: Issue fields dictionary from Jira API
        field_id: Jira field ID to extract (e.g., "fixVersions", "created", "customfield_12345")

    Returns:
        ISO format date string or None if extraction fails
    """
    if field_id == "fixVersions":
        # Special handling for fixVersions array field
        fix_versions = fields.get("fixVersions")
        return _extract_date_from_fixversions(fix_versions)
    else:
        # Regular field - return value directly
        return fields.get(field_id)


def _check_deployment_failed(fields: Dict[str, Any], change_failure_field: str) -> bool:
    """Check if deployment caused a failure/incident in production.

    This function handles different field types for change failure indicators:
    - Select list fields: Checks if value is "Yes" (indicating failure)
    - Boolean fields: Returns True if field is True
    - String fields: Checks if value indicates failure
    - None/missing: Returns False (no failure reported)

    Args:
        fields: Issue fields dictionary from Jira API
        change_failure_field: Jira field ID to check (e.g., "customfield_10001")

    Returns:
        True if deployment caused a failure, False otherwise
    """
    field_value = fields.get(change_failure_field)

    if not field_value:
        return False  # No value = no failure reported

    # Handle select list field (dict with value)
    if isinstance(field_value, dict):
        option_value = field_value.get("value", "")
        if option_value:
            return option_value.lower() in ["yes", "true", "failed", "failure"]

    # Handle boolean field
    if isinstance(field_value, bool):
        return field_value

    # Handle string field
    if isinstance(field_value, str):
        return field_value.lower() in ["yes", "true", "failed", "failure"]

    return False


def _check_deployment_successful(
    fields: Dict[str, Any], deployment_successful_field: str
) -> bool:
    """DEPRECATED: Use _check_deployment_failed instead.

    Check if deployment was successful based on field value.

    This function handles different field types for deployment success indicators:
    - Multi-checkbox fields (like Deployment Approval): Checks if array contains 'Approved' option
    - Boolean fields: Returns value directly
    - String fields: Checks if value indicates success
    - None/missing: Returns False (deployment status unknown)

    Args:
        fields: Issue fields dictionary from Jira API
        deployment_successful_field: Jira field ID to check (e.g., "customfield_10004")

    Returns:
        True if deployment was successful, False otherwise
    """
    field_value = fields.get(deployment_successful_field)

    if not field_value:
        return False

    # Handle multi-checkbox field (array of option objects)
    if isinstance(field_value, list):
        for option in field_value:
            if isinstance(option, dict):
                # Check if option value is 'Approved' or similar
                option_value = option.get("value", "")
                if option_value and "approve" in option_value.lower():
                    return True
            elif isinstance(option, str):
                # Handle simple string array
                if "approve" in option.lower():
                    return True
        return False

    # Handle boolean field
    if isinstance(field_value, bool):
        return field_value

    # Handle string field
    if isinstance(field_value, str):
        return field_value.lower() in [
            "approved",
            "success",
            "successful",
            "true",
            "yes",
        ]

    return False


def _parse_datetime(date_string: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string to timezone-aware datetime object.

    Args:
        date_string: ISO format datetime string

    Returns:
        Parsed timezone-aware datetime object or None if parsing fails
    """
    if not date_string:
        return None

    try:
        # Handle Jira datetime format (ISO 8601) - replace 'Z' with explicit +00:00
        dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))

        # Ensure datetime is timezone-aware (assume UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse datetime '{date_string}': {e}")
        return None


def _determine_performance_tier(
    value: float, tier_config: Dict[str, Any]
) -> Dict[str, str]:
    """Determine performance tier based on metric value and tier configuration.

    Args:
        value: Calculated metric value
        tier_config: Tier configuration with min/max thresholds

    Returns:
        Dict with tier name and color
    """
    for tier_name, tier_spec in tier_config.items():
        min_val = tier_spec.get("min", 0)
        max_val = tier_spec.get("max", float("inf"))

        if min_val <= value < max_val:
            return {"tier": tier_name, "color": tier_spec["color"]}

    # Default to Low tier if no match
    return {"tier": "Low", "color": "red"}


def calculate_deployment_frequency(
    issues: List[Dict[str, Any]],
    field_mappings: Dict[str, str],
    time_period_days: int = 30,
    previous_period_value: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    devops_projects: Optional[List[str]] = None,
    development_projects: Optional[List[str]] = None,
    devops_task_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Calculate deployment frequency metric.

    Args:
        issues: List of all issue dictionaries from Jira (mixed dev + devops)
        field_mappings: Mapping of internal fields to Jira field IDs
        time_period_days: Time period for calculation (default 30 days)
        previous_period_value: Previous period's metric value for trend calculation
        start_date: Optional explicit start date (overrides time_period_days calculation)
        end_date: Optional explicit end date (overrides time_period_days calculation)
        devops_projects: List of DevOps project keys (e.g., ["OPS"]) for filtering deployment issues
        development_projects: List of Development project keys (e.g., ["DEV"]) for fixVersion filtering
        devops_task_types: List of issue type names for DevOps tasks (backward compatible)

    Returns:
        Metric data dictionary with value, unit, performance tier, trend data, and metadata
    """
    # Import filtering functions
    from data.project_filter import (
        filter_development_issues,
        extract_all_fixversions,
        filter_operational_tasks,
    )

    # Filter to deployment issues only (Operational Tasks in DevOps projects linked to development work)
    if devops_projects is None:
        devops_projects = []

    # Extract fixVersions from development issues for filtering
    development_fixversions = None
    if development_projects:
        development_issues = filter_development_issues(issues, devops_projects)
        development_fixversions = extract_all_fixversions(development_issues)
        logger.info(
            f"Extracted {len(development_fixversions)} unique fixVersions from development issues"
        )

    # Filter Operational Tasks to only those linked to development work via fixVersion
    deployment_issues = filter_operational_tasks(
        issues,
        operational_projects=devops_projects,
        development_fixversions=development_fixversions,
        devops_task_types=devops_task_types,
    )

    # Check for required field mapping
    if "deployment_date" not in field_mappings:
        return {
            "metric_name": "deployment_frequency",
            "value": None,
            "unit": "deployments/month",
            "error_state": "missing_mapping",
            "error_message": "Configure 'Deployment Date' field mapping",
            "performance_tier": None,
            "performance_tier_color": None,
            "total_issue_count": len(issues),
            "filtered_issue_count": len(deployment_issues),
            "excluded_issue_count": 0,
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }

    deployment_date_field = field_mappings["deployment_date"]

    # Calculate time period boundaries (use provided dates if available)
    if start_date is None or end_date is None:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=time_period_days)
    else:
        # Use provided explicit boundaries (for retrospective trend calculation)
        time_period_days = (end_date - start_date).days

    # Filter and parse deployments
    # NOTE: Count ALL deployments, regardless of success/failure
    # Change Failure Rate separately tracks which deployments failed
    valid_deployments = []
    excluded_count = 0

    for issue in deployment_issues:
        fields = issue.get("fields", {})

        # Parse deployment date (handles special fields like fixVersions)
        deployment_date_str = _get_date_field_value(fields, deployment_date_field)
        deployment_date = _parse_datetime(deployment_date_str)

        if not deployment_date:
            excluded_count += 1
            continue

        # Check if deployment is in time period
        if not (start_date <= deployment_date <= end_date):
            excluded_count += 1
            continue

        # Count ALL deployments for Deployment Frequency metric
        valid_deployments.append(deployment_date)

    # Handle no data case
    if not valid_deployments:
        return {
            "metric_name": "deployment_frequency",
            "value": None,
            "unit": "deployments/month",
            "error_state": "no_data",
            "error_message": f"No deployments found in the last {time_period_days} days",
            "performance_tier": None,
            "performance_tier_color": None,
            "total_issue_count": len(issues),
            "filtered_issue_count": len(deployment_issues),
            "excluded_issue_count": excluded_count,
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }

    # Calculate deployment frequency (normalize to per-month)
    deployment_count = len(valid_deployments)
    deployments_per_month = (deployment_count / time_period_days) * 30

    # Determine performance tier
    tier_info = _determine_performance_tier(
        deployments_per_month, DEPLOYMENT_FREQUENCY_TIERS
    )

    # Calculate trend if previous period value is provided
    trend_data = _calculate_trend(deployments_per_month, previous_period_value)

    return {
        "metric_name": "deployment_frequency",
        "value": round(deployments_per_month, 1),
        "unit": "deployments/month",
        "error_state": "success",
        "error_message": None,
        "performance_tier": tier_info["tier"],
        "performance_tier_color": tier_info["color"],
        "total_issue_count": len(issues),
        "filtered_issue_count": len(deployment_issues),
        "excluded_issue_count": excluded_count,
        "calculation_timestamp": datetime.now().isoformat(),
        "time_period_start": start_date.isoformat(),
        "time_period_end": end_date.isoformat(),
        "trend_direction": trend_data["trend_direction"],
        "trend_percentage": trend_data["trend_percentage"],
    }


def calculate_lead_time_for_changes(
    issues: List[Dict[str, Any]],
    field_mappings: Dict[str, str],
    previous_period_value: Optional[float] = None,
    devops_projects: Optional[List[str]] = None,
    active_statuses: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Calculate lead time for changes metric.

    Lead time measures the time from code commit to production deployment.

    Code Commit Date: First transition into ANY active_statuses (from changelog)
    Deployment Date: Extracted from fixVersion.releaseDate

    This metric links work items (Stories/Tasks in dev projects) to deployments
    (Operational Tasks in DevOps projects) via the fixVersion field.

    Args:
        issues: List of change issue dictionaries from Jira (work items with changelog)
        field_mappings: Mapping of internal fields to Jira field IDs
        previous_period_value: Previous period's metric value for trend calculation
        devops_projects: List of DevOps project keys (used if filtering is needed)
        active_statuses: List of active status names (e.g., ["In Progress", "In Review", "Testing"])
                        If None, loads from configuration

    Returns:
        Metric data dictionary with value, unit, performance tier, trend data, and metadata

    Note:
        For lead time, we calculate from work items (dev projects) that have deployment dates
        in their fixVersions field. The fixVersions link work items to deployments.
    """
    # Import changelog processor for status transition detection
    from data.changelog_processor import get_first_status_transition_from_list

    # Check for required field mappings
    required_fields = ["deployed_to_production_date"]
    missing_fields = [f for f in required_fields if f not in field_mappings]

    if missing_fields:
        return {
            "metric_name": "lead_time_for_changes",
            "value": None,
            "unit": "days",
            "error_state": "missing_mapping",
            "error_message": f"Configure field mappings: {', '.join(missing_fields)}",
            "performance_tier": None,
            "performance_tier_color": None,
            "total_issue_count": len(issues),
            "excluded_issue_count": 0,
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }

    # Load active_statuses from configuration if not provided
    if active_statuses is None:
        from configuration.metrics_config import get_metrics_config

        config = get_metrics_config()
        active_statuses = config.get_active_statuses()
        if not active_statuses:
            return {
                "metric_name": "lead_time_for_changes",
                "value": None,
                "unit": "days",
                "error_state": "missing_config",
                "error_message": "Configure 'active_statuses' in app_settings.json",
                "performance_tier": None,
                "performance_tier_color": None,
                "total_issue_count": len(issues),
                "excluded_issue_count": 0,
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

    deploy_date_field = field_mappings["deployed_to_production_date"]

    # Calculate lead times
    lead_times = []
    excluded_count = 0
    no_active_transition_count = 0

    for issue in issues:
        fields = issue.get("fields", {})

        # Get commit date from CHANGELOG - first transition to any active_statuses
        commit_result = get_first_status_transition_from_list(
            issue, active_statuses, case_sensitive=False
        )

        if not commit_result:
            # Issue never entered active statuses
            no_active_transition_count += 1
            excluded_count += 1
            continue

        _, commit_date = commit_result  # Unpack (status_name, timestamp)

        # Parse deployment date (handles special fields like fixVersions)
        deploy_date = _parse_datetime(_get_date_field_value(fields, deploy_date_field))

        if not commit_date or not deploy_date:
            excluded_count += 1
            continue

        # Calculate lead time in days
        lead_time_delta = deploy_date - commit_date
        lead_time_days = lead_time_delta.total_seconds() / 86400  # Convert to days

        if lead_time_days < 0:
            # Skip invalid data (deployment before commit)
            excluded_count += 1
            logger.warning(
                f"Issue {issue.get('key')}: deployment date before commit date"
            )
            continue

        lead_times.append(lead_time_days)

    # Handle no data case
    if not lead_times:
        error_details = []
        if no_active_transition_count > 0:
            error_details.append(
                f"{no_active_transition_count} never entered active statuses"
            )

        error_msg = "No changes with valid commit and deployment dates"
        if error_details:
            error_msg += f" ({', '.join(error_details)})"

        return {
            "metric_name": "lead_time_for_changes",
            "value": None,
            "unit": "days",
            "error_state": "no_data",
            "error_message": error_msg,
            "performance_tier": None,
            "performance_tier_color": None,
            "total_issue_count": len(issues),
            "excluded_issue_count": excluded_count,
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }

    # Calculate average lead time
    avg_lead_time = sum(lead_times) / len(lead_times)

    # Determine performance tier
    tier_info = _determine_performance_tier(avg_lead_time, LEAD_TIME_TIERS)

    # Calculate trend if previous period value is provided
    trend_data = _calculate_trend(avg_lead_time, previous_period_value)

    return {
        "metric_name": "lead_time_for_changes",
        "value": round(avg_lead_time, 2),
        "unit": "days",
        "error_state": "success",
        "error_message": None,
        "performance_tier": tier_info["tier"],
        "performance_tier_color": tier_info["color"],
        "total_issue_count": len(issues),
        "excluded_issue_count": excluded_count,
        "calculation_timestamp": datetime.now().isoformat(),
        "trend_direction": trend_data["trend_direction"],
        "trend_percentage": trend_data["trend_percentage"],
    }


def calculate_change_failure_rate(
    deployment_issues: List[Dict[str, Any]],
    incident_issues: List[Dict[str, Any]],
    field_mappings: Dict[str, str],
    previous_period_value: Optional[float] = None,
    devops_projects: Optional[List[str]] = None,
    devops_task_types: Optional[List[str]] = None,
    bug_types: Optional[List[str]] = None,
    production_environment_values: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Calculate change failure rate metric.

    Args:
        deployment_issues: List of deployment issue dictionaries from Jira (pre-filtered or mixed)
        incident_issues: List of incident issue dictionaries from Jira (pre-filtered or mixed)
        field_mappings: Mapping of internal fields to Jira field IDs
        previous_period_value: Previous period's metric value for trend calculation
        devops_projects: List of DevOps project keys for filtering (e.g., ["DEVOPS"])
        devops_task_types: List of issue type names for DevOps tasks (backward compatible)
        bug_types: List of issue type names for bugs (backward compatible)
        production_environment_values: List of production environment identifiers (backward compatible)

    Returns:
        Metric data dictionary with value, unit, performance tier, trend data, and metadata

    Note:
        This function expects either pre-filtered issues OR will filter them if devops_projects is provided:
        - deployment_issues: Should be DevOps task types from DevOps projects
        - incident_issues: Should be production bugs from development projects
    """
    # Filter issues if devops_projects is provided (support both pre-filtered and mixed inputs)
    if devops_projects:
        deployment_issues = filter_deployment_issues(
            deployment_issues, devops_projects, devops_task_types
        )
        incident_issues = filter_incident_issues(
            incident_issues,
            devops_projects,
            production_environment_field=field_mappings.get("affected_environment"),
            production_environment_values=production_environment_values,
            bug_types=bug_types,
        )
    # Check for required field mappings
    if "deployment_date" not in field_mappings:
        return {
            "metric_name": "change_failure_rate",
            "value": None,
            "unit": "percentage",
            "error_state": "missing_mapping",
            "error_message": "Configure 'Deployment Date' field mapping",
            "performance_tier": None,
            "performance_tier_color": None,
            "total_issue_count": len(deployment_issues) + len(incident_issues),
            "excluded_issue_count": 0,
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }

    # Count total deployments
    deployment_count = len(deployment_issues)

    # DEBUG: Log deployment and incident counts
    logger.info(f"CFR Debug: deployment_issues count = {deployment_count}")
    logger.info(f"CFR Debug: incident_issues count = {len(incident_issues)}")

    if deployment_count == 0:
        return {
            "metric_name": "change_failure_rate",
            "value": None,
            "unit": "percentage",
            "error_state": "no_data",
            "error_message": "No deployments found for calculation",
            "performance_tier": None,
            "performance_tier_color": None,
            "total_issue_count": 0,
            "excluded_issue_count": 0,
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }

    # Check if change_failure field is mapped (preferred method)
    change_failure_field = field_mappings.get("change_failure")
    excluded_count = 0

    if change_failure_field:
        # Method 1: Use change_failure field on deployment issues
        # Count deployments where change_failure = "Yes" (indicating production issue)
        failed_deployment_count = 0

        for issue in deployment_issues:
            fields = issue.get("fields", {})
            if _check_deployment_failed(fields, change_failure_field):
                failed_deployment_count += 1

        failure_count = failed_deployment_count
        logger.info(
            f"CFR Debug: Using change_failure field - {failed_deployment_count} failed out of {deployment_count} total"
        )
    else:
        # Method 2: Fallback to incident-based calculation
        # Count production incidents
        production_impact_field = field_mappings.get("production_impact")
        incident_count = 0

        for issue in incident_issues:
            fields = issue.get("fields", {})

            # If production_impact field is mapped, only count incidents with impact
            if production_impact_field:
                has_impact = fields.get(production_impact_field)
                if has_impact:
                    incident_count += 1
                else:
                    excluded_count += 1
            else:
                # If not mapped, count all incidents
                incident_count += 1

        failure_count = incident_count
        logger.info(
            f"CFR Debug: Using incident-based calculation - {incident_count} incidents, {deployment_count} deployments"
        )
        logger.info(f"CFR Debug: production_impact_field = {production_impact_field}")

    # Calculate failure rate percentage
    failure_rate = (failure_count / deployment_count) * 100

    # Determine performance tier
    tier_info = _determine_performance_tier(failure_rate, CHANGE_FAILURE_RATE_TIERS)

    # Calculate trend if previous period value is provided
    trend_data = _calculate_trend(failure_rate, previous_period_value)

    return {
        "metric_name": "change_failure_rate",
        "value": round(failure_rate, 1),
        "unit": "percentage",
        "error_state": "success",
        "error_message": None,
        "performance_tier": tier_info["tier"],
        "performance_tier_color": tier_info["color"],
        "total_issue_count": len(deployment_issues) + len(incident_issues),
        "excluded_issue_count": excluded_count,
        "calculation_timestamp": datetime.now().isoformat(),
        "details": {
            "deployment_count": deployment_count,
            "failure_count": failure_count,
        },
        "trend_direction": trend_data["trend_direction"],
        "trend_percentage": trend_data["trend_percentage"],
    }


def calculate_mean_time_to_recovery(
    issues: List[Dict[str, Any]],
    field_mappings: Dict[str, str],
    previous_period_value: Optional[float] = None,
    devops_projects: Optional[List[str]] = None,
    operational_tasks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Calculate mean time to recovery (MTTR) metric with two-mode calculation.

    MODE A: devops_projects IS configured
        - Calculate: Bug.created → Linked_Operational_Task.resolutiondate
        - Uses fixVersion matching to find related operational tasks
        - Bugs without linked operational tasks are skipped
        - Represents actual production recovery time (when deployment is resolved)

    MODE B: devops_projects NOT configured
        - Calculate: Bug.created → Bug.resolutiondate
        - All production bugs included
        - Represents bug fix time (no deployment process)

    Args:
        issues: List of incident issue dictionaries from Jira (Bugs from development projects)
        field_mappings: Mapping of internal fields to Jira field IDs
        previous_period_value: Previous period's metric value for trend calculation
        devops_projects: List of DevOps project keys - determines calculation mode
        operational_tasks: List of Operational Task issues (required for MODE A)

    Returns:
        Metric data dictionary with value, unit, performance tier, trend data, and metadata
    """
    # Determine calculation mode based on devops_projects configuration
    use_operational_tasks = devops_projects and len(devops_projects) > 0

    if use_operational_tasks:
        logger.info("MTTR Mode A: Using Bug → Linked Operational Task calculation")
    else:
        logger.info(
            "MTTR Mode B: Using Bug → Bug resolution calculation (no devops_projects)"
        )

    # Filter to production incidents (Bugs in development projects)
    if devops_projects:
        issues = filter_incident_issues(
            issues,
            devops_projects,
            production_environment_field=field_mappings.get("affected_environment"),
        )

    # Check for required field mappings
    required_fields = ["incident_detected_at"]
    if not use_operational_tasks:
        # MODE B: Need incident_resolved_at for bug resolution
        required_fields.append("incident_resolved_at")

    missing_fields = [f for f in required_fields if f not in field_mappings]

    if missing_fields:
        return {
            "metric_name": "mean_time_to_recovery",
            "value": None,
            "unit": "hours",
            "error_state": "missing_mapping",
            "error_message": f"Configure field mappings: {', '.join(missing_fields)}",
            "performance_tier": None,
            "performance_tier_color": None,
            "total_issue_count": len(issues),
            "excluded_issue_count": 0,
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }

    detected_field = field_mappings["incident_detected_at"]

    # Calculate recovery times
    recovery_times = []
    excluded_count = 0
    no_linked_task_count = 0

    if use_operational_tasks:
        # MODE A: Bug → Linked Operational Task
        from data.fixversion_matcher import find_matching_operational_tasks

        if not operational_tasks:
            logger.warning("MTTR Mode A requires operational_tasks parameter")
            operational_tasks = []

        for issue in issues:
            fields = issue.get("fields", {})

            # Parse bug detection date (when bug was created)
            detected_at = _parse_datetime(_get_date_field_value(fields, detected_field))

            if not detected_at:
                excluded_count += 1
                continue

            # Find linked operational tasks via fixVersion
            matching_tasks = find_matching_operational_tasks(
                issue, operational_tasks, match_by="auto"
            )

            if not matching_tasks:
                # No linked operational task - skip this bug
                no_linked_task_count += 1
                excluded_count += 1
                logger.debug(
                    f"Issue {issue.get('key')}: No linked operational task via fixVersion"
                )
                continue

            # Use earliest operational task resolution date
            earliest_resolution = None
            for op_task, match_method in matching_tasks:
                op_fields = op_task.get("fields", {})
                op_resolved = _parse_datetime(
                    _get_date_field_value(op_fields, "resolutiondate")
                )

                if op_resolved:
                    if earliest_resolution is None or op_resolved < earliest_resolution:
                        earliest_resolution = op_resolved

            if not earliest_resolution:
                excluded_count += 1
                logger.debug(
                    f"Issue {issue.get('key')}: Linked operational tasks not resolved"
                )
                continue

            # Calculate recovery time: Bug created → Operational task resolved
            recovery_delta = earliest_resolution - detected_at
            recovery_hours = recovery_delta.total_seconds() / 3600

            if recovery_hours < 0:
                excluded_count += 1
                logger.warning(
                    f"Issue {issue.get('key')}: operational task resolved before bug created"
                )
                continue

            recovery_times.append(recovery_hours)

    else:
        # MODE B: Bug → Bug resolution
        resolved_field = field_mappings["incident_resolved_at"]

        for issue in issues:
            fields = issue.get("fields", {})

            # Parse dates
            detected_at = _parse_datetime(_get_date_field_value(fields, detected_field))
            resolved_at = _parse_datetime(_get_date_field_value(fields, resolved_field))

            if not detected_at or not resolved_at:
                excluded_count += 1
                continue

            # Calculate recovery time in hours
            recovery_delta = resolved_at - detected_at
            recovery_hours = recovery_delta.total_seconds() / 3600

            if recovery_hours < 0:
                excluded_count += 1
                logger.warning(
                    f"Issue {issue.get('key')}: resolved date before detected date"
                )
                continue

            recovery_times.append(recovery_hours)

    # Handle no data case
    if not recovery_times:
        error_details = []
        if use_operational_tasks and no_linked_task_count > 0:
            error_details.append(
                f"{no_linked_task_count} bugs without linked operational tasks"
            )

        error_msg = "No resolved incidents found for calculation"
        if error_details:
            error_msg += f" ({', '.join(error_details)})"

        return {
            "metric_name": "mean_time_to_recovery",
            "value": None,
            "unit": "hours",
            "error_state": "no_data",
            "error_message": error_msg,
            "performance_tier": None,
            "performance_tier_color": None,
            "total_issue_count": len(issues),
            "excluded_issue_count": excluded_count,
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "calculation_mode": "operational_task"
            if use_operational_tasks
            else "bug_resolution",
        }

    # Calculate average recovery time
    avg_recovery_time = sum(recovery_times) / len(recovery_times)

    # Determine performance tier
    tier_info = _determine_performance_tier(avg_recovery_time, MTTR_TIERS)

    # Calculate trend if previous period value is provided
    trend_data = _calculate_trend(avg_recovery_time, previous_period_value)

    return {
        "metric_name": "mean_time_to_recovery",
        "value": round(avg_recovery_time, 2),
        "unit": "hours",
        "error_state": "success",
        "error_message": None,
        "performance_tier": tier_info["tier"],
        "performance_tier_color": tier_info["color"],
        "total_issue_count": len(issues),
        "excluded_issue_count": excluded_count,
        "calculation_timestamp": datetime.now().isoformat(),
        "trend_direction": trend_data["trend_direction"],
        "trend_percentage": trend_data["trend_percentage"],
        "calculation_mode": "operational_task"
        if use_operational_tasks
        else "bug_resolution",
    }


def calculate_all_dora_metrics(
    issues: Dict[str, List[Dict[str, Any]]],
    field_mappings: Dict[str, str],
    time_period_days: int = 30,
) -> Dict[str, Dict[str, Any]]:
    """Calculate all four DORA metrics at once.

    Args:
        issues: Dictionary with "deployments" and "incidents" issue lists
        field_mappings: Mapping of internal fields to Jira field IDs
        time_period_days: Time period for deployment frequency calculation

    Returns:
        Dictionary with all four DORA metric results keyed by metric name
    """
    deployment_issues = issues.get("deployments", [])
    incident_issues = issues.get("incidents", [])

    results = {
        "deployment_frequency": calculate_deployment_frequency(
            deployment_issues, field_mappings, time_period_days
        ),
        "lead_time_for_changes": calculate_lead_time_for_changes(
            deployment_issues, field_mappings
        ),
        "change_failure_rate": calculate_change_failure_rate(
            deployment_issues, incident_issues, field_mappings
        ),
        "mean_time_to_recovery": calculate_mean_time_to_recovery(
            incident_issues, field_mappings
        ),
    }

    return results


# ============================================================================
# NEW IMPLEMENTATIONS - Configuration-Driven DORA Metrics
# ============================================================================


def calculate_deployment_frequency_v2(
    operational_tasks: List[Dict[str, Any]],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Calculate deployment frequency using fixVersion.releaseDate.

    This implementation uses:
    - Operational tasks filtered by project_filter.filter_operational_tasks()
    - fixVersion.releaseDate as the authoritative deployment date
    - Only counts deployments where releaseDate <= today (already happened)

    Args:
        operational_tasks: Operational Task issues already filtered by:
                          - Operational projects (e.g., ["OPS"])
                          - Issue type = "Operational Task"
                          - Has fixVersion with matching development issues
        start_date: Optional start date for period (defaults to 30 days ago)
        end_date: Optional end date for period (defaults to today)

    Returns:
        Dictionary with deployment frequency metrics:
        - deployment_count: Total deployments in period
        - deployments_per_week: Average deployments per week
        - period_days: Number of days in period
        - excluded_count: Tasks excluded (future deployments, no releaseDate)

    Example:
        >>> from data.project_filter import filter_operational_tasks, extract_all_fixversions
        >>> from data.fixversion_matcher import filter_operational_tasks_by_fixversion
        >>>
        >>> dev_issues = filter_development_issues(all_issues, ["RI"])
        >>> dev_fixversions = extract_all_fixversions(dev_issues)
        >>> op_tasks = filter_operational_tasks(all_issues, ["RI"], dev_fixversions)
        >>>
        >>> result = calculate_deployment_frequency_v2(op_tasks)
        >>> print(f"Deployments per week: {result['deployments_per_week']:.1f}")
    """
    # Default time period: last 30 days
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    # Ensure timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    period_days = (end_date - start_date).days
    if period_days <= 0:
        logger.warning("Invalid date range: end_date must be after start_date")
        return {
            "deployment_count": 0,
            "deployments_per_week": 0.0,
            "period_days": 0,
            "excluded_count": 0,
            "error": "invalid_date_range",
        }

    today = datetime.now(timezone.utc)
    valid_deployments = []
    unique_releases = set()  # Track unique fixVersion names (releases)
    excluded_count = 0
    no_release_date_count = 0
    future_deployment_count = 0

    for task in operational_tasks:
        fixversions = task.get("fields", {}).get("fixVersions", [])

        if not fixversions:
            # Should not happen - filter_operational_tasks removes these
            excluded_count += 1
            continue

        # Find earliest releaseDate that's in the past
        deployment_date = None
        release_name = None

        for fv in fixversions:
            release_date_str = fv.get("releaseDate", "")

            if not release_date_str or not release_date_str.strip():
                # No releaseDate - check next fixVersion
                continue

            try:
                # Parse releaseDate (format: "2025-10-21")
                release_date = datetime.fromisoformat(release_date_str.strip())

                # Ensure timezone-aware
                if release_date.tzinfo is None:
                    release_date = release_date.replace(tzinfo=timezone.utc)

                # Only consider deployments that have happened (releaseDate <= today)
                if release_date > today:
                    future_deployment_count += 1
                    continue

                # Use earliest deployment date from all fixVersions
                if deployment_date is None or release_date < deployment_date:
                    deployment_date = release_date
                    release_name = fv.get("name", "")  # Track the release name

            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Failed to parse releaseDate '{release_date_str}' "
                    f"for {task.get('key', 'unknown')}: {e}"
                )
                continue

        # Check if we found a valid deployment date
        if deployment_date is None:
            no_release_date_count += 1
            excluded_count += 1
            continue

        # Check if deployment is in the time period
        if start_date <= deployment_date <= end_date:
            valid_deployments.append(
                {
                    "task_key": task.get("key", "unknown"),
                    "deployment_date": deployment_date.isoformat(),
                    "release_name": release_name,
                }
            )
            # Track unique release names
            if release_name:
                unique_releases.add(release_name)
        else:
            excluded_count += 1

    # Log exclusion reasons
    if no_release_date_count > 0:
        logger.info(
            f"Excluded {no_release_date_count} operational tasks with no releaseDate "
            f"(use resolutiondate fallback in future enhancement)"
        )

    if future_deployment_count > 0:
        logger.info(
            f"Excluded {future_deployment_count} operational tasks with future releaseDate "
            f"(deployments not yet happened)"
        )

    # Calculate frequency
    deployment_count = len(valid_deployments)
    release_count = len(unique_releases)  # Count of unique releases
    deployments_per_week = (
        (deployment_count / period_days) * 7 if period_days > 0 else 0.0
    )
    releases_per_week = (release_count / period_days) * 7 if period_days > 0 else 0.0

    logger.info(
        f"Deployment Frequency: {deployment_count} deployments ({release_count} unique releases) "
        f"in {period_days} days ({deployments_per_week:.2f} deployments/week, "
        f"{releases_per_week:.2f} releases/week)"
    )

    return {
        "deployment_count": deployment_count,
        "release_count": release_count,  # NEW: Unique releases
        "deployments_per_week": round(deployments_per_week, 2),
        "releases_per_week": round(
            releases_per_week, 2
        ),  # NEW: Unique releases per week
        "period_days": period_days,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "excluded_count": excluded_count,
        "no_release_date_count": no_release_date_count,
        "future_deployment_count": future_deployment_count,
        "deployments": valid_deployments,
        "unique_releases": sorted(list(unique_releases)),  # NEW: List of release names
    }


def calculate_lead_time_for_changes_v2(
    development_issues: List[Dict[str, Any]],
    operational_tasks: List[Dict[str, Any]],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Calculate Lead Time for Changes using changelog and operational task matching.

    Lead Time measures the time from when code is deployment-ready ("In Deployment" status)
    to when it's actually deployed to production (operational task fixVersion.releaseDate).

    This implementation uses:
    - Start time: First "In Deployment" status timestamp (from changelog)
    - End time: Matching operational task fixVersion.releaseDate
    - Fallback 1: Use "Done" status if never reached "In Deployment"
    - Fallback 2: Use issue's own completion if no operational task found

    Args:
        development_issues: Development issues (already filtered, with changelog data)
        operational_tasks: Operational tasks (already filtered by filter_operational_tasks)
        start_date: Optional start date for filtering completed issues
        end_date: Optional end date for filtering completed issues

    Returns:
        Dictionary with lead time metrics:
        - lead_times_hours: List of individual lead times in hours
        - median_hours: Median lead time
        - mean_hours: Average lead time
        - p75_hours: 75th percentile
        - p90_hours: 90th percentile
        - p95_hours: 95th percentile
        - total_issues: Total issues analyzed
        - excluded_count: Issues excluded (no deployment date, etc.)

    Example:
        >>> from data.changelog_processor import get_first_status_transition_timestamp
        >>> from data.fixversion_matcher import find_matching_operational_tasks, get_earliest_deployment_date
        >>>
        >>> # Development issues should have changelog data
        >>> result = calculate_lead_time_for_changes_v2(dev_issues, op_tasks)
        >>> print(f"Median Lead Time: {result['median_hours']:.1f} hours")
    """
    from data.changelog_processor import (
        get_first_status_transition_timestamp,
        get_first_status_transition_from_list,
    )

    # Default time period: last 30 days of completed issues
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    # Ensure timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    lead_times = []
    excluded_count = 0
    no_deployment_status_count = 0
    no_operational_task_count = 0
    no_deployment_date_count = 0

    for issue in development_issues:
        issue_key = issue.get("key", "UNKNOWN")

        # Step 1: Find deployment readiness timestamp (start time)
        # Primary: "In Deployment" status
        deployment_ready_time = get_first_status_transition_timestamp(
            issue, "In Deployment", case_sensitive=False
        )

        # Fallback: Use "Done" status if never reached "In Deployment"
        if not deployment_ready_time:
            completion_statuses = ["Done", "Resolved", "Closed"]
            result = get_first_status_transition_from_list(
                issue, completion_statuses, case_sensitive=False
            )

            if result:
                status_name, deployment_ready_time = result
                logger.debug(
                    f"{issue_key}: No 'In Deployment' status, using '{status_name}' as fallback"
                )
            else:
                no_deployment_status_count += 1
                excluded_count += 1
                logger.debug(
                    f"{issue_key}: No deployment status or completion status found, skipping"
                )
                continue

        # Step 2: Find matching operational task and deployment date (end time)
        # Use get_relevant_deployment_date which filters to deployments AFTER ready time
        from data.fixversion_matcher import get_relevant_deployment_date

        result = get_relevant_deployment_date(
            issue, operational_tasks, deployment_ready_time=deployment_ready_time
        )

        deployment_date = None

        if result:
            # Unpack the tuple: (deployment_date, operational_task, match_method)
            deployment_date, matched_op_task, match_method = result
            logger.debug(
                f"{issue_key}: Matched to {matched_op_task.get('key')} (by {match_method}), "
                f"deployment_date={deployment_date}"
            )
        else:
            # No matching operational task or no valid deployment date
            no_operational_task_count += 1
            logger.debug(
                f"{issue_key}: No matching operational task with valid deployment date"
            )

        # If no deployment date found, skip this issue
        if not deployment_date:
            excluded_count += 1
            continue

        # Convert date to datetime for comparison (deployment_date comes from get_earliest_deployment_date as date object)
        if isinstance(deployment_date, datetime):
            deployment_datetime = deployment_date
        else:
            # Convert date to datetime (assume midnight UTC)
            deployment_datetime = datetime.combine(
                deployment_date, datetime.min.time()
            ).replace(tzinfo=timezone.utc)

        # Step 3: Filter by time period (based on deployment date)
        if not (start_date <= deployment_datetime <= end_date):
            excluded_count += 1
            continue

        # Step 4: Calculate lead time
        lead_time_seconds = (
            deployment_datetime - deployment_ready_time
        ).total_seconds()
        lead_time_hours = lead_time_seconds / 3600

        # Sanity check: negative lead time indicates data issue
        if lead_time_hours < 0:
            logger.warning(
                f"{issue_key}: Negative lead time ({lead_time_hours:.1f}h), "
                f"deployment_ready={deployment_ready_time.isoformat()}, "
                f"deployment_date={deployment_date.isoformat()}"
            )
            excluded_count += 1
            continue

        lead_times.append(
            {
                "issue_key": issue_key,
                "lead_time_hours": round(lead_time_hours, 2),
                "deployment_ready": deployment_ready_time.isoformat(),
                "deployment_date": deployment_datetime.isoformat(),
            }
        )

    # Calculate statistics
    if not lead_times:
        logger.info("No valid lead times calculated")
        return {
            "lead_times_hours": [],
            "median_hours": None,
            "mean_hours": None,
            "p75_hours": None,
            "p90_hours": None,
            "p95_hours": None,
            "total_issues": len(development_issues),
            "issues_with_lead_time": 0,
            "excluded_count": excluded_count,
            "no_deployment_status_count": no_deployment_status_count,
            "no_operational_task_count": no_operational_task_count,
            "no_deployment_date_count": no_deployment_date_count,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    # Extract just the hours for statistical calculation
    hours_list = [lt["lead_time_hours"] for lt in lead_times]
    hours_list.sort()

    # Calculate percentiles
    def percentile(data, p):
        """Calculate percentile from sorted data"""
        if not data:
            return None
        k = (len(data) - 1) * (p / 100)
        f = int(k)
        c = f + 1 if f < len(data) - 1 else f
        return data[f] + (k - f) * (data[c] - data[f])

    median = percentile(hours_list, 50)
    mean = sum(hours_list) / len(hours_list) if hours_list else None
    p75 = percentile(hours_list, 75)
    p90 = percentile(hours_list, 90)
    p95 = percentile(hours_list, 95)

    logger.info(
        f"Lead Time for Changes: {len(lead_times)} issues analyzed, "
        f"median={median:.1f}h, mean={mean:.1f}h, p95={p95:.1f}h"
    )

    return {
        "lead_times_hours": lead_times,  # Full details for each issue
        "median_hours": round(median, 2) if median else None,
        "mean_hours": round(mean, 2) if mean else None,
        "p75_hours": round(p75, 2) if p75 else None,
        "p90_hours": round(p90, 2) if p90 else None,
        "p95_hours": round(p95, 2) if p95 else None,
        "total_issues": len(development_issues),
        "issues_with_lead_time": len(lead_times),
        "excluded_count": excluded_count,
        "no_deployment_status_count": no_deployment_status_count,
        "no_operational_task_count": no_operational_task_count,
        "no_deployment_date_count": no_deployment_date_count,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }


def calculate_change_failure_rate_v2(
    operational_tasks: List[Dict[str, Any]],
    change_failure_field_id: str = "customfield_10001",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Calculate Change Failure Rate from operational tasks.

    Change Failure Rate measures the percentage of deployments that result in failures
    requiring remediation (e.g., hotfix, rollback, fix forward).

    This implementation uses:
    - Custom field for change failure indicator (configured in field_mappings)
    - ONLY "Yes" = failure (everything else = success: "No", "None", null, empty)
    - Only count deployments that have happened (fixVersion.releaseDate <= today)

    Args:
        operational_tasks: Operational Task issues (already filtered by filter_operational_tasks)
        change_failure_field_id: Custom field ID for change failure indicator
        start_date: Optional start date for filtering deployments
        end_date: Optional end date for filtering deployments

    Returns:
        Dictionary with change failure rate metrics:
        - total_deployments: Total deployments in period
        - failed_deployments: Deployments marked as failures
        - successful_deployments: Deployments not marked as failures
        - change_failure_rate_percent: Percentage of failed deployments
        - excluded_count: Deployments excluded (no releaseDate, future deployments)

    Example:
        >>> from data.project_filter import filter_operational_tasks, extract_all_fixversions
        >>>
        >>> dev_issues = filter_development_issues(all_issues, ["RI"])
        >>> dev_fixversions = extract_all_fixversions(dev_issues)
        >>> op_tasks = filter_operational_tasks(all_issues, ["RI"], dev_fixversions)
        >>>
        >>> result = calculate_change_failure_rate_v2(op_tasks)
        >>> print(f"Change Failure Rate: {result['change_failure_rate_percent']:.1f}%")
    """
    # Default time period: last 30 days
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    # Ensure timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    today = datetime.now(timezone.utc)

    total_deployments = 0
    failed_deployments = 0
    successful_deployments = 0
    excluded_count = 0
    no_release_date_count = 0
    future_deployment_count = 0

    failure_details = []

    for task in operational_tasks:
        task_key = task.get("key", "UNKNOWN")
        fixversions = task.get("fields", {}).get("fixVersions", [])

        if not fixversions:
            # Should not happen - filter_operational_tasks removes these
            excluded_count += 1
            continue

        # Find earliest releaseDate that's in the past
        deployment_date = None

        for fv in fixversions:
            release_date_str = fv.get("releaseDate", "")

            if not release_date_str or not release_date_str.strip():
                continue

            try:
                release_date = datetime.fromisoformat(release_date_str.strip())

                if release_date.tzinfo is None:
                    release_date = release_date.replace(tzinfo=timezone.utc)

                # Only consider deployments that have happened
                if release_date > today:
                    future_deployment_count += 1
                    continue

                # Use earliest deployment date
                if deployment_date is None or release_date < deployment_date:
                    deployment_date = release_date

            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Failed to parse releaseDate '{release_date_str}' for {task_key}: {e}"
                )
                continue

        # Check if we found a valid deployment date
        if deployment_date is None:
            no_release_date_count += 1
            excluded_count += 1
            continue

        # Check if deployment is in the time period
        if not (start_date <= deployment_date <= end_date):
            excluded_count += 1
            continue

        # This is a valid deployment - check for failure
        total_deployments += 1

        # Get change failure field value
        change_failure_value = task.get("fields", {}).get(change_failure_field_id)

        # Handle select field (returns dict with 'value' key)
        if isinstance(change_failure_value, dict):
            change_failure_value = change_failure_value.get("value", "")

        # CRITICAL: ONLY "Yes" indicates failure
        # Everything else is success: "No", "None", null, empty
        is_failure = (
            isinstance(change_failure_value, str)
            and change_failure_value.strip().lower() == "yes"
        )

        if is_failure:
            failed_deployments += 1
            failure_details.append(
                {
                    "task_key": task_key,
                    "deployment_date": deployment_date.isoformat(),
                    "change_failure_value": change_failure_value,
                }
            )
        else:
            successful_deployments += 1

    # Calculate change failure rate
    if total_deployments > 0:
        change_failure_rate = (failed_deployments / total_deployments) * 100
    else:
        change_failure_rate = 0.0

    logger.info(
        f"Change Failure Rate: {failed_deployments}/{total_deployments} failures "
        f"({change_failure_rate:.1f}%)"
    )

    if no_release_date_count > 0:
        logger.info(
            f"Excluded {no_release_date_count} operational tasks with no releaseDate"
        )

    if future_deployment_count > 0:
        logger.info(
            f"Excluded {future_deployment_count} operational tasks with future releaseDate"
        )

    return {
        "total_deployments": total_deployments,
        "failed_deployments": failed_deployments,
        "successful_deployments": successful_deployments,
        "change_failure_rate_percent": round(change_failure_rate, 2),
        "excluded_count": excluded_count,
        "no_release_date_count": no_release_date_count,
        "future_deployment_count": future_deployment_count,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "failure_details": failure_details,
    }


def calculate_mttr_v2(
    production_bugs: List[Dict[str, Any]],
    operational_tasks: List[Dict[str, Any]],
    affected_environment_field_id: str = "customfield_10002",
    production_value: str = "PROD",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Calculate Mean Time to Recovery (MTTR) for production incidents.

    MTTR measures the time from when a production bug is created to when the fix
    is deployed to production.

    This implementation uses:
    - Filter bugs by environment custom field (e.g., "PROD" value)
    - Start time: bug.fields.created
    - End time: Matching operational task fixVersion.releaseDate
    - Fallback: bug.fields.resolutiondate if no operational task found
    - Use median for aggregation (not mean) - more robust to outliers

    Args:
        production_bugs: Bug issues from development projects (not yet filtered by environment)
        operational_tasks: Operational Task issues (already filtered)
        affected_environment_field_id: Custom field ID for affected environment
        production_value: Value indicating production environment (default: "PROD")
        start_date: Optional start date for filtering bugs
        end_date: Optional end date for filtering bugs

    Returns:
        Dictionary with MTTR metrics:
        - mttr_hours: List of individual recovery times in hours
        - median_hours: Median recovery time (primary metric)
        - mean_hours: Average recovery time
        - p75_hours: 75th percentile
        - p90_hours: 90th percentile
        - p95_hours: 95th percentile
        - total_bugs: Total production bugs analyzed
        - excluded_count: Bugs excluded (no fix deployed, etc.)

    Example:
        >>> # Filter production bugs first
        >>> prod_bugs = [b for b in bugs if b.get('fields', {}).get('customfield_10002') == 'PROD']
        >>>
        >>> result = calculate_mttr_v2(prod_bugs, op_tasks)
        >>> print(f"MTTR (median): {result['median_hours']:.1f} hours")
    """
    from data.fixversion_matcher import get_earliest_deployment_date

    # Default time period: last 30 days of created bugs
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    # Ensure timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    # Step 1: Filter to production bugs only
    filtered_prod_bugs = []
    not_production_count = 0

    for bug in production_bugs:
        affected_env = bug.get("fields", {}).get(affected_environment_field_id)

        # Handle select field (returns dict with 'value' key)
        if isinstance(affected_env, dict):
            affected_env = affected_env.get("value", "")

        # CRITICAL: Exact match, case-sensitive (as per spec)
        # "PROD" matches, "prod" does not (but we log a warning)
        if affected_env == production_value:
            filtered_prod_bugs.append(bug)
        elif affected_env and affected_env.upper() == production_value.upper():
            # Case mismatch - include but warn
            filtered_prod_bugs.append(bug)
            logger.warning(
                f"Bug {bug.get('key')}: Case mismatch in production environment - "
                f"expected '{production_value}', got '{affected_env}'"
            )
        else:
            not_production_count += 1

    logger.info(
        f"Filtered to {len(filtered_prod_bugs)} production bugs "
        f"(excluded {not_production_count} non-production bugs)"
    )

    # Step 2: Calculate recovery time for each production bug
    recovery_times = []
    excluded_count = 0
    no_fix_deployed_count = 0
    no_created_date_count = 0

    for bug in filtered_prod_bugs:
        bug_key = bug.get("key", "UNKNOWN")

        # Get bug created timestamp
        created_str = bug.get("fields", {}).get("created")
        if not created_str:
            no_created_date_count += 1
            excluded_count += 1
            logger.warning(f"{bug_key}: No created date, skipping")
            continue

        try:
            bug_created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
        except (ValueError, TypeError) as e:
            logger.warning(
                f"{bug_key}: Failed to parse created date '{created_str}': {e}"
            )
            excluded_count += 1
            continue

        # Filter by time period (based on bug created date)
        if not (start_date <= bug_created <= end_date):
            excluded_count += 1
            continue

        # Find fix deployed timestamp (end time)
        # Method 1: Via operational task (preferred)
        result = get_earliest_deployment_date(bug, operational_tasks)

        fix_deployed = None

        if result:
            deployment_date, matched_op_task, match_method = result
            # Convert date to datetime for calculation (deployment_date is a date object)
            if isinstance(deployment_date, datetime):
                fix_deployed = deployment_date
            else:
                # Convert date to datetime (assume midnight UTC)
                fix_deployed = datetime.combine(
                    deployment_date, datetime.min.time()
                ).replace(tzinfo=timezone.utc)

            logger.debug(
                f"{bug_key}: Fix deployed via {matched_op_task.get('key')} (by {match_method}), "
                f"deployment_date={fix_deployed}"
            )
        else:
            # Method 2: Fallback to bug's own resolution date
            resolution_str = bug.get("fields", {}).get("resolutiondate")
            if resolution_str:
                try:
                    fix_deployed = datetime.fromisoformat(
                        resolution_str.replace("Z", "+00:00")
                    )
                    logger.debug(
                        f"{bug_key}: No matching operational task, using resolutiondate as fallback"
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"{bug_key}: Failed to parse resolutiondate '{resolution_str}': {e}"
                    )

        # If no fix deployed date found, skip this bug
        if not fix_deployed:
            no_fix_deployed_count += 1
            excluded_count += 1
            logger.debug(f"{bug_key}: No fix deployed date found, skipping")
            continue

        # Calculate recovery time
        recovery_seconds = (fix_deployed - bug_created).total_seconds()
        recovery_hours = recovery_seconds / 3600

        # Sanity check: negative recovery time indicates data issue
        if recovery_hours < 0:
            logger.warning(
                f"{bug_key}: Negative recovery time ({recovery_hours:.1f}h), "
                f"created={bug_created.isoformat()}, fixed={fix_deployed.isoformat()}"
            )
            excluded_count += 1
            continue

        recovery_times.append(
            {
                "bug_key": bug_key,
                "recovery_hours": round(recovery_hours, 2),
                "created": bug_created.isoformat(),
                "fixed": fix_deployed.isoformat()
                if isinstance(fix_deployed, datetime)
                else fix_deployed.strftime("%Y-%m-%d"),
            }
        )

    # Calculate statistics
    if not recovery_times:
        logger.info("No valid recovery times calculated for MTTR")
        return {
            "mttr_hours": [],
            "median_hours": None,
            "mean_hours": None,
            "p75_hours": None,
            "p90_hours": None,
            "p95_hours": None,
            "total_bugs": len(production_bugs),
            "production_bugs": len(filtered_prod_bugs),
            "bugs_with_mttr": 0,
            "excluded_count": excluded_count,
            "not_production_count": not_production_count,
            "no_fix_deployed_count": no_fix_deployed_count,
            "no_created_date_count": no_created_date_count,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    # Extract just the hours for statistical calculation
    hours_list = [rt["recovery_hours"] for rt in recovery_times]
    hours_list.sort()

    # Calculate percentiles
    def percentile(data, p):
        """Calculate percentile from sorted data"""
        if not data:
            return None
        k = (len(data) - 1) * (p / 100)
        f = int(k)
        c = f + 1 if f < len(data) - 1 else f
        return data[f] + (k - f) * (data[c] - data[f])

    median = percentile(hours_list, 50)
    mean = sum(hours_list) / len(hours_list) if hours_list else None
    p75 = percentile(hours_list, 75)
    p90 = percentile(hours_list, 90)
    p95 = percentile(hours_list, 95)

    logger.info(
        f"MTTR: {len(recovery_times)} production bugs analyzed, "
        f"median={median:.1f}h, mean={mean:.1f}h, p95={p95:.1f}h"
    )

    return {
        "mttr_hours": recovery_times,  # Full details for each bug
        "median_hours": round(median, 2) if median else None,
        "mean_hours": round(mean, 2) if mean else None,
        "p75_hours": round(p75, 2) if p75 else None,
        "p90_hours": round(p90, 2) if p90 else None,
        "p95_hours": round(p95, 2) if p95 else None,
        "total_bugs": len(production_bugs),
        "production_bugs": len(filtered_prod_bugs),
        "bugs_with_mttr": len(recovery_times),
        "excluded_count": excluded_count,
        "not_production_count": not_production_count,
        "no_fix_deployed_count": no_fix_deployed_count,
        "no_created_date_count": no_created_date_count,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }


# ==============================================================================
# Weekly Aggregation Functions
# ==============================================================================


def aggregate_deployment_frequency_weekly(
    operational_tasks: List,
    completion_statuses: List[str],
    week_labels: List[str],
    case_sensitive: bool = False,
) -> Dict[str, Dict]:
    """
    Aggregate deployment frequency by ISO week.

    Counts both deployments (operational tasks) and releases (unique fixVersions) per week.

    Args:
        operational_tasks: List of operational task issue objects
        completion_statuses: List of completion status names
        week_labels: List of year-week labels to aggregate (e.g., ["2025-43", "2025-44"])
        case_sensitive: Whether to match status names case-sensitively

    Returns:
        Dictionary mapping week labels to deployment and release counts

    Example:
        >>> aggregate_deployment_frequency_weekly(op_tasks, ["Done"], ["2025-43", "2025-44"])
        {
            "2025-43": {"deployments": 12, "releases": 8},
            "2025-44": {"deployments": 15, "releases": 12}
        }
    """
    from data.time_period_calculator import get_year_week_label
    from datetime import datetime

    logger.info(f"Aggregating deployment frequency for {len(week_labels)} weeks")

    # Initialize result with zero counts
    weekly_counts = {
        label: {"deployments": 0, "releases": set()} for label in week_labels
    }

    if not operational_tasks or not completion_statuses:
        logger.warning(
            "aggregate_deployment_frequency_weekly: No operational tasks or completion statuses provided"
        )
        return weekly_counts

    # Convert statuses for case-insensitive matching
    completion_statuses_lower = (
        [s.lower() for s in completion_statuses] if not case_sensitive else []
    )

    for task in operational_tasks:
        try:
            # Check completion status - handle dict format
            fields = task.get("fields", {})
            status_obj = fields.get("status", {})

            if not status_obj:
                continue

            task_status_name = (
                status_obj.get("name")
                if isinstance(status_obj, dict)
                else getattr(status_obj, "name", None)
            )
            if not task_status_name:
                continue

            status_match = (
                task_status_name in completion_statuses
                if case_sensitive
                else task_status_name.lower() in completion_statuses_lower
            )

            if not status_match:
                continue

            # Get deployment date from fixVersion releaseDate
            fixversions = fields.get("fixVersions", [])
            if not fixversions:
                continue

            # Use earliest releaseDate that's in the past
            from datetime import date

            today = date.today()
            deployed_versions = []
            for fv in fixversions:
                if isinstance(fv, dict):
                    release_date_str = fv.get("releaseDate")
                    if (
                        release_date_str
                        and datetime.strptime(release_date_str, "%Y-%m-%d").date()
                        <= today
                    ):
                        deployed_versions.append(fv)
                elif hasattr(fv, "releaseDate") and fv.releaseDate:
                    if datetime.strptime(fv.releaseDate, "%Y-%m-%d").date() <= today:
                        deployed_versions.append(fv)

            if not deployed_versions:
                continue

            def get_release_date(fv):
                if isinstance(fv, dict):
                    return fv.get("releaseDate", "")
                return getattr(fv, "releaseDate", "")

            def get_release_name(fv):
                if isinstance(fv, dict):
                    return fv.get("name", "")
                return getattr(fv, "name", "")

            earliest_release = min(
                deployed_versions, key=lambda fv: get_release_date(fv)
            )
            release_date_str = get_release_date(earliest_release)
            release_name = get_release_name(earliest_release)
            deployment_dt = datetime.strptime(release_date_str, "%Y-%m-%d")
            week_label = get_year_week_label(deployment_dt)

            # Increment count if week is in target weeks
            if week_label in weekly_counts:
                weekly_counts[week_label]["deployments"] += 1
                if release_name:
                    weekly_counts[week_label]["releases"].add(release_name)

        except (AttributeError, ValueError) as e:
            task_key = (
                task.get("key", "unknown")
                if isinstance(task, dict)
                else getattr(task, "key", "unknown")
            )
            logger.debug(f"Error processing task {task_key}: {e}")
            continue

    # Convert sets to counts for return value
    result = {}
    for week_label in week_labels:
        result[week_label] = {
            "deployments": weekly_counts[week_label]["deployments"],
            "releases": len(weekly_counts[week_label]["releases"]),
            "release_names": sorted(list(weekly_counts[week_label]["releases"])),
        }

    # Log summary
    summary = [
        f"{w}: {r['deployments']}d/{r['releases']}r"
        for w, r in result.items()
        if r["deployments"] > 0
    ]
    logger.info(f"Weekly deployment counts: {summary}")
    return result


def aggregate_lead_time_weekly(
    lead_times: List[Dict], week_labels: List[str]
) -> Dict[str, Dict]:
    """
    Aggregate lead time by ISO week using median (not mean).

    Groups lead times by week and calculates median, mean, and percentiles.

    Args:
        lead_times: List of lead time dictionaries from calculate_lead_time_for_changes_v2
        week_labels: List of year-week labels to aggregate

    Returns:
        Dictionary mapping week labels to statistics

    Example:
        >>> aggregate_lead_time_weekly(lead_times, ["2025-43", "2025-44"])
        {
            "2025-43": {"median_hours": 48.5, "mean_hours": 52.1, "count": 12},
            "2025-44": {"median_hours": 45.2, "mean_hours": 47.8, "count": 15}
        }
    """
    from data.time_period_calculator import get_year_week_label
    from datetime import datetime
    import statistics

    logger.info(f"Aggregating lead time for {len(week_labels)} weeks")

    # Initialize result
    weekly_stats = {
        label: {
            "median_hours": None,
            "mean_hours": None,
            "p75_hours": None,
            "p90_hours": None,
            "count": 0,
        }
        for label in week_labels
    }

    if not lead_times:
        logger.warning("aggregate_lead_time_weekly: No lead times provided")
        return weekly_stats

    # Group by week
    from collections import defaultdict

    week_groups = defaultdict(list)

    for lt in lead_times:
        deployment_date_str = lt.get("deployment_date")
        if not deployment_date_str:
            continue

        try:
            deployment_dt = datetime.fromisoformat(
                deployment_date_str.replace("Z", "+00:00")
            )
            week_label = get_year_week_label(deployment_dt)

            if week_label in weekly_stats:
                week_groups[week_label].append(lt["lead_time_hours"])
        except (ValueError, KeyError):
            continue

    # Calculate statistics for each week
    for week_label in week_labels:
        hours_list = week_groups.get(week_label, [])
        if not hours_list:
            continue

        weekly_stats[week_label]["count"] = len(hours_list)
        weekly_stats[week_label]["median_hours"] = round(
            statistics.median(hours_list), 2
        )
        weekly_stats[week_label]["mean_hours"] = round(statistics.mean(hours_list), 2)

        if len(hours_list) >= 4:
            weekly_stats[week_label]["p75_hours"] = round(
                statistics.quantiles(hours_list, n=4)[2], 2
            )

        if len(hours_list) >= 10:
            weekly_stats[week_label]["p90_hours"] = round(
                statistics.quantiles(hours_list, n=10)[8], 2
            )

    logger.info(
        f"Weekly lead time aggregated for {sum(1 for s in weekly_stats.values() if s['count'] > 0)} weeks"
    )
    return weekly_stats


def aggregate_change_failure_rate_weekly(
    operational_tasks: List,
    completion_statuses: List[str],
    change_failure_field: str,
    week_labels: List[str],
    case_sensitive: bool = False,
) -> Dict[str, Dict]:
    """
    Aggregate change failure rate by ISO week (percentage).

    Calculates percentage of failed deployments per week.

    Args:
        operational_tasks: List of operational task issue objects
        completion_statuses: List of completion status names
        change_failure_field: Custom field ID for change failure indicator
        week_labels: List of year-week labels to aggregate
        case_sensitive: Whether to match status names case-sensitively

    Returns:
        Dictionary mapping week labels to failure statistics

    Example:
        >>> aggregate_change_failure_rate_weekly(op_tasks, ["Done"], "customfield_10001", ["2025-43"])
        {
            "2025-43": {
                "failure_rate_percent": 8.3,
                "total_deployments": 12,
                "failed_deployments": 1
            }
        }
    """
    from data.time_period_calculator import get_year_week_label
    from datetime import datetime, date
    from collections import defaultdict

    logger.info(f"Aggregating change failure rate for {len(week_labels)} weeks")

    # Initialize result
    weekly_stats = {
        label: {
            "failure_rate_percent": 0.0,
            "total_deployments": 0,
            "failed_deployments": 0,
        }
        for label in week_labels
    }

    if not operational_tasks or not completion_statuses:
        logger.warning(
            "aggregate_change_failure_rate_weekly: No operational tasks or completion statuses provided"
        )
        return weekly_stats

    # Convert statuses for case-insensitive matching
    completion_statuses_lower = (
        [s.lower() for s in completion_statuses] if not case_sensitive else []
    )

    # Group by week
    week_totals = defaultdict(int)
    week_failures = defaultdict(int)

    today = date.today()

    for task in operational_tasks:
        try:
            # Check completion status - handle dict format
            fields = task.get("fields", {})
            status_obj = fields.get("status", {})

            if not status_obj:
                continue

            task_status_name = (
                status_obj.get("name")
                if isinstance(status_obj, dict)
                else getattr(status_obj, "name", None)
            )
            if not task_status_name:
                continue

            status_match = (
                task_status_name in completion_statuses
                if case_sensitive
                else task_status_name.lower() in completion_statuses_lower
            )

            if not status_match:
                continue

            # Get deployment date from fixVersion releaseDate
            fixversions = fields.get("fixVersions", [])
            if not fixversions:
                continue

            deployed_versions = []
            for fv in fixversions:
                if isinstance(fv, dict):
                    release_date_str = fv.get("releaseDate")
                    if (
                        release_date_str
                        and datetime.strptime(release_date_str, "%Y-%m-%d").date()
                        <= today
                    ):
                        deployed_versions.append(fv)
                elif hasattr(fv, "releaseDate") and fv.releaseDate:
                    if datetime.strptime(fv.releaseDate, "%Y-%m-%d").date() <= today:
                        deployed_versions.append(fv)

            if not deployed_versions:
                continue

            def get_release_date(fv):
                if isinstance(fv, dict):
                    return fv.get("releaseDate", "")
                return getattr(fv, "releaseDate", "")

            earliest_release = min(
                deployed_versions, key=lambda fv: get_release_date(fv)
            )
            release_date_str = get_release_date(earliest_release)
            deployment_dt = datetime.strptime(release_date_str, "%Y-%m-%d")
            week_label = get_year_week_label(deployment_dt)

            if week_label not in weekly_stats:
                continue

            # Count total deployment
            week_totals[week_label] += 1

            # Check if failed
            failure_value = fields.get(change_failure_field)
            if failure_value and str(failure_value).strip().lower() == "yes":
                week_failures[week_label] += 1

        except (AttributeError, ValueError):
            continue

    # Calculate percentages
    for week_label in week_labels:
        total = week_totals.get(week_label, 0)
        failures = week_failures.get(week_label, 0)

        weekly_stats[week_label]["total_deployments"] = total
        weekly_stats[week_label]["failed_deployments"] = failures

        if total > 0:
            weekly_stats[week_label]["failure_rate_percent"] = round(
                (failures / total) * 100, 1
            )

    logger.info(
        f"Weekly change failure rate aggregated for {len([s for s in weekly_stats.values() if s['total_deployments'] > 0])} weeks"
    )
    return weekly_stats


def aggregate_mttr_weekly(
    mttr_data: List[Dict], week_labels: List[str]
) -> Dict[str, Dict]:
    """
    Aggregate MTTR by ISO week using median (not mean).

    Groups MTTR times by week and calculates median, mean, and percentiles.

    Args:
        mttr_data: List of MTTR dictionaries from calculate_mttr_v2
        week_labels: List of year-week labels to aggregate

    Returns:
        Dictionary mapping week labels to statistics

    Example:
        >>> aggregate_mttr_weekly(mttr_data, ["2025-43", "2025-44"])
        {
            "2025-43": {"median_hours": 6.5, "mean_hours": 8.2, "count": 3},
            "2025-44": {"median_hours": 4.8, "mean_hours": 5.1, "count": 2}
        }
    """
    from data.time_period_calculator import get_year_week_label
    from datetime import datetime
    import statistics

    logger.info(f"Aggregating MTTR for {len(week_labels)} weeks")

    # Initialize result
    weekly_stats = {
        label: {
            "median_hours": None,
            "mean_hours": None,
            "p75_hours": None,
            "p90_hours": None,
            "count": 0,
        }
        for label in week_labels
    }

    if not mttr_data:
        logger.warning("aggregate_mttr_weekly: No MTTR data provided")
        return weekly_stats

    # Group by week
    from collections import defaultdict

    week_groups = defaultdict(list)

    for mttr in mttr_data:
        fix_deployed_str = mttr.get("fix_deployed")
        if not fix_deployed_str:
            continue

        try:
            fix_dt = datetime.fromisoformat(fix_deployed_str.replace("Z", "+00:00"))
            week_label = get_year_week_label(fix_dt)

            if week_label in weekly_stats:
                week_groups[week_label].append(mttr["recovery_hours"])
        except (ValueError, KeyError):
            continue

    # Calculate statistics for each week
    for week_label in week_labels:
        hours_list = week_groups.get(week_label, [])
        if not hours_list:
            continue

        weekly_stats[week_label]["count"] = len(hours_list)
        weekly_stats[week_label]["median_hours"] = round(
            statistics.median(hours_list), 2
        )
        weekly_stats[week_label]["mean_hours"] = round(statistics.mean(hours_list), 2)

        if len(hours_list) >= 4:
            weekly_stats[week_label]["p75_hours"] = round(
                statistics.quantiles(hours_list, n=4)[2], 2
            )

        if len(hours_list) >= 10:
            weekly_stats[week_label]["p90_hours"] = round(
                statistics.quantiles(hours_list, n=10)[8], 2
            )

    logger.info(
        f"Weekly MTTR aggregated for {sum(1 for s in weekly_stats.values() if s['count'] > 0)} weeks"
    )
    return weekly_stats
