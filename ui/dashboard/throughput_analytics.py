"""
Throughput Analytics Module for Comprehensive Dashboard

Provides team throughput analytics section with trend analysis:
- Items per week velocity calculation
- Points per week velocity calculation
- Average item size analysis
- Trend detection (comparing older vs recent performance)
- Visual sparklines and performance indicators

CRITICAL: Project Dashboard calculates velocity ad-hoc from project_statistics
to work WITHOUT changelog data. This is different from DORA/Flow metrics which
use metric snapshots (requires changelog).
"""

from __future__ import annotations

import logging
from typing import Any

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from ui.metric_cards import create_metric_card as create_professional_metric_card
from ui.style_constants import COLOR_PALETTE

from .utils import safe_divide

logger = logging.getLogger(__name__)


def create_throughput_analytics_section(
    statistics_df: pd.DataFrame,
    forecast_data: dict[str, Any],
    settings: dict[str, Any],
    data_points_count: int | None = None,
    additional_context: dict[str, Any] | None = None,
) -> html.Div:
    """Create throughput analytics section.

    CRITICAL: Project Dashboard calculates velocity ad-hoc from project_statistics
    to work WITHOUT changelog data. This is different from DORA/Flow metrics which
    use metric snapshots (requires changelog).

    Args:
        statistics_df: DataFrame with filtered statistics (fallback only)
        forecast_data: Dictionary with forecast data
        settings: Settings dictionary containing show_points flag
        data_points_count: Number of weeks for velocity calculation
        additional_context: Dict with profile_id, query_id, current_week_label

    Returns:
        Dash HTML Div containing throughput analytics section
    """
    show_points = settings.get("show_points", True)
    if statistics_df.empty:
        return html.Div()

    # Calculate velocity ad-hoc from project_statistics (works without changelog)
    # This ensures Project Dashboard functions independently of DORA/Flow metrics
    avg_items = None
    avg_points = None

    if (
        additional_context
        and additional_context.get("profile_id")
        and additional_context.get("query_id")
        and additional_context.get("current_week_label")
        and data_points_count
    ):
        from data.budget_calculator import _get_velocity, _get_velocity_points

        avg_items = _get_velocity(
            additional_context["profile_id"],
            additional_context["query_id"],
            additional_context["current_week_label"],
            data_points_count,
        )
        avg_points = _get_velocity_points(
            additional_context["profile_id"],
            additional_context["query_id"],
            additional_context["current_week_label"],
            data_points_count,
        )
        logger.info(
            f"[DASHBOARD] Using _get_velocity for Items per Week: {avg_items:.2f}, "
            f"Points per Week: {avg_points:.2f} (data_points_count={data_points_count})"
        )
    else:
        # Fallback to simple statistics mean
        avg_items = statistics_df["completed_items"].mean()
        avg_points = statistics_df["completed_points"].mean()
        logger.info(
            f"[DASHBOARD] Using statistics fallback for Items per Week: {avg_items:.2f}"
        )

    # Calculate trends by comparing older vs recent halves of filtered data
    items_trend = None
    points_trend = None
    weeks_available = len(statistics_df)

    if weeks_available >= 8:
        # Have enough data for full trend comparison (4 weeks vs 4 weeks)
        mid_point = weeks_available // 2
        older_half = statistics_df.iloc[:mid_point]
        recent_half = statistics_df.iloc[mid_point:]

        older_items = older_half["completed_items"].mean()
        recent_items = recent_half["completed_items"].mean()
        items_trend = {
            "direction": "up"
            if recent_items > older_items
            else "down"
            if recent_items < older_items
            else "stable",
            "percent": abs((recent_items - older_items) / older_items * 100)
            if older_items > 0
            else 0,
        }

        older_points = older_half["completed_points"].mean()
        recent_points = recent_half["completed_points"].mean()
        points_trend = {
            "direction": "up"
            if recent_points > older_points
            else "down"
            if recent_points < older_points
            else "stable",
            "percent": abs((recent_points - older_points) / older_points * 100)
            if older_points > 0
            else 0,
        }
    elif weeks_available >= 4:
        # Have baseline data but not enough for trend comparison
        # Show a message indicating we're building baseline
        items_trend = {
            "direction": "baseline",
            "percent": 0,
            "message": f"Building baseline ({weeks_available} of 8 weeks)",
        }
        points_trend = {
            "direction": "baseline",
            "percent": 0,
            "message": f"Building baseline ({weeks_available} of 8 weeks)",
        }
    else:
        # Not enough data yet
        items_trend = None
        points_trend = None

    # PROGRESSIVE BLENDING: Calculate blend_metadata for current week (Feature bd-a1vn)
    items_blend_metadata = None
    points_blend_metadata = None

    if (
        additional_context
        and additional_context.get("current_week_label")
        and not statistics_df.empty
        and len(statistics_df) >= 2
    ):
        from data.metrics.blending import get_blend_metadata
        from data.metrics_calculator import calculate_forecast

        # Check if last week in dataframe is the current week
        last_week_label = None
        if "week_label" in statistics_df.columns and len(statistics_df) > 0:
            last_week_label = statistics_df["week_label"].iloc[-1]
        current_week_label = additional_context["current_week_label"]

        if last_week_label == current_week_label:
            # Current week is in the data - apply blending
            items_values = list(statistics_df["completed_items"])

            if len(items_values) >= 2:
                current_week_actual = items_values[-1]
                prior_weeks = items_values[:-1]
                forecast_weeks = (
                    prior_weeks[-4:] if len(prior_weeks) >= 4 else prior_weeks
                )

                # Calculate items forecast
                if len(forecast_weeks) >= 2:
                    try:
                        items_forecast_data: dict[str, Any] | None = calculate_forecast(
                            forecast_weeks
                        )
                        forecast_value = (
                            items_forecast_data.get("forecast_value", 0)
                            if items_forecast_data
                            else 0
                        )

                        if forecast_value > 0:
                            items_blend_metadata = get_blend_metadata(
                                current_week_actual, forecast_value
                            )
                            logger.info(
                                "[Blending-Dashboard-Items] "
                                f"Actual: {current_week_actual:.1f}, "
                                f"Forecast: {forecast_value:.1f}, "
                                f"Blended: {items_blend_metadata['blended']:.1f}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to calculate items forecast for blending: {e}"
                        )

            # Calculate points blend metadata
            if show_points and "completed_points" in statistics_df.columns:
                points_values = list(statistics_df["completed_points"])

                if len(points_values) >= 2:
                    current_week_actual_pts = points_values[-1]
                    prior_weeks_pts = points_values[:-1]
                    forecast_weeks_pts = (
                        prior_weeks_pts[-4:]
                        if len(prior_weeks_pts) >= 4
                        else prior_weeks_pts
                    )

                    if len(forecast_weeks_pts) >= 2:
                        try:
                            forecast_data_pts = calculate_forecast(forecast_weeks_pts)
                            forecast_value_pts = (
                                forecast_data_pts.get("forecast_value", 0)
                                if forecast_data_pts
                                else 0
                            )

                            if forecast_value_pts > 0:
                                points_blend_metadata = get_blend_metadata(
                                    current_week_actual_pts, forecast_value_pts
                                )
                                logger.info(
                                    "[Blending-Dashboard-Points] "
                                    f"Actual: {current_week_actual_pts:.1f}, "
                                    f"Forecast: {forecast_value_pts:.1f}, "
                                    f"Blended: {points_blend_metadata['blended']:.1f}"
                                )
                        except Exception as e:
                            logger.warning(
                                f"Failed to calculate points forecast for blending: {e}"
                            )

    points_enabled = bool(show_points and avg_points and avg_points > 0)
    points_disabled_message = (
        "Points tracking is disabled. Enable Points Tracking in Parameters panel "
        "to view story points metrics."
    )
    points_no_data_message = (
        "No story points data available. Configure story points field in "
        "Settings or complete items with point estimates."
    )
    points_disabled_tooltip = (
        "Enable Points Tracking in Parameters panel and configure the points "
        "field in JIRA Configuration to view this metric. "
        "When disabled, forecasts use item counts instead."
    )
    points_period_no_data_tooltip = (
        "No story points data available for the selected time period."
    )
    points_per_week_tooltip = (
        "Average story points completed per week. Story points represent work "
        "complexity and effort. Higher values indicate faster delivery of "
        "larger work items. Progressive blending is applied to the current "
        "week to smooth Monday reliability drops."
    )
    avg_item_size_tooltip = (
        "Average story points per completed work item. Shows typical item "
        "complexity. Higher values mean larger items taking longer to complete. "
        "Use this to understand capacity: fewer large items or more small items "
        "per sprint. Breakdown shows Week 1 (oldest) to Week 4 (newest)."
    )
    items_per_week_tooltip = (
        "Average number of work items completed per week. Calculated using "
        "the corrected velocity method that counts actual weeks with data "
        "(not date range spans). Progressive blending is applied to the "
        "current week to smooth Monday reliability drops."
    )

    item_size_week_rows: list[html.Div] = []
    has_item_size_series = (
        not statistics_df.empty
        and "completed_points" in statistics_df.columns
        and "completed_items" in statistics_df.columns
    )
    has_item_size_trend = has_item_size_series and len(statistics_df) >= 2
    latest_item_size = 0.0
    first_item_size = 0.0
    if has_item_size_trend:
        latest_item_size = safe_divide(
            statistics_df["completed_points"].iloc[-1],
            statistics_df["completed_items"].iloc[-1],
        )
        first_item_size = safe_divide(
            statistics_df["completed_points"].iloc[0],
            statistics_df["completed_items"].iloc[0],
        )

    is_item_size_growing = has_item_size_trend and latest_item_size > first_item_size
    item_size_arrow = (
        "up" if is_item_size_growing else "down" if has_item_size_trend else "right"
    )
    item_size_arrow_color = (
        "#28a745"
        if is_item_size_growing
        else "#dc3545"
        if has_item_size_trend
        else "#6c757d"
    )
    item_size_trend_label = (
        "Growing"
        if is_item_size_growing
        else "Shrinking"
        if has_item_size_trend
        else "Stable"
    )
    item_size_icon_class = f"fas fa-arrow-{item_size_arrow} me-1"
    item_size_label_text = f"{item_size_trend_label} item size"
    item_size_arrow_style = {"color": item_size_arrow_color}

    if has_item_size_series:
        for i in range(min(4, len(statistics_df)) - 1, -1, -1):
            idx = -(i + 1)
            weekly_item_size = safe_divide(
                statistics_df["completed_points"].iloc[idx],
                statistics_df["completed_items"].iloc[idx],
            )
            item_size_week_rows.append(
                html.Div(
                    [
                        html.Small(f"Week {4 - i}: ", className="text-muted"),
                        html.Small(
                            f"{weekly_item_size:.1f} pts/item", className="fw-bold"
                        ),
                    ],
                    className="d-flex justify-content-between mb-1",
                    style={"fontSize": "0.8rem"},
                )
            )

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-shipping-fast me-2",
                        style={"color": "#28a745"},
                    ),
                    "Team Throughput Analytics",
                ],
                className="mb-3 mt-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_professional_metric_card(
                                {
                                    "metric_name": "items_per_week",
                                    "display_name": "Items per Week",
                                    "value": avg_items,
                                    "unit": "items/week",
                                    "subtitle": "Average delivery rate",
                                    "icon": "fa-tasks",
                                    "color": COLOR_PALETTE["items"],
                                    "performance_tier_color": "green"
                                    if avg_items > 10
                                    else "yellow"
                                    if avg_items > 5
                                    else "orange",
                                    "error_state": "success",
                                    "_n_weeks": data_points_count,
                                    "tooltip": items_per_week_tooltip,
                                    "weekly_values": list(
                                        statistics_df["completed_items"]
                                    )
                                    if not statistics_df.empty
                                    else [],
                                    "trend_direction": items_trend.get("direction")
                                    if items_trend
                                    else "stable",
                                    "trend_percent": items_trend.get("percent", 0)
                                    if items_trend
                                    else 0,
                                    # Progressive blending (bd-a1vn)
                                    "blend_metadata": items_blend_metadata,
                                }
                            )
                        ],
                        width=12,
                        md=6,
                        lg=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            create_professional_metric_card(
                                {
                                    "metric_name": "points_per_week",
                                    "display_name": "Points per Week",
                                    "value": avg_points if points_enabled else None,
                                    "unit": "points/week" if points_enabled else "",
                                    "subtitle": "Average story points"
                                    if points_enabled
                                    else "",
                                    "icon": "fa-chart-bar",
                                    "color": COLOR_PALETTE["points"]
                                    if points_enabled
                                    else "#6c757d",
                                    "performance_tier_color": "green"
                                    if show_points and avg_points and avg_points > 20
                                    else "yellow"
                                    if show_points and avg_points and avg_points > 10
                                    else "orange",
                                    "error_state": (
                                        "success"
                                        if points_enabled
                                        else "points_tracking_disabled"
                                        if not show_points
                                        else "no_data"
                                    ),
                                    "error_message": (
                                        points_disabled_message
                                        if not show_points
                                        else points_no_data_message
                                    ),
                                    "_n_weeks": data_points_count,
                                    "tooltip": (
                                        points_per_week_tooltip
                                        if points_enabled
                                        else points_disabled_tooltip
                                        if not show_points
                                        else points_period_no_data_tooltip
                                    ),
                                    "weekly_values": list(
                                        statistics_df["completed_points"]
                                    )
                                    if show_points
                                    and avg_points
                                    and avg_points > 0
                                    and not statistics_df.empty
                                    else [],
                                    "trend_direction": points_trend.get("direction")
                                    if points_trend
                                    and show_points
                                    and avg_points
                                    and avg_points > 0
                                    else "stable",
                                    "trend_percent": points_trend.get("percent", 0)
                                    if points_trend
                                    and show_points
                                    and avg_points
                                    and avg_points > 0
                                    else 0,
                                    # Progressive blending (bd-a1vn)
                                    "blend_metadata": points_blend_metadata,
                                }
                            )
                        ],
                        width=12,
                        md=6,
                        lg=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            create_professional_metric_card(
                                {
                                    "metric_name": "avg_item_size",
                                    "alternative_name": "Average Item Size",
                                    "value": safe_divide(avg_points, avg_items)
                                    if points_enabled
                                    else None,
                                    "unit": "points/item" if points_enabled else "",
                                    "subtitle": "Points per item"
                                    if points_enabled
                                    else "",
                                    "icon": "fa-weight-hanging",
                                    "color": "#17a2b8" if points_enabled else "#6c757d",
                                    "performance_tier_color": "green",
                                    "error_state": (
                                        "success"
                                        if points_enabled
                                        else "points_tracking_disabled"
                                        if not show_points
                                        else "no_data"
                                    ),
                                    "error_message": (
                                        points_disabled_message
                                        if not show_points
                                        else points_no_data_message
                                    ),
                                    "_n_weeks": data_points_count,
                                    "tooltip": (
                                        avg_item_size_tooltip
                                        if points_enabled
                                        else points_disabled_tooltip
                                        if not show_points
                                        else points_period_no_data_tooltip
                                    ),
                                },
                                text_details=[
                                    html.Div(
                                        [
                                            html.Div(
                                                className="text-muted mb-2",
                                                children=[
                                                    html.I(
                                                        className="fas fa-history me-1",
                                                        style={"fontSize": "0.8rem"},
                                                    ),
                                                    html.Span(
                                                        "Past 4 Weeks"
                                                        " (oldest → newest)",
                                                        className="fw-bold",
                                                        style={"fontSize": "0.85rem"},
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                item_size_week_rows,
                                                className="small",
                                                style={
                                                    "backgroundColor": "#f8f9fa",
                                                    "padding": "8px",
                                                    "borderRadius": "4px",
                                                    "fontSize": "0.8rem",
                                                },
                                            ),
                                            html.Div(
                                                [
                                                    html.I(
                                                        className=item_size_icon_class,
                                                        style=item_size_arrow_style,
                                                    ),
                                                    html.Small(
                                                        item_size_label_text,
                                                        className=(
                                                            "text-muted fst-italic"
                                                        ),
                                                    ),
                                                ],
                                                className="mt-2",
                                                style={"fontSize": "0.75rem"},
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                ]
                                if (
                                    show_points
                                    and avg_points
                                    and avg_points > 0
                                    and not statistics_df.empty
                                    and "completed_points" in statistics_df.columns
                                    and "completed_items" in statistics_df.columns
                                )
                                else None,
                            )
                        ],
                        width=12,
                        md=6,
                        lg=4,
                        className="mb-3",
                    ),
                ]
            ),
        ],
        className="mb-4",
    )
