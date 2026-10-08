from dash import dcc, html

from configuration.chart_config import get_bug_analysis_chart_config
from visualization.bug_charts import (
    create_bug_forecast_chart,
    create_bug_investment_chart,
    create_bug_trend_chart,
    get_mobile_chart_config,
    get_mobile_chart_layout,
)


def BugTrendChart(
    weekly_stats: list[dict],
    viewport_size: str = "mobile",
    show_error_boundaries: bool = True,
) -> html.Div:

    try:
        fig = create_bug_trend_chart(weekly_stats, viewport_size)

        chart_config = get_bug_analysis_chart_config()

        chart_layout = get_mobile_chart_layout(viewport_size)
        chart_height = chart_layout.get("height", 500)

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
                        (
                            "Red highlighted areas indicate 3+ weeks of bugs "
                            "created exceeding bugs closed."
                        ),
                    ],
                    className="text-muted d-block mt-2",
                ),
            ]
        )

    except Exception as e:
        if show_error_boundaries:
            return html.Div(
                [
                    html.H5("Bug Trends Chart", className="mb-3"),
                    html.Div(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            html.Span(f"Error loading bug trends: {str(e)}"),
                        ],
                        className=(
                            "text-danger p-3 border border-danger rounded bg-light"
                        ),
                    ),
                ],
                className="mb-3",
            )
        else:
            raise


def BugInvestmentChart(
    weekly_stats: list[dict],
    viewport_size: str = "mobile",
    show_error_boundaries: bool = True,
) -> html.Div:

    try:
        fig = create_bug_investment_chart(weekly_stats, viewport_size)

        chart_config = get_bug_analysis_chart_config()

        chart_layout = get_mobile_chart_layout(viewport_size)
        chart_height = chart_layout.get("height", 500)

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
                        (
                            "Bars show bug item counts (left axis), lines "
                            "show complexity in points (right axis). "
                            "Compare created vs resolved to track bug "
                            "investment trends."
                        ),
                    ],
                    className="text-muted d-block mt-2",
                ),
            ]
        )

    except Exception as e:
        if show_error_boundaries:
            return html.Div(
                [
                    html.H5("Bug Investment Chart", className="mb-3"),
                    html.Div(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            html.Span(f"Error loading bug investment chart: {str(e)}"),
                        ],
                        className=(
                            "text-danger p-3 border border-danger rounded bg-light"
                        ),
                    ),
                ],
                className="mb-3",
            )
        else:
            raise


def BugForecastChart(
    forecast: dict, viewport_size: str = "mobile", show_error_boundaries: bool = True
) -> html.Div:

    try:
        fig = create_bug_forecast_chart(forecast, viewport_size)

        chart_config = get_mobile_chart_config(viewport_size)

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
                        className=(
                            "text-danger p-3 border border-danger rounded bg-light"
                        ),
                    ),
                ],
                className="mb-3",
            )
        else:
            raise
