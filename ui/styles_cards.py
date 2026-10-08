import dash_bootstrap_components as dbc
from dash import html

from ui.styles_tokens import BOOTSTRAP_SPACING
from ui.tooltip_utils import create_info_tooltip


def create_standardized_card(
    header_content,
    body_content,
    className="",
    card_style=None,
    body_className="",
    header_className="",
    footer_content=None,
    footer_className="",
    shadow="sm",
):

    className = f"{className} mb-{BOOTSTRAP_SPACING['3']}"

    body_className = f"{body_className} py-3 px-3"
    header_className = f"{header_className} py-2 px-3"
    footer_className = f"{footer_className} py-2 px-3"

    if shadow and shadow != "none":
        if shadow in ["sm", "md", "lg"]:
            className = f"{className} shadow-{shadow}"
        else:
            className = f"{className} shadow-sm"

    card_components = []

    if header_content:
        card_components.append(
            dbc.CardHeader(header_content, className=header_className)
        )

    card_components.append(dbc.CardBody(body_content, className=body_className))

    if footer_content:
        card_components.append(
            dbc.CardFooter(footer_content, className=footer_className)
        )

    return dbc.Card(
        card_components,
        className=className,
        style=card_style,
    )


def create_card_header_with_tooltip(
    title, tooltip_id=None, tooltip_text=None, help_key=None, help_category=None
):

    if not tooltip_id and not help_key:
        return html.H4(title, className="d-inline")

    header_components = []
    header_components.append(html.H4(title, className="d-inline"))

    if tooltip_id and tooltip_text:
        header_components.append(create_info_tooltip(tooltip_id, tooltip_text))

    if help_key and help_category:
        header_components.append(
            html.Span(
                [
                    dbc.Button(
                        html.I(className="fas fa-question-circle"),
                        id={
                            "type": "help-button",
                            "category": help_category,
                            "key": help_key,
                        },
                        size="sm",
                        color="link",
                        className="text-secondary p-1 ms-1",
                        style={
                            "border": "none",
                            "background": "transparent",
                            "fontSize": "0.8rem",
                            "lineHeight": "1",
                        },
                        title=f"Get detailed help about {title.lower()}",
                    )
                ],
                className="ms-1",
            )
        )

    return header_components


def create_metric_card_header(
    title: str,
    tooltip_text: str | None = None,
    tooltip_id: str | None = None,
    badge: dbc.Badge | None = None,
) -> dbc.CardHeader:

    header_children = [html.Span(title, className="metric-card-title")]

    if tooltip_text and tooltip_id:
        header_children.append(
            create_info_tooltip(
                help_text=tooltip_text,
                id_suffix=tooltip_id,
                placement="top",
                variant="dark",
            )
        )

    if badge is not None:
        header_children.append(html.Span(badge, className="ms-auto"))

    return dbc.CardHeader(
        html.Div(header_children, className="metric-card-header w-100")
    )
