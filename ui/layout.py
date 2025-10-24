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
from configuration import __version__
from data import (
    calculate_total_points,
    load_app_settings,
    load_project_data,
    load_statistics,
)
from ui.button_utils import create_action_button
from ui.cards import (
    create_statistics_data_card,
)
from ui.components import create_parameter_panel
from ui.grid_utils import create_full_width_layout
from ui.tabs import create_tabs
from ui.jira_config_modal import create_jira_config_modal
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
    project_data = load_project_data()
    statistics, is_sample_data = load_statistics()

    # Load unified project scope data (includes JIRA calculated values)
    from data.persistence import get_project_scope

    project_scope = get_project_scope()

    # Merge app settings and project data for backward compatibility
    # Use project_scope values if available (from JIRA), otherwise fall back to project_data defaults
    settings = {**app_settings, **project_data}
    if project_scope:
        # Update with actual JIRA calculated scope values using correct field mappings
        settings.update(
            {
                "total_items": project_scope.get(
                    "remaining_items", project_data["total_items"]
                ),  # Remaining Total Items
                "total_points": project_scope.get(
                    "remaining_total_points", project_data["total_points"]
                ),  # Remaining Total Points (with extrapolation)
                "estimated_items": project_scope.get(
                    "estimated_items", project_data["estimated_items"]
                ),  # Remaining Estimated Items (non-null story points)
                "estimated_points": project_scope.get(
                    "estimated_points", project_data["estimated_points"]
                ),  # Remaining Estimated Points (sum of estimated)
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
    estimated_total_points, avg_points_per_item = calculate_total_points(
        settings["total_items"],
        settings["estimated_items"],
        settings["estimated_points"],
        statistics,
    )

    # Import help system components
    from ui.help_system import create_help_system_layout

    return dbc.Container(
        [
            # JIRA Configuration Modal (Feature 003-jira-config-separation)
            create_jira_config_modal(),
            # Query Management Modals
            create_save_query_modal(),
            create_delete_query_modal(),
            create_edit_query_modal(),
            # Help System (Phase 9.2 Progressive Disclosure)
            create_help_system_layout(),
            # Page initialization complete flag (hidden)
            dcc.Store(id="app-init-complete", data=False),
            # Persistent storage for the current data
            dcc.Store(id="current-settings", data=settings),
            dcc.Store(id="current-statistics", data=statistics),
            # Store for sample data flag
            dcc.Store(id="is-sample-data", data=is_sample_data),
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
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            html.Strong("Using Sample Data: "),
                            "You're currently viewing demo data. ",
                            "Upload your own data using the form below or add entries manually to start tracking your project.",
                            create_action_button(
                                "Dismiss",
                                variant="link",
                                size="sm",
                                id_suffix="sample-alert",
                                className="ms-3",
                            ),
                        ],
                        id="sample-data-alert",
                        color="info",
                        dismissable=False,
                        is_open=is_sample_data,
                        className="mb-3",
                    ),
                ],
                id="sample-data-banner",
            ),
            # Parameter Panel (User Story 1) - Sticky at top for app-like feel
            html.Div(
                create_parameter_panel(settings, is_open=False),
                className="param-panel-sticky",
            ),
            # Settings Panel - Collapsible panel for JIRA integration and import/export
            create_settings_panel(is_open=False),
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
            # Minimal footer with useful information
            html.Div(
                [
                    html.Hr(className="my-3"),
                    dbc.Row(
                        [
                            # Left column - app info
                            dbc.Col(
                                html.Small(
                                    [
                                        html.I(
                                            className="fas fa-chart-line me-2 text-muted"
                                        ),
                                        "Burndown Chart ",
                                        html.Span(
                                            f"v{__version__}", className="text-muted"
                                        ),
                                    ],
                                    className="text-secondary",
                                ),
                                width={"size": "auto"},
                            ),
                            # Center column - GitHub link only
                            dbc.Col(
                                html.Small(
                                    create_action_button(
                                        "GitHub",
                                        icon="code",
                                        variant="link",
                                        size="sm",
                                        id_suffix="footer",
                                        className="text-decoration-none px-2",
                                        href="https://github.com/niksavis/burndown-chart",
                                        target="_blank",
                                    ),
                                ),
                                className="text-center",
                                width=True,
                            ),
                            # Right column - Data info
                            dbc.Col(
                                html.Small(
                                    [
                                        f"Last updated: {datetime.now().strftime('%b %d, %Y')}",
                                    ],
                                    className="text-muted text-end",
                                ),
                                width={"size": "auto"},
                            ),
                        ],
                        className="d-flex justify-content-between align-items-center",
                    ),
                ],
                className="mt-4 mb-2",
            ),
        ],
        fluid=True,
        className="px-3 py-3",  # Add consistent container padding
    )
