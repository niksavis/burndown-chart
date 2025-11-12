"""
Comprehensive Project Dashboard - Modern Analytics Platform

A beautiful, comprehensive dashboard that provides deep insights into project health,
team performance, and delivery forecasts. Method-agnostic design supports any
project management approach (Scrum, Kanban, Waterfall, etc.).

Key Features:
- Executive summary with project health score
- Throughput analytics with trend analysis
- Multi-method forecasting (PERT, confidence intervals)
- Scope change tracking and quality metrics
- Team velocity and capacity planning
- Actionable insights and recommendations
"""

#######################################################################
# IMPORTS
#######################################################################
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from datetime import datetime, timedelta


from ui.style_constants import COLOR_PALETTE
from ui.tooltip_utils import create_info_tooltip


#######################################################################
# UTILITY FUNCTIONS
#######################################################################


def _safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers, returning default if denominator is zero."""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def _format_date_relative(date_str, reference_date=None):
    """Format date with relative time context."""
    if not date_str:
        return "Not set"

    try:
        target_date = pd.to_datetime(date_str)
        ref_date = reference_date or datetime.now()
        days_diff = (target_date - ref_date).days

        if days_diff < 0:
            return f"{abs(days_diff)} days overdue"
        elif days_diff == 0:
            return "Today"
        elif days_diff <= 7:
            return f"{days_diff} days"
        elif days_diff <= 30:
            return f"{days_diff // 7} weeks"
        else:
            return f"{days_diff // 30} months"
    except Exception:
        return str(date_str)


def _calculate_project_health_score(metrics):
    """Calculate overall project health score (0-100)."""
    score = 100

    # Velocity consistency (30% weight)
    velocity_cv = metrics.get("velocity_cv", 0)
    if velocity_cv > 50:
        score -= 30
    elif velocity_cv > 30:
        score -= 15

    # Schedule performance (25% weight)
    schedule_variance = metrics.get("schedule_variance_days", 0)
    if schedule_variance > 30:
        score -= 25
    elif schedule_variance > 14:
        score -= 12

    # Scope stability (20% weight)
    scope_change_rate = metrics.get("scope_change_rate", 0)
    if scope_change_rate > 20:
        score -= 20
    elif scope_change_rate > 10:
        score -= 10

    # Quality trends (15% weight)
    trend_direction = metrics.get("trend_direction", "stable")
    if trend_direction == "declining":
        score -= 15
    elif trend_direction == "improving":
        score += 5

    # Recent performance (10% weight)
    recent_change = metrics.get("recent_velocity_change", 0)
    if recent_change < -20:
        score -= 10
    elif recent_change > 20:
        score += 5

    return max(0, min(100, int(score)))


def _get_health_status(score):
    """Get health status configuration based on score."""
    if score >= 80:
        return {
            "label": "EXCELLENT",
            "color": "#28a745",
            "icon": "fa-check-circle",
            "bg_color": "rgba(40, 167, 69, 0.1)",
        }
    elif score >= 60:
        return {
            "label": "GOOD",
            "color": "#28a745",
            "icon": "fa-check-circle",
            "bg_color": "rgba(40, 167, 69, 0.1)",
        }
    elif score >= 40:
        return {
            "label": "MODERATE",
            "color": "#ffc107",
            "icon": "fa-exclamation-triangle",
            "bg_color": "rgba(255, 193, 7, 0.1)",
        }
    else:
        return {
            "label": "AT RISK",
            "color": "#dc3545",
            "icon": "fa-exclamation-triangle",
            "bg_color": "rgba(220, 53, 69, 0.1)",
        }


def _create_metric_card(
    title,
    value,
    subtitle,
    icon,
    color,
    trend=None,
    sparkline_data=None,
    tooltip_text=None,
    tooltip_id=None,
):
    """Create a standardized metric card.

    Args:
        title: Card title text
        value: Primary metric value to display
        subtitle: Descriptive text below the value
        icon: Font Awesome icon class
        color: Color for icon and value
        trend: Optional trend data dict with 'direction' and 'percent'
        sparkline_data: Optional data for sparkline visualization
        tooltip_text: Optional help text for info tooltip
        tooltip_id: Optional unique ID suffix for tooltip (required if tooltip_text provided)
    """
    trend_element = html.Div()
    if trend:
        trend_color = (
            "#28a745"
            if trend["direction"] == "up"
            else "#dc3545"
            if trend["direction"] == "down"
            else "#6c757d"
        )
        trend_icon = (
            "fa-arrow-up"
            if trend["direction"] == "up"
            else "fa-arrow-down"
            if trend["direction"] == "down"
            else "fa-minus"
        )

        trend_element = html.Div(
            [
                html.I(
                    className=f"fas {trend_icon} me-1", style={"fontSize": "0.75rem"}
                ),
                html.Span(
                    f"{abs(trend['percent']):.0f}%",
                    style={"fontSize": "0.8rem", "fontWeight": "600"},
                ),
            ],
            style={"color": trend_color},
            className="mt-1",
        )

    sparkline_element = html.Div()
    if sparkline_data and len(sparkline_data) > 1:
        sparkline_element = _create_mini_sparkline(sparkline_data, color, height=40)

    # Create title with optional tooltip
    title_content = title
    if tooltip_text and tooltip_id:
        title_content = html.Span(
            [
                title,
                html.Span(" ", style={"marginRight": "4px"}),
                create_info_tooltip(tooltip_text, tooltip_id),
            ],
            style={"display": "flex", "alignItems": "center", "gap": "4px"},
        )

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(
                                className=f"fas {icon}",
                                style={"color": color, "fontSize": "1.2rem"},
                            ),
                            html.H6(
                                title_content,
                                className="mb-1 mt-2",
                                style={"fontSize": "0.9rem", "fontWeight": "600"},
                            ),
                            html.Div(
                                value,
                                className="h4 mb-0",
                                style={"color": color, "fontWeight": "bold"},
                            ),
                            html.Small(subtitle, className="text-muted"),
                            trend_element,
                            sparkline_element,
                        ]
                    )
                ],
                className="p-3",
            )
        ],
        className="h-100 shadow-sm border-0",
    )


def _create_mini_sparkline(data, color, height=20):
    """Create a mini CSS sparkline."""
    if not data or len(data) < 2:
        return html.Div()

    max_val = max(data) if max(data) > 0 else 1
    normalized = [v / max_val for v in data]

    bars = []
    for i, val in enumerate(normalized):
        bar_height = max(val * height, 2)
        opacity = 0.4 + (i / len(normalized)) * 0.6

        bars.append(
            html.Div(
                style={
                    "width": "5px",
                    "height": f"{bar_height}px",
                    "backgroundColor": color,
                    "opacity": opacity,
                    "borderRadius": "2px",
                }
            )
        )

    return html.Div(
        bars,
        className="d-flex align-items-end justify-content-center mt-2",
        style={"height": f"{height}px", "gap": "3px", "minWidth": "80px"},
    )


def _create_progress_ring(percentage, color, size=60):
    """Create a circular progress indicator using Bootstrap progress bar styled as circle."""
    return html.Div(
        [
            # Circular progress using CSS transforms and border
            html.Div(
                [
                    html.Div(
                        f"{percentage:.0f}%",
                        style={
                            "position": "absolute",
                            "top": "50%",
                            "left": "50%",
                            "transform": "translate(-50%, -50%)",
                            "fontSize": "0.85rem",
                            "fontWeight": "bold",
                            "color": color,
                            "textAlign": "center",
                        },
                    )
                ],
                style={
                    "width": f"{size}px",
                    "height": f"{size}px",
                    "borderRadius": "50%",
                    "border": "4px solid #e9ecef",
                    "borderTop": f"4px solid {color}",
                    "borderRight": f"4px solid {color}"
                    if percentage > 25
                    else "4px solid #e9ecef",
                    "borderBottom": f"4px solid {color}"
                    if percentage > 50
                    else "4px solid #e9ecef",
                    "borderLeft": f"4px solid {color}"
                    if percentage > 75
                    else "4px solid #e9ecef",
                    "position": "relative",
                    "transform": "rotate(-90deg)",
                    "transition": "all 0.3s ease",
                },
            )
        ],
        style={
            "display": "inline-block",
            "transform": "rotate(90deg)",  # Counter-rotate the container to fix text orientation
        },
    )


#######################################################################
# MAIN DASHBOARD SECTIONS
#######################################################################


def _create_executive_summary(statistics_df, settings, forecast_data):
    """Create executive summary section with key project health indicators."""
    # Calculate key metrics
    # NOTE: settings["total_items"] and settings["total_points"] NOW represent the total scope
    # at the START of the selected data window (e.g., 317 items 16 weeks ago)
    # This matches the calculation in ui/layout.py serve_layout() and callbacks/settings.py slider callback
    total_items = settings.get("total_items", 0)
    total_points = settings.get("total_points", 0)
    deadline = settings.get("deadline")

    # Calculate completed items from the FILTERED statistics DataFrame
    # This represents work completed WITHIN the selected time window
    completed_items = (
        statistics_df["completed_items"].sum() if not statistics_df.empty else 0
    )
    completed_points = (
        statistics_df["completed_points"].sum() if not statistics_df.empty else 0
    )

    completion_percentage = _safe_divide(completed_items, total_items) * 100
    points_percentage = (
        _safe_divide(completed_points, total_points) * 100 if total_points > 0 else 0
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

    health_metrics = {
        "velocity_cv": velocity_cv,
        "schedule_variance_days": schedule_variance,
        "scope_change_rate": scope_change_rate,
        "trend_direction": trend_direction,
        "recent_velocity_change": recent_velocity_change,
    }

    health_score = _calculate_project_health_score(health_metrics)
    health_status = _get_health_status(health_score)

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
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            # Health Score
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            _create_progress_ring(
                                                health_score, health_status["color"], 80
                                            ),
                                            html.H5(
                                                health_status["label"],
                                                className="mt-2 mb-0",
                                                style={"color": health_status["color"]},
                                            ),
                                            html.Small(
                                                "Overall Health", className="text-muted"
                                            ),
                                        ],
                                        className="text-center",
                                    )
                                ],
                                width=12,
                                md=3,
                            ),
                            # Key Metrics
                            dbc.Col(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Div(
                                                        [
                                                            html.H5(
                                                                f"{completion_percentage:.0f}%",
                                                                className="mb-0",
                                                            ),
                                                            html.Small(
                                                                "Items Complete",
                                                                className="text-muted",
                                                            ),
                                                            html.Div(
                                                                f"{completed_items:,} / {total_items:,}",
                                                                style={
                                                                    "fontSize": "0.8rem",
                                                                    "color": COLOR_PALETTE[
                                                                        "items"
                                                                    ],
                                                                },
                                                            ),
                                                        ]
                                                    )
                                                ],
                                                width=6,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Div(
                                                        [
                                                            html.H5(
                                                                f"{points_percentage:.0f}%",
                                                                className="mb-0",
                                                            ),
                                                            html.Small(
                                                                "Points Complete",
                                                                className="text-muted",
                                                            ),
                                                            html.Div(
                                                                f"{completed_points:,.0f} / {total_points:,.0f}",
                                                                style={
                                                                    "fontSize": "0.8rem",
                                                                    "color": COLOR_PALETTE[
                                                                        "points"
                                                                    ],
                                                                },
                                                            ),
                                                        ]
                                                    )
                                                    if total_points > 0
                                                    else html.Div(
                                                        [
                                                            html.H5(
                                                                "N/A",
                                                                className="mb-0 text-muted",
                                                            ),
                                                            html.Small(
                                                                "Points Disabled",
                                                                className="text-muted",
                                                            ),
                                                        ]
                                                    )
                                                ],
                                                width=6,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    # Timeline info
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-calendar-alt me-2",
                                                style={"color": "#6c757d"},
                                            ),
                                            html.Strong("Deadline: "),
                                            html.Span(
                                                _format_date_relative(deadline)
                                                if deadline
                                                else "Not set"
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-chart-line me-2",
                                                style={"color": "#6c757d"},
                                            ),
                                            html.Strong("Forecast: "),
                                            html.Span(
                                                _format_date_relative(
                                                    forecast_data.get("completion_date")
                                                )
                                                if forecast_data.get("completion_date")
                                                else "Calculating..."
                                            ),
                                        ]
                                    ),
                                ],
                                width=12,
                                md=9,
                            ),
                        ]
                    ),
                ]
            )
        ],
        className="mb-4 shadow-sm border-0",
        style={"background": health_status["bg_color"]},
    )


def _create_throughput_section(statistics_df, forecast_data):
    """Create throughput analytics section.

    Note: statistics_df is already filtered by data_points_count in the callback,
    so we use the entire dataframe for calculations.
    """
    if statistics_df.empty:
        return html.Div()

    # Use ALL the filtered data (already filtered by data_points_count in callback)
    # Calculate throughput metrics from the entire filtered dataset
    avg_items = statistics_df["completed_items"].mean()
    avg_points = statistics_df["completed_points"].mean()

    # Calculate trends by comparing older vs recent halves of filtered data
    items_trend = None
    points_trend = None

    if len(statistics_df) >= 8:
        # Split into older and recent halves
        mid_point = len(statistics_df) // 2
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
    else:
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
                            _create_metric_card(
                                "Items per Week",
                                f"{avg_items:.1f}",
                                "Average delivery rate",
                                "fa-tasks",
                                COLOR_PALETTE["items"],
                                trend=items_trend,
                                sparkline_data=list(statistics_df["completed_items"]),
                                tooltip_text="Average number of work items completed per week. Calculated using the corrected velocity method that counts actual weeks with data (not date range spans).",
                                tooltip_id="throughput-items-per-week",
                            )
                        ],
                        width=12,
                        md=6,
                        lg=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            _create_metric_card(
                                "Points per Week",
                                f"{avg_points:.1f}",
                                "Average story points",
                                "fa-chart-bar",
                                COLOR_PALETTE["points"],
                                trend=points_trend,
                                sparkline_data=list(statistics_df["completed_points"]),
                                tooltip_text="Average story points completed per week. Story points represent work complexity and effort. Higher values indicate faster delivery of larger work items.",
                                tooltip_id="throughput-points-per-week",
                            )
                        ],
                        width=12,
                        md=6,
                        lg=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            _create_metric_card(
                                "Avg Cycle Time",
                                f"{_safe_divide(7, avg_items) if avg_items > 0 else 0:.1f}d",
                                "Days per item",
                                "fa-clock",
                                "#17a2b8",
                                sparkline_data=None,
                                tooltip_text="Average time to complete one work item. Calculated as 7 days ÷ items per week. Lower values indicate faster throughput and shorter feedback cycles.",
                                tooltip_id="throughput-cycle-time",
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


def _create_forecast_section(pert_data, confidence_data):
    """Create forecasting section with multiple prediction methods."""
    current_date = datetime.now()

    # Format forecast dates
    pert_date = (
        current_date + timedelta(days=pert_data.get("pert_time_items", 0))
    ).strftime("%b %d, %Y")
    optimistic_date = (
        current_date + timedelta(days=confidence_data.get("ci_50", 0))
    ).strftime("%b %d, %Y")
    pessimistic_date = (
        current_date + timedelta(days=confidence_data.get("ci_95", 0))
    ).strftime("%b %d, %Y")

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-crystal-ball me-2", style={"color": "#6610f2"}
                    ),
                    "Delivery Forecast",
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.I(
                                                className="fas fa-calendar-check",
                                                style={
                                                    "color": "#6610f2",
                                                    "fontSize": "1.2rem",
                                                },
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "Expected Completion",
                                                        style={
                                                            "fontSize": "0.9rem",
                                                            "fontWeight": "600",
                                                        },
                                                    ),
                                                    create_info_tooltip(
                                                        "expected-completion-info",
                                                        "Calculated using PERT three-point estimation: (Optimistic + 4×Most_Likely + Pessimistic) ÷ 6. "
                                                        "This weighted average emphasizes the most likely scenario (4x weight) while accounting for best/worst cases from your historical velocity data.",
                                                    ),
                                                ],
                                                className="mb-1 mt-2 d-flex align-items-center gap-1",
                                            ),
                                            html.Div(
                                                pert_date,
                                                className="h4 mb-0",
                                                style={
                                                    "color": "#6610f2",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            html.Small(
                                                "Weighted estimate based on historical velocity",
                                                className="text-muted",
                                            ),
                                        ],
                                        className="p-3",
                                    )
                                ],
                                className="h-100 shadow-sm border-0",
                            )
                        ],
                        width=12,
                        md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.I(
                                                className="fas fa-chart-line",
                                                style={
                                                    "color": "#17a2b8",
                                                    "fontSize": "1.2rem",
                                                },
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "Confidence Intervals",
                                                        style={
                                                            "fontSize": "0.9rem",
                                                            "fontWeight": "600",
                                                        },
                                                    ),
                                                    create_info_tooltip(
                                                        "confidence-intervals-info",
                                                        "Statistical probability ranges based on velocity variability. "
                                                        "50%: 50th percentile (median) - the PERT forecast itself. "
                                                        "95%: 95th percentile - conservative estimate with 1.65σ buffer. "
                                                        "Wider spread indicates higher velocity uncertainty.",
                                                    ),
                                                ],
                                                className="mb-1 mt-2 d-flex align-items-center gap-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                "50%: ",
                                                                className="text-muted",
                                                                style={
                                                                    "fontSize": "0.85rem"
                                                                },
                                                            ),
                                                            html.Span(
                                                                optimistic_date,
                                                                style={
                                                                    "color": "#28a745",
                                                                    "fontSize": "1.25rem",
                                                                    "fontWeight": "bold",
                                                                },
                                                            ),
                                                        ],
                                                        className="mb-2",
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                "95%: ",
                                                                className="text-muted",
                                                                style={
                                                                    "fontSize": "0.85rem"
                                                                },
                                                            ),
                                                            html.Span(
                                                                pessimistic_date,
                                                                style={
                                                                    "color": "#dc3545",
                                                                    "fontSize": "1.25rem",
                                                                    "fontWeight": "bold",
                                                                },
                                                            ),
                                                        ]
                                                    ),
                                                ],
                                                className="mb-0",
                                            ),
                                            html.Small(
                                                "Range represents delivery confidence levels",
                                                className="text-muted",
                                            ),
                                        ],
                                        className="p-3",
                                    )
                                ],
                                className="h-100 shadow-sm border-0",
                            )
                        ],
                        width=12,
                        md=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.I(
                                                className="fas fa-bullseye",
                                                style={
                                                    "color": "#28a745"
                                                    if confidence_data.get(
                                                        "deadline_probability", 75
                                                    )
                                                    >= 70
                                                    else "#ffc107"
                                                    if confidence_data.get(
                                                        "deadline_probability", 75
                                                    )
                                                    >= 40
                                                    else "#dc3545",
                                                    "fontSize": "1.2rem",
                                                },
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "On-Track Probability",
                                                        style={
                                                            "fontSize": "0.9rem",
                                                            "fontWeight": "600",
                                                        },
                                                    ),
                                                    create_info_tooltip(
                                                        "on-track-probability-info",
                                                        "Statistical probability of meeting deadline using normal distribution. "
                                                        "Calculated via Z-score: (deadline_days - expected_days) / forecast_std_dev. "
                                                        "Based on how many standard deviations your deadline is from expected completion, adjusted for velocity consistency.",
                                                    ),
                                                ],
                                                className="mb-1 mt-2 d-flex align-items-center gap-1",
                                            ),
                                            html.Div(
                                                f"{confidence_data.get('deadline_probability', 75):.0f}%",
                                                className="h4 mb-0",
                                                style={
                                                    "color": "#28a745"
                                                    if confidence_data.get(
                                                        "deadline_probability", 75
                                                    )
                                                    >= 70
                                                    else "#ffc107"
                                                    if confidence_data.get(
                                                        "deadline_probability", 75
                                                    )
                                                    >= 40
                                                    else "#dc3545",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            html.Small(
                                                "Chance of meeting deadline",
                                                className="text-muted",
                                            ),
                                            html.Div(
                                                _create_progress_ring(
                                                    confidence_data.get(
                                                        "deadline_probability", 75
                                                    ),
                                                    "#28a745"
                                                    if confidence_data.get(
                                                        "deadline_probability", 75
                                                    )
                                                    >= 70
                                                    else "#ffc107"
                                                    if confidence_data.get(
                                                        "deadline_probability", 75
                                                    )
                                                    >= 40
                                                    else "#dc3545",
                                                    70,
                                                ),
                                                className="mt-3",
                                            ),
                                        ],
                                        className="p-3",
                                    )
                                ],
                                className="h-100 shadow-sm border-0",
                            )
                        ],
                        width=12,
                        md=4,
                        className="mb-3",
                    ),
                ]
            ),
        ],
        className="mb-4",
    )


def _create_recent_activity_section(statistics_df):
    """Create compact recent performance section showing completed items clearly.

    Note: This section ALWAYS shows the last 4 weeks of data, regardless of
    the data_points_count slider. This provides a consistent "current status" view.
    Other dashboard sections respect the data_points_count filter.
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
                className="mb-3",
            ),
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            # Items Row
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.H3(
                                                        str(int(total_items_completed)),
                                                        className="mb-0 text-center",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ]
                                                        },
                                                    ),
                                                    html.P(
                                                        "Items Completed",
                                                        className="text-muted text-center mb-0",
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=12,
                                        md=4,
                                        className="text-center mb-3 mb-md-0",
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.H4(
                                                        f"{avg_items_weekly:.1f}",
                                                        className="mb-0 text-center",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ]
                                                        },
                                                    ),
                                                    html.P(
                                                        "Items/Week Avg",
                                                        className="text-muted text-center mb-0",
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=12,
                                        md=4,
                                        className="text-center mb-3 mb-md-0",
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        _create_mini_sparkline(
                                                            items_sparkline_values,
                                                            COLOR_PALETTE["items"],
                                                        ),
                                                        className="d-flex justify-content-center mb-1",
                                                    ),
                                                    html.P(
                                                        "Items Trend",
                                                        className="text-muted text-center mb-0 small",
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=12,
                                        md=4,
                                        className="text-center mb-3 mb-md-0",
                                    ),
                                ],
                                className="align-items-center mb-3",
                            ),
                            # Divider
                            html.Hr(className="my-2") if has_points_data else None,
                            # Points Row (only show if points data exists)
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.H3(
                                                        f"{total_points_completed:.0f}",
                                                        className="mb-0 text-center",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "points"
                                                            ]
                                                        },
                                                    ),
                                                    html.P(
                                                        "Points Completed",
                                                        className="text-muted text-center mb-0",
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=12,
                                        md=4,
                                        className="text-center mb-3 mb-md-0",
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.H4(
                                                        f"{avg_points_weekly:.1f}",
                                                        className="mb-0 text-center",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "points"
                                                            ]
                                                        },
                                                    ),
                                                    html.P(
                                                        "Points/Week Avg",
                                                        className="text-muted text-center mb-0",
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=12,
                                        md=4,
                                        className="text-center mb-3 mb-md-0",
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        _create_mini_sparkline(
                                                            points_sparkline_values,
                                                            COLOR_PALETTE["points"],
                                                        ),
                                                        className="d-flex justify-content-center mb-1",
                                                    ),
                                                    html.P(
                                                        "Points Trend",
                                                        className="text-muted text-center mb-0 small",
                                                    ),
                                                ]
                                            )
                                        ],
                                        width=12,
                                        md=4,
                                        className="text-center",
                                    ),
                                ],
                                className="align-items-center",
                            )
                            if has_points_data
                            else None,
                        ]
                    )
                ],
                className="shadow-sm border-0",
            ),
        ],
        className="mb-4",
    )


def _create_quality_scope_section(statistics_df, settings):
    """Create quality and scope tracking section."""
    if statistics_df.empty:
        return html.Div()

    # Calculate scope metrics with time frame context
    scope_metrics = []

    if "created_items" in statistics_df.columns:
        total_created = statistics_df["created_items"].sum()
        total_completed = statistics_df["completed_items"].sum()
        scope_growth_rate = _safe_divide(total_created, total_completed) * 100

        # Get date range for context
        if "date" in statistics_df.columns and not statistics_df.empty:
            start_date = statistics_df["date"].min()
            end_date = statistics_df["date"].max()
            date_range = f"{pd.to_datetime(start_date).strftime('%b %d, %Y')} - {pd.to_datetime(end_date).strftime('%b %d, %Y')}"
            weeks_count = len(statistics_df)
        else:
            date_range = "tracked period"
            weeks_count = len(statistics_df)

        scope_metrics.extend(
            [
                {
                    "label": "New Items Added",
                    "value": f"{total_created:,}",
                    "color": "#fd7e14",
                    "icon": "fa-plus-circle",
                    "tooltip": f"Total new work items added to project backlog during {date_range} ({weeks_count} weeks). This represents scope expansion - new features, bugs, or tasks discovered after project start. Monitor this to identify uncontrolled scope growth.",
                },
                {
                    "label": "Scope Growth Rate",
                    "value": f"{scope_growth_rate:.1f}%",
                    "color": "#6610f2",
                    "icon": "fa-chart-line",
                    "tooltip": f"Ratio of new items added vs items completed during {date_range}. Shows {total_created:,} new items added while {total_completed:,} completed. Healthy projects: <20% (balanced scope). Warning: 20-50% (scope creep). Critical: >50% (uncontrolled growth). Your value: {scope_growth_rate:.1f}%",
                },
            ]
        )

    # Calculate quality metrics
    if len(statistics_df) >= 4:
        # Velocity stability
        velocity_std = statistics_df["completed_items"].std()
        velocity_mean = statistics_df["completed_items"].mean()
        velocity_cv = _safe_divide(velocity_std, velocity_mean) * 100

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
                                    dbc.CardHeader(
                                        [
                                            html.I(
                                                className="fas fa-expand-arrows-alt me-2"
                                            ),
                                            "Scope Management",
                                            html.Span(
                                                " ", style={"marginRight": "8px"}
                                            ),
                                            create_info_tooltip(
                                                "Track scope changes and backlog growth. Shows ratio of new items added vs completed, helping identify scope creep early. Healthy projects maintain balance between scope growth and completion rate.",
                                                "scope-management-card",
                                            ),
                                        ],
                                        style={
                                            "display": "flex",
                                            "alignItems": "center",
                                        },
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
                                                            html.H5(
                                                                metric["value"],
                                                                style={
                                                                    "color": metric[
                                                                        "color"
                                                                    ]
                                                                },
                                                                className="mb-0",
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
                                ],
                                className="h-100 shadow-sm border-0",
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
                                    dbc.CardHeader(
                                        [
                                            html.I(
                                                className="fas fa-check-circle me-2"
                                            ),
                                            "Quality Indicators",
                                            html.Span(
                                                " ", style={"marginRight": "8px"}
                                            ),
                                            create_info_tooltip(
                                                "Measures delivery predictability and consistency. High values (80%+) indicate stable, reliable team performance. Use these metrics to assess forecast accuracy and process maturity.",
                                                "quality-indicators-card",
                                            ),
                                        ],
                                        style={
                                            "display": "flex",
                                            "alignItems": "center",
                                        },
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
                                                            html.H5(
                                                                metric["value"],
                                                                style={
                                                                    "color": metric[
                                                                        "color"
                                                                    ]
                                                                },
                                                                className="mb-0",
                                                            ),
                                                        ],
                                                        className="text-center p-2",
                                                    )
                                                    for metric in quality_metrics
                                                ]
                                            )
                                        ]
                                    ),
                                ],
                                className="h-100 shadow-sm border-0",
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


def _create_insights_section(statistics_df, settings):
    """Create actionable insights section.

    Note: statistics_df is already filtered by data_points_count in the callback.
    For velocity comparison, we split the filtered data into two halves:
    - First half: "historical" baseline velocity
    - Second half: "recent" velocity trend
    """
    insights = []

    if not statistics_df.empty:
        # Velocity insights - compare first half vs second half of filtered data
        mid_point = len(statistics_df) // 2
        if mid_point > 0:
            recent_velocity = statistics_df.iloc[mid_point:]["completed_items"].mean()
            historical_velocity = statistics_df.iloc[:mid_point][
                "completed_items"
            ].mean()
        else:
            # Fallback if dataset is too small to split
            recent_velocity = statistics_df["completed_items"].mean()
            historical_velocity = recent_velocity

        if recent_velocity > historical_velocity * 1.1:
            insights.append(
                {
                    "type": "positive",
                    "title": "🚀 Accelerating Delivery",
                    "message": f"Team velocity increased {((recent_velocity / historical_velocity - 1) * 100):.0f}% in recent weeks",
                    "action": "Consider taking on additional scope or bringing forward deliverables",
                }
            )
        elif recent_velocity < historical_velocity * 0.9:
            insights.append(
                {
                    "type": "warning",
                    "title": "⚠️ Velocity Decline",
                    "message": f"Team velocity decreased {((1 - recent_velocity / historical_velocity) * 100):.0f}% recently",
                    "action": "Review team capacity, blockers, and scope complexity",
                }
            )

        # Scope change insights
        if "created_items" in statistics_df.columns:
            scope_growth = statistics_df["created_items"].sum()
            scope_completion = statistics_df["completed_items"].sum()

            if scope_growth > scope_completion * 0.2:
                insights.append(
                    {
                        "type": "warning",
                        "title": "📈 High Scope Growth",
                        "message": f"New items ({scope_growth}) represent {(scope_growth / scope_completion * 100):.0f}% of completed work",
                        "action": "Consider scope prioritization and change management processes",
                    }
                )
            elif scope_growth > 0:
                insights.append(
                    {
                        "type": "info",
                        "title": "📊 Active Scope Management",
                        "message": f"Moderate scope growth ({scope_growth} new items) indicates healthy project evolution",
                        "action": "Continue monitoring scope changes and stakeholder feedback",
                    }
                )

        # Consistency insights
        velocity_cv = (
            (
                statistics_df["completed_items"].std()
                / statistics_df["completed_items"].mean()
                * 100
            )
            if statistics_df["completed_items"].mean() > 0
            else 0
        )

        if velocity_cv < 20:
            insights.append(
                {
                    "type": "positive",
                    "title": "🎯 Predictable Delivery",
                    "message": f"Low velocity variation ({velocity_cv:.0f}%) indicates predictable delivery rhythm",
                    "action": "Maintain current practices and use predictability for better planning",
                }
            )
        elif velocity_cv > 50:
            insights.append(
                {
                    "type": "warning",
                    "title": "📊 Inconsistent Velocity",
                    "message": f"High velocity variation ({velocity_cv:.0f}%) suggests unpredictable delivery",
                    "action": "Investigate causes: story sizing, blockers, team availability, or external dependencies",
                }
            )

        # Throughput efficiency insights - compare first half vs second half of filtered data
        if len(statistics_df) >= 8:
            mid_point = len(statistics_df) // 2
            recent_items = statistics_df.iloc[mid_point:]["completed_items"].sum()
            prev_items = statistics_df.iloc[:mid_point]["completed_items"].sum()

            if recent_items > prev_items * 1.2:
                insights.append(
                    {
                        "type": "positive",
                        "title": "📈 Increasing Throughput",
                        "message": f"Recent 4-week throughput ({recent_items} items) exceeded previous period by {((recent_items / prev_items - 1) * 100):.0f}%",
                        "action": "Analyze what's working well and consider scaling successful practices",
                    }
                )

    if not insights:
        insights.append(
            {
                "type": "info",
                "title": "✅ Stable Performance",
                "message": "Project metrics are within normal ranges - no immediate concerns detected",
                "action": "Continue current practices and monitor for changes in upcoming weeks",
            }
        )

    insight_cards = []
    for insight in insights:
        icon_map = {
            "positive": "fa-thumbs-up",
            "warning": "fa-exclamation-triangle",
            "info": "fa-info-circle",
        }
        color_map = {"positive": "#28a745", "warning": "#ffc107", "info": "#17a2b8"}

        insight_cards.append(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className=f"fas {icon_map[insight['type']]} me-2",
                                        style={"color": color_map[insight["type"]]},
                                    ),
                                    html.Strong(insight["title"]),
                                ],
                                className="mb-2",
                            ),
                            html.P(insight["message"], className="mb-2"),
                            html.Small(
                                insight["action"], className="text-muted fst-italic"
                            ),
                        ]
                    )
                ],
                className="mb-2 shadow-sm border-0",
            )
        )

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-lightbulb me-2", style={"color": "#fd7e14"}
                    ),
                    "Actionable Insights",
                ],
                className="mb-3",
            ),
            html.Div(insight_cards),
        ],
        className="mb-4",
    )


#######################################################################
# MAIN DASHBOARD FUNCTION
#######################################################################


def create_comprehensive_dashboard(
    statistics_df,
    statistics_df_unfiltered,
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
    additional_context=None,
):
    """
    Create a comprehensive project dashboard with all available metrics.

    This dashboard provides:
    - Executive summary with project health scoring
    - Throughput analytics with trend analysis
    - Multi-method forecasting with confidence intervals
    - Actionable insights and recommendations

    Args:
        statistics_df: DataFrame with filtered project statistics (respects data_points_count slider)
        statistics_df_unfiltered: DataFrame with ALL project statistics (for Recent Completions)
        pert_time_items: PERT forecast time for items
        pert_time_points: PERT forecast time for points
        avg_weekly_items: Average weekly items completed
        avg_weekly_points: Average weekly points completed
        med_weekly_items: Median weekly items completed
        med_weekly_points: Median weekly points completed
        days_to_deadline: Days until project deadline
        total_items: Total items in project scope
        total_points: Total points in project scope
        deadline_str: Deadline date string
        show_points: Whether to show points-based metrics
        additional_context: Optional additional metrics and context

    Returns:
        html.Div: Complete dashboard layout
    """
    # Prepare forecast data
    forecast_data = {
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "velocity_cv": 25,  # Default coefficient of variation
        "schedule_variance_days": max(0, pert_time_items - days_to_deadline)
        if pert_time_items
        else 0,
        "completion_date": (datetime.now() + timedelta(days=pert_time_items)).strftime(
            "%Y-%m-%d"
        )
        if pert_time_items
        else None,
    }

    # Calculate velocity coefficient of variation if we have enough data
    if not statistics_df.empty and len(statistics_df) >= 4:
        velocity_std = statistics_df["completed_items"].std()
        velocity_mean = statistics_df["completed_items"].mean()
        if velocity_mean > 0:
            forecast_data["velocity_cv"] = (velocity_std / velocity_mean) * 100

    # Prepare confidence intervals
    confidence_data = {
        "ci_50": max(0, pert_time_items - 7) if pert_time_items else 0,
        "ci_80": pert_time_items if pert_time_items else 0,
        "ci_95": pert_time_items + 14 if pert_time_items else 0,
        "deadline_probability": max(
            0,
            min(
                100,
                100 - ((pert_time_items - days_to_deadline) / days_to_deadline * 50),
            ),
        )
        if pert_time_items and days_to_deadline > 0
        else 75,
    }

    # Prepare settings for sections
    settings = {
        "total_items": total_items,
        "total_points": total_points,
        "deadline": deadline_str,
        "show_points": show_points,
    }

    return html.Div(
        [
            # Page header
            # Executive Summary
            _create_executive_summary(statistics_df, settings, forecast_data),
            # Throughput Analytics
            _create_throughput_section(statistics_df, forecast_data),
            # Forecast Section
            _create_forecast_section(forecast_data, confidence_data),
            # Recent Activity Section - uses unfiltered data for consistent 4-week view
            _create_recent_activity_section(statistics_df_unfiltered),
            # Quality & Scope Section
            _create_quality_scope_section(statistics_df, settings),
            # Insights Section
            _create_insights_section(statistics_df, settings),
        ],
        className="dashboard-comprehensive",
    )
