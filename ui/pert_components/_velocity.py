"""PERT Velocity Components

Components for the weekly velocity section.
"""

import dash_bootstrap_components as dbc
from dash import html

from configuration import COLOR_PALETTE
from configuration.settings import VELOCITY_HELP_TEXTS
from ui.tooltip_utils import (
    create_calculation_step_tooltip,
    create_formula_tooltip,
    create_info_tooltip,
)


def _create_velocity_metric_card(
    title, value, trend, trend_icon, trend_color, color, is_mini=False
):
    """
    Create a velocity metric card (average or median).

    Args:
        title: Title of the card (Average or Median)
        value: Value to display
        trend: Trend percentage
        trend_icon: Icon for trend direction
        trend_color: Color for trend indicator
        color: Color for the value
        is_mini: Whether this is the mini version for the sparklines

    Returns:
        dash.html.Div: A velocity metric card
    """
    # Generate demo data for sparklines.
    sparkline_bars = []
    for i in range(10):
        if title == "Average" and not is_mini:
            height = f"{10 + (i * 3) + (5 if i % 3 == 0 else -5)}px"
            bg_color = "#0d6efd" if not is_mini else "#fd7e14"
        else:
            height = f"{8 + (i * 2) + (4 if i % 2 == 0 else -3)}px"
            bg_color = "#6c757d"
            if is_mini:
                height = f"{10 + (i * 2) + (6 if i % 3 == 0 else -2)}px"

        sparkline_bars.append(
            html.Div(
                className="mx-1",
                style={
                    "width": "5px",
                    "height": height,
                    "backgroundColor": bg_color,
                    "opacity": f"{0.4 + (i * 0.06)}",
                    "borderRadius": "1px",
                },
            )
        )

    # Create card styles.
    style_dict = {
        "flex": "1",
        "minWidth": "150px",
    }
    title_key = title.lower()
    velocity_help_key = f"velocity_{title_key}"
    velocity_calc_key = f"velocity_{title_key}_calculation"
    detail_help_title = f"Get detailed help about {title_key} velocity"
    trend_title = (
        f"Visual representation of {title_key} "
        f"{'items' if not is_mini else 'points'} completed over the last 10 weeks"
    )
    formula_description = (
        "Σ(values)/n" if title == "Average" else "middle value when sorted"
    )
    formula_example = (
        "(3+5+7+4+6)/5 = 5.0" if title == "Average" else "[3,4,5,6,7] → 5.0"
    )

    return html.Div(
        [
            # Header row with label and trend
            html.Div(
                [
                    html.Span(
                        [
                            title,
                            create_calculation_step_tooltip(
                                f"velocity-{title_key}",
                                VELOCITY_HELP_TEXTS[velocity_help_key],
                                [
                                    f"{title} = {formula_description}",
                                    f"Example: {formula_example}",
                                    "Based on last 10 weeks of completed work",
                                    (
                                        "Arithmetic mean"
                                        if title == "Average"
                                        else "50th percentile - outlier resistant"
                                    ),
                                ],
                            ),
                            # Phase 9.2 Progressive Disclosure Help Button
                            html.Span(
                                [
                                    html.Span(
                                        [
                                            dbc.Button(
                                                html.I(
                                                    className="fas fa-question-circle"
                                                ),
                                                id={
                                                    "type": "help-button",
                                                    "category": "velocity",
                                                    "key": velocity_calc_key,
                                                },
                                                size="sm",
                                                color="link",
                                                className="text-secondary p-1 ms-1",
                                                style={
                                                    "border": "none",
                                                    "background": "transparent",
                                                    "fontSize": "0.7rem",
                                                    "lineHeight": "1",
                                                },
                                                title=detail_help_title,
                                            )
                                        ],
                                        className="help-button-container",
                                    )
                                ],
                                className="ms-1",
                            )
                            if title in ["Average", "Median"]
                            else create_info_tooltip(
                                f"velocity-{title_key}",
                                VELOCITY_HELP_TEXTS[velocity_help_key],
                            ),
                        ],
                        className="fw-medium d-flex align-items-center",
                    ),
                    html.Span(
                        [
                            html.I(
                                className=f"{trend_icon} me-1",
                                style={
                                    "color": trend_color,
                                    "fontSize": "0.75rem",
                                },
                            ),
                            f"{'+' if trend > 0 else ''}{trend}%",
                            create_calculation_step_tooltip(
                                f"velocity-trend-{title.lower()}",
                                VELOCITY_HELP_TEXTS["velocity_trend"],
                                [
                                    "Trend = ((Current - Previous) / Previous) × 100",
                                    "Example: ((6.0 - 5.0) / 5.0) × 100 = +20%",
                                    "Compares recent 5 weeks vs previous 5 weeks",
                                    "Positive trend = improving velocity",
                                ],
                            ),
                        ],
                        style={"color": trend_color},
                        title="Change compared to previous period",
                        className="d-flex align-items-center",
                    ),
                ],
                className="d-flex justify-content-between align-items-center mb-2",
            ),
            # Value
            html.Div(
                html.Span(
                    f"{float(value):.1f}",  # Display with 1 decimal place
                    className="fs-3 fw-bold",
                    style={"color": color},
                ),
                className="text-center mb-2" if not is_mini else "text-center mb-1",
            ),
            # Mini sparkline trend
            html.Div(
                [
                    html.Div(
                        className="d-flex align-items-end justify-content-center",
                        style={"height": "30px"},
                        children=sparkline_bars,
                    ),
                    html.Div(
                        html.Small(
                            "10-week trend",
                            className="text-muted",
                        ),
                        className="text-center mt-1",
                    ),
                ],
                title=trend_title,
            ),
        ],
        className="p-3 border rounded mb-3",
        style=style_dict,
    )


def _create_velocity_metric_section(
    metric_type,
    avg_weekly_value,
    med_weekly_value,
    avg_trend,
    med_trend,
    avg_trend_icon,
    avg_trend_color,
    med_trend_icon,
    med_trend_color,
):
    """
    Create a velocity metric section (items or points).

    Args:
        metric_type: Type of metric, either "items" or "points"
        avg_weekly_value: Average weekly value
        med_weekly_value: Median weekly value
        avg_trend: Average trend percentage
        med_trend: Median trend percentage
        avg_trend_icon: Icon for average trend
        avg_trend_color: Color for average trend
        med_trend_icon: Icon for median trend
        med_trend_color: Color for median trend

    Returns:
        dash.html.Div: Velocity metric section
    """
    # Set colors based on metric type
    is_items = metric_type == "items"
    avg_color = "#0d6efd" if is_items else "#fd7e14"
    med_color = "#6c757d"
    is_mini = not is_items

    metric_icon_class = "fas fa-tasks me-2" if is_items else "fas fa-chart-bar me-2"
    card_bg_items = (
        "linear-gradient(to bottom, rgba(13, 110, 253, 0.05), rgba(255, 255, 255, 1))"
    )
    card_bg_points = (
        "linear-gradient(to bottom, rgba(253, 126, 20, 0.05), rgba(255, 255, 255, 1))"
    )

    return html.Div(
        [
            # Header with icon - align left instead of center
            html.Div(
                [
                    html.I(
                        className=metric_icon_class,
                        style={"color": COLOR_PALETTE[metric_type]},
                    ),
                    html.Span("Items" if is_items else "Points", className="fw-medium"),
                    create_formula_tooltip(
                        f"velocity-{metric_type}",
                        VELOCITY_HELP_TEXTS["weekly_velocity"],
                        "Weekly Average = Σ(last 10 weeks) ÷ 10",
                        [
                            "Calculates simple arithmetic mean of recent performance",
                            "Uses last 10 weeks of historical data for stability",
                            "Example: (5+7+6+8+4+9+7+6+8+5) ÷ 10 = 6.5 items/week",
                        ],
                    ),
                ],
                className="d-flex align-items-center mb-3",
            ),
            # Velocity metrics - using flex layout with improved gap spacing
            html.Div(
                [
                    # Average Items/Points
                    html.Div(
                        _create_velocity_metric_card(
                            "Average",
                            avg_weekly_value,
                            avg_trend,
                            avg_trend_icon,
                            avg_trend_color,
                            avg_color,
                            is_mini,
                        ),
                        className="px-2",
                        style={"flex": "1", "minWidth": "150px"},
                    ),
                    # Median Items/Points
                    html.Div(
                        _create_velocity_metric_card(
                            "Median",
                            med_weekly_value,
                            med_trend,
                            med_trend_icon,
                            med_trend_color,
                            med_color,
                            is_mini,
                        ),
                        className="px-2",
                        style={"flex": "1", "minWidth": "150px"},
                    ),
                ],
                className="d-flex flex-wrap mx-n2",
                style={"gap": "0px"},
            ),
        ],
        className=f"{'mb-4' if is_items else 'mb-3'} p-3 border rounded",
        style={
            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
            "background": card_bg_items if is_items else card_bg_points,
        },
    )


def _create_weekly_velocity_section(
    avg_weekly_items,
    med_weekly_items,
    avg_weekly_points,
    med_weekly_points,
    avg_items_trend,
    med_items_trend,
    avg_points_trend,
    med_points_trend,
    avg_items_icon,
    avg_items_icon_color,
    med_items_icon,
    med_items_icon_color,
    avg_points_icon,
    avg_points_icon_color,
    med_points_icon,
    med_points_icon_color,
    show_points=True,
    data_points_count=None,
    total_data_points=None,
):
    """
    Create the weekly velocity section.

    Args:
        Multiple parameters for velocity metrics
        show_points: Whether points tracking is enabled (default: True)
        data_points_count: Number of data points used for calculations
        total_data_points: Total data points available

    Returns:
        dash.html.Div: Weekly velocity section
    """
    # Create the velocity cards list
    velocity_cards = [
        # Items Velocity Card
        _create_velocity_metric_section(
            "items",
            avg_weekly_items,
            med_weekly_items,
            avg_items_trend,
            med_items_trend,
            avg_items_icon,
            avg_items_icon_color,
            med_items_icon,
            med_items_icon_color,
        ),
    ]

    # Only add points velocity card if points tracking is enabled
    if show_points:
        velocity_cards.append(
            _create_velocity_metric_section(
                "points",
                avg_weekly_points,
                med_weekly_points,
                avg_points_trend,
                med_points_trend,
                avg_points_icon,
                avg_points_icon_color,
                med_points_icon,
                med_points_icon_color,
            )
        )

    # Footer content
    footer_text = "Based on 10-week rolling average for forecasting accuracy"
    tooltip_key = "velocity-ten-week-calculation"
    tooltip_text = VELOCITY_HELP_TEXTS["ten_week_calculation"]

    if data_points_count is not None and total_data_points is not None:
        if data_points_count < total_data_points:
            footer_text = (
                f"Based on last {data_points_count} weeks of data "
                f"(filtered from {total_data_points} available weeks)"
            )
            tooltip_key = "velocity-data-filtering"
            tooltip_text = (
                "Velocity calculations use the most recent "
                f"{data_points_count} data points as selected by the "
                "'Data Points to Include' slider."
            )

    return html.Div(
        [
            # Add all velocity cards
            *velocity_cards,
            # Enhanced footer with data period explanation and tooltip
            html.Div(
                html.Div(
                    [
                        html.I(
                            className="fas fa-calendar-week me-1",
                            style={"color": "#6c757d"},
                        ),
                        footer_text,
                        create_info_tooltip(
                            tooltip_key,
                            tooltip_text,
                        ),
                    ],
                    className=(
                        "text-muted fst-italic small text-center d-flex "
                        "align-items-center justify-content-center"
                    ),
                ),
                className="mt-3",
            ),
        ],
        className="p-3 border rounded h-100",
    )
