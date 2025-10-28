"""DORA metrics calculator.

Calculates the four DORA metrics from Jira issue data:
- Deployment Frequency
- Lead Time for Changes
- Change Failure Rate
- Mean Time to Recovery

This module contains pure business logic with no UI dependencies.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


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


def _parse_datetime(date_string: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string to datetime object.

    Args:
        date_string: ISO format datetime string

    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not date_string:
        return None

    try:
        # Handle Jira datetime format (ISO 8601)
        return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
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
) -> Dict[str, Any]:
    """Calculate deployment frequency metric.

    Args:
        issues: List of deployment issue dictionaries from Jira
        field_mappings: Mapping of internal fields to Jira field IDs
        time_period_days: Time period for calculation (default 30 days)

    Returns:
        Metric data dictionary with value, unit, performance tier, and metadata
    """
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
            "excluded_issue_count": 0,
        }

    deployment_date_field = field_mappings["deployment_date"]
    deployment_successful_field = field_mappings.get("deployment_successful")

    # Calculate time period boundaries
    end_date = datetime.now()
    start_date = end_date - timedelta(days=time_period_days)

    # Filter and parse deployments
    valid_deployments = []
    excluded_count = 0

    for issue in issues:
        fields = issue.get("fields", {})

        # Parse deployment date
        deployment_date_str = fields.get(deployment_date_field)
        deployment_date = _parse_datetime(deployment_date_str)

        if not deployment_date:
            excluded_count += 1
            continue

        # Check if deployment is in time period
        if not (start_date <= deployment_date <= end_date):
            excluded_count += 1
            continue

        # Check if deployment was successful (if field is mapped)
        if deployment_successful_field:
            was_successful = fields.get(deployment_successful_field)
            if not was_successful:
                excluded_count += 1
                continue

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
            "excluded_issue_count": excluded_count,
        }

    # Calculate deployment frequency (normalize to per-month)
    deployment_count = len(valid_deployments)
    deployments_per_month = (deployment_count / time_period_days) * 30

    # Determine performance tier
    tier_info = _determine_performance_tier(
        deployments_per_month, DEPLOYMENT_FREQUENCY_TIERS
    )

    return {
        "metric_name": "deployment_frequency",
        "value": round(deployments_per_month, 1),
        "unit": "deployments/month",
        "error_state": "success",
        "error_message": None,
        "performance_tier": tier_info["tier"],
        "performance_tier_color": tier_info["color"],
        "total_issue_count": len(issues),
        "excluded_issue_count": excluded_count,
        "calculation_timestamp": datetime.now().isoformat(),
        "time_period_start": start_date.isoformat(),
        "time_period_end": end_date.isoformat(),
    }


def calculate_lead_time_for_changes(
    issues: List[Dict[str, Any]],
    field_mappings: Dict[str, str],
) -> Dict[str, Any]:
    """Calculate lead time for changes metric.

    Args:
        issues: List of change issue dictionaries from Jira
        field_mappings: Mapping of internal fields to Jira field IDs

    Returns:
        Metric data dictionary with value, unit, performance tier, and metadata
    """
    # Check for required field mappings
    required_fields = ["code_commit_date", "deployed_to_production_date"]
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
        }

    commit_date_field = field_mappings["code_commit_date"]
    deploy_date_field = field_mappings["deployed_to_production_date"]

    # Calculate lead times
    lead_times = []
    excluded_count = 0

    for issue in issues:
        fields = issue.get("fields", {})

        # Parse dates
        commit_date = _parse_datetime(fields.get(commit_date_field))
        deploy_date = _parse_datetime(fields.get(deploy_date_field))

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
        return {
            "metric_name": "lead_time_for_changes",
            "value": None,
            "unit": "days",
            "error_state": "no_data",
            "error_message": "No changes with valid commit and deployment dates",
            "performance_tier": None,
            "performance_tier_color": None,
            "total_issue_count": len(issues),
            "excluded_issue_count": excluded_count,
        }

    # Calculate average lead time
    avg_lead_time = sum(lead_times) / len(lead_times)

    # Determine performance tier
    tier_info = _determine_performance_tier(avg_lead_time, LEAD_TIME_TIERS)

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
    }


def calculate_change_failure_rate(
    deployment_issues: List[Dict[str, Any]],
    incident_issues: List[Dict[str, Any]],
    field_mappings: Dict[str, str],
) -> Dict[str, Any]:
    """Calculate change failure rate metric.

    Args:
        deployment_issues: List of deployment issue dictionaries from Jira
        incident_issues: List of incident issue dictionaries from Jira
        field_mappings: Mapping of internal fields to Jira field IDs

    Returns:
        Metric data dictionary with value, unit, performance tier, and metadata
    """
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
        }

    # Count total deployments
    deployment_count = len(deployment_issues)

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
        }

    # Count production incidents
    production_impact_field = field_mappings.get("production_impact")
    incident_count = 0
    excluded_count = 0

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

    # Calculate failure rate percentage
    failure_rate = (incident_count / deployment_count) * 100

    # Determine performance tier
    tier_info = _determine_performance_tier(failure_rate, CHANGE_FAILURE_RATE_TIERS)

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
            "incident_count": incident_count,
        },
    }


def calculate_mean_time_to_recovery(
    issues: List[Dict[str, Any]],
    field_mappings: Dict[str, str],
) -> Dict[str, Any]:
    """Calculate mean time to recovery (MTTR) metric.

    Args:
        issues: List of incident issue dictionaries from Jira
        field_mappings: Mapping of internal fields to Jira field IDs

    Returns:
        Metric data dictionary with value, unit, performance tier, and metadata
    """
    # Check for required field mappings
    required_fields = ["incident_detected_at", "incident_resolved_at"]
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
        }

    detected_field = field_mappings["incident_detected_at"]
    resolved_field = field_mappings["incident_resolved_at"]

    # Calculate recovery times
    recovery_times = []
    excluded_count = 0

    for issue in issues:
        fields = issue.get("fields", {})

        # Parse dates
        detected_at = _parse_datetime(fields.get(detected_field))
        resolved_at = _parse_datetime(fields.get(resolved_field))

        if not detected_at or not resolved_at:
            # Skip unresolved incidents or missing data
            excluded_count += 1
            continue

        # Calculate recovery time in hours
        recovery_delta = resolved_at - detected_at
        recovery_hours = recovery_delta.total_seconds() / 3600  # Convert to hours

        if recovery_hours < 0:
            # Skip invalid data (resolved before detected)
            excluded_count += 1
            logger.warning(
                f"Issue {issue.get('key')}: resolved date before detected date"
            )
            continue

        recovery_times.append(recovery_hours)

    # Handle no data case
    if not recovery_times:
        return {
            "metric_name": "mean_time_to_recovery",
            "value": None,
            "unit": "hours",
            "error_state": "no_data",
            "error_message": "No resolved incidents found for calculation",
            "performance_tier": None,
            "performance_tier_color": None,
            "total_issue_count": len(issues),
            "excluded_issue_count": excluded_count,
        }

    # Calculate average recovery time
    avg_recovery_time = sum(recovery_times) / len(recovery_times)

    # Determine performance tier
    tier_info = _determine_performance_tier(avg_recovery_time, MTTR_TIERS)

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
