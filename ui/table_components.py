"""
Table Components Module

This module provides standardized table components with consistent styling,
responsive behavior, and accessibility features.
"""

from dash import html, dash_table
import dash_bootstrap_components as dbc
from typing import List, Dict, Any, Optional, Union

from ui.aria_utils import enhance_data_table


def create_basic_table(
    data: List[Dict[str, Any]],
    columns: List[Dict[str, str]],
    id: Optional[str] = None,
    striped: bool = True,
    bordered: bool = True,
    hover: bool = True,
    responsive: bool = True,
    className: str = "",
) -> Union[html.Div, dbc.Table]:
    """
    Create a basic table component with standard styling.

    Args:
        data: List of dictionaries containing the data
        columns: List of column specifications with 'id' and 'name' keys
        id: Component ID (optional)
        striped: Whether to use striped rows
        bordered: Whether to add borders
        hover: Whether to add hover effect
        responsive: Whether to wrap in responsive container
        className: Additional CSS classes

    Returns:
        A Dash table component
    """
    # Create the table
    table = dbc.Table(
        # Generate header
        [
            html.Thead(html.Tr([html.Th(col["name"]) for col in columns])),
            # Generate body
            html.Tbody(
                [
                    html.Tr([html.Td(row.get(col["id"], "")) for col in columns])
                    for row in data
                ]
            ),
        ],
        striped=striped,
        bordered=bordered,
        hover=hover,
        responsive=False,  # We'll handle responsiveness ourselves
        className=className,
        id=id,
    )

    # Wrap in responsive container if requested
    if responsive:
        return html.Div(
            table,
            className="table-responsive",
            style={"overflowX": "auto", "width": "100%"},
        )

    return table


def create_data_table(
    data: List[Dict[str, Any]],
    columns: List[Dict[str, str]],
    id: str,
    page_size: int = 10,
    sortable: bool = True,
    filterable: bool = False,
    export_format: Optional[List[str]] = None,
    mobile_responsive: bool = True,
    caption: Optional[str] = None,
) -> html.Div:
    """
    Create an advanced data table with pagination, sorting, and filtering.

    Args:
        data: List of dictionaries containing the data
        columns: List of column specifications
        id: Component ID
        page_size: Number of rows per page
        sortable: Whether columns are sortable
        filterable: Whether to include filters
        export_format: List of export formats to include (e.g., ["csv", "excel"])
        mobile_responsive: Whether to optimize for mobile
        caption: Optional caption for accessibility

    Returns:
        A Dash DataTable wrapped in a container
    """
    # Configure column settings
    if sortable:
        for col in columns:
            col["sortable"] = True

    # Add filter inputs if requested
    if filterable:
        for col in columns:
            col["filter_options"] = {"case": "insensitive"}

    # Create the DataTable
    table = dash_table.DataTable(
        id=id,
        columns=columns,
        data=data,
        page_size=page_size,
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "padding": "8px 12px",
            "fontSize": "14px",
        },
        style_header={
            "backgroundColor": "#f8f9fa",
            "fontWeight": "bold",
            "border": "1px solid #dee2e6",
        },
        style_data={
            "border": "1px solid #f0f0f0",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#f9f9f9",
            }
        ],
    )

    # Add export buttons if requested
    export_buttons = []
    if export_format:
        # This is a placeholder - implementation would depend on your app's export handling
        export_buttons = [
            html.Div(
                [
                    html.Button(
                        f"Export as {fmt.upper()}",
                        id=f"{id}-export-{fmt}",
                        className="btn btn-outline-secondary btn-sm me-2",
                    )
                    for fmt in export_format
                ],
                className="d-flex justify-content-end my-2",
            )
        ]

    # Apply mobile optimizations if requested
    if mobile_responsive:
        table_container = html.Div(
            export_buttons + [table],
            className="table-responsive mobile-optimized-table",
        )
    else:
        table_container = html.Div(export_buttons + [table])

    # Add accessibility features
    options = {}
    if caption:
        options["caption"] = caption

    return enhance_data_table(table_container, options)


# Placeholder for future migration of existing table components
# DO NOT modify existing code until testing confirms this module works
