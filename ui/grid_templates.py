"""
Grid Templates Module (Legacy)

This module provides standardized grid layout components and templates
for consistent layout and alignment throughout the application.

DEPRECATED: This module is maintained for backward compatibility.
New code should use ui.grid_utils instead.
"""

import warnings

#######################################################################
# IMPORTS
#######################################################################
from dash import html, dash_table
import dash_bootstrap_components as dbc

# Import styling functions from ui.styles
from ui.styles import (
    SPACING,
    NEUTRAL_COLORS,
    COMPONENT_SPACING,
    get_vertical_rhythm,
)

# Import new grid utilities
from ui.grid_utils import (
    create_two_column_layout as new_create_two_column_layout,
    create_three_column_layout as new_create_three_column_layout,
    create_multi_column_layout,
    create_responsive_table_wrapper as new_create_responsive_table_wrapper,
    create_form_row as new_create_form_row,
    create_form_section as new_create_form_section,
)

#######################################################################
# GRID TEMPLATES (DEPRECATED)
#######################################################################


def create_two_column_layout(
    left_content, right_content, left_width=6, right_width=6, row_class=None
):
    """
    Creates a standardized two-column layout with responsive behavior.

    DEPRECATED: Use ui.grid_utils.create_two_column_layout() instead.

    Args:
        left_content: Content for the left column
        right_content: Content for the right column
        left_width: Width of left column (1-12) for medium screens and up
        right_width: Width of right column (1-12) for medium screens and up
        row_class: Additional classes to apply to the row

    Returns:
        A dbc.Row containing the two-column layout
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_two_column_layout() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_two_column_layout(
        left_content=left_content,
        right_content=right_content,
        left_width=left_width,
        right_width=right_width,
        className=row_class,
    )


def create_two_cards_layout(
    card1, card2, card1_width=6, card2_width=6, equal_height=True
):
    """
    Creates a standardized layout for two cards side by side with responsive behavior.

    DEPRECATED: Use ui.grid_utils.create_two_column_layout() with card content instead.

    Args:
        card1: First card component
        card2: Second card component
        card1_width: Width of first card (1-12) for medium screens and up
        card2_width: Width of second card (1-12) for medium screens and up
        equal_height: Whether to make the cards the same height

    Returns:
        A dbc.Row containing the two cards layout
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_two_column_layout() with card content instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    if equal_height:
        card1_class = "h-100"
        card2_class = "h-100"
    else:
        card1_class = ""
        card2_class = ""

    card1 = html.Div(card1, className=card1_class)
    card2 = html.Div(card2, className=card2_class)

    return new_create_two_column_layout(
        left_content=card1,
        right_content=card2,
        left_width=card1_width,
        right_width=card2_width,
    )


def create_three_column_layout(
    left, middle, right, left_width=4, middle_width=4, right_width=4, row_class=None
):
    """
    Creates a standardized three-column layout with responsive behavior.

    DEPRECATED: Use ui.grid_utils.create_three_column_layout() instead.

    Args:
        left: Content for the left column
        middle: Content for the middle column
        right: Content for the right column
        left_width: Width of left column (1-12) for medium screens and up
        middle_width: Width of middle column (1-12) for medium screens and up
        right_width: Width of right column (1-12) for medium screens and up
        row_class: Additional classes to apply to the row

    Returns:
        A dbc.Row containing the three-column layout
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_three_column_layout() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_three_column_layout(
        left=left,
        middle=middle,
        right=right,
        left_width=left_width,
        middle_width=middle_width,
        right_width=right_width,
        className=row_class,
    )


def create_four_column_layout(cols, widths=None, row_class=None):
    """
    Creates a standardized four-column layout with responsive behavior.

    DEPRECATED: Use ui.grid_utils.create_multi_column_layout() instead.

    Args:
        cols: List of content for the columns
        widths: List of widths for each column (1-12) for medium screens and up
        row_class: Additional classes to apply to the row

    Returns:
        A dbc.Row containing the four-column layout
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_multi_column_layout() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return create_multi_column_layout(
        columns_content=cols, column_widths=widths, className=row_class
    )


def create_full_width_layout(content, row_class=None):
    """
    Creates a standardized full-width layout.

    DEPRECATED: Use dbc.Row(dbc.Col(content, width=12), className=row_class) directly.

    Args:
        content: Content for the full-width column
        row_class: Additional classes to apply to the row

    Returns:
        A dbc.Row containing the full-width layout
    """
    warnings.warn(
        "This function is deprecated. Use dbc.Row(dbc.Col(content, width=12), className=row_class) directly.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Use vertical rhythm system for consistent spacing
    if row_class is None:
        row_class = f"mb-{COMPONENT_SPACING['section_margin'].replace('rem', '')}"

    return dbc.Row(
        [
            dbc.Col(content, width=12),
        ],
        className=row_class,
    )


#######################################################################
# TABLE TEMPLATES
#######################################################################


def create_standardized_table_style(stripe_color=None, mobile_optimized=True):
    """
    Create standardized styling for data tables.

    Args:
        stripe_color: Color for alternating rows (defaults to light gray)
        mobile_optimized: Whether to apply mobile-specific optimizations

    Returns:
        Dictionary with styling properties
    """
    if stripe_color is None:
        stripe_color = NEUTRAL_COLORS.get("gray-100", "#f8f9fa")

    # Use our vertical rhythm system for consistent table spacing
    cell_padding_v = COMPONENT_SPACING.get("table_cell_padding", SPACING["xs"])
    cell_padding_h = COMPONENT_SPACING.get("table_cell_padding", SPACING["sm"])

    style_dict = {
        "style_table": {
            "overflowX": "auto",
            "borderRadius": "4px",
            "border": f"1px solid {NEUTRAL_COLORS.get('gray-300', '#dee2e6')}",
            "marginBottom": get_vertical_rhythm("section"),
            "-webkit-overflow-scrolling": "touch",  # Improved scroll on iOS
        },
        "style_header": {
            "backgroundColor": NEUTRAL_COLORS.get("gray-200", "#e9ecef"),
            "fontWeight": "bold",
            "textAlign": "center",
            "padding": f"{cell_padding_v} {cell_padding_h}",
            "borderBottom": f"2px solid {NEUTRAL_COLORS.get('gray-400', '#ced4da')}",
        },
        "style_cell": {
            "padding": f"{cell_padding_v} {cell_padding_h}",
            "fontFamily": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "lineHeight": "1.5",
            "minWidth": "100px",
            "maxWidth": "500px",
        },
        "style_data": {
            "border": f"1px solid {NEUTRAL_COLORS.get('gray-200', '#e9ecef')}",
        },
        "style_data_conditional": [
            {
                "if": {"row_index": "odd"},
                "backgroundColor": stripe_color,
            }
        ],
    }

    # Add mobile optimizations if requested
    if mobile_optimized:
        # Add mobile-specific styling for better touch interactions
        style_dict["css"] = [
            # Optimize for touch scrolling
            {
                "selector": ".dash-spreadsheet-container",
                "rule": "touch-action: pan-y; -webkit-overflow-scrolling: touch;",
            }
        ]

        # We'll handle mobile optimizations through separate CSS classes instead
        # of using media queries directly in Dash DataTable CSS

    return style_dict


def create_data_table(
    data,
    columns,
    id,
    editable=False,
    row_selectable=False,
    page_size=None,
    include_pagination=False,
    sort_action=None,
    filter_action=None,
    column_alignments=None,
    sort_by=None,
    mobile_responsive=True,  # New parameter for mobile optimizations
    priority_columns=None,  # New parameter to specify important columns on mobile
):
    """
    Create a standardized data table with consistent styling and behavior.

    Args:
        data: The data to display in the table
        columns: Column definitions
        id: Component ID
        editable: Whether cells are editable
        row_selectable: Whether rows are selectable
        page_size: Number of rows per page
        include_pagination: Whether to include pagination
        sort_action: Sort action ("native" or None)
        filter_action: Filter action ("native" or None)
        column_alignments: Dictionary mapping column IDs to text alignments
        sort_by: Default sorting configuration, e.g. [{'column_id': 'date', 'direction': 'desc'}]
        mobile_responsive: Whether to apply mobile-specific optimizations
        priority_columns: List of column IDs that should be prioritized on small screens

    Returns:
        A dash_table.DataTable with standardized styling
    """
    # Get base styling
    table_style = create_standardized_table_style(mobile_optimized=mobile_responsive)

    # Apply column-specific alignments if provided
    style_cell_conditional = []
    if column_alignments:
        style_cell_conditional = [
            {"if": {"column_id": col_id}, "textAlign": alignment}
            for col_id, alignment in column_alignments.items()
        ]

    # Add mobile optimization for columns if needed
    if mobile_responsive and priority_columns:
        # Create conditional styling for non-priority columns on mobile
        for col in columns:
            if col["id"] not in priority_columns:
                style_cell_conditional.append(
                    {
                        "if": {"column_id": col["id"]},
                        "className": "mobile-hidden",
                        "media": "screen and (max-width: 767px)",
                    }
                )

    # Add highlighting for editable cells
    if editable:
        style_data_conditional = table_style["style_data_conditional"] + [
            {
                "if": {"column_editable": True},
                "backgroundColor": "rgba(0, 123, 255, 0.05)",
                "cursor": "pointer",
            },
            # Add more visual feedback for selected cell
            {
                "if": {"state": "selected"},
                "backgroundColor": "rgba(13, 110, 253, 0.15)",
                "border": "1px solid #0d6efd",
            },
            # Show validation indicators for numeric columns - using correct syntax
            # Apply to individual numeric columns instead of using a generic filter
            *[
                {
                    "if": {
                        "column_id": col["id"],
                        "filter_query": f"{{{col['id']}}} < 0",
                    },
                    "backgroundColor": "rgba(220, 53, 69, 0.1)",
                    "color": "#dc3545",
                }
                for col in columns
                if col.get("type") == "numeric"
            ],
        ]
    else:
        style_data_conditional = table_style["style_data_conditional"]

    # Set up pagination properties
    if include_pagination:
        pagination_settings = {
            "page_action": "native",
            "page_current": 0,
            "page_size": page_size if page_size else 10,
            "page_count": None,
        }
    else:
        pagination_settings = {}

    # Additional CSS for mobile optimization
    css_rules = [
        # Add modern styling
        {
            "selector": ".dash-spreadsheet-menu",
            "rule": "position: absolute; top: 0.5rem; right: 0.5rem;",
        },
        # Improve filter icon appearance
        {
            "selector": ".dash-filter",
            "rule": "padding: 2px 5px; border-radius: 3px; background-color: rgba(0, 0, 0, 0.05);",
        },
        # Hide case-sensitive toggle (simplify filtering UI)
        {"selector": ".dash-filter--case", "rule": "display: none;"},
        # Add indicator to show field is editable on hover
        {
            "selector": "td.cell--editable:hover",
            "rule": "background-color: rgba(13, 110, 253, 0.08) !important;",
        },
        # Improve column sorting indication
        {
            "selector": ".dash-header-cell .column-header--sort",
            "rule": "opacity: 1 !important; color: #0d6efd !important;",
        },
        # Add better focus indication for keyboard navigation
        {
            "selector": ".dash-cell-value:focus",
            "rule": "outline: none !important; box-shadow: inset 0 0 0 2px #0d6efd !important;",
        },
    ]

    if mobile_responsive:
        css_rules.extend(
            [
                # Ensure text wraps on small screens
                {
                    "selector": ".dash-cell-value",
                    "rule": "white-space: normal !important; word-break: break-word !important;",
                },
            ]
        )

    # Create the table
    return dash_table.DataTable(
        id=id,
        data=data,
        columns=columns,
        editable=editable,
        row_selectable="multi" if row_selectable else None,
        row_deletable=editable,
        sort_action=sort_action,
        filter_action=filter_action,
        sort_by=sort_by,  # Set default sorting
        style_table=table_style["style_table"],
        style_header=table_style["style_header"],
        style_cell=table_style["style_cell"],
        style_cell_conditional=style_cell_conditional,
        style_data=table_style["style_data"],
        style_data_conditional=style_data_conditional,
        css=css_rules,
        tooltip_delay=0,
        tooltip_duration=None,
        **pagination_settings,
    )


def create_responsive_table_wrapper(table_component, max_height=None, className=""):
    """
    Create a mobile-responsive wrapper for tables that handles overflow with scrolling.

    DEPRECATED: Use ui.grid_utils.create_responsive_table_wrapper() instead.

    Args:
        table_component: The table component to wrap
        max_height: Optional max height for vertical scrolling
        className: Additional CSS classes

    Returns:
        html.Div: A responsive container for the table
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_responsive_table_wrapper() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_responsive_table_wrapper(
        table_component=table_component, max_height=max_height, className=className
    )


#######################################################################
# TABLE ALIGNMENT UTILITIES
#######################################################################


def detect_column_alignment(dataframe, column_name):
    """
    Automatically detect appropriate alignment for a column based on its data type.

    Args:
        dataframe: Pandas DataFrame containing the data
        column_name: Name of the column to analyze

    Returns:
        str: Appropriate alignment ('left', 'right', or 'center')
    """
    import pandas as pd
    import numpy as np

    if column_name not in dataframe.columns:
        return "left"  # Default to left alignment

    # Get data type of the column
    dtype = dataframe[column_name].dtype

    # Check for date-related columns by name
    date_related_names = ["date", "time", "day", "month", "year", "deadline"]
    if any(date_term in column_name.lower() for date_term in date_related_names):
        return "center"

    # Check for numeric types
    if (
        pd.api.types.is_numeric_dtype(dtype)
        or dtype == np.dtype("float64")
        or dtype == np.dtype("int64")
    ):
        return "right"

    # Check for boolean types
    if pd.api.types.is_bool_dtype(dtype):
        return "center"

    # Default to left alignment for text and other types
    return "left"


def generate_column_alignments(dataframe):
    """
    Generate a dictionary of optimal column alignments for all columns in a DataFrame.

    Args:
        dataframe: Pandas DataFrame to analyze

    Returns:
        dict: Dictionary mapping column names to their optimal alignments
    """
    alignments = {}

    for column in dataframe.columns:
        alignments[column] = detect_column_alignment(dataframe, column)

    return alignments


def create_aligned_datatable(
    dataframe,
    id,
    editable=False,
    page_size=10,
    include_pagination=True,
    filter_action="native",
    sort_action="native",
    override_alignments=None,
    sort_by=None,
):
    """
    Create a DataTable with optimal column alignments based on data types.

    Args:
        dataframe: Pandas DataFrame with the data to display
        id: Component ID for the DataTable
        editable: Whether cells can be edited
        page_size: Number of rows per page
        include_pagination: Whether to include pagination
        filter_action: Filter action ("native" or None)
        sort_action: Sort action ("native" or None)
        override_alignments: Optional dict to override automatic alignments
        sort_by: Default sorting configuration, e.g. [{'column_id': 'date', 'direction': 'desc'}]

    Returns:
        dash_table.DataTable: A properly aligned data table
    """
    # Generate columns with appropriate types
    columns = []
    for col in dataframe.columns:
        col_type = "numeric" if dataframe[col].dtype.kind in "ifc" else "text"
        columns.append({"name": col, "id": col, "type": col_type})

    # Generate automatic alignments
    alignments = generate_column_alignments(dataframe)

    # Apply any override alignments
    if override_alignments:
        alignments.update(override_alignments)

    # Use default sorting by date in descending order for statistics table
    if sort_by is None and id == "statistics-table":
        sort_by = [{"column_id": "date", "direction": "desc"}]

    # Create the DataTable with aligned columns
    return create_data_table(
        data=dataframe.to_dict("records"),
        columns=columns,
        id=id,
        editable=editable,
        row_selectable=False,
        page_size=page_size,
        include_pagination=include_pagination,
        sort_action=sort_action,
        filter_action=filter_action,
        column_alignments=alignments,
        sort_by=sort_by,
    )


#######################################################################
# FORM LAYOUT TEMPLATES
#######################################################################


def create_form_group(
    label, input_component, help_text=None, feedback=None, invalid=False
):
    """
    Create a standardized form group with consistent spacing and alignment.

    Args:
        label: Label text or component
        input_component: The input component
        help_text: Optional help text to display below the input
        feedback: Optional validation feedback text
        invalid: Whether the input is invalid

    Returns:
        A form group div with proper spacing and alignment
    """
    # Use vertical rhythm spacing for form elements
    margin_bottom = get_vertical_rhythm("form_element")

    components = [
        html.Label(label, className="mb-2"),
        input_component,
    ]

    if help_text:
        components.append(html.Small(help_text, className="form-text text-muted mt-1"))

    if feedback:
        feedback_class = "invalid-feedback d-block" if invalid else "invalid-feedback"
        components.append(html.Div(feedback, className=feedback_class))

    return html.Div(components, style={"marginBottom": margin_bottom})


def create_form_row(form_groups, columns=None):
    """
    Create a form row with form groups in columns.

    DEPRECATED: Use ui.grid_utils.create_form_row() instead.

    Args:
        form_groups: List of form group components
        columns: List of column widths for each form group

    Returns:
        A row with form groups in columns
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_form_row() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_form_row(form_groups=form_groups, columns=columns)


def create_form_section(title, components, help_text=None):
    """
    Create a form section with a title and components.

    DEPRECATED: Use ui.grid_utils.create_form_section() instead.

    Args:
        title: Section title
        components: List of components to include in the section
        help_text: Optional help text to display below the title

    Returns:
        A section div with title and components
    """
    warnings.warn(
        "This function is deprecated. Use ui.grid_utils.create_form_section() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return new_create_form_section(
        title=title, components=components, help_text=help_text
    )


#######################################################################
# CONTENT LAYOUT TEMPLATES
#######################################################################


def create_content_section(title, body, footer=None, section_class=None):
    """
    Create a standardized content section with title, body, and optional footer.

    Args:
        title: Section title component or text
        body: Section body content
        footer: Optional section footer content
        section_class: Additional CSS classes for the section

    Returns:
        A content section div
    """
    components = []

    # Calculate margins using our vertical rhythm system
    title_margin = get_vertical_rhythm("after_title")
    section_margin = get_vertical_rhythm("section")

    # Add title with proper spacing
    if isinstance(title, str):
        components.append(html.H3(title, style={"marginBottom": title_margin}))
    else:
        components.append(html.Div(title, style={"marginBottom": title_margin}))

    # Add body
    components.append(html.Div(body))

    # Add footer if provided
    if footer:
        footer_style = {
            "marginTop": get_vertical_rhythm("paragraph"),
            "paddingTop": get_vertical_rhythm("paragraph"),
            "borderTop": f"1px solid {NEUTRAL_COLORS['gray-300']}",
        }
        components.append(html.Div(footer, style=footer_style))

    # Combine any additional classes with our section margin
    section_style = {"marginBottom": section_margin}

    return html.Div(components, className=section_class, style=section_style)


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
        padding = f"p-{COMPONENT_SPACING['card_padding'].replace('rem', '')}"

    return html.Div(content, className=f"{padding} border border-top-0 rounded-bottom")
