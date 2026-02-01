"""Chart generation orchestration for HTML reports."""

import logging
from typing import Dict, List, Any

from data.report.chart_burndown import (
    generate_burndown_chart,
    generate_weekly_breakdown_chart,
)
from data.report.chart_scope import generate_scope_changes_chart
from data.report.chart_bugs import generate_bug_trends_chart
from data.report.chart_flow import generate_work_distribution_chart

logger = logging.getLogger(__name__)


def generate_chart_scripts(metrics: Dict[str, Any], sections: List[str]) -> List[str]:
    """
    Generate Chart.js initialization scripts for visualizations.

    Args:
        metrics: Calculated metrics dictionary
        sections: List of sections to generate charts for

    Returns:
        List of JavaScript code strings
    """
    scripts: List[str] = []

    if "burndown" in sections and metrics.get("burndown", {}).get("has_data"):
        dashboard_metrics = metrics.get("dashboard", {})
        scripts.append(
            generate_burndown_chart(
                metrics["burndown"],
                dashboard_metrics.get("milestone"),
                dashboard_metrics.get("forecast_date"),
                dashboard_metrics.get("deadline"),
                dashboard_metrics.get("show_points", False),
            )
        )

    if "burndown" in sections and metrics.get("burndown", {}).get("weekly_data"):
        scripts.append(
            generate_weekly_breakdown_chart(
                metrics["burndown"]["weekly_data"],
                metrics.get("dashboard", {}).get("show_points", False),
            )
        )

    if "burndown" in sections and metrics.get("scope", {}).get("has_data"):
        scripts.append(generate_scope_changes_chart(metrics))

    if (
        "burndown" in sections
        and metrics.get("bug_analysis", {}).get("has_data")
        and metrics["bug_analysis"].get("weekly_stats")
    ):
        scripts.append(
            generate_bug_trends_chart(metrics["bug_analysis"]["weekly_stats"])
        )

    if "flow" in sections and metrics.get("flow", {}).get("has_data"):
        scripts.append(generate_work_distribution_chart(metrics["flow"]))

    return scripts
