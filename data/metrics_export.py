import csv
import json
from datetime import datetime
from io import StringIO
from typing import Any


def export_dora_to_csv(metrics: dict[str, Any], time_period: str) -> str:

    output = StringIO()
    fieldnames = [
        "Metric",
        "Value",
        "Unit",
        "Performance Tier",
        "Trend Direction",
        "Trend %",
        "Time Period",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for metric_key, metric_data in metrics.items():
        row = {
            "Metric": _format_metric_name(metric_key),
            "Value": _format_value_for_csv(metric_data.get("value")),
            "Unit": metric_data.get("unit", ""),
            "Performance Tier": metric_data.get("performance_tier") or "N/A",
            "Trend Direction": metric_data.get("trend_direction", "stable"),
            "Trend %": metric_data.get("trend_percentage", 0.0),
            "Time Period": time_period,
        }
        writer.writerow(row)

    return output.getvalue()


def export_dora_to_json(metrics: dict[str, Any], time_period: str) -> str:

    export_data = {
        "export_date": datetime.now().isoformat(),
        "metric_type": "DORA",
        "time_period": time_period,
        "metrics": metrics,
    }

    return json.dumps(export_data, indent=2)


def export_flow_to_csv(metrics: dict[str, Any], time_period: str) -> str:

    output = StringIO()
    fieldnames = [
        "Metric",
        "Value",
        "Unit",
        "Trend Direction",
        "Trend %",
        "Time Period",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for metric_key, metric_data in metrics.items():
        value = metric_data.get("value")

        if isinstance(value, dict):
            value_str = ", ".join([f"{k}: {v}" for k, v in value.items()])
        else:
            value_str = _format_value_for_csv(value)

        row = {
            "Metric": _format_metric_name(metric_key),
            "Value": value_str,
            "Unit": metric_data.get("unit", ""),
            "Trend Direction": metric_data.get("trend_direction", "stable"),
            "Trend %": metric_data.get("trend_percentage", 0.0),
            "Time Period": time_period,
        }
        writer.writerow(row)

    return output.getvalue()


def export_flow_to_json(metrics: dict[str, Any], time_period: str) -> str:

    export_data = {
        "export_date": datetime.now().isoformat(),
        "metric_type": "Flow",
        "time_period": time_period,
        "metrics": metrics,
    }

    return json.dumps(export_data, indent=2)


def _format_metric_name(metric_key: str) -> str:

    special_cases = {
        "mean_time_to_recovery": "Mean Time to Recovery",
        "change_failure_rate": "Change Failure Rate",
        "lead_time_for_changes": "Lead Time for Changes",
        "deployment_frequency": "Deployment Frequency",
        "flow_velocity": "Flow Velocity",
        "flow_time": "Flow Time",
        "flow_efficiency": "Flow Efficiency",
        "flow_load": "Flow Load",
        "flow_distribution": "Flow Distribution",
        "velocity": "Flow Velocity",
    }

    if metric_key in special_cases:
        return special_cases[metric_key]

    return metric_key.replace("_", " ").title()


def _format_value_for_csv(value: Any) -> str:

    if value is None:
        return "Error"

    if isinstance(value, dict):
        return ", ".join([f"{k}: {v}" for k, v in value.items()])

    return str(value)
