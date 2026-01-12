"""
UI Layout Module

This module provides the main application layout structure and serves
a fresh layout with the latest data from disk on each page load.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import logging
from datetime import datetime

# Third-party library imports
import dash_bootstrap_components as dbc
from dash import dcc, html

# Application imports
# Application imports
from configuration import __version__
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

# Integrated query management modals (Feature 011 - replaces legacy settings_modal query functions)
from ui.save_query_modal import create_save_query_modal
from ui.unsaved_changes_modal import create_unsaved_changes_modal
from ui.delete_query_modal import create_delete_query_modal
from ui.improved_settings_panel import create_improved_settings_panel
from ui.import_export_panel import create_import_export_flyout

# Initialize logger
logger = logging.getLogger(__name__)

# Feature flag for new accordion-based settings panel (Feature 011)
USE_ACCORDION_SETTINGS = False  # Set to True to use accordion UI, False for tabbed UI

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

    # DEBUG: Log the show_points value being loaded
    logger.info(
        f"[LAYOUT DEBUG] show_points loaded from settings: {app_settings.get('show_points', 'NOT_FOUND')}"
    )

    statistics, is_sample_data = load_statistics()

    # Get project scope and use actual remaining values (no window calculations)
    from data.persistence import get_project_scope

    project_scope = get_project_scope()

    # Use actual remaining values from project scope (no window calculations)
    settings = {**app_settings}
    if project_scope:
        # Get field stats from calculation metadata
        metadata = project_scope.get("calculation_metadata", {})
        field_stats = metadata.get("field_stats", {})

        settings.update(
            {
                "total_items": project_scope.get("remaining_items", 0),
                "total_points": project_scope.get("remaining_total_points", 0),
                "estimated_items": project_scope.get("estimated_items", 0),
                "estimated_points": project_scope.get("estimated_points", 0),
                "field_stats": field_stats,  # Add field stats for points coverage tooltip
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

    # Import app module for version check (late import to avoid circular dependency)
    import app

    # Store version check result for callback access (not rendered in initial layout)
    # Toast will be shown via callback to avoid being cleared by page load callbacks
    version_update_available = hasattr(
        app, "VERSION_CHECK_RESULT"
    ) and app.VERSION_CHECK_RESULT.get("update_available", False)

    if version_update_available:
        version_info = {
            "current": app.VERSION_CHECK_RESULT.get("current_commit", "unknown"),
            "latest": app.VERSION_CHECK_RESULT.get("latest_commit", "unknown"),
        }
    else:
        version_info = None

    # Modern app container with updated styling matching DORA/Flow design
    return dbc.Container(
        [
            # Toast notification container for all app notifications
            # (profile switching, version updates, migration, etc.)
            html.Div(
                id="app-notifications",
                style={
                    "position": "fixed",
                    "top": "10px",
                    "right": "10px",
                    "zIndex": "9999",
                    "width": "320px",
                },
            ),
            # Store version info for callback to display toast after page loads
            dcc.Store(id="version-check-info", data=version_info),
            # Track if update toast has been shown this session (prevents showing on every page refresh)
            dcc.Store(id="update-toast-shown", storage_type="session", data=False),
            # Migration status tracking (prevents re-running migration)
            dcc.Store(id="migration-status", storage_type="session", data=None),
            # JIRA Configuration Modal (Feature 003-jira-config-separation)
            create_jira_config_modal(),
            # Field Mapping Modal (Feature 007-dora-flow-metrics Phase 4)
            create_field_mapping_modal(),
            # Integrated Query Management Modals (Feature 011)
            create_save_query_modal(),
            create_unsaved_changes_modal(),
            create_delete_query_modal(),
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
            # App-level JIRA metadata store (fetched once on startup, refreshed on config change)
            # This store is used by field mapping modal and namespace autocomplete
            dcc.Store(id="jira-metadata-store", data=None),
            # Track JIRA config version to detect changes and trigger metadata refresh
            dcc.Store(id="jira-config-hash", data=None),
            # Trigger for metadata refresh when JIRA config is saved
            dcc.Store(id="jira-config-save-trigger", data=0),
            # Trigger metrics calculation after data fetch completes
            dcc.Store(id="trigger-auto-metrics-calc", data=None),
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
                    # Settings panel - always use improved panel, which now contains accordion
                    create_improved_settings_panel(),
                    # Import/Export flyout panel - separate from Settings (pure data operations)
                    create_import_export_flyout(),
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
            # Compact footer with clean design
            html.Div(
                [
                    html.Hr(
                        className="my-2",
                        style={"borderColor": "#dee2e6", "margin": "0.5rem 0"},
                    ),
                    dbc.Row(
                        [
                            # Left column - app version
                            dbc.Col(
                                html.Small(
                                    [
                                        html.I(
                                            className="fas fa-chart-line me-1 text-primary",
                                            style={"fontSize": "0.8rem"},
                                        ),
                                        html.Span(
                                            f"v{__version__}",
                                            className="fw-medium text-secondary",
                                        ),
                                    ],
                                    style={"fontSize": "0.8rem"},
                                ),
                                xs=12,
                                sm=4,
                                className="d-flex align-items-center justify-content-center justify-content-sm-start mb-1 mb-sm-0",
                            ),
                            # Center column - GitHub link
                            dbc.Col(
                                html.A(
                                    [
                                        html.I(
                                            className="fab fa-github me-1",
                                            style={"fontSize": "0.85rem"},
                                        ),
                                        "GitHub",
                                    ],
                                    href="https://github.com/niksavis/burndown-chart",
                                    target="_blank",
                                    className="text-decoration-none text-primary fw-medium",
                                    style={"fontSize": "0.85rem"},
                                ),
                                xs=12,
                                sm=4,
                                className="d-flex align-items-center justify-content-center mb-1 mb-sm-0",
                            ),
                            # Right column - Last updated
                            dbc.Col(
                                html.Small(
                                    [
                                        html.I(
                                            className="fas fa-clock me-1 text-muted",
                                            style={"fontSize": "0.75rem"},
                                        ),
                                        f"{datetime.now().strftime('%b %d, %Y')}",
                                    ],
                                    className="text-muted",
                                    style={"fontSize": "0.75rem"},
                                ),
                                xs=12,
                                sm=4,
                                className="d-flex align-items-center justify-content-center justify-content-sm-end",
                            ),
                        ],
                        className="g-1",
                    ),
                    # Update available banner (compact, below main row)
                    (
                        html.Div(
                            html.Span(
                                [
                                    html.I(
                                        className="fas fa-sync-alt me-1",
                                        style={"fontSize": "0.7rem"},
                                    ),
                                    "Update: ",
                                    html.Span(
                                        # Show tags when available, fall back to commit hashes for missing tags
                                        f"{app.VERSION_CHECK_RESULT.get('current_tag') or app.VERSION_CHECK_RESULT.get('current_commit', 'unknown')[:7]} → "
                                        f"{app.VERSION_CHECK_RESULT.get('latest_tag') or app.VERSION_CHECK_RESULT.get('latest_commit', 'unknown')[:7]}",
                                        className="opacity-75",
                                        style={"fontSize": "0.7rem"},
                                    ),
                                ],
                                id="footer-update-indicator",
                                n_clicks=0,
                                className="d-inline-block",
                                style={
                                    "cursor": "pointer",
                                    "userSelect": "none",
                                    "color": "#198754",
                                    "fontWeight": "500",
                                    "fontSize": "0.75rem",
                                },
                            ),
                            className="mt-1 text-center",
                            style={"lineHeight": "1.2"},
                        )
                        if hasattr(app, "VERSION_CHECK_RESULT")
                        and app.VERSION_CHECK_RESULT.get("update_available", False)
                        else None
                    ),
                ],
                className="mt-2 mb-1 py-1",
                style={
                    "backgroundColor": "#f8f9fa",
                    "borderRadius": "4px",
                    "padding": "0.35rem 0.75rem",
                },
            ),
        ],
        fluid=True,
        className="px-3 pb-3",  # Remove top padding to allow sticky positioning
    )
