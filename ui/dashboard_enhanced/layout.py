"""
Dashboard Enhanced - Main Assembly

Orchestrates the enhanced dashboard by computing context and assembling
sections from focused submodules.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from ui.dashboard_enhanced.capacity_card import _create_capacity_card
from ui.dashboard_enhanced.metric_cards import (
    _create_forecast_card,
    _create_velocity_card,
)
from ui.dashboard_enhanced.overview_bar import _create_overview_bar
from ui.dashboard_enhanced.stats import (
    _assess_project_health,
    _calculate_confidence_intervals,
    _calculate_deadline_probability,
    _calculate_velocity_statistics,
)
from ui.style_constants import COLOR_PALETTE


def _prepare_dashboard_context(
    statistics_df: pd.DataFrame,
    pert_time_items: float,
    pert_time_points: float | None,
    days_to_deadline: float,
    total_items: float,
    total_points: float,
    show_points: bool,
) -> dict:
    """Compute all derived metrics needed to render the dashboard."""
    # Use last statistics date as forecast starting point (aligns with report)
    current_date = (
        statistics_df["date"].iloc[-1] if not statistics_df.empty else datetime.now()
    )

    completed_items = (
        statistics_df["completed_items"].sum() if not statistics_df.empty else 0
    )
    completed_points = (
        statistics_df["completed_points"].sum()
        if not statistics_df.empty and show_points
        else 0
    )
    remaining_items = max(0, total_items - completed_items)
    remaining_points = max(0, total_points - completed_points) if show_points else 0
    actual_total_items = completed_items + remaining_items
    progress_pct_text = (
        f"{completed_items / actual_total_items:.0%}"
        if actual_total_items > 0
        else "0%"
    )

    items_stats = _calculate_velocity_statistics(statistics_df, "items")
    empty_stats: dict = {
        "mean": 0,
        "median": 0,
        "std_dev": 0,
        "cv": 0,
        "recent_avg": 0,
        "recent_change": 0,
        "sparkline_data": [],
    }
    points_stats = (
        _calculate_velocity_statistics(statistics_df, "points")
        if show_points
        else empty_stats
    )

    # Determine if we have actual points data (not just tracking enabled)
    has_points_data = (
        show_points
        and points_stats["mean"] > 0
        and pert_time_points is not None
        and pert_time_points > 0
    )

    items_ci = _calculate_confidence_intervals(
        pert_time_items, items_stats["mean"], items_stats["std_dev"], remaining_items
    )
    if has_points_data and pert_time_points is not None:
        points_ci = _calculate_confidence_intervals(
            pert_time_points,
            points_stats["mean"],
            points_stats["std_dev"],
            remaining_points,
        )
    else:
        points_ci: dict = {"ci_50": 0, "ci_80": 0, "ci_95": 0}

    items_probability = _calculate_deadline_probability(
        days_to_deadline, pert_time_items, items_stats["std_dev"], items_stats["mean"]
    )
    if has_points_data and pert_time_points is not None:
        points_probability = _calculate_deadline_probability(
            days_to_deadline,
            pert_time_points,
            points_stats["std_dev"],
            points_stats["mean"],
        )
    else:
        points_probability = 0.0

    items_pert_date = (current_date + timedelta(days=pert_time_items)).strftime(
        "%b %d, %Y"
    )
    if has_points_data and pert_time_points is not None:
        points_pert_date = (current_date + timedelta(days=pert_time_points)).strftime(
            "%b %d, %Y"
        )
    else:
        points_pert_date = "N/A"

    items_status = "on_track" if pert_time_items <= days_to_deadline else "at_risk"
    if has_points_data and pert_time_points is not None:
        points_status = (
            "on_track" if pert_time_points <= days_to_deadline else "at_risk"
        )
    else:
        points_status = "no_data"

    weeks_to_deadline = days_to_deadline / 7 if days_to_deadline > 0 else 1
    required_velocity_items = (
        remaining_items / weeks_to_deadline if weeks_to_deadline > 0 else 0
    )
    capacity_gap_percent = (
        (items_stats["mean"] - required_velocity_items) / required_velocity_items * 100
        if required_velocity_items > 0
        else 0
    )

    health = _assess_project_health(
        items_stats["cv"],
        days_to_deadline,
        pert_time_items,
        items_stats["recent_change"],
        capacity_gap_percent,
    )

    return {
        "completed_items": completed_items,
        "actual_total_items": actual_total_items,
        "progress_pct_text": progress_pct_text,
        "remaining_items": remaining_items,
        "items_stats": items_stats,
        "points_stats": points_stats,
        "has_points_data": has_points_data,
        "items_ci": items_ci,
        "points_ci": points_ci,
        "items_probability": items_probability,
        "points_probability": points_probability,
        "items_pert_date": items_pert_date,
        "points_pert_date": points_pert_date,
        "items_status": items_status,
        "points_status": points_status,
        "required_velocity_items": required_velocity_items,
        "health": health,
    }


def _build_cards_row(ctx: dict) -> dbc.Row:
    """Build the four forecast/velocity metric cards row."""
    return dbc.Row(
        [
            dbc.Col(
                _create_forecast_card(
                    title="Items Forecast",
                    icon="fas fa-calendar-check",
                    icon_color=COLOR_PALETTE["items"],
                    pert_date=ctx["items_pert_date"],
                    confidence_intervals=ctx["items_ci"],
                    status=ctx["items_status"],
                    probability=ctx["items_probability"],
                    show_data=True,
                    card_id="dashboard-items-forecast",
                ),
                xs=12,
                md=6,
                lg=3,
                className="mb-2",
            ),
            dbc.Col(
                _create_forecast_card(
                    title="Points Forecast",
                    icon="fas fa-chart-bar",
                    icon_color=COLOR_PALETTE["points"],
                    pert_date=ctx["points_pert_date"],
                    confidence_intervals=ctx["points_ci"],
                    status=ctx["points_status"],
                    probability=ctx["points_probability"],
                    show_data=ctx["has_points_data"],
                    card_id="dashboard-points-forecast",
                ),
                xs=12,
                md=6,
                lg=3,
                className="mb-2",
            ),
            dbc.Col(
                _create_velocity_card(
                    title="Items Velocity",
                    icon="fas fa-tachometer-alt",
                    icon_color="#6610f2",
                    velocity_stats=ctx["items_stats"],
                    show_data=True,
                    card_id="dashboard-items-velocity",
                ),
                xs=12,
                md=6,
                lg=3,
                className="mb-2",
            ),
            dbc.Col(
                _create_velocity_card(
                    title="Points Velocity",
                    icon="fas fa-tachometer-alt",
                    icon_color=COLOR_PALETTE["points"],
                    velocity_stats=ctx["points_stats"],
                    show_data=ctx["has_points_data"],
                    card_id="dashboard-points-velocity",
                ),
                xs=12,
                md=6,
                lg=3,
                className="mb-2",
            ),
        ],
        className="g-2 mb-2",
    )


def _build_team_performance_card(ctx: dict) -> dbc.Card:
    """Build the team performance card showing recent vs historical velocity."""
    items_stats = ctx["items_stats"]
    points_stats = ctx["points_stats"]
    has_points_data = ctx["has_points_data"]

    items_trend_color = "#28a745" if items_stats["recent_change"] >= 0 else "#dc3545"
    points_trend_color = "#28a745" if points_stats["recent_change"] >= 0 else "#dc3545"

    items_section = html.Div(
        [
            html.Div(
                "Items/Week (Recent)",
                className="text-muted",
                style={"fontSize": "0.875rem"},
            ),
            html.Div(
                f"{items_stats['recent_avg']:.1f}",
                className="fw-bold mb-1",
                style={
                    "fontSize": "1.5rem",
                    "color": COLOR_PALETTE["items"],
                    "lineHeight": "1",
                },
            ),
            html.Div(
                [
                    html.Span(
                        "Hist: ", className="text-muted", style={"fontSize": "0.875rem"}
                    ),
                    html.Span(
                        f"{items_stats['mean']:.1f}",
                        className="fw-semibold me-2",
                        style={"fontSize": "0.875rem"},
                    ),
                    html.Span("•", className="text-muted mx-1"),
                    html.Span(
                        "Trend: ",
                        className="text-muted",
                        style={"fontSize": "0.875rem"},
                    ),
                    html.Span(
                        f"{items_stats['recent_change']:+.0f}%",
                        className="fw-bold",
                        style={"fontSize": "0.95rem", "color": items_trend_color},
                    ),
                ],
                className="mb-1 pb-2 border-bottom" if has_points_data else "mb-0",
            ),
        ],
        className="mb-1" if has_points_data else "",
    )

    points_section = (
        html.Div(
            [
                html.Div(
                    "Points/Week (Recent)",
                    className="text-muted",
                    style={"fontSize": "0.875rem"},
                ),
                html.Div(
                    f"{points_stats['recent_avg']:.1f}",
                    className="fw-bold mb-1",
                    style={
                        "fontSize": "1.5rem",
                        "color": COLOR_PALETTE["points"],
                        "lineHeight": "1",
                    },
                ),
                html.Div(
                    [
                        html.Span(
                            "Hist: ",
                            className="text-muted",
                            style={"fontSize": "0.875rem"},
                        ),
                        html.Span(
                            f"{points_stats['mean']:.1f}",
                            className="fw-semibold me-2",
                            style={"fontSize": "0.875rem"},
                        ),
                        html.Span("•", className="text-muted mx-1"),
                        html.Span(
                            "Trend: ",
                            className="text-muted",
                            style={"fontSize": "0.875rem"},
                        ),
                        html.Span(
                            f"{points_stats['recent_change']:+.0f}%",
                            className="fw-bold",
                            style={
                                "fontSize": "0.95rem",
                                "color": points_trend_color,
                            },
                        ),
                    ],
                ),
            ],
        )
        if has_points_data
        else html.Div()
    )

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.I(
                            className="fas fa-chart-line me-2",
                            style={"color": "#20c997", "fontSize": "1rem"},
                        ),
                        html.Span(
                            "Team Performance",
                            className="fw-semibold",
                            style={"fontSize": "1rem"},
                        ),
                    ],
                    className="d-flex align-items-center mb-1",
                ),
                items_section,
                points_section,
            ],
            className="p-2",
        ),
        className="shadow-sm h-100",
        style={"border": "none", "borderRadius": "12px", "minHeight": "240px"},
    )


def _build_capacity_row(ctx: dict, days_to_deadline: float) -> dbc.Row:
    """Build the capacity analysis and team performance row."""
    return dbc.Row(
        [
            dbc.Col(
                _create_capacity_card(
                    required_velocity=ctx["required_velocity_items"],
                    actual_velocity=ctx["items_stats"]["mean"],
                    remaining_items=ctx["remaining_items"],
                    days_to_deadline=days_to_deadline,
                    show_data=True,
                ),
                xs=12,
                lg=6,
                className="mb-2",
            ),
            dbc.Col(
                _build_team_performance_card(ctx),
                xs=12,
                lg=6,
                className="mb-3",
            ),
        ],
        className="g-3",
    )


def create_enhanced_dashboard(
    statistics_df: pd.DataFrame,
    pert_time_items: float,
    pert_time_points: float | None,
    avg_weekly_items: float,
    avg_weekly_points: float,
    med_weekly_items: float,
    med_weekly_points: float,
    days_to_deadline: float,
    total_items: float,
    total_points: float,
    deadline_str: str,
    show_points: bool = True,
) -> html.Div:
    """
    Create concise, actionable enhanced dashboard.

    Sections:
    - Overview bar: health, progress, deadline, success probability
    - Metric cards: items/points forecast + velocity (4 cards)
    - Capacity row: capacity gap + team performance
    """
    ctx = _prepare_dashboard_context(
        statistics_df=statistics_df,
        pert_time_items=pert_time_items,
        pert_time_points=pert_time_points,
        days_to_deadline=days_to_deadline,
        total_items=total_items,
        total_points=total_points,
        show_points=show_points,
    )

    overview_bar = _create_overview_bar(
        health=ctx["health"],
        completed_items=ctx["completed_items"],
        actual_total_items=ctx["actual_total_items"],
        progress_pct_text=ctx["progress_pct_text"],
        days_to_deadline=days_to_deadline,
        deadline_str=deadline_str,
        items_probability=ctx["items_probability"],
    )

    return html.Div(
        [
            overview_bar,
            _build_cards_row(ctx),
            _build_capacity_row(ctx, days_to_deadline),
            html.Div(
                html.Small(
                    [
                        html.I(className="fas fa-info-circle me-1 text-info"),
                        "PERT forecasts use 3-point estimation with "
                        "confidence intervals.",
                    ],
                    className="text-muted",
                    style={"fontSize": "0.75rem"},
                ),
                className="mt-2 pt-2 border-top text-center",
            ),
        ],
        className="dashboard-enhanced",
    )
