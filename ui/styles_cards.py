"""Card and metric card component builders.

High-level Dash Bootstrap card components built from design tokens.
"""

import dash_bootstrap_components as dbc
from dash import html

from ui.styles_tokens import BOOTSTRAP_SPACING


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
    """
    Create a standardized Bootstrap card with consistent padding and spacing.

    Args:
        header_content: Content for the card header
        body_content: Content for the card body
        className (str, optional): Additional classes for the card
        card_style (dict, optional): Custom styles for the card
        body_className (str, optional): Additional classes for the card body
        header_className (str, optional): Additional classes for the card header
        footer_content (optional): Content for the card footer (if needed)
        footer_className (str, optional): Additional classes for the card footer
        shadow (str): Shadow size (sm, md, lg, none)

    Returns:
        dbc.Card: A standardized Bootstrap card component
    """
    import dash_bootstrap_components as dbc

    # Add vertical rhythm spacing using our component spacing
    className = f"{className} mb-{BOOTSTRAP_SPACING['3']}"

    # Apply consistent internal padding
    body_className = f"{body_className} py-3 px-3"
    header_className = f"{header_className} py-2 px-3"
    footer_className = f"{footer_className} py-2 px-3"

    # Add shadow class if requested
    if shadow and shadow != "none":
        if shadow in ["sm", "md", "lg"]:
            className = f"{className} shadow-{shadow}"
        else:
            className = f"{className} shadow-sm"  # Default to small shadow

    # Create the card components
    card_components = []

    # Add header if content is provided
    if header_content:
        card_components.append(
            dbc.CardHeader(header_content, className=header_className)
        )

    # Add body content
    card_components.append(dbc.CardBody(body_content, className=body_className))

    # Add footer if content is provided
    if footer_content:
        card_components.append(
            dbc.CardFooter(footer_content, className=footer_className)
        )

    # Create the final card with all components
    return dbc.Card(
        card_components,
        className=className,
        style=card_style,
    )


def create_card_header_with_tooltip(
    title, tooltip_id=None, tooltip_text=None, help_key=None, help_category=None
):
    """
    Create a standardized card header with an optional tooltip
    and help button (Phase 9.2 Progressive Disclosure).

    Args:
        title (str): Card title text
        tooltip_id (str, optional): ID for the tooltip
        tooltip_text (str, optional): Tooltip text content
        help_key (str, optional): Key for comprehensive help content
            (Phase 9.2)
        help_category (str, optional): Category for comprehensive help content
            (Phase 9.2)

    Returns:
        list or html.H4: Components for card header with tooltip
            and optional help button
    """
    import dash_bootstrap_components as dbc
    from dash import html

    # Import the tooltip function and help system
    from ui.tooltip_utils import create_info_tooltip

    # Start with base header
    if not tooltip_id and not help_key:
        # Simple case - just return the H4
        return html.H4(title, className="d-inline")

    # Complex case - build list of components
    header_components = []
    header_components.append(html.H4(title, className="d-inline"))

    # Add tooltip if provided
    if tooltip_id and tooltip_text:
        header_components.append(create_info_tooltip(tooltip_id, tooltip_text))

    # Phase 9.2 Progressive Disclosure: Add help button if help parameters provided
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
    """
    Create a standardized metric card header with optional tooltip and badge.

    Args:
        title: Header title text
        tooltip_text: Optional tooltip content
        tooltip_id: Optional tooltip ID suffix
        badge: Optional badge element aligned to the right

    Returns:
        CardHeader component with consistent layout
    """
    header_children = [html.Span(title, className="metric-card-title")]

    if tooltip_text and tooltip_id:
        from ui.tooltip_utils import create_info_tooltip

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


#######################################################################
# VERTICAL RHYTHM FUNCTIONS
#######################################################################
