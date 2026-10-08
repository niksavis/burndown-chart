from typing import Literal

from configuration.metrics_config import get_metrics_config

FlowItemType = Literal["Feature", "Defect", "Risk", "Technical_Debt"]

RECOMMENDED_FLOW_DISTRIBUTION = {
    "Feature": {
        "min_percentage": 40,
        "max_percentage": 50,
        "description": "New business value and capabilities",
        "color": "primary",
    },
    "Defect": {
        "min_percentage": 15,
        "max_percentage": 25,
        "description": "Quality maintenance and bug fixes",
        "color": "danger",
    },
    "Risk": {
        "min_percentage": 10,
        "max_percentage": 15,
        "description": "Security, compliance, and operational risks",
        "color": "warning",
    },
    "Technical_Debt": {
        "min_percentage": 20,
        "max_percentage": 25,
        "description": "Code refactoring and sustainability",
        "color": "info",
    },
}

FLOW_EFFICIENCY_THRESHOLDS = {
    "healthy_min": 25,
    "healthy_max": 40,
    "warning_threshold": 15,
}

REQUIRED_FLOW_FIELDS = {
    "flow_velocity": ["flow_item_type"],
    "flow_time": [],
    "flow_efficiency": [],
    "flow_load": ["status"],
    "flow_distribution": ["flow_item_type"],
}

FLOW_METRIC_NAMES = {
    "flow_velocity": "Flow Velocity",
    "flow_time": "Flow Time",
    "flow_efficiency": "Flow Efficiency",
    "flow_load": "Flow Load (WIP)",
    "flow_distribution": "Flow Distribution",
}

FLOW_METRIC_DESCRIPTIONS = {
    "flow_velocity": "Number of work items completed per time period",
    "flow_time": "Average time from work start to completion",
    "flow_efficiency": "Ratio of active work time to total flow time",
    "flow_load": "Number of work items currently in progress",
    "flow_distribution": "Percentage breakdown by work item type",
}

FLOW_METRIC_UNITS = {
    "flow_velocity": "items/period",
    "flow_time": "days",
    "flow_efficiency": "percentage",
    "flow_load": "items",
    "flow_distribution": "percentage",
}


def validate_flow_distribution(distribution: dict[str, float]) -> dict:

    warnings = []
    recommendations = []
    total_percentage = sum(distribution.values())

    if abs(total_percentage - 100) > 0.1:
        warnings.append(
            f"Total distribution is {total_percentage:.1f}%, should be 100%"
        )

    for work_type, percentage in distribution.items():
        if work_type not in RECOMMENDED_FLOW_DISTRIBUTION:
            warnings.append(f"Unknown work type: {work_type}")
            continue

        recommended = RECOMMENDED_FLOW_DISTRIBUTION[work_type]
        min_pct = recommended["min_percentage"]
        max_pct = recommended["max_percentage"]

        if percentage < min_pct:
            warnings.append(
                f"{work_type}: {percentage:.1f}% is below "
                f"recommended minimum of {min_pct}%"
            )
            recommendations.append(
                f"Consider increasing {work_type} allocation "
                f"({recommended['description']})"
            )
        elif percentage > max_pct:
            warnings.append(
                f"{work_type}: {percentage:.1f}% exceeds "
                f"recommended maximum of {max_pct}%"
            )
            recommendations.append(
                f"Consider reducing {work_type} allocation to balance portfolio"
            )

    return {
        "is_valid": len(warnings) == 0,
        "total_percentage": total_percentage,
        "warnings": warnings,
        "recommendations": recommendations,
    }


def get_flow_efficiency_status(efficiency_percentage: float) -> dict:

    thresholds = FLOW_EFFICIENCY_THRESHOLDS

    if thresholds["healthy_min"] <= efficiency_percentage <= thresholds["healthy_max"]:
        return {
            "status": "healthy",
            "color": "success",
            "message": (
                "Flow efficiency is within healthy range "
                f"({thresholds['healthy_min']}-{thresholds['healthy_max']}%)"
            ),
        }
    elif efficiency_percentage < thresholds["warning_threshold"]:
        return {
            "status": "critical",
            "color": "danger",
            "message": (
                "Flow efficiency is critically low "
                f"(<{thresholds['warning_threshold']}%). "
                "High waiting time detected."
            ),
        }
    else:
        return {
            "status": "warning",
            "color": "warning",
            "message": (
                "Flow efficiency is outside recommended range "
                f"({thresholds['healthy_min']}-{thresholds['healthy_max']}%)"
            ),
        }


def get_metric_display_name(metric_name: str) -> str:
    return FLOW_METRIC_NAMES.get(metric_name, metric_name.replace("_", " ").title())


def get_metric_description(metric_name: str) -> str:
    return FLOW_METRIC_DESCRIPTIONS.get(metric_name, "")


def get_metric_unit(metric_name: str) -> str:
    return FLOW_METRIC_UNITS.get(metric_name, "")


def get_required_fields(metric_name: str) -> list:
    return REQUIRED_FLOW_FIELDS.get(metric_name, [])


def get_flow_item_type_color(item_type: str) -> str:
    return RECOMMENDED_FLOW_DISTRIBUTION.get(item_type, {}).get("color", "secondary")


def get_wip_included_statuses() -> list:

    try:
        config = get_metrics_config()
        return config.get_wip_statuses()
    except Exception:
        return ["In Progress", "In Review", "Testing"]


def get_active_statuses() -> list:

    try:
        config = get_metrics_config()
        return config.get_active_statuses()
    except Exception:
        return ["In Progress", "In Review", "Testing"]


def get_wip_included_issue_types() -> list:

    return ["Task", "Story", "Bug"]


def map_effort_category_to_flow_type(effort_category: str) -> str:

    if not effort_category or effort_category == "None":
        return "Feature"

    effort_lower = effort_category.lower()

    if "technical debt" in effort_lower or "tech debt" in effort_lower:
        return "Technical Debt"
    elif any(
        keyword in effort_lower
        for keyword in ["security", "gdpr", "regulatory", "compliance"]
    ):
        return "Risk"
    elif "spike" in effort_lower or "analysis" in effort_lower:
        return "Risk"
    else:
        return "Feature"
