"""Main scope metrics dashboard composition."""

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
    """
    Create a dashboard component displaying all scope metrics.

    IMPORTANT: total_items_scope and total_points_scope should represent the INITIAL
    project scope (baseline) at project start, NOT the current total scope including
    created items. See data/scope_metrics.py module documentation for details.

    Args:
        scope_change_rate (dict): Dictionary containing items_rate,
            points_rate and throughput_ratio
        weekly_growth_data (DataFrame): DataFrame containing weekly growth data
        stability_index (dict): Dictionary containing items_stability
            and points_stability values
        threshold (int): Threshold percentage for scope change notifications
        total_items_scope (int, optional): Initial items scope (baseline)
            at project start
        total_points_scope (int, optional): Initial points scope (baseline)
            at project start
        show_points (bool): Whether points tracking is enabled (default: True)

    Returns:
        html.Div: A dashboard component with scope metrics
    """
    # Read remaining items from project scope using new persistence functions
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
        # If we can't read the file, use defaults
        remaining_items = 34
        remaining_points = 154

    # Get total created and completed items/points from the weekly_growth_data
    # This data is already filtered by data_points_count, ensuring consistency
    # with all other scope metrics calculations
    if not weekly_growth_data.empty:
        # Sum from weekly_growth_data which respects data_points_count filtering
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
        # No weekly data available - use zeros
        total_completed_items = 0
        total_completed_points = 0
        total_created_items = 0
        total_created_points = 0

    # Calculate baselines (initial scope at start of data period)
    # CRITICAL: Use the baseline passed from callback - it's calculated correctly as:
    # baseline = current_remaining + completed_in_period - created_in_period
    # This gives the total work that existed at the START of the filtered time window
    if total_items_scope is not None:
        baseline_items = float(total_items_scope)
    else:
        # Fallback: If not provided, calculate from weekly data
        # Note: This should always be provided by the callback
        baseline_items = remaining_items + total_completed_items - total_created_items

    if total_points_scope is not None:
        baseline_points = float(total_points_scope)
    else:
        # Fallback: If not provided, calculate from weekly data
        # Note: This should always be provided by the callback
        baseline_points = (
            remaining_points + total_completed_points - total_created_points
        )

    # Calculate threshold in absolute values - how many items/points can be added
    # before exceeding the threshold percentage
    threshold_items = round(baseline_items * threshold / 100)
    threshold_points = round(baseline_points * threshold / 100)

    # Extract throughput ratios if available, or calculate them
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
            # PRINCIPAL ENGINEER FIX: Removed problematic alert banner entirely.
            # The scope change information is already displayed
            # in the metrics cards above,
            # so this redundant banner was causing component lifecycle issues in Dash.
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


# For backwards compatibility
create_scope_creep_dashboard = create_scope_metrics_dashboard
