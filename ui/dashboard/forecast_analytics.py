"""Forecast analytics module for dashboard.

Provides forecast analytics functions including:
- PERT (Program Evaluation and Review Technique) three-point estimation
- Confidence intervals with statistical probability ranges
- Historical forecast tracking and trend visualization
- Deadline achievement probability calculations
- Forecast alignment with budget runway

This module supports both items-based and points-based forecasting with
visual indicators for tracking accuracy and trends over time.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import dash_bootstrap_components as dbc
from dash import html

from ui.budget_cards import create_forecast_alignment_card
from ui.style_constants import COLOR_PALETTE
from ui.tooltip_utils import create_info_tooltip


def get_forecast_history() -> tuple[list, list, list]:
    """Get historical forecast data for trend visualization.

    Returns:
        Tuple of (dates, items_forecasts, points_forecasts) lists
    """
    try:
        from data.persistence import load_unified_project_data

        unified_data = load_unified_project_data()
        forecast_history = unified_data.get("forecast_history", [])

        # Extract data for plotting (last 10 data points)
        dates = []
        items_forecasts = []
        points_forecasts = []

        for entry in forecast_history[-10:]:
            dates.append(entry.get("date", ""))
            items_forecasts.append(entry.get("items_forecast_date", ""))
            points_forecasts.append(entry.get("points_forecast_date", ""))

        return dates, items_forecasts, points_forecasts
    except Exception:
        return [], [], []


def create_forecast_analytics_section(
    pert_data: dict,
    confidence_data: dict,
    budget_data: Optional[dict] = None,
    show_points: bool = True,
    remaining_items: Optional[float] = None,
    remaining_points: Optional[float] = None,
    avg_weekly_items: Optional[float] = None,
    avg_weekly_points: Optional[float] = None,
    days_to_deadline: Optional[int] = None,
    deadline_str: Optional[str] = None,
) -> html.Div:
    """Create forecasting section with multiple prediction methods.

    Args:
        pert_data: Dictionary with pert_time_items, pert_time_points, and last_date
        confidence_data: Dictionary with ci_50, ci_95, deadline_probability
        budget_data: Optional budget data for forecast alignment
        show_points: Whether to use points-based (True) or items-based (False) forecast
        remaining_items: Current remaining items (for pace health calculation)
        remaining_points: Current remaining points (for pace health calculation)
        avg_weekly_items: Current velocity in items/week (from filtered data)
        avg_weekly_points: Current velocity in points/week (from filtered data)
        days_to_deadline: Days remaining to deadline (for display purposes)
        deadline_str: Deadline date string in YYYY-MM-DD format (for accurate calculation)
        days_to_deadline: Days remaining to deadline (for pace health calculation)

    Returns:
        dbc.Card component containing forecast analytics
    """
    # Use last statistics date from pert_data (aligns with weekly data structure)
    # Falls back to datetime.now() only if last_date not available
    current_date = pert_data.get("last_date", datetime.now())

    # Calculate BOTH items-based and points-based forecasts
    items_forecast_days = pert_data.get("pert_time_items", 0)
    points_forecast_days = pert_data.get("pert_time_points", 0)

    # Only format date if there's actual forecast time (not 0)
    # Use YYYY-MM-DD format for region-neutral display
    items_pert_date = (
        (current_date + timedelta(days=items_forecast_days)).strftime("%Y-%m-%d")
        if items_forecast_days > 0
        else "No data"
    )
    points_pert_date = (
        (current_date + timedelta(days=points_forecast_days)).strftime("%Y-%m-%d")
        if points_forecast_days > 0
        else "No data"
    )

    # Use appropriate forecast metric for confidence intervals (matches report/burndown)
    forecast_metric = "story points" if show_points else "items"

    # Format confidence interval dates
    optimistic_date = (
        current_date + timedelta(days=confidence_data.get("ci_50", 0))
    ).strftime("%Y-%m-%d")
    pessimistic_date = (
        current_date + timedelta(days=confidence_data.get("ci_95", 0))
    ).strftime("%Y-%m-%d")

    # Get probabilities for both tracks
    deadline_prob_items = confidence_data.get("deadline_probability_items", 75)
    deadline_prob_points = confidence_data.get("deadline_probability_points")

    # Determine on-track probability tier (using primary metric)
    deadline_prob = (
        deadline_prob_points
        if (show_points and deadline_prob_points)
        else deadline_prob_items
    )
    if deadline_prob >= 70:
        prob_tier = "Healthy"
        prob_color = "#28a745"
    elif deadline_prob >= 40:
        prob_tier = "Warning"
        prob_color = "#ffc107"
    else:
        prob_tier = "At Risk"
        prob_color = "#dc3545"

    # Get tier info for items track
    items_prob_tier = (
        "Healthy"
        if deadline_prob_items >= 70
        else "Warning"
        if deadline_prob_items >= 40
        else "At Risk"
    )
    items_prob_color = (
        "#28a745"
        if deadline_prob_items >= 70
        else "#ffc107"
        if deadline_prob_items >= 40
        else "#dc3545"
    )

    # Create Enhanced Expected Completion card with BOTH forecasts
    expected_completion_card = dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Span(
                        "Expected Completion",
                        className="metric-card-title",
                    ),
                    " ",
                    create_info_tooltip(
                        help_text="Calculated using PERT three-point estimation: (Optimistic + 4×Most_Likely + Pessimistic) ÷ 6. "
                        "Shows forecasts based on both items and story points velocity. "
                        "This weighted average emphasizes the most likely scenario (4x weight) while accounting for best/worst cases from your historical velocity data. "
                        "Same method used in Burndown Chart and Report.",
                        id_suffix="metric-expected_completion",
                        placement="top",
                        variant="dark",
                    ),
                ],
                className="d-flex align-items-center",
            ),
            dbc.CardBody(
                [
                    # Items-based forecast
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-tasks me-2",
                                        style={
                                            "color": COLOR_PALETTE["items"],
                                            "fontSize": "1rem",
                                        },
                                    ),
                                    html.Span(
                                        "Items-based",
                                        className="text-muted",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                                className="mb-1",
                            ),
                            html.Div(
                                items_pert_date,
                                className="h3 mb-3",
                                style={
                                    "fontWeight": "bold",
                                    "color": COLOR_PALETTE["items"],
                                },
                            ),
                        ],
                        className="text-center pb-2",
                        style={"borderBottom": "1px solid #e9ecef"}
                        if show_points
                        else {},
                    ),
                    # Points-based forecast (always show, with placeholder when disabled or no data)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-chart-bar me-2",
                                        style={
                                            "color": COLOR_PALETTE["points"]
                                            if show_points
                                            and points_pert_date != "No data"
                                            else "#6c757d",
                                            "fontSize": "1rem",
                                        },
                                    ),
                                    html.Span(
                                        "Points-based",
                                        className="text-muted",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                                className="mb-1 mt-3",
                            ),
                            html.Div(
                                # Case 1: Points tracking enabled with data
                                points_pert_date
                                if show_points and points_pert_date != "No data"
                                # Case 2: Points tracking disabled
                                else (
                                    [
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
                                        )
                                    ]
                                    if not show_points
                                    # Case 3: Points tracking enabled but no data
                                    else [
                                        html.Div(
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
                                        )
                                    ]
                                ),
                                className="h3 mb-0"
                                if show_points and points_pert_date != "No data"
                                else "",
                                style={
                                    "fontWeight": "bold",
                                    "color": COLOR_PALETTE["points"],
                                }
                                if show_points and points_pert_date != "No data"
                                else {},
                            ),
                        ],
                        className="text-center",
                    ),
                ],
                className="text-center py-3",
            ),
            dbc.CardFooter(
                html.Small(
                    "PERT forecast based on items and story points velocity"
                    if show_points
                    else "PERT forecast based on items velocity",
                    className="text-muted",
                ),
                className="text-center",
            ),
        ],
        className="metric-card mb-3 h-100",
    )

    # Enhanced Confidence Intervals card with bigger dates and better spacing
    confidence_intervals_card = dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Span(
                        "Confidence Intervals",
                        className="metric-card-title",
                    ),
                    " ",
                    create_info_tooltip(
                        help_text=f"Statistical probability ranges based on {forecast_metric} velocity variability. "
                        f"50%: 50th percentile (median) - the PERT forecast itself. "
                        f"95%: 95th percentile - conservative estimate with 1.65σ buffer (adds uncertainty for remaining work). "
                        f"Wider spread indicates higher velocity uncertainty. Calculated from your historical data variance.",
                        id_suffix="metric-confidence_intervals",
                        placement="top",
                        variant="dark",
                    ),
                ],
                className="d-flex align-items-center",
            ),
            dbc.CardBody(
                [
                    # 50% Confidence (Optimistic)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-thumbs-up me-2",
                                        style={"color": "#28a745"},
                                    ),
                                    html.Span(
                                        "50% Confidence",
                                        style={
                                            "fontSize": "0.9rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                ],
                                className="mb-2",
                            ),
                            html.Div(
                                optimistic_date,
                                className="h3 mb-3",
                                style={
                                    "color": "#28a745",
                                    "fontWeight": "bold",
                                },
                            ),
                        ],
                        className="text-center pb-3",
                        style={"borderBottom": "2px solid #e9ecef"},
                    ),
                    # 95% Confidence (Pessimistic)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-shield-alt me-2",
                                        style={"color": "#dc3545"},
                                    ),
                                    html.Span(
                                        "95% Confidence",
                                        style={
                                            "fontSize": "0.9rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                ],
                                className="mb-2 mt-3",
                            ),
                            html.Div(
                                pessimistic_date,
                                className="h3 mb-0",
                                style={
                                    "color": "#dc3545",
                                    "fontWeight": "bold",
                                },
                            ),
                        ],
                        className="text-center",
                    ),
                ],
                className="text-center py-3",
            ),
            dbc.CardFooter(
                html.Small(
                    "Statistical delivery probability ranges",
                    className="text-muted",
                ),
                className="text-center",
            ),
        ],
        className="metric-card mb-3 h-100",
    )

    # Enhanced On-Track Probability card with visual indicator
    on_track_card = dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Span(
                        "On-Track Probability",
                        className="metric-card-title",
                    ),
                    " ",
                    create_info_tooltip(
                        help_text="Statistical probability of meeting deadline using normal distribution. "
                        "Calculated via Z-score: (deadline_days - expected_days) / forecast_std_dev. "
                        "Based on how many standard deviations your deadline is from expected completion, adjusted for velocity consistency.",
                        id_suffix="metric-on_track_probability",
                        placement="top",
                        variant="dark",
                    ),
                ],
                className="d-flex align-items-center",
            ),
            dbc.CardBody(
                [
                    # Items-based probability
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-tasks me-1",
                                        style={
                                            "color": COLOR_PALETTE["items"],
                                            "fontSize": "0.9rem",
                                        },
                                    ),
                                    html.Span(
                                        "Items-based",
                                        className="text-muted",
                                        style={"fontSize": "0.75rem"},
                                    ),
                                ],
                                className="mb-1",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                f"{deadline_prob_items:.0f}%",
                                                className="text-muted",
                                                style={
                                                    "fontSize": "0.85rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            html.Span(
                                                items_prob_tier,
                                                className="badge ms-2",
                                                style={
                                                    "backgroundColor": items_prob_color,
                                                    "fontSize": "0.75rem",
                                                },
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center mb-2",
                                    ),
                                    html.Div(
                                        html.Div(
                                            f"{deadline_prob_items:.1f}%",
                                            className="progress-bar",
                                            style={
                                                "width": f"{min(deadline_prob_items, 100)}%",
                                                "backgroundColor": items_prob_color,
                                            },
                                            role="progressbar",
                                        ),
                                        className="progress",
                                        style={"height": "20px"},
                                    ),
                                ],
                            ),
                        ],
                        className="pb-3 mb-3",
                        style={"borderBottom": "1px solid #e9ecef"}
                        if show_points
                        else {"marginBottom": "0"},
                    ),
                    # Points-based probability (always show, with placeholder when disabled)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-chart-bar me-1",
                                        style={
                                            "color": COLOR_PALETTE["points"]
                                            if show_points
                                            else "#6c757d",
                                            "fontSize": "0.9rem",
                                        },
                                    ),
                                    html.Span(
                                        "Points-based",
                                        className="text-muted",
                                        style={"fontSize": "0.75rem"},
                                    ),
                                ],
                                className="mb-1",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                f"{deadline_prob_points:.0f}%",
                                                className="text-muted",
                                                style={
                                                    "fontSize": "0.85rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            html.Span(
                                                prob_tier,
                                                className="badge ms-2",
                                                style={
                                                    "backgroundColor": prob_color,
                                                    "fontSize": "0.75rem",
                                                },
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center mb-2",
                                    ),
                                    html.Div(
                                        html.Div(
                                            f"{deadline_prob_points:.1f}%",
                                            className="progress-bar",
                                            style={
                                                "width": f"{min(deadline_prob_points, 100)}%",
                                                "backgroundColor": prob_color,
                                            },
                                            role="progressbar",
                                        ),
                                        className="progress",
                                        style={"height": "20px"},
                                    ),
                                ],
                            )
                            # Case 1: Points tracking disabled
                            if show_points
                            and deadline_prob_points is not None
                            and deadline_prob_points > 0
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
                                )
                                if not show_points
                                # Case 2: Points tracking enabled but no data
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
                                )
                            ),
                        ],
                    ),
                ],
            ),
            dbc.CardFooter(
                html.Small(
                    "Deadline achievement likelihood based on items and story points"
                    if show_points
                    else "Deadline achievement likelihood based on items",
                    className="text-muted",
                ),
                className="text-center",
            ),
        ],
        className="metric-card mb-3 h-100",
    )

    # Create forecast history trend chart (if data available)
    history_dates, history_items, history_points = get_forecast_history()

    forecast_trend_chart = None
    if history_dates and len(history_dates) >= 2:
        import plotly.graph_objects as go

        fig = go.Figure()

        # Add items-based forecast trend
        if history_items:
            fig.add_trace(
                go.Scatter(
                    x=history_dates,
                    y=history_items,
                    mode="lines+markers",
                    name="Items-based Forecast",
                    line=dict(color=COLOR_PALETTE["items"], width=3),
                    marker=dict(size=8, symbol="circle"),
                )
            )

        # Add points-based forecast trend (if available)
        if history_points and show_points:
            fig.add_trace(
                go.Scatter(
                    x=history_dates,
                    y=history_points,
                    mode="lines+markers",
                    name="Points-based Forecast",
                    line=dict(color=COLOR_PALETTE["points"], width=3, dash="dot"),
                    marker=dict(size=8, symbol="diamond"),
                )
            )

        fig.update_layout(
            title=dict(
                text="Forecast Evolution Over Time",
                font=dict(size=14, color="#495057"),
                x=0.5,
                xanchor="center",
            ),
            xaxis=dict(
                title="Calculation Date",
                showgrid=True,
                gridcolor="#e9ecef",
            ),
            yaxis=dict(
                title="Predicted Completion Date",
                showgrid=True,
                gridcolor="#e9ecef",
            ),
            hovermode="x unified",
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=300,
            margin=dict(l=60, r=40, t=50, b=60),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        from dash import dcc

        forecast_trend_chart = dbc.Card(
            dbc.CardBody(
                [
                    dcc.Graph(
                        figure=fig,
                        config={"displayModeBar": False},
                        style={"height": "300px"},
                    ),
                    html.Div(
                        html.Small(
                            "Historical trend showing how forecast dates have changed as the project progresses",
                            className="text-muted",
                        ),
                        className="text-center mt-2",
                    ),
                ]
            ),
            className="metric-card mb-3",
        )

    # Create Required Pace to Deadline card (if all data available)
    pace_health_card_element = None
    if (
        remaining_items is not None
        and avg_weekly_items is not None
        and days_to_deadline is not None
        and days_to_deadline > 0
        and deadline_str is not None
    ):
        from data.velocity_projections import calculate_required_velocity

        # Calculate required velocities using ACTUAL deadline date (not reconstructed from days)
        # This ensures exact match with burndown charts calculation
        # Use date() to ensure value doesn't change during the same day (consistency)
        deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d")
        current_date = datetime.combine(datetime.now().date(), datetime.min.time())
        required_items = calculate_required_velocity(
            remaining_items, deadline_date, current_date=current_date, time_unit="week"
        )

        # Calculate required points (if available)
        required_points = None
        if (
            show_points
            and remaining_points is not None
            and avg_weekly_points is not None
        ):
            required_points = calculate_required_velocity(
                remaining_points,
                deadline_date,
                current_date=current_date,
                time_unit="week",
            )

        # Create the card
        from ui.cards.pace_health_card import create_pace_health_card

        pace_health_card_element = create_pace_health_card(
            required_items=required_items,
            current_items=avg_weekly_items,
            required_points=required_points,
            current_points=avg_weekly_points if show_points else None,
            deadline_days=days_to_deadline,
            show_points=show_points,
        )

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-chart-line me-2", style={"color": "#6610f2"}
                    ),
                    "Delivery Forecast",
                ],
                className="mb-3 mt-4",
            ),
            dbc.Row(
                [
                    dbc.Col(expected_completion_card, width=12, md=3, className="mb-3"),
                    dbc.Col(
                        confidence_intervals_card, width=12, md=3, className="mb-3"
                    ),
                    dbc.Col(on_track_card, width=12, md=3, className="mb-3"),
                    # Required Pace card (if data available)
                    dbc.Col(
                        pace_health_card_element
                        if pace_health_card_element
                        else html.Div(),
                        width=12,
                        md=3,
                        className="mb-3",
                    ),
                ]
            ),
            # Forecast vs Budget Alignment card (if budget configured)
            (
                dbc.Row(
                    [
                        dbc.Col(
                            create_forecast_alignment_card(
                                pert_time_items=pert_data.get("pert_time_items", 0),
                                pert_time_points=pert_data.get("pert_time_points"),
                                runway_weeks=budget_data.get("runway_weeks", 0),
                                show_points=show_points,
                                last_date=pert_data.get("last_date"),
                                card_id="forecast-alignment-card",
                            ),
                            width=12,
                            className="mb-3",
                        )
                    ]
                )
                if budget_data and budget_data.get("configured")
                else html.Div()
            ),
            # Forecast history trend chart (if available)
            forecast_trend_chart if forecast_trend_chart else html.Div(),
        ],
        className="mb-4",
    )
