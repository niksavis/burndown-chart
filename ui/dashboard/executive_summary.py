"""Executive Summary Module.

This module provides the executive summary section for the dashboard, displaying
key project health indicators including health score, completion metrics, and
forecast information.

The executive summary includes:
- Project health score with status indicator
- Items completion tracking (completed vs remaining)
- Points completion tracking (completed vs remaining)
- Deadline and forecast dates
- Progress rings with visual indicators
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from configuration.help_content import DASHBOARD_METRICS_TOOLTIPS
from ui.style_constants import COLOR_PALETTE

from .utils import (
    calculate_project_health_score,
    create_progress_ring,
    get_brief_health_reason,
    get_health_status,
    safe_divide,
)

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


def create_executive_summary_section(
    statistics_df: pd.DataFrame,
    forecast_data: dict[str, Any],
    settings: dict[str, Any],
    avg_weekly_items: float,
) -> dbc.Card:
    """Create executive summary section with key project health indicators.

    The Data Points slider affects historical metrics but not current remaining work:
    - Remaining (items/points): Always shows current not-yet-done work (fixed)
    - Completed (items/points): Shows work completed in the selected window (changes with slider)
    - Total: Remaining + Completed (changes with slider as Completed changes)

    Args:
        statistics_df: DataFrame containing project statistics
        forecast_data: Dictionary containing forecast data (velocity_cv, schedule_variance_days, completion_date)
        settings: Dictionary containing project settings (total_items, total_points, deadline, show_points, extended_metrics, budget_data)
        avg_weekly_items: Average weekly items completed

    Returns:
        dbc.Card containing the executive summary section
    """
    # Calculate completed items from the FILTERED statistics DataFrame
    completed_items = (
        statistics_df["completed_items"].sum() if not statistics_df.empty else 0
    )
    completed_points = (
        statistics_df["completed_points"].sum() if not statistics_df.empty else 0
    )

    # Use CURRENT remaining from settings (fixed, doesn't change with slider)
    remaining_items = settings.get("total_items", 0)
    remaining_points = settings.get("total_points", 0)

    # Calculate total scope = remaining + completed in window
    total_items = remaining_items + completed_items
    total_points = remaining_points + completed_points

    deadline = settings.get("deadline")

    completion_percentage = safe_divide(completed_items, total_items) * 100
    points_percentage = (
        safe_divide(completed_points, total_points) * 100 if total_points > 0 else 0
    )

    # DEBUG: Log completion calculation
    logger.info(
        f"[APP COMPLETION] completed_items={completed_items}, remaining_items={remaining_items}, "
        f"total_items={total_items}, completion_pct={completion_percentage:.2f}%"
    )

    # Calculate project health score with DYNAMIC metrics from filtered data
    velocity_cv = forecast_data.get("velocity_cv", 0)
    schedule_variance = forecast_data.get("schedule_variance_days", 0)

    # Calculate trend direction from filtered data
    trend_direction = "stable"
    recent_velocity_change = 0

    if not statistics_df.empty and len(statistics_df) >= 6:
        # Split data into older and recent halves
        mid_point = len(statistics_df) // 2
        older_half = statistics_df.iloc[:mid_point]
        recent_half = statistics_df.iloc[mid_point:]

        # Calculate velocity for each half (items per week)
        if len(older_half) > 0 and len(recent_half) > 0:
            older_weeks = max(1, len(older_half))
            recent_weeks = max(1, len(recent_half))

            older_velocity = older_half["completed_items"].sum() / older_weeks
            recent_velocity = recent_half["completed_items"].sum() / recent_weeks

            if older_velocity > 0:
                recent_velocity_change = (
                    (recent_velocity - older_velocity) / older_velocity
                ) * 100

                # Determine trend direction (>10% change is significant)
                if recent_velocity_change > 10:
                    trend_direction = "improving"
                elif recent_velocity_change < -10:
                    trend_direction = "declining"

    # Calculate scope change rate from filtered data
    scope_change_rate = 0
    if not statistics_df.empty and "created_items" in statistics_df.columns:
        total_created = statistics_df["created_items"].sum()
        if total_items > 0:
            scope_change_rate = (total_created / total_items) * 100

    # Calculate completion confidence from schedule variance (same as report)
    # Positive schedule_variance = ahead of schedule (buffer days)
    # Negative schedule_variance = behind schedule
    buffer_days = (
        schedule_variance  # schedule_variance is forecast_days - days_to_deadline
    )
    if buffer_days >= 28:
        completion_confidence = 95  # Very high confidence
    elif buffer_days >= 14:
        completion_confidence = 80  # High confidence
    elif buffer_days >= 0:
        completion_confidence = 65  # Moderate confidence
    elif buffer_days >= -14:
        completion_confidence = 45  # Low confidence
    else:
        completion_confidence = 25  # Very low confidence

    health_metrics = {
        "completion_percentage": completion_percentage,
        "current_velocity_items": avg_weekly_items,  # Items per week from filtered statistics
        "velocity_cv": velocity_cv,
        "schedule_variance_days": schedule_variance,
        "scope_change_rate": scope_change_rate,
        "trend_direction": trend_direction,
        "recent_velocity_change": recent_velocity_change,
        "completion_confidence": completion_confidence,  # Calculated from schedule variance
    }

    # DEBUG: Log health metrics to trace 18% vs 13% discrepancy
    logger.info(
        f"[HEALTH CALC] Input metrics: velocity_cv={velocity_cv:.2f}, "
        f"schedule_variance={schedule_variance:.2f}, scope_change_rate={scope_change_rate:.2f}, "
        f"trend_direction={trend_direction}, recent_velocity_change={recent_velocity_change:.2f}, "
        f"statistics_rows={len(statistics_df)}"
    )

    # Extract extended metrics from additional_context (calculated in callback)
    # These are optional - if not available, uses dashboard-only mode with adaptive weighting
    extended_metrics = settings.get("extended_metrics", {})

    dora_metrics = extended_metrics.get("dora")
    flow_metrics = extended_metrics.get("flow")
    bug_metrics = extended_metrics.get("bug_analysis")
    budget_metrics = settings.get("budget_data")  # Budget data passed separately
    scope_metrics = {"scope_change_rate": scope_change_rate}

    # Log available extended metrics for v3.0 comprehensive formula
    logger.info(
        f"[HEALTH v3.0] Available extended metrics: "
        f"DORA={'✓' if dora_metrics else '✗'}, "
        f"Flow={'✓' if flow_metrics else '✗'}, "
        f"Bug={'✓' if bug_metrics else '✗'}, "
        f"Budget={'✓' if budget_metrics else '✗'}"
    )

    health_score = calculate_project_health_score(
        health_metrics,
        dora_metrics=dora_metrics,
        flow_metrics=flow_metrics,
        bug_metrics=bug_metrics,
        budget_metrics=budget_metrics,
        scope_metrics=scope_metrics,
    )

    logger.info(f"[HEALTH CALC] Calculated health_score={health_score}%")

    health_status = get_health_status(health_score)
    health_reason = get_brief_health_reason(health_metrics)

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4(
                        [
                            html.I(
                                className="fas fa-tachometer-alt me-2",
                                style={"color": "#007bff"},
                            ),
                            "Project Health Overview",
                            html.Span(
                                [
                                    html.I(
                                        className="fas fa-info-circle ms-2",
                                        id="health-calculation-info",
                                        style={
                                            "fontSize": "0.9rem",
                                            "color": "#6c757d",
                                            "cursor": "pointer",
                                        },
                                    ),
                                    dbc.Tooltip(
                                        DASHBOARD_METRICS_TOOLTIPS["health_score"],
                                        target="health-calculation-info",
                                        placement="right",
                                        trigger="click",
                                        autohide=True,
                                    ),
                                ],
                                className="d-inline",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Redesigned metrics row with consistent sizing and alignment
                    dbc.Row(
                        [
                            # Health Score
                            dbc.Col(
                                html.Div(
                                    [
                                        html.H6(
                                            [
                                                html.I(
                                                    className="fas fa-heartbeat me-2",
                                                    style={"color": "#495057"},
                                                ),
                                                "Health",
                                            ],
                                            className="mb-3 text-center",
                                            style={
                                                "fontSize": "0.95rem",
                                                "fontWeight": "600",
                                                "color": "#495057",
                                            },
                                        ),
                                        create_progress_ring(
                                            health_score, health_status["color"], 90
                                        ),
                                        html.Div(
                                            health_status["label"],
                                            className="mt-3 mb-1",
                                            style={
                                                "fontSize": "1.25rem",
                                                "fontWeight": "bold",
                                                "color": health_status["color"],
                                            },
                                        ),
                                        html.Small(
                                            health_reason,
                                            className="text-muted d-block mb-3",
                                            style={
                                                "fontSize": "0.75rem",
                                                "fontStyle": "italic",
                                            },
                                        )
                                        if health_reason
                                        else html.Div(className="mb-2"),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-calendar-alt me-1",
                                                            style={
                                                                "fontSize": "0.8rem"
                                                            },
                                                        ),
                                                        html.Span(
                                                            "Deadline: ",
                                                            style={"fontWeight": "600"},
                                                        ),
                                                        html.Span(
                                                            deadline
                                                            if deadline
                                                            else "Not set"
                                                        ),
                                                    ],
                                                    style={
                                                        "fontSize": "0.9rem",
                                                        "color": "#495057",
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line me-1",
                                                            style={
                                                                "fontSize": "0.9rem"
                                                            },
                                                        ),
                                                        html.Span(
                                                            "Forecast: ",
                                                            style={"fontWeight": "600"},
                                                            title=f"PERT-weighted forecast based on {'story points' if settings.get('show_points', True) else 'items'} velocity (matches Burndown Chart and Report)",
                                                        ),
                                                        html.Span(
                                                            forecast_data.get(
                                                                "completion_date"
                                                            )
                                                            or "Not calculated"
                                                        ),
                                                    ],
                                                    style={
                                                        "fontSize": "0.9rem",
                                                        "color": "#495057",
                                                    },
                                                ),
                                            ],
                                        ),
                                    ],
                                    className="text-center d-flex flex-column align-items-center",
                                    style={
                                        "padding": "20px 15px",
                                        "borderRight": "3px solid #ced4da",
                                        "height": "100%",
                                    },
                                ),
                                xs=12,
                                md=2,
                                className="mb-4 mb-md-0",
                            ),
                            # Items Group
                            dbc.Col(
                                html.Div(
                                    [
                                        html.H6(
                                            [
                                                html.I(
                                                    className="fas fa-tasks me-2",
                                                    style={
                                                        "color": COLOR_PALETTE["items"]
                                                    },
                                                ),
                                                "Items",
                                            ],
                                            className="mb-3 text-center",
                                            style={
                                                "fontSize": "0.95rem",
                                                "fontWeight": "600",
                                                "color": COLOR_PALETTE["items"],
                                            },
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            create_progress_ring(
                                                                completion_percentage,
                                                                COLOR_PALETTE["items"],
                                                                90,
                                                            ),
                                                            html.Div(
                                                                f"{completed_items:,}",
                                                                className="mt-3 mb-1",
                                                                style={
                                                                    "fontSize": "1.5rem",
                                                                    "fontWeight": "bold",
                                                                    "color": COLOR_PALETTE[
                                                                        "items"
                                                                    ],
                                                                },
                                                            ),
                                                            html.Div(
                                                                "Completed",
                                                                className="text-muted",
                                                                style={
                                                                    "fontSize": "0.9rem"
                                                                },
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    width=6,
                                                ),
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            create_progress_ring(
                                                                100
                                                                - completion_percentage,
                                                                COLOR_PALETTE["items"],
                                                                90,
                                                            ),
                                                            html.Div(
                                                                f"{remaining_items:,}",
                                                                className="mt-3 mb-1",
                                                                style={
                                                                    "fontSize": "1.5rem",
                                                                    "fontWeight": "bold",
                                                                    "color": COLOR_PALETTE[
                                                                        "items"
                                                                    ],
                                                                },
                                                            ),
                                                            html.Div(
                                                                "Remaining",
                                                                className="text-muted",
                                                                style={
                                                                    "fontSize": "0.9rem"
                                                                },
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    width=6,
                                                ),
                                            ],
                                        ),
                                        html.Hr(
                                            className="my-2",
                                            style={
                                                "width": "80%",
                                                "margin": "10px auto",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-tasks me-1",
                                                    style={
                                                        "color": COLOR_PALETTE["items"]
                                                    },
                                                ),
                                                html.Span(
                                                    f"{total_items:,} items",
                                                    style={"fontWeight": "600"},
                                                ),
                                            ],
                                            className="mt-2 text-center",
                                            style={
                                                "fontSize": "0.95rem",
                                                "color": "#495057",
                                            },
                                        ),
                                    ],
                                    className="d-flex flex-column",
                                    style={
                                        "padding": "20px 15px",
                                        "borderRight": "3px solid #ced4da",
                                        "height": "100%",
                                    },
                                ),
                                xs=12,
                                md=5,
                                className="mb-4 mb-md-0",
                            ),
                            # Points Group
                            dbc.Col(
                                html.Div(
                                    [
                                        html.H6(
                                            [
                                                html.I(
                                                    className="fas fa-chart-bar me-2",
                                                    style={
                                                        "color": COLOR_PALETTE["points"]
                                                    },
                                                ),
                                                "Points",
                                            ],
                                            className="mb-3 text-center",
                                            style={
                                                "fontSize": "0.95rem",
                                                "fontWeight": "600",
                                                "color": COLOR_PALETTE["points"],
                                            },
                                        ),
                                        # Case 1: Points tracking enabled with data
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            create_progress_ring(
                                                                points_percentage,
                                                                COLOR_PALETTE["points"],
                                                                90,
                                                            ),
                                                            html.Div(
                                                                f"{completed_points:,.1f}",
                                                                className="mt-3 mb-1",
                                                                style={
                                                                    "fontSize": "1.5rem",
                                                                    "fontWeight": "bold",
                                                                    "color": COLOR_PALETTE[
                                                                        "points"
                                                                    ],
                                                                },
                                                            ),
                                                            html.Div(
                                                                "Completed",
                                                                className="text-muted",
                                                                style={
                                                                    "fontSize": "0.9rem"
                                                                },
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    width=6,
                                                ),
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            create_progress_ring(
                                                                100 - points_percentage,
                                                                COLOR_PALETTE["points"],
                                                                90,
                                                            ),
                                                            html.Div(
                                                                f"{remaining_points:,.1f}",
                                                                className="mt-3 mb-1",
                                                                style={
                                                                    "fontSize": "1.5rem",
                                                                    "fontWeight": "bold",
                                                                    "color": COLOR_PALETTE[
                                                                        "points"
                                                                    ],
                                                                },
                                                            ),
                                                            html.Div(
                                                                "Remaining",
                                                                style={
                                                                    "fontSize": "0.9rem",
                                                                    "color": "#6c757d",
                                                                },
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    width=6,
                                                ),
                                            ],
                                        )
                                        if (
                                            total_points > 0
                                            and settings.get("show_points", True)
                                        )
                                        # Case 2: Points tracking disabled
                                        else (
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-toggle-off fa-2x text-secondary mb-2"
                                                    ),
                                                    html.Div(
                                                        "Points Tracking Disabled",
                                                        className="h5 mb-2",
                                                        style={
                                                            "fontWeight": "600",
                                                            "color": "#6c757d",
                                                        },
                                                    ),
                                                    html.Small(
                                                        "Points tracking is disabled. Enable Points Tracking in Parameters panel to view story points metrics.",
                                                        className="text-muted",
                                                        style={"fontSize": "0.75rem"},
                                                    ),
                                                ],
                                                className="text-center",
                                                style={
                                                    "padding": "20px 10px",
                                                },
                                            )
                                            if not settings.get("show_points", True)
                                            # Case 3: Points tracking enabled but no data
                                            else html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-database fa-2x text-secondary mb-2"
                                                    ),
                                                    html.Div(
                                                        "No Points Data",
                                                        className="h5 mb-2",
                                                        style={
                                                            "fontWeight": "600",
                                                            "color": "#6c757d",
                                                        },
                                                    ),
                                                    html.Small(
                                                        "No story points data available. Configure story points field in Settings or complete items with point estimates.",
                                                        className="text-muted",
                                                        style={"fontSize": "0.75rem"},
                                                    ),
                                                ],
                                                className="text-center",
                                                style={
                                                    "padding": "20px 10px",
                                                },
                                            )
                                        ),
                                        html.Hr(
                                            className="my-2",
                                            style={
                                                "width": "80%",
                                                "margin": "10px auto",
                                            },
                                        )
                                        if total_points > 0
                                        and settings.get("show_points", True)
                                        else None,
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-chart-bar me-1",
                                                    style={
                                                        "color": COLOR_PALETTE["points"]
                                                    },
                                                ),
                                                html.Span(
                                                    f"{total_points:,.1f} points",
                                                    style={"fontWeight": "600"},
                                                ),
                                            ],
                                            className="mt-2 text-center",
                                            style={
                                                "fontSize": "0.95rem",
                                                "color": "#495057",
                                            },
                                        )
                                        if total_points > 0
                                        and settings.get("show_points", True)
                                        else None,
                                    ],
                                    className="d-flex flex-column",
                                    style={
                                        "padding": "20px 15px",
                                        "height": "100%",
                                    },
                                ),
                                xs=12,
                                md=5,
                                className="mb-4 mb-md-0",
                            ),
                        ],
                        className="mb-3 align-items-stretch",
                    ),
                ]
            )
        ],
        className="mb-4 shadow-sm",
        style={
            "background": health_status["bg_color"],
            "border": f"2px solid {health_status['color']}",
            "borderRadius": "0.375rem",
            "transition": "all 0.2s ease-in-out",
        },
        id="project-health-overview-card",
    )
