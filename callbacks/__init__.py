"""
Callbacks module for the Burndown application.

Callback Registration Patterns
================================

This module provides centralized callback registration for the Dash application.
Two registration patterns are used depending on the callback module structure:

Pattern 1: Explicit registration via register(app) function
------------------------------------------------------------
Used for callback modules that define a register(app) function.
These modules typically contain multiple callbacks that need explicit registration.

Example:
    def register(app):
        @app.callback(Output(...), Input(...))
        def my_callback(...):
            pass

Modules using Pattern 1:
- statistics.py: register(app) - Statistics table and data callbacks
- visualization.py: register(app) - Chart rendering and tab callbacks
- settings.py: register(app) - Parameter panel and settings callbacks
- mobile_navigation.py: register(app) - Mobile navigation callbacks
- jql_editor.py: register_jql_editor_callbacks(app) - JQL editor sync
- bug_analysis.py: register(app) - Bug analysis metrics callbacks
- dashboard.py: register(app) - Dashboard metrics and PERT timeline

Pattern 2: Auto-registration via @callback decorator
----------------------------------------------------
Used for callback modules that use the @callback decorator directly.
These callbacks register automatically when the module is imported.

Example:
    from dash import callback, Output, Input

    @callback(Output(...), Input(...))
    def my_callback(...):
        pass

Modules using Pattern 2:
- jira_config.py: @callback - JIRA config modal callbacks
- settings_panel.py: @callback - Settings panel callbacks

Migration Guidelines
====================

When creating new callback modules:

1. **Use Pattern 2 (@callback decorator)** for new code:
   - Simpler and more Pythonic
   - Automatic registration on import
   - Recommended by Dash documentation

2. **Use Pattern 1 (register function)** only when:
   - Maintaining consistency with existing modules
   - Need conditional callback registration
   - Complex initialization logic required

3. **Avoid mixing patterns** within a single module

Layer Boundaries
================

Callbacks follow architecture guidelines
(see specs/006-ux-ui-redesign/docs/architecture.md):

[OK] ALLOWED in callbacks:
- Event handling and coordination
- Calling data layer functions
- Updating UI components
- State management via dcc.Store
- Error handling and user feedback

[X] FORBIDDEN in callbacks:
- Business logic implementation (use data/ layer)
- File I/O operations (use data.persistence)
- Complex calculations (use data.processing)
- Direct JSON manipulation (use state_management)
- External API calls (use data.jira_*)

Example - Correct callback pattern:
    from dash import callback, Output, Input
    from data.persistence import load_app_settings, save_app_settings

    @callback(
        Output("settings-store", "data"),
        Input("save-button", "n_clicks"),
        State("pert-input", "value")
    )
    def save_settings(n_clicks, pert_factor):
        if n_clicks is None:
            return dash.no_update

        # Delegate to data layer - no business logic here
        new_settings = save_app_settings({"pert_factor": pert_factor})
        return new_settings
"""

# Import feature flag to determine which UI is active
from callbacks import (
    about_dialog,  # noqa: F401
    active_work_timeline,
    ai_prompt_generation,  # noqa: F401
    app_update,  # noqa: F401
    banner_status_icons,  # noqa: F401
    budget_settings,  # noqa: F401
    bug_analysis,
    # dashboard,  # Removed dead code (ui/dashboard.py not imported)
    dora_flow_metric_details,  # noqa: F401
    dora_flow_metrics,  # noqa: F401
    field_mapping,  # noqa: F401
    field_value_fetch,  # noqa: F401
    flow_metrics_callbacks,  # noqa: F401
    import_export,  # noqa: F401
    integrated_query_management,  # noqa: F401
    jira_config,  # noqa: F401
    jira_data_store,  # noqa: F401
    jira_metadata,  # noqa: F401
    jql_editor,
    metrics_refresh_callbacks,  # noqa: F401
    migration,  # noqa: F401
    mobile_navigation,
    namespace_autocomplete,  # noqa: F401
    profile_management,  # noqa: F401
    progress_bar,  # noqa: F401
    query_management,  # noqa: F401
    query_switching,  # noqa: F401
    report_generation,  # noqa: F401
    # export module does not exist
    # export,
    # scope_metrics,  # Removed orphan callback (no forecast-data-store)
    settings,
    sprint_filters,  # noqa: F401
    sprint_selector,  # noqa: F401
    sprint_tracker,  # noqa: F401
    statistics,
    version_update_notification,  # noqa: F401
    visualization,
)
from ui.layout import USE_ACCORDION_SETTINGS

# Conditionally import settings UI callbacks based on feature flag
if USE_ACCORDION_SETTINGS:
    from callbacks import accordion_settings  # noqa: F401
else:
    from callbacks import tabbed_settings  # noqa: F401

# Always import settings_panel for flyout toggle functionality
# (needed for both accordion and legacy UI to open the Settings flyout)
from callbacks import settings_panel  # noqa: F401


def register_all_callbacks(app):
    """Register all callbacks for the application."""
    statistics.register(app)
    visualization.register(app)
    active_work_timeline.register(app)

    # Always register settings callbacks (needed for Parameters panel toggle)
    settings.register(app)

    # Register clientside callbacks for panel button active states
    settings_panel.register_clientside_callbacks(app)

    # Remove this line since 'export' module doesn't exist
    # export.register(app)
    # scope_metrics.register(app) removed (orphan callback)
    # Scope metrics now handled in visualization.py
    mobile_navigation.register(app)  # Register mobile navigation callbacks
    jql_editor.register_jql_editor_callbacks(app)  # Register JQL editor sync
    bug_analysis.register(app)  # Register bug analysis callbacks (Feature 004)
    # dashboard.register(app) removed (dead code)
    # Some callbacks auto-register via @callback on import.
