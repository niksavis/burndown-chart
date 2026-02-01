"""
Atomic Card Components

This module provides atomic (reusable, self-contained) card components
that serve as building blocks for dashboard layouts. These components
follow the component builder contract specification.

Design Principles:
- Single responsibility per component
- Configurable via parameters
- Consistent styling via design tokens
- Type-safe with full annotations
- Error-resistant with validation

Atomic Cards:
- create_info_card: Generic info display with icon, value, unit
- create_dashboard_metrics_card: Specialized dashboard metric cards
"""

import re
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ui.style_constants import get_card_style, get_color, get_spacing


def create_info_card(
    title: str | html.Span,  # Accept both string and Dash component
    value: Any,
    icon: str = "",
    subtitle: str = "",
    variant: str = "default",
    clickable: bool = False,
    click_id: str = "",
    size: str = "md",
    **kwargs,
) -> dbc.Card:
    """
    Create information display card for metrics/statistics.

    This function follows the component builder contract specification
    in specs/006-ux-ui-redesign/contracts/component-builders.md

    Args:
        title: Card title/label (required) - can be string or Dash component for rich formatting
        value: Primary value to display (required)
        icon: Optional Font Awesome icon name (without "fa-" prefix)
        subtitle: Optional subtitle/description
        variant: Color variant - "default", "primary", "success", "warning", "danger"
        clickable: Whether card should be interactive
        click_id: ID for click callback (required if clickable=True)
        size: Card size - "sm", "md", "lg"
        **kwargs: Additional props (className, style, etc.)

    Returns:
        dbc.Card with standardized info display layout

    Raises:
        ValueError: If title or value is empty, or clickable=True but click_id empty

    Examples:
        >>> create_info_card("Days to Completion", 53, icon="calendar-check",
        ...                  subtitle="Based on current velocity", variant="primary")
        >>> create_info_card("Remaining Items", 42, icon="tasks",
        ...                  clickable=True, click_id="goto-burndown")

    ID Pattern: card-{title-slugified}[-{click_id}]

    Layout:
        - Header: icon + title
        - Body: large value + subtitle
        - Footer: optional action link (if clickable)
    """
    # Validation
    # For component titles, we can't easily validate - just check for None/empty
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

    # Generate card ID - use title_str for slugification
    title_slug = re.sub(r"[^a-z0-9]+", "-", title_str.lower()).strip("-")
    card_id = f"card-{title_slug}"
    if click_id:
        card_id += f"-{click_id}"

    # Get card styling from design tokens
    card_style = get_card_style(variant=variant, elevated=clickable)

    # Build icon if provided
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

    # Build header with icon and title
    header_content = []
    if icon_element:
        header_content.append(icon_element)

    # Handle both string and component titles
    if isinstance(title, str):
        header_content.append(html.Span(title, style={"fontWeight": "600"}))
    else:
        # Title is already a component (e.g., with help icon)
        header_content.append(title)

    card_header = dbc.CardHeader(
        header_content,
        style={
            "display": "flex",
            "alignItems": "center",
            "backgroundColor": get_color("neutral-50"),
            "borderBottom": f"1px solid {get_color('neutral-200')}",
            "padding": get_spacing("sm" if size == "sm" else "md"),
        },
    )

    # Build body with value and subtitle
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

    # Build optional footer for clickable cards
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

    # Merge custom styles with design token styles
    custom_style = kwargs.pop("style", {})
    final_style = {**card_style, **custom_style}

    # Add hover effect for clickable cards
    if clickable:
        final_style.update(
            {
                "cursor": "pointer",
                "transition": "transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out",
            }
        )
        # Add className for hover effect via CSS
        custom_class = kwargs.pop("className", "")
        kwargs["className"] = f"{custom_class} card-clickable".strip()

    # Build card
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
    """
    Create specialized dashboard metrics card with enhanced visualization.

    This function supports User Story 2: Dashboard as Primary Landing View.
    It creates metric cards specifically designed for the Dashboard tab with
    appropriate icons, colors, and formatting for each metric type.

    User Story 6: Contextual Help System - Adds help icons to metric cards.

    Args:
        metrics: DashboardMetrics dictionary from calculate_dashboard_metrics()
        card_type: Type of metric card - "forecast", "velocity", "remaining", "pert"
        variant: Color variant override (auto-selected based on card_type if "default")
        **kwargs: Additional props passed to dbc.Card

    Returns:
        dbc.Card: Formatted dashboard metrics card with help icon

    Raises:
        ValueError: If card_type is invalid

    Example:
        >>> metrics = calculate_dashboard_metrics(stats, settings)
        >>> card = create_dashboard_metrics_card(metrics, "forecast")

    Card Types:
        - "forecast": Completion forecast with confidence
        - "velocity": Current velocity trend
        - "remaining": Remaining work (items/points)
        - "pert": PERT timeline estimates
    """
    # Import help system function for tooltips
    from ui.help_system import create_dashboard_metric_tooltip

    # Validate card type
    valid_types = ["forecast", "velocity", "remaining", "pert"]
    if card_type not in valid_types:
        raise ValueError(
            f"Invalid card_type '{card_type}'. Must be one of: {', '.join(valid_types)}"
        )

    # Configure card based on type
    # Map card_type to help content key
    card_configs = {
        "forecast": {
            "title": "Completion Forecast",
            "icon": "calendar-check",
            "variant": "default",
            "value_field": "days_to_completion",
            "value_suffix": " days",
            "subtitle_template": "{completion_percentage}% complete • {completion_confidence}% confidence",
            "help_key": "completion_forecast",
        },
        "velocity": {
            "title": "Current Velocity",
            "icon": "tachometer-alt",
            "variant": "default",
            "value_field": "current_velocity_items",
            "value_suffix": " items/week",
            "subtitle_template": "{current_velocity_points} pts/week • {velocity_trend}",
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

    # Override variant if specified
    if variant != "default":
        config["variant"] = variant

    # Extract value
    value = metrics.get(config["value_field"], "N/A")
    if value is not None and value != "N/A":
        value = f"{value}{config['value_suffix']}"
    else:
        value = "N/A"

    # Format subtitle with metrics
    try:
        subtitle = config["subtitle_template"].format(**metrics)
    except (KeyError, ValueError):
        subtitle = ""

    # Create title with help icon
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

    # Extract 'id' from kwargs to avoid conflict with create_info_card's auto-generated ID
    # We'll let create_info_card generate the ID based on the title
    # The dashboard callback uses container IDs, not the card IDs directly
    kwargs.pop("id", None)  # Remove any id from kwargs

    # Create card using create_info_card
    return create_info_card(
        title=title_with_help,
        value=value,
        icon=config["icon"],
        subtitle=subtitle,
        variant=config["variant"],
        **kwargs,
    )
