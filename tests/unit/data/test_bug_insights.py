from datetime import datetime, timedelta

from data.bug_insights import (
    InsightSeverity,
    InsightType,
    generate_quality_insights,
)


class TestGenerateQualityInsights:
    def test_generate_quality_insights_basic(self):
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

        assert isinstance(insights, list)
        if insights:
            assert "type" in insights[0]
            assert "severity" in insights[0]
            assert "message" in insights[0]
            assert "actionable_recommendation" in insights[0]

    def test_generate_quality_insights_empty_data(self):
        metrics = {
            "total_bugs": 0,
            "open_bugs": 0,
            "closed_bugs": 0,
            "resolution_rate": 0.0,
        }

        statistics = []

        insights = generate_quality_insights(metrics, statistics)

        assert isinstance(insights, list)

    def test_insight_low_resolution_rate(self):
        metrics = {
            "total_bugs": 100,
            "open_bugs": 70,
            "closed_bugs": 30,
            "resolution_rate": 0.30,
        }

        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 10, "bugs_resolved": 5},
        ]

        insights = generate_quality_insights(metrics, statistics)

        low_res_insights = [
            i for i in insights if "resolution rate" in i["message"].lower()
        ]
        assert len(low_res_insights) > 0
        assert low_res_insights[0]["severity"] in [
            InsightSeverity.HIGH,
            InsightSeverity.CRITICAL,
        ]

    def test_insight_increasing_bug_trend(self):
        metrics = {
            "total_bugs": 50,
            "open_bugs": 20,
            "closed_bugs": 30,
            "resolution_rate": 0.60,
        }

        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 8, "bugs_resolved": 3},
            {"week_start": "2025-01-08", "bugs_created": 10, "bugs_resolved": 4},
            {"week_start": "2025-01-15", "bugs_created": 12, "bugs_resolved": 5},
            {"week_start": "2025-01-22", "bugs_created": 9, "bugs_resolved": 6},
        ]

        insights = generate_quality_insights(metrics, statistics)

        trend_insights = [
            i
            for i in insights
            if "trend" in i["message"].lower() or "increasing" in i["message"].lower()
        ]
        assert len(trend_insights) > 0

    def test_insight_positive_trend(self):
        metrics = {
            "total_bugs": 50,
            "open_bugs": 5,
            "closed_bugs": 45,
            "resolution_rate": 0.90,
        }

        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 3, "bugs_resolved": 8},
            {"week_start": "2025-01-08", "bugs_created": 2, "bugs_resolved": 7},
            {"week_start": "2025-01-15", "bugs_created": 4, "bugs_resolved": 9},
        ]

        insights = generate_quality_insights(metrics, statistics)

        positive_insights = [
            i for i in insights if i["severity"] == InsightSeverity.LOW
        ]
        assert len(positive_insights) > 0

    def test_insights_prioritization(self):
        metrics = {
            "total_bugs": 100,
            "open_bugs": 80,
            "closed_bugs": 20,
            "resolution_rate": 0.20,
        }

        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 20, "bugs_resolved": 2},
            {"week_start": "2025-01-08", "bugs_created": 25, "bugs_resolved": 3},
            {"week_start": "2025-01-15", "bugs_created": 30, "bugs_resolved": 2},
        ]

        insights = generate_quality_insights(metrics, statistics)

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
        metrics = {
            "total_bugs": 50,
            "open_bugs": 20,
            "closed_bugs": 30,
            "resolution_rate": 0.75,
        }

        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 5, "bugs_resolved": 7},
        ]

        insights_default = generate_quality_insights(metrics, statistics)
        low_res_warnings = [
            i
            for i in insights_default
            if "resolution rate" in i["message"].lower()
            and i["severity"] in [InsightSeverity.HIGH, InsightSeverity.CRITICAL]
        ]
        assert len(low_res_warnings) == 0

        custom_thresholds = {"min_resolution_rate": 0.80}
        insights_custom = generate_quality_insights(
            metrics, statistics, thresholds=custom_thresholds
        )
        assert isinstance(insights_custom, list)

    def test_insights_max_limit(self):
        metrics = {
            "total_bugs": 200,
            "open_bugs": 150,
            "closed_bugs": 50,
            "resolution_rate": 0.25,
        }

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

        assert len(insights) <= 10

    def test_insight_stable_quality(self):
        metrics = {
            "total_bugs": 40,
            "open_bugs": 10,
            "closed_bugs": 30,
            "resolution_rate": 0.75,
        }

        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 5, "bugs_resolved": 5},
            {"week_start": "2025-01-08", "bugs_created": 6, "bugs_resolved": 6},
            {"week_start": "2025-01-15", "bugs_created": 5, "bugs_resolved": 5},
            {"week_start": "2025-01-22", "bugs_created": 4, "bugs_resolved": 4},
        ]

        insights = generate_quality_insights(metrics, statistics)

        assert isinstance(insights, list)

    def test_insight_no_open_bugs(self):
        metrics = {
            "total_bugs": 50,
            "open_bugs": 0,
            "closed_bugs": 50,
            "resolution_rate": 1.0,
        }

        statistics = [
            {"week_start": "2025-01-01", "bugs_created": 5, "bugs_resolved": 10},
        ]

        insights = generate_quality_insights(metrics, statistics)

        zero_bugs_insights = [
            i
            for i in insights
            if "no open bugs" in i["message"].lower()
            or "all bugs resolved" in i["message"].lower()
        ]
        assert len(zero_bugs_insights) > 0
        assert zero_bugs_insights[0]["severity"] == InsightSeverity.LOW


class TestInsightTypes:
    def test_insight_type_exists(self):
        assert hasattr(InsightType, "__members__")
        expected_types = [
            "RESOLUTION_RATE",
            "BUG_TREND",
            "POSITIVE_TREND",
            "STABLE_QUALITY",
        ]
        for type_name in expected_types:
            assert hasattr(InsightType, type_name), f"Missing InsightType.{type_name}"

    def test_insight_severity_exists(self):
        assert hasattr(InsightSeverity, "__members__")
        assert hasattr(InsightSeverity, "CRITICAL")
        assert hasattr(InsightSeverity, "HIGH")
        assert hasattr(InsightSeverity, "MEDIUM")
        assert hasattr(InsightSeverity, "LOW")
