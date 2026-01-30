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
from typing import Any, Optional

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from .utils import safe_divide
from ui.metric_cards import create_metric_card as create_professional_metric_card
from ui.style_constants import COLOR_PALETTE


logger = logging.getLogger(__name__)


def create_throughput_analytics_section(
    statistics_df: pd.DataFrame,
    forecast_data: dict[str, Any],
    settings: dict[str, Any],
    data_points_count: Optional[int] = None,
    additional_context: Optional[dict[str, Any]] = None,
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
                                    "tooltip": "Average number of work items completed per week. Calculated using the corrected velocity method that counts actual weeks with data (not date range spans).",
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
                                    "value": avg_points
                                    if (show_points and avg_points and avg_points > 0)
                                    else None,
                                    "unit": "points/week"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "",
                                    "subtitle": "Average story points"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "",
                                    "icon": "fa-chart-bar",
                                    "color": COLOR_PALETTE["points"]
                                    if (show_points and avg_points and avg_points > 0)
                                    else "#6c757d",
                                    "performance_tier_color": "green"
                                    if show_points and avg_points and avg_points > 20
                                    else "yellow"
                                    if show_points and avg_points and avg_points > 10
                                    else "orange",
                                    "error_state": "success"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "points_tracking_disabled"
                                    if not show_points
                                    else "no_data",
                                    "error_message": "Points tracking is disabled. Enable Points Tracking in Parameters panel to view story points metrics."
                                    if not show_points
                                    else "No story points data available. Configure story points field in Settings or complete items with point estimates.",
                                    "_n_weeks": data_points_count,
                                    "tooltip": "Average story points completed per week. Story points represent work complexity and effort. Higher values indicate faster delivery of larger work items."
                                    if (show_points and avg_points and avg_points > 0)
                                    else "Enable Points Tracking in Parameters panel and configure the points field in JIRA Configuration to view this metric. When disabled, forecasts use item counts instead."
                                    if not show_points
                                    else "No story points data available for the selected time period.",
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
                                    if (show_points and avg_points and avg_points > 0)
                                    else None,
                                    "unit": "points/item"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "",
                                    "subtitle": "Points per item"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "",
                                    "icon": "fa-weight-hanging",
                                    "color": "#17a2b8"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "#6c757d",
                                    "performance_tier_color": "green",
                                    "error_state": "success"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "points_tracking_disabled"
                                    if not show_points
                                    else "no_data",
                                    "error_message": "Points tracking is disabled. Enable Points Tracking in Parameters panel to view story points metrics."
                                    if not show_points
                                    else "No story points data available. Configure story points field in Settings or complete items with point estimates.",
                                    "_n_weeks": data_points_count,
                                    "tooltip": "Average story points per completed work item. Shows typical item complexity. Higher values mean larger items taking longer to complete. Use this to understand capacity: fewer large items or more small items per sprint."
                                    if (show_points and avg_points and avg_points > 0)
                                    else "Enable Points Tracking in Parameters panel and configure the points field in JIRA Configuration to view this metric. When disabled, forecasts use item counts instead."
                                    if not show_points
                                    else "No story points data available for the selected time period.",
                                    "weekly_values": [],
                                    "trend_direction": "stable",
                                    "trend_percent": 0,
                                }
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
