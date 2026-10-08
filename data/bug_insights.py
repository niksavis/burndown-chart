from enum import Enum


class InsightType(Enum):
    RESOLUTION_RATE = "resolution_rate"
    BUG_TREND = "bug_trend"
    POSITIVE_TREND = "positive_trend"
    STABLE_QUALITY = "stable_quality"
    NO_OPEN_BUGS = "no_open_bugs"
    HIGH_BUG_CAPACITY = "high_bug_capacity"
    LONG_RESOLUTION_TIME = "long_resolution_time"


class InsightSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


DEFAULT_THRESHOLDS = {
    "resolution_rate_warning": 0.70,
    "resolution_rate_critical": 0.50,
    "capacity_warning": 0.30,
    "capacity_critical": 0.40,
    "avg_resolution_days_warning": 14,
    "avg_resolution_days_critical": 30,
    "trend_window_weeks": 4,
    "trend_ratio_increasing": 1.2,
    "trend_ratio_stable": 0.9,
    "positive_resolution_rate": 0.80,
    "consecutive_increasing_weeks": 3,
    "stable_variance_threshold": 0.2,
}


def generate_quality_insights(
    metrics: dict, statistics: list[dict], thresholds: dict | None = None
) -> list[dict]:

    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS.copy()
    else:
        merged = DEFAULT_THRESHOLDS.copy()
        merged.update(thresholds)
        thresholds = merged

    insights = []

    insight_checks = [
        check_low_resolution_rate(metrics, thresholds),
        check_increasing_bug_trend(statistics, thresholds),
        check_positive_trend(statistics),
        check_stable_quality(statistics, thresholds),
        check_no_open_bugs(metrics),
        check_high_bug_capacity(metrics, thresholds),
        check_long_resolution_time(metrics, thresholds),
    ]

    for insight in insight_checks:
        if insight is not None:
            insights.append(insight)

    severity_order = {
        InsightSeverity.CRITICAL: 0,
        InsightSeverity.HIGH: 1,
        InsightSeverity.MEDIUM: 2,
        InsightSeverity.LOW: 3,
    }
    insights.sort(key=lambda x: severity_order.get(x["severity"], 999))

    return insights[:10]


def check_low_resolution_rate(metrics: dict, thresholds: dict) -> dict | None:

    resolution_rate = metrics.get("resolution_rate", 0.0)
    min_threshold = thresholds.get("resolution_rate_warning", 0.70)
    critical_threshold = thresholds.get("resolution_rate_critical", 0.50)

    if resolution_rate < critical_threshold:
        return {
            "id": "LOW_RESOLUTION_RATE",
            "type": InsightType.RESOLUTION_RATE,
            "severity": InsightSeverity.CRITICAL,
            "title": "Critical Resolution Rate",
            "message": (
                f"Critical: resolution rate of {resolution_rate:.0%} requires "
                "immediate attention"
            ),
            "actionable_recommendation": (
                "Prioritize bug resolution - consider dedicating sprint "
                "capacity to reduce backlog"
            ),
        }
    elif resolution_rate < min_threshold:
        return {
            "id": "BELOW_TARGET_RESOLUTION",
            "type": InsightType.RESOLUTION_RATE,
            "severity": InsightSeverity.HIGH,
            "title": "Low Resolution Rate",
            "message": (
                f"Resolution rate of {resolution_rate:.0%} below "
                f"{min_threshold:.0%} target"
            ),
            "actionable_recommendation": (
                "Increase focus on bug resolution to prevent backlog growth"
            ),
        }

    return None


def check_increasing_bug_trend(statistics: list[dict], thresholds: dict) -> dict | None:

    if len(statistics) < 3:
        return None

    consecutive_weeks = thresholds.get(
        "consecutive_increasing_weeks",
        DEFAULT_THRESHOLDS["consecutive_increasing_weeks"],
    )
    consecutive_count = 0

    for week in statistics[-8:]:
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
                "message": (
                    "Increasing bug trend: creation exceeds resolution for "
                    f"{consecutive_count} consecutive weeks"
                ),
                "actionable_recommendation": (
                    "Review bug prevention practices - consider root cause "
                    "analysis and quality gates"
                ),
            }

    return None


def check_positive_trend(statistics: list[dict]) -> dict | None:

    if len(statistics) < 3:
        return None

    recent_weeks = statistics[-4:]
    positive_weeks = sum(
        1
        for week in recent_weeks
        if week.get("bugs_resolved", 0) > week.get("bugs_created", 0)
    )

    if positive_weeks >= 3:
        return {
            "type": InsightType.POSITIVE_TREND,
            "severity": InsightSeverity.LOW,
            "message": "Excellent: Bug resolution exceeds creation consistently",
            "actionable_recommendation": (
                "Continue current quality practices - backlog is decreasing"
            ),
        }

    return None


def check_stable_quality(statistics: list[dict], thresholds: dict) -> dict | None:

    if len(statistics) < 4:
        return None

    recent_weeks = statistics[-4:]
    net_changes = [
        week.get("bugs_created", 0) - week.get("bugs_resolved", 0)
        for week in recent_weeks
    ]

    avg_net_change = sum(net_changes) / len(net_changes)
    variance = sum((x - avg_net_change) ** 2 for x in net_changes) / len(net_changes)

    if variance < 10 and abs(avg_net_change) < 2:
        return {
            "type": InsightType.STABLE_QUALITY,
            "severity": InsightSeverity.LOW,
            "message": "Stable quality: Bug creation and resolution are balanced",
            "actionable_recommendation": (
                "Maintain current practices - quality is under control"
            ),
        }

    return None


def check_no_open_bugs(metrics: dict) -> dict | None:

    open_bugs = metrics.get("open_bugs", 0)

    if open_bugs == 0 and metrics.get("total_bugs", 0) > 0:
        return {
            "type": InsightType.NO_OPEN_BUGS,
            "severity": InsightSeverity.LOW,
            "message": "Perfect: No open bugs - all bugs resolved!",
            "actionable_recommendation": (
                "Excellent work - maintain proactive bug prevention and resolution"
            ),
        }

    return None


def check_high_bug_capacity(metrics: dict, thresholds: dict) -> dict | None:

    capacity = metrics.get("capacity_consumed_by_bugs", 0.0)

    warning_threshold = thresholds.get("capacity_warning", 0.30)
    critical_threshold = thresholds.get("capacity_critical", 0.40)

    if capacity >= critical_threshold:
        return {
            "type": InsightType.HIGH_BUG_CAPACITY,
            "severity": InsightSeverity.CRITICAL,
            "message": f"Critical: Bugs consuming {capacity:.0%} of team capacity",
            "actionable_recommendation": (
                "Immediate action required - reallocate resources to reduce "
                "bug backlog and improve quality processes"
            ),
        }
    elif capacity >= warning_threshold:
        return {
            "type": InsightType.HIGH_BUG_CAPACITY,
            "severity": InsightSeverity.HIGH,
            "message": f"High bug capacity: {capacity:.0%} of capacity spent on bugs",
            "actionable_recommendation": (
                "Monitor closely - consider investing in bug prevention and "
                "automated testing"
            ),
        }

    return None


def check_long_resolution_time(metrics: dict, thresholds: dict) -> dict | None:

    avg_days = metrics.get("avg_resolution_time_days", 0.0)

    warning_threshold = thresholds.get("avg_resolution_days_warning", 14)
    critical_threshold = thresholds.get("avg_resolution_days_critical", 30)

    if avg_days >= critical_threshold:
        return {
            "type": InsightType.LONG_RESOLUTION_TIME,
            "severity": InsightSeverity.CRITICAL,
            "message": (
                f"Critical: Bugs taking {avg_days:.1f} days to resolve on average"
            ),
            "actionable_recommendation": (
                "Immediate action - review bug triage process and ensure "
                "bugs are prioritized appropriately"
            ),
        }
    elif avg_days >= warning_threshold:
        return {
            "type": InsightType.LONG_RESOLUTION_TIME,
            "severity": InsightSeverity.HIGH,
            "message": f"Slow resolution: Average {avg_days:.1f} days to close bugs",
            "actionable_recommendation": (
                "Consider dedicating more resources to bug resolution or "
                "improving development workflow"
            ),
        }

    return None
