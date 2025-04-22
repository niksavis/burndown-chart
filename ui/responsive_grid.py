"""
Responsive Grid Module (Legacy)

This module provides advanced responsive grid components that utilize all Bootstrap breakpoints
(xs, sm, md, lg, xl, xxl) for fine-grained responsive layouts.

DEPRECATED: This module is maintained for backward compatibility.
New code should use ui.grid_utils instead.
"""

import warnings

#######################################################################
# IMPORTS
#######################################################################
from dash import html
import dash_bootstrap_components as dbc

# Import from styles
from ui.styles import (
    BREAKPOINTS,
    MEDIA_QUERIES,
    SPACING,
    get_breakpoint_value,
    create_responsive_container,
    create_responsive_style,
)

# Import new grid utilities
from ui.grid_utils import (
    create_responsive_row as new_create_responsive_row,
    create_responsive_column as new_create_responsive_column,
    create_responsive_grid as new_create_responsive_grid,
    create_stacked_to_horizontal as new_create_stacked_to_horizontal,
    create_card_grid,
    create_dashboard_layout,
    create_mobile_container as new_create_mobile_container,
    create_breakpoint_visibility_examples as new_create_breakpoint_visibility_examples,
)

#######################################################################
# RESPONSIVE GRID TEMPLATES (DEPRECATED)
#######################################################################


def create_responsive_row(
    children,
    className="",
    style=None,
    row_class_by_breakpoint=None,
    alignment_by_breakpoint=None,
    gutters_by_breakpoint=None,
):
    """
    Create a responsive row with different properties at different breakpoints.

    DEPRECATED: Use ui.grid_utils.create_responsive_row() instead.

    Args:
        children: Content for the row
        className: Base class name for the row
        style: Base style for the row
        row_class_by_breakpoint: Dict mapping breakpoints to classes (e.g. {'xs': 'flex-column', 'md': 'flex-row'})
        alignment_by_breakpoint: Dict mapping breakpoints to alignment classes
                                 (e.g. {'xs': 'justify-content-center', 'lg': 'justify-content-start'})
        gutters_by_breakpoint: Dict mapping breakpoints to gutter sizes
                               (e.g. {'xs': '1', 'md': '3', 'lg': '5'})

    Returns:
        A dbc.Row with responsive behavior
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_responsive_row() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_responsive_row(
        children=children,
        className=className,
        style=style,
        row_class_by_breakpoint=row_class_by_breakpoint,
        alignment_by_breakpoint=alignment_by_breakpoint,
        gutters_by_breakpoint=gutters_by_breakpoint,
    )


def create_responsive_column(
    content,
    xs=12,
    sm=None,
    md=None,
    lg=None,
    xl=None,
    xxl=None,
    className="",
    style=None,
    order_by_breakpoint=None,
    visibility_by_breakpoint=None,
    padding_by_breakpoint=None,
):
    """
    Create a responsive column with different widths and properties at different breakpoints.

    DEPRECATED: Use ui.grid_utils.create_responsive_column() instead.

    Args:
        content: Column content
        xs, sm, md, lg, xl, xxl: Column widths at different breakpoints (1-12)
        className: Additional CSS classes
        style: Additional inline styles
        order_by_breakpoint: Dict mapping breakpoints to order values (e.g. {'xs': '2', 'md': '1'})
        visibility_by_breakpoint: Dict mapping breakpoints to visibility boolean (e.g. {'xs': True, 'md': False})
        padding_by_breakpoint: Dict mapping breakpoints to padding values (e.g. {'xs': '1', 'md': '3'})

    Returns:
        A dbc.Col with responsive behavior
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_responsive_column() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_responsive_column(
        content=content,
        xs=xs,
        sm=sm,
        md=md,
        lg=lg,
        xl=xl,
        xxl=xxl,
        className=className,
        style=style,
        order_by_breakpoint=order_by_breakpoint,
        visibility_by_breakpoint=visibility_by_breakpoint,
        padding_by_breakpoint=padding_by_breakpoint,
    )


def create_responsive_grid(
    items,
    cols_by_breakpoint=None,
    breakpoints=["xs", "sm", "md", "lg", "xl", "xxl"],
    item_class="",
    row_class="",
    container_class="",
):
    """
    Create a responsive grid with a configurable number of columns at different breakpoints.

    DEPRECATED: Use ui.grid_utils.create_responsive_grid() instead.

    Args:
        items: List of content items to place in the grid
        cols_by_breakpoint: Dict mapping breakpoints to number of columns
                           (e.g. {'xs': 1, 'md': 2, 'lg': 3})
        breakpoints: List of breakpoints to include in the grid
        item_class: Additional classes for item containers
        row_class: Additional classes for the row
        container_class: Additional classes for the container

    Returns:
        A responsive grid with the items
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_responsive_grid() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_responsive_grid(
        items=items,
        cols_by_breakpoint=cols_by_breakpoint,
        breakpoints=breakpoints,
        item_class=item_class,
        row_class=row_class,
        container_class=container_class,
    )


def create_stacked_to_horizontal(
    left_content,
    right_content,
    stack_until="md",
    left_width=6,
    right_width=6,
    breakpoints=["xs", "sm", "md", "lg", "xl"],
    row_class="",
    equal_height=True,
):
    """
    Create a layout that stacks vertically until a specified breakpoint,
    then displays horizontally side-by-side.

    DEPRECATED: Use ui.grid_utils.create_stacked_to_horizontal() instead.

    Args:
        left_content: Content for the left column
        right_content: Content for the right column
        stack_until: Stack vertically until this breakpoint ('sm', 'md', 'lg', 'xl')
        left_width: Width of left column (1-12) for non-stacked view
        right_width: Width of right column (1-12) for non-stacked view
        breakpoints: List of breakpoints to consider
        row_class: Additional classes for the row
        equal_height: Whether to make columns equal height when side-by-side

    Returns:
        A layout that stacks vertically on small screens and horizontally on larger screens
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_stacked_to_horizontal() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_stacked_to_horizontal(
        left_content=left_content,
        right_content=right_content,
        stack_until=stack_until,
        left_width=left_width,
        right_width=right_width,
        equal_height=equal_height,
        className=row_class,
    )


def create_responsive_card_deck(
    cards,
    cols_by_breakpoint={"xs": 1, "sm": 1, "md": 2, "lg": 3, "xl": 4},
    card_class="",
    equal_height=True,
):
    """
    Create a responsive card deck that changes columns based on screen size.

    DEPRECATED: Use ui.grid_utils.create_card_grid() instead.

    Args:
        cards: List of card components to display
        cols_by_breakpoint: Dict mapping breakpoints to number of columns
        card_class: Additional classes for card containers
        equal_height: Whether to make all cards in a row the same height

    Returns:
        A responsive grid of cards
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_card_grid() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return create_card_grid(
        cards=cards, cols_by_breakpoint=cols_by_breakpoint, equal_height=equal_height
    )


def create_responsive_dashboard_layout(
    main_content,
    side_content,
    secondary_content=None,
    stack_until="lg",
    main_width=8,
    side_width=4,
    secondary_display_breakpoint="xl",
):
    """
    Create a responsive dashboard layout with main content and sidebars.

    DEPRECATED: Use ui.grid_utils.create_dashboard_layout() instead.

    Args:
        main_content: Primary content area
        side_content: Side panel content
        secondary_content: Optional secondary content that appears at larger breakpoints
        stack_until: Stack layout vertically until this breakpoint
        main_width: Width of main content area when not stacked (1-12)
        side_width: Width of side content area when not stacked (1-12)
        secondary_display_breakpoint: Only show secondary content at this breakpoint and larger

    Returns:
        A responsive dashboard layout
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_dashboard_layout() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return create_dashboard_layout(
        main_content=main_content,
        side_content=side_content,
        secondary_content=secondary_content,
        stack_until=stack_until,
        main_width=main_width,
        side_width=side_width,
        secondary_display_breakpoint=secondary_display_breakpoint,
    )


def create_responsive_tabs_layout(
    tabs_content,
    tabs_labels,
    stack_tabs_at="sm",
    tab_card_class="",
    tab_content_class="p-3",
):
    """
    Create a responsive tabs layout that switches between horizontal tabs and vertical
    accordion-style tabs based on screen size.

    Args:
        tabs_content: List of content for each tab
        tabs_labels: List of labels for each tab
        stack_tabs_at: Breakpoint at which to switch to vertical layout ('sm', 'md', 'lg')
        tab_card_class: Additional classes for the tab container
        tab_content_class: Classes for the tab content area

    Returns:
        A responsive tabs layout with appropriate callbacks
    """
    # Create horizontal tabs for larger screens
    horizontal_tabs = dbc.Tabs(
        [
            dbc.Tab(
                label=label,
                tab_id=f"tab-{i}",
                label_style={"cursor": "pointer"},
                active_label_style={
                    "fontWeight": "bold",
                    "borderBottom": "2px solid #0d6efd",
                },
            )
            for i, label in enumerate(tabs_labels)
        ],
        id="responsive-horizontal-tabs",
        active_tab="tab-0",
        className="d-none d-sm-flex nav-tabs-clean"
        if stack_tabs_at == "sm"
        else "d-none d-md-flex nav-tabs-clean"
        if stack_tabs_at == "md"
        else "d-none d-lg-flex nav-tabs-clean",
    )

    # Create vertical tabs/accordion for smaller screens
    vertical_tabs = html.Div(
        [
            dbc.Accordion(
                [
                    dbc.AccordionItem(content, title=label)
                    for content, label in zip(tabs_content, tabs_labels)
                ],
                id="responsive-vertical-tabs",
                start_collapsed=True,
            )
        ],
        className="d-block d-sm-none"
        if stack_tabs_at == "sm"
        else "d-block d-md-none"
        if stack_tabs_at == "md"
        else "d-block d-lg-none",
    )

    # Create content area for horizontal tabs
    content_area = html.Div(
        tabs_content[0],  # Default to first tab
        id="responsive-tabs-content",
        className=f"{tab_content_class} d-none d-sm-block"
        if stack_tabs_at == "sm"
        else f"{tab_content_class} d-none d-md-block"
        if stack_tabs_at == "md"
        else f"{tab_content_class} d-none d-lg-block",
    )

    # Create the complete layout
    return html.Div(
        [horizontal_tabs, content_area, vertical_tabs],
        className=f"responsive-tabs {tab_card_class}",
    )


def create_mobile_container(content, expanded_height="auto", className=""):
    """
    Create a container that collapses/expands on mobile devices.

    DEPRECATED: Use ui.grid_utils.create_mobile_container() instead.

    Args:
        content: Content to place in the container
        expanded_height: Height when expanded
        className: Additional CSS classes

    Returns:
        A collapsible container for mobile devices
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_mobile_container() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_mobile_container(
        content=content, expanded_height=expanded_height, className=className
    )


def create_breakpoint_visibility_examples():
    """
    Create examples demonstrating how content can be shown/hidden at different breakpoints.

    DEPRECATED: Use ui.grid_utils.create_breakpoint_visibility_examples() instead.

    Returns:
        A component with examples of responsive visibility
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_breakpoint_visibility_examples() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_breakpoint_visibility_examples()
