"""Forecast section builder for metric cards (Feature 009)."""

from typing import Any

import dash_bootstrap_components as dbc
from dash import html


def create_forecast_section(
    forecast_data: dict[str, Any] | None,
    trend_vs_forecast: dict[str, Any] | None,
    metric_name: str,
    unit: str,
) -> html.Div:
    """Create forecast display section for metric card (Feature 009).

    Displays 4-week weighted forecast benchmark with trend indicator showing
    current performance vs forecast.

    Args:
        forecast_data: Forecast calculation results from calculate_forecast():
            {
                "forecast_value": float,
                "confidence": "established" | "building",
                "weeks_available": int,
                "weights_applied": List[float],
                "historical_values": List[float],
                "forecast_range": Optional[Dict] (for Flow Load only)
            }
        trend_vs_forecast: Trend analysis from calculate_trend_vs_forecast():
            {
                "direction": "up" | "right" | "down",
                "deviation_percent": float,
                "status_text": str,
                "color_class": str,
                "is_good": bool
            }
        metric_name: Metric identifier (e.g., "flow_velocity", "dora_lead_time")
        unit: Metric unit for display

    Returns:
        Div containing forecast display, or empty div if no forecast data

    Example:
        >>> forecast_section = create_forecast_section(
        ...     forecast_data={
        ...         "forecast_value": 11.9,
        ...         "confidence": "established",
        ...     },
        ...     trend_vs_forecast={
        ...         "direction": "up",
        ...         "deviation_percent": 26.1,
        ...     },
        ...     metric_name="flow_velocity",
        ...     unit="items/week"
        ... )
    """
    # No forecast data - return empty div
    if not forecast_data:
        return html.Div()

    forecast_value = forecast_data.get("forecast_value")
    confidence = forecast_data.get("confidence", "building")
    # Support both keys for backwards compatibility
    # (weeks_with_data is preferred, weeks_available is fallback)
    weeks_with_data = forecast_data.get("weeks_with_data") or forecast_data.get(
        "weeks_available"
    )
    used_non_zero_filter = forecast_data.get(
        "used_non_zero_filter", False
    )  # Whether zeros were filtered

    # Format forecast value - standard formatting for all metrics
    if forecast_value is not None:
        forecast_display = f"{forecast_value:.2f}"
    else:
        forecast_display = "N/A"

    # Build forecast section children
    forecast_children = []

    # Build forecast label based on metric type and data availability
    # Duration metrics (filtered zeros): "(3w with data)"
    # - emphasizes found non-zero weeks
    # Count/rate metrics (kept zeros): "(4w)" - standard label
    if weeks_with_data:
        if used_non_zero_filter:
            # Duration metric - filtered out zero weeks, always show "with data"
            weeks_label = f" ({weeks_with_data}w with data)"
        else:
            # Count/rate metric - used all weeks including zeros
            weeks_label = f" ({weeks_with_data}w)"
    else:
        weeks_label = ""

    # Confidence badge (building baseline vs established) - only show if building
    if confidence == "building" and weeks_with_data and weeks_with_data < 4:
        confidence_badge = dbc.Badge(
            "Building baseline",
            color="secondary",
            className="ms-2",
            style={"fontSize": "0.65rem", "fontWeight": "500"},
        )
    else:
        confidence_badge = None

    # Forecast value line
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

    # Trend vs forecast (if available)
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

    # Wrap in container with subtle styling
    return html.Div(
        forecast_children,
        className="mt-2 mb-2",
        style={
            "borderTop": "1px solid #dee2e6",
            "paddingTop": "0.5rem",
        },
    )
