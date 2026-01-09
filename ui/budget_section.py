"""
Budget Dashboard Section

Creates budget tracking section for comprehensive dashboard with:
- Conditional rendering based on budget configuration
- 7 budget cards in responsive grid
- Budget exhaustion alert banner
- Currency icon integration
- Data points count filter support

Created: January 4, 2026
"""

import logging
from typing import Optional, Dict, Any

import dash_bootstrap_components as dbc
from dash import html

from ui.budget_cards import (
    create_budget_utilization_card,
    create_weekly_burn_rate_card,
    create_budget_runway_card,
    create_cost_per_item_card,
    create_cost_per_point_card,
    create_budget_forecast_card,
    create_cost_breakdown_card,
)

logger = logging.getLogger(__name__)


def _create_budget_section(
    profile_id: str,
    query_id: str,
    week_label: str,
    budget_data: Optional[Dict[str, Any]] = None,
    points_available: bool = False,
    data_points_count: int = 12,
) -> html.Div:
    """
    Create Budget & Resource Tracking section.

    Conditionally renders based on budget configuration existence.
    Shows 7 budget cards with exhaustion alert banner when applicable.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        week_label: Current ISO week label
        budget_data: Budget state and metrics (optional, from budget_calculator)
        points_available: Whether points field is available
        data_points_count: Number of weeks in view (for trend calculations)

    Returns:
        html.Div: Budget section or empty div if budget not configured

    Example Budget Data Structure:
        {
            "configured": True,
            "currency_symbol": "€",
            "consumed_pct": 75.5,
            "consumed_eur": 37750,
            "budget_total": 50000,
            "burn_rate": 4000,
            "weekly_burn_rates": [3500, 3800, 4100, 4000],
            "weekly_labels": ["W40", "W41", "W42", "W43"],
            "burn_trend_pct": 5.2,
            "runway_weeks": 12.5,
            "pert_forecast_weeks": 15.0,
            "cost_per_item": 425.50,
            "cost_per_point": 85.10,
            "pert_cost_avg_item": 410.20,
            "pert_cost_avg_point": 82.40,
            "forecast_total": 48500,
            "forecast_low": 45000,
            "forecast_high": 52000,
            "breakdown": {
                "Feature": {"cost": 12500, "count": 25, "percentage": 62.5},
                "Defect": {"cost": 5000, "count": 10, "percentage": 25.0},
                "Technical Debt": {"cost": 2500, "count": 5, "percentage": 12.5},
                "Risk": {"cost": 0, "count": 0, "percentage": 0}
            },
            "weekly_breakdowns": [...],  # Historical for sparklines
            "exhaustion_alert": {
                "show": True,
                "exhaustion_week": "2026-W08",
                "weeks_until": 4
            }
        }
    """
    # Check if budget is configured
    if not budget_data or not budget_data.get("configured"):
        logger.debug(f"Budget not configured for profile {profile_id}")
        return html.Div()  # Return empty div if no budget

    currency_symbol = budget_data.get("currency_symbol", "€")
    exhaustion_alert = budget_data.get("exhaustion_alert", {})

    # Section header
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

    # Budget exhaustion alert banner (conditional)
    alert_banner = html.Div()
    if exhaustion_alert.get("show"):
        alert_banner = dbc.Alert(
            [
                html.Div(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        html.Strong("Budget Risk: "),
                        f"Projected to exhaust {exhaustion_alert.get('weeks_until', 0)} weeks "
                        f"before forecast completion (Week {exhaustion_alert.get('exhaustion_week', 'N/A')})",
                    ]
                ),
                dbc.Collapse(
                    [
                        html.Hr(),
                        html.P("Budget burn rate trends indicate insufficient runway:"),
                        html.Ul(
                            [
                                html.Li(
                                    f"Current runway: {budget_data.get('runway_weeks', 0):.1f} weeks"
                                ),
                                html.Li(
                                    f"PERT forecast: {budget_data.get('pert_forecast_weeks', 0):.1f} weeks"
                                ),
                                html.Li(
                                    f"Weekly burn rate: {currency_symbol}{budget_data.get('burn_rate', 0):,.2f}/week"
                                ),
                            ]
                        ),
                        html.P(
                            "Consider: Additional funding, scope reduction, or schedule adjustment."
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

    # Create 7 budget cards
    card_1 = create_budget_utilization_card(
        consumed_pct=budget_data.get("consumed_pct", 0),
        consumed_eur=budget_data.get("consumed_eur", 0),
        budget_total=budget_data.get("budget_total", 0),
        currency_symbol=currency_symbol,
        data_points_count=data_points_count,
        card_id="budget-utilization-card",
    )

    card_2 = create_weekly_burn_rate_card(
        burn_rate=budget_data.get("burn_rate", 0),
        weekly_values=budget_data.get("weekly_burn_rates", []),
        weekly_labels=budget_data.get("weekly_labels", []),
        trend_pct=budget_data.get("burn_trend_pct", 0),
        currency_symbol=currency_symbol,
        data_points_count=data_points_count,
        card_id="weekly-burn-rate-card",
    )

    card_3 = create_budget_runway_card(
        runway_weeks=budget_data.get("runway_weeks", 0),
        pert_forecast_weeks=budget_data.get("pert_forecast_weeks"),
        currency_symbol=currency_symbol,
        data_points_count=data_points_count,
        card_id="budget-runway-card",
    )

    card_4 = create_cost_per_item_card(
        cost_per_item=budget_data.get("cost_per_item", 0),
        pert_weighted_avg=budget_data.get("pert_cost_avg_item"),
        currency_symbol=currency_symbol,
        data_points_count=data_points_count,
        card_id="cost-per-item-card",
    )

    card_5 = create_cost_per_point_card(
        cost_per_point=budget_data.get("cost_per_point", 0),
        pert_weighted_avg=budget_data.get("pert_cost_avg_point"),
        points_available=points_available,
        currency_symbol=currency_symbol,
        data_points_count=data_points_count,
        card_id="cost-per-point-card",
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
    )

    card_7 = create_cost_breakdown_card(
        breakdown=budget_data.get("breakdown", {}),
        weekly_breakdowns=budget_data.get("weekly_breakdowns"),
        weekly_labels=budget_data.get("weekly_breakdown_labels"),
        currency_symbol=currency_symbol,
        data_points_count=data_points_count,
        card_id="cost-breakdown-card",
    )

    # Responsive grid layout
    cards_grid = dbc.Row(
        [
            # Row 1: Utilization, Burn Rate, Runway
            dbc.Col(card_1, xs=12, md=6, lg=4, className="mb-3"),
            dbc.Col(card_2, xs=12, md=6, lg=4, className="mb-3"),
            dbc.Col(card_3, xs=12, md=6, lg=4, className="mb-3"),
            # Row 2: Cost per Item, Cost per Point, Budget Status
            dbc.Col(card_4, xs=12, md=6, lg=4, className="mb-3"),
            dbc.Col(card_5, xs=12, md=6, lg=4, className="mb-3"),
            dbc.Col(card_6, xs=12, md=6, lg=4, className="mb-3"),
            # Row 3: Cost Breakdown (full width)
            dbc.Col(card_7, xs=12, className="mb-3"),
        ]
    )

    return html.Div(
        [section_header, alert_banner, cards_grid], className="budget-section mb-4"
    )
