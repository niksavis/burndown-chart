"""
UI Component Builders for Visualizations

This module contains helper functions for building UI components
used in visualization callbacks, such as headers with trend indicators.
"""

from dash import html

from callbacks.visualization_helpers.pill_components import create_forecast_pill
from configuration import CHART_HELP_TEXTS
from ui import create_compact_trend_indicator
from ui.tooltip_utils import create_info_tooltip


def create_trend_header_with_forecasts(
    trend_data: dict, title: str, icon: str, variant: str, unit: str = "week"
) -> html.Div:
    """
    Create a header with trend indicator and forecast pills.

    Args:
        trend_data: Dictionary with trend and forecast data (from prepare_trend_data)
        title: Title text for the header (e.g., "Weekly Items")
        icon: Icon class for the header (e.g., "fas fa-tasks")
        variant: Color variant for the header icon (e.g., "brand")
        unit: Unit for trend values (default: "week")

    Returns:
        html.Div: Header component with trend indicator, forecast pills, and tooltips

    Example:
        >>> header = create_trend_header_with_forecasts(
        ...     items_trend,
        ...     "Weekly Items",
        ...     "fas fa-tasks",
        ...     "brand"
        ... )
    """
    # Create forecast pills based on available forecast data
    forecast_pills = []

    # Most likely forecast pill
    if "most_likely_forecast" in trend_data:
        forecast_pills.append(
            create_forecast_pill(
                "Most likely", trend_data["most_likely_forecast"], variant
            )
        )

    # Optimistic forecast pill
    if "optimistic_forecast" in trend_data:
        forecast_pills.append(
            create_forecast_pill(
                "Optimistic",
                trend_data["optimistic_forecast"],
                "success",
            )
        )

    # Pessimistic forecast pill
    if "pessimistic_forecast" in trend_data:
        # Use consistent red color for pessimistic across both items and points
        forecast_pills.append(
            create_forecast_pill(
                "Pessimistic", trend_data["pessimistic_forecast"], "danger"
            )
        )

    # Add unit indicator
    forecast_pills.append(
        html.Div(
            html.Small(
                f"{title.split()[1].lower()}/{unit}",
                className="text-muted fst-italic",
            ),
            className="metric-baseline-note",
        )
    )

    # Create tooltip components list for proper rendering
    tooltip_components = []

    # Create methodology tooltip
    methodology_tooltip = create_info_tooltip(
        f"weekly-chart-methodology-{title.split()[1].lower()}",
        CHART_HELP_TEXTS["weekly_chart_methodology"],
    )
    tooltip_components.append(methodology_tooltip)

    # Create weighted average tooltip
    weighted_avg_tooltip = create_info_tooltip(
        f"weighted-average-{title.split()[1].lower()}",
        CHART_HELP_TEXTS["weighted_moving_average"],
    )
    tooltip_components.append(weighted_avg_tooltip)

    # Create exponential weighting tooltip
    exponential_tooltip = create_info_tooltip(
        f"exponential-weighting-{title.split()[1].lower()}",
        CHART_HELP_TEXTS["exponential_weighting"],
    )
    tooltip_components.append(exponential_tooltip)

    # Create forecast methodology tooltip
    forecast_tooltip = create_info_tooltip(
        f"forecast-methodology-{title.split()[1].lower()}",
        CHART_HELP_TEXTS["forecast_vs_actual_bars"],
    )
    tooltip_components.append(forecast_tooltip)

    # Create the header component with tooltips rendered separately
    return html.Div(
        [
            # Header with icon and title - enhanced with tooltips
            html.Div(
                [
                    html.I(
                        className=f"{icon} me-2 text-{variant}",
                    ),
                    html.Span(
                        title,
                        className="fw-medium",
                    ),
                    # Add methodology tooltip icon only
                    html.I(
                        className="fas fa-info-circle text-info ms-2 cursor-pointer",
                        id=f"info-tooltip-weekly-chart-methodology-{title.split()[1].lower()}",
                    ),
                ],
                className="d-flex align-items-center mb-2",
            ),
            # Enhanced trend indicator with weighted average tooltip
            html.Div(
                [
                    create_compact_trend_indicator(trend_data, title.split()[1]),
                    # Add weighted average explanation tooltip icon
                    html.I(
                        className="fas fa-chart-line text-info ms-2 cursor-pointer",
                        id=f"info-tooltip-weighted-average-{title.split()[1].lower()}",
                    ),
                    # Add exponential weighting details tooltip icon
                    html.I(
                        className="fas fa-calculator text-info ms-2 cursor-pointer",
                        id=f"info-tooltip-exponential-weighting-{title.split()[1].lower()}",
                    ),
                    # Add forecast methodology tooltip icon
                    html.I(
                        className="fas fa-chart-bar text-info ms-2 cursor-pointer",
                        id=f"info-tooltip-forecast-methodology-{title.split()[1].lower()}",
                    ),
                ],
                className="d-flex align-items-center gap-1",
            ),
            # Enhanced forecast pills
            html.Div(
                forecast_pills,
                className="d-flex flex-wrap align-items-center mt-2 gap-1",
            ),
            # Add all tooltip components at the end for proper rendering
            html.Div(tooltip_components, className="d-none"),
        ],
        className="col-md-6 col-12 mb-3 pe-md-2",
    )
