"""
Modern Dashboard UI Module - Complete Enhanced Version

This is the COMPLETE working version with:
- All metrics from old dashboard (Project Overview, Completion Forecast, Weekly Velocity)
- Enhanced features: sparklines, collapsible details, progress bars
- All forecast methods: PERT, Average, Median
- Subtle animations
- Proper card alignment
"""

#######################################################################
# IMPORTS
#######################################################################
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from datetime import datetime, timedelta

from ui.style_constants import COLOR_PALETTE


#######################################################################
# HELPER FUNCTIONS
#######################################################################


def _create_sparkline_bars(data_series, color="#0d6efd", height=40):
    """Create CSS-based sparkline bar chart from data series."""
    if not data_series or len(data_series) == 0:
        return html.Div(
            "No data",
            className="text-muted text-center",
            style={
                "height": f"{height}px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
            },
        )

    # Take last 10 data points
    recent_data = list(data_series)[-10:]

    # Normalize values
    max_val = max(recent_data) if max(recent_data) > 0 else 1
    normalized = [v / max_val for v in recent_data]

    # Create bars with fade effect
    bars = []
    for i, norm_val in enumerate(normalized):
        bar_height = max(norm_val * height, 3)
        opacity = 0.4 + (i / len(normalized)) * 0.6

        bars.append(
            html.Div(
                style={
                    "width": "8px",
                    "height": f"{bar_height}px",
                    "backgroundColor": color,
                    "opacity": opacity,
                    "borderRadius": "2px",
                    "transition": "all 0.3s ease",
                },
                className="sparkline-bar mx-1",
            )
        )

    return html.Div(
        bars,
        className="d-flex align-items-end justify-content-center",
        style={"height": f"{height}px", "gap": "2px"},
    )


def _calculate_velocity_trend(statistics_df, metric_type="items"):
    """Calculate velocity trend percentage and direction."""
    if statistics_df.empty or len(statistics_df) < 4:
        return {
            "percent": 0,
            "direction": "stable",
            "color": "#6c757d",
            "icon": "fa-minus",
        }

    recent = statistics_df.tail(4)
    col_name = f"completed_{metric_type}"

    if col_name not in recent.columns:
        return {
            "percent": 0,
            "direction": "stable",
            "color": "#6c757d",
            "icon": "fa-minus",
        }

    recent_avg = recent[col_name].tail(2).mean()
    previous_avg = recent[col_name].head(2).mean()

    if previous_avg == 0:
        return {
            "percent": 0,
            "direction": "stable",
            "color": "#6c757d",
            "icon": "fa-minus",
        }

    percent_change = ((recent_avg - previous_avg) / previous_avg) * 100

    if abs(percent_change) < 5:
        return {
            "percent": 0,
            "direction": "stable",
            "color": "#6c757d",
            "icon": "fa-minus",
        }
    elif percent_change > 0:
        return {
            "percent": percent_change,
            "direction": "up",
            "color": "#28a745",
            "icon": "fa-arrow-up",
        }
    else:
        return {
            "percent": percent_change,
            "direction": "down",
            "color": "#dc3545",
            "icon": "fa-arrow-down",
        }


def _create_progress_bar(completed, total, color="#0d6efd"):
    """Create a progress bar showing completion percentage."""
    if total == 0:
        percent = 0
    else:
        percent = min((completed / total) * 100, 100)

    return html.Div(
        [
            html.Div(
                f"{percent:.0f}%",
                className="progress-bar",
                style={
                    "width": f"{percent}%",
                    "backgroundColor": color,
                    "transition": "width 1s ease",
                },
            ),
        ],
        className="progress",
        style={"height": "20px", "borderRadius": "10px", "backgroundColor": "#e9ecef"},
    )


#######################################################################
# ENHANCED METRIC CARD
#######################################################################


def create_enhanced_dashboard_card(
    title,
    icon,
    icon_color,
    primary_metric,
    sparkline_data=None,
    details=None,
    card_id=None,
):
    """
    Create an enhanced dashboard card with all features.

    Args:
        title: Card title
        icon: FontAwesome icon
        icon_color: Icon color
        primary_metric: Dict with {" value", "label"}
        sparkline_data: List of values for sparkline
        details: List of dicts with {"label", "value"} for additional metrics
        card_id: Optional card ID
    """
    details = details or []

    card_content = [
        # Header
        html.Div(
            [
                html.I(
                    className=f"{icon} me-2",
                    style={"color": icon_color, "fontSize": "1.1rem"},
                ),
                html.Span(
                    title, className="fw-semibold", style={"fontSize": "0.95rem"}
                ),
            ],
            className="d-flex align-items-center mb-3 pb-2 border-bottom",
        ),
        # Primary metric
        html.Div(
            [
                html.Div(
                    primary_metric["value"],
                    className="display-6 fw-bold mb-1",
                    style={"color": icon_color, "lineHeight": "1.2"},
                ),
                html.Small(primary_metric["label"], className="text-muted d-block"),
            ],
            className="text-center mb-3",
        ),
    ]

    # Add sparkline if provided
    if sparkline_data:
        card_content.append(
            html.Div(
                [
                    _create_sparkline_bars(sparkline_data, color=icon_color, height=35),
                    html.Small(
                        "Last 10 weeks",
                        className="text-muted text-center d-block mt-1",
                        style={"fontSize": "0.7rem"},
                    ),
                ],
                className="mb-3 px-2",
            )
        )

    # Add details
    if details:
        detail_items = []
        for detail in details:
            detail_items.append(
                html.Div(
                    [
                        html.Small(
                            detail["label"],
                            className="text-muted d-block",
                            style={"fontSize": "0.75rem"},
                        ),
                        html.Div(
                            detail["value"],
                            className="fw-semibold",
                            style={"fontSize": "0.9rem"},
                        ),
                    ],
                    className="mb-2",
                )
            )
        card_content.append(html.Div(detail_items, className="border-top pt-3 mt-2"))

    return dbc.Card(
        dbc.CardBody(card_content),
        className="h-100 shadow-sm",
        id=card_id,
        style={
            "minHeight": "340px",
            "transition": "transform 0.2s ease, box-shadow 0.2s ease",
        },
    )


#######################################################################
# MAIN DASHBOARD LAYOUT
#######################################################################


def create_modern_dashboard_content(
    statistics_df,
    pert_time_items,
    pert_time_points,
    avg_weekly_items,
    avg_weekly_points,
    med_weekly_items,
    med_weekly_points,
    days_to_deadline,
    total_items,
    total_points,
    deadline_str,
    show_points=True,
):
    """
    Create complete modern dashboard with all metrics and enhancements.

    This includes everything from the old dashboard plus:
    - Sparkline velocity charts
    - Progress bars
    - All forecast methods (PERT, Average, Median)
    - Trend indicators
    """
    current_date = datetime.now()

    # Calculate completed and remaining
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
    actual_total_points = completed_points + remaining_points if show_points else 0

    # PERT forecast dates
    items_pert_date = current_date + timedelta(days=pert_time_items)
    items_pert_str = items_pert_date.strftime("%b %d, %Y")
    items_on_track = pert_time_items <= days_to_deadline

    points_pert_date = (
        current_date + timedelta(days=pert_time_points) if pert_time_points else None
    )
    points_pert_str = (
        points_pert_date.strftime("%b %d, %Y") if points_pert_date else "N/A"
    )
    points_on_track = (
        pert_time_points <= days_to_deadline if pert_time_points else False
    )

    # Calculate Average and Median forecast dates
    items_avg_days = (
        (remaining_items / avg_weekly_items * 7)
        if avg_weekly_items > 0
        else float("inf")
    )
    items_med_days = (
        (remaining_items / med_weekly_items * 7)
        if med_weekly_items > 0
        else float("inf")
    )

    if show_points:
        points_avg_days = (
            (remaining_points / avg_weekly_points * 7)
            if avg_weekly_points > 0
            else float("inf")
        )
        points_med_days = (
            (remaining_points / med_weekly_points * 7)
            if med_weekly_points > 0
            else float("inf")
        )
    else:
        points_avg_days = float("inf")
        points_med_days = float("inf")

    # Format dates
    def format_forecast_date(days):
        if days == float("inf") or days > 3650:
            return "∞"
        date = current_date + timedelta(days=days)
        return date.strftime("%b %d, %Y")

    items_avg_str = format_forecast_date(items_avg_days)
    items_med_str = format_forecast_date(items_med_days)
    points_avg_str = format_forecast_date(points_avg_days) if show_points else "N/A"
    points_med_str = format_forecast_date(points_med_days) if show_points else "N/A"

    # Get velocity trends
    items_trend = _calculate_velocity_trend(statistics_df, "items")
    points_trend = (
        _calculate_velocity_trend(statistics_df, "points") if show_points else None
    )

    # Extract sparkline data (last 10 weeks)
    items_sparkline = (
        list(statistics_df["completed_items"].tail(10))
        if not statistics_df.empty
        else []
    )
    points_sparkline = (
        list(statistics_df["completed_points"].tail(10))
        if not statistics_df.empty and show_points
        else []
    )

    # Project Overview Section
    overview_section = html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-project-diagram me-2",
                        style={"color": "#20c997"},
                    ),
                    "Project Overview",
                ],
                className="mb-3",
            ),
            dbc.Card(
                dbc.CardBody(
                    [
                        # Progress bars
                        html.Div(
                            [
                                html.H6("Items Progress", className="mb-2"),
                                _create_progress_bar(
                                    completed_items,
                                    actual_total_items,
                                    COLOR_PALETTE["items"],
                                ),
                                html.Small(
                                    f"{completed_items:,} of {actual_total_items:,} items ({remaining_items:,} remaining)",
                                    className="text-muted d-block mt-1",
                                ),
                            ],
                            className="mb-3",
                        ),
                        html.Div(
                            [
                                html.H6("Points Progress", className="mb-2"),
                                _create_progress_bar(
                                    completed_points,
                                    actual_total_points,
                                    COLOR_PALETTE["points"],
                                )
                                if show_points
                                else html.Div(
                                    "Points tracking disabled", className="text-muted"
                                ),
                                html.Small(
                                    f"{completed_points:,.1f} of {actual_total_points:,.1f} points ({remaining_points:,.1f} remaining)",
                                    className="text-muted d-block mt-1",
                                )
                                if show_points
                                else html.Div(),
                            ],
                            className="mb-3",
                        ),
                        # Deadline
                        dbc.Alert(
                            [
                                html.I(className="fas fa-calendar-day me-2"),
                                html.Strong("Deadline: "),
                                pd.to_datetime(deadline_str).strftime("%b %d, %Y"),
                                html.Span(
                                    f" ({days_to_deadline} days remaining)",
                                    className="ms-2",
                                    style={
                                        "color": "#28a745"
                                        if days_to_deadline > 30
                                        else "#ffc107"
                                        if days_to_deadline > 7
                                        else "#dc3545"
                                    },
                                ),
                            ],
                            color="light",
                            className="mb-0",
                        ),
                    ]
                ),
                className="shadow-sm",
            ),
        ],
        className="mb-4",
    )

    # Metric Cards Row
    cards = dbc.Row(
        [
            # Items Forecast Card
            dbc.Col(
                create_enhanced_dashboard_card(
                    title="Items Forecast",
                    icon="fas fa-calendar-check",
                    icon_color=COLOR_PALETTE["items"],
                    primary_metric={
                        "value": items_pert_str,
                        "label": "PERT Completion",
                    },
                    details=[
                        {"label": "Average Method", "value": items_avg_str},
                        {"label": "Median Method", "value": items_med_str},
                        {
                            "label": "Status",
                            "value": html.Span(
                                ["On Track" if items_on_track else "At Risk"],
                                style={
                                    "color": "#28a745" if items_on_track else "#dc3545"
                                },
                            ),
                        },
                    ],
                    card_id="dashboard-items-forecast",
                ),
                xs=12,
                md=6,
                lg=3,
                className="mb-3",
            ),
            # Points Forecast Card
            dbc.Col(
                create_enhanced_dashboard_card(
                    title="Points Forecast",
                    icon="fas fa-chart-bar",
                    icon_color=COLOR_PALETTE["points"],
                    primary_metric={
                        "value": points_pert_str,
                        "label": "PERT Completion" if show_points else "Disabled",
                    },
                    details=[
                        {"label": "Average Method", "value": points_avg_str},
                        {"label": "Median Method", "value": points_med_str},
                        {
                            "label": "Status",
                            "value": html.Span(
                                ["On Track" if points_on_track else "At Risk"]
                                if show_points
                                else "—",
                                style={
                                    "color": "#28a745" if points_on_track else "#dc3545"
                                },
                            ),
                        },
                    ]
                    if show_points
                    else [],
                    card_id="dashboard-points-forecast",
                ),
                xs=12,
                md=6,
                lg=3,
                className="mb-3",
            ),
            # Items Velocity Card
            dbc.Col(
                create_enhanced_dashboard_card(
                    title="Items Velocity",
                    icon="fas fa-tachometer-alt",
                    icon_color="#6610f2",
                    primary_metric={
                        "value": f"{avg_weekly_items:.1f}",
                        "label": "Average per week",
                    },
                    sparkline_data=items_sparkline,
                    details=[
                        {
                            "label": "Median",
                            "value": f"{med_weekly_items:.1f} items/week",
                        },
                        {
                            "label": "Trend",
                            "value": html.Span(
                                [
                                    html.I(className=f"fas {items_trend['icon']} me-1"),
                                    f"{abs(items_trend['percent']):.0f}% {items_trend['direction']}",
                                ],
                                style={"color": items_trend["color"]},
                            ),
                        },
                    ],
                    card_id="dashboard-items-velocity",
                ),
                xs=12,
                md=6,
                lg=3,
                className="mb-3",
            ),
            # Points Velocity Card
            dbc.Col(
                create_enhanced_dashboard_card(
                    title="Points Velocity",
                    icon="fas fa-rocket",
                    icon_color="#fd7e14",
                    primary_metric={
                        "value": f"{avg_weekly_points:.1f}" if show_points else "N/A",
                        "label": "Average per week" if show_points else "Disabled",
                    },
                    sparkline_data=points_sparkline if show_points else None,
                    details=[
                        {
                            "label": "Median",
                            "value": f"{med_weekly_points:.1f} points/week"
                            if show_points
                            else "—",
                        },
                        {
                            "label": "Trend",
                            "value": html.Span(
                                [
                                    html.I(
                                        className=f"fas {points_trend['icon']} me-1"
                                    ),
                                    f"{abs(points_trend['percent']):.0f}% {points_trend['direction']}",
                                ],
                                style={"color": points_trend["color"]},
                            )
                            if show_points and points_trend
                            else "—",
                        },
                    ]
                    if show_points
                    else [],
                    card_id="dashboard-points-velocity",
                ),
                xs=12,
                md=6,
                lg=3,
                className="mb-3",
            ),
        ],
        className="g-3",
    )

    # Complete dashboard layout
    return html.Div(
        [
            # Header
            html.Div(
                [
                    html.H4(
                        [
                            html.I(
                                className="fas fa-tachometer-alt me-2",
                                style={"color": "#20c997"},
                            ),
                            "Project Dashboard",
                        ],
                        className="mb-1",
                    ),
                    html.P(
                        "Real-time project health and completion forecasts",
                        className="text-muted mb-3",
                    ),
                ],
                className="mb-4",
            ),
            # Project Overview
            overview_section,
            # Metric Cards
            cards,
            # Footer help
            html.Div(
                html.Small(
                    [
                        html.I(className="fas fa-info-circle me-1 text-info"),
                        "Dashboard shows PERT (optimistic + likely + pessimistic), Average, and Median forecasts. ",
                        "Sparklines show 10-week velocity trends.",
                    ],
                    className="text-muted fst-italic",
                ),
                className="mt-4 text-center",
            ),
        ]
    )
