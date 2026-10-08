import pytest

from data.project_health_calculator import calculate_comprehensive_project_health


class TestProjectHealthCalculator:
    @pytest.fixture
    def minimal_dashboard_metrics(self):
        return {
            "completion_percentage": 50.0,
            "current_velocity_items": 5.0,
            "velocity_cv": 30.0,
            "trend_direction": "stable",
            "recent_velocity_change": 0.0,
            "schedule_variance_days": 0,
            "completion_confidence": 75,
        }

    @pytest.fixture
    def healthy_project_metrics(self):
        return {
            "dashboard": {
                "completion_percentage": 75.0,
                "current_velocity_items": 8.0,
                "velocity_cv": 20.0,
                "trend_direction": "improving",
                "recent_velocity_change": 10.0,
                "schedule_variance_days": -5,
                "completion_confidence": 85,
            },
            "dora": {
                "has_data": True,
                "deployment_frequency": 5.0,
                "lead_time": 2.0,
                "change_failure_rate": 5.0,
                "mttr_hours": 4.0,
            },
            "flow": {
                "has_data": True,
                "velocity": 8.0,
                "flow_time": 4.0,
                "efficiency": 40.0,
                "wip": 10,
                "work_distribution": {
                    "total": 100,
                    "feature": 65,
                    "defect": 20,
                    "tech_debt": 15,
                },
            },
            "bug": {
                "has_data": True,
                "resolution_rate": 0.90,
                "avg_resolution_time_days": 3.0,
                "capacity_consumed_by_bugs": 0.15,
                "open_bugs": 5,
            },
            "budget": {
                "has_data": True,
                "variance": {
                    "burn_rate_variance_pct": 3.0,
                    "runway_vs_baseline_pct": 5.0,
                    "utilization_vs_pace_pct": 4.0,
                },
            },
            "scope": {"scope_change_rate": 20.0},
        }

    @pytest.fixture
    def at_risk_project_metrics(self):
        return {
            "dashboard": {
                "completion_percentage": 25.0,
                "current_velocity_items": 2.0,
                "velocity_cv": 80.0,
                "trend_direction": "declining",
                "recent_velocity_change": -15.0,
                "schedule_variance_days": 20,
                "completion_confidence": 40,
            },
            "dora": {
                "has_data": True,
                "deployment_frequency": 0.5,
                "lead_time": 30.0,
                "change_failure_rate": 25.0,
                "mttr_hours": 48.0,
            },
            "flow": {
                "has_data": True,
                "velocity": 2.0,
                "flow_time": 15.0,
                "efficiency": 15.0,
                "wip": 20,
                "work_distribution": {
                    "total": 100,
                    "feature": 40,
                    "defect": 50,
                    "tech_debt": 10,
                },
            },
            "scope": {"scope_change_rate": 150.0},
        }

    def test_returns_required_fields(self, minimal_dashboard_metrics):
        result = calculate_comprehensive_project_health(
            dashboard_metrics=minimal_dashboard_metrics,
            scope_metrics={"scope_change_rate": 50.0},
        )

        assert "overall_score" in result
        assert "dimensions" in result
        assert "project_stage" in result
        assert "completion_percentage" in result
        assert "formula_version" in result
        assert "timestamp" in result

        assert isinstance(result["overall_score"], int)
        assert 0 <= result["overall_score"] <= 100
        assert result["formula_version"] == "3.0"

    def test_six_dimensions_present(self, minimal_dashboard_metrics):
        result = calculate_comprehensive_project_health(
            dashboard_metrics=minimal_dashboard_metrics,
            scope_metrics={"scope_change_rate": 50.0},
        )

        dimensions = result["dimensions"]
        assert len(dimensions) == 6
        assert "delivery" in dimensions
        assert "predictability" in dimensions
        assert "quality" in dimensions
        assert "efficiency" in dimensions
        assert "sustainability" in dimensions
        assert "financial" in dimensions

    def test_dimension_structure(self, minimal_dashboard_metrics):
        result = calculate_comprehensive_project_health(
            dashboard_metrics=minimal_dashboard_metrics,
            scope_metrics={"scope_change_rate": 50.0},
        )

        for dim_name, dim_data in result["dimensions"].items():
            assert "score" in dim_data, f"Missing 'score' in {dim_name}"
            assert "weight" in dim_data, f"Missing 'weight' in {dim_name}"
            assert "max_weight" in dim_data, f"Missing 'max_weight' in {dim_name}"

            assert isinstance(dim_data["score"], (int, float))
            assert isinstance(dim_data["weight"], (int, float))
            assert isinstance(dim_data["max_weight"], (int, float))

            assert 0 <= dim_data["score"] <= 100
            assert 0 <= dim_data["weight"] <= 100
            assert 0 < dim_data["max_weight"] <= 100

    def test_weight_redistribution_sums_to_100(self, minimal_dashboard_metrics):
        result = calculate_comprehensive_project_health(
            dashboard_metrics=minimal_dashboard_metrics,
            scope_metrics={"scope_change_rate": 50.0},
        )

        total_weight = sum(d["weight"] for d in result["dimensions"].values())
        assert abs(total_weight - 100.0) < 0.1, (
            f"Weights don't sum to 100%: {total_weight}"
        )

    def test_dashboard_only_uses_core_dimensions(self, minimal_dashboard_metrics):
        result = calculate_comprehensive_project_health(
            dashboard_metrics=minimal_dashboard_metrics,
            dora_metrics=None,
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics={"scope_change_rate": 50.0},
        )

        assert result["dimensions"]["delivery"]["weight"] > 0
        assert result["dimensions"]["predictability"]["weight"] > 0
        assert result["dimensions"]["sustainability"]["weight"] > 0

        assert result["dimensions"]["quality"]["weight"] == 0
        assert result["dimensions"]["efficiency"]["weight"] == 0
        assert result["dimensions"]["financial"]["weight"] == 0

    def test_all_metrics_activates_all_dimensions(self, healthy_project_metrics):
        metrics = healthy_project_metrics
        result = calculate_comprehensive_project_health(
            dashboard_metrics=metrics["dashboard"],
            dora_metrics=metrics["dora"],
            flow_metrics=metrics["flow"],
            bug_metrics=metrics["bug"],
            budget_metrics=metrics["budget"],
            scope_metrics=metrics["scope"],
        )

        for dim_name, dim_data in result["dimensions"].items():
            assert dim_data["weight"] > 0, f"{dim_name} should have weight"

    def test_healthy_project_scores_good(self, healthy_project_metrics):
        metrics = healthy_project_metrics
        result = calculate_comprehensive_project_health(
            dashboard_metrics=metrics["dashboard"],
            dora_metrics=metrics["dora"],
            flow_metrics=metrics["flow"],
            bug_metrics=metrics["bug"],
            budget_metrics=metrics["budget"],
            scope_metrics=metrics["scope"],
        )

        assert result["overall_score"] >= 70, (
            f"Healthy project should score 70+, got {result['overall_score']}"
        )

    def test_at_risk_project_scores_low(self, at_risk_project_metrics):
        metrics = at_risk_project_metrics
        result = calculate_comprehensive_project_health(
            dashboard_metrics=metrics["dashboard"],
            dora_metrics=metrics["dora"],
            flow_metrics=metrics["flow"],
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics=metrics["scope"],
        )

        assert result["overall_score"] < 50, (
            f"At-risk project should score < 50, got {result['overall_score']}"
        )

    def test_project_stage_detection(self):
        result = calculate_comprehensive_project_health(
            dashboard_metrics={"completion_percentage": 15.0},
            scope_metrics={"scope_change_rate": 50.0},
        )
        assert result["project_stage"] == "inception"

        result = calculate_comprehensive_project_health(
            dashboard_metrics={"completion_percentage": 35.0},
            scope_metrics={"scope_change_rate": 50.0},
        )
        assert result["project_stage"] == "early"

        result = calculate_comprehensive_project_health(
            dashboard_metrics={"completion_percentage": 60.0},
            scope_metrics={"scope_change_rate": 50.0},
        )
        assert result["project_stage"] == "mid"

        result = calculate_comprehensive_project_health(
            dashboard_metrics={"completion_percentage": 85.0},
            scope_metrics={"scope_change_rate": 50.0},
        )
        assert result["project_stage"] == "late"

    def test_context_aware_scope_penalty(self):
        high_scope = {"scope_change_rate": 200.0}

        early_result = calculate_comprehensive_project_health(
            dashboard_metrics={"completion_percentage": 35.0},
            scope_metrics=high_scope,
        )

        late_result = calculate_comprehensive_project_health(
            dashboard_metrics={"completion_percentage": 85.0},
            scope_metrics=high_scope,
        )

        early_sustain = early_result["dimensions"]["sustainability"]["score"]
        late_sustain = late_result["dimensions"]["sustainability"]["score"]

        assert early_sustain > late_sustain, (
            "Early stage should have lighter scope penalty than late stage"
        )

    def test_partial_metrics_weight_redistribution(self, minimal_dashboard_metrics):
        dora = {
            "has_data": True,
            "deployment_frequency": 3.0,
            "lead_time": 5.0,
            "change_failure_rate": 10.0,
            "mttr_hours": 12.0,
        }

        result = calculate_comprehensive_project_health(
            dashboard_metrics=minimal_dashboard_metrics,
            dora_metrics=dora,
            flow_metrics=None,
            bug_metrics=None,
            budget_metrics=None,
            scope_metrics={"scope_change_rate": 50.0},
        )

        assert result["dimensions"]["quality"]["weight"] > 0

        assert result["dimensions"]["efficiency"]["weight"] == 0

        assert result["dimensions"]["financial"]["weight"] == 0

        total_weight = sum(d["weight"] for d in result["dimensions"].values())
        assert abs(total_weight - 100.0) < 0.1

    def test_formula_version_always_3_0(self, minimal_dashboard_metrics):
        result1 = calculate_comprehensive_project_health(
            dashboard_metrics=minimal_dashboard_metrics,
            scope_metrics={"scope_change_rate": 50.0},
        )
        assert result1["formula_version"] == "3.0"

        result2 = calculate_comprehensive_project_health(
            dashboard_metrics=minimal_dashboard_metrics,
            dora_metrics={"has_data": True},
            flow_metrics={"has_data": True},
            bug_metrics={"has_data": True},
            budget_metrics={"has_data": True},
            scope_metrics={"scope_change_rate": 50.0},
        )
        assert result2["formula_version"] == "3.0"

    def test_high_cv_gets_partial_credit(self):
        result = calculate_comprehensive_project_health(
            dashboard_metrics={
                "completion_percentage": 50.0,
                "velocity_cv": 150.0,
                "trend_direction": "stable",
            },
            scope_metrics={"scope_change_rate": 50.0},
        )

        predictability_score = result["dimensions"]["predictability"]["score"]
        assert predictability_score > 0, "High CV should still get some credit"

    def test_improving_trend_scores_higher_than_declining(self):
        improving = calculate_comprehensive_project_health(
            dashboard_metrics={
                "completion_percentage": 50.0,
                "velocity_cv": 30.0,
                "trend_direction": "improving",
                "recent_velocity_change": 10.0,
            },
            scope_metrics={"scope_change_rate": 50.0},
        )

        declining = calculate_comprehensive_project_health(
            dashboard_metrics={
                "completion_percentage": 50.0,
                "velocity_cv": 30.0,
                "trend_direction": "declining",
                "recent_velocity_change": -10.0,
            },
            scope_metrics={"scope_change_rate": 50.0},
        )

        assert improving["overall_score"] > declining["overall_score"], (
            "Improving trend should score higher than declining"
        )
