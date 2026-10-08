import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ui.budget_cards import (
    create_budget_forecast_card,
    create_budget_runway_card,
    create_budget_timeline_card,
    create_budget_utilization_card,
    create_cost_breakdown_card,
    create_cost_per_item_card,
    create_cost_per_point_card,
    create_weekly_burn_rate_card,
)

logger = logging.getLogger(__name__)


def _create_budget_section(
    profile_id: str,
    query_id: str,
    week_label: str,
    budget_data: dict[str, Any] | None = None,
    points_available: bool = False,
    data_points_count: int = 12,
) -> html.Div:

    if not budget_data or not budget_data.get("configured"):
        logger.debug(f"Budget not configured for profile {profile_id}")
        return html.Div()

    currency_symbol = budget_data.get("currency_symbol", "€")
    exhaustion_alert = budget_data.get("exhaustion_alert", {})

    section_header = html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-wallet me-2",
                        style={"color": "#6f42c1"},
                    ),
                    "Budget & Resource Tracking",
                ],
                className="mb-3 mt-4",
            )
        ]
    )

    alert_banner = html.Div()
    if exhaustion_alert.get("show"):
        weeks_until = exhaustion_alert.get("weeks_until", 0)
        exhaustion_week = exhaustion_alert.get("exhaustion_week", "N/A")
        runway_weeks = budget_data.get("runway_weeks", 0)
        pert_forecast_weeks = budget_data.get("pert_forecast_weeks", 0)
        burn_rate = budget_data.get("burn_rate", 0)
        weekly_burn_text = f"Weekly burn rate: {currency_symbol}{burn_rate:,.2f}/week"
        alert_banner = dbc.Alert(
            [
                html.Div(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        html.Strong("Budget Risk: "),
                        f"Projected to exhaust {weeks_until} weeks "
                        f"before forecast completion (Week {exhaustion_week})",
                    ]
                ),
                dbc.Collapse(
                    [
                        html.Hr(),
                        html.P("Budget burn rate trends indicate insufficient runway:"),
                        html.Ul(
                            [
                                html.Li(f"Current runway: {runway_weeks:.1f} weeks"),
                                html.Li(
                                    f"PERT forecast: {pert_forecast_weeks:.1f} weeks"
                                ),
                                html.Li(weekly_burn_text),
                            ]
                        ),
                        html.P(
                            "Consider: Additional funding, scope reduction, "
                            "or schedule adjustment."
                        ),
                    ],
                    id="budget-alert-detail-collapse",
                    is_open=False,
                ),
                dbc.Button(
                    "Show Details",
                    id="budget-alert-detail-toggle",
                    color="link",
                    size="sm",
                    className="p-0 text-white text-decoration-underline",
                ),
            ],
            color="danger",
            className="mb-3",
        )

    baseline_comparison = budget_data.get("baseline_comparison")

    card_1 = create_budget_utilization_card(
        consumed_pct=budget_data.get("consumed_pct", 0),
        consumed_eur=budget_data.get("consumed_eur", 0),
        budget_total=budget_data.get("budget_total", 0),
        currency_symbol=currency_symbol,
        data_points_count=data_points_count,
        card_id="budget-utilization-card",
        baseline_data=baseline_comparison,
    )

    card_2 = create_weekly_burn_rate_card(
        burn_rate=budget_data.get("burn_rate", 0),
        weekly_values=budget_data.get("weekly_burn_rates", []),
        weekly_labels=budget_data.get("weekly_labels", []),
        trend_pct=budget_data.get("burn_trend_pct", 0),
        currency_symbol=currency_symbol,
        data_points_count=data_points_count,
        card_id="weekly-burn-rate-card",
        baseline_data=baseline_comparison,
    )

    card_3 = create_budget_runway_card(
        runway_weeks=budget_data.get("runway_weeks", 0),
        pert_forecast_weeks=budget_data.get("pert_forecast_weeks"),
        currency_symbol=currency_symbol,
        data_points_count=data_points_count,
        card_id="budget-runway-card",
        baseline_data=baseline_comparison,
    )

    card_4 = create_cost_per_item_card(
        cost_per_item=budget_data.get("cost_per_item", 0),
        pert_weighted_avg=budget_data.get("pert_cost_avg_item"),
        currency_symbol=currency_symbol,
        data_points_count=data_points_count,
        card_id="cost-per-item-card",
        baseline_data=baseline_comparison,
    )

    card_5 = create_cost_per_point_card(
        cost_per_point=budget_data.get("cost_per_point", 0),
        pert_weighted_avg=budget_data.get("pert_cost_avg_point"),
        points_available=points_available,
        currency_symbol=currency_symbol,
        data_points_count=data_points_count,
        card_id="cost-per-point-card",
        baseline_data=baseline_comparison,
    )

    card_6 = create_budget_forecast_card(
        forecast_value=budget_data.get("forecast_total", 0),
        confidence_low=budget_data.get("forecast_low", 0),
        confidence_high=budget_data.get("forecast_high", 0),
        consumed_pct=budget_data.get("consumed_pct", 0),
        consumed_eur=budget_data.get("consumed_eur", 0),
        budget_total=budget_data.get("budget_total", 0),
        confidence_level="established",
        currency_symbol=currency_symbol,
        card_id="budget-forecast-card",
        data_points_count=data_points_count,
    )

    card_7 = create_cost_breakdown_card(
        breakdown=budget_data.get("breakdown", {}),
        weekly_breakdowns=budget_data.get("weekly_breakdowns"),
        weekly_labels=budget_data.get("weekly_breakdown_labels"),
        currency_symbol=currency_symbol,
        data_points_count=data_points_count,
        card_id="cost-breakdown-card",
    )

    card_8 = None
    if baseline_comparison:
        card_8 = create_budget_timeline_card(
            baseline_data=baseline_comparison,
            pert_forecast_weeks=budget_data.get("pert_forecast_weeks"),
            last_date=budget_data.get("last_date"),
            card_id="budget-timeline-card",
        )

    timeline_row = [dbc.Col(card_8, xs=12, className="mb-3")] if card_8 else []

    cards_grid = dbc.Row(
        [
            dbc.Col(card_1, xs=12, md=6, lg=4, className="mb-3"),
            dbc.Col(card_2, xs=12, md=6, lg=4, className="mb-3"),
            dbc.Col(card_3, xs=12, md=6, lg=4, className="mb-3"),
            dbc.Col(card_4, xs=12, md=6, lg=4, className="mb-3"),
            dbc.Col(card_5, xs=12, md=6, lg=4, className="mb-3"),
            dbc.Col(card_6, xs=12, md=6, lg=4, className="mb-3"),
            dbc.Col(card_7, xs=12, className="mb-3"),
            *timeline_row,
        ]
    )

    return html.Div(
        [section_header, alert_banner, cards_grid], className="budget-section mb-4"
    )
