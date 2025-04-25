"""
UI Cards Module

This module provides card components that make up the main UI sections
of the application, such as the forecast graph card, info card, etc.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from datetime import datetime, timedelta

# Third-party library imports
import dash_bootstrap_components as dbc
from dash import html, dcc
import pandas as pd

# Application imports
from configuration import HELP_TEXTS, COLOR_PALETTE

# Import styling functions from utility modules
from ui.styles import (
    NEUTRAL_COLORS,
    create_standardized_card,
    create_card_header_with_tooltip,
    create_rhythm_text,
    create_datepicker_style,
    create_form_feedback_style,
    create_input_style,
)
from ui.button_utils import create_button
from ui.tooltip_utils import create_info_tooltip

#######################################################################
# CARD COMPONENTS
#######################################################################


def create_forecast_graph_card():
    """
    Create the forecast graph card component with customized download filename.

    Returns:
        Dash Card component with the forecast graph
    """
    # Generate the current date for the filename
    current_date = datetime.now().strftime("%Y%m%d")
    default_filename = f"burndown_forecast_{current_date}"

    # Create the card header with tooltip
    header_content = create_card_header_with_tooltip(
        "Forecast Graph",
        tooltip_id="forecast-graph",
        tooltip_text=HELP_TEXTS["forecast_explanation"],
    )

    # Create the card body content
    body_content = dcc.Graph(
        id="forecast-graph",
        style={
            "height": "700px"
        },  # Updated from 650px to match the height in apply_layout_settings
        config={
            # Only specify the filename, let Plotly handle the rest of the export settings
            "toImageButtonOptions": {
                "filename": default_filename,
            },
        },
    )

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        body_className="p-2",  # Less padding to maximize graph space
        shadow="sm",
    )


def create_forecast_info_card():
    """
    Create the forecast methodology information card component with concise explanation.

    Returns:
        Dash Card component with concise forecast methodology explanation
    """
    # Generate a unique ID for this collapse component
    collapse_id = "forecast-info-collapse"

    # Create the card body content with optimized layout
    body_content = html.Div(
        [
            # Concise introduction paragraph
            create_rhythm_text(
                [
                    html.Strong("PERT Forecast: "),
                    "Estimates based on optimistic, most likely, and pessimistic scenarios from your historical data.",
                ],
                element_type="paragraph",
            ),
            # Compact list with less styling and more concise descriptions
            html.Div(
                className="row g-2 mb-2",
                children=[
                    html.Div(
                        className="col-12 col-md-6",
                        children=html.Div(
                            className="border rounded p-2",
                            children=[
                                html.Strong("Line Colors:"),
                                html.Ul(
                                    [
                                        html.Li(
                                            [
                                                html.Span(
                                                    "Blue",
                                                    style={
                                                        "color": COLOR_PALETTE["items"],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                "/",
                                                html.Span(
                                                    "Orange",
                                                    style={
                                                        "color": COLOR_PALETTE[
                                                            "points"
                                                        ],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                ": Most likely",
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                html.Span(
                                                    "Teal",
                                                    style={
                                                        "color": COLOR_PALETTE[
                                                            "optimistic"
                                                        ],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                "/",
                                                html.Span(
                                                    "Gold",
                                                    style={
                                                        "color": "rgb(184, 134, 11)",
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                ": Optimistic",
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                html.Span(
                                                    "Indigo",
                                                    style={
                                                        "color": COLOR_PALETTE[
                                                            "pessimistic"
                                                        ],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                "/",
                                                html.Span(
                                                    "Brown",
                                                    style={
                                                        "color": "rgb(165, 42, 42)",
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                ": Pessimistic",
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                html.Span(
                                                    "Red",
                                                    style={
                                                        "color": "red",
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                ": Deadline",
                                            ]
                                        ),
                                    ],
                                    className="mb-0 ps-3",
                                    style={"fontSize": "0.9rem"},
                                ),
                            ],
                        ),
                    ),
                    html.Div(
                        className="col-12 col-md-6",
                        children=html.Div(
                            className="border rounded p-2",
                            children=[
                                html.Strong("Reading Guide:"),
                                html.Ul(
                                    [
                                        html.Li("Solid lines: Historical data"),
                                        html.Li("Dashed/dotted: Forecasts"),
                                        html.Li(
                                            [
                                                "Dates in ",
                                                html.Span(
                                                    "green", style={"color": "green"}
                                                ),
                                                ": On track",
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                "Dates in ",
                                                html.Span(
                                                    "red", style={"color": "red"}
                                                ),
                                                ": At risk",
                                            ]
                                        ),
                                    ],
                                    className="mb-0 ps-3",
                                    style={"fontSize": "0.9rem"},
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ],
        style={"textAlign": "left"},
    )

    # Return a card with collapsible body content
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                "Forecast Information",
                                className="d-inline mb-0",
                                style={"fontSize": "0.875rem", "fontWeight": "600"},
                            ),
                            className="col-10 col-lg-11",  # Explicit Bootstrap column classes
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"{collapse_id}-button",
                                        color="link",
                                        size="sm",
                                        className="p-0 border-0",
                                    ),
                                    create_info_tooltip(
                                        "forecast-info",
                                        "How to interpret the forecast graph.",
                                    ),
                                ],
                                className="d-flex justify-content-end align-items-center",
                            ),
                            className="col-2 col-lg-1",  # Explicit Bootstrap column classes
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                className="py-2 px-3 d-flex justify-content-between align-items-center",
            ),
            dbc.Collapse(
                dbc.CardBody(body_content, className="p-3"),
                id=collapse_id,
                is_open=False,
            ),
        ],
        className="my-2 shadow-sm",  # Changed from "mb-3 shadow-sm mt-3" to "my-2" for consistent 8px margins
    )


def create_pert_analysis_card():
    """
    Create the PERT analysis card component.

    Returns:
        Dash Card component for PERT analysis
    """
    # Create the card header with tooltip
    header_content = create_card_header_with_tooltip(
        "PERT Analysis",
        tooltip_id="pert-info",
        tooltip_text="PERT (Program Evaluation and Review Technique) estimates project completion time based on optimistic, pessimistic, and most likely scenarios.",
    )

    # Create the card body content
    body_content = html.Div(id="pert-info-container", className="text-center")

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        className="mb-3 h-100",
        body_className="p-3",
        shadow="sm",
    )


def create_input_parameters_card(
    current_settings, avg_points_per_item, estimated_total_points
):
    """
    Create the input parameters card component with improved organization and visual hierarchy.

    Args:
        current_settings: Dictionary with current application settings
        avg_points_per_item: Current average points per item
        estimated_total_points: Estimated total points

    Returns:
        Dash Card component for input parameters
    """
    # Create the card header with tooltip
    header_content = create_card_header_with_tooltip(
        "Input Parameters",
        tooltip_id="parameters",
        tooltip_text="Change these values to adjust your project forecast.",
    )

    # Create the card body content
    body_content = [
        # Project Timeline Section
        html.Div(
            [
                html.H5(
                    [
                        html.I(
                            className="fas fa-calendar-alt me-2",
                            style={"color": COLOR_PALETTE["items"]},
                        ),
                        "Project Timeline",
                    ],
                    className="mb-3 border-bottom pb-2 d-flex align-items-center",
                ),
                # First row: Deadline and PERT Factor (swapped and no padding)
                dbc.Row(
                    [
                        # Deadline - now first
                        dbc.Col(
                            [
                                html.Label(
                                    [
                                        "Deadline:",
                                        create_info_tooltip(
                                            "deadline",
                                            HELP_TEXTS["deadline"],
                                        ),
                                    ],
                                    className="fw-medium",
                                ),
                                dcc.DatePickerSingle(
                                    id="deadline-picker",
                                    date=current_settings["deadline"],
                                    display_format="YYYY-MM-DD",
                                    first_day_of_week=1,
                                    show_outside_days=True,
                                    # Use a responsive portal approach - will only be used on small screens
                                    with_portal=False,
                                    with_full_screen_portal=False,
                                    placeholder="Select deadline date",
                                    persistence=True,
                                    min_date_allowed=datetime.now().strftime(
                                        "%Y-%m-%d"
                                    ),
                                    style=create_datepicker_style(size="md"),
                                    className="w-100",
                                ),
                                html.Div(
                                    id="deadline-feedback",
                                    className="d-none",
                                    style=create_form_feedback_style("invalid"),
                                ),
                            ],
                            width=12,
                            sm=12,  # Full width on mobile/small screens
                            md=4,  # 1/3 width on medium and up
                            className="mb-4 mb-md-0",  # Add bottom margin on mobile only
                        ),
                        # PERT Factor - directly adjacent to Deadline
                        dbc.Col(
                            [
                                html.Label(
                                    [
                                        "PERT Factor:",
                                        create_info_tooltip(
                                            "pert-factor",
                                            HELP_TEXTS["pert_factor"],
                                        ),
                                    ],
                                    className="fw-medium",
                                ),
                                dcc.Slider(
                                    id="pert-factor-slider",
                                    min=3,
                                    max=15,
                                    value=current_settings["pert_factor"],
                                    marks={i: str(i) for i in range(3, 16, 2)},
                                    step=1,
                                    tooltip={
                                        "placement": "bottom",
                                        "always_visible": False,
                                    },
                                    className="my-3",  # Added margin top and bottom
                                ),
                                html.Small(
                                    id="pert-factor-info",
                                    children="PERT Factor determines forecast confidence range",
                                    className="text-muted mt-1 d-block text-center",
                                    style={
                                        "cursor": "pointer"
                                    },  # Make it look clickable
                                    title="Click to see PERT Factor details",  # Add hover title
                                ),
                                html.Div(
                                    id="pert-factor-feedback",
                                    className="d-none",
                                    style=create_form_feedback_style("invalid"),
                                ),
                            ],
                            width=12,  # Full width on extra small screens
                            sm=12,  # Full width on small screens
                            md=8,  # 2/3 width on medium and up
                        ),
                    ],
                    className="mb-3",  # Keep margin below this row
                ),
                # Second row: Data Points to Include (full width)
                dbc.Row(
                    [
                        # Data Points - now full width
                        dbc.Col(
                            [
                                html.Label(
                                    [
                                        "Data Points to Include:",
                                        create_info_tooltip(
                                            "data-points-count",
                                            HELP_TEXTS["data_points_count"],
                                        ),
                                    ],
                                    className="fw-medium",
                                ),
                                dcc.Slider(
                                    id="data-points-input",
                                    min=current_settings["pert_factor"] * 2,
                                    max=10,
                                    value=current_settings.get(
                                        "data_points_count",
                                        current_settings["pert_factor"] * 2,
                                    ),
                                    marks=None,
                                    step=1,
                                    tooltip={
                                        "placement": "bottom",
                                        "always_visible": False,
                                    },
                                    className="mb-1 mt-3",
                                ),
                                html.Small(
                                    id="data-points-info",
                                    children="Using all available data points",
                                    className="text-muted mt-1 d-block text-center",
                                    style={
                                        "cursor": "pointer"
                                    },  # Make it look clickable
                                    title="Click to see data points selection details",  # Add hover title
                                ),
                            ],
                            width=12,  # Full width in all screen sizes
                        ),
                    ],
                ),
            ],
            className="mb-4 p-3 bg-light rounded-3",
        ),
        # Project Scope Section - unchanged
        html.Div(
            [
                html.H5(
                    [
                        html.I(
                            className="fas fa-tasks me-2",
                            style={"color": COLOR_PALETTE["points"]},
                        ),
                        "Project Scope",
                    ],
                    className="mb-3 border-bottom pb-2 d-flex align-items-center",
                ),
                # Items (Estimated and Total) in one row
                dbc.Row(
                    [
                        # Estimated Items
                        dbc.Col(
                            [
                                html.Label(
                                    [
                                        "Remaining Estimated Items:",
                                        create_info_tooltip(
                                            "estimated-items",
                                            HELP_TEXTS["estimated_items"],
                                        ),
                                    ],
                                    className="fw-medium",
                                ),
                                dbc.Input(
                                    id="estimated-items-input",
                                    type="number",
                                    value=current_settings["estimated_items"],
                                    min=0,
                                    step=1,
                                    style=create_input_style(size="md"),
                                    invalid=False,  # Will be controlled by callback
                                    className="form-control",
                                ),
                                html.Div(
                                    id="estimated-items-feedback",
                                    className="d-none",
                                    style=create_form_feedback_style("invalid"),
                                ),
                            ],
                            width=12,
                            md=6,
                        ),
                        # Total Items
                        dbc.Col(
                            [
                                html.Label(
                                    [
                                        "Remaining Total Items:",
                                        create_info_tooltip(
                                            "total-items",
                                            HELP_TEXTS["total_items"],
                                        ),
                                    ],
                                    className="fw-medium",
                                ),
                                dbc.Input(
                                    id="total-items-input",
                                    type="number",
                                    value=current_settings["total_items"],
                                    min=0,
                                    step=1,
                                    style=create_input_style(size="md"),
                                    invalid=False,  # Will be controlled by callback
                                    className="form-control",
                                ),
                                html.Div(
                                    id="total-items-feedback",
                                    className="d-none",
                                    style=create_form_feedback_style("invalid"),
                                ),
                            ],
                            width=12,
                            md=6,
                        ),
                    ],
                    className="mb-3",
                ),
                # Points (Estimated and Total) in one row
                dbc.Row(
                    [
                        # Estimated Points
                        dbc.Col(
                            [
                                html.Label(
                                    [
                                        "Remaining Estimated Points:",
                                        create_info_tooltip(
                                            "estimated-points",
                                            HELP_TEXTS["estimated_points"],
                                        ),
                                    ],
                                    className="fw-medium",
                                ),
                                dbc.Input(
                                    id="estimated-points-input",
                                    type="number",
                                    value=current_settings["estimated_points"],
                                    min=0,
                                    step=1,
                                    style=create_input_style(size="md"),
                                    invalid=False,  # Will be controlled by callback
                                    className="form-control",
                                ),
                                html.Div(
                                    id="estimated-points-feedback",
                                    className="d-none",
                                    style=create_form_feedback_style("invalid"),
                                ),
                            ],
                            width=12,
                            md=6,
                        ),
                        # Total Points (Calculated)
                        dbc.Col(
                            [
                                html.Label(
                                    [
                                        "Remaining Total Points:",
                                        html.Span(
                                            "auto",
                                            className="badge bg-secondary ms-1",
                                            style={
                                                "fontSize": "0.7rem",
                                                "verticalAlign": "text-top",
                                            },
                                        ),
                                        create_info_tooltip(
                                            "total-points",
                                            HELP_TEXTS["total_points"],
                                        ),
                                    ],
                                    className="fw-medium",
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(
                                            id="total-points-display",
                                            value=f"{estimated_total_points:.0f}",
                                            disabled=True,
                                            style=create_input_style(
                                                disabled=True, readonly=True
                                            ),
                                        ),
                                        dbc.InputGroupText(
                                            html.I(className="fas fa-calculator"),
                                            style={
                                                "backgroundColor": NEUTRAL_COLORS[
                                                    "gray-200"
                                                ]
                                            },
                                        ),
                                    ]
                                ),
                                html.Small(
                                    id="points-calculation-info",
                                    children=[
                                        f"Using {avg_points_per_item:.1f} points per remaining item for calculation"
                                    ],
                                    className="text-muted mt-1 d-block",
                                ),
                            ],
                            width=12,
                            md=6,
                        ),
                    ],
                ),
            ],
            className="mb-4 p-3 bg-light rounded-3",
        ),
        # Data Import Section
        html.Div(
            [
                html.H5(
                    [
                        html.I(
                            className="fas fa-file-import me-2",
                            style={"color": COLOR_PALETTE["optimistic"]},
                        ),
                        "Data Import",
                    ],
                    className="mb-3 border-bottom pb-2 d-flex align-items-center",
                ),
                # CSV Upload
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label(
                                    [
                                        "Upload Statistics CSV:",
                                        create_info_tooltip(
                                            "csv-upload",
                                            HELP_TEXTS["csv_format"],
                                        ),
                                    ],
                                    className="fw-medium mb-2",
                                ),
                                dcc.Upload(
                                    id="upload-data",
                                    children=html.Div(
                                        [
                                            html.I(className="fas fa-file-upload me-2"),
                                            "Drag and Drop or ",
                                            html.A(
                                                "Select CSV File",
                                                className="text-primary",
                                            ),
                                        ],
                                        className="d-flex align-items-center justify-content-center",
                                    ),
                                    style={
                                        "width": "100%",
                                        "height": "60px",
                                        "lineHeight": "60px",
                                        "borderWidth": "1px",
                                        "borderStyle": "dashed",
                                        "borderRadius": "0.25rem",
                                        "textAlign": "center",
                                        "backgroundColor": NEUTRAL_COLORS["gray-100"],
                                        "transition": "border-color 0.15s ease-in-out, background-color 0.15s ease-in-out",
                                        "borderColor": COLOR_PALETTE["items"],
                                    },
                                    multiple=False,
                                ),
                            ],
                            width=12,
                        ),
                    ],
                ),
            ],
            className="p-3 bg-light rounded-3",
        ),
    ]

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        className="mb-3 h-100 shadow-sm",
        body_className="p-3",
        shadow="sm",
    )


def create_statistics_data_card(current_statistics):
    """
    Create the statistics data card component with standardized table styling.

    Args:
        current_statistics: List of dictionaries containing current statistics data

    Returns:
        Dash Card component for statistics data
    """
    import pandas as pd
    from dash import html, dash_table
    import dash_bootstrap_components as dbc
    from ui.styles import NEUTRAL_COLORS, get_vertical_rhythm

    # Create the card header with tooltip
    header_content = create_card_header_with_tooltip(
        "Statistics Data",
        tooltip_id="statistics-data",
        tooltip_text=HELP_TEXTS["statistics_table"],
    )

    # Convert to DataFrame for automatic column type detection
    statistics_df = pd.DataFrame(current_statistics)

    # Function to detect appropriate column alignment based on data type
    def detect_column_alignment(dataframe, column_name):
        """
        Automatically detect appropriate alignment for a column based on its data type.
        """
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

    # Generate a dictionary of optimal column alignments for all columns
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
        )

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
            pagination_settings = {}

        # Create the table with enhanced styling and responsive features
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
            css=table_style.get("css", []),
            tooltip_delay=0,
            tooltip_duration=None,
            **pagination_settings,
        )

    # Function to create a responsive table wrapper
    def create_responsive_table_wrapper(table_component, max_height=None, className=""):
        """
        Create a mobile-responsive wrapper for tables that handles overflow with scrolling.
        """
        container_style = {
            "overflowX": "auto",
            "width": "100%",
            "-webkit-overflow-scrolling": "touch",  # Smooth scrolling on iOS
        }

        if max_height:
            container_style["maxHeight"] = max_height
            container_style["overflowY"] = "auto"

        return html.Div(
            table_component,
            className=f"table-responsive {className}",
            style=container_style,
        )

    # Create a data table with optimal column alignments
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
        return create_enhanced_data_table(
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
            mobile_responsive=True,
            priority_columns=["date"] if id == "statistics-table" else None,
        )

    # Use automatic column alignment if we have data
    if not statistics_df.empty:
        # Create an automatically aligned table with enhanced responsiveness
        statistics_table = create_aligned_datatable(
            dataframe=statistics_df,
            id="statistics-table",
            editable=True,
            page_size=10,
            include_pagination=True,
            filter_action="native",
            sort_action="native",
            # Override automatic alignments if needed
            override_alignments={
                "date": "center",  # Ensure dates are centered
            },
        )
    else:
        # Define column configuration for empty table
        columns = [
            {
                "name": "Date (YYYY-MM-DD)",
                "id": "date",
                "type": "text",
            },
            {
                "name": "Items Completed",
                "id": "completed_items",
                "type": "numeric",
            },
            {
                "name": "Points Completed",
                "id": "completed_points",
                "type": "numeric",
            },
        ]

        # Set column alignments based on data type
        column_alignments = {
            "date": "center",
            "completed_items": "right",
            "completed_points": "right",
        }

        # Create the enhanced table with manual alignments
        statistics_table = create_enhanced_data_table(
            data=current_statistics,
            columns=columns,
            id="statistics-table",
            editable=True,
            row_selectable=False,
            page_size=10,
            include_pagination=True,
            sort_action="native",
            filter_action="native",
            column_alignments=column_alignments,
        )

    # Create help text for data input
    help_text = html.Div(
        [
            html.Small(
                [
                    html.I(className="fas fa-info-circle me-1 text-info"),
                    "Enter your weekly completed items and points. Use the ",
                    html.Code("Add Row"),
                    " button to add new entries.",
                ],
                className="text-muted",
            ),
            html.Small(
                [
                    html.I(className="fas fa-calendar-alt me-1 text-info"),
                    "Dates should be in ",
                    html.Code("YYYY-MM-DD"),
                    " format.",
                ],
                className="text-muted d-block mt-1",
            ),
        ],
        className="mb-3",
    )

    # Wrap the table in a responsive container
    responsive_table = create_responsive_table_wrapper(statistics_table)

    # Create the card body content
    body_content = [
        # Add help text at the top
        help_text,
        # Add space between help text and table (removed export buttons from top)
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
                            "Adds a new row with date 7 days after the most recent entry",
                            target="add-row-button",
                            placement="top",
                        ),
                    ],
                    className="me-2 mb-2 mb-sm-0",  # Add right margin and bottom margin on mobile
                    style={"display": "inline-block"},
                ),
                # Button to clear filters - resized and repositioned
                html.Div(
                    create_button(
                        text="Clear Filters",
                        id="clear-filters-button",
                        variant="outline-secondary",
                        icon_class="fas fa-filter",
                    ),
                    className="me-2 mb-2 mb-sm-0",  # Add right margin and bottom margin on mobile
                    style={"display": "inline-block"},
                ),
                # Export Statistics Button with fixed styling
                html.Div(
                    [
                        create_button(
                            text="Export Statistics",
                            id="export-statistics-button",
                            variant="outline-secondary",
                            icon_class="fas fa-file-export",
                        ),
                        dbc.Tooltip(
                            "Export statistics data as CSV",
                            target="export-statistics-button",
                            placement="top",
                        ),
                        html.Div(dcc.Download(id="export-statistics-download")),
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


def create_project_status_card(statistics_df, settings):
    """
    Create a comprehensive project status card with metrics and indicators.

    Args:
        statistics_df: DataFrame containing the project statistics
        settings: Dictionary with current settings

    Returns:
        A Dash card component for project status summary
    """
    try:
        import pandas as pd
        import dash_bootstrap_components as dbc
        from dash import html

        # Extract key metrics from settings (these represent remaining work)
        remaining_items = settings.get("total_items", 0)
        remaining_points = settings.get("total_points", 0)

        # Calculate completed items and points from statistics
        completed_items = (
            int(statistics_df["completed_items"].sum())
            if not statistics_df.empty
            else 0
        )
        completed_points = (
            int(statistics_df["completed_points"].sum())
            if not statistics_df.empty
            else 0
        )

        # Calculate true project totals (completed + remaining)
        total_items = remaining_items + completed_items
        total_points = round(
            remaining_points + completed_points
        )  # Round to nearest integer
        remaining_points = round(
            remaining_points
        )  # Round remaining points to nearest integer

        # Calculate percentages based on true project totals
        items_percentage = (
            int((completed_items / total_items) * 100) if total_items > 0 else 0
        )
        points_percentage = (
            int((completed_points / total_points) * 100) if total_points > 0 else 0
        )

        # Calculate average weekly velocity and coefficient of variation (last 10 weeks)
        # Create a copy of the DataFrame to avoid SettingWithCopyWarning
        recent_df = statistics_df.copy() if not statistics_df.empty else pd.DataFrame()

        # Default values if no data is available
        avg_weekly_items = 0
        avg_weekly_points = 0
        stability_status = "Unknown"
        stability_color = "secondary"
        stability_icon = "fa-question-circle"

        # Convert to datetime to ensure proper week grouping
        if not recent_df.empty:
            # Use proper pandas assignment with .loc to avoid SettingWithCopyWarning
            recent_df.loc[:, "date"] = pd.to_datetime(recent_df["date"])

            # Add week and year columns
            recent_df.loc[:, "week"] = recent_df["date"].dt.isocalendar().week
            recent_df.loc[:, "year"] = recent_df["date"].dt.isocalendar().year

            # Group by week to get weekly data
            weekly_data = (
                recent_df.groupby(["year", "week"])
                .agg({"completed_items": "sum", "completed_points": "sum"})
                .reset_index()
                .tail(10)  # Consider only the last 10 weeks
            )

            # Calculate average weekly velocity
            avg_weekly_items = weekly_data["completed_items"].mean()
            avg_weekly_points = weekly_data["completed_points"].mean()

            # Calculate standard deviation for coefficient of variation
            std_weekly_items = weekly_data["completed_items"].std()
            std_weekly_points = weekly_data["completed_points"].std()

            # Calculate coefficient of variation (CV = std/mean)
            cv_items = (
                (std_weekly_items / avg_weekly_items * 100)
                if avg_weekly_items > 0
                else 0
            )
            cv_points = (
                (std_weekly_points / avg_weekly_points * 100)
                if avg_weekly_points > 0
                else 0
            )

            # Count zero weeks and high weeks (outliers)
            zero_item_weeks = len(weekly_data[weekly_data["completed_items"] == 0])
            zero_point_weeks = len(weekly_data[weekly_data["completed_points"] == 0])
            high_item_weeks = len(
                weekly_data[weekly_data["completed_items"] > avg_weekly_items * 2]
            )
            high_point_weeks = len(
                weekly_data[weekly_data["completed_points"] > avg_weekly_points * 2]
            )

            # Calculate overall stability score (0-100)
            stability_score = max(
                0,
                100
                - cv_items * 0.5
                - cv_points * 0.5
                - zero_item_weeks * 10
                - zero_point_weeks * 10
                - high_item_weeks * 5
                - high_point_weeks * 5,
            )
            stability_score = min(100, max(0, stability_score))

            # Determine velocity consistency status
            if stability_score >= 80:
                stability_status = "Consistent"
                stability_color = "success"
                stability_icon = "fa-check-circle"
            elif stability_score >= 50:
                stability_status = "Moderate"
                stability_color = "warning"
                stability_icon = "fa-exclamation-circle"
            else:
                stability_status = "Variable"
                stability_color = "danger"
                stability_icon = "fa-times-circle"

        # Calculate days of data available
        if not statistics_df.empty:
            if "date" in statistics_df.columns:
                earliest_date = pd.to_datetime(statistics_df["date"].min())
                latest_date = pd.to_datetime(statistics_df["date"].max())
                days_of_data = (
                    (latest_date - earliest_date).days + 1
                    if earliest_date and latest_date
                    else 0
                )
            else:
                days_of_data = 0
        else:
            days_of_data = 0

        # Create the card component
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.H4("Project Status Summary", className="d-inline"),
                        create_info_tooltip(
                            "project-status",
                            "Summary of your project's current progress and metrics.",
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        # Project Completion Stats Row
                        dbc.Row(
                            [
                                # Items Completion
                                dbc.Col(
                                    [
                                        html.H6("Items Completion"),
                                        html.Div(
                                            [
                                                html.Span(
                                                    f"{items_percentage}%",
                                                    style={
                                                        "fontSize": "24px",
                                                        "fontWeight": "bold",
                                                        "color": COLOR_PALETTE["items"],
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        f"Completed: {completed_items} of {total_items} items",
                                                    ],
                                                    className="text-muted small",
                                                ),
                                            ],
                                            className="text-center mb-2",
                                        ),
                                        # Progress bar for items
                                        dbc.Progress(
                                            value=items_percentage,
                                            color="info",
                                            className="mb-3",
                                            style={"height": "10px"},
                                        ),
                                    ],
                                    md=6,
                                ),
                                # Points Completion
                                dbc.Col(
                                    [
                                        html.H6("Points Completion"),
                                        html.Div(
                                            [
                                                html.Span(
                                                    f"{points_percentage}%",
                                                    style={
                                                        "fontSize": "24px",
                                                        "fontWeight": "bold",
                                                        "color": COLOR_PALETTE[
                                                            "points"
                                                        ],
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        f"Completed: {completed_points} of {total_points} points",
                                                    ],
                                                    className="text-muted small",
                                                ),
                                            ],
                                            className="text-center mb-2",
                                        ),
                                        # Progress bar for points
                                        dbc.Progress(
                                            value=points_percentage,
                                            color="warning",
                                            className="mb-3",
                                            style={"height": "10px"},
                                        ),
                                    ],
                                    md=6,
                                ),
                            ],
                            className="mb-4",
                        ),
                        # Metrics Row
                        dbc.Row(
                            [
                                # Weekly Averages
                                dbc.Col(
                                    [
                                        html.H6("Weekly Averages", className="mb-3"),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-tasks me-2",
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "items"
                                                                ]
                                                            },
                                                        ),
                                                        f"{avg_weekly_items:.1f}",
                                                        html.Small(" items/week"),
                                                    ],
                                                    className="d-flex align-items-center mb-2",
                                                ),
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line me-2",
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ]
                                                            },
                                                        ),
                                                        f"{avg_weekly_points:.1f}",
                                                        html.Small(" points/week"),
                                                    ],
                                                    className="d-flex align-items-center",
                                                ),
                                            ],
                                            className="ps-3",
                                        ),
                                    ],
                                    md=4,
                                ),
                                # Velocity Stability
                                dbc.Col(
                                    [
                                        html.H6("Velocity Stability", className="mb-3"),
                                        html.Div(
                                            [
                                                html.I(
                                                    className=f"fas {stability_icon} me-2",
                                                    style={
                                                        "color": f"var(--bs-{stability_color})"
                                                    },
                                                ),
                                                html.Span(
                                                    stability_status,
                                                    style={
                                                        "color": f"var(--bs-{stability_color})",
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                            ],
                                            className="d-flex align-items-center ps-3",
                                        ),
                                    ],
                                    md=4,
                                ),
                                # Dataset Info
                                dbc.Col(
                                    [
                                        html.H6("Dataset Info", className="mb-3"),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-calendar-alt me-2 text-secondary"
                                                        ),
                                                        f"{days_of_data} days of data",
                                                    ],
                                                    className="d-flex align-items-center mb-2",
                                                ),
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-table me-2 text-secondary"
                                                        ),
                                                        f"{len(statistics_df) if not statistics_df.empty else 0} data points",
                                                    ],
                                                    className="d-flex align-items-center",
                                                ),
                                            ],
                                            className="ps-3",
                                        ),
                                    ],
                                    md=4,
                                ),
                            ],
                        ),
                    ],
                    className="py-4",
                ),
            ],
            className="mb-4 shadow-sm",
        )

    except Exception as e:
        # Return an error card if something goes wrong
        import dash_bootstrap_components as dbc
        from dash import html

        return dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("Project Status Summary", className="text-danger")
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-exclamation-triangle text-danger me-2"
                                ),
                                html.Span(
                                    "Unable to display project information. Please ensure you have valid project data.",
                                    className="text-danger",
                                ),
                            ],
                            className="d-flex align-items-center mb-2",
                        ),
                        html.Small(f"Error: {str(e)}", className="text-muted"),
                    ]
                ),
            ],
            className="mb-4 shadow-sm",
        )


def create_project_summary_card(statistics_df, settings, pert_data=None):
    """
    Create a card with project dashboard information optimized for side-by-side layout.

    Args:
        statistics_df: DataFrame containing the project statistics
        settings: Dictionary with current settings
        pert_data: Dictionary containing PERT analysis data (optional)

    Returns:
        A Dash card component with project dashboard information
    """
    try:
        import pandas as pd
        import dash_bootstrap_components as dbc
        from dash import html

        # Make a copy of statistics_df to avoid modifying the original
        statistics_df = (
            statistics_df.copy() if not statistics_df.empty else pd.DataFrame()
        )

        # Convert 'date' column to datetime right at the beginning
        if not statistics_df.empty and "date" in statistics_df.columns:
            statistics_df["date"] = pd.to_datetime(statistics_df["date"])

        # Calculate values needed for the dashboard
        if not statistics_df.empty:
            # Add week and year columns
            recent_df = statistics_df.tail(10).copy()
            recent_df.loc[:, "week"] = recent_df["date"].dt.isocalendar().week
            recent_df.loc[:, "year"] = recent_df["date"].dt.isocalendar().year

            weekly_data = (
                recent_df.groupby(["year", "week"])
                .agg({"completed_items": "sum", "completed_points": "sum"})
                .reset_index()
            )

            # Calculate metrics needed for PERT table
            avg_weekly_items = weekly_data["completed_items"].mean()
            avg_weekly_points = weekly_data["completed_points"].mean()
        else:
            avg_weekly_items = 0
            avg_weekly_points = 0

        # Format deadline string for display
        deadline_date = settings.get("deadline")
        deadline_obj = None
        if deadline_date:
            deadline_str = deadline_date
            try:
                deadline_obj = datetime.strptime(deadline_date, "%Y-%m-%d")
                days_to_deadline = (deadline_obj - datetime.now()).days
            except (ValueError, TypeError):
                days_to_deadline = None
        else:
            deadline_str = "Not set"
            days_to_deadline = None

        # Create the pert_info content
        if pert_data:
            try:
                pert_time_items = pert_data.get("pert_time_items")
                pert_time_points = pert_data.get("pert_time_points")

                # If both PERT values are None, provide a placeholder message
                if pert_time_items is None and pert_time_points is None:
                    pert_info_content = html.Div(
                        "Forecast available after data processing",
                        className="text-muted text-center py-2",
                        style={"fontSize": "1rem"},
                    )
                else:
                    # Format PERT data for compact display
                    current_date = datetime.now()

                    if pert_time_items is not None:
                        items_completion_date = current_date + timedelta(
                            days=pert_time_items
                        )
                        items_completion_str = items_completion_date.strftime(
                            "%Y-%m-%d"
                        )
                        items_days = int(pert_time_items)
                        items_weeks = round(pert_time_items / 7, 1)
                    else:
                        items_completion_str = "Unknown"
                        items_days = "--"
                        items_weeks = "--"

                    if pert_time_points is not None:
                        points_completion_date = current_date + timedelta(
                            days=pert_time_points
                        )
                        points_completion_str = points_completion_date.strftime(
                            "%Y-%m-%d"
                        )
                        points_days = int(pert_time_points)
                        points_weeks = round(pert_time_points / 7, 1)
                    else:
                        points_completion_str = "Unknown"
                        points_days = "--"
                        points_weeks = "--"

                    # Create compact PERT info content with optimized spacing
                    pert_info_content = html.Div(
                        [
                            # Title
                            html.H6(
                                "Project Completion Forecast",
                                className="border-bottom pb-1 mb-3",
                                style={"fontSize": "1.1rem", "fontWeight": "bold"},
                            ),
                            # PERT Forecast in compact table format
                            dbc.Row(
                                [
                                    # Items Forecast Column
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ],
                                                            "fontSize": "1rem",
                                                        },
                                                    ),
                                                    html.Span(
                                                        "Items Completion:",
                                                        style={
                                                            "fontSize": "0.95rem",
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                ],
                                                className="mb-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        f"{items_completion_str}",
                                                        className="fw-bold",
                                                        style={
                                                            "fontSize": "1rem",
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ],
                                                        },
                                                    ),
                                                ],
                                                className="ms-3 mb-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        f"{items_days} days ({items_weeks} weeks)",
                                                        style={"fontSize": "0.9rem"},
                                                    ),
                                                ],
                                                className="ms-3",
                                            ),
                                        ],
                                        width=6,
                                        className="px-2",
                                    ),
                                    # Points Forecast Column
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-chart-line me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "points"
                                                            ],
                                                            "fontSize": "1rem",
                                                        },
                                                    ),
                                                    html.Span(
                                                        "Points Completion:",
                                                        style={
                                                            "fontSize": "0.95rem",
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                ],
                                                className="mb-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        f"{points_completion_str}",
                                                        className="fw-bold",
                                                        style={
                                                            "fontSize": "1rem",
                                                            "color": COLOR_PALETTE[
                                                                "points"
                                                            ],
                                                        },
                                                    ),
                                                ],
                                                className="ms-3 mb-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        f"{points_days} days ({points_weeks} weeks)",
                                                        style={"fontSize": "0.9rem"},
                                                    ),
                                                ],
                                                className="ms-3",
                                            ),
                                        ],
                                        width=6,
                                        className="px-2",
                                    ),
                                ],
                                className="mb-4",  # Increased bottom margin for better spacing
                            ),
                            # Weekly velocity section
                            html.H6(
                                "Weekly Velocity",
                                className="border-bottom pb-1 mb-3",
                                style={"fontSize": "1.1rem", "fontWeight": "bold"},
                            ),
                            dbc.Row(
                                [
                                    # Items velocity
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ],
                                                            "fontSize": "1rem",
                                                        },
                                                    ),
                                                    html.Span(
                                                        f"{avg_weekly_items:.1f}",
                                                        className="fw-bold",
                                                        style={
                                                            "fontSize": "1.1rem",
                                                            "color": COLOR_PALETTE[
                                                                "items"
                                                            ],
                                                        },
                                                    ),
                                                    html.Small(
                                                        " items/week",
                                                        style={"fontSize": "0.9rem"},
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                        ],
                                        width=6,
                                        className="px-2",
                                    ),
                                    # Points velocity
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-chart-line me-1",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "points"
                                                            ],
                                                            "fontSize": "1rem",
                                                        },
                                                    ),
                                                    html.Span(
                                                        f"{avg_weekly_points:.1f}",
                                                        className="fw-bold",
                                                        style={
                                                            "fontSize": "1.1rem",
                                                            "color": COLOR_PALETTE[
                                                                "points"
                                                            ],
                                                        },
                                                    ),
                                                    html.Small(
                                                        " points/week",
                                                        style={"fontSize": "0.9rem"},
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                        ],
                                        width=6,
                                        className="px-2",
                                    ),
                                ],
                                className="mb-3",  # Added bottom margin to prevent overlap
                            ),
                            # Deadline section if available
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-calendar-alt me-1 text-secondary",
                                                style={"fontSize": "1rem"},
                                            ),
                                            html.Span(
                                                "Deadline: ",
                                                style={
                                                    "fontSize": "0.95rem",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            html.Span(
                                                deadline_str,
                                                style={"fontSize": "0.95rem"},
                                            ),
                                            html.Span(
                                                f" ({days_to_deadline} days remaining)"
                                                if days_to_deadline is not None
                                                else "",
                                                style={
                                                    "fontSize": "0.9rem",
                                                    "marginLeft": "8px",
                                                },
                                            ),
                                        ],
                                        className="mt-2",
                                    ),
                                ]
                            )
                            if deadline_date
                            else html.Div(),
                        ],
                        className="mb-2",  # Added bottom margin to prevent overlap with card border
                    )
            except Exception as pert_error:
                pert_info_content = html.P(
                    f"Error: {str(pert_error)}",
                    className="text-danger p-2",
                    style={"fontSize": "1rem"},
                )
        else:
            pert_info_content = html.Div(
                "Project forecast will display here once data is available",
                className="text-muted text-center py-3",
                style={"fontSize": "1rem"},
            )

        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.H4(
                            "Project Dashboard",
                            className="d-inline",
                        ),
                        create_info_tooltip(
                            "project-dashboard",
                            "Project analysis based on your historical data.",
                        ),
                    ],
                    className="py-2",
                ),
                dbc.CardBody(
                    [
                        # The content is directly placed here without any header or section dividers
                        html.Div(
                            pert_info_content,
                            id="project-dashboard-pert-content",
                            className="pt-1 pb-2",  # Added padding at top and bottom
                        ),
                    ],
                    className="p-3",  # Increased padding for better spacing
                ),
            ],
            className="mb-3 shadow-sm h-100",
        )
    except Exception as e:
        # Fallback card in case of errors
        return dbc.Card(
            [
                dbc.CardHeader(
                    html.H4(
                        "Project Dashboard",
                        className="d-inline",
                        style={"fontSize": "1.4rem"},  # Increased heading size
                    )
                ),
                dbc.CardBody(
                    [
                        html.P(
                            "Unable to display project information. Please ensure you have valid project data.",
                            className="text-danger mb-1",
                            style={"fontSize": "1rem"},
                        ),
                        html.Small(f"Error: {str(e)}", className="text-muted"),
                    ],
                    className="p-3",
                ),
            ],
            className="mb-3 shadow-sm h-100",
        )


def create_items_forecast_info_card(statistics_df=None, pert_data=None):
    """
    Create a concise forecast information card for the Items per Week tab.

    Args:
        statistics_df: DataFrame containing the project statistics (optional)
        pert_data: Dictionary containing PERT analysis data (optional)

    Returns:
        Dash Card component with items forecast explanation
    """

    # Extract metrics from statistics if available
    if statistics_df is not None and not statistics_df.empty:
        # Convert to datetime to ensure proper week grouping
        recent_df = statistics_df.copy()
        recent_df["date"] = pd.to_datetime(recent_df["date"])
        recent_df["week"] = recent_df["date"].dt.isocalendar().week
        recent_df["year"] = recent_df["date"].dt.isocalendar().year

        # Use tail(10) to focus on recent data
        recent_df = recent_df.tail(10)

    # Generate a unique ID for this collapse component
    collapse_id = "items-forecast-info-collapse"

    # The card content with chart elements and forecast method
    chart_info = html.Div(
        className="row g-3",
        children=[
            # Column 1: Chart Elements
            html.Div(
                className="col-12 col-md-6",
                children=html.Div(
                    className="border rounded p-2 h-100",
                    children=[
                        html.H6(
                            "Chart Elements",
                            className="mb-2",
                            style={"fontSize": "0.875rem", "fontWeight": "600"},
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Span(
                                            "Blue Bars",
                                            style={
                                                "color": COLOR_PALETTE["items"],
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Historical weekly completed items",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Span(
                                            "Dark Blue Line",
                                            style={
                                                "color": "#0047AB",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Weighted 4-week moving average",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Span(
                                            "Patterned Bar",
                                            style={
                                                "color": COLOR_PALETTE["items"],
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Next week's forecast",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
            # Column 2: Forecast Method
            html.Div(
                className="col-12 col-md-6",
                children=html.Div(
                    className="border rounded p-2 h-100",
                    children=[
                        html.H6(
                            "PERT Forecast Method",
                            className="mb-2",
                            style={"fontSize": "0.875rem", "fontWeight": "600"},
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Strong("Most Likely: "),
                                        "Average of recent weekly data",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Optimistic: "),
                                        "Average of highest performing weeks",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Pessimistic: "),
                                        "Average of lowest performing weeks",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Weighted Average: "),
                                        "Recent weeks weighted [10%, 20%, 30%, 40%]",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
        ],
    )

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                "Items Forecast Information",
                                className="d-inline mb-0",
                                style={"fontSize": "0.875rem", "fontWeight": "600"},
                            ),
                            className="col-10 col-lg-11",  # Explicit Bootstrap column classes
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"{collapse_id}-button",
                                        color="link",
                                        size="sm",
                                        className="p-0 border-0",
                                    ),
                                    create_info_tooltip(
                                        "items-forecast-info",
                                        "Understanding the weekly items forecast chart and trends.",
                                    ),
                                ],
                                className="d-flex justify-content-end align-items-center",
                            ),
                            className="col-2 col-lg-1",  # Explicit Bootstrap column classes
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                className="py-2 px-3 d-flex justify-content-between align-items-center",
            ),
            dbc.Collapse(
                dbc.CardBody(chart_info, className="p-3"),
                id=collapse_id,
                is_open=False,
            ),
        ],
        className="my-2 shadow-sm",  # Changed from "mt-3 mb-2 shadow-sm" to "my-2" for consistent 8px margins
    )


def create_points_forecast_info_card(statistics_df=None, pert_data=None):
    """
    Create a concise forecast information card for the Points per Week tab.

    Args:
        statistics_df: DataFrame containing the project statistics (optional)
        pert_data: Dictionary containing PERT analysis data (optional)

    Returns:
        Dash Card component with points forecast explanation
    """

    # Extract metrics from statistics if available
    if statistics_df is not None and not statistics_df.empty:
        # Convert to datetime to ensure proper week grouping
        recent_df = statistics_df.copy()
        recent_df["date"] = pd.to_datetime(recent_df["date"])
        recent_df["week"] = recent_df["date"].dt.isocalendar().week
        recent_df["year"] = recent_df["date"].dt.isocalendar().year

        # Use tail(10) to focus on recent data
        recent_df = recent_df.tail(10)

    # Generate a unique ID for this collapse component
    collapse_id = "points-forecast-info-collapse"

    # The card content with chart elements and forecast method
    chart_info = html.Div(
        className="row g-3",
        children=[
            # Column 1: Chart Elements
            html.Div(
                className="col-12 col-md-6",
                children=html.Div(
                    className="border rounded p-2 h-100",
                    children=[
                        html.H6(
                            "Chart Elements",
                            className="mb-2",
                            style={"fontSize": "0.875rem", "fontWeight": "600"},
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Span(
                                            "Orange Bars",
                                            style={
                                                "color": COLOR_PALETTE["points"],
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Historical weekly completed points",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Span(
                                            "Tomato Line",
                                            style={
                                                "color": "#FF6347",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Weighted 4-week moving average",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Span(
                                            "Patterned Bar",
                                            style={
                                                "color": COLOR_PALETTE["points"],
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Next week's forecast with confidence interval",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
            # Column 2: Forecast Method
            html.Div(
                className="col-12 col-md-6",
                children=html.Div(
                    className="border rounded p-2 h-100",
                    children=[
                        html.H6(
                            "PERT Forecast Method",
                            className="mb-2",
                            style={"fontSize": "0.875rem", "fontWeight": "600"},
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Strong("Most Likely: "),
                                        "Average of recent weekly data",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Optimistic: "),
                                        "Average of highest performing weeks",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Pessimistic: "),
                                        "Average of lowest performing weeks",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Weighted Average: "),
                                        "Recent weeks weighted [10%, 20%, 30%, 40%]",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
        ],
    )

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                "Points Forecast Information",
                                className="d-inline mb-0",
                                style={"fontSize": "0.875rem", "fontWeight": "600"},
                            ),
                            className="col-10 col-lg-11",  # Explicit Bootstrap column classes
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"{collapse_id}-button",
                                        color="link",
                                        size="sm",
                                        className="p-0 border-0",
                                    ),
                                    create_info_tooltip(
                                        "points-forecast-info",
                                        "Understanding the weekly points forecast chart and trends.",
                                    ),
                                ],
                                className="d-flex justify-content-end align-items-center",
                            ),
                            className="col-2 col-lg-1",  # Explicit Bootstrap column classes
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                className="py-2 px-3 d-flex justify-content-between align-items-center",
            ),
            dbc.Collapse(
                dbc.CardBody(chart_info, className="p-3"),
                id=collapse_id,
                is_open=False,
            ),
        ],
        className="my-2 shadow-sm",
    )
