import logging
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ui.metric_cards import create_metric_card

logger = logging.getLogger(__name__)


def create_cost_per_item_card(
    cost_per_item: float,
    pert_weighted_avg: float | None = None,
    currency_symbol: str = "€",
    data_points_count: int = 12,
    card_id: str | None = None,
    baseline_data: dict[str, Any] | None = None,
) -> dbc.Card:

    details = {"calculation": "Auto-calculated: Team Cost / Velocity"}
    if pert_weighted_avg:
        details["pert_avg"] = f"{currency_symbol}{pert_weighted_avg:.2f}"

    text_details = None
    if baseline_data:
        variance_eur = baseline_data["variance"]["cost_per_item_variance_eur"]
        variance_pct = baseline_data["variance"]["cost_per_item_variance_pct"]
        velocity = baseline_data["actual"]["velocity_items"]
        baseline_velocity = baseline_data["baseline"]["assumed_baseline_velocity"]
        budgeted_rate = baseline_data["baseline"]["team_cost_per_week_eur"]

        budgeted_cost_per_item = budgeted_rate / baseline_velocity

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
                                (
                                    f"Budgeted: {currency_symbol}"
                                    f"{budgeted_cost_per_item:.0f}/item @ "
                                    f"{baseline_velocity:.2f} items/wk (baseline)"
                                ),
                                className="text-muted d-block mb-1 text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Span(
                                (
                                    "Actual: "
                                    f"{currency_symbol}{cost_per_item:.0f}/item @ "
                                    f"{velocity:.2f} items/wk"
                                ),
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
        "tooltip": (
            "Team cost divided by delivery velocity (items/week). "
            "Baseline velocity is captured from Recent Completions "
            "(Last 4 Weeks) when budget is configured and used as "
            "fixed reference. Actual velocity updates dynamically. "
            "Shows efficiency: lower cost per item = better. "
            "Variance shows if team is more/less efficient than baseline."
        ),
    }

    return create_metric_card(
        metric_data, card_id, show_details_button=False, text_details=text_details
    )


def create_cost_per_point_card(
    cost_per_point: float,
    pert_weighted_avg: float | None = None,
    points_available: bool = True,
    currency_symbol: str = "€",
    data_points_count: int = 12,
    card_id: str | None = None,
    baseline_data: dict[str, Any] | None = None,
) -> dbc.Card:

    if not points_available:
        metric_data = {
            "metric_name": "cost_per_point",
            "alternative_name": "Cost Per Point",
            "value": None,
            "unit": "",
            "performance_tier": "Not Configured",
            "performance_tier_color": "secondary",
            "error_state": "points_tracking_disabled",
            "error_message": (
                "Points tracking is disabled. Enable Points Tracking in "
                "Parameters panel to view story points metrics."
            ),
            "total_issue_count": 0,
            "_n_weeks": data_points_count,
            "details": {
                "status": "Story points field not configured. "
                "Set up points field in Settings → Field Mapping to enable."
            },
        }
        return create_metric_card(metric_data, card_id, show_details_button=False)

    if cost_per_point is None or cost_per_point == 0:
        metric_data = {
            "metric_name": "cost_per_point",
            "alternative_name": "Cost Per Point",
            "value": None,
            "unit": "",
            "performance_tier": "No Data",
            "performance_tier_color": "secondary",
            "error_state": "no_data",
            "error_message": (
                "No story points data available. Configure story points "
                "field in Settings or complete items with point estimates."
            ),
            "total_issue_count": 0,
            "_n_weeks": data_points_count,
            "details": {"status": "No story points data available."},
        }
        return create_metric_card(metric_data, card_id, show_details_button=False)

    details = {"calculation": "Auto-calculated: Team Cost / Velocity (points)"}
    if pert_weighted_avg:
        details["pert_avg"] = f"{currency_symbol}{pert_weighted_avg:.2f}"

    text_details = None
    if baseline_data:
        velocity_points = baseline_data["actual"]["velocity_points"]
        budgeted_rate = baseline_data["baseline"]["team_cost_per_week_eur"]
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
                                (
                                    f"Budgeted: {currency_symbol}"
                                    f"{budgeted_cost_per_point:.0f}/pt @ "
                                    f"{baseline_velocity_points:.2f} points/wk "
                                    "(baseline)"
                                ),
                                className="text-muted d-block mb-1 text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Span(
                                (
                                    "Actual: "
                                    f"{currency_symbol}{cost_per_point:.0f}/pt @ "
                                    f"{velocity_points:.2f} points/wk"
                                ),
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
        "tooltip": (
            "Team cost divided by story point velocity (points/week). "
            "Baseline velocity is captured from Recent Completions "
            "(Last 4 Weeks) when budget is configured and used as fixed "
            "reference. Actual velocity updates dynamically. "
            "Shows efficiency: lower cost per point = better. "
            "Variance shows if team is more/less efficient than baseline."
        ),
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
    card_id: str | None = None,
    data_points_count: int = 12,
) -> dbc.Card:

    remaining_eur = budget_total - consumed_eur

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

    text_details = [
        html.Div(
            [
                html.Small(
                    "BUDGET BREAKDOWN",
                    className="text-muted fw-bold d-block mb-3 text-center",
                    style={"fontSize": "0.75rem"},
                ),
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
                            className=(
                                "d-flex justify-content-between align-items-center mb-1"
                            ),
                        ),
                        dbc.Progress(
                            value=min(consumed_pct, 100),
                            color=progress_color,
                            style={"height": "8px"},
                            className="mb-3",
                        ),
                    ],
                ),
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
                            (
                                f" ({currency_symbol}{confidence_low:,.0f}-"
                                f"{currency_symbol}{confidence_high:,.0f})"
                            ),
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
        "tooltip": (
            "Total budget allocation with consumption status. Shows consumed "
            "vs remaining budget with PERT-based forecast. Health zones "
            "indicate spending pace relative to timeline."
        ),
    }

    return create_metric_card(
        metric_data, card_id, show_details_button=False, text_details=text_details
    )
