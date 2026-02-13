"""Bug chart UI components.

Provides UI wrappers for bug visualization charts with proper error handling
and mobile optimization.
"""

#######################################################################
# IMPORTS
#######################################################################
from typing import Dict, List
from dash import dcc, html


def BugTrendChart(
    weekly_stats: List[Dict],
    viewport_size: str = "mobile",
    show_error_boundaries: bool = True,
) -> html.Div:
    """
    Create bug trend chart component wrapper.

    Implements T038 - BugTrendChart component wrapper.
    Wraps visualization.bug_charts.create_bug_trend_chart() with error handling.

    Args:
        weekly_stats: List of weekly bug statistics from calculate_bug_statistics()
        viewport_size: "mobile", "tablet", or "desktop"
        show_error_boundaries: Whether to show error boundaries

    Returns:
        Dash Bootstrap Components Card with bug trend chart
    """
    try:
        from visualization.bug_charts import (
            create_bug_trend_chart,
            get_mobile_chart_layout,
        )
        from configuration.chart_config import get_bug_analysis_chart_config

        # Create the chart figure
        fig = create_bug_trend_chart(weekly_stats, viewport_size)

        # Get unified chart config for consistency across the app
        chart_config = get_bug_analysis_chart_config()

        chart_layout = get_mobile_chart_layout(viewport_size)
        chart_height = chart_layout.get("height", 500)

        # Return chart directly without Card wrapper (like Items per Week tab)
        # This prevents Bootstrap dismissal issues
        return html.Div(
            [
                html.H5(
                    [
                        html.I(
                            className="fas fa-chart-line me-2",
                            style={"color": "#dc3545"},
                        ),
                        "Bug Trends Over Time",
                    ],
                    className="mb-3 mt-4",
                ),
                dcc.Graph(
                    id="bug-trend-graph",
                    figure=fig,
                    config=chart_config,  # type: ignore
                    style={"height": f"{chart_height}px"},
                ),
                html.Small(
                    [
                        html.I(className="fas fa-info-circle me-1 text-info"),
                        "Red highlighted areas indicate 3+ weeks of bugs created exceeding bugs closed.",
                    ],
                    className="text-muted d-block mt-2",
                ),
            ]
        )

    except Exception as e:
        # Error boundary - return error message without Card
        if show_error_boundaries:
            return html.Div(
                [
                    html.H5("Bug Trends Chart", className="mb-3"),
                    html.Div(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            html.Span(f"Error loading bug trends: {str(e)}"),
                        ],
                        className="text-danger p-3 border border-danger rounded bg-light",
                    ),
                ],
                className="mb-3",
            )
        else:
            # Re-raise exception if error boundaries are disabled
            raise


def BugInvestmentChart(
    weekly_stats: List[Dict],
    viewport_size: str = "mobile",
    show_error_boundaries: bool = True,
) -> html.Div:
    """
    Create bug investment chart component wrapper.

    Implements T053 - BugInvestmentChart component wrapper.
    Wraps visualization.bug_charts.create_bug_investment_chart() with error handling.

    Args:
        weekly_stats: List of weekly bug statistics from calculate_bug_statistics()
        viewport_size: "mobile", "tablet", or "desktop"
        show_error_boundaries: Whether to show error boundaries

    Returns:
        Dash Bootstrap Components Div with bug investment chart
    """
    try:
        from visualization.bug_charts import (
            create_bug_investment_chart,
            get_mobile_chart_layout,
        )
        from configuration.chart_config import get_bug_analysis_chart_config

        # Create the chart figure
        fig = create_bug_investment_chart(weekly_stats, viewport_size)

        # Get unified chart config for consistency across the app
        chart_config = get_bug_analysis_chart_config()

        chart_layout = get_mobile_chart_layout(viewport_size)
        chart_height = chart_layout.get("height", 500)

        # Return chart directly without Card wrapper (consistent with BugTrendChart)
        return html.Div(
            [
                html.H5(
                    [
                        html.I(
                            className="fas fa-coins me-2",
                            style={"color": "#fd7e14"},
                        ),
                        "Bug Investment: Items vs Points",
                    ],
                    className="mb-3 mt-4",
                ),
                dcc.Graph(
                    id="bug-investment-graph",
                    figure=fig,
                    config=chart_config,  # type: ignore
                    style={"height": f"{chart_height}px"},
                ),
                html.Small(
                    [
                        html.I(className="fas fa-info-circle me-1 text-info"),
                        "Bars show bug item counts (left axis), lines show complexity in points (right axis). Compare created vs resolved to track bug investment trends.",
                    ],
                    className="text-muted d-block mt-2",
                ),
            ]
        )

    except Exception as e:
        # Error boundary - return error message without Card
        if show_error_boundaries:
            return html.Div(
                [
                    html.H5("Bug Investment Chart", className="mb-3"),
                    html.Div(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            html.Span(f"Error loading bug investment chart: {str(e)}"),
                        ],
                        className="text-danger p-3 border border-danger rounded bg-light",
                    ),
                ],
                className="mb-3",
            )
        else:
            # Re-raise exception if error boundaries are disabled
            raise


def BugForecastChart(
    forecast: Dict, viewport_size: str = "mobile", show_error_boundaries: bool = True
) -> html.Div:
    """
    Create bug forecast chart component wrapper.

    Implements T099 - BugForecastChart component wrapper.
    Wraps visualization.bug_charts.create_bug_forecast_chart() with error handling.

    Args:
        forecast: Bug forecast dictionary from forecast_bug_resolution()
        viewport_size: "mobile", "tablet", or "desktop"
        show_error_boundaries: Whether to show error boundaries

    Returns:
        Dash Bootstrap Components Div with bug forecast chart
    """
    try:
        from visualization.bug_charts import create_bug_forecast_chart

        # Create the chart figure
        fig = create_bug_forecast_chart(forecast, viewport_size)

        # Get mobile-optimized config
        from visualization.bug_charts import get_mobile_chart_config

        chart_config = get_mobile_chart_config(viewport_size)

        # Return chart directly without Card wrapper (consistent with other bug charts)
        return html.Div(
            [
                html.Div(
                    [
                        html.I(className="fas fa-calendar-alt me-2"),
                        html.Strong("Bug Resolution Forecast"),
                    ],
                    className="mb-2",
                    style={"fontSize": "1.1rem"},
                ),
                dcc.Graph(
                    figure=fig,
                    config=chart_config,  # type: ignore
                    responsive=True,
                    style={"height": "350px" if viewport_size == "mobile" else "450px"},
                ),
            ],
            className="mb-3",
        )

    except Exception as e:
        if show_error_boundaries:
            return html.Div(
                [
                    html.H5("Bug Forecast Chart", className="mb-3"),
                    html.Div(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            html.Span(f"Error loading bug forecast chart: {str(e)}"),
                        ],
                        className="text-danger p-3 border border-danger rounded bg-light",
                    ),
                ],
                className="mb-3",
            )
        else:
            # Re-raise exception if error boundaries are disabled
            raise
