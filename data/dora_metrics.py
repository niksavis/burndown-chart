"""Modern DORA metrics calculator using variable extraction.

Calculates the four DORA (DevOps Research and Assessment) metrics:
- Deployment Frequency: How often code is deployed to production
- Lead Time for Changes: Time from code commit to production deployment
- Change Failure Rate: Percentage of deployments causing incidents
- Mean Time to Recovery: Time to restore service after incidents

This implementation uses VariableExtractor for clean, rule-based data extraction
with no backward compatibility for legacy field_mappings.

Architecture:
- Pure business logic with no UI dependencies
- Clean separation between data extraction (VariableExtractor) and calculation
- Consistent error handling and performance tier classification
- Comprehensive logging for debugging and monitoring

Reference: docs/dora_metrics_spec.md
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

from data.variable_mapping.extractor import VariableExtractor
from data.performance_utils import log_performance

logger = logging.getLogger(__name__)


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
    extractor: VariableExtractor,
    time_period_days: int = 30,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate deployment frequency metric.

    Measures how often code is deployed to production. Industry-leading teams
    deploy multiple times per day (elite), while lower-performing teams deploy
    monthly or less (low).

    Args:
        issues: List of JIRA issues to analyze
        extractor: VariableExtractor configured with deployment variable mappings
        time_period_days: Number of days in measurement period (default: 30)
        previous_period_value: Optional previous period value for trend calculation

    Returns:
        Dictionary with deployment frequency metrics:
        {
            "value": float,  # Deployments per day
            "unit": "deployments/day" | "deployments/week" | "deployments/month",
            "performance_tier": "elite" | "high" | "medium" | "low",
            "deployment_count": int,
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

        # Extract deployments using variable mapping
        deployments = []
        no_timestamp_count = 0

        for issue in issues:
            # Extract changelog if present
            changelog = issue.get("changelog", {}).get("histories", [])

            # Check if this issue represents a deployment
            deployment_event = extractor.extract_variable(
                "deployment_event", issue, changelog
            )
            if not deployment_event.get("found") or not deployment_event.get("value"):
                continue

            # Filter out failed deployments (if deployment_successful field is mapped)
            deployment_successful = extractor.extract_variable(
                "deployment_successful", issue, changelog
            )
            if deployment_successful.get("found") and not deployment_successful.get(
                "value"
            ):
                logger.debug(
                    f"[DORA] Issue {issue.get('key')} is failed deployment, excluding from count"
                )
                continue

            # Extract deployment timestamp
            deployment_timestamp = extractor.extract_variable(
                "deployment_timestamp", issue, changelog
            )
            if not deployment_timestamp.get("found"):
                no_timestamp_count += 1
                logger.debug(
                    f"[DORA] Issue {issue.get('key')} is deployment but has no timestamp"
                )
                continue

            timestamp_str = deployment_timestamp.get("value")
            if not timestamp_str:
                no_timestamp_count += 1
                continue

            try:
                # Parse timestamp
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                deployments.append(
                    {
                        "issue_key": issue.get("key"),
                        "timestamp": timestamp,
                        "source_priority": deployment_timestamp.get("source_priority"),
                    }
                )
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"[DORA] Invalid timestamp format for {issue.get('key')}: {timestamp_str} - {e}"
                )
                no_timestamp_count += 1
                continue

        if not deployments:
            return {
                "error_state": "no_data",
                "error_message": f"No valid deployments found in {len(issues)} issues "
                f"({no_timestamp_count} without timestamps)",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Calculate deployment frequency
        deployment_count = len(deployments)
        deployments_per_day = deployment_count / time_period_days

        # Determine best display unit
        if deployments_per_day >= 0.9:
            unit = "deployments/day"
            display_value = deployments_per_day
        elif deployments_per_day >= 0.13:
            unit = "deployments/week"
            display_value = deployments_per_day * 7
        else:
            unit = "deployments/month"
            display_value = deployments_per_day * 30

        # Classify performance tier
        performance_tier = _classify_performance_tier(
            deployments_per_day, DEPLOYMENT_FREQUENCY_TIERS, higher_is_better=True
        )

        # Calculate trend
        trend = _calculate_trend(deployments_per_day, previous_period_value)

        logger.info(
            f"[DORA] Deployment Frequency: {display_value:.1f} {unit} "
            f"({deployment_count} deployments / {time_period_days} days) - {performance_tier}"
        )

        return {
            "value": display_value,
            "unit": unit,
            "performance_tier": performance_tier,
            "deployment_count": deployment_count,
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
    extractor: VariableExtractor,
    time_period_days: int = 30,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate lead time for changes metric.

    Measures time from code commit to production deployment. Elite teams have
    lead times under 1 day, while low performers take over 1 month.

    Args:
        issues: List of JIRA issues to analyze
        extractor: VariableExtractor configured with lead time variable mappings
        time_period_days: Number of days in measurement period (default: 30)
        previous_period_value: Optional previous period value for trend calculation

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

        # Extract lead times
        lead_times = []
        missing_start_count = 0
        missing_end_count = 0

        for issue in issues:
            # Extract changelog if present
            changelog = issue.get("changelog", {}).get("histories", [])

            # Extract work start timestamp
            work_start = extractor.extract_variable(
                "work_started_timestamp", issue, changelog
            )
            if not work_start.get("found"):
                missing_start_count += 1
                continue

            # Extract deployment timestamp
            deployment = extractor.extract_variable(
                "deployment_timestamp", issue, changelog
            )
            if not deployment.get("found"):
                missing_end_count += 1
                continue

            try:
                start_time = datetime.fromisoformat(
                    work_start["value"].replace("Z", "+00:00")
                )
                end_time = datetime.fromisoformat(
                    deployment["value"].replace("Z", "+00:00")
                )

                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)

                # Calculate lead time in days
                lead_time_delta = end_time - start_time
                lead_time_days = (
                    lead_time_delta.total_seconds() / 86400
                )  # 86400 seconds per day

                if lead_time_days < 0:
                    logger.warning(
                        f"[DORA] Negative lead time for {issue.get('key')}: "
                        f"start={start_time}, end={end_time}"
                    )
                    continue

                lead_times.append(lead_time_days)

            except (ValueError, TypeError) as e:
                logger.warning(f"[DORA] Invalid timestamp for {issue.get('key')}: {e}")
                continue

        if not lead_times:
            return {
                "error_state": "no_data",
                "error_message": f"No valid lead times calculated from {len(issues)} issues "
                f"(missing start: {missing_start_count}, missing end: {missing_end_count})",
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

        # Calculate average lead time
        avg_lead_time_days = sum(lead_times) / len(lead_times)

        # Determine display unit
        if avg_lead_time_days < 1:
            unit = "hours"
            display_value = avg_lead_time_days * 24
        else:
            unit = "days"
            display_value = avg_lead_time_days

        # Classify performance tier (lower is better)
        performance_tier = _classify_performance_tier(
            avg_lead_time_days, LEAD_TIME_TIERS, higher_is_better=False
        )

        # Calculate trend
        trend = _calculate_trend(avg_lead_time_days, previous_period_value)

        logger.info(
            f"[DORA] Lead Time for Changes: {display_value:.1f} {unit} "
            f"({len(lead_times)} issues) - {performance_tier}"
        )

        return {
            "value": display_value,
            "unit": unit,
            "performance_tier": performance_tier,
            "sample_count": len(lead_times),
            "period_days": time_period_days,
            # Backward compatibility fields for metrics_calculator
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
    extractor: VariableExtractor,
    time_period_days: int = 30,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate change failure rate metric.

    Measures percentage of deployments that cause incidents requiring remediation.
    Elite teams have failure rates under 15%, while low performers exceed 45%.

    Args:
        deployment_issues: List of deployment issues
        incident_issues: List of incident/bug issues
        extractor: VariableExtractor configured with incident variable mappings
        time_period_days: Number of days in measurement period (default: 30)
        previous_period_value: Optional previous period value for trend calculation

    Returns:
        Dictionary with change failure rate metrics:
        {
            "value": float,  # Failure rate percentage (0-100)
            "unit": "%",
            "performance_tier": "elite" | "high" | "medium" | "low",
            "deployment_count": int,
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
        # Count deployments
        deployment_count = 0
        for issue in deployment_issues:
            changelog = issue.get("changelog", {}).get("histories", [])
            deployment_event = extractor.extract_variable(
                "deployment_event", issue, changelog
            )
            if deployment_event.get("found") and deployment_event.get("value"):
                deployment_count += 1

        if deployment_count == 0:
            return {
                "error_state": "no_data",
                "error_message": "No deployments found in specified period",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Count incidents caused by deployments
        incident_count = 0
        for issue in incident_issues:
            changelog = issue.get("changelog", {}).get("histories", [])
            # Check if incident is deployment-related
            incident_event = extractor.extract_variable(
                "incident_event", issue, changelog
            )
            if incident_event.get("found") and incident_event.get("value"):
                incident_count += 1

        # Calculate failure rate
        failure_rate = (incident_count / deployment_count) * 100

        # Classify performance tier (lower is better)
        performance_tier = _classify_performance_tier(
            failure_rate, CHANGE_FAILURE_RATE_TIERS, higher_is_better=False
        )

        # Calculate trend
        trend = _calculate_trend(failure_rate, previous_period_value)

        logger.info(
            f"[DORA] Change Failure Rate: {failure_rate:.1f}% "
            f"({incident_count} incidents / {deployment_count} deployments) - {performance_tier}"
        )

        return {
            "value": failure_rate,
            "unit": "%",
            "performance_tier": performance_tier,
            "deployment_count": deployment_count,
            "incident_count": incident_count,
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
    extractor: VariableExtractor,
    time_period_days: int = 30,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate mean time to recovery metric.

    Measures average time to restore service after an incident. Elite teams
    recover in under 1 hour, while low performers take over 1 week.

    Args:
        incident_issues: List of incident/bug issues
        extractor: VariableExtractor configured with incident variable mappings
        time_period_days: Number of days in measurement period (default: 30)
        previous_period_value: Optional previous period value for trend calculation

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

        # Extract recovery times
        recovery_times = []
        missing_start_count = 0
        missing_end_count = 0

        for issue in incident_issues:
            # Extract changelog if present
            changelog = issue.get("changelog", {}).get("histories", [])

            # Extract incident start timestamp
            incident_start = extractor.extract_variable(
                "incident_start_timestamp", issue, changelog
            )
            if not incident_start.get("found"):
                missing_start_count += 1
                continue

            # Extract incident resolved timestamp
            incident_resolved = extractor.extract_variable(
                "incident_resolved_timestamp", issue, changelog
            )
            if not incident_resolved.get("found"):
                missing_end_count += 1
                continue

            try:
                start_time = datetime.fromisoformat(
                    incident_start["value"].replace("Z", "+00:00")
                )
                end_time = datetime.fromisoformat(
                    incident_resolved["value"].replace("Z", "+00:00")
                )

                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)

                # Calculate recovery time in hours
                recovery_delta = end_time - start_time
                recovery_hours = (
                    recovery_delta.total_seconds() / 3600
                )  # 3600 seconds per hour

                if recovery_hours < 0:
                    logger.warning(
                        f"[DORA] Negative recovery time for {issue.get('key')}: "
                        f"start={start_time}, end={end_time}"
                    )
                    continue

                recovery_times.append(recovery_hours)

            except (ValueError, TypeError) as e:
                logger.warning(f"[DORA] Invalid timestamp for {issue.get('key')}: {e}")
                continue

        if not recovery_times:
            return {
                "error_state": "no_data",
                "error_message": f"No valid recovery times calculated from {len(incident_issues)} incidents "
                f"(missing start: {missing_start_count}, missing end: {missing_end_count})",
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            }

        # Calculate average MTTR
        avg_mttr_hours = sum(recovery_times) / len(recovery_times)

        # Determine display unit
        if avg_mttr_hours >= 24:
            unit = "days"
            display_value = avg_mttr_hours / 24
        else:
            unit = "hours"
            display_value = avg_mttr_hours

        # Classify performance tier (lower is better)
        performance_tier = _classify_performance_tier(
            avg_mttr_hours, MTTR_TIERS, higher_is_better=False
        )

        # Calculate trend
        trend = _calculate_trend(avg_mttr_hours, previous_period_value)

        logger.info(
            f"[DORA] Mean Time to Recovery: {display_value:.1f} {unit} "
            f"({len(recovery_times)} incidents) - {performance_tier}"
        )

        return {
            "value": display_value,
            "unit": unit,
            "performance_tier": performance_tier,
            "incident_count": len(recovery_times),
            "period_days": time_period_days,
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
