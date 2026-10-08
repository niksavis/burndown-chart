from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from configuration.help_content_metrics import DASHBOARD_METRICS_TOOLTIPS
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

    completed_items = (
        statistics_df["completed_items"].sum() if not statistics_df.empty else 0
    )
    completed_points = (
        statistics_df["completed_points"].sum() if not statistics_df.empty else 0
    )

    remaining_items = settings.get("total_items", 0)
    remaining_points = settings.get("total_points", 0)

    total_items = remaining_items + completed_items
    total_points = remaining_points + completed_points

    deadline = settings.get("deadline")

    completion_percentage = safe_divide(completed_items, total_items) * 100
    points_percentage = (
        safe_divide(completed_points, total_points) * 100 if total_points > 0 else 0
    )
    points_enabled = settings.get("show_points", True)
    points_available = total_points > 0 and points_enabled
    forecast_basis = "story points" if points_enabled else "items"
    forecast_title_text = (
        "PERT-weighted forecast based on "
        f"{forecast_basis} velocity "
        "(matches Burndown and Report)"
    )

    metric_value_style_items = {
        "fontSize": "1.5rem",
        "fontWeight": "bold",
        "color": COLOR_PALETTE["items"],
    }
    metric_value_style_points = {
        "fontSize": "1.5rem",
        "fontWeight": "bold",
        "color": COLOR_PALETTE["points"],
    }
    metric_label_style = {"fontSize": "0.9rem"}
    metric_label_muted_style = {"fontSize": "0.9rem", "color": "#6c757d"}
    secondary_panel_title_style = {"fontWeight": "600", "color": "#6c757d"}
    deadline_icon_class = "fas fa-calendar-alt me-1"
    forecast_icon_class = "fas fa-chart-line me-1"
    points_disabled_icon_class = "fas fa-toggle-off fa-2x text-secondary mb-2"
    points_no_data_icon_class = "fas fa-database fa-2x text-secondary mb-2"
    points_disabled_help = (
        "Points tracking is disabled. Enable Points Tracking in Parameters panel "
        "to view story points metrics."
    )
    points_no_data_help = (
        "No story points data available. Configure story points field in Settings "
        "or complete items with point estimates."
    )

    logger.info(
        f"[APP COMPLETION] completed_items={completed_items}, "
        f"remaining_items={remaining_items}, "
        f"total_items={total_items}, completion_pct={completion_percentage:.2f}%"
    )

    velocity_cv = forecast_data.get("velocity_cv", 0)
    schedule_variance = forecast_data.get("schedule_variance_days", 0)

    trend_direction = "stable"
    recent_velocity_change = 0

    if not statistics_df.empty and len(statistics_df) >= 6:
        mid_point = len(statistics_df) // 2
        older_half = statistics_df.iloc[:mid_point]
        recent_half = statistics_df.iloc[mid_point:]

        if len(older_half) > 0 and len(recent_half) > 0:
            older_weeks = max(1, len(older_half))
            recent_weeks = max(1, len(recent_half))

            older_velocity = older_half["completed_items"].sum() / older_weeks
            recent_velocity = recent_half["completed_items"].sum() / recent_weeks

            if older_velocity > 0:
                recent_velocity_change = (
                    (recent_velocity - older_velocity) / older_velocity
                ) * 100

                if recent_velocity_change > 10:
                    trend_direction = "improving"
                elif recent_velocity_change < -10:
                    trend_direction = "declining"

    scope_change_rate = 0
    if not statistics_df.empty and "created_items" in statistics_df.columns:
        total_created = statistics_df["created_items"].sum()
        if total_items > 0:
            scope_change_rate = (total_created / total_items) * 100

    buffer_days = schedule_variance
    if buffer_days >= 28:
        completion_confidence = 95
    elif buffer_days >= 14:
        completion_confidence = 80
    elif buffer_days >= 0:
        completion_confidence = 65
    elif buffer_days >= -14:
        completion_confidence = 45
    else:
        completion_confidence = 25

    health_metrics = {
        "completion_percentage": completion_percentage,
        "current_velocity_items": avg_weekly_items,
        "velocity_cv": velocity_cv,
        "schedule_variance_days": schedule_variance,
        "scope_change_rate": scope_change_rate,
        "trend_direction": trend_direction,
        "recent_velocity_change": recent_velocity_change,
        "completion_confidence": completion_confidence,
    }

    logger.info(
        f"[HEALTH CALC] Input metrics: velocity_cv={velocity_cv:.2f}, "
        f"schedule_variance={schedule_variance:.2f}, "
        f"scope_change_rate={scope_change_rate:.2f}, "
        f"trend_direction={trend_direction}, "
        f"recent_velocity_change={recent_velocity_change:.2f}, "
        f"statistics_rows={len(statistics_df)}"
    )

    extended_metrics = settings.get("extended_metrics", {})

    dora_metrics = extended_metrics.get("dora")
    flow_metrics = extended_metrics.get("flow")
    bug_metrics = extended_metrics.get("bug_analysis")
    budget_metrics = settings.get("budget_data")
    scope_metrics = {"scope_change_rate": scope_change_rate}

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
                                        className="fas fa-info-circle ms-2 text-info",
                                        id="health-calculation-info",
                                        style={
                                            "fontSize": "0.9rem",
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
                    dbc.Row(
                        [
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
                                                            className=deadline_icon_class,
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
                                                            className=forecast_icon_class,
                                                            style={
                                                                "fontSize": "0.9rem"
                                                            },
                                                        ),
                                                        html.Span(
                                                            "Forecast: ",
                                                            style={"fontWeight": "600"},
                                                            title=forecast_title_text,
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
                                    className=(
                                        "text-center d-flex flex-column "
                                        "align-items-center"
                                    ),
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
                                                                style=metric_value_style_items,
                                                            ),
                                                            html.Div(
                                                                "Completed",
                                                                className="text-muted",
                                                                style=metric_label_style,
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
                                                                style=metric_value_style_items,
                                                            ),
                                                            html.Div(
                                                                "Remaining",
                                                                className="text-muted",
                                                                style=metric_label_style,
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
                                                                style=metric_value_style_points,
                                                            ),
                                                            html.Div(
                                                                "Completed",
                                                                className="text-muted",
                                                                style=metric_label_style,
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
                                                                style=metric_value_style_points,
                                                            ),
                                                            html.Div(
                                                                "Remaining",
                                                                style=metric_label_muted_style,
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    width=6,
                                                ),
                                            ],
                                        )
                                        if points_available
                                        else (
                                            html.Div(
                                                [
                                                    html.I(
                                                        className=points_disabled_icon_class
                                                    ),
                                                    html.Div(
                                                        "Points Tracking Disabled",
                                                        className="h5 mb-2",
                                                        style=secondary_panel_title_style,
                                                    ),
                                                    html.Small(
                                                        points_disabled_help,
                                                        className="text-muted",
                                                        style={"fontSize": "0.75rem"},
                                                    ),
                                                ],
                                                className="text-center",
                                                style={
                                                    "padding": "20px 10px",
                                                },
                                            )
                                            if not points_enabled
                                            else html.Div(
                                                [
                                                    html.I(
                                                        className=points_no_data_icon_class
                                                    ),
                                                    html.Div(
                                                        "No Points Data",
                                                        className="h5 mb-2",
                                                        style=secondary_panel_title_style,
                                                    ),
                                                    html.Small(
                                                        points_no_data_help,
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
                                        if points_available
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
                                        if points_available
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
