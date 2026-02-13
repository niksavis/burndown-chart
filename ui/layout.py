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
from configuration import __version__
from data import calculate_total_points
from data.persistence import (
    load_app_settings,
    load_statistics,
    get_project_scope,
)
from ui import (
    create_parameter_panel,
)
from ui.grid_utils import create_full_width_layout
from ui.tabs import create_desktop_tabs_only
from ui.mobile_navigation import create_mobile_navigation_system
from ui.jira_config_modal import create_jira_config_modal
from ui.query_creation_modal import create_query_creation_modal
from ui.field_mapping_modal import create_field_mapping_modal

# Integrated query management modals (Feature 011 - replaces legacy settings_modal query functions)
from ui.save_query_modal import create_save_query_modal
from ui.unsaved_changes_modal import create_unsaved_changes_modal
from ui.delete_query_modal import create_delete_query_modal
from ui.improved_settings_panel import create_improved_settings_panel
from ui.import_export_panel import create_import_export_flyout
from ui.about_dialog import create_about_dialog

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
    project_scope = get_project_scope()

    # Use actual remaining values from project scope (no window calculations)
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

    # Import app module for version check (late import to avoid circular dependency)
    import app

    # Store version check result for callback access (not rendered in initial layout)
    # Toast will be shown via callback to avoid being cleared by page load callbacks
    version_update_available = (
        hasattr(app, "VERSION_CHECK_RESULT")
        and isinstance(app.VERSION_CHECK_RESULT, dict)
        and app.VERSION_CHECK_RESULT.get("update_available", False)
    )

    if version_update_available and isinstance(app.VERSION_CHECK_RESULT, dict):
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
                    "top": "5px",
                    "right": "-132px",
                    "zIndex": "9999",
                    "width": "520px",
                },
            ),
            # Store version info for callback to display toast after page loads
            dcc.Store(id="version-check-info", data=version_info),
            # Track if update toast has been shown this session (prevents showing on every page refresh)
            dcc.Store(id="update-toast-shown", storage_type="session", data=False),
            # Update status store for tracking download/install progress
            dcc.Store(id="update-status-store", data=None),
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
            # About Dialog (Feature 016 - Standalone Packaging)
            create_about_dialog(),
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
            # Interval for download progress polling
            dcc.Interval(
                id="download-progress-poll",
                interval=1000,  # Poll every second
                n_intervals=0,
                disabled=True,  # Initially disabled, enabled when download starts
            ),
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
                    # Desktop tabs - integrated as part of sticky panel
                    create_desktop_tabs_only(),
                ],
                className="param-panel-sticky",
            ),
            # Backdrop overlay to dim content when panels are expanded
            html.Div(id="panel-backdrop", className="panel-backdrop"),
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
                                html.I(className="fas fa-info-circle me-2 text-info"),
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
            # Mobile navigation system - must be outside card for proper fixed positioning
            create_mobile_navigation_system(),
            # Tab content container - wrapped in card for styling
            create_full_width_layout(
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                # Content div that will be filled based on active tab
                                html.Div(id="tab-content"),
                            ]
                        ),
                    ],
                    className="shadow-sm",
                ),
                row_class="mb-4",
            ),
            # Compact footer with clean design
            html.Div(
                [
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
                                            id="footer-version-text",
                                            className="fw-medium text-secondary",
                                        ),
                                    ],
                                    style={"fontSize": "0.8rem"},
                                ),
                                xs=12,
                                sm=4,
                                className="d-flex align-items-center justify-content-center justify-content-sm-start mb-1 mb-sm-0",
                            ),
                            # Center column - GitHub and About links
                            dbc.Col(
                                html.Div(
                                    [
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
                                            className="text-decoration-none text-primary fw-medium me-3",
                                            style={
                                                "fontSize": "0.85rem",
                                                "transition": "opacity 0.2s",
                                            },
                                        ),
                                        html.A(
                                            [
                                                html.I(
                                                    className="fas fa-question-circle me-1",
                                                    style={"fontSize": "0.85rem"},
                                                ),
                                                "About",
                                            ],
                                            id="about-button",
                                            href="#",
                                            className="text-decoration-none text-primary fw-medium",
                                            style={
                                                "fontSize": "0.85rem",
                                                "transition": "opacity 0.2s",
                                            },
                                        ),
                                    ],
                                    className="d-flex align-items-center justify-content-center",
                                ),
                                xs=12,
                                sm=4,
                                className="mb-1 mb-sm-0",
                            ),
                            # Right column - Last updated
                            dbc.Col(
                                html.Small(
                                    [
                                        html.I(
                                            className="fas fa-clock me-1",
                                            style={"fontSize": "0.8rem"},
                                        ),
                                        f"{datetime.now().strftime('%b %d, %Y')}",
                                    ],
                                    className="text-muted",
                                    style={"fontSize": "0.8rem"},
                                ),
                                xs=12,
                                sm=4,
                                className="d-flex align-items-center justify-content-center justify-content-sm-end",
                            ),
                        ],
                        className="g-1",
                    ),
                    # Update available banner (compact, below main row)
                    html.Div(
                        id="footer-update-container",
                        children=(
                            html.Div(
                                html.Button(
                                    [
                                        html.I(
                                            className="fas fa-sync-alt me-1"
                                            if app.VERSION_CHECK_RESULT.state
                                            != app.VERSION_CHECK_RESULT.state.__class__.READY
                                            else "fas fa-check-circle me-1",
                                            style={"fontSize": "0.7rem"},
                                        ),
                                        (
                                            f"Update Available: {app.VERSION_CHECK_RESULT.current_version} → {app.VERSION_CHECK_RESULT.available_version}"
                                            if app.VERSION_CHECK_RESULT.state
                                            == app.VERSION_CHECK_RESULT.state.__class__.AVAILABLE
                                            else (
                                                "Update Ready - Click to Install"
                                                if app.VERSION_CHECK_RESULT.state
                                                == app.VERSION_CHECK_RESULT.state.__class__.READY
                                                else f"Manual Update Available: {app.VERSION_CHECK_RESULT.current_version} → {app.VERSION_CHECK_RESULT.available_version}"
                                            )
                                        ),
                                    ],
                                    id="footer-update-indicator",
                                    n_clicks=0,
                                    className="btn btn-link p-0 border-0",
                                    style={
                                        "color": "#198754",
                                        "fontWeight": "500",
                                        "fontSize": "0.75rem",
                                        "textDecoration": "none",
                                    },
                                ),
                                className="mt-1 text-center",
                                style={"lineHeight": "1.2"},
                            )
                            if hasattr(app, "VERSION_CHECK_RESULT")
                            and app.VERSION_CHECK_RESULT is not None
                            and hasattr(app.VERSION_CHECK_RESULT, "state")
                            and app.VERSION_CHECK_RESULT.state
                            in [
                                app.VERSION_CHECK_RESULT.state.__class__.AVAILABLE,
                                app.VERSION_CHECK_RESULT.state.__class__.MANUAL_UPDATE_REQUIRED,
                                app.VERSION_CHECK_RESULT.state.__class__.READY,
                            ]
                            else None
                        ),
                    ),
                ],
                className="mt-2 mb-1 py-2",
                style={
                    "backgroundColor": "#f8f9fa",
                    "borderTop": "1px solid #dee2e6",
                    "borderRadius": "4px",
                    "padding": "0.5rem 0.75rem",
                },
            ),
        ],
        fluid=True,
        className="px-3 pb-3",  # Remove top padding to allow sticky positioning
    )
