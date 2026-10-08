from typing import Any

import dash_bootstrap_components as dbc
from dash import html


def create_forecast_section(
    forecast_data: dict[str, Any] | None,
    trend_vs_forecast: dict[str, Any] | None,
    metric_name: str,
    unit: str,
) -> html.Div:

    if not forecast_data:
        return html.Div()

    forecast_value = forecast_data.get("forecast_value")
    confidence = forecast_data.get("confidence", "building")
    weeks_with_data = forecast_data.get("weeks_with_data") or forecast_data.get(
        "weeks_available"
    )
    used_non_zero_filter = forecast_data.get("used_non_zero_filter", False)

    if forecast_value is not None:
        forecast_display = f"{forecast_value:.2f}"
    else:
        forecast_display = "N/A"

    forecast_children = []

    if weeks_with_data:
        if used_non_zero_filter:
            weeks_label = f" ({weeks_with_data}w with data)"
        else:
            weeks_label = f" ({weeks_with_data}w)"
    else:
        weeks_label = ""

    if confidence == "building" and weeks_with_data and weeks_with_data < 4:
        confidence_badge = dbc.Badge(
            "Building baseline",
            color="secondary",
            className="ms-2",
            style={"fontSize": "0.65rem", "fontWeight": "500"},
        )
    else:
        confidence_badge = None

    forecast_children.append(
        html.Div(
            [
                html.Span(
                    "Forecast: ",
                    className="text-muted",
                    style={"fontSize": "0.85rem"},
                ),
                html.Span(
                    forecast_display,
                    className="fw-bold",
                    style={"fontSize": "0.85rem"},
                ),
                html.Span(
                    f" {unit}",
                    className="text-muted",
                    style={"fontSize": "0.75rem"},
                ),
                html.Span(
                    weeks_label,
                    className="text-muted",
                    style={"fontSize": "0.7rem"},
                ),
                confidence_badge if confidence_badge else html.Span(),
            ],
            className="text-center mb-1",
        )
    )

    if trend_vs_forecast:
        direction = trend_vs_forecast.get("direction", "\u2192")
        status_text = trend_vs_forecast.get("status_text", "On track")
        color_class = trend_vs_forecast.get("color_class", "text-secondary")

        forecast_children.append(
            html.Div(
                [
                    html.Span(
                        direction,
                        className="me-1",
                        style={"fontFamily": "inherit", "fontVariantEmoji": "text"},
                    ),
                    html.Span(status_text, className=f"{color_class}"),
                ],
                className="text-center small",
                style={"fontSize": "0.8rem", "fontWeight": "500"},
            )
        )

    return html.Div(
        forecast_children,
        className="mt-2 mb-2",
        style={
            "borderTop": "1px solid #dee2e6",
            "paddingTop": "0.5rem",
        },
    )
