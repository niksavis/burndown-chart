"""
Grid Utilities Module

This module provides a unified grid system with both simple and advanced responsive
layout capabilities. It combines functionality from both grid_templates.py and responsive_grid.py
into a layered API that offers flexibility for different use cases.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
# (none currently needed)

# Third-party library imports
from dash import html
import dash_bootstrap_components as dbc

# Application imports
from ui.styles import (
    get_vertical_rhythm,
)

#######################################################################
# CONSTANTS
#######################################################################

BOOTSTRAP_BREAKPOINTS = ["xs", "sm", "md", "lg", "xl", "xxl"]

#######################################################################
# LOW-LEVEL FUNCTIONS (CORE GRID BUILDING BLOCKS)
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
    Create a responsive column with different widths and properties at different breakpoints.

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
    # Set up widths for each breakpoint
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


def create_container(content, fluid=True, className="", style=None):
    """
    Create a Bootstrap container.

    Args:
        content: Container content
        fluid: Whether to use a fluid container (full width) or fixed width
        className: Additional CSS classes
        style: Additional inline styles

    Returns:
        A dbc.Container with the content
    """
    return dbc.Container(
        content,
        fluid=fluid,
        className=className,
        style=style,
    )


def apply_grid_rhythm(component, rhythm_type="section", extra_classes=None):
    """
    Apply vertical rhythm spacing to a grid component.

    Args:
        component: The component to add rhythm spacing to
        rhythm_type: Type of rhythm spacing to apply (section, card, paragraph, etc.)
        extra_classes: Additional classes to add

    Returns:
        The component with rhythm spacing applied
    """
    # Get the appropriate spacing
    margin_bottom = get_vertical_rhythm(rhythm_type)

    # Set up the classes
    classes = extra_classes.split() if extra_classes else []

    # Create the style with appropriate margin
    style = {"marginBottom": margin_bottom}

    # If the component is a dict with a className attribute, update it
    if hasattr(component, "className") and component.className:
        classes.append(component.className)

    # Same for style
    if hasattr(component, "style") and component.style:
        style.update(component.style)

    # Set the new className and style
    component.className = " ".join(classes) if classes else None
    component.style = style

    return component


#######################################################################
# MID-LEVEL FUNCTIONS (COMMON GRID PATTERNS)
#######################################################################


def create_multi_column_layout(
    columns_content,
    column_widths=None,
    breakpoint="md",
    spacing="standard",
    className="",
):
    """
    Create a responsive multi-column layout with configurable breakpoints.

    Args:
        columns_content: List of content for each column
        column_widths: List of column widths (defaults to equal distribution)
        breakpoint: Breakpoint at which to switch from stacked to side-by-side
        spacing: Spacing between columns ("compact", "standard", "wide")
        className: Additional classes for the row

    Returns:
        A responsive row with the content in columns
    """
    if not columns_content:
        return html.Div()

    # If no column widths provided, distribute columns evenly
    num_columns = len(columns_content)
    if column_widths is None:
        col_width = 12 // num_columns
        column_widths = [col_width] * num_columns

    # Set up spacing between columns
    if spacing == "compact":
        gutter = {"xs": "1", breakpoint: "2"}
    elif spacing == "wide":
        gutter = {"xs": "2", breakpoint: "4"}
    else:  # standard
        gutter = {"xs": "2", breakpoint: "3"}

    # Set up margin class
    margin_bottom = get_vertical_rhythm("section")
    row_style = {"marginBottom": margin_bottom}

    # Create columns
    cols = []
    for i, content in enumerate(columns_content):
        # All columns are full width until the breakpoint
        widths = {"xs": 12}

        # Apply specified width at and above the breakpoint
        if breakpoint != "xs":
            widths[breakpoint] = column_widths[i] if i < len(column_widths) else 12

        # Add margin bottom on xs only (above breakpoint the columns will be side by side)
        col_class = f"mb-4 mb-{breakpoint}-0" if i < num_columns - 1 else ""

        cols.append(create_responsive_column(content, className=col_class, **widths))

    # Create the row with gutters
    return create_responsive_row(
        cols, className=className, gutters_by_breakpoint=gutter, style=row_style
    )


def create_two_column_layout(
    left_content,
    right_content,
    left_width=6,
    right_width=6,
    breakpoint="md",
    className="",
):
    """
    Create a standard two-column layout with responsive behavior.

    Args:
        left_content: Content for left column
        right_content: Content for right column
        left_width: Width of left column at or above breakpoint (1-12)
        right_width: Width of right column at or above breakpoint (1-12)
        breakpoint: Breakpoint at which to switch from stacked to side-by-side
        className: Additional CSS classes for the row

    Returns:
        A responsive two-column layout
    """
    return create_multi_column_layout(
        [left_content, right_content],
        [left_width, right_width],
        breakpoint=breakpoint,
        className=className,
    )


def create_three_column_layout(
    left,
    middle,
    right,
    left_width=4,
    middle_width=4,
    right_width=4,
    breakpoint="md",
    className="",
):
    """
    Create a standard three-column layout with responsive behavior.

    Args:
        left: Content for left column
        middle: Content for middle column
        right: Content for right column
        left_width: Width of left column at or above breakpoint (1-12)
        middle_width: Width of middle column at or above breakpoint (1-12)
        right_width: Width of right column at or above breakpoint (1-12)
        breakpoint: Breakpoint at which to switch from stacked to side-by-side
        className: Additional CSS classes for the row

    Returns:
        A responsive three-column layout
    """
    return create_multi_column_layout(
        [left, middle, right],
        [left_width, middle_width, right_width],
        breakpoint=breakpoint,
        className=className,
    )


def create_stacked_to_horizontal(
    left_content,
    right_content,
    stack_until="md",
    left_width=6,
    right_width=6,
    equal_height=True,
    className="",
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
        equal_height: Whether to make columns equal height when side-by-side
        className: Additional CSS classes for the row

    Returns:
        A layout that stacks vertically on small screens and horizontally on larger screens
    """
    # Find the index of the stack_until breakpoint
    bp_order = BOOTSTRAP_BREAKPOINTS
    try:
        stack_index = bp_order.index(stack_until)
    except ValueError:
        stack_index = 1  # Default to 'sm' if not found

    # Create width configurations for each column
    left_widths = {"xs": 12}  # Start with full width
    right_widths = {"xs": 12}  # Start with full width

    # Set specified widths for breakpoints after stack_until
    for bp in bp_order[stack_index + 1 :]:
        left_widths[bp] = left_width
        right_widths[bp] = right_width

    # Create columns
    left_margin_classes = ["mb-4"]
    for bp in bp_order[stack_index + 1 :]:
        left_margin_classes.append(f"mb-{bp}-0")

    left_column = create_responsive_column(
        left_content,
        className=" ".join(left_margin_classes) + (" h-100" if equal_height else ""),
        **left_widths,
    )

    right_column = create_responsive_column(
        right_content, className=("h-100" if equal_height else ""), **right_widths
    )

    # Create row with margins
    margin_bottom = get_vertical_rhythm("section")
    base_style = {"marginBottom": margin_bottom}

    return create_responsive_row(
        [left_column, right_column], className=className, style=base_style
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
    if not items:
        return html.Div()

    # Apply default column configuration if not provided
    if cols_by_breakpoint is None:
        cols_by_breakpoint = {
            "xs": 1,  # One column on extra small screens (mobile)
            "md": 2,  # Two columns on medium screens (tablet)
            "lg": 3,  # Three columns on large screens (desktop)
        }

    # Calculate column widths for each breakpoint
    column_widths = {}
    for breakpoint, num_cols in cols_by_breakpoint.items():
        if num_cols > 0:
            column_widths[breakpoint] = (
                12 // num_cols
            )  # Convert to Bootstrap's 12-column system

    # Create columns for the grid
    columns = []
    for item in items:
        # Apply width config to each column
        width_config = {}
        for breakpoint in breakpoints:
            if breakpoint in column_widths:
                width_config[breakpoint] = column_widths[breakpoint]

        # Create a column with responsive behavior
        columns.append(
            create_responsive_column(
                html.Div(item, className=f"grid-item {item_class}"),
                className="mb-4",  # Add margin between rows
                **width_config,
            )
        )

    # Create the row with all columns
    grid = create_responsive_row(columns, className=row_class)

    return html.Div(grid, className=f"responsive-grid-container {container_class}")


#######################################################################
# HIGH-LEVEL PATTERN FUNCTIONS (SPECIFIC LAYOUT PATTERNS)
#######################################################################


def create_content_sidebar_layout(
    content,
    sidebar,
    sidebar_position="right",
    sidebar_width=4,
    content_width=8,
    stack_until="md",
    spacing="standard",
):
    """
    Create a layout with main content and sidebar.

    Args:
        content: Main content area
        sidebar: Sidebar content
        sidebar_position: Position of sidebar ("left" or "right")
        sidebar_width: Width of sidebar at or above breakpoint (1-12)
        content_width: Width of content area at or above breakpoint (1-12)
        stack_until: Stack vertically until this breakpoint
        spacing: Spacing between columns ("compact", "standard", "wide")

    Returns:
        A responsive content + sidebar layout
    """
    if sidebar_position == "left":
        left_content = sidebar
        right_content = content
        left_width = sidebar_width
        right_width = content_width
    else:
        left_content = content
        right_content = sidebar
        left_width = content_width
        right_width = sidebar_width

    # Create the layout
    return create_stacked_to_horizontal(
        left_content=left_content,
        right_content=right_content,
        stack_until=stack_until,
        left_width=left_width,
        right_width=right_width,
        equal_height=True,
    )


def create_dashboard_layout(
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
    main_column_props = {"xs": 12}  # Full width on mobile

    # Set specified widths for breakpoints after stack_until
    bp_order = BOOTSTRAP_BREAKPOINTS
    stack_index = bp_order.index("lg")  # Default to 'lg' breakpoint
    try:
        stack_index = bp_order.index(stack_until)
        for bp in bp_order[stack_index + 1 :]:
            main_column_props[bp] = main_width
    except ValueError:
        main_column_props["lg"] = main_width  # Default behavior

    # Create side column with responsive behavior
    side_column_props = {"xs": 12}  # Full width on mobile

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


#######################################################################
# SPECIALIZED GRID FUNCTIONS (BY PURPOSE)
#######################################################################


def create_card_grid(
    cards, cols_by_breakpoint={"xs": 1, "md": 2, "lg": 3}, equal_height=True
):
    """
    Create a responsive grid of cards.

    Args:
        cards: List of card components to display
        cols_by_breakpoint: Dict mapping breakpoints to number of columns
        equal_height: Whether to make all cards the same height within a row

    Returns:
        A responsive grid layout of cards
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
        # Add classes for card container
        card_container_class = "mb-4" + (" h-100" if equal_height else "")

        columns.append(
            create_responsive_column(
                html.Div(card, className=card_container_class), **col_widths
            )
        )

    # Create row with cards
    return dbc.Row(columns, className="card-deck")


def create_form_row(form_groups, columns=None):
    """
    Create a responsive form row with form groups.

    Args:
        form_groups: List of form group components
        columns: List of column widths for each form group

    Returns:
        A row with form groups in columns
    """
    if columns is None:
        # Distribute columns evenly
        col_width = 12 // len(form_groups)
        columns = [col_width] * len(form_groups)

    cols = []
    for i, form_group in enumerate(form_groups):
        cols.append(dbc.Col(form_group, width=12, md=columns[i]))

    # Use our vertical rhythm system for form spacing
    margin_bottom = get_vertical_rhythm("form_element")

    return dbc.Row(cols, style={"marginBottom": margin_bottom})


def create_responsive_table_wrapper(table_component, max_height=None, className=""):
    """
    Create a mobile-responsive wrapper for tables that handles overflow with scrolling.

    Args:
        table_component: The table component to wrap
        max_height: Optional max height for vertical scrolling
        className: Additional CSS classes

    Returns:
        html.Div: A responsive container for the table
    """
    container_style = {
        "overflowX": "auto",
        "width": "100%",
        "WebkitOverflowScrolling": "touch",  # Smooth scrolling on iOS
    }

    if max_height:
        container_style["maxHeight"] = max_height
        container_style["overflowY"] = "auto"

    return html.Div(
        table_component,
        className=f"table-responsive {className}",
        style=container_style,
    )


def create_form_section(title, components, help_text=None):
    """
    Create a form section with a title and components.

    Args:
        title: Section title
        components: List of components to include in the section
        help_text: Optional help text to display below the title

    Returns:
        A section div with title and components
    """
    section_components = []

    section_components.append(
        html.H5(
            title,
            className="border-bottom pb-2",
            style={"marginBottom": get_vertical_rhythm("heading.h5")},
        )
    )

    if help_text:
        section_components.append(
            html.P(
                help_text,
                className="text-muted",
                style={"marginBottom": get_vertical_rhythm("paragraph")},
            )
        )

    section_components.extend(components)

    # Use section margin from our vertical rhythm system
    margin_bottom = get_vertical_rhythm("section")

    return html.Div(section_components, style={"marginBottom": margin_bottom})


def create_breakpoint_visibility_examples():
    """
    Create examples demonstrating how content can be shown/hidden at different breakpoints.
    Useful for testing responsive behavior.

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


def create_mobile_container(content, expanded_height="auto", className=""):
    """
    Create a container that collapses/expands on mobile devices.

    Args:
        content: Content to place in the container
        expanded_height: Height when expanded
        className: Additional CSS classes

    Returns:
        A collapsible container for mobile devices
    """
    container = html.Div(
        content,
        className=f"mobile-collapsible-container d-md-block {className}",
    )

    return container


def create_tab_content(content, padding=None):
    """
    Create standardized tab content with consistent padding.

    Args:
        content: The content to display in the tab
        padding: Padding class to apply

    Returns:
        A div with the tab content and consistent styling
    """
    # Use consistent padding from our spacing system
    if padding is None:
        padding = "p-3"  # Default padding

    return html.Div(content, className=f"{padding} border border-top-0 rounded-bottom")


def create_full_width_layout(content, row_class=None):
    """
    Creates a standardized full-width layout.

    Args:
        content: Content for the full-width column
        row_class: Additional classes to apply to the row

    Returns:
        A dbc.Row containing the full-width layout
    """
    # Use vertical rhythm system for consistent spacing
    margin_bottom = get_vertical_rhythm("section")
    row_style = {"marginBottom": margin_bottom}

    # Apply custom class if provided
    combined_class = row_class if row_class else ""

    return dbc.Row(
        [
            dbc.Col(content, width=12),
        ],
        className=combined_class,
        style=row_style,
    )


def create_two_cards_layout(
    card1, card2, card1_width=6, card2_width=6, equal_height=True
):
    """
    Creates a standardized layout for two cards side by side with responsive behavior.

    Args:
        card1: First card component
        card2: Second card component
        card1_width: Width of first card (1-12) for medium screens and up
        card2_width: Width of second card (1-12) for medium screens and up
        equal_height: Whether to make the cards the same height

    Returns:
        A dbc.Row containing the two cards layout
    """
    card1_class = "h-100" if equal_height else ""
    card2_class = "h-100" if equal_height else ""

    card1 = html.Div(card1, className=card1_class)
    card2 = html.Div(card2, className=card2_class)

    return create_two_column_layout(
        left_content=card1,
        right_content=card2,
        left_width=card1_width,
        right_width=card2_width,
    )
