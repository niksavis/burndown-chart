from dash import html

from ui.help_system import create_help_button_with_tooltip
from ui.tooltip_utils import create_info_tooltip
from ui.trend_components import TREND_COLORS, TREND_ICONS


def _create_header_with_icon(
    icon_class: str,
    title: str,
    color: str = "#20c997",
    tooltip_id: str | None = None,
    tooltip_text: str | None = None,
    help_key: str | None = None,
    help_category: str | None = None,
) -> html.H5:

    header_content = [
        html.I(
            className=f"{icon_class} me-2",
            style={"color": color},
        ),
        title,
    ]

    if help_key and help_category:
        header_content.append(
            html.Span(
                [
                    create_help_button_with_tooltip(
                        tooltip_text or "Click for detailed information",
                        help_key,
                        help_category,
                        tooltip_placement="bottom",
                    )
                ],
                className="ms-2",
            )
        )
    elif tooltip_id and tooltip_text:
        header_content.append(create_info_tooltip(tooltip_id, tooltip_text))

    return html.H5(
        header_content,
        className="mb-3 border-bottom pb-2 d-flex align-items-center",
    )


def _create_forecast_row(
    label, completion_date, timeframe, bg_color, is_highlighted=False, icon=None
):
    row_classes = ["forecast-row"]
    label_classes = ["label-text"]
    icon_classes = ["forecast-row-icon"]

    if is_highlighted:
        row_classes.append("highlighted")
        label_classes.append("highlighted")
        if "40,167,69" in bg_color:
            row_classes.append("success")
            icon_classes.append("success")
        else:
            row_classes.append("danger")
            icon_classes.append("danger")

    row_style = {"backgroundColor": bg_color}

    if isinstance(label, list):
        label_content = [html.Span(label[0], className=" ".join(label_classes))]
        if len(label) > 1:
            label_content.extend(label[1:])
    else:
        label_content = [html.Span(label, className=" ".join(label_classes))]

    if icon and is_highlighted:
        label_content.append(
            html.Span(html.I(className=f"{icon} ms-2 {' '.join(icon_classes)}"))
        )

    return html.Div(
        className=" ".join(row_classes),
        style=row_style,
        children=[
            html.Div(label_content, className="forecast-row-label"),
            html.Div(
                html.Span(
                    completion_date,
                    className="fw-medium",
                ),
                className="forecast-row-date",
            ),
            html.Div(html.Small(timeframe), className="forecast-row-timeframe"),
        ],
    )


def _get_trend_icon_and_color(trend_value):

    if abs(trend_value) < 5:
        return TREND_ICONS["stable"], TREND_COLORS["stable"]
    elif trend_value > 0:
        return TREND_ICONS["up"], TREND_COLORS["up"]
    else:
        return TREND_ICONS["down"], TREND_COLORS["down"]
