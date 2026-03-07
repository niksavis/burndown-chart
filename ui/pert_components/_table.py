"""PERT Table - Public Entry Point

Assembles all PERT sections into the final info table component.
"""

from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
from dash import html

from configuration.settings import FORECAST_HELP_TEXTS, VELOCITY_HELP_TEXTS

from ._forecast import _create_completion_forecast_section
from ._helpers import _create_header_with_icon, _get_trend_icon_and_color
from ._project_overview import (
    _create_deadline_section,
    _create_project_overview_section,
)
from ._velocity import _create_weekly_velocity_section


def create_pert_info_table(
    pert_time_items,
    pert_time_points,
    days_to_deadline,
    avg_weekly_items: float = 0.0,
    avg_weekly_points: float = 0.0,
    med_weekly_items: float = 0.0,
    med_weekly_points: float = 0.0,
    pert_factor=3,
    total_items=0,
    total_points=0,
    deadline_str=None,
    statistics_df=None,
    milestone_str=None,
    show_points=True,
    data_points_count=None,
):
    """
    Create the PERT information table with improved organization and visual grouping.

    Args:
        pert_time_items: PERT estimate for items (days)
        pert_time_points: PERT estimate for points (days)
        days_to_deadline: Days remaining until deadline
        avg_weekly_items: Average weekly items completed (last 10 weeks)
        avg_weekly_points: Average weekly points completed (last 10 weeks)
        med_weekly_items: Median weekly items completed (last 10 weeks)
        med_weekly_points: Median weekly points completed (last 10 weeks)
        pert_factor: Number of data points used for optimistic/pessimistic scenarios
        total_items: Total remaining items to complete
        total_points: Total remaining points to complete
        deadline_str: The deadline date string from settings
        statistics_df: DataFrame containing the statistics data
        milestone_str: Milestone date string from settings
        show_points: Whether points tracking is enabled (default: True)
        data_points_count: Number of data points to use for calculations

    Returns:
        Dash component with improved PERT information display
    """
    # Determine colors based on if we'll meet the deadline
    items_color = "green" if pert_time_items <= days_to_deadline else "red"
    points_color = "green" if pert_time_points <= days_to_deadline else "red"

    # Calculate weeks to complete based on average and median rates
    weeks_avg_items = (
        total_items / avg_weekly_items if avg_weekly_items > 0 else float("inf")
    )
    weeks_med_items = (
        total_items / med_weekly_items if med_weekly_items > 0 else float("inf")
    )
    weeks_avg_points = (
        total_points / avg_weekly_points if avg_weekly_points > 0 else float("inf")
    )
    weeks_med_points = (
        total_points / med_weekly_points if med_weekly_points > 0 else float("inf")
    )

    # Determine colors for weeks estimates
    weeks_avg_items_color = (
        "green" if weeks_avg_items * 7 <= days_to_deadline else "red"
    )
    weeks_med_items_color = (
        "green" if weeks_med_items * 7 <= days_to_deadline else "red"
    )
    weeks_avg_points_color = (
        "green" if weeks_avg_points * 7 <= days_to_deadline else "red"
    )
    weeks_med_points_color = (
        "green" if weeks_med_points * 7 <= days_to_deadline else "red"
    )

    # Calculate projected completion dates
    current_date = datetime.now()
    items_completion_date = current_date + timedelta(days=pert_time_items)
    points_completion_date = current_date + timedelta(days=pert_time_points)

    # Calculate dates for average and median completion (handle infinity values)
    avg_items_completion_date = (
        current_date + timedelta(days=min(weeks_avg_items * 7, 3653))
        if weeks_avg_items != float("inf")
        else current_date + timedelta(days=3653)
    )
    med_items_completion_date = (
        current_date + timedelta(days=min(weeks_med_items * 7, 3653))
        if weeks_med_items != float("inf")
        else current_date + timedelta(days=3653)
    )
    avg_points_completion_date = (
        current_date + timedelta(days=min(weeks_avg_points * 7, 3653))
        if weeks_avg_points != float("inf")
        else current_date + timedelta(days=3653)
    )
    med_points_completion_date = (
        current_date + timedelta(days=min(weeks_med_points * 7, 3653))
        if weeks_med_points != float("inf")
        else current_date + timedelta(days=3653)
    )

    # Format dates and values for display
    items_completion_str = items_completion_date.strftime("%Y-%m-%d")
    points_completion_str = points_completion_date.strftime("%Y-%m-%d")
    avg_items_completion_str = avg_items_completion_date.strftime("%Y-%m-%d")
    med_items_completion_str = med_items_completion_date.strftime("%Y-%m-%d")
    avg_points_completion_str = avg_points_completion_date.strftime("%Y-%m-%d")
    med_points_completion_str = med_points_completion_date.strftime("%Y-%m-%d")

    # Calculate days for display
    avg_items_days = weeks_avg_items * 7
    med_items_days = weeks_med_items * 7
    avg_points_days = weeks_avg_points * 7
    med_points_days = weeks_med_points * 7

    # Sample trend values (would be calculated from real data in production)
    avg_items_trend = 10
    med_items_trend = -5
    avg_points_trend = 0
    med_points_trend = 15

    # Get icons and colors for each metric
    avg_items_icon, avg_items_icon_color = _get_trend_icon_and_color(avg_items_trend)
    med_items_icon, med_items_icon_color = _get_trend_icon_and_color(med_items_trend)
    avg_points_icon, avg_points_icon_color = _get_trend_icon_and_color(avg_points_trend)
    med_points_icon, med_points_icon_color = _get_trend_icon_and_color(med_points_trend)

    # Use provided deadline string or calculate
    if deadline_str:
        deadline_date_str = deadline_str
    else:
        deadline_date = current_date + timedelta(days=days_to_deadline)
        deadline_date_str = deadline_date.strftime("%Y-%m-%d")

    # Calculate completed items and points from statistics data
    completed_items = 0
    completed_points = 0
    if statistics_df is not None and not statistics_df.empty:
        completed_items = int(statistics_df["completed_items"].sum())
        completed_points = round(statistics_df["completed_points"].sum(), 1)

    # Calculate actual total project items and points
    actual_total_items = completed_items + total_items
    actual_total_points = round(completed_points + total_points, 1)
    remaining_points = round(total_points, 1)

    # Calculate percentages
    items_percentage = (
        round((completed_items / actual_total_items) * 100, 1)
        if actual_total_items > 0
        else 0
    )
    points_percentage = (
        round((completed_points / actual_total_points) * 100, 1)
        if actual_total_points > 0
        else 0
    )

    # Check if percentages are similar (within 2%)
    similar_percentages = abs(items_percentage - points_percentage) <= 2

    return html.Div(
        [
            # Project Overview section
            html.Div(
                [
                    _create_header_with_icon(
                        "fas fa-project-diagram",
                        "Project Overview",
                        "#20c997",
                        tooltip_text=FORECAST_HELP_TEXTS["pert_methodology"],
                        help_key="project_overview",
                        help_category="forecast",
                    ),
                    html.Div(
                        [
                            _create_project_overview_section(
                                items_percentage,
                                points_percentage,
                                completed_items,
                                completed_points,
                                actual_total_items,
                                actual_total_points,
                                total_items,
                                remaining_points,
                                similar_percentages,
                                show_points,
                            ),
                            _create_deadline_section(
                                deadline_date_str, days_to_deadline
                            ),
                        ],
                        className="p-3 border rounded h-100",
                    ),
                ],
                className="mb-4",
            ),
            # Completion Forecast and Weekly Velocity side by side
            dbc.Row(
                [
                    dbc.Col(
                        [
                            _create_header_with_icon(
                                "fas fa-calendar-check",
                                "Completion Forecast",
                                "#20c997",
                                tooltip_text=FORECAST_HELP_TEXTS["pert_methodology"],
                                help_key="pert_methodology",
                                help_category="forecast",
                            ),
                            _create_completion_forecast_section(
                                items_completion_str,
                                points_completion_str,
                                pert_time_items,
                                pert_time_points,
                                items_color,
                                points_color,
                                avg_items_completion_str,
                                med_items_completion_str,
                                avg_points_completion_str,
                                med_points_completion_str,
                                weeks_avg_items,
                                weeks_med_items,
                                weeks_avg_points,
                                weeks_med_points,
                                avg_items_days,
                                med_items_days,
                                avg_points_days,
                                med_points_days,
                                weeks_avg_items_color,
                                weeks_med_items_color,
                                weeks_avg_points_color,
                                weeks_med_points_color,
                                show_points=show_points,
                            ),
                        ],
                        width=12,
                        lg=6,
                        className="mb-3 mb-lg-0",
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    _create_header_with_icon(
                                        "fas fa-tachometer-alt",
                                        "Weekly Velocity",
                                        "#6610f2",
                                        tooltip_text=VELOCITY_HELP_TEXTS[
                                            "weekly_velocity"
                                        ],
                                        help_key="weekly_velocity_calculation",
                                        help_category="velocity",
                                    ),
                                    _create_weekly_velocity_section(
                                        avg_weekly_items,
                                        med_weekly_items,
                                        avg_weekly_points,
                                        med_weekly_points,
                                        avg_items_trend,
                                        med_items_trend,
                                        avg_points_trend,
                                        med_points_trend,
                                        avg_items_icon,
                                        avg_items_icon_color,
                                        med_items_icon,
                                        med_items_icon_color,
                                        avg_points_icon,
                                        avg_points_icon_color,
                                        med_points_icon,
                                        med_points_icon_color,
                                        show_points=show_points,
                                        data_points_count=data_points_count,
                                        total_data_points=len(statistics_df)
                                        if statistics_df is not None
                                        and not statistics_df.empty
                                        else None,
                                    ),
                                ],
                                className="mt-3 mt-lg-0",
                            ),
                        ],
                        width=12,
                        lg=6,
                    ),
                ],
                className="mb-4",
            ),
        ],
    )
