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
from typing import Any, Dict, List, Optional

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


def _create_card_footer(text: str, icon: str = "fa-info-circle") -> dbc.CardFooter:
    """Create consistent card footer with info text.

    DRY helper for uniform card footers across budget and dashboard cards.

    Args:
        text: Footer text to display
        icon: FontAwesome icon class (default: fa-info-circle)

    Returns:
        CardFooter component with consistent styling

    Example:
        >>> footer = _create_card_footer(
        ...     "Based on last 7 weeks | Flow Distribution classification",
        ...     "fa-chart-bar"
        ... )
    """
    return dbc.CardFooter(
        html.Div(
            [
                html.I(className=f"fas {icon} me-1"),
                text,
            ],
            className="text-center text-muted py-2 px-3",
            style={"fontSize": "0.85rem", "lineHeight": "1.4"},
        ),
        className="bg-light border-top",
    )


def create_budget_utilization_card(
    consumed_pct: float,
    consumed_eur: float,
    budget_total: float,
    currency_symbol: str = "€",
    data_points_count: int = 12,
    card_id: Optional[str] = None,
    baseline_data: Optional[Dict[str, Any]] = None,
) -> dbc.Card:
    """Create Budget Utilization card showing consumption percentage.

    Health zones (% consumed):
    - Green (<70%): Healthy
    - Yellow (70-85%): Warning
    - Orange (85-95%): High
    - Red (95-100%+): Critical

    Args:
        consumed_pct: Percentage of budget consumed
        consumed_eur: Absolute amount consumed
        budget_total: Total budget amount
        currency_symbol: Currency symbol for display
        data_points_count: Number of weeks for context
        card_id: Optional HTML ID for the card
        baseline_data: Optional dict from get_budget_baseline_vs_actual()

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

    details = {
        "consumed": f"{currency_symbol}{consumed_eur:,.2f}",
        "total": f"{currency_symbol}{budget_total:,.2f}",
        "remaining": f"{currency_symbol}{(budget_total - consumed_eur):,.2f}",
    }

    # Build rich text details for baseline comparison
    text_details = None
    if baseline_data:
        elapsed_weeks = baseline_data["actual"]["elapsed_weeks"]
        allocated_weeks = baseline_data["baseline"]["time_allocated_weeks"]
        elapsed_pct = baseline_data["actual"]["elapsed_pct"]
        variance_pct = baseline_data["variance"]["utilization_vs_pace_pct"]

        # Determine pace status with clear zones
        if variance_pct < -10:
            pace_status = "Under-spending"
            pace_color = "#198754"  # Green
            pace_icon = "fa-check-circle"
        elif variance_pct < -2:
            pace_status = "Efficient"
            pace_color = "#20c997"  # Teal
            pace_icon = "fa-thumbs-up"
        elif variance_pct <= 2:
            pace_status = "On Pace"
            pace_color = "#6c757d"  # Gray
            pace_icon = "fa-equals"
        elif variance_pct <= 10:
            pace_status = "Warning"
            pace_color = "#ffc107"  # Yellow
            pace_icon = "fa-exclamation-triangle"
        else:
            pace_status = "Over-spending"
            pace_color = "#dc3545"  # Red
            pace_icon = "fa-exclamation-circle"

        text_details = [
            html.Div(
                [
                    html.Small(
                        "TIME vs BUDGET UTILIZATION",
                        className="text-muted fw-bold d-block mb-2 text-center",
                        style={"fontSize": "0.75rem"},
                    ),
                    # Two side-by-side progress indicators
                    html.Div(
                        [
                            # Time Elapsed Column
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-clock me-1",
                                                style={"fontSize": "0.7rem"},
                                            ),
                                            html.Small(
                                                "Time", style={"fontSize": "0.75rem"}
                                            ),
                                        ],
                                        className="text-muted text-center mb-1",
                                    ),
                                    html.Div(
                                        f"{elapsed_pct:.0f}%",
                                        className="fw-bold text-center mb-1",
                                        style={
                                            "fontSize": "1.1rem",
                                            "color": "#6c757d",
                                        },
                                    ),
                                    dbc.Progress(
                                        value=elapsed_pct,
                                        color="secondary",
                                        style={"height": "8px"},
                                    ),
                                    html.Small(
                                        f"{elapsed_weeks:.0f}/{allocated_weeks:.0f}w",
                                        className="text-muted d-block text-center mt-1",
                                        style={"fontSize": "0.7rem"},
                                    ),
                                ],
                                style={"flex": "1", "marginRight": "0.5rem"},
                            ),
                            # Budget Used Column
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-wallet me-1",
                                                style={"fontSize": "0.7rem"},
                                            ),
                                            html.Small(
                                                "Budget", style={"fontSize": "0.75rem"}
                                            ),
                                        ],
                                        className="text-muted text-center mb-1",
                                    ),
                                    html.Div(
                                        f"{consumed_pct:.0f}%",
                                        className="fw-bold text-center mb-1",
                                        style={
                                            "fontSize": "1.1rem",
                                            "color": pace_color,
                                        },
                                    ),
                                    dbc.Progress(
                                        value=consumed_pct,
                                        color="success"
                                        if variance_pct < 0
                                        else "danger",
                                        style={"height": "8px"},
                                    ),
                                    html.Small(
                                        f"{consumed_pct:.1f}%",
                                        className="text-muted d-block text-center mt-1",
                                        style={"fontSize": "0.7rem"},
                                    ),
                                ],
                                style={"flex": "1", "marginLeft": "0.5rem"},
                            ),
                        ],
                        className="d-flex mb-3",
                    ),
                    # Pace Status Indicator
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className=f"fas {pace_icon} me-2",
                                        style={
                                            "color": pace_color,
                                            "fontSize": "0.9rem",
                                        },
                                    ),
                                    html.Span(
                                        pace_status,
                                        className="fw-bold",
                                        style={
                                            "fontSize": "0.9rem",
                                            "color": pace_color,
                                        },
                                    ),
                                ],
                                className="d-flex align-items-center justify-content-center mb-1",
                            ),
                            html.Small(
                                f"Budget pace is {abs(variance_pct):.1f}% {'ahead' if variance_pct > 0 else 'behind'} time"
                                if abs(variance_pct) >= 2
                                else "Budget and time are aligned",
                                className="text-muted d-block text-center",
                                style={"fontSize": "0.75rem"},
                            ),
                        ],
                        className="border-top pt-2",
                    ),
                ],
            ),
        ]

    metric_data = {
        "metric_name": "budget_utilization",
        "value": consumed_pct,
        "unit": "%",
        "performance_tier": tier_label,
        "performance_tier_color": tier_color,
        "error_state": "success",
        "total_issue_count": 0,
        "_n_weeks": data_points_count,
        "details": details,
        "tooltip": "Shows budget consumption rate vs time elapsed. Compares actual spending pace against planned pace. Healthy (<70%): Spending slower than time passing. Warning (70-95%): Pace matches time. Critical (>95%): Burning budget faster than expected.",
    }

    return create_metric_card(
        metric_data, card_id, show_details_button=False, text_details=text_details
    )


def create_weekly_burn_rate_card(
    burn_rate: float,
    weekly_values: List[float],
    weekly_labels: List[str],
    trend_pct: float,
    currency_symbol: str = "€",
    data_points_count: int = 4,
    card_id: Optional[str] = None,
    baseline_data: Optional[Dict[str, Any]] = None,
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
        baseline_data: Optional dict from get_budget_baseline_vs_actual()

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

    details = {
        "trend": f"{trend_arrow} {abs(trend_pct):.1f}%",
        "trend_color": trend_color,
    }

    # Build rich text details for baseline comparison
    text_details = None
    if baseline_data:
        import math

        budgeted_rate = baseline_data["baseline"]["team_cost_per_week_eur"]
        variance_eur = baseline_data["variance"]["burn_rate_variance_eur"]
        variance_pct = baseline_data["variance"]["burn_rate_variance_pct"]
        runway_weeks = baseline_data["actual"]["runway_weeks"]

        # Variance color badge
        if abs(variance_pct) < 5:
            variance_badge = dbc.Badge("On Target", color="success", className="ms-2")
        elif variance_eur < 0:
            variance_badge = dbc.Badge(
                f"{abs(variance_pct):.1f}% Under Budget",
                color="success",
                className="ms-2",
            )
        else:
            variance_badge = dbc.Badge(
                f"{variance_pct:.1f}% Over Budget", color="danger", className="ms-2"
            )

        # Calculate projected impact
        projected_impact = (
            variance_eur * runway_weeks
            if not math.isinf(runway_weeks) and runway_weeks > 0
            else 0
        )

        # Calculate deviation percentage for centered bar visualization
        deviation_pct = min(max(variance_pct, -50), 50)
        visual_position = 50 + deviation_pct

        text_details = [
            html.Div(
                [
                    html.Small(
                        "BASELINE vs ACTUAL",
                        className="text-muted fw-bold d-block mb-2 text-center",
                        style={"fontSize": "0.75rem"},
                    ),
                    html.Div(
                        [
                            html.Span(
                                f"Budgeted: {currency_symbol}{budgeted_rate:,.0f}/wk",
                                className="text-muted d-block mb-1 text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Span(
                                f"Actual: {currency_symbol}{burn_rate:,.0f}/wk",
                                className="text-muted d-block mb-2 text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                        ],
                    ),
                    # Deviation indicator (centered at baseline)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Small(
                                        "Under Budget",
                                        className="text-success",
                                        style={"fontSize": "0.65rem"},
                                    ),
                                    html.Small(
                                        "Baseline",
                                        className="text-muted",
                                        style={
                                            "fontSize": "0.65rem",
                                            "position": "absolute",
                                            "left": "50%",
                                            "transform": "translateX(-50%)",
                                        },
                                    ),
                                    html.Small(
                                        "Over Budget",
                                        className="text-danger",
                                        style={"fontSize": "0.65rem"},
                                    ),
                                ],
                                className="d-flex justify-content-between mb-1 position-relative",
                            ),
                            html.Div(
                                [
                                    # Background gradient track
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "width": "100%",
                                            "height": "6px",
                                            "background": "linear-gradient(to right, #198754 0%, #6c757d 50%, #dc3545 100%)",
                                            "borderRadius": "3px",
                                            "opacity": "0.3",
                                        },
                                    ),
                                    # Baseline marker (center)
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "left": "50%",
                                            "width": "2px",
                                            "height": "12px",
                                            "backgroundColor": "#6c757d",
                                            "transform": "translateX(-50%)",
                                            "top": "-3px",
                                        },
                                    ),
                                    # Actual position indicator
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "left": f"{visual_position}%",
                                            "width": "12px",
                                            "height": "12px",
                                            "backgroundColor": "#ffffff",
                                            "borderRadius": "50%",
                                            "border": "2.5px solid #212529",
                                            "transform": "translateX(-50%)",
                                            "top": "-3px",
                                            "boxShadow": "0 2px 6px rgba(0,0,0,0.3)",
                                        },
                                    ),
                                ],
                                style={
                                    "position": "relative",
                                    "height": "6px",
                                    "marginBottom": "0.5rem",
                                    "marginLeft": "8px",
                                    "marginRight": "8px",
                                },
                            ),
                        ],
                        className="mb-2",
                    ),
                    html.Div(
                        [
                            html.Span(
                                "Variance: ",
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                            variance_badge,
                        ],
                        className="d-flex align-items-center justify-content-center mb-2",
                    ),
                    html.Div(
                        [
                            html.Span(
                                f"Projected Impact: {currency_symbol}{abs(projected_impact):,.0f}",
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                            dbc.Badge(
                                "Savings" if projected_impact < 0 else "Overrun",
                                color="success" if projected_impact < 0 else "danger",
                                className="ms-2",
                            )
                            if abs(projected_impact) > budgeted_rate
                            else None,
                        ],
                        className="d-flex align-items-center justify-content-center",
                    ),
                ],
            )
        ]

    metric_data = {
        "metric_name": "weekly_burn_rate",
        "value": burn_rate,
        "unit": f"{currency_symbol}/week",
        "performance_tier": None,
        "performance_tier_color": "secondary",
        "error_state": "success",
        "total_issue_count": 0,
        "_n_weeks": data_points_count,
        "details": details,
        "tooltip": "Average weekly spending rate calculated from actual costs divided by elapsed time. Compares actual burn rate against budgeted weekly cost. Green: Under budget. Yellow: On target (±10%). Red: Over budget. Includes projected total savings/overrun.",
    }

    return create_metric_card(
        metric_data, card_id, show_details_button=False, text_details=text_details
    )


def create_budget_runway_card(
    runway_weeks: float,
    pert_forecast_weeks: Optional[float] = None,
    currency_symbol: str = "€",
    data_points_count: int = 12,
    card_id: Optional[str] = None,
    baseline_data: Optional[Dict[str, Any]] = None,
) -> dbc.Card:
    """
    Create Budget Runway card with critical <4 weeks warning.

    Args:
        runway_weeks: Remaining budget runway in weeks
        pert_forecast_weeks: PERT forecast completion weeks (for comparison)
        currency_symbol: Currency symbol for display
        card_id: Optional HTML ID for the card
        baseline_data: Optional dict from get_budget_baseline_vs_actual()

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> card = create_budget_runway_card(12.5, 15.0, "€")
    """
    import math

    # Handle infinity runway (when burn rate is 0)
    if math.isinf(runway_weeks):
        metric_data = {
            "metric_name": "budget_runway",
            "value": None,
            "unit": "",
            "performance_tier": "No Consumption",
            "performance_tier_color": "blue",
            "error_state": "info",
            "total_issue_count": 0,
            "_n_weeks": data_points_count,
            "details": {
                "status": "Waiting for work completion to calculate burn rate. "
                "Budget runway is calculated from ACTUAL completed items, not just team cost."
            },
        }
        return create_metric_card(metric_data, card_id, show_details_button=False)

    # Handle negative runway (over budget)
    if runway_weeks < 0:
        metric_data = {
            "metric_name": "budget_runway",
            "value": abs(runway_weeks),
            "unit": "weeks over budget",
            "performance_tier": "Over Budget",
            "performance_tier_color": "red",
            "error_state": "success",  # Must be "success" to render as metric card, not error card
            "total_issue_count": 0,
            "_n_weeks": data_points_count,
            "details": {
                "status": "Budget exceeded. Immediate action required: Review scope, increase budget, or reduce team costs."
            },
        }
        return create_metric_card(metric_data, card_id, show_details_button=False)

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

    # Build rich text details for baseline comparison
    text_details = None
    if baseline_data:
        extension_weeks = baseline_data["variance"]["runway_vs_baseline_weeks"]

        # Extension badge
        if abs(extension_weeks) < 1:
            extension_badge = dbc.Badge("On Target", color="success", className="ms-2")
        elif extension_weeks > 0:
            extension_badge = dbc.Badge(
                f"+{extension_weeks:.2f}w Extension", color="success", className="ms-2"
            )
        else:
            extension_badge = dbc.Badge(
                f"{extension_weeks:.2f}w Shortage", color="danger", className="ms-2"
            )

        # Calculate forecast comparison
        forecast_gap = runway_weeks - pert_forecast_weeks if pert_forecast_weeks else 0
        allocated_weeks_baseline = baseline_data["baseline"]["time_allocated_weeks"]

        # Calculate deviation percentage for centered bar visualization
        extension_pct = (
            (extension_weeks / allocated_weeks_baseline * 100)
            if allocated_weeks_baseline > 0
            else 0
        )
        deviation_pct = min(max(extension_pct, -50), 50)
        visual_position = 50 + deviation_pct

        text_details = [
            html.Div(
                [
                    html.Small(
                        "RUNWAY COMPARISON",
                        className="text-muted fw-bold d-block mb-2 text-center",
                        style={"fontSize": "0.75rem"},
                    ),
                    html.Div(
                        [
                            html.Span(
                                f"Allocated: {allocated_weeks_baseline:.0f} weeks",
                                className="text-muted d-block mb-1 text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Span(
                                f"Actual Runway: {runway_weeks:.2f} weeks",
                                className="text-muted d-block mb-2 text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                        ],
                    ),
                    # Deviation indicator (centered at baseline)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Small(
                                        "Shorter",
                                        className="text-danger",
                                        style={"fontSize": "0.65rem"},
                                    ),
                                    html.Small(
                                        "Baseline",
                                        className="text-muted",
                                        style={
                                            "fontSize": "0.65rem",
                                            "position": "absolute",
                                            "left": "50%",
                                            "transform": "translateX(-50%)",
                                        },
                                    ),
                                    html.Small(
                                        "Extended",
                                        className="text-success",
                                        style={"fontSize": "0.65rem"},
                                    ),
                                ],
                                className="d-flex justify-content-between mb-1 position-relative",
                            ),
                            html.Div(
                                [
                                    # Background gradient track
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "width": "100%",
                                            "height": "6px",
                                            "background": "linear-gradient(to right, #dc3545 0%, #6c757d 50%, #198754 100%)",
                                            "borderRadius": "3px",
                                            "opacity": "0.3",
                                        },
                                    ),
                                    # Baseline marker (center)
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "left": "50%",
                                            "width": "2px",
                                            "height": "12px",
                                            "backgroundColor": "#6c757d",
                                            "transform": "translateX(-50%)",
                                            "top": "-3px",
                                        },
                                    ),
                                    # Actual position indicator
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "left": f"{visual_position}%",
                                            "width": "12px",
                                            "height": "12px",
                                            "backgroundColor": "#ffffff",
                                            "borderRadius": "50%",
                                            "border": "2.5px solid #212529",
                                            "transform": "translateX(-50%)",
                                            "top": "-3px",
                                            "boxShadow": "0 2px 6px rgba(0,0,0,0.3)",
                                        },
                                    ),
                                ],
                                style={
                                    "position": "relative",
                                    "height": "6px",
                                    "marginBottom": "0.5rem",
                                    "marginLeft": "8px",
                                    "marginRight": "8px",
                                },
                            ),
                        ],
                        className="mb-2",
                    ),
                    html.Div(
                        [
                            html.Span(
                                "Extension: ",
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                            extension_badge,
                        ],
                        className="d-flex align-items-center justify-content-center mb-2",
                    ),
                    html.Div(
                        [
                            html.Span(
                                f"vs Forecast: {forecast_gap:+.1f}w"
                                if pert_forecast_weeks
                                else "Forecast: N/A",
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                            dbc.Badge(
                                "Buffer" if forecast_gap > 0 else "Short",
                                color="success" if forecast_gap > 0 else "warning",
                                className="ms-2",
                            )
                            if pert_forecast_weeks and abs(forecast_gap) > 1
                            else None,
                        ],
                        className="d-flex align-items-center justify-content-center",
                    ),
                ],
            )
        ]

    metric_data = {
        "metric_name": "budget_runway",
        "value": runway_weeks,
        "unit": "weeks",
        "performance_tier": tier_label,
        "performance_tier_color": tier_color,
        "error_state": "success",
        "total_issue_count": 0,
        "_n_weeks": data_points_count,
        "details": details,
        "tooltip": "How long the budget will last at current burn rate. Calculated as remaining budget divided by weekly burn rate. Green: Runway exceeds allocation. Yellow: Close to baseline. Red: Running out faster than planned. Shows extension/shortfall vs allocated time and forecast.",
    }

    return create_metric_card(
        metric_data, card_id, show_details_button=False, text_details=text_details
    )


def create_cost_per_item_card(
    cost_per_item: float,
    pert_weighted_avg: Optional[float] = None,
    currency_symbol: str = "€",
    data_points_count: int = 12,
    card_id: Optional[str] = None,
    baseline_data: Optional[Dict[str, Any]] = None,
) -> dbc.Card:
    """
    Create Cost per Item card (auto-calculated from Team Cost ÷ Velocity).

    Args:
        cost_per_item: Current cost per item
        pert_weighted_avg: PERT-weighted average cost per item
        currency_symbol: Currency symbol for display
        card_id: Optional HTML ID for the card
        baseline_data: Optional dict from get_budget_baseline_vs_actual()

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> card = create_cost_per_item_card(425.50, 410.20, "€")
    """
    details = {"calculation": "Auto-calculated: Team Cost / Velocity"}
    if pert_weighted_avg:
        details["pert_avg"] = f"{currency_symbol}{pert_weighted_avg:.2f}"

    # Build rich text details for baseline comparison
    text_details = None
    if baseline_data:
        variance_eur = baseline_data["variance"]["cost_per_item_variance_eur"]
        variance_pct = baseline_data["variance"]["cost_per_item_variance_pct"]
        velocity = baseline_data["actual"]["velocity_items"]
        baseline_velocity = baseline_data["baseline"]["assumed_baseline_velocity"]
        budgeted_rate = baseline_data["baseline"]["team_cost_per_week_eur"]

        budgeted_cost_per_item = budgeted_rate / baseline_velocity

        # Variance badge
        if abs(variance_pct) < 5:
            variance_badge = dbc.Badge("On Target", color="success", className="ms-2")
        elif variance_eur < 0:
            variance_badge = dbc.Badge(
                f"{abs(variance_pct):.1f}% More Efficient",
                color="success",
                className="ms-2",
            )
        else:
            variance_badge = dbc.Badge(
                f"{variance_pct:.1f}% Less Efficient", color="danger", className="ms-2"
            )

        # Calculate deviation percentage (negative = more efficient, positive = less efficient)
        # Cap at ±50% for visual display
        deviation_pct = min(max(variance_pct, -50), 50)
        # Convert to 0-100 scale: -50% = 0, 0% = 50, +50% = 100
        visual_position = 50 + deviation_pct

        text_details = [
            html.Div(
                [
                    html.Small(
                        "BASELINE vs ACTUAL",
                        className="text-muted fw-bold d-block mb-2 text-center",
                        style={"fontSize": "0.75rem"},
                    ),
                    html.Div(
                        [
                            html.Span(
                                f"Budgeted: {currency_symbol}{budgeted_cost_per_item:.0f}/item @ {baseline_velocity:.2f} items/wk (baseline)",
                                className="text-muted d-block mb-1 text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Span(
                                f"Actual: {currency_symbol}{cost_per_item:.0f}/item @ {velocity:.2f} items/wk",
                                className="text-muted d-block mb-2 text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                        ],
                    ),
                    # Efficiency deviation indicator (centered at baseline)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Small(
                                        "More Efficient",
                                        className="text-success",
                                        style={"fontSize": "0.65rem"},
                                    ),
                                    html.Small(
                                        "Baseline",
                                        className="text-muted",
                                        style={
                                            "fontSize": "0.65rem",
                                            "position": "absolute",
                                            "left": "50%",
                                            "transform": "translateX(-50%)",
                                        },
                                    ),
                                    html.Small(
                                        "Less Efficient",
                                        className="text-danger",
                                        style={"fontSize": "0.65rem"},
                                    ),
                                ],
                                className="d-flex justify-content-between mb-1 position-relative",
                            ),
                            html.Div(
                                [
                                    # Background track
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "width": "100%",
                                            "height": "6px",
                                            "background": "linear-gradient(to right, #198754 0%, #6c757d 50%, #dc3545 100%)",
                                            "borderRadius": "3px",
                                            "opacity": "0.3",
                                        },
                                    ),
                                    # Baseline marker (center)
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "left": "50%",
                                            "width": "2px",
                                            "height": "12px",
                                            "backgroundColor": "#6c757d",
                                            "transform": "translateX(-50%)",
                                            "top": "-3px",
                                        },
                                    ),
                                    # Actual position indicator
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "left": f"{visual_position}%",
                                            "width": "12px",
                                            "height": "12px",
                                            "backgroundColor": "#ffffff",
                                            "borderRadius": "50%",
                                            "border": "2.5px solid #212529",
                                            "transform": "translateX(-50%)",
                                            "top": "-3px",
                                            "boxShadow": "0 2px 6px rgba(0,0,0,0.3)",
                                        },
                                    ),
                                ],
                                style={
                                    "position": "relative",
                                    "height": "6px",
                                    "marginBottom": "0.5rem",
                                    "marginLeft": "8px",
                                    "marginRight": "8px",
                                },
                            ),
                        ],
                        className="mb-2",
                    ),
                    html.Div(
                        [
                            html.Span(
                                "Efficiency: ",
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                            variance_badge,
                        ],
                        className="d-flex align-items-center justify-content-center",
                    ),
                ],
            )
        ]

    metric_data = {
        "metric_name": "cost_per_item",
        "value": cost_per_item,
        "unit": f"{currency_symbol}/item",
        "performance_tier": None,
        "performance_tier_color": "secondary",
        "error_state": "success",
        "total_issue_count": 0,
        "_n_weeks": data_points_count,
        "details": details,
        "tooltip": "Team cost divided by delivery velocity (items/week). Baseline velocity is captured from Recent Completions (Last 4 Weeks) when budget is configured and used as fixed reference. Actual velocity updates dynamically. Shows efficiency: lower cost per item = better. Variance shows if team is more/less efficient than baseline.",
    }

    return create_metric_card(
        metric_data, card_id, show_details_button=False, text_details=text_details
    )


def create_cost_per_point_card(
    cost_per_point: float,
    pert_weighted_avg: Optional[float] = None,
    points_available: bool = True,
    currency_symbol: str = "€",
    data_points_count: int = 12,
    card_id: Optional[str] = None,
    baseline_data: Optional[Dict[str, Any]] = None,
) -> dbc.Card:
    """
    Create Cost per Point card (conditional on points_field_available).

    Args:
        cost_per_point: Current cost per story point
        pert_weighted_avg: PERT-weighted average cost per point
        points_available: Whether points field is available
        currency_symbol: Currency symbol for display
        card_id: Optional HTML ID for the card
        baseline_data: Optional dict from get_budget_baseline_vs_actual()

    Returns:
        Dash Bootstrap Card component or warning card

    Example:
        >>> card = create_cost_per_point_card(85.10, 82.40, True, "€")
    """
    if not points_available:
        # Return placeholder card when points are not configured
        metric_data = {
            "metric_name": "cost_per_point",
            "value": None,
            "unit": "",
            "performance_tier": "Not Configured",
            "performance_tier_color": "secondary",
            "error_state": "info",
            "total_issue_count": 0,
            "_n_weeks": data_points_count,
            "details": {
                "status": "Story points field not configured. "
                "Set up points field in Settings → Field Mapping to enable."
            },
        }
        return create_metric_card(metric_data, card_id, show_details_button=False)

    details = {"calculation": "Auto-calculated: Team Cost / Velocity (points)"}
    if pert_weighted_avg:
        details["pert_avg"] = f"{currency_symbol}{pert_weighted_avg:.2f}"

    # Build rich text details for baseline comparison (similar to cost per item)
    text_details = None
    if baseline_data:
        velocity_points = baseline_data["actual"]["velocity_points"]
        budgeted_rate = baseline_data["baseline"]["team_cost_per_week_eur"]
        # Get baseline velocity from budget settings (not hardcoded)
        baseline_velocity_points = baseline_data["baseline"].get(
            "assumed_baseline_velocity_points", 21.0
        )
        budgeted_cost_per_point = budgeted_rate / baseline_velocity_points

        variance_eur = cost_per_point - budgeted_cost_per_point
        variance_pct = (
            (variance_eur / budgeted_cost_per_point * 100)
            if budgeted_cost_per_point > 0
            else 0
        )

        # Variance badge
        if abs(variance_pct) < 5:
            variance_badge = dbc.Badge("On Target", color="success", className="ms-2")
        elif variance_eur < 0:
            variance_badge = dbc.Badge(
                f"{abs(variance_pct):.1f}% More Efficient",
                color="success",
                className="ms-2",
            )
        else:
            variance_badge = dbc.Badge(
                f"{variance_pct:.1f}% Less Efficient", color="danger", className="ms-2"
            )

        # Calculate deviation percentage (negative = more efficient, positive = less efficient)
        # Cap at ±50% for visual display
        deviation_pct = min(max(variance_pct, -50), 50)
        # Convert to 0-100 scale: -50% = 0, 0% = 50, +50% = 100
        visual_position = 50 + deviation_pct

        text_details = [
            html.Div(
                [
                    html.Small(
                        "BASELINE vs ACTUAL",
                        className="text-muted fw-bold d-block mb-2 text-center",
                        style={"fontSize": "0.75rem"},
                    ),
                    html.Div(
                        [
                            html.Span(
                                f"Budgeted: {currency_symbol}{budgeted_cost_per_point:.0f}/pt @ {baseline_velocity_points:.2f} points/wk (baseline)",
                                className="text-muted d-block mb-1 text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Span(
                                f"Actual: {currency_symbol}{cost_per_point:.0f}/pt @ {velocity_points:.2f} points/wk",
                                className="text-muted d-block mb-2 text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                        ],
                    ),
                    # Efficiency deviation indicator (centered at baseline)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Small(
                                        "More Efficient",
                                        className="text-success",
                                        style={"fontSize": "0.65rem"},
                                    ),
                                    html.Small(
                                        "Baseline",
                                        className="text-muted",
                                        style={
                                            "fontSize": "0.65rem",
                                            "position": "absolute",
                                            "left": "50%",
                                            "transform": "translateX(-50%)",
                                        },
                                    ),
                                    html.Small(
                                        "Less Efficient",
                                        className="text-danger",
                                        style={"fontSize": "0.65rem"},
                                    ),
                                ],
                                className="d-flex justify-content-between mb-1 position-relative",
                            ),
                            html.Div(
                                [
                                    # Background track
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "width": "100%",
                                            "height": "6px",
                                            "background": "linear-gradient(to right, #198754 0%, #6c757d 50%, #dc3545 100%)",
                                            "borderRadius": "3px",
                                            "opacity": "0.3",
                                        },
                                    ),
                                    # Baseline marker (center)
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "left": "50%",
                                            "width": "2px",
                                            "height": "12px",
                                            "backgroundColor": "#6c757d",
                                            "transform": "translateX(-50%)",
                                            "top": "-3px",
                                        },
                                    ),
                                    # Actual position indicator
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "left": f"{visual_position}%",
                                            "width": "12px",
                                            "height": "12px",
                                            "backgroundColor": "#ffffff",
                                            "borderRadius": "50%",
                                            "border": "2.5px solid #212529",
                                            "transform": "translateX(-50%)",
                                            "top": "-3px",
                                            "boxShadow": "0 2px 6px rgba(0,0,0,0.3)",
                                        },
                                    ),
                                ],
                                style={
                                    "position": "relative",
                                    "height": "6px",
                                    "marginBottom": "0.5rem",
                                    "marginLeft": "8px",
                                    "marginRight": "8px",
                                },
                            ),
                        ],
                        className="mb-2",
                    ),
                    html.Div(
                        [
                            html.Span(
                                "Efficiency: ",
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                            variance_badge,
                        ],
                        className="d-flex align-items-center justify-content-center",
                    ),
                ],
            )
        ]

    metric_data = {
        "metric_name": "cost_per_point",
        "value": cost_per_point,
        "unit": f"{currency_symbol}/point",
        "performance_tier": None,
        "performance_tier_color": "secondary",
        "error_state": "success",
        "total_issue_count": 0,
        "_n_weeks": data_points_count,
        "details": details,
        "tooltip": "Team cost divided by story point velocity (points/week). Baseline velocity is captured from Recent Completions (Last 4 Weeks) when budget is configured and used as fixed reference. Actual velocity updates dynamically. Shows efficiency: lower cost per point = better. Variance shows if team is more/less efficient than baseline.",
    }

    return create_metric_card(
        metric_data, card_id, show_details_button=False, text_details=text_details
    )


def create_budget_forecast_card(
    forecast_value: float,
    confidence_low: float,
    confidence_high: float,
    consumed_pct: float,
    consumed_eur: float,
    budget_total: float,
    confidence_level: str = "established",
    currency_symbol: str = "€",
    card_id: Optional[str] = None,
    data_points_count: int = 12,
) -> dbc.Card:
    """
    Create Budget Status card with consumed/remaining progress and forecast.

    Compact layout with horizontal progress bar and inline metrics.

    Args:
        forecast_value: Forecasted total budget needed
        confidence_low: Lower confidence bound (pessimistic)
        confidence_high: Upper confidence bound (optimistic)
        consumed_pct: Percentage of budget consumed
        consumed_eur: Absolute amount consumed
        budget_total: Total budget amount
        confidence_level: "established" or "building"
        currency_symbol: Currency symbol for display
        card_id: Optional HTML ID for the card
        data_points_count: Number of weeks for context

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> card = create_budget_forecast_card(
        ...     48500, 45000, 52000, 75.5, 37750, 50000, "established", "€"
        ... )
    """
    remaining_eur = budget_total - consumed_eur

    # Build text details with progress bar and breakdown
    if consumed_pct < 70:
        tier_color = "green"
        tier_label = "Healthy"
        progress_color = "success"
    elif consumed_pct < 85:
        tier_color = "yellow"
        tier_label = "Warning"
        progress_color = "warning"
    elif consumed_pct < 95:
        tier_color = "orange"
        tier_label = "High"
        progress_color = "warning"
    else:
        tier_color = "red"
        tier_label = "Critical"
        progress_color = "danger"

    remaining_eur = budget_total - consumed_eur

    # Build text details with progress bar and breakdown
    text_details = [
        html.Div(
            [
                html.Small(
                    "BUDGET BREAKDOWN",
                    className="text-muted fw-bold d-block mb-3 text-center",
                    style={"fontSize": "0.75rem"},
                ),
                # Progress bar
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    f"{consumed_pct:.1f}% Consumed",
                                    className="text-muted",
                                    style={"fontSize": "0.75rem"},
                                ),
                                html.Span(
                                    tier_label,
                                    className="badge",
                                    style={
                                        "fontSize": "0.7rem",
                                        "backgroundColor": "#28a745"
                                        if tier_color == "green"
                                        else "#ffc107"
                                        if tier_color == "yellow"
                                        else "#fd7e14"
                                        if tier_color == "orange"
                                        else "#dc3545",
                                    },
                                ),
                            ],
                            className="d-flex justify-content-between align-items-center mb-1",
                        ),
                        dbc.Progress(
                            value=min(consumed_pct, 100),
                            color=progress_color,
                            style={"height": "8px"},
                            className="mb-3",
                        ),
                    ],
                ),
                # Consumed and Remaining breakdown
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Span(
                                    "Consumed",
                                    className="text-muted d-block text-center",
                                    style={"fontSize": "0.75rem"},
                                ),
                                html.Span(
                                    f"{currency_symbol}{consumed_eur:,.0f}",
                                    className="fw-bold d-block text-center",
                                    style={"fontSize": "0.9rem"},
                                ),
                            ],
                            width=6,
                            className="mb-2",
                        ),
                        dbc.Col(
                            [
                                html.Span(
                                    "Remaining",
                                    className="text-muted d-block text-center",
                                    style={"fontSize": "0.75rem"},
                                ),
                                html.Span(
                                    f"{currency_symbol}{remaining_eur:,.0f}",
                                    className="fw-bold d-block text-center",
                                    style={"fontSize": "0.9rem"},
                                ),
                            ],
                            width=6,
                            className="mb-2",
                        ),
                    ],
                    className="g-2",
                ),
                # Forecast
                html.Div(
                    [
                        html.I(
                            className="fas fa-chart-line me-2 text-info",
                            style={"fontSize": "0.85rem"},
                        ),
                        html.Span(
                            "Forecast: ",
                            className="text-muted",
                            style={"fontSize": "0.8rem"},
                        ),
                        html.Span(
                            f"{currency_symbol}{forecast_value:,.0f}",
                            className="fw-bold",
                            style={"fontSize": "0.85rem"},
                        ),
                        html.Span(
                            f" ({currency_symbol}{confidence_low:,.0f}-{currency_symbol}{confidence_high:,.0f})",
                            className="text-muted",
                            style={"fontSize": "0.75rem"},
                        ),
                    ],
                    className="text-center mt-2 pt-2 border-top",
                ),
            ],
        )
    ]

    metric_data = {
        "metric_name": "budget_status",
        "value": budget_total,
        "unit": currency_symbol,
        "performance_tier": tier_label,
        "performance_tier_color": tier_color,
        "error_state": "success",
        "total_issue_count": 0,
        "_n_weeks": data_points_count,
        "details": {},
        "tooltip": "Total budget allocation with consumption status. Shows consumed vs remaining budget with PERT-based forecast. Health zones indicate spending pace relative to timeline.",
    }

    return create_metric_card(
        metric_data, card_id, show_details_button=False, text_details=text_details
    )


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
                html.Strong("Cost Breakdown by Work Distribution"),
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
                ]
            ),
            _create_card_footer(
                f"Costs aggregated over {data_points_count} weeks • Categorized by Flow Distribution types",
                "fa-chart-bar",
            ),
        ],
        id=card_id,
        className="metric-card mb-3 h-100",
    )

    return card_content


def _create_inline_sparkline(values: List[float]):
    """
    Create inline scatter chart sparkline for cost breakdown table.

    Uses Plotly mini scatter chart to show cost trends over time,
    similar to other metric cards but more compact for table cells.

    Args:
        values: List of cost values over time

    Returns:
        dcc.Graph or html.Div containing mini scatter chart or placeholder
    """
    from dash import dcc
    import plotly.graph_objects as go

    if not values or len(values) < 2:
        return html.Div("—", className="text-muted")

    # Create mini scatter chart
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=list(range(len(values))),
            y=values,
            mode="lines+markers",
            line={"color": "#0d6efd", "width": 2},
            marker={"size": 4, "color": "#0d6efd"},
            hovertemplate="€%{y:,.0f}<extra></extra>",
            showlegend=False,
        )
    )

    # Determine y-axis range for better visualization
    min_val = min(values)
    max_val = max(values)
    range_padding = (max_val - min_val) * 0.2 if max_val > min_val else max_val * 0.1
    y_min = max(0, min_val - range_padding)  # Never go below 0 for costs
    y_max = max_val + range_padding

    fig.update_layout(
        {
            "height": 40,
            "margin": {"t": 2, "r": 2, "b": 2, "l": 2},
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "xaxis": {
                "visible": False,
                "showgrid": False,
            },
            "yaxis": {
                "visible": False,
                "showgrid": False,
                "range": [y_min, y_max],
            },
            "hovermode": "closest",
        }
    )

    return dcc.Graph(
        figure=fig,
        config={
            "displayModeBar": False,
            "staticPlot": False,
            "responsive": True,
        },
        style={"height": "40px", "minWidth": "120px"},
        className="w-100",
    )


def create_forecast_alignment_card(
    pert_time_items: float,
    pert_time_points: Optional[float],
    runway_weeks: float,
    show_points: bool = True,
    card_id: Optional[str] = None,
) -> dbc.Card:
    """
    Create Forecast vs Budget Alignment card showing timeline comparison.

    Displays gap between PERT forecast completion time and budget runway
    for both items and points tracking. Styled as table matching Cost Breakdown card.

    Args:
        pert_time_items: PERT forecast days (items-based)
        pert_time_points: PERT forecast days (points-based)
        runway_weeks: Budget runway in weeks
        show_points: Whether points tracking is active
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component (full-width table layout)

    Health Status:
        - Healthy (green): Budget runway >= PERT forecast (gap >= 0)
        - Warning (yellow): Gap between -2 and 0 weeks
        - At Risk (red): Budget exhausts >2 weeks before completion
        - No Data (blue): No budget consumption detected

    Example:
        >>> card = create_forecast_alignment_card(105.0, 92.4, 12.5, True)
    """
    import math
    from configuration import COLOR_PALETTE

    # Convert days to weeks
    pert_weeks_items = pert_time_items / 7.0
    pert_weeks_points = pert_time_points / 7.0 if pert_time_points else pert_weeks_items

    # Handle infinity runway (no budget consumption)
    if math.isinf(runway_weeks):
        # Show informational message when no consumption data
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Span(
                            "Forecast vs Budget Alignment",
                            className="fw-bold",
                        ),
                        " ",
                        html.I(
                            className="fas fa-info-circle text-info",
                            title="Waiting for budget consumption data",
                        ),
                    ],
                ),
                dbc.CardBody(
                    [
                        dbc.Alert(
                            [
                                html.I(className="fas fa-hourglass-start me-2"),
                                html.Strong("No Budget Consumption Data"),
                                html.P(
                                    "Budget tracking will begin once work completion is recorded. "
                                    "The burn rate is calculated from ACTUAL completed work, not just team cost. "
                                    "Complete some items to start tracking budget consumption.",
                                    className="mb-0 mt-2 small",
                                ),
                            ],
                            color="info",
                            className="mb-0",
                        )
                    ]
                ),
            ],
            id=card_id,
            className="mb-3",
        )

    # Calculate gaps
    gap_items = runway_weeks - pert_weeks_items
    gap_points = runway_weeks - pert_weeks_points

    # Determine overall health (worst case of items/points)
    min_gap = min(gap_items, gap_points) if show_points else gap_items
    if min_gap >= 0:
        overall_health = "Healthy"
        health_color = "#198754"  # green
        health_icon = "fa-check-circle"
    elif min_gap >= -2:
        overall_health = "Warning"
        health_color = "#ffc107"  # yellow
        health_icon = "fa-exclamation-triangle"
    else:
        overall_health = "At Risk"
        health_color = "#dc3545"  # red
        health_icon = "fa-times-circle"

    # Helper to format gap display
    def format_gap(gap: float) -> tuple[str, str, str]:
        if gap >= 0:
            return f"+{gap:.1f} weeks", "#198754", "fa-arrow-up"
        elif gap >= -2:
            return f"{gap:.1f} weeks", "#ffc107", "fa-minus-circle"
        else:
            return f"{gap:.1f} weeks", "#dc3545", "fa-arrow-down"

    gap_items_text, gap_items_color, gap_items_icon = format_gap(gap_items)
    gap_points_text, gap_points_color, gap_points_icon = format_gap(gap_points)

    # Build table rows
    table_rows = []

    # Items-based row
    table_rows.append(
        html.Tr(
            [
                html.Td(
                    [
                        html.I(
                            className="fas fa-tasks me-2",
                            style={"color": COLOR_PALETTE["items"]},
                        ),
                        "Items-based",
                    ],
                    className="text-start fw-semibold",
                ),
                html.Td(f"{pert_weeks_items:.1f} weeks", className="text-end"),
                html.Td(f"{runway_weeks:.1f} weeks", className="text-end"),
                html.Td(
                    [
                        html.I(className=f"fas {gap_items_icon} me-1"),
                        html.Span(
                            gap_items_text,
                            style={"color": gap_items_color, "fontWeight": "bold"},
                        ),
                    ],
                    className="text-end",
                ),
            ]
        )
    )

    # Points-based row (if enabled)
    if show_points:
        table_rows.append(
            html.Tr(
                [
                    html.Td(
                        [
                            html.I(
                                className="fas fa-chart-bar me-2",
                                style={"color": COLOR_PALETTE["points"]},
                            ),
                            "Points-based",
                        ],
                        className="text-start fw-semibold",
                    ),
                    html.Td(f"{pert_weeks_points:.1f} weeks", className="text-end"),
                    html.Td(f"{runway_weeks:.1f} weeks", className="text-end"),
                    html.Td(
                        [
                            html.I(className=f"fas {gap_points_icon} me-1"),
                            html.Span(
                                gap_points_text,
                                style={"color": gap_points_color, "fontWeight": "bold"},
                            ),
                        ],
                        className="text-end",
                    ),
                ]
            )
        )

    alignment_table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Metric", className="text-start"),
                        html.Th("PERT Forecast", className="text-end"),
                        html.Th("Budget Runway", className="text-end"),
                        html.Th("Gap", className="text-end"),
                    ]
                )
            ),
            html.Tbody(table_rows),
        ],
        bordered=True,
        hover=True,
        responsive=True,
        size="sm",
    )

    # Create card with health status badge
    from ui.tooltip_utils import create_info_tooltip

    card = dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Span(
                        "Forecast vs Budget Alignment",
                        className="fw-bold",
                    ),
                    " ",
                    create_info_tooltip(
                        help_text="Compares PERT forecast completion time with budget runway. "
                        "Positive gap = budget outlasts forecast (healthy). "
                        "Negative gap = budget exhausts before completion (risk). "
                        "Budget runway is calculated from ACTUAL work completed, not just team cost.",
                        id_suffix="metric-forecast_alignment",
                        placement="top",
                        variant="dark",
                    ),
                    html.Div(
                        [
                            html.I(className=f"fas {health_icon} me-1"),
                            html.Span(
                                overall_health,
                                className="badge",
                                style={
                                    "backgroundColor": health_color,
                                    "color": "white",
                                    "fontSize": "0.85rem",
                                    "padding": "0.35rem 0.65rem",
                                },
                            ),
                        ],
                        className="ms-auto d-flex align-items-center",
                    ),
                ],
                className="d-flex align-items-center",
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className=f"fas {health_icon} me-2",
                                        style={"color": health_color},
                                    ),
                                    html.Span(
                                        overall_health,
                                        style={
                                            "color": health_color,
                                            "fontWeight": "bold",
                                            "fontSize": "1.5rem",
                                        },
                                    ),
                                ],
                                className="d-flex align-items-center justify-content-center mb-1",
                            ),
                            html.P(
                                f"Worst gap: {min_gap:+.1f} weeks",
                                className="text-muted mb-3",
                                style={"fontSize": "0.9rem"},
                            ),
                        ],
                        className="text-center",
                    ),
                    alignment_table,
                ],
                className="pt-3 pb-0 mb-0",
            ),
            _create_card_footer(
                "Positive gap = sufficient budget • Negative gap = budget risk • Runway from actual burn rate",
                "fa-balance-scale",
            ),
        ],
        id=card_id,
        className="metric-card mb-3 h-100",
    )

    return card


def create_budget_timeline_card(
    baseline_data: Dict[str, Any],
    pert_forecast_weeks: Optional[float] = None,
    card_id: Optional[str] = None,
) -> dbc.Card:
    """
    Create Budget Timeline card showing all critical dates.

    Visual timeline with:
    - Budget start date
    - Current date (today)
    - PERT forecast completion (if available)
    - Baseline allocated end date
    - Budget runway end date

    Args:
        baseline_data: Dict from get_budget_baseline_vs_actual()
        pert_forecast_weeks: Optional PERT forecast weeks for completion date
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> card = create_budget_timeline_card(baseline_data, 15.0)
    """
    from datetime import datetime, timedelta

    # Extract dates
    start_date_str = baseline_data["baseline"]["start_date"]
    allocated_end_str = baseline_data["baseline"]["allocated_end_date"]
    runway_end_str = baseline_data["actual"]["runway_end_date"]

    # Parse dates
    try:
        allocated_end = datetime.fromisoformat(allocated_end_str)
        current_date = datetime.now()

        # Calculate forecast end date
        if pert_forecast_weeks:
            forecast_end = current_date + timedelta(weeks=pert_forecast_weeks)
            forecast_end_str = forecast_end.date().isoformat()
        else:
            forecast_end = None
            forecast_end_str = "N/A"

        # Parse runway end (handle special cases)
        if runway_end_str and runway_end_str not in [
            "N/A (no consumption)",
            "Over budget",
        ]:
            runway_end = datetime.fromisoformat(runway_end_str)
        else:
            runway_end = None

    except Exception as e:
        logger.error(f"Failed to parse timeline dates: {e}")
        # Return error card
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Budget Timeline", className="card-title"),
                    html.P(
                        "Unable to calculate timeline dates", className="text-muted"
                    ),
                ]
            ),
            id=card_id,
            className="metric-card mb-3 h-100",
        )

    # Calculate gaps
    elapsed_weeks = baseline_data["actual"]["elapsed_weeks"]
    allocated_weeks = baseline_data["baseline"]["time_allocated_weeks"]
    runway_vs_baseline_weeks = baseline_data["variance"]["runway_vs_baseline_weeks"]

    # Build timeline milestones
    milestones = []

    # Budget started
    milestones.append(
        html.Tr(
            [
                html.Td(html.I(className="fas fa-play text-secondary")),
                html.Td("Budget Started", className="fw-bold"),
                html.Td(start_date_str, className="text-end"),
                html.Td(
                    f"{allocated_weeks}w allocated", className="text-muted text-end"
                ),
            ]
        )
    )

    # Today
    milestones.append(
        html.Tr(
            [
                html.Td(html.I(className="fas fa-calendar-day text-primary")),
                html.Td("Today", className="fw-bold text-primary"),
                html.Td(current_date.date().isoformat(), className="text-end"),
                html.Td(
                    f"{elapsed_weeks:.1f}w elapsed", className="text-muted text-end"
                ),
            ]
        )
    )

    # Forecast completion (if available)
    if forecast_end:
        forecast_weeks_remaining = (forecast_end - current_date).days / 7.0
        milestones.append(
            html.Tr(
                [
                    html.Td(html.I(className="fas fa-chart-line text-info")),
                    html.Td("Forecast Complete", className="fw-bold"),
                    html.Td(forecast_end_str, className="text-end"),
                    html.Td(
                        f"{forecast_weeks_remaining:.1f}w remaining",
                        className="text-muted text-end",
                    ),
                ]
            )
        )

    # Baseline end
    baseline_weeks_remaining = (allocated_end - current_date).days / 7.0
    milestones.append(
        html.Tr(
            [
                html.Td(html.I(className="fas fa-flag-checkered text-warning")),
                html.Td("Baseline End", className="fw-bold"),
                html.Td(allocated_end_str, className="text-end"),
                html.Td(
                    f"{baseline_weeks_remaining:.1f}w remaining",
                    className="text-muted text-end",
                ),
            ]
        )
    )

    # Runway end
    if runway_end:
        runway_weeks_remaining = (runway_end - current_date).days / 7.0
        runway_color = (
            "text-success"
            if runway_weeks_remaining > baseline_weeks_remaining
            else "text-danger"
        )
        milestones.append(
            html.Tr(
                [
                    html.Td(html.I(className=f"fas fa-money-bill-wave {runway_color}")),
                    html.Td("Runway End", className=f"fw-bold {runway_color}"),
                    html.Td(runway_end_str, className="text-end"),
                    html.Td(
                        f"{runway_weeks_remaining:.1f}w remaining",
                        className="text-muted text-end",
                    ),
                ]
            )
        )
    else:
        # Special case: infinite runway or over budget
        status_text = runway_end_str
        milestones.append(
            html.Tr(
                [
                    html.Td(html.I(className="fas fa-money-bill-wave text-secondary")),
                    html.Td("Runway End", className="fw-bold"),
                    html.Td(status_text, className="text-end", colSpan=2),
                ]
            )
        )

    # Build gaps section
    gaps = []

    if forecast_end and runway_end:
        forecast_gap = (runway_end - forecast_end).days / 7.0
        gap_color = "success" if forecast_gap >= 0 else "danger"
        gap_icon = "check-circle" if forecast_gap >= 0 else "exclamation-triangle"
        gaps.append(
            html.Div(
                [
                    html.I(className=f"fas fa-{gap_icon} text-{gap_color} me-2"),
                    html.Span("Runway vs Forecast: ", className="text-muted"),
                    html.Strong(
                        f"{'+' if forecast_gap >= 0 else ''}{forecast_gap:.1f} weeks",
                        className=f"text-{gap_color}",
                    ),
                ],
                className="mb-2",
            )
        )

    if runway_end:
        baseline_gap = runway_vs_baseline_weeks
        gap_color = "success" if baseline_gap >= 0 else "danger"
        gap_icon = "check-circle" if baseline_gap >= 0 else "exclamation-triangle"
        gaps.append(
            html.Div(
                [
                    html.I(className=f"fas fa-{gap_icon} text-{gap_color} me-2"),
                    html.Span("Runway vs Baseline: ", className="text-muted"),
                    html.Strong(
                        f"{'+' if baseline_gap >= 0 else ''}{baseline_gap:.1f} weeks",
                        className=f"text-{gap_color}",
                    ),
                ],
                className="mb-2",
            )
        )

    # Build card
    card = dbc.Card(
        [
            dbc.CardHeader(
                html.Div(
                    [
                        html.I(className="fas fa-timeline me-2"),
                        html.Span("Budget Timeline", className="fw-bold"),
                    ]
                )
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.Table(
                                html.Tbody(milestones), className="table table-sm mb-3"
                            )
                        ]
                    ),
                    html.Hr(),
                    html.Div(
                        [html.H6("Timeline Gaps", className="text-muted mb-2"), *gaps]
                    )
                    if gaps
                    else html.Div(),
                ]
            ),
            _create_card_footer(
                "All dates based on actual burn rate • Gaps show buffer or risk",
                "fa-clock",
            ),
        ],
        id=card_id,
        className="metric-card mb-3 h-100",
    )

    return card
