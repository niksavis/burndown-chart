"""
UI Cards Module

This module provides card components that make up the main UI sections
of the application, such as the forecast graph card, info card, etc.
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import pandas as pd

# Import from other modules
from configuration import HELP_TEXTS, COLOR_PALETTE
from visualization import empty_figure

# Fix circular import issue - import directly from components instead of ui
from ui.components import create_info_tooltip, create_pert_info_table

# Import styling functions from ui.styles
from ui.styles import (
    create_input_style,
    create_datepicker_style,
    create_slider_style,
    create_form_feedback_style,
    NEUTRAL_COLORS,
)

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

    # Use the standardized card styling function
    from ui.styles import create_standardized_card, create_card_header_with_tooltip

    # Create the card header with tooltip
    header_content = create_card_header_with_tooltip(
        "Forecast Graph",
        tooltip_id="forecast-graph",
        tooltip_text=HELP_TEXTS["forecast_explanation"],
    )

    # Create the card body content
    body_content = dcc.Graph(
        id="forecast-graph",
        style={"height": "650px"},
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
    Create the forecast methodology information card component with enhanced explanations.

    Returns:
        Dash Card component with detailed forecast methodology explanation
    """
    # Use the standardized card styling function
    from ui.styles import (
        create_standardized_card,
        create_card_header_with_tooltip,
        create_rhythm_text,
        get_vertical_rhythm,
        apply_vertical_rhythm,
    )

    # Create the card header with tooltip
    header_content = create_card_header_with_tooltip(
        "Forecast Information",
        tooltip_id="forecast-info",
        tooltip_text="Detailed explanation of how to interpret the forecast graph.",
    )

    # Create the card body content with proper vertical rhythm
    body_content = html.Div(
        [
            # Introduction paragraph with proper spacing
            create_rhythm_text(
                [
                    html.Strong("Forecast Methodology: "),
                    "PERT (Program Evaluation and Review Technique) estimation based on your historical performance data. ",
                    "The forecast uses three scenarios:",
                ],
                element_type="paragraph",
            ),
            # List with proper spacing between items and after the list
            html.Ul(
                [
                    html.Li(
                        [
                            html.Strong("Optimistic: "),
                            html.Span(
                                "Teal",
                                style={
                                    "color": COLOR_PALETTE["optimistic"],
                                    "fontWeight": "bold",
                                },
                            ),
                            " for items, ",
                            html.Span(
                                "Gold",
                                style={
                                    "color": "rgb(184, 134, 11)",
                                    "fontWeight": "bold",
                                },
                            ),
                            " for points. Based on your best performance periods (20% confidence level).",
                        ],
                        style=apply_vertical_rhythm("list_item"),
                    ),
                    html.Li(
                        [
                            html.Strong("Most Likely: "),
                            html.Span(
                                "Blue",
                                style={
                                    "color": COLOR_PALETTE["items"],
                                    "fontWeight": "bold",
                                },
                            ),
                            " for items, ",
                            html.Span(
                                "Orange",
                                style={
                                    "color": COLOR_PALETTE["points"],
                                    "fontWeight": "bold",
                                },
                            ),
                            " for points. Based on your average performance (50% confidence level).",
                        ],
                        style=apply_vertical_rhythm("list_item"),
                    ),
                    html.Li(
                        [
                            html.Strong("Pessimistic: "),
                            html.Span(
                                "Purple",
                                style={
                                    "color": COLOR_PALETTE["pessimistic"],
                                    "fontWeight": "bold",
                                },
                            ),
                            " for items, ",
                            html.Span(
                                "Brown",
                                style={
                                    "color": "rgb(165, 42, 42)",
                                    "fontWeight": "bold",
                                },
                            ),
                            " for points. Based on your slowest performance periods (80% confidence level).",
                        ]
                    ),
                ],
                style=apply_vertical_rhythm("list"),
            ),
            # Second paragraph with proper spacing
            create_rhythm_text(
                [
                    html.Strong("Reading the Graph: "),
                    "Solid lines show historical data. Dashed and dotted lines show forecasts. ",
                    "Where these lines cross zero indicates estimated completion dates.",
                ],
                element_type="paragraph",
            ),
            # Final paragraph with no bottom margin since it's the last element
            create_rhythm_text(
                [
                    html.Strong("Color Coding for Estimates: "),
                    "Estimated days appear in ",
                    html.Span(
                        "green",
                        style={"color": "green", "fontWeight": "bold"},
                    ),
                    " when on track to meet the deadline, and in ",
                    html.Span(
                        "red",
                        style={"color": "red", "fontWeight": "bold"},
                    ),
                    " when at risk of missing the deadline. The red vertical line represents your deadline date.",
                ],
                element_type="paragraph",
            ),
        ],
        style={"textAlign": "left"},
    )

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        body_className="py-3 px-3",  # Using standardized padding
        shadow="sm",
    )


def create_pert_analysis_card():
    """
    Create the PERT analysis card component.

    Returns:
        Dash Card component for PERT analysis
    """
    # Use the standardized card styling function
    from ui.styles import create_standardized_card, create_card_header_with_tooltip

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
    # Use the standardized card styling function
    from ui.styles import create_standardized_card, create_card_header_with_tooltip

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
                html.H5("Project Timeline", className="mb-3 border-bottom pb-2"),
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
                                    ]
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
                                    ]
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
                                        "always_visible": True,
                                    },
                                    className="my-3",  # Added margin top and bottom
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
                                    ]
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
            className="mb-4",
        ),
        # Project Scope Section - unchanged
        html.Div(
            [
                html.H5("Project Scope", className="mb-3 border-bottom pb-2"),
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
                                    ]
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
                                    ]
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
                                    ]
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
                                        "Remaining Total Points (calculated):",
                                        create_info_tooltip(
                                            "total-points",
                                            HELP_TEXTS["total_points"],
                                        ),
                                    ]
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
            className="mb-4",
        ),
        # Data Import Section
        html.Div(
            [
                html.H5("Data Import", className="mb-3 border-bottom pb-2"),
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
                                    ]
                                ),
                                dcc.Upload(
                                    id="upload-data",
                                    children=html.Div(
                                        [
                                            html.I(className="fas fa-file-upload mr-2"),
                                            "Drag and Drop or ",
                                            html.A("Select CSV File"),
                                        ]
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
                                    },
                                    multiple=False,
                                ),
                            ],
                            width=12,
                        ),
                    ],
                ),
            ],
        ),
    ]

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        className="mb-3 h-100",
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
    from dash import dash_table, html
    import dash_bootstrap_components as dbc
    from ui.components import create_export_buttons, create_info_tooltip, create_button
    from ui.styles import create_standardized_card, create_card_header_with_tooltip
    from ui.grid_templates import create_aligned_datatable, create_data_table

    # Create the card header with tooltip
    header_content = create_card_header_with_tooltip(
        "Statistics Data",
        tooltip_id="statistics-data",
        tooltip_text=HELP_TEXTS["statistics_table"],
    )

    # Convert to DataFrame for automatic column type detection
    statistics_df = pd.DataFrame(current_statistics)

    # Use automatic column alignment if we have data
    if not statistics_df.empty:
        # Create an automatically aligned table
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
                "id": "no_items",
                "type": "numeric",
            },
            {
                "name": "Points Completed",
                "id": "no_points",
                "type": "numeric",
            },
        ]

        # Set column alignments based on data type
        column_alignments = {
            "date": "center",
            "no_items": "right",
            "no_points": "right",
        }

        # Create the standardized table with manual alignments
        statistics_table = create_data_table(
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

    # Create the card body content
    body_content = [
        # Add help text at the top
        help_text,
        # Add space between help text and table (removed export buttons from top)
        html.Div(className="mb-3"),
        # Add the table with standardized styling
        statistics_table,
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
                    className="d-inline-block",
                ),
                # Button to clear filters
                create_button(
                    text="Clear Filters",
                    id="clear-filters-button",
                    variant="outline-secondary",
                    icon_class="fas fa-filter",
                    className="ms-2",
                ),
                # Export Statistics Button moved to this row
                html.Div(
                    [
                        create_button(
                            text="Export Statistics",
                            id="export-statistics-button",
                            variant="outline-secondary",
                            icon_class="fas fa-file-export",
                            className="ms-2",
                            tooltip="Export statistics data as CSV",
                        ),
                        html.Div(dcc.Download(id="export-statistics-download")),
                    ],
                    className="d-inline-block",
                ),
            ],
            className="d-flex justify-content-center mt-4",
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
            int(statistics_df["no_items"].sum()) if not statistics_df.empty else 0
        )
        completed_points = (
            int(statistics_df["no_points"].sum()) if not statistics_df.empty else 0
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

        # Check if percentages are similar (within 2% of each other)
        similar_percentages = abs(items_percentage - points_percentage) <= 2

        # Calculate average weekly velocity and coefficient of variation (last 10 weeks)
        # Create a copy of the DataFrame to avoid SettingWithCopyWarning
        recent_df = statistics_df.copy() if not statistics_df.empty else pd.DataFrame()

        # Convert to datetime to ensure proper week grouping
        if not recent_df.empty:
            # Use proper pandas assignment with .loc to avoid SettingWithCopyWarning
            recent_df.loc[:, "date"] = pd.to_datetime(recent_df["date"])
            recent_df.loc[:, "week"] = recent_df["date"].dt.isocalendar().week
            recent_df.loc[:, "year"] = recent_df["date"].dt.isocalendar().year

            # Use tail(10) after assigning week and year columns
            recent_df = recent_df.tail(10)

            weekly_data = (
                recent_df.groupby(["year", "week"])
                .agg({"no_items": "sum", "no_points": "sum"})
                .reset_index()
            )

            # Calculate metrics
            avg_weekly_items = weekly_data["no_items"].mean()
            avg_weekly_points = weekly_data["no_points"].mean()

            # Calculate coefficient of variation (CV = stdev / mean)
            std_weekly_items = weekly_data["no_items"].std()
            std_weekly_points = weekly_data["no_points"].std()

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

            # Calculate stability metrics (weeks with 0 or > 2x average)
            zero_item_weeks = len(weekly_data[weekly_data["no_items"] == 0])
            zero_point_weeks = len(weekly_data[weekly_data["no_points"] == 0])

            high_item_weeks = len(
                weekly_data[weekly_data["no_items"] > avg_weekly_items * 2]
            )
            high_point_weeks = len(
                weekly_data[weekly_data["no_points"] > avg_weekly_points * 2]
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
        else:
            # Default values if no data is available
            avg_weekly_items = 0
            avg_weekly_points = 0
            stability_status = "Unknown"
            stability_color = "secondary"
            stability_icon = "fa-question-circle"

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

        # Extract key metrics from settings (these represent remaining work)
        remaining_items = settings.get("total_items", 0)
        remaining_points = settings.get("total_points", 0)

        # Calculate completed items and points from statistics
        completed_items = (
            int(statistics_df["no_items"].sum()) if not statistics_df.empty else 0
        )
        completed_points = (
            int(statistics_df["no_points"].sum()) if not statistics_df.empty else 0
        )

        # Calculate values needed for the dashboard
        if not statistics_df.empty:
            # Add week and year columns
            recent_df = statistics_df.tail(10).copy()
            recent_df.loc[:, "week"] = recent_df["date"].dt.isocalendar().week
            recent_df.loc[:, "year"] = recent_df["date"].dt.isocalendar().year

            weekly_data = (
                recent_df.groupby(["year", "week"])
                .agg({"no_items": "sum", "no_points": "sum"})
                .reset_index()
            )

            # Calculate metrics needed for PERT table
            avg_weekly_items = weekly_data["no_items"].mean()
            avg_weekly_points = weekly_data["no_points"].mean()
            med_weekly_items = weekly_data["no_items"].median()
            med_weekly_points = weekly_data["no_points"].median()
        else:
            avg_weekly_items = 0
            avg_weekly_points = 0
            med_weekly_items = 0
            med_weekly_points = 0

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


def create_items_forecast_info_card():
    """
    Create a forecast information card specifically for the Items per Week tab.

    Returns:
        Dash Card component with items forecast explanation
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Items Forecast Information", className="d-inline"),
                    create_info_tooltip(
                        "items-forecast-info",
                        "Explanation of how to interpret the weekly items forecast.",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.P(
                                [
                                    html.Strong("Weekly Items Chart: "),
                                    "This chart shows your historical weekly completed items as blue bars and forecasts the next week's expected completion.",
                                ],
                                className="mb-2",
                            ),
                            html.P(
                                [
                                    html.Strong("Chart Components: "),
                                    "The chart includes several visual elements:",
                                ],
                                className="mb-1",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Blue Bars: "),
                                            html.Span(
                                                "Historical weekly completed items",
                                                style={
                                                    "color": COLOR_PALETTE["items"],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            ". These represent your actual completed work each week.",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Dark Blue Line: "),
                                            html.Span(
                                                "Weighted 4-week moving average",
                                                style={
                                                    "color": "#0047AB",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " that prioritizes recent performance (40% latest week, 30%, 20%, 10% for earlier weeks).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Patterned Bar: "),
                                            html.Span(
                                                "Next week forecast",
                                                style={
                                                    "color": COLOR_PALETTE["items"],
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " based on PERT estimation using your historical data.",
                                        ]
                                    ),
                                ],
                                className="mb-3",  # Increased spacing
                            ),
                            html.P(
                                [
                                    html.Strong("Forecast Methodology: "),
                                    "The next week forecast is calculated using PERT (Program Evaluation and Review Technique) methodology:",
                                ],
                                className="mb-1",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Most Likely: "),
                                            html.Span(
                                                "Average of all historical weekly items data",
                                                style={
                                                    "color": COLOR_PALETTE["items"],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            " (50% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Optimistic: "),
                                            html.Span(
                                                "Average of your best performing weeks",
                                                style={
                                                    "color": COLOR_PALETTE[
                                                        "optimistic"
                                                    ],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            " (highest item counts, 20% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Pessimistic: "),
                                            html.Span(
                                                "Average of your lowest performing weeks",
                                                style={
                                                    "color": COLOR_PALETTE[
                                                        "pessimistic"
                                                    ],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            " (excluding zero values, 80% confidence level).",
                                        ]
                                    ),
                                ],
                                className="mb-3",  # Increased spacing
                            ),
                            html.P(
                                [
                                    html.Strong("Interpreting the Forecast: "),
                                    "This forecast helps you predict how many items you're likely to complete next week based on your historical performance patterns. "
                                    "Use this to plan sprint capacities and adjust resource allocation.",
                                ],
                                className="mb-0",
                            ),
                        ],
                        style={"textAlign": "left"},
                    )
                ],
                className="py-4",  # Increased padding for better readability and more space from chart
            ),
        ],
        className="mt-5 mb-3 shadow-sm",  # Added top margin to create more space from the chart
    )


def create_points_forecast_info_card():
    """
    Create a forecast information card specifically for the Points per Week tab.

    Returns:
        Dash Card component with points forecast explanation
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Points Forecast Information", className="d-inline"),
                    create_info_tooltip(
                        "points-forecast-info",
                        "Explanation of how to interpret the weekly points forecast.",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.P(
                                [
                                    html.Strong("Weekly Points Chart: "),
                                    "This chart visualizes your historical weekly completed points as orange bars and provides a statistical forecast for next week.",
                                ],
                                className="mb-2",
                            ),
                            html.P(
                                [
                                    html.Strong("Chart Components: "),
                                    "The chart includes several visual elements:",
                                ],
                                className="mb-1",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Orange Bars: "),
                                            html.Span(
                                                "Historical weekly completed points",
                                                style={
                                                    "color": COLOR_PALETTE["points"],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            ". These represent your actual completed story points each week.",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Red Trend Line: "),
                                            html.Span(
                                                "Weighted 4-week moving average",
                                                style={
                                                    "color": "#FF6347",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " with exponential weighting (40% for most recent week, 30%, 20%, 10% for earlier weeks).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong(
                                                "Patterned Bar with Error Bars: "
                                            ),
                                            html.Span(
                                                "Next week forecast",
                                                style={
                                                    "color": COLOR_PALETTE["points"],
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " with confidence interval showing the range of likely outcomes.",
                                        ]
                                    ),
                                ],
                                className="mb-3",  # Increased spacing
                            ),
                            html.P(
                                [
                                    html.Strong(
                                        "Understanding the Confidence Interval: "
                                    ),
                                    "The forecast bar includes error bars representing a statistical confidence interval:",
                                ],
                                className="mb-1",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Upper Bound: "),
                                            html.Span(
                                                "25% of the difference between Most Likely and Optimistic estimates",
                                                style={
                                                    "color": COLOR_PALETTE[
                                                        "optimistic"
                                                    ],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            ".",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Lower Bound: "),
                                            html.Span(
                                                "25% of the difference between Most Likely and Pessimistic estimates",
                                                style={
                                                    "color": COLOR_PALETTE[
                                                        "pessimistic"
                                                    ],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            ".",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            "This gives you a reasonable range of expected performance for planning purposes."
                                        ]
                                    ),
                                ],
                                className="mb-3",  # Increased spacing
                            ),
                            html.P(
                                [
                                    html.Strong("Forecast Method: "),
                                    "The forecast uses historical data with different weights for three scenarios:",
                                ],
                                className="mb-1",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Most Likely: "),
                                            html.Span(
                                                "Average of all historical weekly points data",
                                                style={
                                                    "color": COLOR_PALETTE["points"],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            " (50% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Optimistic: "),
                                            html.Span(
                                                "Average of weeks with highest point completions",
                                                style={
                                                    "color": "rgb(184, 134, 11)",
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            " (20% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Pessimistic: "),
                                            html.Span(
                                                "Average of weeks with lowest non-zero point completions",
                                                style={
                                                    "color": "rgb(165, 42, 42)",
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            " (80% confidence level).",
                                        ]
                                    ),
                                ],
                                className="mb-3",  # Increased spacing
                            ),
                            html.P(
                                [
                                    html.Strong("Practical Use: "),
                                    "Use the points forecast to estimate sprint capacity and project velocity. "
                                    "Consider the confidence interval for risk assessment and establishing delivery commitments.",
                                ],
                                className="mb-0",
                            ),
                        ],
                        style={"textAlign": "left"},
                    )
                ],
                className="py-4",  # Increased padding for better readability and more space from chart
            ),
        ],
        className="mt-5 mb-3 shadow-sm",  # Added top margin to create more space from the chart
    )


def debug_pert_data(pert_data):
    """Simple utility to display pert_data contents for debugging"""
    import json
    from dash import html

    if pert_data is None:
        return html.Pre("pert_data is None")

    try:
        # Format as pretty JSON with indentation
        json_str = json.dumps(pert_data, indent=2, default=str)
        return html.Pre(json_str)
    except Exception as e:
        return html.Pre(f"Error serializing pert_data: {str(e)}")


def create_simple_pert_forecast_section(pert_data):
    """
    Create a simple PERT forecast section that directly displays the values.
    This is a simplified version that avoids complex conditional formatting.

    Args:
        pert_data: Dictionary containing PERT analysis data

    Returns:
        Dash component with PERT forecast information
    """
    import dash_bootstrap_components as dbc
    from dash import html
    from datetime import datetime, timedelta

    # Default values
    items_completion_str = "Unknown"
    points_completion_str = "Unknown"
    items_days = "Unknown"
    points_days = "Unknown"
    items_weeks = "Unknown"
    points_weeks = "Unknown"

    # Extract values if available
    if pert_data and isinstance(pert_data, dict):
        pert_time_items = pert_data.get("pert_time_items")
        pert_time_points = pert_data.get("pert_time_points")

        # Check if we have pre-formatted completion strings in pert_data
        items_completion_enhanced = pert_data.get("items_completion_enhanced")
        points_completion_enhanced = pert_data.get("points_completion_enhanced")

        if items_completion_enhanced is not None:
            # Use pre-formatted string directly
            items_completion_str_with_details = items_completion_enhanced
        elif pert_time_items is not None:
            # Format values if they exist but we don't have pre-formatted strings
            current_date = datetime.now()
            items_completion_date = current_date + timedelta(days=pert_time_items)
            items_completion_str = items_completion_date.strftime("%Y-%m-%d")
            items_days = f"{pert_time_items:.1f}"
            items_weeks = f"{pert_time_items / 7:.1f}"
            items_completion_str_with_details = (
                f"{items_completion_str} ({items_days} days, {items_weeks} weeks)"
            )
        else:
            items_completion_str_with_details = "Unknown"

        if points_completion_enhanced is not None:
            # Use pre-formatted string directly
            points_completion_str_with_details = points_completion_enhanced
        elif pert_time_points is not None:
            # Format values if they exist but we don't have pre-formatted strings
            current_date = datetime.now()
            points_completion_date = current_date + timedelta(days=pert_time_points)
            points_completion_str = points_completion_date.strftime("%Y-%m-%d")
            points_days = f"{pert_time_points:.1f}"
            points_weeks = f"{pert_time_points / 7:.1f}"
            points_completion_str_with_details = (
                f"{points_completion_str} ({points_days} days, {points_weeks} weeks)"
            )
        else:
            points_completion_str_with_details = "Unknown"

    return dbc.Card(
        [
            dbc.CardHeader("PERT Forecast"),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.P(
                                [
                                    html.Strong("Items completion (PERT): "),
                                    items_completion_str_with_details,
                                ]
                            ),
                            html.P(
                                [
                                    html.Strong("Points completion (PERT): "),
                                    points_completion_str_with_details,
                                ]
                            ),
                        ]
                    )
                ]
            ),
        ]
    )


def create_pert_forecast_display():
    """
    Create a simplified PERT forecast display with hardcoded values for testing.

    Returns:
        Dash component with PERT forecast information
    """
    import dash_bootstrap_components as dbc
    from dash import html

    return html.Div(
        [
            # Header with tooltip
            html.H5("PERT Forecast"),
            # Directly show hardcoded values for testing
            html.Div(
                [
                    html.P(
                        [
                            html.Strong("Items completion (PERT): "),
                            "2025-05-15 (55.5 days, 7.9 weeks)",
                        ]
                    ),
                    html.P(
                        [
                            html.Strong("Points completion (PERT): "),
                            "2025-05-20 (60.2 days, 8.6 weeks)",
                        ]
                    ),
                ],
                className="border p-2 rounded",
            ),
        ],
    )
