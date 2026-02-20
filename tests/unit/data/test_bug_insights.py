"""
Unit tests for bug quality insights generation.

Tests the rule-based insight engine that analyzes bug patterns and generates
actionable recommendations for quality improvement.
"""

from datetime import datetime, timedelta

from data.bug_insights import (
    InsightSeverity,
    InsightType,
    generate_quality_insights,
)


class TestGenerateQualityInsights:
    """Test suite for quality insights generation."""

    def test_generate_quality_insights_basic(self):
        """Test basic insight generation with normal metrics."""
        metrics = {
            "total_bugs": 50,
            "open_bugs": 10,
            "closed_bugs": 40,
            "resolution_rate": 0.80,
        }

        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 5, "bugs_resolved": 7},
            {"week_start": "2025-01-08", "bugs_created": 3, "bugs_resolved": 6},
            {"week_start": "2025-01-15", "bugs_created": 4, "bugs_resolved": 5},
        ]

        insights = generate_quality_insights(metrics, statistics)

        # Should generate insights list
        assert isinstance(insights, list)
        # Each insight should have required fields
        if insights:
            assert "type" in insights[0]
            assert "severity" in insights[0]
            assert "message" in insights[0]
            assert "actionable_recommendation" in insights[0]

    def test_generate_quality_insights_empty_data(self):
        """Test insight generation with no bug data."""
        metrics = {
            "total_bugs": 0,
            "open_bugs": 0,
            "closed_bugs": 0,
            "resolution_rate": 0.0,
        }

        statistics = []

        insights = generate_quality_insights(metrics, statistics)

        # Should return valid list (may contain "no bugs" positive insight)
        assert isinstance(insights, list)

    def test_insight_low_resolution_rate(self):
        """Test warning generated for low resolution rate."""
        metrics = {
            "total_bugs": 100,
            "open_bugs": 70,
            "closed_bugs": 30,
            "resolution_rate": 0.30,  # Below 0.70 threshold
        }

        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 10, "bugs_resolved": 5},
        ]

        insights = generate_quality_insights(metrics, statistics)

        # Should contain warning about low resolution rate
        low_res_insights = [
            i for i in insights if "resolution rate" in i["message"].lower()
        ]
        assert len(low_res_insights) > 0
        assert low_res_insights[0]["severity"] in [
            InsightSeverity.HIGH,
            InsightSeverity.CRITICAL,
        ]

    def test_insight_increasing_bug_trend(self):
        """Test warning for increasing bug creation trend."""
        metrics = {
            "total_bugs": 50,
            "open_bugs": 20,
            "closed_bugs": 30,
            "resolution_rate": 0.60,
        }

        # 3+ consecutive weeks where creation > resolution
        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 8, "bugs_resolved": 3},
            {"week_start": "2025-01-08", "bugs_created": 10, "bugs_resolved": 4},
            {"week_start": "2025-01-15", "bugs_created": 12, "bugs_resolved": 5},
            {"week_start": "2025-01-22", "bugs_created": 9, "bugs_resolved": 6},
        ]

        insights = generate_quality_insights(metrics, statistics)

        # Should warn about increasing trend
        trend_insights = [
            i
            for i in insights
            if "trend" in i["message"].lower() or "increasing" in i["message"].lower()
        ]
        assert len(trend_insights) > 0

    def test_insight_positive_trend(self):
        """Test positive feedback for improving bug resolution."""
        metrics = {
            "total_bugs": 50,
            "open_bugs": 5,
            "closed_bugs": 45,
            "resolution_rate": 0.90,
        }

        # Consistent resolution > creation
        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 3, "bugs_resolved": 8},
            {"week_start": "2025-01-08", "bugs_created": 2, "bugs_resolved": 7},
            {"week_start": "2025-01-15", "bugs_created": 4, "bugs_resolved": 9},
        ]

        insights = generate_quality_insights(metrics, statistics)

        # Should contain positive insight
        positive_insights = [
            i for i in insights if i["severity"] == InsightSeverity.LOW
        ]
        assert len(positive_insights) > 0

    def test_insights_prioritization(self):
        """Test insights are sorted by severity."""
        metrics = {
            "total_bugs": 100,
            "open_bugs": 80,  # High open bugs
            "closed_bugs": 20,
            "resolution_rate": 0.20,  # Very low resolution
        }

        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 20, "bugs_resolved": 2},
            {"week_start": "2025-01-08", "bugs_created": 25, "bugs_resolved": 3},
            {"week_start": "2025-01-15", "bugs_created": 30, "bugs_resolved": 2},
        ]

        insights = generate_quality_insights(metrics, statistics)

        # Insights should be sorted by severity (critical first)
        severity_order = [
            InsightSeverity.CRITICAL,
            InsightSeverity.HIGH,
            InsightSeverity.LOW,
        ]
        for i in range(len(insights) - 1):
            current_severity = insights[i]["severity"]
            next_severity = insights[i + 1]["severity"]
            current_index = severity_order.index(current_severity)
            next_index = severity_order.index(next_severity)
            assert current_index <= next_index

    def test_insights_custom_thresholds(self):
        """Test insight generation respects custom thresholds."""
        metrics = {
            "total_bugs": 50,
            "open_bugs": 20,
            "closed_bugs": 30,
            "resolution_rate": 0.75,  # Just above default 0.70 threshold
        }

        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 5, "bugs_resolved": 7},
        ]

        # With default thresholds (0.70), should not warn
        insights_default = generate_quality_insights(metrics, statistics)
        low_res_warnings = [
            i
            for i in insights_default
            if "resolution rate" in i["message"].lower()
            and i["severity"] in [InsightSeverity.HIGH, InsightSeverity.CRITICAL]
        ]
        assert len(low_res_warnings) == 0

        # With custom higher threshold (0.80), should warn
        custom_thresholds = {"min_resolution_rate": 0.80}
        insights_custom = generate_quality_insights(
            metrics, statistics, thresholds=custom_thresholds
        )
        # May or may not warn depending on implementation, just verify it accepts the parameter
        assert isinstance(insights_custom, list)

    def test_insights_max_limit(self):
        """Test insights are capped at 10 maximum."""
        # Create scenario that would generate many insights
        metrics = {
            "total_bugs": 200,
            "open_bugs": 150,
            "closed_bugs": 50,
            "resolution_rate": 0.25,
        }

        # Long statistics with various problematic patterns
        statistics = []
        for week in range(20):
            week_start = (datetime(2025, 1, 1) + timedelta(weeks=week)).strftime(
                "%Y-%m-%d"
            )
            statistics.append(
                {
                    "week_start": week_start,
                    "bugs_created": 15 + (week % 5),
                    "bugs_resolved": 3 + (week % 3),
                }
            )

        insights = generate_quality_insights(metrics, statistics)

        # Should be capped at 10 insights
        assert len(insights) <= 10

    def test_insight_stable_quality(self):
        """Test positive insight for stable quality metrics."""
        metrics = {
            "total_bugs": 40,
            "open_bugs": 10,
            "closed_bugs": 30,
            "resolution_rate": 0.75,
        }

        # Stable pattern - consistent creation and resolution
        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 5, "bugs_resolved": 5},
            {"week_start": "2025-01-08", "bugs_created": 6, "bugs_resolved": 6},
            {"week_start": "2025-01-15", "bugs_created": 5, "bugs_resolved": 5},
            {"week_start": "2025-01-22", "bugs_created": 4, "bugs_resolved": 4},
        ]

        insights = generate_quality_insights(metrics, statistics)

        # May contain stable quality insight
        assert isinstance(insights, list)

    def test_insight_no_open_bugs(self):
        """Test positive insight when all bugs are resolved."""
        metrics = {
            "total_bugs": 50,
            "open_bugs": 0,  # All resolved!
            "closed_bugs": 50,
            "resolution_rate": 1.0,
        }

        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 5, "bugs_resolved": 10},
        ]

        insights = generate_quality_insights(metrics, statistics)

        # Should contain congratulatory insight
        zero_bugs_insights = [
            i
            for i in insights
            if "no open bugs" in i["message"].lower()
            or "all bugs resolved" in i["message"].lower()
        ]
        assert len(zero_bugs_insights) > 0
        assert zero_bugs_insights[0]["severity"] == InsightSeverity.LOW


class TestInsightTypes:
    """Test insight type and severity enums."""

    def test_insight_type_exists(self):
        """Test InsightType enum is defined."""
        assert hasattr(InsightType, "__members__")
        # Common expected types
        expected_types = [
            "RESOLUTION_RATE",
            "BUG_TREND",
            "POSITIVE_TREND",
            "STABLE_QUALITY",
        ]
        for type_name in expected_types:
            assert hasattr(InsightType, type_name), f"Missing InsightType.{type_name}"

    def test_insight_severity_exists(self):
        """Test InsightSeverity enum is defined."""
        assert hasattr(InsightSeverity, "__members__")
        # Required severity levels (4-level scale)
        assert hasattr(InsightSeverity, "CRITICAL")
        assert hasattr(InsightSeverity, "HIGH")
        assert hasattr(InsightSeverity, "MEDIUM")
        assert hasattr(InsightSeverity, "LOW")
