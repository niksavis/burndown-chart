"""DORA metric definitions and performance benchmarks.

This module provides industry-standard DORA (DevOps Research and Assessment) metric
definitions, performance tier benchmarks, and utility functions for tier determination.

Reference: DORA_Flow_Jira_Mapping.md
"""

from typing import Dict, Literal

# Performance tier type definition
PerformanceTier = Literal["Elite", "High", "Medium", "Low"]

# DORA Metric Performance Benchmarks
# Source: DORA State of DevOps Research (2024)
DORA_BENCHMARKS = {
    "deployment_frequency": {
        "elite": {
            "threshold": 1,  # per day
            "unit": "deployments/day",
            "color": "green",
            "description": "Multiple deployments per day (on-demand)",
        },
        "high": {
            "threshold": 1,  # per week
            "unit": "deployments/week",
            "color": "yellow",
            "description": "Once per week to once per month",
        },
        "medium": {
            "threshold": 1,  # per month
            "unit": "deployments/month",
            "color": "orange",
            "description": "Once per month to once every 6 months",
        },
        "low": {
            "threshold": 0.17,  # ~1 per 6 months (1/6 per month)
            "unit": "deployments/month",
            "color": "red",
            "description": "Less than once every 6 months",
        },
    },
    "lead_time_for_changes": {
        "elite": {
            "threshold": 0.04,  # Less than 1 hour (1/24 days)
            "unit": "days",
            "color": "green",
            "description": "Less than 1 hour",
        },
        "high": {
            "threshold": 7,  # Between 1 day and 1 week
            "unit": "days",
            "color": "yellow",
            "description": "Between 1 day and 1 week",
        },
        "medium": {
            "threshold": 30,  # Between 1 week and 1 month
            "unit": "days",
            "color": "orange",
            "description": "Between 1 week and 1 month",
        },
        "low": {
            "threshold": 180,  # Between 1 month and 6 months
            "unit": "days",
            "color": "red",
            "description": "More than 1 month",
        },
    },
    "change_failure_rate": {
        "elite": {
            "threshold": 15,  # 0-15%
            "unit": "percentage",
            "color": "green",
            "description": "0-15% failure rate",
        },
        "high": {
            "threshold": 30,  # 15-30%
            "unit": "percentage",
            "color": "yellow",
            "description": "15-30% failure rate",
        },
        "medium": {
            "threshold": 46,  # 30-46%
            "unit": "percentage",
            "color": "orange",
            "description": "30-46% failure rate",
        },
        "low": {
            "threshold": 60,  # 46-60%
            "unit": "percentage",
            "color": "red",
            "description": "More than 46% failure rate",
        },
    },
    "mean_time_to_recovery": {
        "elite": {
            "threshold": 0.04,  # Less than 1 hour (1/24 days)
            "unit": "hours",
            "color": "green",
            "description": "Less than 1 hour",
        },
        "high": {
            "threshold": 1,  # Less than 1 day (24 hours)
            "unit": "days",
            "color": "yellow",
            "description": "Less than 1 day",
        },
        "medium": {
            "threshold": 7,  # Between 1 day and 1 week
            "unit": "days",
            "color": "orange",
            "description": "Between 1 day and 1 week",
        },
        "low": {
            "threshold": 30,  # More than 1 week
            "unit": "days",
            "color": "red",
            "description": "More than 1 week",
        },
    },
}

# Required field mappings for each DORA metric
REQUIRED_DORA_FIELDS = {
    "deployment_frequency": ["deployment_date", "target_environment"],
    "lead_time_for_changes": ["code_commit_date", "deployed_to_production_date"],
    "change_failure_rate": ["deployment_successful", "incident_related"],
    "mean_time_to_recovery": ["incident_detected_at", "incident_resolved_at"],
}

# Metric display names
DORA_METRIC_NAMES = {
    "deployment_frequency": "Deployment Frequency",
    "lead_time_for_changes": "Lead Time for Changes",
    "change_failure_rate": "Change Failure Rate",
    "mean_time_to_recovery": "Mean Time to Recovery (MTTR)",
}

# Metric descriptions
DORA_METRIC_DESCRIPTIONS = {
    "deployment_frequency": "How frequently code is successfully deployed to production",
    "lead_time_for_changes": "Time from code commit to production deployment",
    "change_failure_rate": "Percentage of deployments causing failures or incidents",
    "mean_time_to_recovery": "Time to restore service after a production incident",
}


def determine_performance_tier(metric_name: str, value: float) -> dict:
    """Determine performance tier for a DORA metric value.

    Args:
        metric_name: Name of the DORA metric
        value: Calculated metric value

    Returns:
        Dictionary with tier, color, and benchmark details:
        {
            "tier": "Elite" | "High" | "Medium" | "Low",
            "color": "green" | "yellow" | "orange" | "red",
            "details": {
                "benchmark_elite": float,
                "benchmark_high": float,
                "benchmark_medium": float,
                "benchmark_low": float,
                "description": str
            }
        }

    Example:
        >>> determine_performance_tier("deployment_frequency", 2.5)
        {
            "tier": "Elite",
            "color": "green",
            "details": {...}
        }
    """
    if metric_name not in DORA_BENCHMARKS:
        return {
            "tier": None,
            "color": "secondary",
            "details": {},
        }

    benchmarks = DORA_BENCHMARKS[metric_name]

    # Determine tier based on metric-specific logic
    tier = _calculate_tier(metric_name, value, benchmarks)

    return {
        "tier": tier,
        "color": benchmarks[tier.lower()]["color"],
        "details": {
            "benchmark_elite": benchmarks["elite"]["threshold"],
            "benchmark_high": benchmarks["high"]["threshold"],
            "benchmark_medium": benchmarks["medium"]["threshold"],
            "benchmark_low": benchmarks["low"]["threshold"],
            "description": benchmarks[tier.lower()]["description"],
        },
    }


def _calculate_tier(
    metric_name: str, value: float, benchmarks: Dict
) -> PerformanceTier:
    """Calculate performance tier based on metric-specific logic.

    Different metrics have different comparison logic:
    - deployment_frequency: Higher is better
    - lead_time_for_changes: Lower is better
    - change_failure_rate: Lower is better
    - mean_time_to_recovery: Lower is better
    """
    if metric_name == "deployment_frequency":
        # Higher is better - compare against daily rate
        # Convert value to deployments per day for comparison
        if value >= benchmarks["elite"]["threshold"]:
            return "Elite"
        elif value >= benchmarks["high"]["threshold"] / 7:  # Weekly to daily
            return "High"
        elif value >= benchmarks["medium"]["threshold"] / 30:  # Monthly to daily
            return "Medium"
        else:
            return "Low"

    elif metric_name in ["lead_time_for_changes", "mean_time_to_recovery"]:
        # Lower is better
        if value <= benchmarks["elite"]["threshold"]:
            return "Elite"
        elif value <= benchmarks["high"]["threshold"]:
            return "High"
        elif value <= benchmarks["medium"]["threshold"]:
            return "Medium"
        else:
            return "Low"

    elif metric_name == "change_failure_rate":
        # Lower is better (percentage)
        if value <= benchmarks["elite"]["threshold"]:
            return "Elite"
        elif value <= benchmarks["high"]["threshold"]:
            return "High"
        elif value <= benchmarks["medium"]["threshold"]:
            return "Medium"
        else:
            return "Low"

    return "Low"  # Default fallback


def get_metric_display_name(metric_name: str) -> str:
    """Get human-readable display name for metric."""
    return DORA_METRIC_NAMES.get(metric_name, metric_name.replace("_", " ").title())


def get_metric_description(metric_name: str) -> str:
    """Get description for metric."""
    return DORA_METRIC_DESCRIPTIONS.get(metric_name, "")


def get_required_fields(metric_name: str) -> list:
    """Get required field mappings for a metric."""
    return REQUIRED_DORA_FIELDS.get(metric_name, [])
