"""
Responsive Grid Module

This module provides advanced responsive grid components that utilize all Bootstrap breakpoints
(xs, sm, md, lg, xl, xxl) for fine-grained responsive layouts.
"""

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

#######################################################################
# RESPONSIVE GRID TEMPLATES
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
    # Build class name with breakpoint-specific classes
    classes = [className] if className else []

    # Add responsive classes
    if row_class_by_breakpoint:
        for bp, cls in row_class_by_breakpoint.items():
            if bp == "xs":
                classes.append(cls)
            else:
                classes.append(f"{cls}-{bp}")

    # Add alignment classes
    if alignment_by_breakpoint:
        for bp, align in alignment_by_breakpoint.items():
            if bp == "xs":
                classes.append(align)
            else:
                classes.append(f"{align}-{bp}")

    # Add gutter classes
    if gutters_by_breakpoint:
        for bp, gutter in gutters_by_breakpoint.items():
            if bp == "xs":
                classes.append(f"g-{gutter}")
            else:
                classes.append(f"g-{bp}-{gutter}")

    # Join all classes
    row_class = " ".join(classes)

    return dbc.Row(children, className=row_class, style=style)


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
    Create a column with different widths at different breakpoints.

    Args:
        content: Content for the column
        xs, sm, md, lg, xl, xxl: Column width (1-12) at each breakpoint
        className: Additional CSS classes
        style: Additional styles
        order_by_breakpoint: Dict mapping breakpoints to order values (e.g. {'xs': '2', 'lg': '1'})
        visibility_by_breakpoint: Dict mapping breakpoints to visibility (e.g. {'xs': True, 'md': False})
        padding_by_breakpoint: Dict mapping breakpoints to padding (e.g. {'xs': '2', 'md': '4'})

    Returns:
        A dbc.Col with responsive behavior
    """
    # Create the width configuration for each breakpoint
    width_config = {}
    if xs is not None:
        width_config["xs"] = xs
    if sm is not None:
        width_config["sm"] = sm
    if md is not None:
        width_config["md"] = md
    if lg is not None:
        width_config["lg"] = lg
    if xl is not None:
        width_config["xl"] = xl
    if xxl is not None:
        width_config["xxl"] = xxl

    # Build class name with additional responsive classes
    classes = [className] if className else []

    # Add order classes for reordering content at different breakpoints
    if order_by_breakpoint:
        for bp, order in order_by_breakpoint.items():
            if bp == "xs":
                classes.append(f"order-{order}")
            else:
                classes.append(f"order-{bp}-{order}")

    # Add visibility classes
    if visibility_by_breakpoint:
        for bp, visible in visibility_by_breakpoint.items():
            if bp == "xs":
                classes.append(f"d-{'block' if visible else 'none'}")
            else:
                classes.append(f"d-{bp}-{'block' if visible else 'none'}")

    # Add padding classes
    if padding_by_breakpoint:
        for bp, padding in padding_by_breakpoint.items():
            if bp == "xs":
                classes.append(f"p-{padding}")
            else:
                classes.append(f"p-{bp}-{padding}")

    col_class = " ".join(classes)

    return dbc.Col(content, **width_config, className=col_class, style=style)


def create_responsive_grid(
    items,
    cols_by_breakpoint=None,
    breakpoints=["xs", "sm", "md", "lg", "xl", "xxl"],
    item_class="",
    row_class="",
    container_class="",
):
    """
    Create a responsive grid layout with a configurable number of columns at different breakpoints.

    Args:
        items: List of content items to place in the grid
        cols_by_breakpoint: Dict mapping breakpoints to number of columns
                           (e.g. {'xs': 1, 'sm': 2, 'md': 3, 'lg': 4, 'xl': 6})
        breakpoints: List of breakpoints to include in the grid (default: all Bootstrap breakpoints)
        item_class: Class to apply to each item
        row_class: Class to apply to each row
        container_class: Class to apply to the container

    Returns:
        A responsively laid out grid of items with different column counts at different breakpoints
    """
    if not items:
        return html.Div()

    if cols_by_breakpoint is None:
        cols_by_breakpoint = {"xs": 1, "md": 2, "lg": 3, "xl": 4}

    # Calculate column width for each breakpoint
    col_widths = {}
    for bp in breakpoints:
        if bp in cols_by_breakpoint:
            col_widths[bp] = 12 // cols_by_breakpoint[bp]

    # Create columns with responsive widths
    columns = []
    for item in items:
        columns.append(
            create_responsive_column(
                html.Div(item, className=item_class),
                **{bp: width for bp, width in col_widths.items()},
                className="mb-3",
            )
        )

    # Create row with items
    row = dbc.Row(columns, className=row_class)

    return html.Div(row, className=container_class)


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

    Args:
        left_content: Content for the left column
        right_content: Content for the right column
        stack_until: Stack vertically until this breakpoint ('sm', 'md', 'lg', 'xl')
        left_width: Width of left column (1-12) for non-stacked view
        right_width: Width of right column (1-12) for non-stacked view
        breakpoints: List of breakpoints to include
        row_class: Additional classes for the row
        equal_height: Whether to make columns equal height when side-by-side

    Returns:
        A layout that stacks vertically on small screens and horizontally on larger screens
    """
    # Find the index of the stack_until breakpoint
    bp_order = ["xs", "sm", "md", "lg", "xl", "xxl"]
    try:
        stack_index = bp_order.index(stack_until)
    except ValueError:
        stack_index = 1  # Default to 'sm' if not found

    # Create width configurations for each column
    left_widths = {}
    right_widths = {}

    # Set full width for breakpoints before stack_until
    for bp in bp_order[: stack_index + 1]:
        if bp in breakpoints:
            left_widths[bp] = 12
            right_widths[bp] = 12

    # Set specified widths for breakpoints after stack_until
    for bp in bp_order[stack_index + 1 :]:
        if bp in breakpoints:
            left_widths[bp] = left_width
            right_widths[bp] = right_width

    # Create columns
    left_margin_classes = ["mb-3"]
    for bp in bp_order[stack_index + 1 :]:
        if bp in breakpoints:
            left_margin_classes.append(f"mb-{bp}-0")

    left_column = create_responsive_column(
        left_content,
        **left_widths,
        className=" ".join(left_margin_classes) + (" h-100" if equal_height else ""),
    )

    right_column = create_responsive_column(
        right_content, **right_widths, className=("h-100" if equal_height else "")
    )

    # Create row
    base_classes = ["mb-4"]
    if row_class:
        base_classes.append(row_class)

    return dbc.Row([left_column, right_column], className=" ".join(base_classes))


def create_responsive_card_deck(
    cards,
    cols_by_breakpoint={"xs": 1, "sm": 1, "md": 2, "lg": 3, "xl": 4},
    card_class="",
    equal_height=True,
):
    """
    Create a responsive card deck layout with different numbers of columns at different breakpoints.

    Args:
        cards: List of card components to display
        cols_by_breakpoint: Dict mapping breakpoints to number of columns
        card_class: Additional class to apply to each card container
        equal_height: Whether to make all cards the same height within a row

    Returns:
        A responsive card deck layout
    """
    if not cards:
        return html.Div()

    # Calculate column width for each breakpoint
    col_widths = {}
    for bp, cols in cols_by_breakpoint.items():
        col_widths[bp] = 12 // cols

    # Create columns with cards
    columns = []
    for card in cards:
        card_container_class = f"{card_class} mb-4" + (" h-100" if equal_height else "")

        columns.append(
            create_responsive_column(
                html.Div(card, className=card_container_class), **col_widths
            )
        )

    # Create row with cards
    return dbc.Row(columns, className="card-deck")


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
    # Create main column with responsive behavior
    main_column_props = {
        "xs": 12,  # Full width on mobile
    }

    # Set specified widths for breakpoints after stack_until
    bp_order = ["xs", "sm", "md", "lg", "xl", "xxl"]
    try:
        stack_index = bp_order.index(stack_until)
        for bp in bp_order[stack_index + 1 :]:
            main_column_props[bp] = main_width
    except ValueError:
        main_column_props["lg"] = main_width  # Default behavior

    # Create side column with responsive behavior
    side_column_props = {
        "xs": 12,  # Full width on mobile
    }

    # Set specified widths for breakpoints after stack_until
    try:
        for bp in bp_order[stack_index + 1 :]:
            side_column_props[bp] = side_width
    except ValueError:
        side_column_props["lg"] = side_width  # Default behavior

    # Create visibility settings for secondary content
    secondary_visibility = {}
    secondary_column = None

    if secondary_content:
        try:
            sec_index = bp_order.index(secondary_display_breakpoint)
            for i, bp in enumerate(bp_order):
                secondary_visibility[bp] = i >= sec_index
        except ValueError:
            # Default to show on xl and above if breakpoint not found
            secondary_visibility = {
                "xs": False,
                "sm": False,
                "md": False,
                "lg": False,
                "xl": True,
                "xxl": True,
            }

        # Create secondary column
        secondary_column = create_responsive_column(
            secondary_content,
            xs=12,
            className="mb-4",
            visibility_by_breakpoint=secondary_visibility,
        )

    # Create main and side columns
    main_column = create_responsive_column(
        main_content, **main_column_props, className="mb-4"
    )

    side_column = create_responsive_column(
        side_content, **side_column_props, className="mb-4"
    )

    # Create the row with all columns
    columns = [main_column, side_column]
    if secondary_column:
        columns.append(secondary_column)

    return dbc.Row(columns)


def create_responsive_tabs_layout(
    tabs_content,
    tabs_labels,
    stack_tabs_at="sm",
    tab_card_class="",
    tab_content_class="p-3",
):
    """
    Create a responsive tabs layout that switches between horizontal and vertical tabs.

    Args:
        tabs_content: List of tab content components
        tabs_labels: List of tab labels
        stack_tabs_at: Stack tabs vertically at this breakpoint and below
        tab_card_class: Class for the outer card container
        tab_content_class: Class for the tab content container

    Returns:
        A responsive tabs layout
    """
    from dash import dcc

    # Create horizontal tabs for larger screens
    horizontal_tabs = dcc.Tabs(
        id="responsive-horizontal-tabs",
        value=0,
        children=[dcc.Tab(label=label, value=i) for i, label in enumerate(tabs_labels)],
        className="d-none d-sm-block"
        if stack_tabs_at == "sm"
        else "d-none d-md-block"
        if stack_tabs_at == "md"
        else "d-none d-lg-block",
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
    Create a container that can expand/collapse for better mobile viewing.

    Args:
        content: The content to place in the container
        expanded_height: Height when expanded
        className: Additional CSS classes

    Returns:
        A collapsible container optimized for mobile
    """
    collapse_id = f"collapse-{id(content)}"

    container = html.Div(
        [
            # Header that's always visible
            html.Div(
                [
                    html.Button(
                        html.I(className="fas fa-chevron-down"),
                        id=f"{collapse_id}-toggle",
                        className="btn btn-link p-0",
                        n_clicks=0,
                    )
                ],
                className="d-flex justify-content-between align-items-center mb-2",
            ),
            # Collapsible content
            dbc.Collapse(
                html.Div(
                    content, style={"maxHeight": expanded_height, "overflow": "auto"}
                ),
                id=collapse_id,
                is_open=False,
            ),
        ],
        className=f"mobile-collapsible-container d-md-block {className}",
    )

    return container


def create_breakpoint_visibility_examples():
    """
    Create examples demonstrating how content can be shown/hidden at different breakpoints.

    Returns:
        A component with examples of responsive visibility
    """
    examples = [
        html.Div(
            "Visible on extra small screens only (xs)",
            className="bg-primary text-white p-2 d-block d-sm-none",
        ),
        html.Div(
            "Visible on small screens and up (sm+)",
            className="bg-secondary text-white p-2 d-none d-sm-block",
        ),
        html.Div(
            "Visible on medium screens and up (md+)",
            className="bg-success text-white p-2 d-none d-md-block",
        ),
        html.Div(
            "Visible on large screens and up (lg+)",
            className="bg-info text-white p-2 d-none d-lg-block",
        ),
        html.Div(
            "Visible on extra large screens and up (xl+)",
            className="bg-warning p-2 d-none d-xl-block",
        ),
        html.Div(
            "Visible on extra extra large screens only (xxl)",
            className="bg-danger text-white p-2 d-none d-xxl-block",
        ),
        html.Div(
            "Visible on mobile only (xs and sm)",
            className="bg-dark text-white p-2 d-block d-md-none",
        ),
        html.Div(
            "Visible on tablet only (md)",
            className="bg-light p-2 d-none d-md-block d-lg-none",
        ),
    ]

    return html.Div(examples, className="mb-4")
