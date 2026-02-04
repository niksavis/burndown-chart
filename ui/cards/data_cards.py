"""Data table cards for weekly statistics display and editing.

This module provides data table components for displaying and editing weekly
work statistics, including items/points completed and scope changes.

WARNING: This file exceeds the 500-line architectural guideline (currently ~650 lines).
TODO: Future optimization should split table rendering logic into separate helpers:
      - table_styles.py: Styling functions
      - table_builders.py: Table creation logic
      - column_definitions.py: Column config

Functions:
    create_statistics_data_card: Main data table card with editing capabilities
"""

from __future__ import annotations

from typing import Any, Dict, List, cast

import dash_bootstrap_components as dbc
import pandas as pd
from dash import dash_table, html

from configuration.settings import STATISTICS_HELP_TEXTS
from ui.styles import (
    create_card_header_with_tooltip,
    create_standardized_card,
    NEUTRAL_COLORS,
    get_vertical_rhythm,
)
from ui.tooltip_utils import create_info_tooltip
from ui.button_utils import create_button

# Type aliases for complex nested structures
StyleCellConditional = Dict[str, Any]


def create_statistics_data_card(current_statistics) -> dbc.Card:
    """Create weekly statistics data table card with editing capabilities.

    Displays a responsive data table showing weekly work completion and scope changes.
    Includes editable fields, pagination, sorting, filtering, and column explanations.

    Args:
        current_statistics: List of dictionaries containing current statistics data

    Returns:
        Standardized card component containing:
            - Help text explaining weekly timebox model
            - Column definitions (collapsible)
            - Enhanced data table with:
                * Editable cells
                * Sort/filter capabilities
                * Pagination (10 rows per page)
                * Mobile-responsive design
            - Add Row button for new weekly entries
    """
    # Convert to DataFrame for automatic column type detection
    statistics_df = pd.DataFrame(current_statistics)

    # Card header with title and tooltip
    header_content = create_card_header_with_tooltip(
        "Weekly Progress Data",
        tooltip_id="statistics-data",
        tooltip_text="Weekly tracking of completed and newly created work items and story points. Each Monday date represents work done during that week (Monday through Sunday). This data drives all velocity calculations and forecasting.",
        help_key="weekly_progress_data_explanation",
        help_category="dashboard",
    )

    # Ensure required columns exist in the DataFrame
    if statistics_df.empty:
        # Initialize with empty structure if no data
        statistics_df = pd.DataFrame(
            columns=[
                "date",
                "completed_items",
                "completed_points",
                "created_items",
                "created_points",
            ]
        )

    # Helper functions for responsive table creation
    def create_responsive_table_wrapper(table_component):
        """Wrap table in a responsive container with mobile optimizations."""
        return html.Div(
            table_component,
            className="table-responsive",
            style={
                # Enable horizontal scrolling on overflow
                "overflowX": "auto",
                # Smooth scrolling on touch devices
                "WebkitOverflowScrolling": "touch",
                # Ensure table takes full width
                "width": "100%",
            },
        )

    def detect_column_alignment(dataframe, column_name):
        """Detect optimal alignment for a column based on its data type."""
        if pd.api.types.is_numeric_dtype(dataframe[column_name]):
            return "right"
        elif pd.api.types.is_datetime64_any_dtype(dataframe[column_name]):
            return "center"
        else:
            return "left"

    def generate_column_alignments(dataframe):
        """
        Generate a dictionary of optimal column alignments for all columns in a DataFrame.
        """
        alignments = {}
        for column in dataframe.columns:
            alignments[column] = detect_column_alignment(dataframe, column)
        return alignments

    # Create standardized styling for data tables
    def create_standardized_table_style(stripe_color=None, mobile_optimized=True):
        """
        Create standardized styling for data tables with responsive behavior.
        """
        if stripe_color is None:
            stripe_color = NEUTRAL_COLORS.get("gray-100", "#f8f9fa")

        # Use vertical rhythm system for consistent table spacing
        cell_padding_v = "0.5rem"
        cell_padding_h = "0.75rem"

        style_dict = {
            "style_table": {
                "overflowX": "auto",
                "borderRadius": "4px",
                "border": f"1px solid {NEUTRAL_COLORS.get('gray-300', '#dee2e6')}",
                "marginBottom": get_vertical_rhythm("section"),
                "WebkitOverflowScrolling": "touch",  # Improved scroll on iOS
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
                },
                # Ensure text wraps on small screens
                {
                    "selector": ".dash-cell-value",
                    "rule": "white-space: normal !important; word-break: break-word !important;",
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

        return style_dict

    # Create a direct implementation of data table with enhanced responsive features
    def create_enhanced_data_table(
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
        mobile_responsive=True,
        priority_columns=None,
    ):
        """
        Create a data table with standardized styling and enhanced mobile responsiveness.
        """
        # Get base styling
        table_style = create_standardized_table_style(
            mobile_optimized=mobile_responsive
        )  # Apply column-specific alignments if provided
        style_cell_conditional: List[StyleCellConditional] = []
        if column_alignments:
            style_cell_conditional = [
                cast(
                    StyleCellConditional,
                    {"if": {"column_id": col_id}, "textAlign": alignment},
                )
                for col_id, alignment in column_alignments.items()
            ]  # Add mobile optimization for columns if needed
        if mobile_responsive and priority_columns:
            # Create conditional styling for non-priority columns on mobile
            for col in columns:
                if col["id"] not in priority_columns:
                    style_cell_conditional.append(
                        cast(
                            StyleCellConditional,
                            {
                                "if": {"column_id": col["id"]},
                                "className": "mobile-hidden",
                                "media": "screen and (max-width: 767px)",
                            },
                        )
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
                # Show validation indicators for numeric columns
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
            pagination_settings = {}  # Create the table with enhanced styling and responsive features
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
            style_cell_conditional=style_cell_conditional,  # type: ignore # Ignore type error for style_cell_conditional
            style_data=table_style["style_data"],
            style_data_conditional=style_data_conditional,
            css=table_style.get("css", []),
            tooltip_delay=0,
            tooltip_duration=None,
            **pagination_settings,
        )

    # Define standard column configuration to ensure consistent columns
    columns = [
        {
            "name": "Week Start (Monday)",
            "id": "date",
            "type": "text",
        },
        {
            "name": "Items Done This Week",
            "id": "completed_items",
            "type": "numeric",
        },
        {
            "name": "Points Done This Week",
            "id": "completed_points",
            "type": "numeric",
        },
        {
            "name": "New Items Added",
            "id": "created_items",
            "type": "numeric",
        },
        {
            "name": "New Points Added",
            "id": "created_points",
            "type": "numeric",
        },
    ]

    # Set column alignments based on data type
    column_alignments = {
        "date": "center",
        "completed_items": "right",
        "completed_points": "right",
        "created_items": "right",
        "created_points": "right",
    }

    # Create the statistics table directly in Weekly Data tab
    # No hidden placeholder needed - Dash handles components in tabs just fine!
    statistics_table = create_enhanced_data_table(
        data=statistics_df.to_dict("records"),
        columns=columns,
        id="statistics-table",
        editable=True,
        row_selectable=False,
        page_size=10,
        include_pagination=True,
        sort_action="native",
        filter_action="native",
        column_alignments=column_alignments,
        sort_by=[{"column_id": "date", "direction": "desc"}],
    )

    # Create help text for data input
    help_text = html.Div(
        [
            html.Small(
                [
                    html.I(className="fas fa-info-circle me-1 text-info"),
                    "Enter weekly data for work completed and created. Each Monday date represents work done during that full week (Monday through Sunday, inclusive).",
                ],
                className="text-muted",
            ),
            html.Small(
                [
                    html.I(className="fas fa-calendar-week me-1 text-info"),
                    html.Strong("Weekly Timeboxes: "),
                    "Monday date = work completed/created from that Monday through the following Sunday (7-day period, inclusive). Use the ",
                    html.Code("Add Row"),
                    " button to add new weekly entries.",
                ],
                className="text-muted d-block mt-1",
            ),
            html.Small(
                [
                    html.I(className="fas fa-plus-circle me-1 text-info"),
                    html.Strong("Scope Tracking: "),
                    "Include both completed work (finished items/points) and created work (new items/points added to backlog) to track scope changes.",
                ],
                className="text-muted d-block mt-1",
            ),
            html.Small(
                [
                    html.I(className="fas fa-calendar-alt me-1 text-info"),
                    html.Strong("Date Format: "),
                    "Always use Monday dates in ",
                    html.Code("YYYY-MM-DD"),
                    " format (e.g., 2025-09-22 for the week of Sept 22-28, inclusive).",
                ],
                className="text-muted d-block mt-1",
            ),
            html.Small(
                [
                    html.I(className="fas fa-exclamation-triangle me-1 text-warning"),
                    html.Strong("Important: ", style={"color": "#856404"}),
                    "Manual edits persist in the database. However, ",
                    html.Strong("Update Data"),
                    " will overwrite all edits with fresh JIRA data, and ",
                    html.Strong("Force Refresh"),
                    " will delete all data and reload from JIRA. Save important manual changes elsewhere before updating.",
                ],
                className="d-block mt-2 p-2",
                style={
                    "backgroundColor": "#fff3cd",
                    "border": "1px solid #ffc107",
                    "borderRadius": "4px",
                    "color": "#856404",
                },
            ),
        ],
        className="mb-3",
    )

    # Wrap the table in a responsive container
    responsive_table = create_responsive_table_wrapper(statistics_table)

    # Create column explanations section
    column_explanations = html.Div(
        [
            # Collapsible button for column explanations
            dbc.Button(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "Column Explanations",
                ],
                id="column-explanations-toggle",
                color="info",
                outline=True,
                size="sm",
                className="mb-2",
            ),
            # Collapsible content
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H6("Data Column Definitions", className="mb-3"),
                            html.Div(
                                [
                                    # Week Start (Monday) explanation
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className="fas fa-calendar-week me-1 text-primary"
                                                    ),
                                                    "Week Start (Monday):",
                                                ]
                                            ),
                                            html.Span(
                                                " Data collection date (weekly snapshots). Each Monday represents work done during that full week (Monday-Sunday).",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "date-field-column",
                                                STATISTICS_HELP_TEXTS["date_field"],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    # Items Done This Week explanation
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className="fas fa-check-circle me-1 text-success"
                                                    ),
                                                    "Items Done This Week:",
                                                ]
                                            ),
                                            html.Span(
                                                " Number of work items (stories, tasks, tickets) completed during this weekly period.",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "completed-items-column",
                                                STATISTICS_HELP_TEXTS[
                                                    "completed_items"
                                                ],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    # Points Done This Week explanation
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className="fas fa-star me-1 text-warning"
                                                    ),
                                                    "Points Done This Week:",
                                                ]
                                            ),
                                            html.Span(
                                                " Story points or effort units completed during this weekly period.",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "completed-points-column",
                                                STATISTICS_HELP_TEXTS[
                                                    "completed_points"
                                                ],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    # New Items Added explanation
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className="fas fa-plus-circle me-1 text-info"
                                                    ),
                                                    "New Items Added:",
                                                ]
                                            ),
                                            html.Span(
                                                " Number of new work items added to the project during this period (scope growth).",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "created-items-column",
                                                STATISTICS_HELP_TEXTS["created_items"],
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    # New Points Added explanation
                                    html.Div(
                                        [
                                            html.Strong(
                                                [
                                                    html.I(
                                                        className="fas fa-plus-square me-1 text-secondary"
                                                    ),
                                                    "New Points Added:",
                                                ]
                                            ),
                                            html.Span(
                                                " Story points for new work items added during this period (scope change impact).",
                                                className="ms-1",
                                            ),
                                            create_info_tooltip(
                                                "created-points-column",
                                                STATISTICS_HELP_TEXTS["created_points"],
                                            ),
                                        ],
                                        className="mb-0",
                                    ),
                                ],
                                className="small",
                            ),
                        ]
                    ),
                    color="light",
                ),
                id="column-explanations-collapse",
                is_open=False,
            ),
        ],
        className="mb-3",
    )

    # Create the card body content
    body_content = [
        # Add help text at the top
        help_text,
        # Add column explanations section
        column_explanations,
        # Add space before table
        html.Div(className="mb-3"),
        # Add the responsive table
        responsive_table,
        # Create a row for table actions with better styling
        html.Div(
            [
                # Button for adding rows with tooltip
                html.Div(
                    [
                        create_button(
                            text="Add Row",
                            id="add-row-button",
                            variant="primary",
                            icon_class="fas fa-plus",
                        ),
                        dbc.Tooltip(
                            "Adds a new weekly entry with Monday date 7 days after the most recent entry. Enter work completed and created during that week (Monday-Sunday).",
                            target="add-row-button",
                            placement="top",
                            trigger="click",
                            autohide=True,
                        ),
                    ],
                    className="mb-2 mb-sm-0",  # Add bottom margin on mobile
                    style={"display": "inline-block"},
                ),
            ],
            className="d-flex flex-wrap justify-content-center align-items-center mt-4",
            # Use flex-wrap to allow buttons to wrap on mobile
        ),
    ]

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        body_className="p-3",
        shadow="sm",
    )
