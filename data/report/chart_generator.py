"""Chart generation orchestration for HTML reports."""

import logging
from datetime import datetime
from typing import Any

from data.report.chart_bugs import generate_bug_trends_chart
from data.report.chart_burndown import (
    generate_burndown_chart,
    generate_weekly_breakdown_chart,
)
from data.report.chart_flow import generate_work_distribution_chart
from data.report.chart_scope import generate_scope_changes_chart

logger = logging.getLogger(__name__)


def _load_remaining_work(deadline: str | None) -> tuple[float, float, float, float]:
    """Load remaining items/points and required velocities from project scope.

    Uses the exact same approach as the app's burndown tab callback:
    - Loading remaining_items and remaining_total_points from project_scope
    - Computing required velocity with midnight-today as current_date

    Args:
        deadline: Deadline date string (YYYY-MM-DD)

    Returns:
        Tuple of (remaining_items, remaining_points,
                  required_velocity_items, required_velocity_points)
    """
    from data.persistence import load_unified_project_data
    from data.velocity_projections import calculate_required_velocity

    project_data = load_unified_project_data()
    project_scope = project_data.get("project_scope", {})
    remaining_items = float(project_scope.get("remaining_items") or 0)
    remaining_points = float(project_scope.get("remaining_total_points") or 0)

    required_items = 0.0
    required_points = 0.0

    if deadline:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            # Use midnight today - matches app's burndown tab callback exactly
            current_date = datetime.combine(datetime.now().date(), datetime.min.time())
            if remaining_items > 0:
                raw = calculate_required_velocity(
                    remaining_items,
                    deadline_date,
                    current_date=current_date,
                    time_unit="week",
                )
                required_items = raw if raw != float("inf") else 0.0
            if remaining_points > 0:
                raw_pts = calculate_required_velocity(
                    remaining_points,
                    deadline_date,
                    current_date=current_date,
                    time_unit="week",
                )
                required_points = raw_pts if raw_pts != float("inf") else 0.0
        except ValueError:
            pass

    logger.info(
        "[REPORT CHART] Required velocity from project_scope: "
        f"remaining_items={remaining_items}, remaining_points={remaining_points}, "
        f"deadline={deadline}, "
        f"required_items={required_items:.4f}, required_points={required_points:.4f}"
    )

    return remaining_items, remaining_points, required_items, required_points


def generate_chart_scripts(metrics: dict[str, Any], sections: list[str]) -> list[str]:
    """
    Generate Chart.js initialization scripts for visualizations.

    Args:
        metrics: Calculated metrics dictionary
        sections: List of sections to generate charts for

    Returns:
        List of JavaScript code strings
    """
    scripts: list[str] = []

    if "burndown" in sections and metrics.get("burndown", {}).get("has_data"):
        dashboard_metrics = metrics.get("dashboard", {})
        scripts.append(
            generate_burndown_chart(
                metrics["burndown"],
                dashboard_metrics.get("milestone"),
                dashboard_metrics.get("forecast_date"),
                dashboard_metrics.get("deadline"),
                dashboard_metrics.get("show_points", False),
                statistics=metrics.get("statistics", []),
                pert_factor=dashboard_metrics.get("pert_factor", 3),
            )
        )

    if "burndown" in sections and metrics.get("burndown", {}).get("weekly_data"):
        dashboard_metrics = metrics.get("dashboard", {})
        deadline = dashboard_metrics.get("deadline")
        remaining_items, remaining_points, _, _ = _load_remaining_work(deadline)
        scripts.append(
            generate_weekly_breakdown_chart(
                metrics["burndown"]["weekly_data"],
                dashboard_metrics.get("show_points", False),
                statistics=metrics.get("statistics", []),
                pert_factor=dashboard_metrics.get("pert_factor", 3),
                deadline=deadline,
                remaining_items=remaining_items,
                remaining_points=remaining_points,
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
