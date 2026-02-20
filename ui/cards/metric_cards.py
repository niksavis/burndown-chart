"""
Unified Metric Card Components

This module provides standardized metric card components following the
Bug Analysis Dashboard design pattern. These components ensure consistent
styling and behavior across all dashboard sections.

Design Pattern:
- Icon circle with status-based coloring
- Three lines of information (title/value, secondary, tertiary)
- Responsive layout (full width mobile, configurable desktop columns)
- Equal height cards with h-100 class
"""


import dash_bootstrap_components as dbc
from dash import html


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
    """
    Create a unified metric card following the Bug Analysis Dashboard design pattern.

    This component provides consistent styling across all tabs:
    - Icon circle with status-based coloring
    - Three lines of information (title/value, secondary, tertiary)
    - Responsive layout (full width mobile, configurable desktop columns)
    - Equal height cards with h-100 class

    Args:
        title: Main metric title/label
        value: Primary metric value to display
        icon: FontAwesome icon class (e.g., "fa-check-circle")
        status_color: Primary status color (hex)
        status_bg: Background color with transparency
        status_border: Border color with transparency
        secondary_info: Second line of contextual information
        tertiary_info: Third line of contextual information (date range, etc.)
        help_text: Optional tooltip text for help icon
        card_id: Optional ID for the card element

    Returns:
        dbc.Col: Responsive column containing the metric card

    Example:
        >>> card = create_unified_metric_card(
        ...     title="Resolution Rate",
        ...     value="73.2%",
        ...     icon="fa-check-circle",
        ...     status_color="#28a745",
        ...     status_bg="rgba(40, 167, 69, 0.1)",
        ...     status_border="rgba(40, 167, 69, 0.2)",
        ...     secondary_info="123 closed / 168 total • Good",
        ...     tertiary_info="[Date] May 22, 2025 - Oct 23, 2025",
        ... )
    """
    from ui.style_constants import METRIC_CARD

    # Build card content layers
    card_content = [
        # Icon circle with status color
        html.Div(
            html.I(
                className=f"fas {icon}",
                style={"color": status_color, "fontSize": "1.25rem"},
            ),
            className="d-flex align-items-center justify-content-center rounded-circle me-3",
            style={
                "width": METRIC_CARD["icon_circle_size"],
                "height": METRIC_CARD["icon_circle_size"],
                "backgroundColor": METRIC_CARD["icon_bg"],
                "flexShrink": "0",
            },
        ),
        # Text content column
        html.Div(
            [
                # Line 1: Title and value
                html.Div(
                    [
                        html.Span(f"{title}: ", className="text-muted small"),
                        html.Span(
                            value, className="fw-bold", style={"fontSize": "1.1rem"}
                        ),
                    ],
                    className="mb-1",
                ),
                # Line 2: Secondary information
                html.Div(secondary_info, className="small text-muted")
                if secondary_info
                else None,
                # Line 3: Tertiary information
                html.Div(tertiary_info, className="small text-muted")
                if tertiary_info
                else None,
            ],
            className="flex-grow-1",
            style={"minWidth": "0"},  # Allow text truncation if needed
        ),
        # Optional help icon
        html.I(
            className="fas fa-info-circle text-info ms-2",
            style={"cursor": "pointer", "fontSize": "0.875rem"},
            id=f"help-{card_id}" if card_id else None,
        )
        if help_text
        else None,
    ]

    # Create the card
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

    # Wrap in responsive column (full width mobile, can be adjusted via className)
    return dbc.Col(
        card,
        width=12,  # Full width on mobile
        md=4,  # 3 columns on tablet/desktop
        className="mb-2",
    )


def create_unified_metric_row(cards: list[dbc.Col]) -> dbc.Row:
    """
    Create a responsive row of unified metric cards.

    Args:
        cards: List of metric card columns (from create_unified_metric_card)

    Returns:
        dbc.Row: Row containing metric cards with responsive layout

    Example:
        >>> cards = [
        ...     create_unified_metric_card(...),
        ...     create_unified_metric_card(...),
        ...     create_unified_metric_card(...),
        ... ]
        >>> row = create_unified_metric_row(cards)
    """
    return dbc.Row(
        cards,
        className="g-2 mb-3",  # g-2 for consistent gutter spacing
    )
