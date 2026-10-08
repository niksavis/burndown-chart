from typing import Literal

from configuration.metrics_config import get_metrics_config

PerformanceTier = Literal["Elite", "High", "Medium", "Low"]

DORA_BENCHMARKS = {
    "deployment_frequency": {
        "elite": {
            "threshold": 1,
            "unit": "deployments/day",
            "color": "green",
            "description": "Multiple deployments per day (on-demand)",
        },
        "high": {
            "threshold": 1,
            "unit": "deployments/week",
            "color": "yellow",
            "description": "Once per week to once per month",
        },
        "medium": {
            "threshold": 1,
            "unit": "deployments/month",
            "color": "orange",
            "description": "Once per month to once every 6 months",
        },
        "low": {
            "threshold": 0.17,
            "unit": "deployments/month",
            "color": "red",
            "description": "Less than once every 6 months",
        },
    },
    "lead_time_for_changes": {
        "elite": {
            "threshold": 0.04,
            "unit": "days",
            "color": "green",
            "description": "Less than 1 hour",
        },
        "high": {
            "threshold": 7,
            "unit": "days",
            "color": "yellow",
            "description": "Between 1 day and 1 week",
        },
        "medium": {
            "threshold": 30,
            "unit": "days",
            "color": "orange",
            "description": "Between 1 week and 1 month",
        },
        "low": {
            "threshold": 180,
            "unit": "days",
            "color": "red",
            "description": "More than 1 month",
        },
    },
    "change_failure_rate": {
        "elite": {
            "threshold": 15,
            "unit": "percentage",
            "color": "green",
            "description": "0-15% failure rate",
        },
        "high": {
            "threshold": 30,
            "unit": "percentage",
            "color": "yellow",
            "description": "15-30% failure rate",
        },
        "medium": {
            "threshold": 46,
            "unit": "percentage",
            "color": "orange",
            "description": "30-46% failure rate",
        },
        "low": {
            "threshold": 60,
            "unit": "percentage",
            "color": "red",
            "description": "More than 46% failure rate",
        },
    },
    "mean_time_to_recovery": {
        "elite": {
            "threshold": 0.04,
            "unit": "hours",
            "color": "green",
            "description": "Less than 1 hour",
        },
        "high": {
            "threshold": 1,
            "unit": "days",
            "color": "yellow",
            "description": "Less than 1 day",
        },
        "medium": {
            "threshold": 7,
            "unit": "days",
            "color": "orange",
            "description": "Between 1 day and 1 week",
        },
        "low": {
            "threshold": 30,
            "unit": "days",
            "color": "red",
            "description": "More than 1 week",
        },
    },
}

REQUIRED_DORA_FIELDS = {
    "deployment_frequency": ["deployment_date", "target_environment"],
    "lead_time_for_changes": ["code_commit_date", "deployment_date"],
    "change_failure_rate": ["change_failure"],
    "mean_time_to_recovery": ["incident_detected_at", "incident_resolved_at"],
}

DORA_METRIC_NAMES = {
    "deployment_frequency": "Deployment Frequency",
    "lead_time_for_changes": "Lead Time for Changes",
    "change_failure_rate": "Change Failure Rate",
    "mean_time_to_recovery": "Mean Time to Recovery (MTTR)",
}

DORA_METRIC_DESCRIPTIONS = {
    "deployment_frequency": (
        "How frequently code is successfully deployed to production"
    ),
    "lead_time_for_changes": "Time from code commit to production deployment",
    "change_failure_rate": "Percentage of deployments causing failures or incidents",
    "mean_time_to_recovery": "Time to restore service after a production incident",
}


def determine_performance_tier(metric_name: str, value: float) -> dict:

    if metric_name not in DORA_BENCHMARKS:
        return {
            "tier": None,
            "color": "secondary",
            "details": {},
        }

    benchmarks = DORA_BENCHMARKS[metric_name]

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
    metric_name: str, value: float, benchmarks: dict
) -> PerformanceTier:

    if metric_name == "deployment_frequency":
        if value >= benchmarks["elite"]["threshold"]:
            return "Elite"
        elif value >= benchmarks["high"]["threshold"] / 7:
            return "High"
        elif value >= benchmarks["medium"]["threshold"] / 30:
            return "Medium"
        else:
            return "Low"

    elif metric_name in ["lead_time_for_changes", "mean_time_to_recovery"]:
        if value <= benchmarks["elite"]["threshold"]:
            return "Elite"
        elif value <= benchmarks["high"]["threshold"]:
            return "High"
        elif value <= benchmarks["medium"]["threshold"]:
            return "Medium"
        else:
            return "Low"

    elif metric_name == "change_failure_rate":
        if value <= benchmarks["elite"]["threshold"]:
            return "Elite"
        elif value <= benchmarks["high"]["threshold"]:
            return "High"
        elif value <= benchmarks["medium"]["threshold"]:
            return "Medium"
        else:
            return "Low"

    return "Low"


def get_metric_display_name(metric_name: str) -> str:
    return DORA_METRIC_NAMES.get(metric_name, metric_name.replace("_", " ").title())


def get_metric_description(metric_name: str) -> str:
    return DORA_METRIC_DESCRIPTIONS.get(metric_name, "")


def get_required_fields(metric_name: str) -> list:
    return REQUIRED_DORA_FIELDS.get(metric_name, [])


def get_operational_project_keys() -> list:

    try:
        config = get_metrics_config()
        return config.get_devops_projects()
    except Exception:
        return []


def get_flow_end_status_names() -> list:

    try:
        config = get_metrics_config()
        return config.get_flow_end_statuses()
    except Exception:
        return ["Done", "Resolved", "Closed"]


def is_status_match(
    status_name: str, target_statuses: list, case_sensitive: bool = False
) -> bool:

    try:
        config = get_metrics_config()
        return config.is_status_in_list(status_name, target_statuses, case_sensitive)
    except Exception:
        if case_sensitive:
            return status_name in target_statuses
        else:
            return status_name.lower() in [s.lower() for s in target_statuses]
