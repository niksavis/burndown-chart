"""
UI Layout Module

This module provides the main application layout structure and serves
a fresh layout with the latest data from disk on each page load.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from datetime import datetime

# Third-party library imports
import dash_bootstrap_components as dbc
from dash import dcc, html

# Application imports
from configuration import __version__, logger
from data import (
    calculate_total_points,
    load_app_settings,
    load_statistics,
)
from ui.cards import (
    create_statistics_data_card,
)
from ui.components import (
    create_parameter_panel,
)
from ui.grid_utils import create_full_width_layout
from ui.tabs import create_tabs
from ui.jira_config_modal import create_jira_config_modal
from ui.query_creation_modal import create_query_creation_modal
from ui.field_mapping_modal import create_field_mapping_modal
from ui.settings_modal import (
    create_save_query_modal,
    create_delete_query_modal,
    create_edit_query_modal,
)
from ui.settings_panel import create_settings_panel

#######################################################################
# LAYOUT FUNCTION
#######################################################################


def serve_layout():
    """
    Create the application layout.

    Returns:
        Dash application layout with all components
    """
    # Load initial data using new separated functions
    app_settings = load_app_settings()
    statistics, is_sample_data = load_statistics()

    # Calculate initial parameter values based on selected time window
    # This ensures consistency between app load and slider interaction
    from data.persistence import get_project_scope
    import pandas as pd

    project_scope = get_project_scope()
    data_points_count = app_settings.get("data_points_count", 16)

    # Calculate remaining work at START of selected time window (same logic as slider callback)
    if project_scope and statistics and len(statistics) >= data_points_count:
        try:
            df = pd.DataFrame(statistics)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date", ascending=False)
            selected_data = df.head(data_points_count)

            # Calculate completed work in the selected window
            completed_in_window_items = selected_data["completed_items"].sum()
            completed_in_window_points = selected_data["completed_points"].sum()

            # Get current remaining work
            current_remaining_items = project_scope.get("remaining_items", 0)
            current_remaining_points = project_scope.get("remaining_total_points", 0)

            # Calculate remaining work at START of window
            remaining_items_at_start = (
                current_remaining_items + completed_in_window_items
            )
            remaining_points_at_start = (
                current_remaining_points + completed_in_window_points
            )

            # Calculate estimated items/points using ratio
            current_total_items = project_scope.get("total_items", 1)
            current_estimated_items = project_scope.get("estimated_items", 0)

            if current_total_items > 0:
                estimate_ratio = current_estimated_items / current_total_items
                estimated_items_at_start = int(
                    remaining_items_at_start * estimate_ratio
                )
            else:
                estimated_items_at_start = current_estimated_items

            # Calculate estimated points
            estimated_items_in_window = selected_data[
                selected_data["completed_points"] > 0
            ]["completed_items"].sum()
            estimated_points_in_window = selected_data["completed_points"].sum()

            if estimated_items_at_start > 0 and estimated_points_in_window > 0:
                avg_points = estimated_points_in_window / max(
                    estimated_items_in_window, 1
                )
                estimated_points_at_start = int(estimated_items_at_start * avg_points)
            else:
                estimated_points_at_start = project_scope.get("estimated_points", 0)

            # Set calculated values in settings
            settings = {**app_settings}
            settings.update(
                {
                    "total_items": int(remaining_items_at_start),
                    "total_points": remaining_points_at_start,
                    "estimated_items": estimated_items_at_start,
                    "estimated_points": estimated_points_at_start,
                }
            )
        except Exception as e:
            logger.error(f"Error calculating initial window values: {e}")
            # Fallback to current scope values
            settings = {**app_settings}
            if project_scope:
                settings.update(
                    {
                        "total_items": project_scope.get("remaining_items", 0),
                        "total_points": project_scope.get("remaining_total_points", 0),
                        "estimated_items": project_scope.get("estimated_items", 0),
                        "estimated_points": project_scope.get("estimated_points", 0),
                    }
                )
    else:
        # Fallback: use current scope values if calculation not possible
        settings = {**app_settings}
        if project_scope:
            settings.update(
                {
                    "total_items": project_scope.get("remaining_items", 0),
                    "total_points": project_scope.get("remaining_total_points", 0),
                    "estimated_items": project_scope.get("estimated_items", 0),
                    "estimated_points": project_scope.get("estimated_points", 0),
                }
            )

    app_layout = create_app_layout(settings, statistics, is_sample_data)
    return app_layout


def create_app_layout(settings, statistics, is_sample_data):
    """
    Serve a fresh layout with the latest data from disk.
    This is crucial for proper browser refresh behavior.

    Args:
        settings: Dictionary with application settings
        statistics: List of dictionaries with statistics data
        is_sample_data: Boolean indicating if the data is sample data

    Returns:
        Dash Container component with complete application layout
    """
    # Calculate total points based on estimated values (for initial display)
    # Use .get() with defaults since these values will be set by the initialization callback
    estimated_total_points, avg_points_per_item = calculate_total_points(
        settings.get("total_items", 0),
        settings.get("estimated_items", 0),
        settings.get("estimated_points", 0),
        statistics,
    )

    # Import help system components
    from ui.help_system import create_help_system_layout

    # Modern app container with updated styling matching DORA/Flow design
    return dbc.Container(
        [
            # JIRA Configuration Modal (Feature 003-jira-config-separation)
            create_jira_config_modal(),
            # Field Mapping Modal (Feature 007-dora-flow-metrics Phase 4)
            create_field_mapping_modal(),
            # Query Management Modals
            create_save_query_modal(),
            create_delete_query_modal(),
            create_edit_query_modal(),
            # Query Creation Modal (Feature 011-profile-workspace-switching Phase 4)
            create_query_creation_modal(),
            # Help System (Phase 9.2 Progressive Disclosure)
            create_help_system_layout(),
            # URL location for triggering page load callbacks
            dcc.Location(id="url", refresh=False),
            # Page initialization complete flag (hidden)
            dcc.Store(id="app-init-complete", data=False),
            # Persistent storage for the current data
            dcc.Store(id="current-settings", data=settings),
            dcc.Store(id="current-statistics", data=statistics),
            # Store for sample data flag
            dcc.Store(id="is-sample-data", data=is_sample_data),
            # Store for raw JIRA issues data (for DORA/Flow metrics calculations)
            dcc.Store(id="jira-issues-store", data=None),
            # Store for calculation results
            dcc.Store(
                id="calculation-results",
                data={
                    "total_points": estimated_total_points,
                    "avg_points_per_item": avg_points_per_item,
                },
            ),
            # Store for date range selection
            dcc.Store(id="date-range-weeks", data=None),
            # Store for client-side chart caching (performance optimization)
            dcc.Store(id="chart-cache", data={}),
            # Store for UI state (loading states, active tabs, etc.)
            dcc.Store(id="ui-state", data={"loading": False, "last_tab": None}),
            # Store for viewport size detection (mobile, tablet, desktop)
            dcc.Store(id="viewport-size", data="desktop"),
            # Store for triggering metrics refresh (DORA/Flow)
            dcc.Store(id="metrics-refresh-trigger", data=None),
            # Interval component for dynamic viewport detection
            dcc.Interval(
                id="viewport-detector",
                interval=1000,  # Check every second
                n_intervals=0,
                max_intervals=-1,  # Run indefinitely
            ),
            # Store for mobile navigation state
            dcc.Store(
                id="mobile-nav-state",
                data={
                    "drawer_open": False,
                    "active_tab": "tab-burndown",
                    "swipe_enabled": True,
                },
                storage_type="memory",  # Explicitly set storage type
            ),
            # Store for parameter panel state (User Story 1)
            dcc.Store(
                id="parameter-panel-state",
                data={"is_open": False, "user_preference": False},
                storage_type="local",  # Persist across sessions
            ),
            # Parameter & Settings Panels - Sticky at top for app-like feel
            # MUST be first visible element for sticky positioning to work
            html.Div(
                [
                    create_parameter_panel(
                        settings, is_open=False, statistics=statistics
                    ),
                    create_settings_panel(is_open=False),
                ],
                className="param-panel-sticky",
            ),
            # Add an empty div to hold the forecast-graph (will be populated by callback)
            html.Div(
                dcc.Graph(id="forecast-graph", style={"display": "none"}),
                id="forecast-graph-container",
            ),
            # Sample data notification banner (shown only when using sample data)
            # Positioned below the parameter panel
            html.Div(
                [
                    dbc.Alert(
                        html.Div(
                            [
                                html.I(className="fas fa-info-circle me-2"),
                                html.Span(
                                    [
                                        html.Strong("Using Sample Data"),
                                        html.Br(),
                                        html.Small(
                                            "You're currently viewing demo data. Upload your own data using the form below or add entries manually to start tracking your project.",
                                            style={"opacity": "0.85"},
                                        ),
                                    ]
                                ),
                            ],
                            className="d-flex align-items-start",
                        ),
                        id="sample-data-alert",
                        color="info",
                        dismissable=True,
                        is_open=is_sample_data,
                        className="mb-3",
                    ),
                ],
                id="sample-data-banner",
            ),
            # Tab Navigation and Charts Row - using full width template
            create_full_width_layout(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                # Tabbed interface
                                create_tabs(),
                            ]
                        ),
                    ],
                    className="shadow-sm",
                ),
                row_class="mb-4",
            ),
            # Statistics Data Table - using full width layout
            create_full_width_layout(
                create_statistics_data_card(statistics),
                row_class="mb-4",
            ),
            # Modern footer with clean design matching DORA/Flow style
            html.Div(
                [
                    html.Hr(className="my-4", style={"borderColor": "#dee2e6"}),
                    dbc.Row(
                        [
                            # Left column - app info
                            dbc.Col(
                                html.Small(
                                    [
                                        html.I(
                                            className="fas fa-chart-line me-2 text-primary"
                                        ),
                                        html.Span(
                                            "Burndown Chart ", className="fw-medium"
                                        ),
                                        html.Span(
                                            f"v{__version__}", className="text-muted"
                                        ),
                                    ],
                                    className="text-secondary",
                                ),
                                width={"size": "auto"},
                                className="d-flex align-items-center",
                            ),
                            # Center column - GitHub link
                            dbc.Col(
                                html.Small(
                                    html.A(
                                        [
                                            html.I(className="fab fa-github me-2"),
                                            "View on GitHub",
                                        ],
                                        href="https://github.com/niksavis/burndown-chart",
                                        target="_blank",
                                        className="text-decoration-none text-primary",
                                        style={"fontWeight": "500"},
                                    ),
                                ),
                                className="text-center",
                                width=True,
                            ),
                            # Right column - Last updated
                            dbc.Col(
                                html.Small(
                                    [
                                        html.I(
                                            className="fas fa-clock me-2 text-muted"
                                        ),
                                        f"Updated {datetime.now().strftime('%b %d, %Y')}",
                                    ],
                                    className="text-muted text-end",
                                ),
                                width={"size": "auto"},
                                className="d-flex align-items-center",
                            ),
                        ],
                        className="d-flex justify-content-between align-items-center g-3",
                    ),
                ],
                className="mt-5 mb-3",
                style={
                    "backgroundColor": "#f8f9fa",
                    "borderRadius": "8px",
                    "padding": "1rem 1.5rem",
                },
            ),
        ],
        fluid=True,
        className="px-3 pb-3",  # Remove top padding to allow sticky positioning
    )
