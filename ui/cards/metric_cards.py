import dash_bootstrap_components as dbc
from dash import html

from ui.style_constants import METRIC_CARD


def create_unified_metric_card(
    title: str,
    value: str,
    icon: str,
    status_color: str,
    status_bg: str,
    status_border: str,
    secondary_info: str = "",
    tertiary_info: str = "",
    help_text: str = "",
    card_id: str = "",
) -> dbc.Col:

    card_content = [
        html.Div(
            html.I(
                className=f"fas {icon}",
                style={"color": status_color, "fontSize": "1.25rem"},
            ),
            className=(
                "d-flex align-items-center justify-content-center rounded-circle me-3"
            ),
            style={
                "width": METRIC_CARD["icon_circle_size"],
                "height": METRIC_CARD["icon_circle_size"],
                "backgroundColor": METRIC_CARD["icon_bg"],
                "flexShrink": "0",
            },
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Span(f"{title}: ", className="text-muted small"),
                        html.Span(
                            value, className="fw-bold", style={"fontSize": "1.1rem"}
                        ),
                    ],
                    className="mb-1",
                ),
                html.Div(secondary_info, className="small text-muted")
                if secondary_info
                else None,
                html.Div(tertiary_info, className="small text-muted")
                if tertiary_info
                else None,
            ],
            className="flex-grow-1",
            style={"minWidth": "0"},
        ),
        html.I(
            className="fas fa-info-circle text-info ms-2",
            style={"cursor": "pointer", "fontSize": "0.875rem"},
            id=f"help-{card_id}" if card_id else None,
        )
        if help_text
        else None,
    ]

    card = html.Div(
        card_content,
        className="compact-trend-indicator d-flex align-items-center p-3 rounded h-100",
        style={
            "backgroundColor": status_bg,
            "border": f"{METRIC_CARD['border_width']} solid {status_border}",
            "minHeight": METRIC_CARD["min_height"],
        },
        id=card_id if card_id else None,
    )

    return dbc.Col(
        card,
        width=12,
        md=4,
        className="mb-2",
    )


def create_unified_metric_row(cards: list[dbc.Col]) -> dbc.Row:

    return dbc.Row(
        cards,
        className="g-2 mb-3",
    )
