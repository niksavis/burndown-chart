"""
Pill Component Helpers

Helper functions for creating forecast pill components with consistent styling.
"""

from dash import html


def create_forecast_pill(forecast_type: str, value: float, variant: str) -> html.Div:
    """
    Create a forecast pill component with consistent styling.

    Args:
        forecast_type: Type of forecast (e.g., 'Most likely', 'Optimistic', 'Pessimistic')
        value: Forecast value
        variant: Color variant for styling the pill

    Returns:
        html.Div: Forecast pill component
    """
    return html.Div(
        [
            html.I(className="fas fa-chart-line me-1 forecast-icon"),
            html.Small(
                [
                    f"{forecast_type}: ",
                    html.Strong(
                        f"{value:.2f}",
                        className="forecast-value",
                    ),
                ],
            ),
        ],
        className=f"forecast-pill forecast-pill--{variant}",
    )
