import dash_bootstrap_components as dbc
import pandas as pd
from dash import html

from data.schema import DEFAULT_SETTINGS
from ui.trend_components import TREND_COLORS, TREND_ICONS


def create_scope_change_indicator(
    title,
    value,
    threshold=None,
    tooltip=None,
    throughput_ratio=None,
    help_key=None,
    help_category=None,
):

    if threshold is None:
        threshold = DEFAULT_SETTINGS["scope_change_threshold"]

    indicator_id = f"scope-indicator-{title.lower().replace(' ', '-')}"

    high_throughput_ratio = throughput_ratio and throughput_ratio > 1

    if value is None or pd.isna(value):
        icon_class = TREND_ICONS["stable"]
        text_color = TREND_COLORS["stable"]
        bg_color = "rgba(108, 117, 125, 0.1)"
        border_color = "rgba(108, 117, 125, 0.2)"
        value_text = "N/A"
        status_text = "Unknown"
    elif value > threshold and high_throughput_ratio:
        icon_class = TREND_ICONS["up"]
        text_color = TREND_COLORS["down"]
        bg_color = "rgba(220, 53, 69, 0.1)"
        border_color = "rgba(220, 53, 69, 0.2)"
        value_text = f"{value}%"
        status_text = "High Change"
    elif value > threshold * 0.8 and high_throughput_ratio:
        icon_class = TREND_ICONS["up"]
        text_color = "#fd7e14"
        bg_color = "rgba(253, 126, 20, 0.1)"
        border_color = "rgba(253, 126, 20, 0.2)"
        value_text = f"{value}%"
        status_text = "Moderate Change"
    else:
        icon_class = TREND_ICONS["up" if value > 0 else "stable"]
        text_color = "#20c997"
        bg_color = "rgba(32, 201, 151, 0.1)"
        border_color = "rgba(32, 201, 151, 0.2)"
        value_text = f"{value}%"
        status_text = "Normal Change"

    status_class = "ms-1 scope-change-status"
    if value is None or pd.isna(value):
        status_class = f"{status_class} scope-change-status--inherit"

    help_button_title = f"Get detailed help about {title.lower()}"
    help_button_icon_class = "fas fa-question-circle"
    threshold_row_class = (
        "d-flex justify-content-between align-items-baseline "
        "mt-1 text-size-xs text-muted"
    )

    indicator = html.Div(
        className=(
            "compact-trend-indicator scope-change-indicator d-flex "
            "align-items-center p-2 rounded mb-3 w-100"
        ),
        style={
            "--scope-indicator-bg": bg_color,
            "--scope-indicator-border": border_color,
            "--scope-indicator-text": text_color,
        },
        id=indicator_id,
        children=[
            html.Div(
                className=(
                    "trend-icon scope-change-icon me-3 d-flex "
                    "align-items-center justify-content-center rounded-circle"
                ),
                children=html.I(
                    className=f"{icon_class} scope-change-icon-symbol",
                ),
            ),
            html.Div(
                className="trend-info scope-change-info",
                children=[
                    html.Div(
                        className="d-flex justify-content-between align-items-baseline",
                        children=[
                            html.Div(
                                [
                                    html.Span(
                                        title,
                                        className="fw-medium text-size-sm",
                                    ),
                                    (
                                        help_key
                                        and help_category
                                        and html.Span(
                                            [
                                                dbc.Button(
                                                    html.I(
                                                        className=help_button_icon_class
                                                    ),
                                                    id={
                                                        "type": "help-button",
                                                        "category": help_category,
                                                        "key": help_key,
                                                    },
                                                    size="sm",
                                                    color="link",
                                                    className=(
                                                        "text-secondary p-0 ms-1 "
                                                        "scope-change-help-button"
                                                    ),
                                                    title=help_button_title,
                                                )
                                            ],
                                            className="ms-1",
                                        )
                                    )
                                    or None,
                                ],
                                className="d-flex align-items-center",
                            ),
                            html.Span(
                                value_text,
                                className="fw-medium text-size-sm scope-change-value",
                            ),
                        ],
                    ),
                    html.Div(
                        className=threshold_row_class,
                        children=[
                            html.Span(
                                [
                                    "Threshold: ",
                                    html.Span(f"{threshold}%"),
                                    throughput_ratio is not None
                                    and html.Span(
                                        [
                                            " | Throughput Ratio: ",
                                            html.Span(
                                                f"{throughput_ratio:.2f}x",
                                                className=(
                                                    "text-danger"
                                                    if high_throughput_ratio
                                                    else "text-accent"
                                                ),
                                            ),
                                        ]
                                    ),
                                ],
                                className="me-3",
                            ),
                            html.Span(
                                status_text,
                                className=status_class,
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

    if tooltip:
        return html.Div(
            [
                indicator,
                dbc.Tooltip(
                    tooltip,
                    target=indicator_id,
                    className="tooltip-custom",
                    trigger="click",
                    autohide=True,
                ),
            ]
        )

    return indicator


create_scope_creep_indicator = create_scope_change_indicator
