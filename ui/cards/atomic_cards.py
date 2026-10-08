import re
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ui.help_system import create_dashboard_metric_tooltip
from ui.style_constants import get_card_style, get_color, get_spacing
from ui.styles import create_metric_card_header


def create_info_card(
    title: str | html.Span,
    value: Any,
    icon: str = "",
    subtitle: str = "",
    variant: str = "default",
    clickable: bool = False,
    click_id: str = "",
    size: str = "md",
    **kwargs,
) -> dbc.Card:

    title_str = str(title) if isinstance(title, str) else "component-title"
    if not title or (isinstance(title, str) and title.strip() == ""):
        raise ValueError("Title is required and cannot be empty")

    if value is None or str(value).strip() == "":
        raise ValueError("Value is required and cannot be empty")

    valid_variants = ["default", "primary", "success", "warning", "danger"]
    if variant not in valid_variants:
        raise ValueError(
            f"Invalid variant '{variant}'. Must be one of: {', '.join(valid_variants)}"
        )

    if clickable and (not click_id or click_id.strip() == ""):
        raise ValueError("click_id is required when clickable=True")

    title_slug = re.sub(r"[^a-z0-9]+", "-", title_str.lower()).strip("-")
    card_id = f"card-{title_slug}"
    if click_id:
        card_id += f"-{click_id}"

    card_style = get_card_style(variant=variant, elevated=clickable)

    icon_element = None
    if icon:
        icon_class = f"fas fa-{icon}" if not icon.startswith("fa-") else icon
        icon_color = get_color(
            f"{variant}-500" if variant != "default" else "neutral-600"
        )
        icon_element = html.I(
            className=icon_class,
            style={
                "fontSize": "1.5rem" if size == "lg" else "1.25rem",
                "color": icon_color,
                "marginRight": get_spacing("sm"),
            },
        )

    header_content = []
    if icon_element:
        header_content.append(icon_element)

    if isinstance(title, str):
        header_content.append(html.Span(title, style={"fontWeight": "600"}))
    else:
        header_content.append(title)

    card_header = create_metric_card_header(
        title=title_str,
    )

    value_style = {
        "fontSize": "2.5rem" if size == "lg" else "2rem" if size == "md" else "1.5rem",
        "fontWeight": "700",
        "color": get_color(f"{variant}-600" if variant != "default" else "neutral-900"),
        "lineHeight": "1.2",
        "marginBottom": get_spacing("xs") if subtitle else "0",
    }

    body_content = [html.Div(str(value), style=value_style)]

    if subtitle:
        subtitle_style = {
            "fontSize": "0.875rem",
            "color": get_color("neutral-600"),
            "marginTop": get_spacing("xs"),
        }
        body_content.append(html.Div(subtitle, style=subtitle_style))

    card_body = dbc.CardBody(
        body_content,
        style={
            "padding": get_spacing("md" if size == "lg" else "sm"),
            "textAlign": "center",
        },
    )

    card_footer = None
    if clickable:
        footer_link = html.A(
            [
                "View Details ",
                html.I(className="fas fa-arrow-right", style={"marginLeft": "0.25rem"}),
            ],
            style={
                "fontSize": "0.875rem",
                "color": get_color("primary-500"),
                "textDecoration": "none",
                "fontWeight": "500",
            },
        )
        card_footer = dbc.CardFooter(
            footer_link,
            style={
                "backgroundColor": get_color("neutral-50"),
                "borderTop": f"1px solid {get_color('neutral-200')}",
                "padding": get_spacing("sm"),
                "textAlign": "center",
            },
        )

    custom_style = kwargs.pop("style", {})
    final_style = {**card_style, **custom_style}

    if clickable:
        final_style.update(
            {
                "cursor": "pointer",
                "transition": "transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out",
            }
        )
        custom_class = kwargs.pop("className", "")
        kwargs["className"] = f"{custom_class} card-clickable".strip()

    card_components = [card_header, card_body]
    if card_footer:
        card_components.append(card_footer)

    return dbc.Card(
        card_components,
        id=card_id,
        style=final_style,
        **kwargs,
    )


def create_dashboard_metrics_card(
    metrics: dict,
    card_type: str,
    variant: str = "default",
    **kwargs,
) -> dbc.Card:

    valid_types = ["forecast", "velocity", "remaining", "pert"]
    if card_type not in valid_types:
        raise ValueError(
            f"Invalid card_type '{card_type}'. Must be one of: {', '.join(valid_types)}"
        )

    card_configs = {
        "forecast": {
            "title": "Completion Forecast",
            "icon": "calendar-check",
            "variant": "default",
            "value_field": "days_to_completion",
            "value_suffix": " days",
            "subtitle_template": (
                "{completion_percentage}% complete • "
                "{completion_confidence}% confidence"
            ),
            "help_key": "completion_forecast",
        },
        "velocity": {
            "title": "Current Velocity",
            "icon": "tachometer-alt",
            "variant": "default",
            "value_field": "current_velocity_items",
            "value_suffix": " items/week",
            "subtitle_template": (
                "{current_velocity_points} pts/week • {velocity_trend}"
            ),
            "help_key": "velocity_trend",
        },
        "remaining": {
            "title": "Remaining Work",
            "icon": "tasks",
            "variant": "default",
            "value_field": "remaining_items",
            "value_suffix": " items",
            "subtitle_template": "{remaining_points} story points remaining",
            "help_key": "remaining_work",
        },
        "pert": {
            "title": "Timeline Range",
            "icon": "clock",
            "variant": "default",
            "value_field": "days_to_deadline",
            "value_suffix": " days to deadline",
            "subtitle_template": "Forecast: {days_to_completion} days",
            "help_key": "pert_expected",
        },
    }

    config = card_configs[card_type]

    if variant != "default":
        config["variant"] = variant

    value = metrics.get(config["value_field"], "N/A")
    if value is not None and value != "N/A":
        value = f"{value}{config['value_suffix']}"
    else:
        value = "N/A"

    try:
        subtitle = config["subtitle_template"].format(**metrics)
    except KeyError, ValueError:
        subtitle = ""

    title_with_help = html.Span(
        [
            html.Span(config["title"]),
            html.Span(
                create_dashboard_metric_tooltip(config["help_key"]),
                style={"marginLeft": "0.5rem"},
            ),
        ],
        style={"display": "flex", "alignItems": "center"},
    )

    kwargs.pop("id", None)

    return create_info_card(
        title=title_with_help,
        value=value,
        icon=config["icon"],
        subtitle=subtitle,
        variant=config["variant"],
        **kwargs,
    )
