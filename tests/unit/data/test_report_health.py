def test_dashboard_metrics_uses_comprehensive_health():
    from data.report.dashboard_metrics import (
        calculate_dashboard_metrics as _calculate_dashboard_metrics,
    )

    all_statistics = [
        {
            "date": "2024-01-01",
            "week_label": "2024-W01",
            "completed_items": 5,
            "completed_points": 13,
            "created_items": 2,
            "created_points": 5,
        },
        {
            "date": "2024-01-08",
            "week_label": "2024-W02",
            "completed_items": 6,
            "completed_points": 15,
            "created_items": 1,
            "created_points": 3,
        },
        {
            "date": "2024-01-15",
            "week_label": "2024-W03",
            "completed_items": 7,
            "completed_points": 18,
            "created_items": 0,
            "created_points": 0,
        },
    ]

    windowed_statistics = all_statistics.copy()

    project_scope = {
        "remaining_items": 50,
        "remaining_total_points": 120,
    }

    settings = {
        "show_points": False,
        "data_points_count": 3,
        "deadline": "2024-06-01",
        "milestone": "Q2 Release",
        "pert_factor": 6,
    }

    result = _calculate_dashboard_metrics(
        all_statistics=all_statistics,
        windowed_statistics=windowed_statistics,
        project_scope=project_scope,
        settings=settings,
        weeks_count=3,
        show_points=False,
        extended_metrics=None,
    )

    assert result["has_data"] is True
    assert "health_score" in result
    assert "health_status" in result

    assert 0 <= result["health_score"] <= 100

    assert result["health_status"] in ["GOOD", "CAUTION", "AT RISK", "CRITICAL"]

    assert "completed_items" in result
    assert "remaining_items" in result
    assert "total_items" in result
    assert "velocity_items" in result

    assert 20 <= result["health_score"] <= 80, (
        f"Health score {result['health_score']} outside expected "
        "range for early project"
    )


def test_dashboard_metrics_with_extended_metrics():
    from data.report.dashboard_metrics import (
        calculate_dashboard_metrics as _calculate_dashboard_metrics,
    )

    all_statistics = [
        {
            "date": "2024-01-01",
            "week_label": "2024-W01",
            "completed_items": 5,
            "completed_points": 13,
            "created_items": 1,
            "created_points": 3,
        },
        {
            "date": "2024-01-08",
            "week_label": "2024-W02",
            "completed_items": 6,
            "completed_points": 15,
            "created_items": 1,
            "created_points": 3,
        },
    ]

    windowed_statistics = all_statistics.copy()

    project_scope = {
        "remaining_items": 20,
        "remaining_total_points": 50,
    }

    settings = {
        "show_points": False,
        "data_points_count": 2,
        "deadline": "2024-03-01",
        "milestone": "Q1 Release",
        "pert_factor": 6,
    }

    extended_metrics = {
        "dora": {
            "deployment_frequency_per_day": 2.0,
            "lead_time_for_changes_hours": 4.0,
            "change_failure_rate": 5.0,
            "mean_time_to_restore_hours": 2.0,
        },
        "flow": {
            "average_cycle_time_days": 5.0,
            "flow_efficiency_pct": 35.0,
        },
        "bug_analysis": {
            "total_bugs": 10,
            "open_bugs": 2,
            "resolved_bugs": 8,
            "bug_resolution_rate_pct": 80.0,
        },
        "budget": {
            "budget_spent_pct": 50.0,
            "runway_weeks": 20,
        },
    }

    result = _calculate_dashboard_metrics(
        all_statistics=all_statistics,
        windowed_statistics=windowed_statistics,
        project_scope=project_scope,
        settings=settings,
        weeks_count=2,
        show_points=False,
        extended_metrics=extended_metrics,
    )

    assert result["has_data"] is True
    assert "health_score" in result
    assert "health_status" in result

    assert 0 <= result["health_score"] <= 100

    assert result["health_status"] in ["GOOD", "CAUTION", "AT RISK", "CRITICAL"]

    assert result["health_score"] >= 30


def test_dashboard_metrics_graceful_degradation():
    from data.report.dashboard_metrics import (
        calculate_dashboard_metrics as _calculate_dashboard_metrics,
    )

    result = _calculate_dashboard_metrics(
        all_statistics=[],
        windowed_statistics=[],
        project_scope={},
        settings={},
        weeks_count=0,
        show_points=False,
        extended_metrics=None,
    )

    assert result["has_data"] is False
    assert result["health_score"] == 0
    assert result["health_status"] == "Unknown"
    assert result["completed_items"] == 0
    assert result["remaining_items"] == 0
