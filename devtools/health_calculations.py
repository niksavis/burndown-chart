from data.project_health_calculator import (
    _calculate_delivery_dimension,
    _calculate_efficiency_dimension,
    _calculate_predictability_dimension,
    _calculate_sustainability_dimension,
    _determine_project_stage,
    calculate_comprehensive_project_health,
)


def health_calculations(source: str) -> dict:
    if source == "health-empty":
        return calculate_comprehensive_project_health()
    if source == "health-stage":
        return {
            "complete": _determine_project_stage(200 / 3),
            "stalled": _determine_project_stage(100 / 3),
            "singleton": _determine_project_stage(100),
        }
    if source != "health-calibration":
        raise ValueError(f"Unknown health diagnostic source: {source}")
    dashboard = {
        "completion_percentage": 200 / 3,
        "current_velocity_items": 4,
        "velocity_cv": 0,
        "trend_direction": "stable",
        "recent_velocity_change": 0,
        "schedule_variance_days": 0,
        "completion_confidence": 100,
    }
    flow = {
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
    }
    return {
        "delivery": _result(_calculate_delivery_dimension(dashboard, flow, None)),
        "predictability": _result(
            _calculate_predictability_dimension(dashboard, flow, None)
        ),
        "efficiency": _result(_calculate_efficiency_dimension(flow, dashboard)),
        "sustainability": _result(
            _calculate_sustainability_dimension(None, flow, "mid")
        ),
    }


def _result(value: tuple[float, float]) -> dict:
    return {"score": value[0], "weight": value[1]}
