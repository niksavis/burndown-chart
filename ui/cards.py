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
from typing import Any, Dict, List, cast

# Third-party library imports
from dash import html, dcc
import dash_bootstrap_components as dbc
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

# Type definition for StyleCellConditional
StyleCellConditional = Dict[str, Any]

#######################################################################
# HELPER FUNCTIONS
#######################################################################


def _get_default_data_source():
    """
    Determine the default data source based on JIRA configuration.

    Returns:
        str: "JIRA" if JIRA is configured, "CSV" otherwise
    """
    try:
        from data.persistence import should_sync_jira

        return "JIRA" if should_sync_jira() else "CSV"
    except ImportError:
        return "CSV"


def _get_default_jql_query():
    """
    Get the default JQL query from app settings.

    Returns:
        str: JQL query from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jql_query", "project = JRASERVER")
    except ImportError:
        return "project = JRASERVER"


def _get_default_jira_api_endpoint():
    """
    Get the default JIRA API endpoint from app settings.

    Returns:
        str: JIRA API endpoint from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get(
            "jira_api_endpoint", "https://jira.atlassian.com/rest/api/2/search"
        )
    except ImportError:
        return "https://jira.atlassian.com/rest/api/2/search"


def _get_default_jira_token():
    """
    Get the default JIRA token from app settings.

    Returns:
        str: JIRA token from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jira_token", "")
    except ImportError:
        return ""


def _get_default_jira_story_points_field():
    """
    Get the default JIRA story points field from app settings.

    Returns:
        str: Story points field from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jira_story_points_field", "")
    except ImportError:
        return ""


def _get_default_jira_cache_max_size():
    """
    Get the default JIRA cache max size from app settings.

    Returns:
        int: Cache max size from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jira_cache_max_size", 100)
    except ImportError:
        return 100


def _get_default_jira_max_results():
    """
    Get the default JIRA max results from app settings.

    Returns:
        int: Max results from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jira_max_results", 1000)
    except ImportError:
        return 1000


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
                                                    style={  # Fixed double curly braces to single
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
                # First row: Deadline and Milestone (side by side)
                dbc.Row(
                    [
                        # Deadline
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
                            md=6,
                            # Removed the mb-3 mb-md-0 classes to fix the spacing issue
                            className="",
                        ),
                        # Milestone toggle and date picker in one column
                        dbc.Col(
                            [
                                # Label and toggle combined in a flex container
                                html.Div(
                                    [
                                        # Label for the milestone section
                                        html.Label(
                                            [
                                                "Milestone:",
                                                create_info_tooltip(
                                                    "milestone-date",
                                                    "Set a milestone marker on the charts (must be before deadline).",
                                                ),
                                            ],
                                            className="fw-medium me-2",
                                            style={
                                                "display": "inline-flex",
                                                "alignItems": "center",
                                            },
                                        ),
                                        # Toggle switch directly next to the label (without text label)
                                        dbc.Switch(
                                            id="milestone-toggle",
                                            value=current_settings.get(
                                                "show_milestone", False
                                            ),
                                            label="",  # Removed "Enable" text
                                            className="ms-2 responsive-toggle",
                                            style={},  # Remove inline transform
                                        ),
                                    ],
                                    className="d-flex align-items-center",  # Removed mb-2 to reduce bottom spacing
                                ),
                                # Date picker in its own row
                                dcc.DatePickerSingle(
                                    id="milestone-picker",
                                    date=current_settings.get("milestone", None),
                                    display_format="YYYY-MM-DD",
                                    first_day_of_week=1,
                                    show_outside_days=True,
                                    with_portal=False,
                                    with_full_screen_portal=False,
                                    placeholder="Select milestone date",
                                    persistence=True,
                                    min_date_allowed=datetime.now().strftime(
                                        "%Y-%m-%d"
                                    ),
                                    style=create_datepicker_style(size="md"),
                                    className="w-100",
                                    disabled=not current_settings.get(
                                        "show_milestone", False
                                    ),
                                ),
                                html.Div(
                                    id="milestone-feedback",
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
                # Second row: PERT Factor (full width)
                dbc.Row(
                    [
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
                                    min=1,  # Start with minimum possible value
                                    max=15,  # This will be updated dynamically by callback
                                    value=current_settings["pert_factor"],
                                    marks={
                                        i: str(i) for i in [1, 3, 5, 8, 10, 12, 15]
                                    },  # This will be updated dynamically by callback
                                    step=1,
                                    tooltip={
                                        "placement": "bottom",
                                        "always_visible": False,
                                    },
                                    className="mb-1 mt-3",
                                ),
                                html.Small(
                                    id="pert-factor-info",
                                    children="PERT Factor determines forecast confidence range",
                                    className="text-muted mt-1 d-block text-center",
                                    style={"cursor": "pointer"},
                                    title="Click to see PERT Factor details",
                                ),
                                html.Div(
                                    id="pert-factor-feedback",
                                    className="d-none",
                                    style=create_form_feedback_style("invalid"),
                                ),
                            ],
                            width=12,
                        ),
                    ],
                    className="mb-3",
                ),
                # Third row: Data Points to Include (full width)
                dbc.Row(
                    [
                        # Data Points - full width
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
                                    style={"cursor": "pointer"},
                                    title="Click to see data points selection details",
                                ),
                            ],
                            width=12,
                        ),
                    ],
                ),
            ],
            className="mb-4 p-3 bg-light rounded-3",
        ),
        # Project Scope Section - Updated breakpoints
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
                            # Changed from md=6 to lg=6 to stack on medium screens
                            lg=6,
                            # Add bottom margin when stacked
                            className="mb-3 mb-lg-0",
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
                            # Changed from md=6 to lg=6 to stack on medium screens
                            lg=6,
                        ),
                    ],
                    className="mb-3",
                ),
                # Points Toggle Section
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                # Label and toggle combined in a flex container
                                html.Div(
                                    [
                                        # Label for the points section
                                        html.Label(
                                            [
                                                "Points Tracking:",
                                                create_info_tooltip(
                                                    "points-toggle",
                                                    "Enable points tracking and forecasting (disable if not using story points).",
                                                ),
                                            ],
                                            className="fw-medium me-2",
                                            style={
                                                "display": "inline-flex",
                                                "alignItems": "center",
                                            },
                                        ),
                                        # Toggle switch directly next to the label (without text label)
                                        dbc.Switch(
                                            id="points-toggle",
                                            value=current_settings.get(
                                                "show_points", False
                                            ),
                                            label="",  # No text label
                                            className="ms-2 responsive-toggle",
                                            style={},  # Remove inline transform
                                        ),
                                    ],
                                    className="d-flex align-items-center mb-2",
                                ),
                            ],
                            width=12,
                        ),
                    ],
                    className="mb-3",
                ),
                # Points Inputs Container (controlled by points toggle)
                html.Div(
                    id="points-inputs-container",
                    children=[
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
                                    # Changed from md=6 to lg=6 to stack on medium screens
                                    lg=6,
                                    # Add bottom margin when stacked
                                    className="mb-3 mb-lg-0",
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
                                                    html.I(
                                                        className="fas fa-calculator"
                                                    ),
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
                                    # Changed from md=6 to lg=6 to stack on medium screens
                                    lg=6,
                                ),
                            ],
                        ),
                    ],  # Close points inputs container
                ),
            ],
            className="mb-4 p-3 bg-light rounded-3",
        ),
        # Data Source Section
        html.Div(
            [
                html.H5(
                    [
                        html.I(
                            className="fas fa-database me-2",
                            style={"color": COLOR_PALETTE["optimistic"]},
                        ),
                        "Data Source",
                    ],
                    className="mb-3 border-bottom pb-2 d-flex align-items-center",
                ),
                # Data Source Selection
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label(
                                    [
                                        "Data Source:",
                                        create_info_tooltip(
                                            "data-source",
                                            "Choose between JSON/CSV file upload or JIRA API data source.",
                                        ),
                                    ],
                                    className="fw-medium mb-2",
                                ),
                                dbc.RadioItems(
                                    id="data-source-selection",
                                    options=[
                                        {
                                            "label": "JSON/CSV Import",
                                            "value": "CSV",
                                        },
                                        {
                                            "label": "JIRA API",
                                            "value": "JIRA",
                                        },
                                    ],
                                    value=_get_default_data_source(),
                                    inline=True,
                                    className="mb-3",
                                ),
                            ],
                            width=12,
                        ),
                    ],
                ),
                # Data Export Action - Available for both data sources
                html.Hr(className="my-3"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label(
                                    "Export Options:",
                                    className="fw-medium mb-2",
                                ),
                                html.Div(
                                    [
                                        create_button(
                                            text="Export Data",
                                            id="export-project-data-button",
                                            variant="secondary",
                                            icon_class="fas fa-file-export",
                                        ),
                                        html.Small(
                                            "Export complete project data as JSON",
                                            className="text-muted mt-1 d-block",
                                        ),
                                        html.Div(
                                            dcc.Download(
                                                id="export-project-data-download"
                                            )
                                        ),
                                    ],
                                    className="d-flex flex-column",
                                ),
                            ],
                            width=12,
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
                            className="fas fa-upload me-2",
                            style={"color": COLOR_PALETTE["items"]},
                        ),
                        "Data Import Configuration",
                    ],
                    className="mb-3 border-bottom pb-2 d-flex align-items-center",
                ),
                # CSV Upload Container (hidden by default when data source is JIRA)
                html.Div(
                    id="csv-upload-container",
                    style={
                        "display": "none"
                        if _get_default_data_source() == "JIRA"
                        else "block"
                    },
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Upload CSV/JSON File:",
                                            className="fw-medium",
                                        ),
                                        dcc.Upload(
                                            id="upload-data",
                                            children=html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-cloud-upload-alt fa-2x mb-2"
                                                    ),
                                                    html.Br(),
                                                    "Drag and Drop or Click to Select",
                                                ],
                                                className="d-flex flex-column justify-content-center align-items-center h-100",
                                                style={"lineHeight": "1.2"},
                                            ),
                                            style={
                                                "width": "100%",
                                                "height": "100px",
                                                "borderWidth": "2px",
                                                "borderStyle": "dashed",
                                                "borderRadius": "8px",
                                                "borderColor": "#dee2e6",
                                                "backgroundColor": "#f8f9fa",
                                                "cursor": "pointer",
                                                "transition": "all 0.2s ease",
                                            },
                                            multiple=False,
                                        ),
                                    ],
                                    width=12,
                                    className="mb-3",
                                ),
                            ],
                        ),
                    ],
                ),
                # Import Status Message Container
                html.Div(
                    id="import-status-message",
                    className="text-success small mb-3",
                    style={"display": "none"},
                ),
                # JIRA Configuration Container (hidden by default when data source is CSV)
                html.Div(
                    id="jira-config-container",
                    style={
                        "display": "block"
                        if _get_default_data_source() == "JIRA"
                        else "none"
                    },
                    children=[
                        # JIRA API Endpoint - Full width on mobile
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "JIRA API Endpoint (URL):",
                                            className="fw-medium",
                                        ),
                                        dbc.Input(
                                            id="jira-url",
                                            type="text",
                                            placeholder="https://your-jira.com/rest/api/2/search",
                                            value=_get_default_jira_api_endpoint(),
                                            style=create_input_style(size="md"),
                                        ),
                                    ],
                                    width=12,
                                    className="mb-3",
                                ),
                            ],
                        ),
                        # JQL Query - Full width on mobile
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "JQL Query:",
                                            className="fw-medium",
                                        ),
                                        dbc.Textarea(
                                            id="jira-jql-query",
                                            placeholder="project = MYPROJECT AND created >= startOfYear()",
                                            value=_get_default_jql_query(),
                                            rows=3,
                                            style=create_input_style(size="md"),
                                        ),
                                        html.Small(
                                            "Use JQL syntax to filter issues. Supports ScriptRunner functions.",
                                            className="text-muted",
                                        ),
                                        # Hidden element for JQL query save status callback
                                        html.Div(
                                            id="jira-jql-query-save-status",
                                            style={"display": "none"},
                                        ),
                                    ],
                                    width=12,
                                    className="mb-3",
                                ),
                            ],
                        ),
                        # Personal Access Token - Full width on mobile
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Personal Access Token (optional):",
                                            className="fw-medium",
                                        ),
                                        dbc.Input(
                                            id="jira-token",
                                            type="password",
                                            placeholder="Optional for public projects",
                                            value=_get_default_jira_token(),
                                            style=create_input_style(size="md"),
                                        ),
                                    ],
                                    width=12,
                                    className="mb-3",
                                ),
                            ],
                        ),
                        # Points Field - Full width on mobile
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Points Field (optional):",
                                            className="fw-medium",
                                        ),
                                        dbc.Input(
                                            id="jira-story-points-field",
                                            type="text",
                                            placeholder="Leave empty if no story points, or enter your JIRA field ID",
                                            value=_get_default_jira_story_points_field(),
                                            style=create_input_style(size="md"),
                                        ),
                                    ],
                                    width=12,
                                    className="mb-3",
                                ),
                            ],
                        ),
                        # Cache Size Limit - Full width on mobile
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Cache Size Limit (MB):",
                                            className="fw-medium",
                                        ),
                                        dbc.Input(
                                            id="jira-cache-max-size",
                                            type="number",
                                            placeholder="100",
                                            value=_get_default_jira_cache_max_size(),
                                            min=1,
                                            max=1000,
                                            style=create_input_style(size="md"),
                                        ),
                                    ],
                                    width=12,
                                    className="mb-3",
                                ),
                            ],
                        ),
                        # Max Results Limit - Full width on mobile
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Max Results per API Call:",
                                            className="fw-medium",
                                        ),
                                        dbc.Input(
                                            id="jira-max-results",
                                            type="number",
                                            placeholder="1000",
                                            value=_get_default_jira_max_results(),
                                            min=1,
                                            max=50000,
                                            style=create_input_style(size="md"),
                                        ),
                                    ],
                                    width=12,
                                    className="mb-3",
                                ),
                            ],
                        ),
                        # Update Data Button Section - Full width on mobile with standardized button styling
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Data Import Actions:",
                                            className="fw-medium",
                                        ),
                                        html.Div(
                                            [
                                                create_button(
                                                    text="Update Data",
                                                    id="update-data-unified",
                                                    variant="primary",
                                                    icon_class="fas fa-sync-alt",
                                                ),
                                                html.Small(
                                                    "Import data from selected source and update charts",
                                                    className="text-muted mt-1 d-block",
                                                ),
                                            ],
                                            className="d-flex flex-column",
                                        ),
                                    ],
                                    width=12,
                                    className="mb-3",
                                ),
                            ],
                        ),
                        # Cache Status and Validation Errors
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            id="jira-cache-status",
                                            className="text-muted small",
                                        ),
                                        html.Div(
                                            id="jira-validation-errors",
                                            className="text-danger small",
                                        ),
                                    ],
                                    width=12,
                                ),
                            ],
                        ),
                        # JIRA Scope Calculation Section
                        html.Hr(className="my-3"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Project Scope from JIRA:",
                                            className="fw-medium",
                                        ),
                                        html.Div(
                                            [
                                                create_button(
                                                    text="Calculate Scope",
                                                    id="jira-scope-calculate-btn",
                                                    variant="success",
                                                    icon_class="fas fa-calculator",
                                                ),
                                                html.Small(
                                                    "Calculate project scope based on JIRA issue statuses",
                                                    className="text-muted mt-1 d-block",
                                                ),
                                            ],
                                            className="d-flex flex-column",
                                        ),
                                        html.Div(
                                            id="jira-scope-status",
                                            className="mt-2",
                                        ),
                                        html.Div(
                                            id="jira-scope-update-time",
                                            className="mt-1",
                                        ),
                                    ],
                                    width=12,
                                    className="mb-3",
                                ),
                            ],
                        ),
                    ],
                ),
                # Hidden store components for JIRA data loading state
                dcc.Store(id="jira-data-loader"),
                dcc.Store(id="jira-data-reload-trigger"),
            ],
            className="mb-4 p-3 bg-light rounded-3",
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
    import numpy as np
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

    # Ensure required columns exist in the DataFrame
    required_columns = [
        "date",
        "completed_items",
        "completed_points",
        "created_items",
        "created_points",
    ]
    for col in required_columns:
        if col not in statistics_df.columns:
            statistics_df[col] = 0  # Add missing columns with default values

    # Function to create a responsive table wrapper
    def create_responsive_table_wrapper(table_component, max_height=None, className=""):
        """
        Create a mobile-responsive wrapper for tables that handles overflow with scrolling.
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

    # Function to detect appropriate column alignment based on data type
    def detect_column_alignment(dataframe, column_name):
        """
        Automatically detect appropriate alignment for a column based on its data type.
        """
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
        {
            "name": "Items Created",
            "id": "created_items",
            "type": "numeric",
        },
        {
            "name": "Points Created",
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

    # Create the enhanced table with consistent columns
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
                    "Enter your weekly completed items and points. Use the ",
                    html.Code("Add Row"),
                    " button to add new entries.",
                ],
                className="text-muted",
            ),
            html.Small(
                [
                    html.I(className="fas fa-plus-circle me-1 text-info"),
                    "Include created items and points to track scope changes.",
                ],
                className="text-muted d-block mt-1",
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
                                                        f"{float(avg_weekly_items):.2f}",
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
                                                        f"{float(avg_weekly_points):.2f}",
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


def create_project_summary_card(
    statistics_df, settings, pert_data=None, show_points=True
):
    """
    Create a card with project dashboard information optimized for side-by-side layout.

    Args:
        statistics_df: DataFrame containing the project statistics
        settings: Dictionary with current settings
        pert_data: Dictionary containing PERT analysis data (optional)
        show_points: Whether points tracking is enabled

    Returns:
        A Dash card component with project dashboard information
    """
    try:
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
                                        width=6 if show_points else 12,
                                        className="px-2",
                                    ),
                                ]
                                + (
                                    [
                                        # Points Forecast Column - only show if points tracking is enabled
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
                                                            style={
                                                                "fontSize": "0.9rem"
                                                            },
                                                        ),
                                                    ],
                                                    className="ms-3",
                                                ),
                                            ],
                                            width=6,
                                            className="px-2",
                                        ),
                                    ]
                                    if show_points
                                    else []
                                ),
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
                                                        f"{float(avg_weekly_items):.2f}",
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
                                        width=6 if show_points else 12,
                                        className="px-2",
                                    ),
                                ]
                                + (
                                    [
                                        # Points velocity - only show if points tracking is enabled
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
                                                            f"{float(avg_weekly_points):.2f}",
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
                                                            style={
                                                                "fontSize": "0.9rem"
                                                            },
                                                        ),
                                                    ],
                                                    className="mb-2",
                                                ),
                                            ],
                                            width=6,
                                            className="px-2",
                                        ),
                                    ]
                                    if show_points
                                    else []
                                ),
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
