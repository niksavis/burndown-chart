"""
Budget Cards - UI Components for Lean Budgeting

Implements 7 budget metric cards using create_metric_card() pattern:
1. Budget Utilization gauge with health zones
2. Weekly Burn Rate with sparkline and trend arrow
3. Budget Runway with critical warnings
4. Cost per Item (auto-calculated)
5. Cost per Point (conditional on points_field_available)
6. Budget Forecast with PERT confidence intervals
7. Cost Breakdown by Work Type (Flow Distribution alignment)

Currency handling with FontAwesome icon mapping.

Created: January 4, 2026
"""

import logging
from typing import Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import html

from ui.metric_cards import create_metric_card

logger = logging.getLogger(__name__)


# Currency symbol to FontAwesome icon mapping
CURRENCY_ICON_MAP = {
    "$": "fa-dollar-sign",
    "€": "fa-euro-sign",
    "£": "fa-pound-sign",
    "¥": "fa-yen-sign",
}


def get_currency_icon(currency_symbol: str) -> str:
    """
    Map currency symbol to FontAwesome icon class.

    Args:
        currency_symbol: Currency symbol (e.g., "$", "€", "£", "¥")

    Returns:
        FontAwesome icon class name

    Example:
        >>> get_currency_icon("€")
        "fa-euro-sign"
        >>> get_currency_icon("₹")
        "fa-coins"
    """
    return CURRENCY_ICON_MAP.get(currency_symbol, "fa-coins")


def create_budget_utilization_card(
    consumed_pct: float,
    consumed_eur: float,
    budget_total: float,
    currency_symbol: str = "€",
    card_id: Optional[str] = None,
) -> dbc.Card:
    """
    Create Budget Utilization gauge card with health zones.

    Health zones:
    - Green (0-70%): Healthy
    - Yellow (70-85%): Warning
    - Orange (85-95%): High
    - Red (95-100%+): Critical

    Args:
        consumed_pct: Percentage of budget consumed
        consumed_eur: Absolute amount consumed
        budget_total: Total budget amount
        currency_symbol: Currency symbol for display
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> card = create_budget_utilization_card(75.5, 37750, 50000, "€")
    """
    # Determine health zone
    if consumed_pct < 70:
        tier_color = "green"
        tier_label = "Healthy"
    elif consumed_pct < 85:
        tier_color = "yellow"
        tier_label = "Warning"
    elif consumed_pct < 95:
        tier_color = "orange"
        tier_label = "High"
    else:
        tier_color = "red"
        tier_label = "Critical"

    metric_data = {
        "metric_name": "budget_utilization",
        "alternative_name": "Budget Utilization",
        "value": consumed_pct,
        "unit": "%",
        "performance_tier": tier_label,
        "performance_tier_color": tier_color,
        "error_state": "success",
        "total_issue_count": 0,
        "details": {
            "consumed": f"{currency_symbol}{consumed_eur:,.2f}",
            "total": f"{currency_symbol}{budget_total:,.2f}",
            "remaining": f"{currency_symbol}{(budget_total - consumed_eur):,.2f}",
        },
    }

    return create_metric_card(metric_data, card_id)


def create_weekly_burn_rate_card(
    burn_rate: float,
    weekly_values: List[float],
    weekly_labels: List[str],
    trend_pct: float,
    currency_symbol: str = "€",
    data_points_count: int = 4,
    card_id: Optional[str] = None,
) -> dbc.Card:
    """
    Create Weekly Burn Rate card with sparkline and 4-week weighted trend arrow.

    Args:
        burn_rate: Current weighted burn rate (EUR/week)
        weekly_values: Historical weekly burn rates for sparkline
        weekly_labels: Week labels for sparkline
        trend_pct: Trend percentage change (positive = increasing burn)
        currency_symbol: Currency symbol for display
        data_points_count: Number of weeks shown (respects filter)
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> card = create_weekly_burn_rate_card(
        ...     4000, [3500, 3800, 4100, 4000], ["W40", "W41", "W42", "W43"],
        ...     5.2, "€", 4
        ... )
    """
    # Determine trend direction
    if abs(trend_pct) < 2:
        trend_arrow = "→"
        trend_color = "text-secondary"
    elif trend_pct > 0:
        trend_arrow = "↗"
        trend_color = "text-danger"  # Increasing burn = warning
    else:
        trend_arrow = "↘"
        trend_color = "text-success"  # Decreasing burn = good

    metric_data = {
        "metric_name": "weekly_burn_rate",
        "alternative_name": "Weekly Burn Rate",
        "value": burn_rate,
        "unit": f"{currency_symbol}/week",
        "performance_tier": None,
        "performance_tier_color": "secondary",
        "error_state": "success",
        "total_issue_count": 0,
        "weekly_values": weekly_values[-data_points_count:],
        "weekly_labels": weekly_labels[-data_points_count:],
        "details": {
            "trend": f"{trend_arrow} {abs(trend_pct):.1f}%",
            "trend_color": trend_color,
            "_n_weeks": data_points_count,
        },
    }

    return create_metric_card(metric_data, card_id)


def create_budget_runway_card(
    runway_weeks: float,
    pert_forecast_weeks: Optional[float] = None,
    currency_symbol: str = "€",
    card_id: Optional[str] = None,
) -> dbc.Card:
    """
    Create Budget Runway card with critical <4 weeks warning.

    Args:
        runway_weeks: Remaining budget runway in weeks
        pert_forecast_weeks: PERT forecast completion weeks (for comparison)
        currency_symbol: Currency symbol for display
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> card = create_budget_runway_card(12.5, 15.0, "€")
    """
    # Determine health status
    if runway_weeks < 4:
        tier_color = "red"
        tier_label = "Critical"
    elif pert_forecast_weeks and runway_weeks < pert_forecast_weeks:
        tier_color = "orange"
        tier_label = "At Risk"
    elif runway_weeks < 8:
        tier_color = "yellow"
        tier_label = "Warning"
    else:
        tier_color = "green"
        tier_label = "Healthy"

    details = {}
    if pert_forecast_weeks:
        gap = runway_weeks - pert_forecast_weeks
        details["vs_forecast"] = f"{'+' if gap >= 0 else ''}{gap:.1f} weeks"

    metric_data = {
        "metric_name": "budget_runway",
        "alternative_name": "Budget Runway",
        "value": runway_weeks,
        "unit": "weeks",
        "performance_tier": tier_label,
        "performance_tier_color": tier_color,
        "error_state": "success",
        "total_issue_count": 0,
        "details": details,
    }

    return create_metric_card(metric_data, card_id)


def create_cost_per_item_card(
    cost_per_item: float,
    pert_weighted_avg: Optional[float] = None,
    currency_symbol: str = "€",
    card_id: Optional[str] = None,
) -> dbc.Card:
    """
    Create Cost per Item card (auto-calculated from Team Cost ÷ Velocity).

    Args:
        cost_per_item: Current cost per item
        pert_weighted_avg: PERT-weighted average cost per item
        currency_symbol: Currency symbol for display
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> card = create_cost_per_item_card(425.50, 410.20, "€")
    """
    details = {"calculation": "Auto-calculated: Team Cost ÷ Velocity"}
    if pert_weighted_avg:
        details["pert_avg"] = f"{currency_symbol}{pert_weighted_avg:.2f}"

    metric_data = {
        "metric_name": "cost_per_item",
        "alternative_name": "Cost per Item",
        "value": cost_per_item,
        "unit": f"{currency_symbol}/item",
        "performance_tier": None,
        "performance_tier_color": "secondary",
        "error_state": "success",
        "total_issue_count": 0,
        "details": details,
    }

    return create_metric_card(metric_data, card_id)


def create_cost_per_point_card(
    cost_per_point: float,
    pert_weighted_avg: Optional[float] = None,
    points_available: bool = True,
    currency_symbol: str = "€",
    card_id: Optional[str] = None,
) -> dbc.Card:
    """
    Create Cost per Point card (conditional on points_field_available).

    Args:
        cost_per_point: Current cost per story point
        pert_weighted_avg: PERT-weighted average cost per point
        points_available: Whether points field is available
        currency_symbol: Currency symbol for display
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component or warning card

    Example:
        >>> card = create_cost_per_point_card(85.10, 82.40, True, "€")
    """
    if not points_available:
        # Return warning card when points unavailable
        metric_data = {
            "metric_name": "cost_per_point",
            "alternative_name": "Cost per Point",
            "value": None,
            "unit": f"{currency_symbol}/point",
            "error_state": "missing_mapping",
            "error_message": "Points unavailable, using item cost only",
            "total_issue_count": 0,
        }
        return create_metric_card(metric_data, card_id)

    details = {"calculation": "Auto-calculated: Team Cost ÷ (Velocity × Points/Item)"}
    if pert_weighted_avg:
        details["pert_avg"] = f"{currency_symbol}{pert_weighted_avg:.2f}"

    metric_data = {
        "metric_name": "cost_per_point",
        "alternative_name": "Cost per Point",
        "value": cost_per_point,
        "unit": f"{currency_symbol}/point",
        "performance_tier": None,
        "performance_tier_color": "secondary",
        "error_state": "success",
        "total_issue_count": 0,
        "details": details,
    }

    return create_metric_card(metric_data, card_id)


def create_budget_forecast_card(
    forecast_value: float,
    confidence_low: float,
    confidence_high: float,
    confidence_level: str = "established",
    currency_symbol: str = "€",
    card_id: Optional[str] = None,
) -> dbc.Card:
    """
    Create Budget Forecast card with PERT confidence intervals.

    Args:
        forecast_value: Forecasted total budget needed
        confidence_low: Lower confidence bound (pessimistic)
        confidence_high: Upper confidence bound (optimistic)
        confidence_level: "established" or "building"
        currency_symbol: Currency symbol for display
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> card = create_budget_forecast_card(
        ...     48500, 45000, 52000, "established", "€"
        ... )
    """
    metric_data = {
        "metric_name": "budget_forecast",
        "alternative_name": "Budget Forecast",
        "value": forecast_value,
        "unit": currency_symbol,
        "performance_tier": None,
        "performance_tier_color": "secondary",
        "error_state": "success",
        "total_issue_count": 0,
        "details": {
            "confidence_range": f"{currency_symbol}{confidence_low:,.0f} - {currency_symbol}{confidence_high:,.0f}",
            "confidence_level": confidence_level.title(),
        },
    }

    return create_metric_card(metric_data, card_id)


def create_cost_breakdown_card(
    breakdown: Dict[str, Dict[str, float]],
    weekly_breakdowns: Optional[List[Dict[str, Dict[str, float]]]] = None,
    weekly_labels: Optional[List[str]] = None,
    currency_symbol: str = "€",
    data_points_count: int = 4,
    card_id: Optional[str] = None,
) -> dbc.Card:
    """
    Create Cost Breakdown by Work Type card.

    4-category breakdown matching Flow Distribution (Feature/Defect/Technical Debt/Risk).
    Shows aggregated total + per-category costs with percentages.
    Optional sparklines respecting data_points_count filter.

    Args:
        breakdown: Current cost breakdown by flow type:
            {"Feature": {"cost": 12500, "count": 25, "percentage": 62.5}, ...}
        weekly_breakdowns: Historical breakdowns for sparklines (optional)
        weekly_labels: Week labels for sparklines (optional)
        currency_symbol: Currency symbol for display
        data_points_count: Number of weeks shown in sparklines
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component spanning full width (lg=12)

    Example:
        >>> breakdown = {
        ...     "Feature": {"cost": 12500, "count": 25, "percentage": 62.5},
        ...     "Defect": {"cost": 5000, "count": 10, "percentage": 25.0}
        ... }
        >>> card = create_cost_breakdown_card(breakdown, currency_symbol="€")
    """
    total_cost = sum(cat["cost"] for cat in breakdown.values())

    # Build category rows
    category_rows = []
    for flow_type in ["Feature", "Defect", "Technical Debt", "Risk"]:
        cat_data = breakdown.get(flow_type, {"cost": 0, "count": 0, "percentage": 0})
        cost = cat_data["cost"]
        count = cat_data["count"]
        pct = cat_data["percentage"]

        # Extract sparkline data if available
        sparkline_values = []
        if weekly_breakdowns and weekly_labels:
            sparkline_values = [
                wb.get(flow_type, {}).get("cost", 0)
                for wb in weekly_breakdowns[-data_points_count:]
            ]

        # Create mini sparkline
        sparkline = (
            _create_inline_sparkline(sparkline_values)
            if sparkline_values
            else html.Div()
        )

        category_rows.append(
            html.Tr(
                [
                    html.Td(flow_type, className="text-start"),
                    html.Td(f"{currency_symbol}{cost:,.2f}", className="text-end"),
                    html.Td(f"{pct:.1f}%", className="text-end"),
                    html.Td(f"{count} items", className="text-end text-muted"),
                    html.Td(sparkline, className="text-center"),
                ]
            )
        )

    breakdown_table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Work Type", className="text-start"),
                        html.Th("Cost", className="text-end"),
                        html.Th("%", className="text-end"),
                        html.Th("Count", className="text-end"),
                        html.Th("Trend", className="text-center"),
                    ]
                )
            ),
            html.Tbody(category_rows),
        ],
        bordered=True,
        hover=True,
        responsive=True,
        size="sm",
    )

    card_content = dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.I(className=f"fas {get_currency_icon(currency_symbol)} me-2"),
                    html.Strong("Cost Breakdown by Work Type"),
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.H4(
                                f"{currency_symbol}{total_cost:,.2f}",
                                className="text-primary mb-1",
                            ),
                            html.P("Total Project Cost", className="text-muted mb-3"),
                        ],
                        className="text-center",
                    ),
                    breakdown_table,
                    html.Small(
                        f"Based on last {data_points_count} weeks | Flow Distribution classification",
                        className="text-muted",
                    ),
                ]
            ),
        ],
        id=card_id,
        className="mb-3",
    )

    return card_content


def _create_inline_sparkline(values: List[float]) -> html.Div:
    """
    Create inline CSS-based sparkline for cost breakdown table.

    Args:
        values: List of numeric values

    Returns:
        Div containing mini bar chart
    """
    if not values or len(values) < 2:
        return html.Div("—", className="text-muted")

    max_val = max(values) if max(values) > 0 else 1
    normalized = [v / max_val for v in values]

    bars = []
    for i, val in enumerate(normalized):
        bar_height = max(val * 20, 2)  # Max 20px height
        opacity = 0.5 + (i / len(normalized)) * 0.5

        bars.append(
            html.Div(
                style={
                    "width": "3px",
                    "height": f"{bar_height}px",
                    "backgroundColor": "#0d6efd",
                    "opacity": opacity,
                    "borderRadius": "1px",
                    "margin": "0 1px",
                }
            )
        )

    return html.Div(
        bars,
        className="d-flex align-items-end justify-content-center",
        style={"height": "20px", "gap": "1px"},
    )
