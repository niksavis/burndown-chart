"""
Burndown Tab Renderer

Renders the tab-burndown content including forecast chart,
weekly items chart, and weekly points chart.
"""

import logging
from datetime import datetime

import pandas as pd

from callbacks.visualization_helpers.data_checks import check_has_points_in_period
from callbacks.visualization_helpers.tab_content import create_burndown_tab_content
from callbacks.visualization_helpers.trend_data import prepare_trend_data
from data.persistence import load_unified_project_data
from data.velocity_projections import calculate_required_velocity
from visualization import create_forecast_plot
from visualization.charts import apply_mobile_optimization
from visualization.weekly_chart_items import create_weekly_items_chart
from visualization.weekly_chart_points import create_weekly_points_chart

logger = logging.getLogger("burndown_chart")


def _render_burndown_tab(
    df: pd.DataFrame,
    statistics: list,
    settings: dict,
    show_points: bool,
    data_points_count: int,
    is_mobile: bool,
    is_tablet: bool,
) -> object:
    """
    Render the burndown tab content.

    Generates the forecast chart, weekly items chart, and weekly points chart,
    then assembles them via create_burndown_tab_content.

    Args:
        df: Raw statistics DataFrame (unfiltered).
        statistics: Raw statistics list (for functions that require list form).
        settings: Current application settings dictionary.
        show_points: Whether story-points tracking is enabled.
        data_points_count: Number of data points (weeks) to display.
        is_mobile: Whether the current viewport is mobile.
        is_tablet: Whether the current viewport is tablet.

    Returns:
        Rendered burndown tab content (html.Div).
    """
    pert_factor = settings.get("pert_factor", 1.2)
    deadline = settings.get("deadline") or None
    total_items = settings.get("total_items", 0)
    total_points = settings.get("total_points", 0)
    show_milestone = settings.get("show_milestone", False)
    milestone = settings.get("milestone", None) if show_milestone else None

    items_trend, points_trend = prepare_trend_data(
        statistics, pert_factor, data_points_count
    )

    has_points_data = False
    if show_points:
        has_points_data = check_has_points_in_period(statistics, data_points_count)
    effective_show_points = show_points and has_points_data

    burndown_fig, _ = create_forecast_plot(
        df=df,
        total_items=total_items,
        total_points=total_points,
        pert_factor=pert_factor,
        deadline_str=deadline,
        milestone_str=milestone,
        data_points_count=data_points_count,
        show_points=effective_show_points,
    )

    required_velocity_items = None
    required_velocity_points = None
    if deadline:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            current_date = datetime.combine(datetime.now().date(), datetime.min.time())
            project_data = load_unified_project_data()
            project_scope = project_data.get("project_scope", {})
            remaining_items = project_scope.get("remaining_items", 0)
            remaining_points = project_scope.get("remaining_total_points", 0)

            if remaining_items > 0:
                required_velocity_items = calculate_required_velocity(
                    remaining_items,
                    deadline_date,
                    current_date=current_date,
                    time_unit="week",
                )
            if remaining_points and remaining_points > 0:
                required_velocity_points = calculate_required_velocity(
                    remaining_points,
                    deadline_date,
                    current_date=current_date,
                    time_unit="week",
                )
        except Exception as e:
            logger.warning(f"Could not calculate required velocity: {e}")

    items_fig = create_weekly_items_chart(
        statistics,
        pert_factor,
        data_points_count=data_points_count,
        required_velocity=required_velocity_items,
    )
    items_fig, _ = apply_mobile_optimization(
        items_fig,
        is_mobile=is_mobile,
        is_tablet=is_tablet,
        title="Weekly Items" if not is_mobile else None,
    )

    points_fig = None
    if show_points and has_points_data:
        points_fig = create_weekly_points_chart(
            statistics,
            pert_factor,
            data_points_count=data_points_count,
            required_velocity=required_velocity_points,
        )
        points_fig, _ = apply_mobile_optimization(
            points_fig,
            is_mobile=is_mobile,
            is_tablet=is_tablet,
            title="Weekly Points" if not is_mobile else None,
        )

    return create_burndown_tab_content(
        df,
        items_trend,
        points_trend,
        burndown_fig,
        items_fig,
        points_fig,
        settings,
        show_points,
        has_points_data,
    )
