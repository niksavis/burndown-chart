"""PERT Forecast Components

Components for the completion forecast section.
"""

from dash import html

from configuration import COLOR_PALETTE
from configuration.settings import FORECAST_HELP_TEXTS, VELOCITY_HELP_TEXTS
from ui.tooltip_utils import (
    create_calculation_step_tooltip,
    create_formula_tooltip,
    create_info_tooltip,
    create_statistical_context_tooltip,
)

from ._helpers import _create_forecast_row


def _create_forecast_card(
    title,
    metric_type,
    completion_str,
    pert_time,
    color,
    avg_completion_str,
    med_completion_str,
    weeks_avg,
    avg_days,
    weeks_med,
    med_days,
    weeks_avg_color,
    weeks_med_color,
):
    """
    Create a forecast card for either items or points.

    Args:
        title: Title of the forecast card (e.g., "Items Forecast")
        metric_type: Type of metric, either "items" or "points"
        completion_str: Formatted completion date string
        pert_time: PERT estimate for completion (days)
        color: Color indicator (green/red) based on meeting deadline
        avg_completion_str: Average completion date string
        med_completion_str: Median completion date string
        weeks_avg: Number of weeks to completion based on average
        avg_days: Number of days to completion based on average
        weeks_med: Number of weeks to completion based on median
        med_days: Number of days to completion based on median
        weeks_avg_color: Color for average forecast (green/red)
        weeks_med_color: Color for median forecast (green/red)

    Returns:
        dash.html.Div: A forecast card component
    """
    metric_icon_class = (
        "fas fa-tasks me-2" if metric_type == "items" else "fas fa-chart-bar me-2"
    )
    center_header_class = (
        "text-muted text-center d-flex align-items-center justify-content-center"
    )
    end_header_class = (
        "text-muted text-end d-flex align-items-center justify-content-end"
    )
    week_tone_avg = "40,167,69" if weeks_avg_color == "green" else "220,53,69"
    week_tone_med = "40,167,69" if weeks_med_color == "green" else "220,53,69"
    avg_row_bg = f"rgba({week_tone_avg},0.05)"
    med_row_bg = f"rgba({week_tone_med},0.05)"
    card_bg_items = (
        "linear-gradient(to bottom, rgba(13, 110, 253, 0.05), rgba(255, 255, 255, 1))"
    )
    card_bg_points = (
        "linear-gradient(to bottom, rgba(253, 126, 20, 0.05), rgba(255, 255, 255, 1))"
    )

    return html.Div(
        [
            # Header with icon
            html.Div(
                [
                    html.I(
                        className=metric_icon_class,
                        style={"color": COLOR_PALETTE[metric_type]},
                    ),
                    html.Span(
                        title,
                        className="fw-medium",
                    ),
                ],
                className="d-flex align-items-center mb-3",
            ),
            # Table header
            html.Div(
                className="d-flex mb-2 px-3 py-2 bg-light rounded-top border-bottom",
                style={"fontSize": "0.8rem"},
                children=[
                    html.Div(
                        [
                            "Method",
                            create_formula_tooltip(
                                f"forecast-method-{metric_type}",
                                FORECAST_HELP_TEXTS["three_point_estimation"],
                                "Three-Point Estimation",
                                [
                                    "PERT: (Optimistic + 4×Most_Likely + "
                                    "Pessimistic) / 6",
                                    "Average: Historical mean completion rate",
                                    "Median: Middle value of historical rates",
                                    "Each method provides different confidence levels",
                                ],
                            ),
                        ],
                        className="text-muted d-flex align-items-center",
                        style={"width": "25%"},
                    ),
                    html.Div(
                        [
                            "Completion Date",
                            create_info_tooltip(
                                f"completion-date-{metric_type}",
                                "Projected completion date based on "
                                "historical velocity "
                                "and confidence window analysis.",
                            ),
                        ],
                        className=center_header_class,
                        style={"width": "45%"},
                    ),
                    html.Div(
                        [
                            "Timeframe",
                            create_info_tooltip(
                                f"timeframe-{metric_type}",
                                "Estimated duration to complete remaining work, "
                                "shown in days (d) and weeks (w).",
                            ),
                        ],
                        className=end_header_class,
                        style={"width": "30%"},
                    ),
                ],
            ),
            _create_forecast_row(
                [
                    "Confidence Window",
                    create_formula_tooltip(
                        f"pert-forecast-{metric_type}",
                        FORECAST_HELP_TEXTS["expected_forecast"],
                        "Confidence Window = (O + 4×M + P) / 6",
                        [
                            "O = Best case scenario (optimistic)",
                            "M = Most likely scenario (modal)",
                            "P = Worst case scenario (pessimistic)",
                            "Uses beta distribution weighting with 4x emphasis "
                            "on the most likely case",
                        ],
                    ),
                ],
                completion_str,
                f"{pert_time:.1f}d ({pert_time / 7:.1f}w)",
                f"rgba({color == 'green' and '40,167,69' or '220,53,69'},0.08)",
                is_highlighted=True,
                icon="fas fa-chart-line",
            ),
            # Average row
            _create_forecast_row(
                [
                    "Average",
                    create_calculation_step_tooltip(
                        f"average-forecast-{metric_type}",
                        VELOCITY_HELP_TEXTS["velocity_average"],
                        [
                            "Average = Σ(weekly_values) / n",
                            "Example: (5+7+3+6+4)/5 = 5.0 items/week",
                            "Completion = remaining_work / average_velocity",
                            "Uses arithmetic mean of recent velocity data",
                        ],
                    ),
                ],
                avg_completion_str,
                (
                    f"{avg_days:.1f}d ({weeks_avg:.1f}w)"
                    if weeks_avg != float("inf")
                    else "∞"
                ),
                avg_row_bg,
            ),
            # Median row
            _create_forecast_row(
                [
                    "Median",
                    create_statistical_context_tooltip(
                        f"median-forecast-{metric_type}",
                        VELOCITY_HELP_TEXTS["velocity_median"],
                        "50th percentile",
                        "More robust than average - less affected by outliers "
                        "and extreme values. Better for forecasting "
                        "when velocity varies significantly.",
                    ),
                ],
                med_completion_str,
                (
                    f"{med_days:.1f}d ({weeks_med:.1f}w)"
                    if weeks_med != float("inf")
                    else "∞"
                ),
                med_row_bg,
            ),
        ],
        className=f"{'mb-4' if metric_type == 'items' else 'mb-3'} p-3 border rounded",
        style={
            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
            "background": card_bg_items if metric_type == "items" else card_bg_points,
        },
    )


def _create_completion_forecast_section(
    items_completion_str,
    points_completion_str,
    pert_time_items,
    pert_time_points,
    items_color,
    points_color,
    avg_items_completion_str,
    med_items_completion_str,
    avg_points_completion_str,
    med_points_completion_str,
    weeks_avg_items,
    weeks_med_items,
    weeks_avg_points,
    weeks_med_points,
    avg_items_days,
    med_items_days,
    avg_points_days,
    med_points_days,
    weeks_avg_items_color,
    weeks_med_items_color,
    weeks_avg_points_color,
    weeks_med_points_color,
    show_points=True,
):
    """
    Create the completion forecast section.

    Args:
        Multiple parameters for both items and points forecasts
        show_points: Whether points tracking is enabled (default: True)

    Returns:
        dash.html.Div: Completion forecast section
    """
    # Create the forecast cards list
    forecast_cards = [
        # Items Forecast Card
        _create_forecast_card(
            "Items Forecast",
            "items",
            items_completion_str,
            pert_time_items,
            items_color,
            avg_items_completion_str,
            med_items_completion_str,
            weeks_avg_items,
            avg_items_days,
            weeks_med_items,
            med_items_days,
            weeks_avg_items_color,
            weeks_med_items_color,
        ),
    ]

    # Only add points forecast card if points tracking is enabled
    if show_points:
        forecast_cards.append(
            _create_forecast_card(
                "Points Forecast",
                "points",
                points_completion_str,
                pert_time_points,
                points_color,
                avg_points_completion_str,
                med_points_completion_str,
                weeks_avg_points,
                avg_points_days,
                weeks_med_points,
                med_points_days,
                weeks_avg_points_color,
                weeks_med_points_color,
            )
        )

    return html.Div(
        [
            # Add all forecast cards
            *forecast_cards,
            # Enhanced footer with methodology explanation and tooltip
            html.Div(
                html.Small(
                    [
                        html.I(
                            className="fas fa-chart-line me-1",
                            style={"color": "#6c757d"},
                        ),
                        "Confidence Window three-point estimation "
                        "(optimistic + most likely + pessimistic)",
                        create_info_tooltip(
                            "pert-methodology",
                            FORECAST_HELP_TEXTS["pert_methodology"],
                        ),
                    ],
                    className=(
                        "text-muted fst-italic text-center d-flex "
                        "align-items-center justify-content-center"
                    ),
                ),
                className="mt-3",
            ),
        ],
        className="p-3 border rounded h-100",
    )
