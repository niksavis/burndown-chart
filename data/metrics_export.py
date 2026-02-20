"""Metrics export functionality for DORA and Flow metrics.

Provides CSV and JSON export capabilities for metrics data.
"""

import csv
import json
from datetime import datetime
from io import StringIO
from typing import Any


def export_dora_to_csv(metrics: dict[str, Any], time_period: str) -> str:
    """Export DORA metrics to CSV format.

    Args:
        metrics: Dictionary of DORA metric data
        time_period: Time period for the metrics (e.g., "30 days")

    Returns:
        CSV content as string
    """
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
    """Export DORA metrics to JSON format.

    Args:
        metrics: Dictionary of DORA metric data
        time_period: Time period for the metrics

    Returns:
        JSON content as string
    """
    export_data = {
        "export_date": datetime.now().isoformat(),
        "metric_type": "DORA",
        "time_period": time_period,
        "metrics": metrics,
    }

    return json.dumps(export_data, indent=2)


def export_flow_to_csv(metrics: dict[str, Any], time_period: str) -> str:
    """Export Flow metrics to CSV format.

    Args:
        metrics: Dictionary of Flow metric data
        time_period: Time period for the metrics

    Returns:
        CSV content as string
    """
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

        # Special handling for distribution (nested dict)
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
    """Export Flow metrics to JSON format.

    Args:
        metrics: Dictionary of Flow metric data
        time_period: Time period for the metrics

    Returns:
        JSON content as string
    """
    export_data = {
        "export_date": datetime.now().isoformat(),
        "metric_type": "Flow",
        "time_period": time_period,
        "metrics": metrics,
    }

    return json.dumps(export_data, indent=2)


def _format_metric_name(metric_key: str) -> str:
    """Format metric key for display.

    Args:
        metric_key: Internal metric key (e.g., "deployment_frequency")

    Returns:
        Formatted display name (e.g., "Deployment Frequency")
    """
    # Handle special cases with exact formatting
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
        "velocity": "Flow Velocity",  # Map velocity to Flow Velocity for consistency
    }

    if metric_key in special_cases:
        return special_cases[metric_key]

    # Default: Title case with spaces
    return metric_key.replace("_", " ").title()


def _format_value_for_csv(value: Any) -> str:
    """Format value for CSV output.

    Args:
        value: Metric value (can be number, None, or dict)

    Returns:
        Formatted string for CSV
    """
    if value is None:
        return "Error"

    if isinstance(value, dict):
        # For nested dicts (like distribution)
        return ", ".join([f"{k}: {v}" for k, v in value.items()])

    return str(value)
