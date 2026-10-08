from dash import html

from callbacks.visualization_helpers.pill_components import create_forecast_pill
from configuration import CHART_HELP_TEXTS
from ui import create_compact_trend_indicator
from ui.tooltip_utils import create_info_tooltip


def create_trend_header_with_forecasts(
    trend_data: dict, title: str, icon: str, variant: str, unit: str = "week"
) -> html.Div:

    forecast_pills = []

    if "most_likely_forecast" in trend_data:
        forecast_pills.append(
            create_forecast_pill(
                "Most likely", trend_data["most_likely_forecast"], variant
            )
        )

    if "optimistic_forecast" in trend_data:
        forecast_pills.append(
            create_forecast_pill(
                "Optimistic",
                trend_data["optimistic_forecast"],
                "success",
            )
        )

    if "pessimistic_forecast" in trend_data:
        forecast_pills.append(
            create_forecast_pill(
                "Pessimistic", trend_data["pessimistic_forecast"], "danger"
            )
        )

    forecast_pills.append(
        html.Div(
            html.Small(
                f"{title.split()[1].lower()}/{unit}",
                className="text-muted fst-italic",
            ),
            className="metric-baseline-note",
        )
    )

    tooltip_components = []

    methodology_tooltip = create_info_tooltip(
        f"weekly-chart-methodology-{title.split()[1].lower()}",
        CHART_HELP_TEXTS["weekly_chart_methodology"],
    )
    tooltip_components.append(methodology_tooltip)

    weighted_avg_tooltip = create_info_tooltip(
        f"weighted-average-{title.split()[1].lower()}",
        CHART_HELP_TEXTS["weighted_moving_average"],
    )
    tooltip_components.append(weighted_avg_tooltip)

    exponential_tooltip = create_info_tooltip(
        f"exponential-weighting-{title.split()[1].lower()}",
        CHART_HELP_TEXTS["exponential_weighting"],
    )
    tooltip_components.append(exponential_tooltip)

    forecast_tooltip = create_info_tooltip(
        f"forecast-methodology-{title.split()[1].lower()}",
        CHART_HELP_TEXTS["forecast_vs_actual_bars"],
    )
    tooltip_components.append(forecast_tooltip)

    return html.Div(
        [
            html.Div(
                [
                    html.I(
                        className=f"{icon} me-2 text-{variant}",
                    ),
                    html.Span(
                        title,
                        className="fw-medium",
                    ),
                    html.I(
                        className="fas fa-info-circle text-info ms-2 cursor-pointer",
                        id=f"info-tooltip-weekly-chart-methodology-{title.split()[1].lower()}",
                    ),
                ],
                className="d-flex align-items-center mb-2",
            ),
            html.Div(
                [
                    create_compact_trend_indicator(trend_data, title.split()[1]),
                    html.I(
                        className="fas fa-chart-line text-info ms-2 cursor-pointer",
                        id=f"info-tooltip-weighted-average-{title.split()[1].lower()}",
                    ),
                    html.I(
                        className="fas fa-calculator text-info ms-2 cursor-pointer",
                        id=f"info-tooltip-exponential-weighting-{title.split()[1].lower()}",
                    ),
                    html.I(
                        className="fas fa-chart-bar text-info ms-2 cursor-pointer",
                        id=f"info-tooltip-forecast-methodology-{title.split()[1].lower()}",
                    ),
                ],
                className="d-flex align-items-center gap-1",
            ),
            html.Div(
                forecast_pills,
                className="d-flex flex-wrap align-items-center mt-2 gap-1",
            ),
            html.Div(tooltip_components, className="d-none"),
        ],
        className="col-md-6 col-12 mb-3 pe-md-2",
    )
