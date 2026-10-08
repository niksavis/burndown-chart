from collections.abc import Mapping
from typing import cast

import pandas as pd
from dash import html

from data.persistence import load_unified_project_data

from ._dashboard_sections import (
    _build_adaptability_section,
    _build_backlog_chart_section,
    _build_growth_patterns_section,
    _build_throughput_section,
)
from ._indicator_section import _build_scope_indicators_section


def create_scope_metrics_dashboard(
    scope_change_rate: dict,
    weekly_growth_data: pd.DataFrame,
    stability_index: dict,
    threshold: float = 20,
    total_items_scope: int | None = None,
    total_points_scope: int | None = None,
    show_points: bool = True,
) -> html.Div:

    try:
        project_data = load_unified_project_data()
        project_scope = cast(
            Mapping[str, object], project_data.get("project_scope", {})
        )
        remaining_items_value = project_scope.get("remaining_items", 34)
        remaining_points_value = project_scope.get("remaining_total_points", 154)
        remaining_items = (
            int(remaining_items_value)
            if isinstance(remaining_items_value, (int, float, str))
            else 34
        )
        remaining_points = (
            float(remaining_points_value)
            if isinstance(remaining_points_value, (int, float, str))
            else 154
        )
    except Exception:
        remaining_items = 34
        remaining_points = 154

    if not weekly_growth_data.empty:
        total_completed_items = (
            weekly_growth_data["completed_items"].sum()
            if "completed_items" in weekly_growth_data.columns
            else 0
        )
        total_completed_points = (
            weekly_growth_data["completed_points"].sum()
            if "completed_points" in weekly_growth_data.columns
            else 0
        )
        total_created_items = (
            weekly_growth_data["created_items"].sum()
            if "created_items" in weekly_growth_data.columns
            else 0
        )
        total_created_points = (
            weekly_growth_data["created_points"].sum()
            if "created_points" in weekly_growth_data.columns
            else 0
        )
    else:
        total_completed_items = 0
        total_completed_points = 0
        total_created_items = 0
        total_created_points = 0

    if total_items_scope is not None:
        baseline_items = float(total_items_scope)
    else:
        baseline_items = remaining_items + total_completed_items - total_created_items

    if total_points_scope is not None:
        baseline_points = float(total_points_scope)
    else:
        baseline_points = (
            remaining_points + total_completed_points - total_created_points
        )

    threshold_items = round(baseline_items * threshold / 100)
    threshold_points = round(baseline_points * threshold / 100)

    items_throughput_ratio = (
        scope_change_rate.get("throughput_ratio", {}).get("items", 0)
        if isinstance(scope_change_rate.get("throughput_ratio", {}), dict)
        else (
            total_created_items / total_completed_items
            if total_completed_items > 0
            else float("inf")
            if total_created_items > 0
            else 0
        )
    )

    points_throughput_ratio = (
        scope_change_rate.get("throughput_ratio", {}).get("points", 0)
        if isinstance(scope_change_rate.get("throughput_ratio", {}), dict)
        else (
            total_created_points / total_completed_points
            if total_completed_points > 0
            else float("inf")
            if total_created_points > 0
            else 0
        )
    )

    return html.Div(
        [
            _build_scope_indicators_section(
                scope_change_rate,
                threshold,
                items_throughput_ratio,
                points_throughput_ratio,
                total_created_items,
                total_completed_items,
                total_created_points,
                total_completed_points,
                threshold_items,
                threshold_points,
                baseline_items,
                baseline_points,
                show_points,
            ),
            _build_backlog_chart_section(
                weekly_growth_data, baseline_items, baseline_points, show_points
            ),
            _build_throughput_section(
                items_throughput_ratio,
                points_throughput_ratio,
                total_created_items,
                total_completed_items,
                total_created_points,
                total_completed_points,
                show_points,
            ),
            _build_growth_patterns_section(weekly_growth_data, show_points),
            _build_adaptability_section(stability_index, show_points),
        ]
    )


create_scope_creep_dashboard = create_scope_metrics_dashboard
