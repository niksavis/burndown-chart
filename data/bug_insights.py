"""Quality insights engine for bug analysis.

Provides rule-based insights generation for actionable quality recommendations
based on bug patterns and trends.
"""

from enum import Enum
from typing import Dict, List, Optional


class InsightType(Enum):
    """Type of quality insight."""

    RESOLUTION_RATE = "resolution_rate"
    BUG_TREND = "bug_trend"
    POSITIVE_TREND = "positive_trend"
    STABLE_QUALITY = "stable_quality"
    NO_OPEN_BUGS = "no_open_bugs"
    HIGH_BUG_CAPACITY = "high_bug_capacity"
    LONG_RESOLUTION_TIME = "long_resolution_time"


class InsightSeverity(Enum):
    """Severity level of quality insight (T066)."""

    CRITICAL = "critical"  # Immediate action needed
    HIGH = "high"  # Address soon
    MEDIUM = "medium"  # Monitor
    LOW = "low"  # Informational/positive feedback


# Default thresholds for quality insights (T067)
DEFAULT_THRESHOLDS = {
    "resolution_rate_warning": 0.70,  # Below this triggers warning
    "resolution_rate_critical": 0.50,  # Below this triggers critical
    "capacity_warning": 0.30,  # Above this triggers warning
    "capacity_critical": 0.40,  # Above this triggers critical
    "avg_resolution_days_warning": 14,  # Above this triggers warning
    "avg_resolution_days_critical": 30,  # Above this triggers critical
    "trend_window_weeks": 4,  # Number of weeks for trend analysis
    "trend_ratio_increasing": 1.2,  # bugs_created / bugs_resolved
    "trend_ratio_stable": 0.9,  # Lower bound for stable
    "positive_resolution_rate": 0.80,  # Above this is positive
    "consecutive_increasing_weeks": 3,  # 3+ weeks of creation > closure
    "stable_variance_threshold": 0.2,  # ±20% variation considered stable
}


def generate_quality_insights(
    metrics: Dict, statistics: List[Dict], thresholds: Optional[Dict] = None
) -> List[Dict]:
    """Generate actionable quality insights from bug data.

    Analyzes bug patterns and generates actionable recommendations with severity
    levels. Insights are prioritized by severity and limited to top 10.

    Args:
        metrics: Bug metrics summary (total_bugs, open_bugs, closed_bugs, resolution_rate)
        statistics: Weekly bug statistics (bugs_created, bugs_resolved per week)
        thresholds: Optional custom thresholds for insight rules

    Returns:
        List of quality insight dictionaries, sorted by severity (critical → warning → info)
        Each insight has: type, severity, message, actionable_recommendation

    Example:
        >>> metrics = {"total_bugs": 50, "open_bugs": 10, "closed_bugs": 40, "resolution_rate": 0.80}
        >>> statistics = [{"week_start": "2025-01-01", "bugs_created": 5, "bugs_resolved": 7}]
        >>> insights = generate_quality_insights(metrics, statistics)
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS.copy()
    else:
        # Merge with defaults
        merged = DEFAULT_THRESHOLDS.copy()
        merged.update(thresholds)
        thresholds = merged

    insights = []

    # Run all insight rules
    insight_checks = [
        check_low_resolution_rate(metrics, thresholds),
        check_increasing_bug_trend(statistics, thresholds),
        check_positive_trend(statistics),
        check_stable_quality(statistics, thresholds),
        check_no_open_bugs(metrics),
        check_high_bug_capacity(metrics, thresholds),
        check_long_resolution_time(metrics, thresholds),
    ]

    # Collect non-None insights
    for insight in insight_checks:
        if insight is not None:
            insights.append(insight)

    # Sort by severity (critical → high → medium → low) - T076
    severity_order = {
        InsightSeverity.CRITICAL: 0,
        InsightSeverity.HIGH: 1,
        InsightSeverity.MEDIUM: 2,
        InsightSeverity.LOW: 3,
    }
    insights.sort(key=lambda x: severity_order.get(x["severity"], 999))

    # Cap at 10 insights
    return insights[:10]


def check_low_resolution_rate(metrics: Dict, thresholds: Dict) -> Optional[Dict]:
    """Check if bug resolution rate is below threshold.

    Implements T068 - low resolution rate check.

    Args:
        metrics: Bug metrics summary with resolution_rate
        thresholds: Custom thresholds

    Returns:
        Insight dict if triggered, None otherwise
    """
    resolution_rate = metrics.get("resolution_rate", 0.0)
    min_threshold = thresholds.get("resolution_rate_warning", 0.70)
    critical_threshold = thresholds.get("resolution_rate_critical", 0.50)

    if resolution_rate < critical_threshold:
        return {
            "id": "LOW_RESOLUTION_RATE",
            "type": InsightType.RESOLUTION_RATE,
            "severity": InsightSeverity.CRITICAL,
            "title": "Critical Resolution Rate",
            "message": f"Critical: resolution rate of {resolution_rate:.0%} requires immediate attention",
            "actionable_recommendation": "Prioritize bug resolution - consider dedicating sprint capacity to reduce backlog",
        }
    elif resolution_rate < min_threshold:
        return {
            "id": "BELOW_TARGET_RESOLUTION",
            "type": InsightType.RESOLUTION_RATE,
            "severity": InsightSeverity.HIGH,
            "title": "Low Resolution Rate",
            "message": f"Resolution rate of {resolution_rate:.0%} below {min_threshold:.0%} target",
            "actionable_recommendation": "Increase focus on bug resolution to prevent backlog growth",
        }

    return None


def check_increasing_bug_trend(
    statistics: List[Dict], thresholds: Dict
) -> Optional[Dict]:
    """Check if bug creation exceeds closure for consecutive weeks.

    Args:
        statistics: Weekly bug statistics
        thresholds: Custom thresholds

    Returns:
        Insight dict if triggered, None otherwise
    """
    if len(statistics) < 3:
        return None

    consecutive_weeks = thresholds.get(
        "consecutive_increasing_weeks",
        DEFAULT_THRESHOLDS["consecutive_increasing_weeks"],
    )
    consecutive_count = 0

    for week in statistics[-8:]:  # Check last 8 weeks
        created = week.get("bugs_created", 0)
        resolved = week.get("bugs_resolved", 0)

        if created > resolved:
            consecutive_count += 1
        else:
            consecutive_count = 0

        if consecutive_count >= consecutive_weeks:
            return {
                "type": InsightType.BUG_TREND,
                "severity": InsightSeverity.HIGH,
                "message": f"Increasing bug trend: creation exceeds resolution for {consecutive_count} consecutive weeks",
                "actionable_recommendation": "Review bug prevention practices - consider root cause analysis and quality gates",
            }

    return None


def check_positive_trend(statistics: List[Dict]) -> Optional[Dict]:
    """Check for positive quality trends.

    Args:
        statistics: Weekly bug statistics

    Returns:
        Positive insight dict if conditions met, None otherwise
    """
    if len(statistics) < 3:
        return None

    recent_weeks = statistics[-4:]  # Check last 4 weeks
    positive_weeks = sum(
        1
        for week in recent_weeks
        if week.get("bugs_resolved", 0) > week.get("bugs_created", 0)
    )

    if positive_weeks >= 3:  # 3+ out of 4 weeks positive
        return {
            "type": InsightType.POSITIVE_TREND,
            "severity": InsightSeverity.LOW,
            "message": "Excellent: Bug resolution exceeds creation consistently",
            "actionable_recommendation": "Continue current quality practices - backlog is decreasing",
        }

    return None


def check_stable_quality(statistics: List[Dict], thresholds: Dict) -> Optional[Dict]:
    """Check for stable quality (consistent closure rate).

    Args:
        statistics: Weekly bug statistics
        thresholds: Custom thresholds

    Returns:
        Positive insight dict if conditions met, None otherwise
    """
    if len(statistics) < 4:
        return None

    recent_weeks = statistics[-4:]
    net_changes = [
        week.get("bugs_created", 0) - week.get("bugs_resolved", 0)
        for week in recent_weeks
    ]

    # Calculate variance in net change
    avg_net_change = sum(net_changes) / len(net_changes)
    variance = sum((x - avg_net_change) ** 2 for x in net_changes) / len(net_changes)

    # Stable if low variance and net change near zero
    if variance < 10 and abs(avg_net_change) < 2:
        return {
            "type": InsightType.STABLE_QUALITY,
            "severity": InsightSeverity.LOW,
            "message": "Stable quality: Bug creation and resolution are balanced",
            "actionable_recommendation": "Maintain current practices - quality is under control",
        }

    return None


def check_no_open_bugs(metrics: Dict) -> Optional[Dict]:
    """Check if there are no open bugs.

    Args:
        metrics: Bug metrics summary with open_bugs count

    Returns:
        Positive insight dict if no open bugs, None otherwise
    """
    open_bugs = metrics.get("open_bugs", 0)

    if open_bugs == 0 and metrics.get("total_bugs", 0) > 0:
        return {
            "type": InsightType.NO_OPEN_BUGS,
            "severity": InsightSeverity.LOW,
            "message": "Perfect: No open bugs - all bugs resolved!",
            "actionable_recommendation": "Excellent work - maintain proactive bug prevention and resolution",
        }

    return None


def check_high_bug_capacity(metrics: Dict, thresholds: Dict) -> Optional[Dict]:
    """Check if bugs are consuming high percentage of capacity.

    Implements T070 - high bug capacity warning.

    Args:
        metrics: Bug metrics summary with capacity_consumed_by_bugs
        thresholds: Custom thresholds

    Returns:
        Insight dict if triggered, None otherwise
    """
    capacity = metrics.get("capacity_consumed_by_bugs", 0.0)

    # Default thresholds from contract: 30% warning, 40% critical
    warning_threshold = thresholds.get("capacity_warning", 0.30)
    critical_threshold = thresholds.get("capacity_critical", 0.40)

    if capacity >= critical_threshold:
        return {
            "type": InsightType.HIGH_BUG_CAPACITY,
            "severity": InsightSeverity.CRITICAL,
            "message": f"Critical: Bugs consuming {capacity:.0%} of team capacity",
            "actionable_recommendation": "Immediate action required - reallocate resources to reduce bug backlog and improve quality processes",
        }
    elif capacity >= warning_threshold:
        return {
            "type": InsightType.HIGH_BUG_CAPACITY,
            "severity": InsightSeverity.HIGH,
            "message": f"High bug capacity: {capacity:.0%} of capacity spent on bugs",
            "actionable_recommendation": "Monitor closely - consider investing in bug prevention and automated testing",
        }

    return None


def check_long_resolution_time(metrics: Dict, thresholds: Dict) -> Optional[Dict]:
    """Check if average bug resolution time is too long.

    Implements T071 - long resolution time warning.

    Args:
        metrics: Bug metrics summary with avg_resolution_time_days
        thresholds: Custom thresholds

    Returns:
        Insight dict if triggered, None otherwise
    """
    avg_days = metrics.get("avg_resolution_time_days", 0.0)

    # Default thresholds from contract: 14 days warning, 30 days critical
    warning_threshold = thresholds.get("avg_resolution_days_warning", 14)
    critical_threshold = thresholds.get("avg_resolution_days_critical", 30)

    if avg_days >= critical_threshold:
        return {
            "type": InsightType.LONG_RESOLUTION_TIME,
            "severity": InsightSeverity.CRITICAL,
            "message": f"Critical: Bugs taking {avg_days:.1f} days to resolve on average",
            "actionable_recommendation": "Immediate action - review bug triage process and ensure bugs are prioritized appropriately",
        }
    elif avg_days >= warning_threshold:
        return {
            "type": InsightType.LONG_RESOLUTION_TIME,
            "severity": InsightSeverity.HIGH,
            "message": f"Slow resolution: Average {avg_days:.1f} days to close bugs",
            "actionable_recommendation": "Consider dedicating more resources to bug resolution or improving development workflow",
        }

    return None
