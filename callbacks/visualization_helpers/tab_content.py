"""
Tab Content Builders for Visualizations

This module contains functions for building tab content layouts
in the visualization callbacks.
"""

from dash import html, dcc
from configuration.chart_config import (
    get_burndown_chart_config,
    get_weekly_chart_config,
)
from callbacks.visualization_helpers.ui_builders import create_trend_header_with_forecasts


def create_burndown_tab_content(
    df,
    items_trend: dict,
    points_trend: dict,
    burndown_fig,
    items_fig,
    points_fig,
    settings: dict,
    show_points: bool = True,
    has_points_data: bool = True,
):
    """
    Create content for the burndown tab with burndown chart, items chart, and points chart.

    Args:
        df: DataFrame with statistics data
        items_trend: Dictionary with items trend and forecast data
        points_trend: Dictionary with points trend and forecast data
        burndown_fig: Burndown chart figure
        items_fig: Weekly items chart figure
        points_fig: Weekly points chart figure (None if no data or disabled)
        settings: Settings dictionary
        show_points: Whether points tracking is enabled
        has_points_data: Whether points data exists in selected period

    Returns:
        html.Div: Burndown tab content with all three charts
    """
    chart_height = settings.get("chart_height", 700)

    # Build the content list starting with burndown chart
    content = [
        # Weekly trend indicators in a row
        html.Div(
            [
                # Items trend box
                create_trend_header_with_forecasts(
                    items_trend,
                    "Weekly Items Trend",
                    "fas fa-tasks",
                    "#0d6efd",  # Blue for items
                ),
            ]
            + (
                [
                    # Points trend box - only show if points tracking is enabled
                    create_trend_header_with_forecasts(
                        points_trend,
                        "Weekly Items Trend",
                        "fas fa-chart-bar",
                        "#fd7e14",
                    ),
                ]
                if show_points
                else []
            ),
            className="row mb-3",
        ),
        # Burndown chart with title
        html.H5(
            [
                html.I(
                    className="fas fa-chart-line me-2", style={"color": "#0d6efd"}
                ),
                "Forecast Based On Historical Data",
            ],
            className="mb-3 mt-4",
        ),
        dcc.Graph(
            id="forecast-graph",
            figure=burndown_fig,
            config=get_burndown_chart_config(),  # type: ignore
            style={"height": f"{chart_height}px"},
        ),
    ]

    # Add Items per Week chart section
    content.extend(
        [
            # Items per Week section header (standardized H5 styling)
            html.H5(
                [
                    html.I(
                        className="fas fa-tasks me-2",
                        style={"color": "#0d6efd"},  # Blue for items
                    ),
                    "Weekly Completed Items",
                ],
                className="mb-3 mt-4",
            ),
            # Items chart (trend header removed - already shown at top)
            dcc.Graph(
                id="items-chart",
                figure=items_fig,
                config=get_weekly_chart_config(),  # type: ignore
                style={"height": "700px"},
            ),
        ]
    )

    # Add Points per Week section
    content.extend(
        [
            # Points per Week section header (standardized H5 styling)
            html.H5(
                [
                    html.I(
                        className="fas fa-chart-bar me-2",
                        style={"color": "#fd7e14"},
                    ),
                    "Weekly Completed Points",
                ],
                className="mb-3 mt-4",
            ),
        ]
    )

    # Determine which content to show for points section
    if not show_points:
        # Case 1: Points tracking disabled
        content.append(
            html.Div(
                [
                    html.I(className="fas fa-toggle-off fa-2x text-secondary mb-3"),
                    html.Div(
                        "Points Tracking Disabled",
                        className="fw-bold mb-2",
                        style={"fontSize": "1.2rem", "color": "#6c757d"},
                    ),
                    html.Small(
                        "Enable Points Tracking in Parameters panel to view story points metrics.",
                        className="text-muted",
                        style={"fontSize": "0.9rem"},
                    ),
                ],
                className="d-flex align-items-center justify-content-center flex-column",
                style={"gap": "0.25rem", "padding": "80px 20px"},
            )
        )
    elif not has_points_data:
        # Case 2: Points tracking enabled but no data in period
        content.append(
            html.Div(
                [
                    html.I(className="fas fa-database fa-lg text-secondary mb-3"),
                    html.Div(
                        "No Points Data",
                        className="fw-bold mb-2",
                        style={"fontSize": "1.2rem", "color": "#6c757d"},
                    ),
                    html.Small(
                        "No story points data available in the selected time period. Configure story points field in Settings or complete items with point estimates.",
                        className="text-muted",
                        style={
                            "fontSize": "0.9rem",
                            "textAlign": "center",
                            "maxWidth": "500px",
                        },
                    ),
                ],
                className="d-flex align-items-center justify-content-center flex-column",
                style={"gap": "0.25rem", "padding": "80px 20px"},
            )
        )
    else:
        # Case 3: Points tracking enabled with data - show chart
        # Points trend header removed - already shown at top
        content.append(
            dcc.Graph(
                id="points-chart",
                figure=points_fig,
                config=get_weekly_chart_config(),  # type: ignore
                style={"height": "700px"},
            )
        )

    return html.Div(content)


def create_items_tab_content(items_trend: dict, items_fig):
    """
    Create content for the items tab.

    Args:
        items_trend: Dictionary with items trend and forecast data
        items_fig: Weekly items chart figure

    Returns:
        html.Div: Items tab content
    """
    return html.Div(
        [
            # Enhanced header with trend indicator and forecast pills
            html.Div(
                [
                    # Column for items trend
                    create_trend_header_with_forecasts(
                        items_trend,
                        "Weekly Items Trend",
                        "fas fa-tasks",
                        "#0d6efd",  # Blue for items
                    ),
                ],
                className="mb-4",
            ),
            # Consolidated items weekly chart with forecast
            dcc.Graph(
                id="items-chart",
                figure=items_fig,
                config=get_weekly_chart_config(),  # type: ignore
                style={"height": "700px"},
            ),
        ]
    )


def create_points_tab_content(points_trend: dict, points_fig):
    """
    Create content for the points tab.

    Args:
        points_trend: Dictionary with points trend and forecast data
        points_fig: Weekly points chart figure

    Returns:
        html.Div: Points tab content
    """
    return html.Div(
        [
            # Enhanced header with trend indicator and forecast pills
            html.Div(
                [
                    # Column for points trend
                    create_trend_header_with_forecasts(
                        points_trend,
                        "Weekly Points Trend",
                        "fas fa-chart-bar",
                        "#fd7e14",
                    ),
                ],
                className="mb-4",
            ),
            # Consolidated points weekly chart with forecast
            dcc.Graph(
                id="points-chart",
                figure=points_fig,
                config=get_weekly_chart_config(),  # type: ignore
                style={"height": "700px"},
            ),
        ]
    )
