"""Flow metric definitions and recommended distribution ranges.

This module provides Flow metrics definitions, recommended work type distribution
ranges, and utility functions for Flow metric calculations.

Reference: DORA_Flow_Jira_Mapping.md
"""

from typing import Dict, Literal

# Flow work item types
FlowItemType = Literal["Feature", "Defect", "Risk", "Technical_Debt"]

# Recommended Flow Distribution Ranges
# Source: Flow Framework (2018) by Mik Kersten
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

# Flow Efficiency thresholds
# Typical healthy efficiency is 25-40%
FLOW_EFFICIENCY_THRESHOLDS = {
    "healthy_min": 25,
    "healthy_max": 40,
    "warning_threshold": 15,  # Below this is concerning
}

# Required field mappings for each Flow metric
REQUIRED_FLOW_FIELDS = {
    "flow_velocity": ["flow_item_type", "completed_date"],
    "flow_time": ["work_started_date", "work_completed_date"],
    "flow_efficiency": ["status_entry_timestamp", "active_work_hours"],
    "flow_load": ["status"],  # Current status
    "flow_distribution": ["flow_item_type", "completed_date"],
}

# Metric display names
FLOW_METRIC_NAMES = {
    "flow_velocity": "Flow Velocity",
    "flow_time": "Flow Time",
    "flow_efficiency": "Flow Efficiency",
    "flow_load": "Flow Load (WIP)",
    "flow_distribution": "Flow Distribution",
}

# Metric descriptions
FLOW_METRIC_DESCRIPTIONS = {
    "flow_velocity": "Number of work items completed per time period",
    "flow_time": "Average time from work start to completion",
    "flow_efficiency": "Ratio of active work time to total flow time",
    "flow_load": "Number of work items currently in progress",
    "flow_distribution": "Percentage breakdown by work item type",
}

# Metric units
FLOW_METRIC_UNITS = {
    "flow_velocity": "items/period",
    "flow_time": "days",
    "flow_efficiency": "percentage",
    "flow_load": "items",
    "flow_distribution": "percentage",
}


def validate_flow_distribution(distribution: Dict[str, float]) -> dict:
    """Validate Flow Distribution against recommended ranges.

    Args:
        distribution: Dictionary with work type percentages
            Example: {"Feature": 45, "Defect": 20, "Risk": 12, "Technical_Debt": 23}

    Returns:
        Dictionary with validation results:
        {
            "is_valid": True/False,
            "total_percentage": float,
            "warnings": [list of warning messages],
            "recommendations": [list of improvement suggestions]
        }

    Example:
        >>> validate_flow_distribution({"Feature": 60, "Defect": 30, "Risk": 5, "Technical_Debt": 5})
        {
            "is_valid": True,
            "total_percentage": 100,
            "warnings": ["Feature: 60% exceeds recommended maximum of 50%"],
            "recommendations": ["Consider balancing Feature work with Technical_Debt"]
        }
    """
    warnings = []
    recommendations = []
    total_percentage = sum(distribution.values())

    # Check if total percentage is 100%
    if abs(total_percentage - 100) > 0.1:
        warnings.append(
            f"Total distribution is {total_percentage:.1f}%, should be 100%"
        )

    # Check each work type against recommended ranges
    for work_type, percentage in distribution.items():
        if work_type not in RECOMMENDED_FLOW_DISTRIBUTION:
            warnings.append(f"Unknown work type: {work_type}")
            continue

        recommended = RECOMMENDED_FLOW_DISTRIBUTION[work_type]
        min_pct = recommended["min_percentage"]
        max_pct = recommended["max_percentage"]

        if percentage < min_pct:
            warnings.append(
                f"{work_type}: {percentage:.1f}% is below recommended minimum of {min_pct}%"
            )
            recommendations.append(
                f"Consider increasing {work_type} allocation ({recommended['description']})"
            )
        elif percentage > max_pct:
            warnings.append(
                f"{work_type}: {percentage:.1f}% exceeds recommended maximum of {max_pct}%"
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
    """Determine if Flow Efficiency is within healthy range.

    Args:
        efficiency_percentage: Flow efficiency as percentage (0-100)

    Returns:
        Dictionary with status information:
        {
            "status": "healthy" | "warning" | "critical",
            "color": "success" | "warning" | "danger",
            "message": str
        }

    Example:
        >>> get_flow_efficiency_status(35)
        {
            "status": "healthy",
            "color": "success",
            "message": "Flow efficiency is within healthy range (25-40%)"
        }
    """
    thresholds = FLOW_EFFICIENCY_THRESHOLDS

    if thresholds["healthy_min"] <= efficiency_percentage <= thresholds["healthy_max"]:
        return {
            "status": "healthy",
            "color": "success",
            "message": f"Flow efficiency is within healthy range ({thresholds['healthy_min']}-{thresholds['healthy_max']}%)",
        }
    elif efficiency_percentage < thresholds["warning_threshold"]:
        return {
            "status": "critical",
            "color": "danger",
            "message": f"Flow efficiency is critically low (<{thresholds['warning_threshold']}%). High waiting time detected.",
        }
    else:
        return {
            "status": "warning",
            "color": "warning",
            "message": f"Flow efficiency is outside recommended range ({thresholds['healthy_min']}-{thresholds['healthy_max']}%)",
        }


def get_metric_display_name(metric_name: str) -> str:
    """Get human-readable display name for metric."""
    return FLOW_METRIC_NAMES.get(metric_name, metric_name.replace("_", " ").title())


def get_metric_description(metric_name: str) -> str:
    """Get description for metric."""
    return FLOW_METRIC_DESCRIPTIONS.get(metric_name, "")


def get_metric_unit(metric_name: str) -> str:
    """Get unit for metric."""
    return FLOW_METRIC_UNITS.get(metric_name, "")


def get_required_fields(metric_name: str) -> list:
    """Get required field mappings for a metric."""
    return REQUIRED_FLOW_FIELDS.get(metric_name, [])


def get_flow_item_type_color(item_type: str) -> str:
    """Get Bootstrap color for work item type."""
    return RECOMMENDED_FLOW_DISTRIBUTION.get(item_type, {}).get("color", "secondary")
