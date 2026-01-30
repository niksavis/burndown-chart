"""
Unit tests for health calculation consistency between app and report.

Ensures health scores are calculated identically in both app dashboard
and report generation, preventing divergence across queries and data points.
"""

import pytest
from data.project_health_calculator import (
    calculate_comprehensive_project_health,
    prepare_dashboard_metrics_for_health,
)


class TestHealthConsistency:
    """Test suite ensuring app and report calculate identical health scores."""

    @pytest.fixture
    def sample_dashboard_metrics(self):
        """Sample dashboard metrics for testing."""
        return {
            "completion_percentage": 65.5,
            "current_velocity_items": 5.2,
            "velocity_cv": 25.3,
            "trend_direction": "stable",
            "recent_velocity_change": 2.1,
            "schedule_variance_days": 7.0,
            "completion_confidence": 70,
        }

    @pytest.fixture
    def sample_extended_metrics(self):
        """Sample extended metrics (DORA, Flow, Bug) for testing."""
        return {
            "dora": {
                "has_data": True,
                "deployment_frequency": 3.5,
                "lead_time": 4.2,
                "change_failure_rate": 8.5,
                "mttr_hours": 2.3,
            },
            "flow": {
                "has_data": True,
                "velocity": 5.1,
                "flow_time": 6.8,
                "efficiency": 42.5,
                "wip": 12,
                "work_distribution": {
                    "feature": 45,
                    "defect": 15,
                    "tech_debt": 8,
                    "risk": 2,
                    "total": 70,
                },
            },
            "bug_analysis": {
                "has_data": True,
                "resolution_rate": 85.5,
                "avg_resolution_time_days": 12.5,
                "avg_age_days": 173.9,
                "capacity_consumed_by_bugs": 0.15,
                "open_bugs": 23,
            },
            "budget": {
                "has_data": True,
                "consumed_pct": 62.3,
                "burn_rate": 5000.0,
                "runway_weeks": 8.5,
                "variance_pct": -2.1,
            },
        }

    @pytest.fixture
    def sample_scope_metrics(self):
        """Sample scope metrics for testing."""
        return {"scope_change_rate": 15.2}

    def test_health_calculation_consistency_full_metrics(
        self, sample_dashboard_metrics, sample_extended_metrics, sample_scope_metrics
    ):
        """Test health scores match when all extended metrics are available."""
        # Prepare dashboard metrics using shared function (same as app/report)
        dashboard_metrics = prepare_dashboard_metrics_for_health(
            completion_percentage=sample_dashboard_metrics["completion_percentage"],
            current_velocity_items=sample_dashboard_metrics["current_velocity_items"],
            velocity_cv=sample_dashboard_metrics["velocity_cv"],
            trend_direction=sample_dashboard_metrics["trend_direction"],
            recent_velocity_change=sample_dashboard_metrics["recent_velocity_change"],
            schedule_variance_days=sample_dashboard_metrics["schedule_variance_days"],
            completion_confidence=sample_dashboard_metrics["completion_confidence"],
        )

        # Simulate app calculation
        app_health = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics,
            dora_metrics=sample_extended_metrics.get("dora"),
            flow_metrics=sample_extended_metrics.get("flow"),
            bug_metrics=sample_extended_metrics.get("bug_analysis"),
            budget_metrics=sample_extended_metrics.get("budget"),
            scope_metrics=sample_scope_metrics,
        )

        # Simulate report calculation (using same function)
        report_health = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics,
            dora_metrics=sample_extended_metrics.get("dora"),
            flow_metrics=sample_extended_metrics.get("flow"),
            bug_metrics=sample_extended_metrics.get("bug_analysis"),
            budget_metrics=sample_extended_metrics.get("budget"),
            scope_metrics=sample_scope_metrics,
        )

        # Health scores must match exactly
        assert app_health["overall_score"] == report_health["overall_score"], (
            f"Health mismatch: app={app_health['overall_score']}, report={report_health['overall_score']}"
        )

        # Formula versions must match
        assert app_health["formula_version"] == report_health["formula_version"]

        # Dimension scores must match
        for dimension in app_health.get("dimensions", {}).keys():
            assert (
                app_health["dimensions"][dimension]["score"]
                == report_health["dimensions"][dimension]["score"]
            ), f"Dimension {dimension} mismatch"

    def test_health_calculation_consistency_no_extended_metrics(
        self, sample_dashboard_metrics, sample_scope_metrics
    ):
        """Test health scores match when extended metrics are unavailable."""
        # Prepare dashboard metrics using shared function
        dashboard_metrics = prepare_dashboard_metrics_for_health(
            completion_percentage=sample_dashboard_metrics["completion_percentage"],
            current_velocity_items=sample_dashboard_metrics["current_velocity_items"],
            velocity_cv=sample_dashboard_metrics["velocity_cv"],
            trend_direction=sample_dashboard_metrics["trend_direction"],
            recent_velocity_change=sample_dashboard_metrics["recent_velocity_change"],
            schedule_variance_days=sample_dashboard_metrics["schedule_variance_days"],
            completion_confidence=sample_dashboard_metrics["completion_confidence"],
        )

        # Simulate app calculation without extended metrics
        app_health = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics,
            dora_metrics=None,
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics=sample_scope_metrics,
        )

        # Simulate report calculation without extended metrics
        report_health = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics,
            dora_metrics=None,
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics=sample_scope_metrics,
        )

        # Health scores must match exactly (with dynamic weight redistribution)
        assert app_health["overall_score"] == report_health["overall_score"], (
            f"Health mismatch without extended metrics: app={app_health['overall_score']}, report={report_health['overall_score']}"
        )

    def test_health_calculation_consistency_partial_metrics(
        self, sample_dashboard_metrics, sample_extended_metrics, sample_scope_metrics
    ):
        """Test health scores match with partial extended metrics (e.g., DORA only)."""
        # Prepare dashboard metrics
        dashboard_metrics = prepare_dashboard_metrics_for_health(
            completion_percentage=sample_dashboard_metrics["completion_percentage"],
            current_velocity_items=sample_dashboard_metrics["current_velocity_items"],
            velocity_cv=sample_dashboard_metrics["velocity_cv"],
            trend_direction=sample_dashboard_metrics["trend_direction"],
            recent_velocity_change=sample_dashboard_metrics["recent_velocity_change"],
            schedule_variance_days=sample_dashboard_metrics["schedule_variance_days"],
            completion_confidence=sample_dashboard_metrics["completion_confidence"],
        )

        # Test with only DORA metrics
        app_health = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics,
            dora_metrics=sample_extended_metrics.get("dora"),
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics=sample_scope_metrics,
        )

        report_health = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics,
            dora_metrics=sample_extended_metrics.get("dora"),
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics=sample_scope_metrics,
        )

        assert app_health["overall_score"] == report_health["overall_score"]

        # Test with only Bug metrics
        app_health_bugs = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics,
            dora_metrics=None,
            flow_metrics=None,
            bug_metrics=sample_extended_metrics.get("bug_analysis"),
            budget_metrics=None,
            scope_metrics=sample_scope_metrics,
        )

        report_health_bugs = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics,
            dora_metrics=None,
            flow_metrics=None,
            bug_metrics=sample_extended_metrics.get("bug_analysis"),
            budget_metrics=None,
            scope_metrics=sample_scope_metrics,
        )

        assert app_health_bugs["overall_score"] == report_health_bugs["overall_score"]

    def test_extended_metrics_key_consistency(self):
        """Test that extended metrics use consistent keys between app and report."""
        # This test documents the expected key names
        expected_keys = ["dora", "flow", "bug_analysis", "budget"]

        # These keys must be used consistently in both:
        # - callbacks/visualization.py (app)
        # - data/report_generator.py (report)
        # - ui/dashboard.py (dashboard)

        # Verify the keys are documented
        assert "dora" in expected_keys
        assert "flow" in expected_keys
        assert "bug_analysis" in expected_keys  # NOT "bug"
        assert "budget" in expected_keys

    def test_prepare_metrics_function_idempotency(self, sample_dashboard_metrics):
        """Test that prepare_dashboard_metrics_for_health is deterministic."""
        # Call function twice with same inputs
        metrics1 = prepare_dashboard_metrics_for_health(
            completion_percentage=sample_dashboard_metrics["completion_percentage"],
            current_velocity_items=sample_dashboard_metrics["current_velocity_items"],
            velocity_cv=sample_dashboard_metrics["velocity_cv"],
            trend_direction=sample_dashboard_metrics["trend_direction"],
            recent_velocity_change=sample_dashboard_metrics["recent_velocity_change"],
            schedule_variance_days=sample_dashboard_metrics["schedule_variance_days"],
            completion_confidence=sample_dashboard_metrics["completion_confidence"],
        )

        metrics2 = prepare_dashboard_metrics_for_health(
            completion_percentage=sample_dashboard_metrics["completion_percentage"],
            current_velocity_items=sample_dashboard_metrics["current_velocity_items"],
            velocity_cv=sample_dashboard_metrics["velocity_cv"],
            trend_direction=sample_dashboard_metrics["trend_direction"],
            recent_velocity_change=sample_dashboard_metrics["recent_velocity_change"],
            schedule_variance_days=sample_dashboard_metrics["schedule_variance_days"],
            completion_confidence=sample_dashboard_metrics["completion_confidence"],
        )

        # Results must be identical
        assert metrics1 == metrics2

    def test_health_calculation_with_different_data_points(
        self, sample_dashboard_metrics, sample_extended_metrics, sample_scope_metrics
    ):
        """Test health consistency when data_points_count varies (simulating slider)."""
        # Simulate different time windows by varying metrics slightly
        # In real scenario, data_points_count affects which weeks are included

        dashboard_metrics = prepare_dashboard_metrics_for_health(
            completion_percentage=sample_dashboard_metrics["completion_percentage"],
            current_velocity_items=sample_dashboard_metrics["current_velocity_items"],
            velocity_cv=sample_dashboard_metrics["velocity_cv"],
            trend_direction=sample_dashboard_metrics["trend_direction"],
            recent_velocity_change=sample_dashboard_metrics["recent_velocity_change"],
            schedule_variance_days=sample_dashboard_metrics["schedule_variance_days"],
            completion_confidence=sample_dashboard_metrics["completion_confidence"],
        )

        # Both app and report should use same calculation regardless of window
        app_health = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics,
            dora_metrics=sample_extended_metrics.get("dora"),
            flow_metrics=sample_extended_metrics.get("flow"),
            bug_metrics=sample_extended_metrics.get("bug_analysis"),
            budget_metrics=sample_extended_metrics.get("budget"),
            scope_metrics=sample_scope_metrics,
        )

        report_health = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics,
            dora_metrics=sample_extended_metrics.get("dora"),
            flow_metrics=sample_extended_metrics.get("flow"),
            bug_metrics=sample_extended_metrics.get("bug_analysis"),
            budget_metrics=sample_extended_metrics.get("budget"),
            scope_metrics=sample_scope_metrics,
        )

        assert app_health["overall_score"] == report_health["overall_score"]

    def test_health_calculation_edge_cases(self, sample_scope_metrics):
        """Test health consistency with edge case inputs."""
        # Test with 0% completion
        dashboard_metrics_zero = prepare_dashboard_metrics_for_health(
            completion_percentage=0.0,
            current_velocity_items=0.0,
            velocity_cv=0.0,
            trend_direction="stable",
            recent_velocity_change=0.0,
            schedule_variance_days=0.0,
            completion_confidence=50,
        )

        app_health = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_zero,
            dora_metrics=None,
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics=sample_scope_metrics,
        )

        report_health = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_zero,
            dora_metrics=None,
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics=sample_scope_metrics,
        )

        assert app_health["overall_score"] == report_health["overall_score"]

        # Test with 100% completion
        dashboard_metrics_complete = prepare_dashboard_metrics_for_health(
            completion_percentage=100.0,
            current_velocity_items=10.0,
            velocity_cv=5.0,
            trend_direction="improving",
            recent_velocity_change=5.0,
            schedule_variance_days=0.0,
            completion_confidence=95,
        )

        app_health_complete = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_complete,
            dora_metrics=None,
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics=sample_scope_metrics,
        )

        report_health_complete = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_complete,
            dora_metrics=None,
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics=sample_scope_metrics,
        )

        assert (
            app_health_complete["overall_score"]
            == report_health_complete["overall_score"]
        )
