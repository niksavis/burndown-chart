from dash import html


def create_forecast_pill(forecast_type: str, value: float, variant: str) -> html.Div:

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
