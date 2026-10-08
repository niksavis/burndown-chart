import logging
import math
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ui.metric_cards import create_metric_card

logger = logging.getLogger(__name__)


def create_budget_utilization_card(
    consumed_pct: float,
    consumed_eur: float,
    budget_total: float,
    currency_symbol: str = "€",
    data_points_count: int = 12,
    card_id: str | None = None,
    baseline_data: dict[str, Any] | None = None,
) -> dbc.Card:

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

    text_details = None
    if baseline_data:
        elapsed_weeks = baseline_data["actual"]["elapsed_weeks"]
        allocated_weeks = baseline_data["baseline"]["time_allocated_weeks"]
        elapsed_pct = baseline_data["actual"]["elapsed_pct"]
        variance_pct = baseline_data["variance"]["utilization_vs_pace_pct"]
        pace_summary_text = (
            f"Budget pace is {abs(variance_pct):.1f}% "
            f"{'ahead' if variance_pct > 0 else 'behind'} time"
            if abs(variance_pct) >= 2
            else "Budget and time are aligned"
        )

        if variance_pct < -10:
            pace_status = "Under-spending"
            pace_color = "#198754"
            pace_icon = "fa-check-circle"
        elif variance_pct < -2:
            pace_status = "Efficient"
            pace_color = "#20c997"
            pace_icon = "fa-thumbs-up"
        elif variance_pct <= 2:
            pace_status = "On Pace"
            pace_color = "#6c757d"
            pace_icon = "fa-equals"
        elif variance_pct <= 10:
            pace_status = "Warning"
            pace_color = "#ffc107"
            pace_icon = "fa-exclamation-triangle"
        else:
            pace_status = "Over-spending"
            pace_color = "#dc3545"
            pace_icon = "fa-exclamation-circle"

        text_details = [
            html.Div(
                [
                    html.Small(
                        "TIME vs BUDGET UTILIZATION",
                        className="text-muted fw-bold d-block mb-2 text-center",
                        style={"fontSize": "0.75rem"},
                    ),
                    html.Div(
                        [
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
                                className=(
                                    "d-flex align-items-center "
                                    "justify-content-center mb-1"
                                ),
                            ),
                            html.Small(
                                pace_summary_text,
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
        "tooltip": (
            "Shows budget consumption rate vs time elapsed. "
            "Compares actual spending pace against planned pace. "
            "Healthy (<70%): Spending slower than time passing. "
            "Warning (70-95%): Pace matches time. "
            "Critical (>95%): Burning budget faster than expected."
        ),
    }

    return create_metric_card(
        metric_data, card_id, show_details_button=False, text_details=text_details
    )


def create_weekly_burn_rate_card(
    burn_rate: float,
    weekly_values: list[float],
    weekly_labels: list[str],
    trend_pct: float,
    currency_symbol: str = "€",
    data_points_count: int = 4,
    card_id: str | None = None,
    baseline_data: dict[str, Any] | None = None,
) -> dbc.Card:

    if abs(trend_pct) < 2:
        trend_arrow = "→"
        trend_color = "text-secondary"
    elif trend_pct > 0:
        trend_arrow = "↗"
        trend_color = "text-danger"
    else:
        trend_arrow = "↘"
        trend_color = "text-success"

    details = {
        "trend": f"{trend_arrow} {abs(trend_pct):.1f}%",
        "trend_color": trend_color,
    }

    text_details = None
    if baseline_data:
        budgeted_rate = baseline_data["baseline"]["team_cost_per_week_eur"]
        variance_eur = baseline_data["variance"]["burn_rate_variance_eur"]
        variance_pct = baseline_data["variance"]["burn_rate_variance_pct"]
        runway_weeks = baseline_data["actual"]["runway_weeks"]

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

        projected_impact = (
            variance_eur * runway_weeks
            if not math.isinf(runway_weeks) and runway_weeks > 0
            else 0
        )

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
                                className=(
                                    "d-flex justify-content-between "
                                    "mb-1 position-relative"
                                ),
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "width": "100%",
                                            "height": "6px",
                                            "background": (
                                                "linear-gradient(to right, "
                                                "#198754 0%, #6c757d 50%, "
                                                "#dc3545 100%)"
                                            ),
                                            "borderRadius": "3px",
                                            "opacity": "0.3",
                                        },
                                    ),
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
                        className=(
                            "d-flex align-items-center justify-content-center mb-2"
                        ),
                    ),
                    html.Div(
                        [
                            html.Span(
                                (
                                    "Projected Impact: "
                                    f"{currency_symbol}{abs(projected_impact):,.0f}"
                                ),
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
        "tooltip": (
            "Average weekly spending rate calculated from actual costs "
            "divided by elapsed time. Compares actual burn rate against "
            "budgeted weekly cost. Green: Under budget. "
            "Yellow: On target (±10%). Red: Over budget. "
            "Includes projected total savings/overrun."
        ),
    }

    return create_metric_card(
        metric_data, card_id, show_details_button=False, text_details=text_details
    )


def create_budget_runway_card(
    runway_weeks: float,
    pert_forecast_weeks: float | None = None,
    currency_symbol: str = "€",
    data_points_count: int = 12,
    card_id: str | None = None,
    baseline_data: dict[str, Any] | None = None,
) -> dbc.Card:

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
                "Budget runway is calculated from ACTUAL completed items, "
                "not just team cost."
            },
        }
        return create_metric_card(metric_data, card_id, show_details_button=False)

    if runway_weeks < 0:
        metric_data = {
            "metric_name": "budget_runway",
            "value": abs(runway_weeks),
            "unit": "weeks over budget",
            "performance_tier": "Over Budget",
            "performance_tier_color": "red",
            "error_state": "success",
            "total_issue_count": 0,
            "_n_weeks": data_points_count,
            "details": {
                "status": (
                    "Budget exceeded. Immediate action required: "
                    "Review scope, increase budget, or reduce team costs."
                )
            },
        }
        return create_metric_card(metric_data, card_id, show_details_button=False)

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

    text_details = None
    if baseline_data:
        extension_weeks = baseline_data["variance"]["runway_vs_baseline_weeks"]

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

        forecast_gap = runway_weeks - pert_forecast_weeks if pert_forecast_weeks else 0
        allocated_weeks_baseline = baseline_data["baseline"]["time_allocated_weeks"]

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
                                className=(
                                    "d-flex justify-content-between "
                                    "mb-1 position-relative"
                                ),
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        style={
                                            "position": "absolute",
                                            "width": "100%",
                                            "height": "6px",
                                            "background": (
                                                "linear-gradient(to right, "
                                                "#dc3545 0%, #6c757d 50%, "
                                                "#198754 100%)"
                                            ),
                                            "borderRadius": "3px",
                                            "opacity": "0.3",
                                        },
                                    ),
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
                        className=(
                            "d-flex align-items-center justify-content-center mb-2"
                        ),
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
        "tooltip": (
            "How long the budget will last at current burn rate. "
            "Calculated as remaining budget divided by weekly burn rate. "
            "Green: Runway exceeds allocation. Yellow: Close to baseline. "
            "Red: Running out faster than planned. "
            "Shows extension/shortfall vs allocated time and forecast."
        ),
    }

    return create_metric_card(
        metric_data, card_id, show_details_button=False, text_details=text_details
    )
