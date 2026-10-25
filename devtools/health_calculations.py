from data.project_health_calculator import (
    _calculate_delivery_dimension,
    _calculate_efficiency_dimension,
    _calculate_financial_dimension,
    _calculate_predictability_dimension,
    _calculate_quality_dimension,
    _calculate_sustainability_dimension,
    _determine_project_stage,
    calculate_comprehensive_project_health,
)


def _calibration_inputs() -> dict[str, dict]:
    return {
        "dashboard_metrics": {
            "completion_percentage": 200 / 3,
            "current_velocity_items": 4,
            "velocity_cv": 0,
            "trend_direction": "stable",
            "recent_velocity_change": 0,
            "schedule_variance_days": 0,
            "completion_confidence": 100,
        },
        "flow_metrics": {
            "has_data": True,
            "velocity": 4,
            "wip": 11,
            "flow_time": 0.6875,
            "efficiency": 62.76041666666667,
            "work_distribution": {
                "total": 32,
                "feature": 8,
                "defect": 8,
                "tech_debt": 8,
                "risk": 8,
            },
        },
        "bug_metrics": {
            "has_data": True,
            "resolution_rate": 100,
            "capacity_consumed_by_bugs": 0,
            "avg_age_days": 0,
        },
        "dora_metrics": {"has_data": True, "change_failure_rate": 25, "mttr_hours": 54},
        "budget_metrics": {
            "has_data": True,
            "burn_rate_variance_pct": 0,
            "runway_vs_baseline_pct": 0,
            "utilization_vs_pace_pct": 0,
        },
    }


def health_calculations(source: str) -> dict:
    if source == "health-empty":
        return calculate_comprehensive_project_health()
    if source == "health-stage":
        return {
            "complete": _determine_project_stage(200 / 3),
            "stalled": _determine_project_stage(100 / 3),
            "singleton": _determine_project_stage(100),
        }
    if source == "health-financial-calibration":
        return _financial_calibrations()
    inputs = _calibration_inputs()
    if source == "health-composite-calibration":
        return calculate_comprehensive_project_health(**inputs)
    if source != "health-calibration":
        raise ValueError(f"Unknown health diagnostic source: {source}")
    dashboard, flow = inputs["dashboard_metrics"], inputs["flow_metrics"]
    return {
        "delivery": _result(_calculate_delivery_dimension(dashboard, flow, None)),
        "predictability": _result(
            _calculate_predictability_dimension(dashboard, flow, None)
        ),
        "efficiency": _result(_calculate_efficiency_dimension(flow, dashboard)),
        "sustainability": _result(
            _calculate_sustainability_dimension(None, flow, "mid")
        ),
        "quality": _result(
            _calculate_quality_dimension(
                inputs["bug_metrics"], inputs["dora_metrics"], "mid"
            )
        ),
        "financial": _result(_calculate_financial_dimension(inputs["budget_metrics"])),
    }


def _financial_calibrations() -> dict:
    result = {}
    for name, variance, runway, pace in (
        ("on_plan", 0, 0, 0),
        ("ahead", 0, 10, 0),
        ("pressure", 5, -10, 5),
        ("threshold", 10, -25, 10),
        ("medium", 30, 0, 30),
        ("exhausted", 50, -25, 50),
    ):
        result[name] = _result(
            _calculate_financial_dimension(
                {
                    "has_data": True,
                    "burn_rate_variance_pct": variance,
                    "runway_vs_baseline_pct": runway,
                    "utilization_vs_pace_pct": pace,
                }
            )
        )
    return result


def _result(value: tuple[float, float]) -> dict:
    return {"score": value[0], "weight": value[1]}
