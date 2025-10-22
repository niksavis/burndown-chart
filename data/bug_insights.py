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
    """Severity level of quality insight."""

    CRITICAL = "critical"  # Immediate action needed
    WARNING = "warning"  # Address soon
    INFO = "info"  # Informational/positive feedback


# Default thresholds for quality insights
DEFAULT_THRESHOLDS = {
    "min_resolution_rate": 0.60,  # Below 60% triggers warning
    "critical_resolution_rate": 0.40,  # Below 40% triggers critical
    "consecutive_increasing_weeks": 3,  # 3+ weeks of creation > closure
    "stable_variance_threshold": 0.2,  # ±20% variation considered stable
    "high_bug_capacity_threshold": 0.30,  # 30%+ bug points/total points
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
    ]

    # Collect non-None insights
    for insight in insight_checks:
        if insight is not None:
            insights.append(insight)

    # Sort by severity (critical → warning → info)
    severity_order = {
        InsightSeverity.CRITICAL: 0,
        InsightSeverity.WARNING: 1,
        InsightSeverity.INFO: 2,
    }
    insights.sort(key=lambda x: severity_order.get(x["severity"], 999))

    # Cap at 10 insights
    return insights[:10]


def check_low_resolution_rate(metrics: Dict, thresholds: Dict) -> Optional[Dict]:
    """Check if bug resolution rate is below threshold.

    Args:
        metrics: Bug metrics summary with resolution_rate
        thresholds: Custom thresholds

    Returns:
        Insight dict if triggered, None otherwise
    """
    resolution_rate = metrics.get("resolution_rate", 0.0)
    min_threshold = thresholds.get(
        "min_resolution_rate", DEFAULT_THRESHOLDS["min_resolution_rate"]
    )
    critical_threshold = thresholds.get(
        "critical_resolution_rate", DEFAULT_THRESHOLDS["critical_resolution_rate"]
    )

    if resolution_rate < critical_threshold:
        return {
            "type": InsightType.RESOLUTION_RATE,
            "severity": InsightSeverity.CRITICAL,
            "message": f"Critical: Bug resolution rate is only {resolution_rate:.0%}",
            "actionable_recommendation": "Prioritize bug resolution - consider dedicating sprint capacity to reduce backlog",
        }
    elif resolution_rate < min_threshold:
        return {
            "type": InsightType.RESOLUTION_RATE,
            "severity": InsightSeverity.WARNING,
            "message": f"Low bug resolution rate: {resolution_rate:.0%}",
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
                "severity": InsightSeverity.WARNING,
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
            "severity": InsightSeverity.INFO,
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
            "severity": InsightSeverity.INFO,
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
            "severity": InsightSeverity.INFO,
            "message": "Perfect: No open bugs - all bugs resolved!",
            "actionable_recommendation": "Excellent work - maintain proactive bug prevention and resolution",
        }

    return None
