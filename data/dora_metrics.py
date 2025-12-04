"""Modern DORA metrics calculator using field mappings.

Calculates the four DORA (DevOps Research and Assessment) metrics:
- Deployment Frequency: How often code is deployed to production
- Lead Time for Changes: Time from code commit to production deployment
- Change Failure Rate: Percentage of deployments causing incidents
- Mean Time to Recovery: Time to restore service after incidents

Note: Per official DORA methodology (Google Four Keys), Lead Time and MTTR
use MEDIAN calculations for outlier resistance, even though MTTR's name
contains "Mean" for historical reasons.

This implementation uses field_mappings from user profile configuration.

Architecture:
- Pure business logic with no UI dependencies
- Uses user-configured field mappings (no hardcoded field names)
- Supports changelog extraction for datetime values (status:StatusName.DateTime)
- Consistent error handling and performance tier classification
- Comprehensive logging for debugging and monitoring

Reference: docs/dora_metrics_spec.md
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

from data.performance_utils import log_performance

logger = logging.getLogger(__name__)


def _get_field_mappings():
    """Load field mappings from app settings.

    Returns:
        Tuple of (dora_mappings, project_classification)
    """
    from data.persistence import load_app_settings

    app_settings = load_app_settings()
    field_mappings = app_settings.get("field_mappings", {})
    dora_mappings = field_mappings.get("dora", {})

    # Project classification is flattened to root level by load_app_settings
    # Reconstruct the nested structure for backward compatibility
    # Provide sensible defaults if not configured (for testing and new installations)
    default_flow_end_statuses = ["Done", "Resolved", "Closed"]
    default_flow_start_statuses = ["In Progress", "In Review"]
    default_wip_statuses = ["In Progress", "In Review", "In Development"]

    project_classification = {
        "flow_end_statuses": app_settings.get("flow_end_statuses")
        or default_flow_end_statuses,
        "active_statuses": app_settings.get("active_statuses", []),
        "wip_statuses": app_settings.get("wip_statuses") or default_wip_statuses,
        "flow_start_statuses": app_settings.get("flow_start_statuses")
        or default_flow_start_statuses,
        "bug_types": app_settings.get("bug_types", []),
        "devops_task_types": app_settings.get("devops_task_types", []),
        "production_environment_values": app_settings.get(
            "production_environment_values", []
        ),
    }

    return dora_mappings, project_classification


def _is_issue_completed(issue: Dict[str, Any], flow_end_statuses: List[str]) -> bool:
    """Check if issue is in a completed status.

    Args:
        issue: JIRA issue dictionary
        flow_end_statuses: List of status names that indicate completion

    Returns:
        True if issue status is in flow_end_statuses
    """
    status = issue.get("fields", {}).get("status", {}).get("name", "")
    return status in flow_end_statuses


def _extract_datetime_from_field_mapping(
    issue: Dict[str, Any], field_mapping: str, changelog: Optional[List] = None
) -> Optional[str]:
    """Extract datetime value from issue based on field mapping configuration.

    Supports multiple field mapping formats:
    - Simple field: "created", "resolutiondate"
    - Nested field: "status.name"
    - Changelog transition: "status:In Progress.DateTime" (extracts timestamp when status changed to "In Progress")
    - fixVersions: "fixVersions" (extracts releaseDate from first fixVersion)

    Args:
        issue: JIRA issue dictionary
        field_mapping: Field mapping string from profile.json (e.g., "status:Done.DateTime")
        changelog: Optional changelog history for transition timestamp extraction

    Returns:
        ISO datetime string if found, None otherwise
    """
    if not field_mapping:
        return None

    # Handle changelog transition format: "status:StatusName.DateTime"
    if ":" in field_mapping and ".DateTime" in field_mapping:
        # Extract field name and target status
        # Format: "status:In Progress.DateTime"
        parts = field_mapping.split(":")
        if len(parts) != 2:
            return None

        field_name = parts[0]  # "status"
        status_datetime = parts[1]  # "In Progress.DateTime"
        target_status = status_datetime.replace(".DateTime", "")  # "In Progress"

        # Search changelog for transition to target status
        if changelog is None:
            changelog = issue.get("changelog", {}).get("histories", [])

        if not isinstance(changelog, list):
            return None

        for history in changelog:
            for item in history.get("items", []):
                if (
                    item.get("field") == field_name
                    and item.get("toString") == target_status
                ):
                    return history.get("created")  # Return transition timestamp

        return None

    # Handle fixVersions special case
    if field_mapping == "fixVersions":
        fix_versions = issue.get("fields", {}).get("fixVersions", [])
        for fv in fix_versions:
            release_date = fv.get("releaseDate")
            if release_date:
                return release_date
        return None

    # Handle simple and nested field paths
    fields = issue.get("fields", {})
    if "." in field_mapping:
        # Nested field like "status.name"
        parts = field_mapping.split(".")
        value = fields
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value if isinstance(value, str) else None
    else:
        # Simple field like "created", "resolutiondate"
        return fields.get(field_mapping)


def parse_field_value_filter(field_mapping: str) -> tuple:
    """Parse field=Value syntax from field mapping.

    Supports:
    - Simple field: "customfield_11309" → ("customfield_11309", None)
    - Single value: "customfield_11309=PROD" → ("customfield_11309", ["PROD"])
    - Multiple values: "customfield_11309=PROD|Production" → ("customfield_11309", ["PROD", "Production"])

    Args:
        field_mapping: Field mapping string, optionally with =Value filter

    Returns:
        Tuple of (field_id, filter_values)
        - field_id: The field ID to check
        - filter_values: List of values to match, or None if no filter
    """
    if not field_mapping:
        return None, None

    if "=" in field_mapping:
        parts = field_mapping.split("=", 1)
        field_id = parts[0].strip()
        value_str = parts[1].strip()
        # Support | separator for multiple values
        filter_values = [v.strip() for v in value_str.split("|") if v.strip()]
        return field_id, filter_values if filter_values else None
    else:
        return field_mapping, None


def check_field_value_match(
    issue: Dict[str, Any], field_id: str, filter_values: List[str]
) -> bool:
    """Check if issue field value matches any of the filter values.

    Handles various JIRA field types:
    - String: Direct comparison
    - Dict (select): Check 'value' or 'name' keys
    - List (multi-select): Check if any item matches

    Args:
        issue: JIRA issue dictionary
        field_id: Field ID to check (e.g., "customfield_11309")
        filter_values: List of values to match (e.g., ["PROD", "Production"])

    Returns:
        True if any filter value matches the field value
    """
    if not filter_values:
        return True  # No filter means all pass

    field_value = issue.get("fields", {}).get(field_id)

    if field_value is None:
        return False

    # Normalize filter values to lowercase for case-insensitive matching
    filter_values_lower = [v.lower() for v in filter_values]

    # Handle string field
    if isinstance(field_value, str):
        return field_value.lower() in filter_values_lower

    # Handle dict field (single select)
    if isinstance(field_value, dict):
        value_str = field_value.get("value", "") or field_value.get("name", "")
        return value_str.lower() in filter_values_lower

    # Handle list field (multi-select)
    if isinstance(field_value, list):
        for item in field_value:
            if isinstance(item, str):
                if item.lower() in filter_values_lower:
                    return True
            elif isinstance(item, dict):
                item_str = item.get("value", "") or item.get("name", "")
                if item_str.lower() in filter_values_lower:
                    return True

    return False


def is_production_environment(
    issue: Dict[str, Any],
    affected_environment_mapping: str,
    fallback_values: Optional[List[str]] = None,
) -> bool:
    """Check if issue is from production environment.

    Uses the =Value syntax in affected_environment field mapping.
    Falls back to production_environment_values if no =Value specified.

    Args:
        issue: JIRA issue dictionary
        affected_environment_mapping: Field mapping (e.g., "customfield_11309=PROD")
        fallback_values: Fallback list of production values (from project_classification)

    Returns:
        True if issue is from production environment
    """
    if not affected_environment_mapping:
        return True  # No filter configured, include all

    field_id, filter_values = parse_field_value_filter(affected_environment_mapping)

    if field_id is None:
        return True

    # If =Value syntax used, apply that filter
    if filter_values:
        return check_field_value_match(issue, field_id, filter_values)

    # Fallback to production_environment_values list
    if fallback_values:
        return check_field_value_match(issue, field_id, fallback_values)

    # No filter values at all - include all
    return True


# DORA performance tier thresholds (based on industry research)
DEPLOYMENT_FREQUENCY_TIERS = {
    "elite": {"threshold": 0.9, "unit": "per day", "label": "Multiple deploys per day"},
    "high": {"threshold": 0.13, "unit": "per day", "label": "Daily to weekly"},
    "medium": {"threshold": 0.033, "unit": "per day", "label": "Weekly to monthly"},
    "low": {"threshold": 0, "unit": "per day", "label": "Less than monthly"},
}

LEAD_TIME_TIERS = {
    "elite": {"threshold": 1, "unit": "days", "label": "Less than 1 day"},
    "high": {"threshold": 7, "unit": "days", "label": "1-7 days"},
    "medium": {"threshold": 30, "unit": "days", "label": "1 week to 1 month"},
    "low": {"threshold": float("inf"), "unit": "days", "label": "More than 1 month"},
}

CHANGE_FAILURE_RATE_TIERS = {
    "elite": {"threshold": 15, "unit": "%", "label": "0-15%"},
    "high": {"threshold": 30, "unit": "%", "label": "16-30%"},
    "medium": {"threshold": 45, "unit": "%", "label": "31-45%"},
    "low": {"threshold": 100, "unit": "%", "label": "More than 45%"},
}

MTTR_TIERS = {
    "elite": {"threshold": 1, "unit": "hours", "label": "Less than 1 hour"},
    "high": {"threshold": 24, "unit": "hours", "label": "Less than 1 day"},
    "medium": {"threshold": 168, "unit": "hours", "label": "1-7 days"},
    "low": {"threshold": float("inf"), "unit": "hours", "label": "More than 1 week"},
}


def _classify_performance_tier(
    value: float, tiers: Dict, higher_is_better: bool = True
) -> str:
    """Classify metric value into DORA performance tier.

    Args:
        value: Metric value to classify
        tiers: Tier definitions with thresholds
        higher_is_better: True if higher values = better performance (e.g., deployment frequency)
                         False if lower values = better (e.g., lead time, MTTR)

    Returns:
        Performance tier: "elite", "high", "medium", or "low"
    """
    if higher_is_better:
        # Higher values are better (deployment frequency)
        if value >= tiers["elite"]["threshold"]:
            return "elite"
        elif value >= tiers["high"]["threshold"]:
            return "high"
        elif value >= tiers["medium"]["threshold"]:
            return "medium"
        else:
            return "low"
    else:
        # Lower values are better (lead time, CFR, MTTR)
        if value <= tiers["elite"]["threshold"]:
            return "elite"
        elif value <= tiers["high"]["threshold"]:
            return "high"
        elif value <= tiers["medium"]["threshold"]:
            return "medium"
        else:
            return "low"


def _determine_performance_tier(value: Optional[float], tiers: Dict) -> Dict[str, str]:
    """Determine performance tier with color for UI display (legacy compatibility).

    This function maintains backward compatibility with existing callback code.

    Args:
        value: Metric value to classify (None = unknown)
        tiers: Tier definitions with thresholds

    Returns:
        Dictionary with tier and color:
        {
            "tier": "Elite" | "High" | "Medium" | "Low" | "Unknown",
            "color": "success" | "info" | "warning" | "danger" | "secondary"
        }
    """
    if value is None:
        return {"tier": "Unknown", "color": "secondary"}

    # Determine if higher is better by checking tier thresholds
    higher_is_better = tiers["elite"]["threshold"] > tiers["low"]["threshold"]

    tier = _classify_performance_tier(value, tiers, higher_is_better)

    # Map tier to color for UI
    tier_colors = {
        "elite": "success",
        "high": "info",
        "medium": "warning",
        "low": "danger",
    }

    return {
        "tier": tier.capitalize(),
        "color": tier_colors.get(tier, "secondary"),
    }


def _calculate_trend(
    current_value: float, previous_value: Optional[float]
) -> Dict[str, Any]:
    """Calculate trend direction and percentage change.

    Args:
        current_value: Current period metric value
        previous_value: Previous period metric value (None if unavailable)

    Returns:
        Dictionary with trend information:
        {
            "trend_direction": "up" | "down" | "stable",
            "trend_percentage": float (percentage change)
        }
    """
    if previous_value is None or previous_value == 0:
        return {"trend_direction": "stable", "trend_percentage": 0.0}

    percentage_change = ((current_value - previous_value) / previous_value) * 100

    # Consider changes < 5% as "stable"
    if abs(percentage_change) < 5.0:
        return {"trend_direction": "stable", "trend_percentage": percentage_change}

    return {
        "trend_direction": "up" if percentage_change > 0 else "down",
        "trend_percentage": percentage_change,
    }


@log_performance
def calculate_deployment_frequency(
    issues: List[Dict[str, Any]],
    time_period_days: int = 30,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate deployment frequency metric.

    Measures how often code is deployed to production:
    - Deployments: Count of operational tasks with fixVersion.releaseDate in period
    - Releases: Count of DISTINCT fixVersions with releaseDate in period

    Multiple deployments (operational tasks) can share one release (fixVersion).

    Args:
        issues: List of JIRA issues (operational tasks) to analyze
        time_period_days: Number of days in measurement period (default: 30)
        previous_period_value: Optional previous period value for trend calculation

    Returns:
        Dictionary with deployment frequency metrics:
        {
            "value": float,  # Deployments per week (primary metric)
            "deployments_per_week": float,
            "releases_per_week": float,
            "unit": "deployments/week",
            "performance_tier": "elite" | "high" | "medium" | "low",
            "deployment_count": int,  # Total operational tasks
            "release_count": int,  # Distinct fixVersions
            "release_names": List[str],  # Names of releases
            "period_days": int,
            "trend_direction": "up" | "down" | "stable",
            "trend_percentage": float
        }

        On error:
        {
            "error_state": "missing_mapping" | "no_data" | "calculation_error",
            "error_message": str,
            "trend_direction": "stable",
            "trend_percentage": 0.0
        }
    """
    try:
        if not issues:
            return {
                "error_state": "no_data",
                "error_message": "No issues provided for analysis",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Get field mappings from profile
        dora_mappings, project_classification = _get_field_mappings()
        flow_end_statuses = project_classification.get(
            "flow_end_statuses", ["Done", "Resolved", "Closed"]
        )

        # Count deployments (operational tasks) and releases (distinct fixVersions)
        deployment_count = 0
        all_releases = set()  # Track distinct fixVersion names

        for issue in issues:
            fields = issue.get("fields", {})

            # Check if issue is completed
            if not _is_issue_completed(issue, flow_end_statuses):
                continue

            # Check if issue has fixVersion with releaseDate
            fix_versions = fields.get("fixVersions", [])
            has_release_date = False

            for fv in fix_versions:
                if fv.get("releaseDate"):
                    has_release_date = True
                    release_name = fv.get("name", "")
                    if release_name:
                        all_releases.add(release_name)

            if has_release_date:
                deployment_count += 1
                logger.debug(
                    f"[DORA] Issue {issue.get('key')} counted as deployment: "
                    f"type={fields.get('issuetype', {}).get('name')}, "
                    f"fixVersions={[v.get('name') for v in fix_versions if v.get('releaseDate')]}"
                )

        if deployment_count == 0:
            return {
                "error_state": "no_data",
                "error_message": f"No completed deployments with fixVersion.releaseDate found in {len(issues)} issues",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Calculate frequencies
        release_count = len(all_releases)
        weeks = time_period_days / 7.0

        deployments_per_week = deployment_count / weeks if weeks > 0 else 0
        releases_per_week = release_count / weeks if weeks > 0 else 0
        deployments_per_day = deployment_count / time_period_days

        # Determine best display unit based on frequency
        if deployments_per_day >= 0.9:
            unit = "deployments/day"
            display_value = deployments_per_day
        elif deployments_per_day >= 0.13:
            unit = "deployments/week"
            display_value = deployments_per_week
        else:
            unit = "deployments/month"
            display_value = deployments_per_day * 30

        # Classify performance tier based on deployments per day
        performance_tier = _classify_performance_tier(
            deployments_per_day, DEPLOYMENT_FREQUENCY_TIERS, higher_is_better=True
        )

        # Calculate trend
        trend = _calculate_trend(deployments_per_day, previous_period_value)

        logger.info(
            f"[DORA] Deployment Frequency: {display_value:.1f} {unit} "
            f"({deployment_count} deployments, {release_count} releases / {time_period_days} days) - {performance_tier}"
        )
        logger.debug(f"[DORA] Releases: {sorted(all_releases)}")

        return {
            "value": display_value,
            "deployments_per_week": deployments_per_week,
            "releases_per_week": releases_per_week,
            "unit": unit,
            "performance_tier": performance_tier,
            "deployment_count": deployment_count,
            "release_count": release_count,
            "release_names": sorted(all_releases),
            "period_days": time_period_days,
            **trend,
        }

    except Exception as e:
        logger.error(
            f"[DORA] Deployment frequency calculation failed: {e}", exc_info=True
        )
        return {
            "error_state": "calculation_error",
            "error_message": str(e),
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }


@log_performance
def calculate_lead_time_for_changes(
    issues: List[Dict[str, Any]],
    time_period_days: int = 30,
    previous_period_value: Optional[float] = None,
    fixversion_release_map: Optional[Dict[str, datetime]] = None,
) -> Dict[str, Any]:
    """Calculate lead time for changes metric.

    Measures time from code commit (status:In Progress) to production deployment
    (fixVersion.releaseDate from matching Operational Task).

    IMPORTANT: Lead Time uses the SAME deployment date logic as Deployment Frequency:
    - Development issues link to Operational Tasks via shared fixVersions
    - Deployment date = fixVersion.releaseDate from the Operational Task
    - fixversion_release_map is built once and reused across metrics (DRY)

    Args:
        issues: List of development issues to analyze
        time_period_days: Number of days in measurement period (default: 30)
        previous_period_value: Optional previous period value for trend calculation
        fixversion_release_map: Map of fixVersion name → releaseDate datetime
            Built from Operational Tasks via build_fixversion_release_map()

    Returns:
        Dictionary with lead time metrics:
        {
            "value": float,  # Average lead time in days
            "unit": "days" | "hours",
            "performance_tier": "elite" | "high" | "medium" | "low",
            "sample_count": int,
            "period_days": int,
            "trend_direction": "up" | "down" | "stable",
            "trend_percentage": float
        }

        On error:
        {
            "error_state": "missing_mapping" | "no_data" | "calculation_error",
            "error_message": str,
            "trend_direction": "stable",
            "trend_percentage": 0.0
        }
    """
    try:
        if not issues:
            return {
                "error_state": "no_data",
                "error_message": "No issues provided for analysis",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Import shared fixversion lookup function
        from data.fixversion_matcher import get_deployment_date_for_issue

        # Extract lead times
        lead_times = []
        missing_start_count = 0
        missing_deployment_count = 0
        no_fixversion_match_count = 0

        # Get field mappings from profile configuration
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        field_mappings = app_settings.get("field_mappings", {})
        dora_mappings = field_mappings.get("dora", {})

        code_commit_field = dora_mappings.get("code_commit_date", "created")

        for issue in issues:
            issue_key = issue.get("key", "UNKNOWN")

            # Extract changelog if present
            changelog = issue.get("changelog", {}).get("histories", [])

            # Extract work start timestamp using field mapping (e.g., status:In Progress.DateTime)
            work_start_value = _extract_datetime_from_field_mapping(
                issue, code_commit_field, changelog
            )
            if not work_start_value:
                missing_start_count += 1
                continue

            # Get deployment date from fixVersion release map (shared with Deployment Frequency)
            if fixversion_release_map:
                deployment_datetime = get_deployment_date_for_issue(
                    issue, fixversion_release_map
                )
                if not deployment_datetime:
                    no_fixversion_match_count += 1
                    logger.debug(
                        f"[Lead Time] {issue_key}: No matching fixVersion in release map"
                    )
                    continue
            else:
                # Fallback: Try to extract from issue's own fixVersions (legacy behavior)
                deployment_value = _extract_datetime_from_field_mapping(
                    issue, "fixVersions", changelog
                )
                if not deployment_value:
                    missing_deployment_count += 1
                    continue
                try:
                    deployment_datetime = datetime.fromisoformat(
                        deployment_value.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    missing_deployment_count += 1
                    continue

            try:
                start_time = datetime.fromisoformat(
                    work_start_value.replace("Z", "+00:00")
                )

                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                if deployment_datetime.tzinfo is None:
                    deployment_datetime = deployment_datetime.replace(
                        tzinfo=timezone.utc
                    )

                # Calculate lead time in days
                lead_time_delta = deployment_datetime - start_time
                lead_time_days = (
                    lead_time_delta.total_seconds() / 86400
                )  # 86400 seconds per day

                if lead_time_days < 0:
                    logger.warning(
                        f"[DORA] Negative lead time for {issue_key}: "
                        f"start={start_time}, deployment={deployment_datetime}"
                    )
                    continue

                lead_times.append(lead_time_days)
                logger.debug(
                    f"[Lead Time] {issue_key}: {lead_time_days:.1f} days "
                    f"(start={start_time.date()}, deploy={deployment_datetime.date()})"
                )

            except (ValueError, TypeError) as e:
                logger.warning(f"[DORA] Invalid timestamp for {issue_key}: {e}")
                continue

        if not lead_times:
            error_details = []
            if missing_start_count:
                error_details.append(f"missing start: {missing_start_count}")
            if no_fixversion_match_count:
                error_details.append(
                    f"no fixVersion match: {no_fixversion_match_count}"
                )
            if missing_deployment_count:
                error_details.append(f"missing deployment: {missing_deployment_count}")

            return {
                "error_state": "no_data",
                "error_message": f"No valid lead times from {len(issues)} issues "
                f"({', '.join(error_details)})",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
                # Backward compatibility fields for metrics_calculator
                "median_hours": 0,
                "mean_hours": 0,
                "p95_hours": 0,
                "issues_with_lead_time": 0,
            }

        # Calculate statistics in hours for backward compatibility
        import statistics

        lead_times_hours = [lt * 24 for lt in lead_times]
        median_hours = statistics.median(lead_times_hours)
        mean_hours = statistics.mean(lead_times_hours)
        p95_hours = (
            sorted(lead_times_hours)[int(len(lead_times_hours) * 0.95)]
            if len(lead_times_hours) >= 2
            else mean_hours
        )

        # Use MEDIAN per official DORA methodology (outlier resistant)
        median_lead_time_days = median_hours / 24

        # Determine display unit
        if median_lead_time_days < 1:
            unit = "hours"
            display_value = median_hours
        else:
            unit = "days"
            display_value = median_lead_time_days

        # Classify performance tier (lower is better)
        performance_tier = _classify_performance_tier(
            median_lead_time_days, LEAD_TIME_TIERS, higher_is_better=False
        )

        # Calculate trend
        trend = _calculate_trend(median_lead_time_days, previous_period_value)

        logger.info(
            f"[DORA] Lead Time for Changes: {display_value:.1f} {unit} "
            f"({len(lead_times)} issues) - {performance_tier}"
        )

        return {
            "value": display_value,
            "unit": unit,
            "value_hours": median_hours,
            "value_days": median_lead_time_days,
            "performance_tier": performance_tier,
            "sample_count": len(lead_times),
            "period_days": time_period_days,
            # Additional statistics for analysis
            "median_hours": median_hours,
            "mean_hours": mean_hours,
            "p95_hours": p95_hours,
            "issues_with_lead_time": len(lead_times),
            **trend,
        }

    except Exception as e:
        logger.error(f"[DORA] Lead time calculation failed: {e}", exc_info=True)
        return {
            "error_state": "calculation_error",
            "error_message": str(e),
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }


@log_performance
def calculate_change_failure_rate(
    deployment_issues: List[Dict[str, Any]],
    incident_issues: List[Dict[str, Any]],
    time_period_days: int = 30,
    previous_period_value: Optional[float] = None,
    valid_fix_versions: Optional[set] = None,
) -> Dict[str, Any]:
    """Calculate change failure rate metric.

    Measures percentage of deployments that cause incidents requiring remediation.
    Elite teams have failure rates under 15%, while low performers exceed 45%.

    Args:
        deployment_issues: List of deployment/operational task issues
        incident_issues: List of incident/bug issues (kept for backward compatibility, not used)
        time_period_days: Number of days in measurement period (default: 30)
        previous_period_value: Optional previous period value for trend calculation
        valid_fix_versions: Set of fixVersion names from development projects.
            If provided, only count Operational Tasks with matching fixVersions.

    Returns:
        Dictionary with change failure rate metrics:
        {
            "value": float,  # Failure rate percentage (0-100)
            "unit": "%",
            "performance_tier": "elite" | "high" | "medium" | "low",
            "total_deployments": int,
            "failed_deployments": int,
            "total_releases": int,
            "failed_releases": int,
            "release_names": List[str],
            "failed_release_names": List[str],
            "period_days": int,
            "trend_direction": "up" | "down" | "stable",
            "trend_percentage": float
        }

        On error:
        {
            "error_state": "missing_mapping" | "no_data" | "calculation_error",
            "error_message": str,
            "trend_direction": "stable",
            "trend_percentage": 0.0
        }
    """
    try:
        # Check for empty input first (before configuration check)
        if not deployment_issues:
            return {
                "error_state": "no_data",
                "error_message": "No deployment issues provided",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Get field mappings from profile
        dora_mappings, project_classification = _get_field_mappings()

        # Get change_failure field from profile (e.g., "customfield_12708" or "customfield_12708=Yes")
        change_failure_mapping = dora_mappings.get("change_failure")
        if not change_failure_mapping:
            return {
                "error_state": "missing_mapping",
                "error_message": "change_failure field not configured in profile.json field_mappings.dora",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Parse field mapping - support "field=value" syntax for configurable failure values
        # Default positive values if no specific value is configured
        change_failure_field = change_failure_mapping
        configured_failure_values = {"yes", "true", "1"}  # Default positive values

        if "=" in change_failure_mapping:
            # Configurable value syntax: "customfield_12708=Yes" or "customfield_12708=Yes|Ja|Oui"
            field_part, value_part = change_failure_mapping.split("=", 1)
            change_failure_field = field_part.strip()
            # Support multiple values separated by pipe: "Yes|Ja|Oui"
            configured_failure_values = {
                v.strip().lower() for v in value_part.split("|") if v.strip()
            }
            logger.info(
                f"[DORA CFR] Using configured failure values: {configured_failure_values}"
            )

        flow_end_statuses = project_classification.get(
            "flow_end_statuses", ["Done", "Resolved", "Closed"]
        )

        # Count deployments and track which have change_failure flag set
        # Also track releases (distinct fixVersions)
        total_deployments = 0
        failed_deployments = 0
        all_releases = set()  # Track all fixVersion names
        failed_releases = set()  # Track fixVersions that had failures

        for issue in deployment_issues:
            fields = issue.get("fields", {})

            # Check if issue is completed
            if not _is_issue_completed(issue, flow_end_statuses):
                continue

            # Check if issue has fixVersion with releaseDate (deployment date)
            fix_versions = fields.get("fixVersions", [])
            has_valid_release = False
            issue_releases = []

            for fv in fix_versions:
                if fv.get("releaseDate"):
                    release_name = fv.get("name", "")
                    if release_name:
                        # Filter: Only count if fixVersion exists in development projects
                        if (
                            valid_fix_versions
                            and release_name not in valid_fix_versions
                        ):
                            continue
                        has_valid_release = True
                        issue_releases.append(release_name)
                        all_releases.add(release_name)

            if not has_valid_release:
                continue

            total_deployments += 1

            # Check change_failure field from profile mapping
            # Handle both simple values and object values (e.g., {"value": "Yes"})
            change_failure_value = fields.get(change_failure_field)
            is_failure = False

            if change_failure_value is not None:
                if isinstance(change_failure_value, bool):
                    # Boolean fields: true means failure
                    is_failure = change_failure_value
                elif isinstance(change_failure_value, dict):
                    # Handle JIRA custom field objects like {"value": "Yes", "id": "123"}
                    val = change_failure_value.get("value", "")
                    is_failure = str(val).lower() in configured_failure_values
                elif isinstance(change_failure_value, str):
                    is_failure = (
                        change_failure_value.lower() in configured_failure_values
                    )
                elif isinstance(change_failure_value, (int, float)):
                    # Numeric fields: non-zero means failure, or check if matches configured value
                    is_failure = str(
                        int(change_failure_value)
                    ) in configured_failure_values or bool(change_failure_value)

            if is_failure:
                failed_deployments += 1
                # Mark these releases as having failures
                for release_name in issue_releases:
                    failed_releases.add(release_name)

                logger.debug(
                    f"[DORA] Issue {issue.get('key')} marked as causing production issue "
                    f"(change_failure={change_failure_value})"
                )

        if total_deployments == 0:
            return {
                "error_state": "no_data",
                "error_message": "No completed deployments with fixVersion.releaseDate found",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Calculate failure rates
        # CFR based on deployments (operational tasks)
        change_failure_rate = (failed_deployments / total_deployments) * 100

        # Also calculate release-level failure rate
        total_releases_count = len(all_releases)
        failed_releases_count = len(failed_releases)
        release_failure_rate = (
            (failed_releases_count / total_releases_count) * 100
            if total_releases_count > 0
            else 0
        )

        # Classify performance tier (lower is better)
        performance_tier = _classify_performance_tier(
            change_failure_rate, CHANGE_FAILURE_RATE_TIERS, higher_is_better=False
        )

        # Calculate trend
        trend = _calculate_trend(change_failure_rate, previous_period_value)

        logger.info(
            f"[DORA] Change Failure Rate: {change_failure_rate:.1f}% "
            f"({failed_deployments}/{total_deployments} deployments, "
            f"{failed_releases_count}/{total_releases_count} releases) - {performance_tier}"
        )

        return {
            "value": change_failure_rate,
            "change_failure_rate_percent": change_failure_rate,
            "unit": "%",
            "performance_tier": performance_tier,
            "total_deployments": total_deployments,
            "failed_deployments": failed_deployments,
            "total_releases": total_releases_count,
            "failed_releases": failed_releases_count,
            "release_failure_rate_percent": release_failure_rate,
            "release_names": sorted(list(all_releases)),
            "failed_release_names": sorted(list(failed_releases)),
            "period_days": time_period_days,
            **trend,
        }

    except Exception as e:
        logger.error(
            f"[DORA] Change failure rate calculation failed: {e}", exc_info=True
        )
        return {
            "error_state": "calculation_error",
            "error_message": str(e),
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }


@log_performance
def calculate_mean_time_to_recovery(
    incident_issues: List[Dict[str, Any]],
    time_period_days: int = 30,
    previous_period_value: Optional[float] = None,
    fixversion_release_map: Optional[Dict[str, datetime]] = None,
) -> Dict[str, Any]:
    """Calculate mean time to recovery metric.

    Measures average time to restore service after an incident. Elite teams
    recover in under 1 hour, while low performers take over 1 week.

    IMPORTANT: MTTR end state depends on `incident_resolved_at` field mapping:
    - "resolutiondate": Bug created → Bug resolved (team fix time)
    - "fixVersions": Bug created → Bug deployed (true production MTTR)

    When using "fixVersions", MTTR uses the SAME deployment date logic as
    Deployment Frequency and Lead Time (DRY principle).

    Args:
        incident_issues: List of incident/bug issues
        time_period_days: Number of days in measurement period (default: 30)
        previous_period_value: Optional previous period value for trend calculation
        fixversion_release_map: Map of fixVersion name → releaseDate datetime
            Built from Operational Tasks via build_fixversion_release_map()
            Required when incident_resolved_at is "fixVersions"

    Returns:
        Dictionary with MTTR metrics:
        {
            "value": float,  # Average recovery time in hours or days
            "unit": "hours" | "days",
            "performance_tier": "elite" | "high" | "medium" | "low",
            "incident_count": int,
            "period_days": int,
            "trend_direction": "up" | "down" | "stable",
            "trend_percentage": float
        }

        On error:
        {
            "error_state": "missing_mapping" | "no_data" | "calculation_error",
            "error_message": str,
            "trend_direction": "stable",
            "trend_percentage": 0.0
        }
    """
    try:
        if not incident_issues:
            return {
                "error_state": "no_data",
                "error_message": "No incident issues provided for analysis",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Import shared fixversion lookup function
        from data.fixversion_matcher import get_deployment_date_for_issue

        # Extract recovery times
        recovery_times = []
        missing_start_count = 0
        missing_end_count = 0
        no_fixversion_match_count = 0

        # Get field mappings from profile configuration
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        field_mappings = app_settings.get("field_mappings", {})
        dora_mappings = field_mappings.get("dora", {})

        incident_detected_field = dora_mappings.get("incident_detected_at", "created")
        incident_resolved_field = dora_mappings.get(
            "incident_resolved_at", "resolutiondate"
        )

        # Check if using fixVersions for end state (production deployment)
        use_deployment_date = incident_resolved_field.lower() == "fixversions"

        for issue in incident_issues:
            issue_key = issue.get("key", "UNKNOWN")

            # Extract changelog if present
            changelog = issue.get("changelog", {}).get("histories", [])

            # Extract incident start timestamp using field mapping
            incident_start_value = _extract_datetime_from_field_mapping(
                issue, incident_detected_field, changelog
            )
            if not incident_start_value:
                missing_start_count += 1
                continue

            # Get end timestamp based on configuration
            if use_deployment_date and fixversion_release_map:
                # Use deployment date from Operational Task (same as Lead Time)
                end_datetime = get_deployment_date_for_issue(
                    issue, fixversion_release_map
                )
                if not end_datetime:
                    no_fixversion_match_count += 1
                    logger.debug(
                        f"[MTTR] {issue_key}: No matching fixVersion in release map"
                    )
                    continue
            else:
                # Use standard field extraction (e.g., resolutiondate)
                incident_resolved_value = _extract_datetime_from_field_mapping(
                    issue, incident_resolved_field, changelog
                )
                if not incident_resolved_value:
                    missing_end_count += 1
                    continue
                try:
                    end_datetime = datetime.fromisoformat(
                        incident_resolved_value.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    missing_end_count += 1
                    continue

            try:
                start_time = datetime.fromisoformat(
                    incident_start_value.replace("Z", "+00:00")
                )

                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                if end_datetime.tzinfo is None:
                    end_datetime = end_datetime.replace(tzinfo=timezone.utc)

                # Calculate recovery time in hours
                recovery_delta = end_datetime - start_time
                recovery_hours = (
                    recovery_delta.total_seconds() / 3600
                )  # 3600 seconds per hour

                if recovery_hours < 0:
                    logger.warning(
                        f"[DORA] Negative recovery time for {issue_key}: "
                        f"start={start_time}, end={end_datetime}"
                    )
                    continue

                recovery_times.append(recovery_hours)
                logger.debug(
                    f"[MTTR] {issue_key}: {recovery_hours:.1f} hours "
                    f"(start={start_time.date()}, end={end_datetime.date()})"
                )

            except (ValueError, TypeError) as e:
                logger.warning(f"[DORA] Invalid timestamp for {issue_key}: {e}")
                continue

        if not recovery_times:
            error_details = []
            if missing_start_count:
                error_details.append(f"missing start: {missing_start_count}")
            if no_fixversion_match_count:
                error_details.append(
                    f"no fixVersion match: {no_fixversion_match_count}"
                )
            if missing_end_count:
                error_details.append(f"missing end: {missing_end_count}")

            return {
                "error_state": "no_data",
                "error_message": f"No valid recovery times from {len(incident_issues)} incidents "
                f"({', '.join(error_details)})",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Use MEDIAN per official DORA methodology (outlier resistant)
        # Note: MTTR name contains "Mean" for historical reasons, but DORA uses median
        import statistics

        median_mttr_hours = statistics.median(recovery_times)
        median_mttr_days = median_mttr_hours / 24
        mean_mttr_hours = sum(recovery_times) / len(
            recovery_times
        )  # Keep for reference

        # Determine display unit
        if median_mttr_hours >= 24:
            unit = "days"
            display_value = median_mttr_days
        else:
            unit = "hours"
            display_value = median_mttr_hours

        # Classify performance tier (lower is better)
        performance_tier = _classify_performance_tier(
            median_mttr_hours, MTTR_TIERS, higher_is_better=False
        )

        # Calculate trend
        trend = _calculate_trend(median_mttr_hours, previous_period_value)

        logger.info(
            f"[DORA] Mean Time to Recovery (median): {display_value:.1f} {unit} "
            f"({len(recovery_times)} incidents) - {performance_tier}"
        )

        return {
            "value": display_value,
            "unit": unit,
            "value_hours": median_mttr_hours,
            "value_days": median_mttr_days,
            "performance_tier": performance_tier,
            "incident_count": len(recovery_times),
            "period_days": time_period_days,
            # Additional statistics for analysis
            "mean_hours": mean_mttr_hours,
            **trend,
        }

    except Exception as e:
        logger.error(f"[DORA] MTTR calculation failed: {e}", exc_info=True)
        return {
            "error_state": "calculation_error",
            "error_message": str(e),
            "trend_direction": "stable",
            "trend_percentage": 0.0,
        }
