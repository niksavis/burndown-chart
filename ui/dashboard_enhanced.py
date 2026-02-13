"""
Project Dashboard - Comprehensive Project Management Analytics

A modern, method-agnostic dashboard providing comprehensive project insights:
- Real-time throughput and velocity metrics
- Multi-dimensional forecasting (PERT, trends, confidence intervals)
- Scope change tracking and quality indicators
- Team performance analytics and capacity planning
- Actionable insights and recommendations

Designed for any project management methodology (Scrum, Kanban, Waterfall, etc.)
"""

#######################################################################
# IMPORTS
#######################################################################
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from datetime import datetime, timedelta
from scipy import stats

from ui.style_constants import COLOR_PALETTE


#######################################################################
# STATISTICAL HELPER FUNCTIONS
#######################################################################


def _calculate_velocity_statistics(statistics_df, metric_type="items"):
    """Calculate comprehensive velocity statistics."""
    if statistics_df.empty:
        return {
            "mean": 0,
            "median": 0,
            "std_dev": 0,
            "cv": 0,
            "recent_avg": 0,
            "recent_change": 0,
            "sparkline_data": [],
        }

    col_name = f"completed_{metric_type}"
    if col_name not in statistics_df.columns:
        return {
            "mean": 0,
            "median": 0,
            "std_dev": 0,
            "cv": 0,
            "recent_avg": 0,
            "recent_change": 0,
            "sparkline_data": [],
        }

    data = statistics_df[col_name]
    mean_vel = data.mean()
    std_dev = data.std()
    cv = (std_dev / mean_vel * 100) if mean_vel > 0 else 0

    # Recent performance (last 4 weeks)
    recent_avg = data.tail(4).mean() if len(data) >= 4 else mean_vel
    historical_avg = data.head(-4).mean() if len(data) > 4 else mean_vel
    recent_change = (
        ((recent_avg - historical_avg) / historical_avg * 100)
        if historical_avg > 0
        else 0
    )

    return {
        "mean": mean_vel,
        "median": data.median(),
        "std_dev": std_dev,
        "cv": cv,
        "recent_avg": recent_avg,
        "recent_change": recent_change,
        "sparkline_data": list(data.tail(10)),
    }


def _calculate_confidence_intervals(
    pert_forecast_days, velocity_mean, velocity_std, remaining_work
):
    """
    Calculate forecast confidence intervals using statistical distribution.

    IMPORTANT: These are TRUE STATISTICAL CONFIDENCE INTERVALS based on velocity variance,
    NOT the optimistic/pessimistic dates from the burndown chart (which use best/worst N weeks).

    Mathematical Basis:
    - Uses normal distribution approximation
    - Calculates coefficient of variation (CV = std_dev / mean) to measure velocity uncertainty
    - Applies standard statistical confidence levels (percentiles)

    Confidence Interval Calculations (One-Sided Percentiles):
    - 50th percentile: PERT forecast (median estimate)
      This is the expected completion date with 50% probability
      Formula: pert_days

    - 80th percentile: PERT forecast + (0.84σ) → 80% chance of completion by this date
      Common project management buffer level
      Formula: pert_days + (0.84 × forecast_std)

    - 95th percentile: PERT forecast + (1.65σ) → 95% chance of completion by this date
      Conservative estimate with substantial buffer
      Formula: pert_days + (1.65 × forecast_std)

    Interpretation:
    - 50%: Median forecast - 50% probability of completing by this date
    - 80%: Good confidence - 80% probability of completing by this date
    - 95%: High confidence - 95% probability of completing by this date (safe estimate)
    - Wider spread between percentiles = higher velocity uncertainty
    - These are DIFFERENT from optimistic/pessimistic on burndown chart!

    Args:
        pert_forecast_days: Expected completion days from PERT calculation
        velocity_mean: Average historical velocity (items/week)
        velocity_std: Standard deviation of historical velocity
        remaining_work: Remaining items/points to complete

    Returns:
        dict with ci_50, ci_80, ci_95 (days to completion)
    """
    if velocity_mean == 0 or velocity_std == 0:
        return {
            "ci_50": pert_forecast_days,
            "ci_80": pert_forecast_days,
            "ci_95": pert_forecast_days,
        }

    # Coefficient of variation (CV = std_dev / mean)
    cv = velocity_std / velocity_mean

    # Calculate forecast standard deviation
    # This represents the uncertainty in the forecast due to velocity variability
    forecast_std = cv * pert_forecast_days

    # Calculate confidence intervals using standard normal distribution percentiles
    # These are one-sided "completion by" dates, not two-sided ranges
    ci_50 = pert_forecast_days  # 50th percentile (median)
    ci_80 = pert_forecast_days + (0.84 * forecast_std)  # 80th percentile (z=0.84)
    ci_95 = pert_forecast_days + (1.65 * forecast_std)  # 95th percentile (z=1.65)

    return {"ci_50": max(0, ci_50), "ci_80": max(0, ci_80), "ci_95": max(0, ci_95)}


def _calculate_deadline_probability(
    days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
):
    """
    Calculate probability of meeting deadline using normal distribution.

    This is the "On-Track Probability" shown on forecast cards.

    Mathematical Basis:
    - Assumes velocity follows a normal (bell curve) distribution
    - Uses standard deviation of historical velocity to estimate forecast uncertainty
    - Calculates Z-score: how many standard deviations the deadline is from expected completion
    - Converts Z-score to probability using cumulative distribution function (CDF)

    Calculation Steps:
    1. Calculate coefficient of variation: CV = velocity_std / velocity_mean
    2. Estimate forecast uncertainty: forecast_std = CV × pert_forecast_days
    3. Calculate Z-score: z = (deadline_days - pert_forecast_days) / forecast_std
    4. Convert to probability: P = CDF(z) × 100%

    Interpretation:
    - 100%: Deadline is well after expected completion → Very likely to meet deadline
    - 80%: Deadline is after expected completion → Good chance of meeting deadline
    - 50%: Deadline equals expected completion → Coin flip odds
    - 20%: Deadline is before expected completion → Risky, likely to miss
    - 0%: Deadline is well before expected completion → Very unlikely to meet

    Example:
    - Expected completion: 100 days
    - Deadline: 110 days (10 days buffer)
    - Forecast std dev: 15 days
    - Z-score: (110-100)/15 = 0.67
    - Probability: CDF(0.67) = ~75% chance of meeting deadline

    Args:
        days_to_deadline: Days remaining until deadline
        pert_forecast_days: Expected completion days from PERT
        velocity_std: Standard deviation of velocity
        velocity_mean: Average velocity

    Returns:
        float: Probability (0-100%) of meeting the deadline
    """
    if velocity_mean == 0:
        return 50.0

    # Calculate coefficient of variation and forecast standard deviation
    cv = velocity_std / velocity_mean
    forecast_std_days = cv * pert_forecast_days

    # Edge case: deterministic (no variance)
    if forecast_std_days == 0:
        return 100.0 if days_to_deadline >= pert_forecast_days else 0.0

    # Calculate Z-score: how many standard deviations the deadline is from expected
    z = (days_to_deadline - pert_forecast_days) / forecast_std_days

    # Convert to probability using normal CDF
    probability = stats.norm.cdf(z) * 100

    return max(0, min(100, probability))


def _assess_project_health(
    velocity_cv,
    days_to_deadline,
    pert_forecast_days,
    recent_velocity_change,
    capacity_gap_percent,
):
    """Assess overall project health and return structured score."""
    factors = []

    # Factor 1: Velocity Predictability
    if velocity_cv < 25:
        factors.append(
            {"name": "Velocity Predictable", "status": "good", "icon": "[OK]"}
        )
    elif velocity_cv < 40:
        factors.append(
            {"name": "Velocity Moderately Stable", "status": "warning", "icon": "[!]"}
        )
    else:
        factors.append(
            {"name": "Velocity Unpredictable", "status": "bad", "icon": "[X]"}
        )

    # Factor 2: Schedule Status
    schedule_delta = pert_forecast_days - days_to_deadline
    if schedule_delta <= 0:
        factors.append({"name": "On Schedule", "status": "good", "icon": "[OK]"})
    elif schedule_delta <= 14:
        factors.append({"name": "Slightly Behind", "status": "warning", "icon": "[!]"})
    else:
        factors.append({"name": "Behind Schedule", "status": "bad", "icon": "[X]"})

    # Factor 3: Velocity Trend
    if recent_velocity_change >= 5:
        factors.append({"name": "Velocity Improving", "status": "good", "icon": "[OK]"})
    elif recent_velocity_change >= -5:
        factors.append({"name": "Velocity Stable", "status": "good", "icon": "[OK]"})
    else:
        factors.append(
            {"name": "Velocity Declining", "status": "warning", "icon": "[!]"}
        )

    # Factor 4: Capacity
    if capacity_gap_percent >= -10:
        factors.append({"name": "Adequate Capacity", "status": "good", "icon": "[OK]"})
    elif capacity_gap_percent >= -25:
        factors.append(
            {"name": "Capacity Stretched", "status": "warning", "icon": "[!]"}
        )
    else:
        factors.append({"name": "Capacity Shortfall", "status": "bad", "icon": "[X]"})

    # Calculate overall health score
    good_count = sum(1 for f in factors if f["status"] == "good")
    bad_count = sum(1 for f in factors if f["status"] == "bad")

    if good_count >= 3:
        overall = {
            "level": "healthy",
            "color": "#28a745",
            "emoji": "[OK]",
            "label": "HEALTHY",
        }
    elif bad_count >= 2:
        overall = {
            "level": "at_risk",
            "color": "#dc3545",
            "emoji": "[X]",
            "label": "AT RISK",
        }
    else:
        overall = {
            "level": "moderate",
            "color": "#ffc107",
            "emoji": "[!]",
            "label": "MODERATE",
        }

    return {"overall": overall, "factors": factors}


#######################################################################
# SPARKLINE VISUALIZATION
#######################################################################


def _create_sparkline_bars(data_series, color="#0d6efd", height=35):
    """Create beautiful sparkline bar chart."""
    if not data_series or len(data_series) == 0:
        return html.Div(
            "No data",
            className="text-muted text-center",
            style={
                "height": f"{height}px",
                "lineHeight": f"{height}px",
                "fontSize": "0.75rem",
            },
        )

    recent_data = list(data_series)[-10:]
    max_val = max(recent_data) if max(recent_data) > 0 else 1
    normalized = [v / max_val for v in recent_data]

    bars = []
    for i, norm_val in enumerate(normalized):
        bar_height = max(norm_val * height, 3)
        opacity = 0.4 + (i / len(normalized)) * 0.6

        bars.append(
            html.Div(
                style={
                    "width": "7px",
                    "height": f"{bar_height}px",
                    "backgroundColor": color,
                    "opacity": opacity,
                    "borderRadius": "2px",
                    "transition": "all 0.3s ease",
                },
                className="sparkline-bar",
            )
        )

    return html.Div(
        bars,
        className="d-flex align-items-end justify-content-center",
        style={"height": f"{height}px", "gap": "3px"},
    )


def _create_progress_bar(completed, total, color="#0d6efd"):
    """Create animated progress bar."""
    if total == 0:
        percent = 0
    else:
        percent = min((completed / total) * 100, 100)

    return html.Div(
        [
            html.Div(
                f"{percent:.0f}%",
                className="progress-bar fw-semibold",
                style={
                    "width": f"{percent}%",
                    "backgroundColor": color,
                    "transition": "width 1s ease",
                },
            ),
        ],
        className="progress",
        style={
            "height": "22px",
            "borderRadius": "11px",
            "backgroundColor": "#e9ecef",
            "boxShadow": "inset 0 1px 2px rgba(0,0,0,0.1)",
        },
    )


#######################################################################
# ENHANCED METRIC CARDS
#######################################################################


def _create_forecast_card(
    title,
    icon,
    icon_color,
    pert_date,
    confidence_intervals,
    status,
    probability,
    show_data=True,
    card_id=None,
):
    """Create enhanced forecast card - readable text, minimal whitespace."""
    if not show_data:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(
                                className=f"{icon} me-2",
                                style={"color": icon_color, "fontSize": "1.25rem"},
                            ),
                            html.Span(
                                title,
                                className="fw-semibold",
                                style={"fontSize": "1rem"},
                            ),
                        ],
                        className="d-flex align-items-center mb-1",
                    ),
                    html.Div(
                        "Tracking disabled",
                        className="text-center text-muted py-2",
                        style={"fontSize": "0.95rem"},
                    ),
                ],
                className="p-2",
            ),
            className="h-100 shadow-sm",
            id=card_id,
            style={"border": "none", "borderRadius": "12px", "minHeight": "240px"},
        )

    ci_50_date = (
        datetime.now() + timedelta(days=confidence_intervals["ci_50"])
    ).strftime("%b %d, %Y")
    ci_95_date = (
        datetime.now() + timedelta(days=confidence_intervals["ci_95"])
    ).strftime("%b %d, %Y")

    status_color = "#28a745" if status == "on_track" else "#dc3545"
    status_icon = (
        "fa-check-circle" if status == "on_track" else "fa-exclamation-triangle"
    )
    status_text = "On Track" if status == "on_track" else "At Risk"

    # Probability color
    if probability >= 70:
        prob_color = "#28a745"
    elif probability >= 40:
        prob_color = "#ffc107"
    else:
        prob_color = "#dc3545"

    return dbc.Card(
        dbc.CardBody(
            [
                # Header - minimal spacing
                html.Div(
                    [
                        html.I(
                            className=f"{icon} me-2",
                            style={"color": icon_color, "fontSize": "1.25rem"},
                        ),
                        html.Span(
                            title,
                            className="fw-semibold",
                            style={"fontSize": "1rem"},
                        ),
                    ],
                    className="d-flex align-items-center mb-1",
                ),
                # Primary forecast
                html.Div(
                    [
                        html.Div(
                            pert_date,
                            className="fw-bold",
                            style={
                                "color": icon_color,
                                "fontSize": "1.75rem",
                                "lineHeight": "1",
                            },
                        ),
                        html.Div(
                            "Expected Completion",
                            className="text-muted",
                            style={"fontSize": "0.875rem", "fontWeight": "500"},
                        ),
                    ],
                    className="mb-2",
                ),
                # Confidence intervals
                html.Div(
                    [
                        # Section header with tooltip
                        html.Div(
                            [
                                html.Span(
                                    "Confidence Intervals",
                                    className="text-muted",
                                    style={
                                        "fontSize": "0.75rem",
                                        "fontWeight": "600",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "0.5px",
                                    },
                                ),
                                html.I(
                                    className="fas fa-info-circle ms-1 text-info",
                                    id=f"ci-section-info-{card_id or 'default'}",
                                    style={
                                        "fontSize": "0.7rem",
                                        "cursor": "help",
                                    },
                                ),
                                dbc.Tooltip(
                                    "Statistical probability ranges for completion dates. Based on velocity variance using normal distribution (50th and 95th percentiles).",
                                    target=f"ci-section-info-{card_id or 'default'}",
                                    placement="top",
                                    trigger="click",
                                    autohide=True,
                                ),
                            ],
                            className="mb-1",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    [
                                        "50%: ",
                                        html.I(
                                            className="fas fa-info-circle ms-1 text-info",
                                            id=f"ci-50-info-{card_id or 'default'}",
                                            style={
                                                "fontSize": "0.75rem",
                                                "cursor": "help",
                                            },
                                        ),
                                    ],
                                    className="text-muted",
                                    style={"fontSize": "0.875rem"},
                                ),
                                dbc.Tooltip(
                                    "50th percentile (median): 50% probability of completion by this date. This is the PERT forecast.",
                                    target=f"ci-50-info-{card_id or 'default'}",
                                    placement="top",
                                    trigger="click",
                                    autohide=True,
                                ),
                                html.Span(
                                    ci_50_date,
                                    className="fw-semibold",
                                    style={"fontSize": "0.95rem"},
                                ),
                            ],
                            className="d-flex justify-content-between mb-1",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    [
                                        "95%: ",
                                        html.I(
                                            className="fas fa-info-circle ms-1 text-info",
                                            id=f"ci-95-info-{card_id or 'default'}",
                                            style={
                                                "fontSize": "0.75rem",
                                                "cursor": "help",
                                            },
                                        ),
                                    ],
                                    className="text-muted",
                                    style={"fontSize": "0.875rem"},
                                ),
                                dbc.Tooltip(
                                    "95th percentile (high confidence): 95% probability of completion by this date. Safe estimate with 1.65σ buffer.",
                                    target=f"ci-95-info-{card_id or 'default'}",
                                    placement="top",
                                    trigger="click",
                                    autohide=True,
                                ),
                                html.Span(
                                    ci_95_date,
                                    className="fw-semibold",
                                    style={"fontSize": "0.95rem"},
                                ),
                            ],
                            className="d-flex justify-content-between",
                        ),
                    ],
                    className="mb-2 pb-2 border-bottom",
                ),
                # Status
                html.Div(
                    [
                        html.Div(
                            [
                                html.I(
                                    className=f"fas {status_icon} me-1",
                                    style={"color": status_color, "fontSize": "1rem"},
                                ),
                                html.Span(
                                    status_text,
                                    style={
                                        "color": status_color,
                                        "fontWeight": "600",
                                        "fontSize": "1rem",
                                    },
                                ),
                            ],
                            className="mb-1",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    "On-Track: ",
                                    className="text-muted me-1",
                                    style={"fontSize": "0.875rem"},
                                ),
                                html.Span(
                                    f"{probability:.0f}%",
                                    className="fw-bold",
                                    style={"color": prob_color, "fontSize": "1.1rem"},
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            className="p-2",
        ),
        className="h-100 shadow-sm",
        id=card_id,
        style={"border": "none", "borderRadius": "12px", "minHeight": "240px"},
    )


def _create_velocity_card(
    title, icon, icon_color, velocity_stats, show_data=True, card_id=None
):
    """Create enhanced velocity card with predictability - COMPACT REDESIGN."""
    if not show_data:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(
                                className=f"{icon} me-2",
                                style={"color": icon_color, "fontSize": "1.1rem"},
                            ),
                            html.Span(
                                title,
                                className="fw-semibold",
                                style={"fontSize": "0.9rem"},
                            ),
                        ],
                        className="d-flex align-items-center mb-2",
                    ),
                    html.Div(
                        "Tracking disabled",
                        className="text-center text-muted py-3",
                        style={"fontSize": "0.9rem"},
                    ),
                ]
            ),
            className="h-100 shadow-sm",
            id=card_id,
            style={"border": "none", "borderRadius": "12px"},
        )

    cv = velocity_stats["cv"]

    # Predictability classification
    if cv < 25:
        predict_label = "Predictable"
        predict_color = "#28a745"
        predict_emoji = "[OK]"
    elif cv < 40:
        predict_label = "Moderate"
        predict_color = "#ffc107"
        predict_emoji = "[!]"
    else:
        predict_label = "Unpredictable"
        predict_color = "#dc3545"
        predict_emoji = "[X]"

    # Recent trend
    recent_change = velocity_stats["recent_change"]
    if abs(recent_change) < 5:
        trend_icon = "fa-minus"
        trend_color = "#6c757d"
        trend_text = "Stable"
    elif recent_change > 0:
        trend_icon = "fa-arrow-up"
        trend_color = "#28a745"
        trend_text = f"+{recent_change:.0f}%"
    else:
        trend_icon = "fa-arrow-down"
        trend_color = "#dc3545"
        trend_text = f"{recent_change:.0f}%"

    return dbc.Card(
        dbc.CardBody(
            [
                # Header
                html.Div(
                    [
                        html.I(
                            className=f"{icon} me-2",
                            style={"color": icon_color, "fontSize": "1rem"},
                        ),
                        html.Span(
                            title,
                            className="fw-semibold",
                            style={"fontSize": "1rem"},
                        ),
                    ],
                    className="d-flex align-items-center mb-1",
                ),
                # Primary metric
                html.Div(
                    [
                        html.Div(
                            f"{velocity_stats['mean']:.1f}",
                            className="fw-bold mb-1",
                            style={
                                "color": icon_color,
                                "fontSize": "1.75rem",
                                "lineHeight": "1",
                            },
                        ),
                        html.Div(
                            "per week (avg)",
                            className="text-muted",
                            style={"fontSize": "0.875rem", "fontWeight": "500"},
                        ),
                    ],
                    className="mb-1",
                ),
                # Sparkline
                html.Div(
                    [
                        _create_sparkline_bars(
                            velocity_stats["sparkline_data"],
                            color=icon_color,
                            height=30,
                        ),
                        html.Div(
                            "Last 10 weeks",
                            className="text-muted text-center mt-1",
                            style={"fontSize": "0.75rem"},
                        ),
                    ],
                    className="mb-1 pb-2 border-bottom",
                ),
                # Predictability
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    predict_emoji,
                                    style={"fontSize": "1rem"},
                                    className="me-1",
                                ),
                                html.Span(
                                    predict_label,
                                    style={
                                        "color": predict_color,
                                        "fontWeight": "600",
                                        "fontSize": "0.95rem",
                                    },
                                ),
                            ],
                            className="mb-1",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    "Trend: ",
                                    className="text-muted me-1",
                                    style={"fontSize": "0.875rem"},
                                ),
                                html.Span(
                                    [
                                        html.I(
                                            className=f"fas {trend_icon} me-1",
                                            style={"fontSize": "0.75rem"},
                                        ),
                                        trend_text,
                                    ],
                                    style={
                                        "color": trend_color,
                                        "fontWeight": "600",
                                        "fontSize": "0.95rem",
                                    },
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            className="p-2",
        ),
        className="h-100 shadow-sm",
        id=card_id,
        style={"border": "none", "borderRadius": "12px", "minHeight": "240px"},
    )


def _create_capacity_card(
    required_velocity,
    actual_velocity,
    remaining_items,
    days_to_deadline,
    show_data=True,
):
    """Create capacity gap analysis card - COMPACT REDESIGN."""
    if not show_data:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-gauge-high me-2",
                                style={"color": "#6610f2", "fontSize": "1.1rem"},
                            ),
                            html.Span(
                                "Capacity Analysis",
                                className="fw-semibold",
                                style={"fontSize": "0.9rem"},
                            ),
                        ],
                        className="d-flex align-items-center mb-2",
                    ),
                    html.Div(
                        "Tracking disabled",
                        className="text-center text-muted py-3",
                        style={"fontSize": "0.9rem"},
                    ),
                ]
            ),
            className="h-100 shadow-sm",
            style={"border": "none", "borderRadius": "12px"},
        )

    capacity_gap = actual_velocity - required_velocity
    gap_percent = (
        (capacity_gap / required_velocity * 100) if required_velocity > 0 else 0
    )

    # Status
    if gap_percent >= -5:
        gap_color = "#28a745"
        gap_emoji = "[OK]"
        gap_label = "ADEQUATE"
    elif gap_percent >= -20:
        gap_color = "#ffc107"
        gap_emoji = "[!]"
        gap_label = "STRETCHED"
    else:
        gap_color = "#dc3545"
        gap_emoji = "[X]"
        gap_label = "SHORTFALL"

    # Calculate options
    weeks_to_deadline = days_to_deadline / 7
    scope_reduction = abs(capacity_gap * weeks_to_deadline) if gap_percent < 0 else 0
    velocity_increase = abs(gap_percent) if gap_percent < 0 else 0

    return dbc.Card(
        dbc.CardBody(
            [
                # Header
                html.Div(
                    [
                        html.I(
                            className="fas fa-gauge-high me-2",
                            style={"color": "#6610f2", "fontSize": "1rem"},
                        ),
                        html.Span(
                            "Capacity Analysis",
                            className="fw-semibold",
                            style={"fontSize": "1rem"},
                        ),
                    ],
                    className="d-flex align-items-center mb-1",
                ),
                # Status
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    gap_emoji,
                                    style={"fontSize": "1.2rem"},
                                    className="me-1",
                                ),
                                html.Span(
                                    gap_label,
                                    style={
                                        "color": gap_color,
                                        "fontWeight": "bold",
                                        "fontSize": "1rem",
                                    },
                                ),
                            ],
                            className="mb-1",
                        ),
                        html.Div(
                            f"{gap_percent:+.0f}% capacity gap",
                            className="text-muted",
                            style={"fontSize": "0.875rem", "fontWeight": "500"},
                        ),
                    ],
                    className="mb-1",
                ),
                # Metrics
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Required: ",
                                    className="text-muted",
                                    style={"fontSize": "0.875rem"},
                                ),
                                html.Span(
                                    f"{required_velocity:.1f}/wk",
                                    className="fw-semibold",
                                    style={"fontSize": "0.95rem"},
                                ),
                            ],
                            className="d-flex justify-content-between mb-1",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    "Current: ",
                                    className="text-muted",
                                    style={"fontSize": "0.875rem"},
                                ),
                                html.Span(
                                    f"{actual_velocity:.1f}/wk",
                                    className="fw-semibold",
                                    style={"fontSize": "0.95rem"},
                                ),
                            ],
                            className="d-flex justify-content-between",
                        ),
                    ],
                    className="mb-1 pb-2 border-bottom",
                ),
                # Action - simplified single message
                html.Div(
                    (
                        html.Div(
                            f"Need +{velocity_increase:.0f}% velocity or {scope_reduction:.0f} fewer items",
                            className="text-center",
                            style={
                                "fontSize": "0.875rem",
                                "color": gap_color,
                                "fontWeight": "500",
                            },
                        )
                        if gap_percent < -5
                        else html.Div(
                            "[OK] On track to meet deadline",
                            className="text-center",
                            style={
                                "fontSize": "0.95rem",
                                "color": "#28a745",
                                "fontWeight": "500",
                            },
                        )
                    ),
                ),
            ],
            className="p-2",
        ),
        className="h-100 shadow-sm",
        style={"border": "none", "borderRadius": "12px", "minHeight": "240px"},
    )


#######################################################################
# MAIN ENHANCED DASHBOARD
#######################################################################


def create_enhanced_dashboard(
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
    Create beautiful, concise, actionable enhanced dashboard.

    Improvements over original:
    - Removed redundant Average/Median forecasts (keep only PERT)
    - Added confidence intervals (50%, 80%, 95%)
    - Added velocity predictability scoring
    - Added capacity gap analysis with recommendations
    - Added project health assessment
    - Added deadline probability calculation
    - Cleaner, more focused presentation
    """
    # Use last statistics date as forecast starting point (aligns with report)
    # Statistics are weekly-based (Mondays), so forecast should start from last data point
    # NOT datetime.now() which could be any day of the week
    current_date = (
        statistics_df["date"].iloc[-1] if not statistics_df.empty else datetime.now()
    )

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

    # Calculate velocity statistics
    items_stats = _calculate_velocity_statistics(statistics_df, "items")
    points_stats = (
        _calculate_velocity_statistics(statistics_df, "points")
        if show_points
        else {
            "mean": 0,
            "median": 0,
            "std_dev": 0,
            "cv": 0,
            "recent_avg": 0,
            "recent_change": 0,
            "sparkline_data": [],
        }
    )

    # CRITICAL: Determine if we have actual points data (not just tracking enabled)
    has_points_data = (
        show_points
        and points_stats["mean"] > 0
        and pert_time_points is not None
        and pert_time_points > 0
    )

    # Calculate confidence intervals
    items_ci = _calculate_confidence_intervals(
        pert_time_items, items_stats["mean"], items_stats["std_dev"], remaining_items
    )
    points_ci = (
        _calculate_confidence_intervals(
            pert_time_points,
            points_stats["mean"],
            points_stats["std_dev"],
            remaining_points,
        )
        if has_points_data
        else {"ci_50": 0, "ci_80": 0, "ci_95": 0}
    )

    # Calculate probabilities
    items_probability = _calculate_deadline_probability(
        days_to_deadline, pert_time_items, items_stats["std_dev"], items_stats["mean"]
    )
    points_probability = (
        _calculate_deadline_probability(
            days_to_deadline,
            pert_time_points,
            points_stats["std_dev"],
            points_stats["mean"],
        )
        if has_points_data
        else 0  # Changed from 100.0 to 0 for N/A handling
    )

    # Format forecast dates
    items_pert_date = (current_date + timedelta(days=pert_time_items)).strftime(
        "%b %d, %Y"
    )
    points_pert_date = (
        (current_date + timedelta(days=pert_time_points)).strftime("%b %d, %Y")
        if has_points_data
        else "N/A"
    )

    # Determine status
    items_status = "on_track" if pert_time_items <= days_to_deadline else "at_risk"
    points_status = (
        ("on_track" if pert_time_points <= days_to_deadline else "at_risk")
        if has_points_data
        else "no_data"  # Changed from defaulting to "on_track"
    )

    # Calculate capacity gap
    weeks_to_deadline = days_to_deadline / 7 if days_to_deadline > 0 else 1
    required_velocity_items = (
        remaining_items / weeks_to_deadline if weeks_to_deadline > 0 else 0
    )
    capacity_gap_percent = (
        (
            (items_stats["mean"] - required_velocity_items)
            / required_velocity_items
            * 100
        )
        if required_velocity_items > 0
        else 0
    )

    # Assess project health
    health = _assess_project_health(
        items_stats["cv"],
        days_to_deadline,
        pert_time_items,
        items_stats["recent_change"],
        capacity_gap_percent,
    )

    # COMPACT: Single-line overview bar with key metrics - REDESIGNED for better mobile support
    overview_bar = dbc.Card(
        dbc.CardBody(
            [
                # Top row: Main metrics (wraps on mobile)
                html.Div(
                    [
                        # Health Status
                        html.Div(
                            [
                                html.Span(
                                    health["overall"]["emoji"],
                                    style={
                                        "fontSize": "1.35rem",
                                        "marginRight": "0.4rem",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Small(
                                            "Health",
                                            className="text-muted d-block",
                                            style={
                                                "fontSize": "0.7rem",
                                                "lineHeight": "1",
                                            },
                                        ),
                                        html.Strong(
                                            health["overall"]["label"],
                                            style={
                                                "fontSize": "0.85rem",
                                                "color": health["overall"]["color"],
                                            },
                                        ),
                                    ],
                                ),
                            ],
                            className="d-flex align-items-center px-2 py-1",
                            style={"minWidth": "100px"},
                        ),
                        # Divider (hidden on mobile)
                        html.Div(
                            style={
                                "width": "1px",
                                "height": "35px",
                                "backgroundColor": "#dee2e6",
                                "margin": "0 0.5rem",
                            },
                            className="d-none d-md-block",
                        ),
                        # Progress
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-tasks",
                                    style={
                                        "fontSize": "1.35rem",
                                        "color": COLOR_PALETTE["items"],
                                        "marginRight": "0.4rem",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Small(
                                            "Progress",
                                            className="text-muted d-block",
                                            style={
                                                "fontSize": "0.7rem",
                                                "lineHeight": "1",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.Strong(
                                                    f"{completed_items:,}",
                                                    style={
                                                        "fontSize": "0.85rem",
                                                        "color": COLOR_PALETTE["items"],
                                                    },
                                                ),
                                                html.Span(
                                                    f"/{actual_total_items:,}",
                                                    className="text-muted",
                                                    style={"fontSize": "0.8rem"},
                                                ),
                                                html.Span(
                                                    f" • {(completed_items / actual_total_items * 100):.0f}%"
                                                    if actual_total_items > 0
                                                    else " • 0%",
                                                    style={
                                                        "fontSize": "0.8rem",
                                                        "fontWeight": "600",
                                                        "color": COLOR_PALETTE["items"],
                                                    },
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                            className="d-flex align-items-center px-2 py-1",
                            style={"minWidth": "140px"},
                        ),
                        # Divider (hidden on mobile)
                        html.Div(
                            style={
                                "width": "1px",
                                "height": "35px",
                                "backgroundColor": "#dee2e6",
                                "margin": "0 0.5rem",
                            },
                            className="d-none d-md-block",
                        ),
                        # Deadline
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-calendar-day",
                                    style={
                                        "fontSize": "1.35rem",
                                        "color": "#6610f2",
                                        "marginRight": "0.4rem",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Small(
                                            "Deadline",
                                            className="text-muted d-block",
                                            style={
                                                "fontSize": "0.7rem",
                                                "lineHeight": "1",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.Strong(
                                                    pd.to_datetime(
                                                        deadline_str
                                                    ).strftime("%b %d"),
                                                    style={"fontSize": "0.85rem"},
                                                ),
                                                html.Span(
                                                    f" • {days_to_deadline}d",
                                                    className="text-muted",
                                                    style={"fontSize": "0.8rem"},
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                            className="d-flex align-items-center px-2 py-1",
                            style={"minWidth": "120px"},
                        ),
                        # Divider (hidden on mobile)
                        html.Div(
                            style={
                                "width": "1px",
                                "height": "35px",
                                "backgroundColor": "#dee2e6",
                                "margin": "0 0.5rem",
                            },
                            className="d-none d-lg-block",
                        ),
                        # Success Probability
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-percentage",
                                    style={
                                        "fontSize": "1.35rem",
                                        "color": "#28a745"
                                        if items_probability >= 70
                                        else "#ffc107"
                                        if items_probability >= 40
                                        else "#dc3545",
                                        "marginRight": "0.4rem",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Small(
                                            "Success",
                                            className="text-muted d-block",
                                            style={
                                                "fontSize": "0.7rem",
                                                "lineHeight": "1",
                                            },
                                        ),
                                        html.Strong(
                                            f"{items_probability:.0f}%",
                                            style={
                                                "fontSize": "0.95rem",
                                                "color": "#28a745"
                                                if items_probability >= 70
                                                else "#ffc107"
                                                if items_probability >= 40
                                                else "#dc3545",
                                            },
                                        ),
                                    ],
                                ),
                            ],
                            className="d-flex align-items-center px-2 py-1",
                            style={"minWidth": "90px"},
                        ),
                    ],
                    className="d-flex align-items-center flex-wrap justify-content-start",
                    style={"gap": "0.25rem"},
                ),
                # Divider line (on mobile)
                html.Hr(className="my-2 d-md-none", style={"margin": "0.5rem 0"}),
                # Bottom row: Key Indicators (wraps on mobile)
                html.Div(
                    [
                        html.Span(
                            [
                                html.Span(
                                    f["icon"],
                                    className="me-1",
                                    style={"fontSize": "0.8rem"},
                                ),
                                html.Span(f["name"], style={"fontSize": "0.7rem"}),
                            ],
                            className="badge me-1 mb-1",
                            style={
                                # Use semi-transparent background for better contrast
                                "backgroundColor": "rgba(40, 167, 69, 0.15)"
                                if f["status"] == "good"
                                else "rgba(255, 193, 7, 0.2)"
                                if f["status"] == "warning"
                                else "rgba(220, 53, 69, 0.15)",
                                "border": f"1.5px solid {'#28a745' if f['status'] == 'good' else '#d39e00' if f['status'] == 'warning' else '#dc3545'}",
                                "color": "#28a745"
                                if f["status"] == "good"
                                else "#856404"  # Much darker yellow for readability
                                if f["status"] == "warning"
                                else "#dc3545",
                                "fontWeight": "600",
                                "fontSize": "0.7rem",
                                "padding": "0.25rem 0.45rem",
                                "whiteSpace": "nowrap",
                            },
                        )
                        for f in health["factors"]
                    ],
                    className="d-flex flex-wrap align-items-center justify-content-center justify-content-md-start pt-2 pt-md-0 mt-md-0",
                    style={"gap": "0.2rem"},
                ),
            ],
            className="py-2 px-2",
        ),
        className="shadow-sm mb-3",
        style={"border": "none", "borderRadius": "8px"},
    )

    # Metric Cards - 4 cards in standard Bootstrap layout - COMPACT VERSION
    cards_row = dbc.Row(
        [
            # Items Forecast
            dbc.Col(
                _create_forecast_card(
                    title="Items Forecast",
                    icon="fas fa-calendar-check",
                    icon_color=COLOR_PALETTE["items"],
                    pert_date=items_pert_date,
                    confidence_intervals=items_ci,
                    status=items_status,
                    probability=items_probability,
                    show_data=True,
                    card_id="dashboard-items-forecast",
                ),
                xs=12,
                md=6,
                lg=3,
                className="mb-2",
            ),
            # Points Forecast
            dbc.Col(
                _create_forecast_card(
                    title="Points Forecast",
                    icon="fas fa-chart-bar",
                    icon_color=COLOR_PALETTE["points"],
                    pert_date=points_pert_date,
                    confidence_intervals=points_ci,
                    status=points_status,
                    probability=points_probability,
                    show_data=has_points_data,  # Use proper data validation
                    card_id="dashboard-points-forecast",
                ),
                xs=12,
                md=6,
                lg=3,
                className="mb-2",
            ),
            # Items Velocity
            dbc.Col(
                _create_velocity_card(
                    title="Items Velocity",
                    icon="fas fa-tachometer-alt",
                    icon_color="#6610f2",
                    velocity_stats=items_stats,
                    show_data=True,
                    card_id="dashboard-items-velocity",
                ),
                xs=12,
                md=6,
                lg=3,
                className="mb-2",
            ),
            # Points Velocity
            dbc.Col(
                _create_velocity_card(
                    title="Points Velocity",
                    icon="fas fa-tachometer-alt",
                    icon_color=COLOR_PALETTE["points"],
                    velocity_stats=points_stats,
                    show_data=has_points_data,  # Use proper data validation
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

    # Capacity Card - Full width for better readability - COMPACT VERSION
    capacity_row = dbc.Row(
        [
            dbc.Col(
                _create_capacity_card(
                    required_velocity=required_velocity_items,
                    actual_velocity=items_stats["mean"],
                    remaining_items=remaining_items,
                    days_to_deadline=days_to_deadline,
                    show_data=True,
                ),
                xs=12,
                lg=6,
                className="mb-2",
            ),
            # Team Performance
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-chart-line me-2",
                                        style={
                                            "color": "#20c997",
                                            "fontSize": "1rem",
                                        },
                                    ),
                                    html.Span(
                                        "Team Performance",
                                        className="fw-semibold",
                                        style={"fontSize": "1rem"},
                                    ),
                                ],
                                className="d-flex align-items-center mb-1",
                            ),
                            # Items Performance
                            html.Div(
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
                                                "Hist: ",
                                                className="text-muted",
                                                style={"fontSize": "0.875rem"},
                                            ),
                                            html.Span(
                                                f"{items_stats['mean']:.1f}",
                                                className="fw-semibold me-2",
                                                style={"fontSize": "0.875rem"},
                                            ),
                                            html.Span(
                                                "•",
                                                className="text-muted mx-1",
                                            ),
                                            html.Span(
                                                "Trend: ",
                                                className="text-muted",
                                                style={"fontSize": "0.875rem"},
                                            ),
                                            html.Span(
                                                f"{items_stats['recent_change']:+.0f}%",
                                                className="fw-bold",
                                                style={
                                                    "fontSize": "0.95rem",
                                                    "color": "#28a745"
                                                    if items_stats["recent_change"] >= 0
                                                    else "#dc3545",
                                                },
                                            ),
                                        ],
                                        className="mb-1 pb-2 border-bottom"
                                        if has_points_data
                                        else "mb-0",
                                    ),
                                ],
                                className="mb-1" if has_points_data else "",
                            ),
                            # Points Performance (only if data exists)
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
                                            html.Span(
                                                "•",
                                                className="text-muted mx-1",
                                            ),
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
                                                    "color": "#28a745"
                                                    if points_stats["recent_change"]
                                                    >= 0
                                                    else "#dc3545",
                                                },
                                            ),
                                        ],
                                    ),
                                ],
                            )
                            if has_points_data
                            else html.Div(),
                        ],
                        className="p-2",
                    ),
                    className="shadow-sm h-100",
                    style={
                        "border": "none",
                        "borderRadius": "12px",
                        "minHeight": "240px",
                    },
                ),
                xs=12,
                lg=6,
                className="mb-3",
            ),
        ],
        className="g-3",
    )

    # Complete dashboard - COMPACT REDESIGN
    return html.Div(
        [
            # Compact overview bar with all key info
            overview_bar,
            # Metric Cards (4 columns)
            cards_row,
            # Capacity and Performance (2 columns)
            capacity_row,
            # Footer - minimal and compact
            html.Div(
                html.Small(
                    [
                        html.I(className="fas fa-info-circle me-1 text-info"),
                        "PERT forecasts use 3-point estimation with confidence intervals.",
                    ],
                    className="text-muted",
                    style={"fontSize": "0.75rem"},
                ),
                className="mt-2 pt-2 border-top text-center",
            ),
        ],
        className="dashboard-enhanced",
    )
