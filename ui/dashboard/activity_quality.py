"""Activity and Quality/Scope Section Components.

This module provides dashboard sections for:
- Recent Activity: Tracking completed items and story points over a fixed 4-week window
- Quality & Scope: Monitoring scope management, backlog growth, and delivery consistency

These sections provide key insights into team throughput, scope creep, and delivery
predictability for effective project management and forecasting.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd
from dash import html
import dash_bootstrap_components as dbc

from ui.metric_cards import create_metric_card as create_professional_metric_card
from ui.styles import create_metric_card_header
from ui.tooltip_utils import create_info_tooltip
from ui.style_constants import COLOR_PALETTE


logger = logging.getLogger(__name__)


def safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers, returning default if denominator is zero."""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def create_recent_activity_section(
    statistics_df: pd.DataFrame,
    show_points: bool = True,
    additional_context: Optional[dict[str, Any]] = None,
) -> html.Div:
    """Create compact recent performance section showing completed items clearly.

    Note: This section ALWAYS shows the last 4 weeks of data, regardless of
    the data_points_count slider. This provides a consistent "current status" view.
    Other dashboard sections respect the data_points_count filter.

    Args:
        statistics_df: DataFrame with statistics data
        show_points: Whether to show points-related metrics (default: True)

    Returns:
        Dash HTML Div component with recent completions metrics
    """
    if statistics_df.empty:
        return html.Div()

    # ALWAYS use last 4 weeks for "Recent Completions" - fixed window
    recent_window = min(4, len(statistics_df))  # 4 weeks or less if data is limited
    recent_data = statistics_df.tail(recent_window)

    if recent_data.empty:
        return html.Div()

    # Calculate metrics for items
    total_items_completed = recent_data["completed_items"].sum()
    avg_items_weekly = recent_data["completed_items"].mean()
    items_sparkline_values = recent_data["completed_items"].tolist()

    # Calculate metrics for points
    has_points_data = "completed_points" in recent_data.columns
    total_points_completed = (
        recent_data["completed_points"].sum() if has_points_data else 0
    )
    avg_points_weekly = recent_data["completed_points"].mean() if has_points_data else 0
    points_sparkline_values = (
        recent_data["completed_points"].tolist() if has_points_data else [0, 0, 0, 0]
    )

    # PROGRESSIVE BLENDING: Calculate blend_metadata for current week (Feature bd-a1vn)
    items_blend_metadata = None
    points_blend_metadata = None

    if (
        additional_context
        and additional_context.get("current_week_label")
        and len(recent_data) >= 2
    ):
        from data.metrics.blending import get_blend_metadata
        from data.metrics_calculator import calculate_forecast

        # Check if last week in recent_data is the current week
        last_week_label = None
        if "week_label" in recent_data.columns and len(recent_data) > 0:
            last_week_label = recent_data["week_label"].iloc[-1]
        current_week_label = additional_context["current_week_label"]

        if last_week_label == current_week_label:
            # Current week is in recent data - apply blending
            items_values = items_sparkline_values.copy()

            if len(items_values) >= 2:
                current_week_actual = items_values[-1]
                prior_weeks = items_values[:-1]
                forecast_weeks = (
                    prior_weeks[-4:] if len(prior_weeks) >= 4 else prior_weeks
                )

                # Calculate items forecast
                if len(forecast_weeks) >= 2:
                    try:
                        forecast_weeks_float = [float(v) for v in forecast_weeks]
                        forecast_data = calculate_forecast(forecast_weeks_float)
                        forecast_value = (
                            forecast_data.get("forecast_value", 0)
                            if forecast_data
                            else 0
                        )

                        if forecast_value > 0:
                            items_blend_metadata = get_blend_metadata(
                                current_week_actual, forecast_value
                            )
                            logger.info(
                                f"[Blending-RecentCompletions-Items] Actual: {current_week_actual:.1f}, "
                                f"Forecast: {forecast_value:.1f}, "
                                f"Blended: {items_blend_metadata['blended']:.1f}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to calculate items forecast for recent completions blending: {e}"
                        )

            # Calculate points blend metadata
            if has_points_data and show_points:
                points_values = points_sparkline_values.copy()

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
                            forecast_weeks_pts_float = [
                                float(v) for v in forecast_weeks_pts
                            ]
                            forecast_data_pts = calculate_forecast(
                                forecast_weeks_pts_float
                            )
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
                                    f"[Blending-RecentCompletions-Points] Actual: {current_week_actual_pts:.1f}, "
                                    f"Forecast: {forecast_value_pts:.1f}, "
                                    f"Blended: {points_blend_metadata['blended']:.1f}"
                                )
                        except Exception as e:
                            logger.warning(
                                f"Failed to calculate points forecast for recent completions blending: {e}"
                            )

    # Create metric cards for Recent Completions
    items_cards = [
        create_professional_metric_card(
            {
                "metric_name": "items_completed",
                "value": total_items_completed,
                "unit": "items",
                "_n_weeks": recent_window,
                "tooltip": f"Total items completed in the last {recent_window} weeks. This metric shows recent delivery throughput regardless of the data points filter. Breakdown shows Week 1 (oldest) to Week 4 (newest).",
                "error_state": "success",
                "total_issue_count": 0,
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
                                    "Past 4 Weeks (oldest → newest)",
                                    className="fw-bold",
                                    style={"fontSize": "0.85rem"},
                                ),
                            ],
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Small(
                                            f"Week {4 - i}: ", className="text-muted"
                                        ),
                                        html.Small(
                                            f"{int(items_sparkline_values[-(i + 1)])} items",
                                            className="fw-bold",
                                        ),
                                    ],
                                    className="d-flex justify-content-between mb-1",
                                    style={"fontSize": "0.8rem"},
                                )
                                for i in range(
                                    min(4, len(items_sparkline_values)) - 1, -1, -1
                                )
                            ],
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
                                    className=f"fas fa-arrow-{'up' if len(items_sparkline_values) >= 2 and items_sparkline_values[-1] > items_sparkline_values[0] else 'down' if len(items_sparkline_values) >= 2 else 'right'} me-1",
                                    style={
                                        "color": "#28a745"
                                        if len(items_sparkline_values) >= 2
                                        and items_sparkline_values[-1]
                                        > items_sparkline_values[0]
                                        else "#dc3545"
                                        if len(items_sparkline_values) >= 2
                                        else "#6c757d"
                                    },
                                ),
                                html.Small(
                                    f"{'Growing' if len(items_sparkline_values) >= 2 and items_sparkline_values[-1] > items_sparkline_values[0] else 'Declining' if len(items_sparkline_values) >= 2 else 'Stable'} throughput",
                                    className="text-muted fst-italic",
                                ),
                            ],
                            className="mt-2",
                            style={"fontSize": "0.75rem"},
                        ),
                    ],
                    className="mb-3",
                ),
            ]
            if items_sparkline_values and len(items_sparkline_values) > 0
            else None,
        ),
        create_professional_metric_card(
            {
                "metric_name": "items_per_week_avg",
                "alternative_name": "Average Items Per Week",
                "value": avg_items_weekly,
                "unit": "items/week",
                "_n_weeks": recent_window,
                "tooltip": f"Average items completed per week over the last {recent_window} weeks. Indicates current team velocity. Progressive blending is applied to the current week to smooth Monday reliability drops.",
                "error_state": "success",
                "total_issue_count": 0,
                "weekly_values": items_sparkline_values,
                "weekly_labels": [
                    f"W{i + 1}" for i in range(len(items_sparkline_values))
                ],
                "blend_metadata": items_blend_metadata,  # Progressive blending (bd-a1vn)
            },
            show_details_button=False,
        ),
    ]

    # Always show points cards - distinguish between disabled and no data
    if has_points_data and show_points and total_points_completed > 0:
        # Case 1: Points tracking enabled with data
        points_cards = [
            create_professional_metric_card(
                {
                    "metric_name": "points_completed",
                    "value": total_points_completed,
                    "unit": "points",
                    "_n_weeks": recent_window,
                    "tooltip": f"Total story points completed in the last {recent_window} weeks. This metric shows recent delivery throughput in terms of story points. Breakdown shows Week 1 (oldest) to Week 4 (newest).",
                    "error_state": "success",
                    "total_issue_count": 0,
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
                                        "Past 4 Weeks (oldest → newest)",
                                        className="fw-bold",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Small(
                                                f"Week {4 - i}: ",
                                                className="text-muted",
                                            ),
                                            html.Small(
                                                f"{points_sparkline_values[-(i + 1)]:.1f} pts",
                                                className="fw-bold",
                                            ),
                                        ],
                                        className="d-flex justify-content-between mb-1",
                                        style={"fontSize": "0.8rem"},
                                    )
                                    for i in range(
                                        min(4, len(points_sparkline_values)) - 1, -1, -1
                                    )
                                ],
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
                                        className=f"fas fa-arrow-{'up' if len(points_sparkline_values) >= 2 and points_sparkline_values[-1] > points_sparkline_values[0] else 'down' if len(points_sparkline_values) >= 2 else 'right'} me-1",
                                        style={
                                            "color": "#28a745"
                                            if len(points_sparkline_values) >= 2
                                            and points_sparkline_values[-1]
                                            > points_sparkline_values[0]
                                            else "#dc3545"
                                            if len(points_sparkline_values) >= 2
                                            else "#6c757d"
                                        },
                                    ),
                                    html.Small(
                                        f"{'Growing' if len(points_sparkline_values) >= 2 and points_sparkline_values[-1] > points_sparkline_values[0] else 'Declining' if len(points_sparkline_values) >= 2 else 'Stable'} throughput",
                                        className="text-muted fst-italic",
                                    ),
                                ],
                                className="mt-2",
                                style={"fontSize": "0.75rem"},
                            ),
                        ],
                        className="mb-3",
                    ),
                ]
                if points_sparkline_values and len(points_sparkline_values) > 0
                else None,
            ),
            create_professional_metric_card(
                {
                    "metric_name": "points_per_week_avg",
                    "alternative_name": "Average Points Per Week",
                    "value": avg_points_weekly,
                    "unit": "points/week",
                    "_n_weeks": recent_window,
                    "tooltip": f"Average story points completed per week over the last {recent_window} weeks. Indicates current team velocity in terms of story points. Progressive blending is applied to the current week to smooth Monday reliability drops.",
                    "error_state": "success",
                    "total_issue_count": 0,
                    "weekly_values": points_sparkline_values,
                    "weekly_labels": [
                        f"W{i + 1}" for i in range(len(points_sparkline_values))
                    ],
                    "blend_metadata": points_blend_metadata,  # Progressive blending (bd-a1vn)
                },
                show_details_button=False,
            ),
        ]
    elif not show_points:
        # Case 2: Points tracking disabled
        points_cards = [
            create_professional_metric_card(
                {
                    "metric_name": "points_completed",
                    "value": None,
                    "unit": "",
                    "error_state": "points_tracking_disabled",
                    "error_message": "Points tracking is disabled. Enable Points Tracking in Parameters panel to view story points metrics.",
                    "tooltip": "Enable Points Tracking in Parameters panel and configure the points field in JIRA Configuration to view this metric. When disabled, use Items Completed for throughput tracking.",
                    "total_issue_count": 0,
                }
            ),
            create_professional_metric_card(
                {
                    "metric_name": "points_per_week_avg",
                    "alternative_name": "Average Points Per Week",
                    "value": None,
                    "unit": "",
                    "error_state": "points_tracking_disabled",
                    "error_message": "Points tracking is disabled. Enable Points Tracking in Parameters panel to view story points metrics.",
                    "tooltip": "Enable Points Tracking in Parameters panel and configure the points field in JIRA Configuration to view this metric. When disabled, use Items/Week Avg for velocity tracking.",
                    "total_issue_count": 0,
                }
            ),
        ]
    else:
        # Case 3: Points tracking enabled but no data (0 points)
        points_cards = [
            create_professional_metric_card(
                {
                    "metric_name": "points_completed",
                    "value": None,
                    "unit": "",
                    "error_state": "no_data",
                    "error_message": "No story points data available. Configure story points field in Settings or complete items with point estimates.",
                    "tooltip": f"No story points completed in the last {recent_window} weeks. This may indicate that story points are not configured or no items with point estimates have been completed.",
                    "total_issue_count": 0,
                }
            ),
            create_professional_metric_card(
                {
                    "metric_name": "points_per_week_avg",
                    "alternative_name": "Average Points Per Week",
                    "value": None,
                    "unit": "",
                    "error_state": "no_data",
                    "error_message": "No story points data available. Configure story points field in Settings or complete items with point estimates.",
                    "tooltip": f"No story points data available for the last {recent_window} weeks. Configure story points field in Settings or complete items with point estimates.",
                    "total_issue_count": 0,
                }
            ),
        ]

    all_cards = items_cards + points_cards

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-check-circle me-2",
                        style={"color": COLOR_PALETTE["items"]},
                    ),
                    "Recent Completions",
                    html.Small(
                        f" (Last {recent_window} Weeks)", className="text-muted ms-2"
                    ),
                ],
                className="mb-3 mt-4",
            ),
            dbc.Row(
                [
                    dbc.Col(card, width=12, md=6, lg=3, className="mb-3")
                    for card in all_cards
                ]
            ),
        ],
        className="mb-4",
    )


def create_quality_scope_section(
    statistics_df: pd.DataFrame, settings: dict
) -> html.Div:
    """Create quality and scope tracking section.

    Args:
        statistics_df: DataFrame with statistics data
        settings: Dictionary with application settings

    Returns:
        Dash HTML Div component with quality and scope metrics
    """
    if statistics_df.empty:
        return html.Div()

    # Calculate scope metrics with time frame context
    scope_metrics = []

    if "created_items" in statistics_df.columns:
        total_created = statistics_df["created_items"].sum()
        total_completed = statistics_df["completed_items"].sum()
        scope_growth_rate = safe_divide(total_created, total_completed) * 100

        # Calculate scope change rate (% of current backlog that's new work)
        # Use remaining items from last snapshot + completed items as total_items
        total_items = total_created + (
            statistics_df["remaining_items"].iloc[-1]
            if "remaining_items" in statistics_df.columns and not statistics_df.empty
            else 0
        )
        scope_change_rate = (
            safe_divide(total_created, total_items) * 100 if total_items > 0 else 0
        )

        # Get date range for context
        if "date" in statistics_df.columns and not statistics_df.empty:
            start_date = statistics_df["date"].min()
            end_date = statistics_df["date"].max()
            # Convert to datetime and handle NaT (Not a Time) values
            start_dt = pd.to_datetime(start_date, format="mixed", errors="coerce")
            end_dt = pd.to_datetime(end_date, format="mixed", errors="coerce")
            if pd.notna(start_dt) and pd.notna(end_dt):
                date_range = (
                    f"{start_dt.strftime('%Y-%m-%d')} - {end_dt.strftime('%Y-%m-%d')}"
                )
            else:
                date_range = "tracked period"
            weeks_count = len(statistics_df)
        else:
            date_range = "tracked period"
            weeks_count = len(statistics_df)

        scope_metrics.extend(
            [
                {
                    "label": "New Work in Backlog",
                    "value": f"{scope_change_rate:.1f}%",
                    "color": "rgb(20, 168, 150)",  # Teal - distinct from items blue
                    "icon": "fa-chart-area",
                    "tooltip": f"New work as % of current backlog. Added {total_created:,} of {total_items:,} items during {date_range} ({weeks_count} weeks). Healthy: <15%, Warning: 15-35%, Critical: >35%. Your value: {scope_change_rate:.1f}%",
                },
                {
                    "label": "Scope Growth Rate",
                    "value": f"{scope_growth_rate:.1f}%",
                    "color": "#6610f2",
                    "icon": "fa-chart-line",
                    "tooltip": f"Work creation vs completion rate. Added {total_created:,} items, completed {total_completed:,} during {date_range}. <100% = shrinking backlog, >100% = growing backlog. Your value: {scope_growth_rate:.1f}%",
                },
            ]
        )

    # Calculate quality metrics
    if len(statistics_df) >= 4:
        # Velocity stability
        velocity_std = statistics_df["completed_items"].std()
        velocity_mean = statistics_df["completed_items"].mean()
        velocity_cv = safe_divide(velocity_std, velocity_mean) * 100

        # Trend analysis - compare first half vs second half of filtered data
        mid_point = len(statistics_df) // 2
        recent_avg = statistics_df.iloc[mid_point:]["completed_items"].mean()
        older_avg = (
            statistics_df.iloc[:mid_point]["completed_items"].mean()
            if mid_point > 0
            else recent_avg
        )
        trend_stability = (
            abs(recent_avg - older_avg) / older_avg * 100 if older_avg > 0 else 0
        )

        quality_metrics = [
            {
                "label": "Velocity Consistency",
                "value": f"{max(0, 100 - velocity_cv):.0f}%",
                "color": "#28a745",
            },
            {
                "label": "Trend Stability",
                "value": f"{max(0, 100 - trend_stability):.0f}%",
                "color": "#17a2b8",
            },
        ]
    else:
        quality_metrics = [
            {"label": "Velocity Consistency", "value": "N/A", "color": "#6c757d"},
            {"label": "Trend Stability", "value": "N/A", "color": "#6c757d"},
        ]

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-shield-alt me-2", style={"color": "#6f42c1"}
                    ),
                    "Quality & Scope Tracking",
                ],
                className="mb-3 mt-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    create_metric_card_header(
                                        title="Scope Management",
                                        tooltip_text="Track scope changes and backlog growth. Shows ratio of new items added vs completed, helping identify scope creep early. Healthy projects maintain balance between scope growth and completion rate.",
                                        tooltip_id="scope-management-card",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.I(
                                                                        className=f"fas {metric.get('icon', 'fa-info-circle')} me-2",
                                                                        style={
                                                                            "color": metric[
                                                                                "color"
                                                                            ],
                                                                            "fontSize": "1.2rem",
                                                                        },
                                                                    ),
                                                                    metric["label"],
                                                                    html.Span(
                                                                        " ",
                                                                        style={
                                                                            "marginRight": "4px"
                                                                        },
                                                                    ),
                                                                    create_info_tooltip(
                                                                        metric.get(
                                                                            "tooltip",
                                                                            "",
                                                                        ),
                                                                        f"scope-{metric['label'].lower().replace(' ', '-')}",
                                                                    )
                                                                    if metric.get(
                                                                        "tooltip"
                                                                    )
                                                                    else None,
                                                                ],
                                                                className="text-muted",
                                                                style={
                                                                    "fontSize": "0.85rem",
                                                                    "display": "flex",
                                                                    "alignItems": "center",
                                                                    "justifyContent": "center",
                                                                },
                                                            ),
                                                            html.Div(
                                                                metric["value"],
                                                                className="h3 mb-0",
                                                                style={
                                                                    "fontWeight": "bold",
                                                                    "color": metric[
                                                                        "color"
                                                                    ],
                                                                },
                                                            ),
                                                        ],
                                                        className="text-center p-2",
                                                    )
                                                    for metric in scope_metrics
                                                ]
                                            )
                                            if scope_metrics
                                            else html.Div(
                                                "No scope change data available",
                                                className="text-muted text-center p-3",
                                            )
                                        ]
                                    ),
                                    dbc.CardFooter(
                                        html.Small(
                                            [
                                                html.I(
                                                    className="fas fa-chart-line me-1"
                                                ),
                                                "Tracks new items added vs completed • Monitors backlog growth over project lifecycle",
                                            ],
                                            className="text-muted",
                                        ),
                                        className="text-center bg-light border-top py-2",
                                    ),
                                ],
                                id="scope-management-card",
                                className="h-100 shadow-sm border-0 metric-card",
                            )
                        ],
                        width=12,
                        md=6,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    create_metric_card_header(
                                        title="Quality Indicators",
                                        tooltip_text="Measures delivery predictability and consistency. High values (80%+) indicate stable, reliable team performance. Use these metrics to assess forecast accuracy and process maturity.",
                                        tooltip_id="quality-indicators-card",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    metric["label"],
                                                                    html.Span(
                                                                        " ",
                                                                        style={
                                                                            "marginRight": "4px"
                                                                        },
                                                                    ),
                                                                    create_info_tooltip(
                                                                        "Measures how consistent velocity is week-over-week. Calculated as 100% - coefficient of variation. Higher values (80%+) indicate predictable delivery pace, making forecasts more reliable.",
                                                                        "quality-velocity-consistency",
                                                                    )
                                                                    if metric["label"]
                                                                    == "Velocity Consistency"
                                                                    else create_info_tooltip(
                                                                        "Measures velocity change between recent and historical periods. High values (80%+) indicate stable trends. Low values suggest significant velocity shifts requiring investigation.",
                                                                        "quality-trend-stability",
                                                                    )
                                                                    if metric["label"]
                                                                    == "Trend Stability"
                                                                    else None,
                                                                ],
                                                                className="text-muted",
                                                                style={
                                                                    "fontSize": "0.85rem",
                                                                    "display": "flex",
                                                                    "alignItems": "center",
                                                                    "justifyContent": "center",
                                                                },
                                                            ),
                                                            html.Div(
                                                                metric["value"],
                                                                className="h3 mb-0",
                                                                style={
                                                                    "fontWeight": "bold",
                                                                    "color": metric[
                                                                        "color"
                                                                    ],
                                                                },
                                                            ),
                                                        ],
                                                        className="text-center p-2",
                                                    )
                                                    for metric in quality_metrics
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardFooter(
                                        html.Small(
                                            [
                                                html.I(
                                                    className="fas fa-gauge-high me-1"
                                                ),
                                                "Consistency + stability metrics • High values (80%+) enable reliable forecasting",
                                            ],
                                            className="text-muted",
                                        ),
                                        className="text-center bg-light border-top py-2",
                                    ),
                                ],
                                id="quality-indicators-card",
                                className="h-100 shadow-sm border-0 metric-card",
                            )
                        ],
                        width=12,
                        md=6,
                        className="mb-3",
                    ),
                ]
            ),
        ],
        className="mb-4",
    )
