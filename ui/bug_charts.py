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
    Wraps visualization.mobile_charts.create_bug_trend_chart() with error handling.

    Args:
        weekly_stats: List of weekly bug statistics from calculate_bug_statistics()
        viewport_size: "mobile", "tablet", or "desktop"
        show_error_boundaries: Whether to show error boundaries

    Returns:
        Dash Bootstrap Components Card with bug trend chart
    """
    try:
        from visualization.mobile_charts import create_bug_trend_chart

        # Create the chart figure
        fig = create_bug_trend_chart(weekly_stats, viewport_size)

        # Get mobile-optimized config
        from visualization.mobile_charts import get_mobile_chart_config

        chart_config = get_mobile_chart_config(viewport_size)

        # Return chart directly without Card wrapper (like Items per Week tab)
        # This prevents Bootstrap dismissal issues
        return html.Div(
            [
                html.Div(
                    [
                        html.I(className="fas fa-chart-line me-2"),
                        "Bug Trends Over Time",
                    ],
                    className="mb-3 border-bottom pb-2 d-flex align-items-center fw-bold",
                ),
                dcc.Graph(
                    id="bug-trend-graph",
                    figure=fig,
                    config=chart_config,  # type: ignore
                    style={"height": "500px"},
                ),
                html.Small(
                    [
                        html.I(className="fas fa-info-circle me-1"),
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
