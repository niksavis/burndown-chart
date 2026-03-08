"""Forecast Analytics - Section Assembly.

Orchestrates forecast cards, trend chart, and pace health into the
Delivery Forecast dashboard section.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
from dash import html

from ui.budget_cards import create_forecast_alignment_card
from ui.dashboard.forecast_analytics_cards import (
    _build_confidence_intervals_card,
    _build_expected_completion_card,
)
from ui.dashboard.forecast_analytics_charts import (
    _build_forecast_trend_chart,
    get_forecast_history,
)
from ui.dashboard.forecast_analytics_controls import (
    _build_on_track_card,
    _build_pace_health_element,
    _get_probability_tier,
    calculate_schedule_status,
)


def create_forecast_analytics_section(
    pert_data: dict,
    confidence_data: dict,
    budget_data: dict | None = None,
    show_points: bool = True,
    remaining_items: float | None = None,
    remaining_points: float | None = None,
    avg_weekly_items: float | None = None,
    avg_weekly_points: float | None = None,
    days_to_deadline: int | None = None,
    deadline_str: str | None = None,
) -> html.Div:
    """Create forecasting section with multiple prediction methods."""
    current_date = pert_data.get("last_date", datetime.now())

    items_forecast_days = pert_data.get("pert_time_items", 0)
    points_forecast_days = pert_data.get("pert_time_points", 0)

    items_pert_date = (
        (current_date + timedelta(days=items_forecast_days)).strftime("%Y-%m-%d")
        if items_forecast_days > 0
        else "No data"
    )
    points_pert_date = (
        (current_date + timedelta(days=points_forecast_days)).strftime("%Y-%m-%d")
        if points_forecast_days > 0
        else "No data"
    )

    forecast_metric = "story points" if show_points else "items"

    optimistic_date = (
        current_date + timedelta(days=confidence_data.get("ci_50", 0))
    ).strftime("%Y-%m-%d")
    pessimistic_date = (
        current_date + timedelta(days=confidence_data.get("ci_95", 0))
    ).strftime("%Y-%m-%d")

    deadline_prob_items = confidence_data.get("deadline_probability_items", 75)
    deadline_prob_points = confidence_data.get("deadline_probability_points")

    deadline_prob = (
        deadline_prob_points
        if (show_points and deadline_prob_points)
        else deadline_prob_items
    )
    prob_tier, prob_color = _get_probability_tier(deadline_prob)
    items_prob_tier, items_prob_color = _get_probability_tier(deadline_prob_items)

    items_schedule_status = calculate_schedule_status(
        items_pert_date, deadline_str, current_date
    )
    points_schedule_status = calculate_schedule_status(
        points_pert_date, deadline_str, current_date
    )

    ci_50_status = calculate_schedule_status(
        optimistic_date,
        deadline_str,
        current_date,
    )
    ci_95_status = calculate_schedule_status(
        pessimistic_date, deadline_str, current_date
    )

    row_between_class = "d-flex justify-content-between align-items-center mb-2"
    points_disabled_text = (
        "Points tracking is disabled. Enable Points Tracking "
        "in Parameters panel to view story points metrics."
    )
    no_points_data_text = (
        "No story points data available. Configure story points field "
        "in Settings or complete items with point estimates."
    )
    expected_completion_tooltip = (
        "Calculated using PERT three-point estimation: "
        "(Optimistic + 4xMost_Likely + Pessimistic) / 6. "
        "Shows forecasts based on both items and story points velocity. "
        "This weighted average emphasizes the most likely scenario (4x weight) "
        "while accounting for best/worst cases from historical velocity data. "
        "Same method used in Burndown and Report."
    )
    confidence_intervals_tooltip = (
        "Statistical probability ranges based on "
        f"{forecast_metric} velocity variability. "
        "50%: 50th percentile (median) - the PERT forecast itself. "
        "95%: 95th percentile - conservative estimate with 1.65 sigma buffer "
        "(adds uncertainty for remaining work). "
        "Wider spread indicates higher velocity uncertainty. "
        "Calculated from historical data variance."
    )
    on_track_tooltip = (
        "Statistical probability of meeting deadline using normal distribution. "
        "Calculated via Z-score: (deadline_days - expected_days) / forecast_std_dev. "
        "Based on how many standard deviations your deadline is from expected "
        "completion, adjusted for velocity consistency."
    )

    expected_completion_card = _build_expected_completion_card(
        items_pert_date=items_pert_date,
        points_pert_date=points_pert_date,
        items_schedule_status=items_schedule_status,
        points_schedule_status=points_schedule_status,
        show_points=show_points,
        points_disabled_text=points_disabled_text,
        no_points_data_text=no_points_data_text,
        expected_completion_tooltip=expected_completion_tooltip,
        row_between_class=row_between_class,
    )

    confidence_intervals_card = _build_confidence_intervals_card(
        optimistic_date=optimistic_date,
        pessimistic_date=pessimistic_date,
        ci_50_status=ci_50_status,
        ci_95_status=ci_95_status,
        confidence_intervals_tooltip=confidence_intervals_tooltip,
        row_between_class=row_between_class,
    )

    on_track_card = _build_on_track_card(
        deadline_prob_items=deadline_prob_items,
        deadline_prob_points=deadline_prob_points,
        items_prob_tier=items_prob_tier,
        items_prob_color=items_prob_color,
        prob_tier=prob_tier,
        prob_color=prob_color,
        show_points=show_points,
        points_disabled_text=points_disabled_text,
        no_points_data_text=no_points_data_text,
        on_track_tooltip=on_track_tooltip,
        row_between_class=row_between_class,
    )

    history_dates, history_items, history_points = get_forecast_history()
    forecast_trend_chart = _build_forecast_trend_chart(
        history_dates, history_items, history_points, show_points
    )

    pace_health_card_element = _build_pace_health_element(
        remaining_items=remaining_items,
        remaining_points=remaining_points,
        avg_weekly_items=avg_weekly_items,
        avg_weekly_points=avg_weekly_points,
        days_to_deadline=days_to_deadline,
        deadline_str=deadline_str,
        show_points=show_points,
        current_date=current_date,
    )

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-chart-line me-2",
                        style={"color": "#6610f2"},
                    ),
                    "Delivery Forecast",
                ],
                className="mb-3 mt-4",
            ),
            dbc.Row(
                [
                    dbc.Col(expected_completion_card, width=12, md=3, className="mb-3"),
                    dbc.Col(
                        confidence_intervals_card,
                        width=12,
                        md=3,
                        className="mb-3",
                    ),
                    dbc.Col(on_track_card, width=12, md=3, className="mb-3"),
                    dbc.Col(
                        (
                            pace_health_card_element
                            if pace_health_card_element
                            else html.Div()
                        ),
                        width=12,
                        md=3,
                        className="mb-3",
                    ),
                ]
            ),
            (
                dbc.Row(
                    [
                        dbc.Col(
                            create_forecast_alignment_card(
                                pert_time_items=pert_data.get("pert_time_items", 0),
                                pert_time_points=pert_data.get("pert_time_points"),
                                runway_weeks=budget_data.get("runway_weeks", 0),
                                show_points=show_points,
                                last_date=pert_data.get("last_date"),
                                card_id="forecast-alignment-card",
                            ),
                            width=12,
                            className="mb-3",
                        )
                    ]
                )
                if budget_data and budget_data.get("configured")
                else html.Div()
            ),
            forecast_trend_chart if forecast_trend_chart else html.Div(),
        ],
        className="mb-4",
    )
