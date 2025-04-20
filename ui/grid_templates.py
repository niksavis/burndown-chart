"""
Grid Templates Module

This module provides standardized grid layout components and templates
for consistent layout and alignment throughout the application.
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import html, dash_table
import dash_bootstrap_components as dbc

# Import styling functions from ui.styles
from ui.styles import SPACING, NEUTRAL_COLORS

#######################################################################
# GRID TEMPLATES
#######################################################################


def create_two_column_layout(
    left_content, right_content, left_width=6, right_width=6, row_class="mb-4"
):
    """
    Creates a standardized two-column layout with responsive behavior.

    Args:
        left_content: Content for the left column
        right_content: Content for the right column
        left_width: Width of left column (1-12) for medium screens and up
        right_width: Width of right column (1-12) for medium screens and up
        row_class: Additional classes to apply to the row

    Returns:
        A dbc.Row containing the two-column layout
    """
    return dbc.Row(
        [
            dbc.Col(left_content, xs=12, md=left_width, className="mb-3 mb-md-0"),
            dbc.Col(right_content, xs=12, md=right_width),
        ],
        className=row_class,
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
    if equal_height:
        card1_class = "mb-3 mb-md-0 h-100"
        card2_class = "h-100"
    else:
        card1_class = "mb-3 mb-md-0"
        card2_class = ""

    return dbc.Row(
        [
            dbc.Col(html.Div(card1, className=card1_class), xs=12, md=card1_width),
            dbc.Col(html.Div(card2, className=card2_class), xs=12, md=card2_width),
        ],
        className="mb-4",
    )


def create_three_column_layout(
    left, middle, right, left_width=4, middle_width=4, right_width=4, row_class="mb-4"
):
    """
    Creates a standardized three-column layout with responsive behavior.

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
    return dbc.Row(
        [
            dbc.Col(left, xs=12, md=left_width, className="mb-3 mb-md-0"),
            dbc.Col(middle, xs=12, md=middle_width, className="mb-3 mb-md-0"),
            dbc.Col(right, xs=12, md=right_width),
        ],
        className=row_class,
    )


def create_four_column_layout(cols, widths=None, row_class="mb-4"):
    """
    Creates a standardized four-column layout with responsive behavior.

    Args:
        cols: List of content for the columns
        widths: List of widths for each column (1-12) for medium screens and up
        row_class: Additional classes to apply to the row

    Returns:
        A dbc.Row containing the four-column layout
    """
    if widths is None:
        widths = [3, 3, 3, 3]

    col_components = []
    for i, col_content in enumerate(cols):
        col_class = "mb-3 mb-md-0" if i < len(cols) - 1 else ""
        col_components.append(
            dbc.Col(col_content, xs=12, md=widths[i], className=col_class)
        )

    return dbc.Row(col_components, className=row_class)


def create_full_width_layout(content, row_class="mb-4"):
    """
    Creates a standardized full-width layout.

    Args:
        content: Content for the full-width column
        row_class: Additional classes to apply to the row

    Returns:
        A dbc.Row containing the full-width layout
    """
    return dbc.Row(
        [
            dbc.Col(content, width=12),
        ],
        className=row_class,
    )


#######################################################################
# TABLE TEMPLATES
#######################################################################


def create_standardized_table_style(stripe_color=None):
    """
    Create standardized styling for data tables.

    Args:
        stripe_color: Color for alternating rows (defaults to light gray)

    Returns:
        Dictionary with styling properties
    """
    if stripe_color is None:
        stripe_color = NEUTRAL_COLORS.get("gray-100", "#f8f9fa")

    return {
        "style_table": {
            "overflowX": "auto",
            "borderRadius": "4px",
            "border": f"1px solid {NEUTRAL_COLORS.get('gray-300', '#dee2e6')}",
        },
        "style_header": {
            "backgroundColor": NEUTRAL_COLORS.get("gray-200", "#e9ecef"),
            "fontWeight": "bold",
            "textAlign": "center",
            "padding": f"{SPACING.get('sm', '0.5rem')} {SPACING.get('md', '1rem')}",
            "borderBottom": f"2px solid {NEUTRAL_COLORS.get('gray-400', '#ced4da')}",
        },
        "style_cell": {
            "padding": f"{SPACING.get('xs', '0.25rem')} {SPACING.get('sm', '0.5rem')}",
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

    Returns:
        A dash_table.DataTable with standardized styling
    """
    # Get base styling
    table_style = create_standardized_table_style()

    # Apply column-specific alignments if provided
    if column_alignments:
        style_cell_conditional = [
            {"if": {"column_id": col_id}, "textAlign": alignment}
            for col_id, alignment in column_alignments.items()
        ]
    else:
        style_cell_conditional = []

    # Add highlighting for editable cells
    if editable:
        style_data_conditional = table_style["style_data_conditional"] + [
            {
                "if": {"column_editable": True},
                "backgroundColor": "rgba(0, 123, 255, 0.05)",
                "cursor": "pointer",
            }
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
        style_table=table_style["style_table"],
        style_header=table_style["style_header"],
        style_cell=table_style["style_cell"],
        style_cell_conditional=style_cell_conditional,
        style_data=table_style["style_data"],
        style_data_conditional=style_data_conditional,
        css=[
            # Add modern styling
            {
                "selector": ".dash-spreadsheet-menu",
                "rule": "position: absolute; top: 0.5rem; right: 0.5rem;",
            },
            {"selector": ".dash-filter--case", "rule": "display: none;"},
        ],
        **pagination_settings,
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
    components = [
        html.Label(label, className="mb-2"),
        input_component,
    ]

    if help_text:
        components.append(html.Small(help_text, className="form-text text-muted mt-1"))

    if feedback:
        feedback_class = "invalid-feedback d-block" if invalid else "invalid-feedback"
        components.append(html.Div(feedback, className=feedback_class))

    return html.Div(components, className="mb-3")


def create_form_row(form_groups, columns=None):
    """
    Create a form row with form groups in columns.

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

    return dbc.Row(cols, className="mb-3")


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
    section_components = [
        html.H5(title, className="mb-3 border-bottom pb-2"),
    ]

    if help_text:
        section_components.append(html.P(help_text, className="text-muted mb-3"))

    section_components.extend(components)

    return html.Div(section_components, className="mb-4")


#######################################################################
# CONTENT LAYOUT TEMPLATES
#######################################################################


def create_content_section(title, body, footer=None, section_class="mb-5"):
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

    # Add title
    if isinstance(title, str):
        components.append(html.H3(title, className="mb-4"))
    else:
        components.append(html.Div(title, className="mb-4"))

    # Add body
    components.append(html.Div(body))

    # Add footer if provided
    if footer:
        components.append(html.Div(footer, className="mt-3 pt-3 border-top"))

    return html.Div(components, className=section_class)


def create_tab_content(content, padding="p-3"):
    """
    Create standardized tab content with consistent padding.

    Args:
        content: The content to display in the tab
        padding: Padding class to apply

    Returns:
        A div with the tab content and consistent styling
    """
    return html.Div(content, className=f"{padding} border border-top-0 rounded-bottom")
