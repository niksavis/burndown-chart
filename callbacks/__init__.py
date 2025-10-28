"""
Callbacks module for the burndown chart application.

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

Callbacks must follow architecture guidelines (see specs/006-ux-ui-redesign/docs/architecture.md):

✅ ALLOWED in callbacks:
- Event handling and coordination
- Calling data layer functions
- Updating UI components
- State management via dcc.Store
- Error handling and user feedback

❌ FORBIDDEN in callbacks:
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

from callbacks import (
    bug_analysis,  # Bug analysis metrics callbacks (Feature 004)
    dashboard,  # Dashboard metrics and PERT timeline callbacks (Feature 006, User Story 2)
    dora_flow_metrics,  # DORA/Flow metrics callbacks (Feature 007, auto-registers via @callback)  # noqa: F401
    jira_config,  # JIRA config modal callbacks (auto-registers via @callback)  # noqa: F401
    jql_editor,  # JQL editor textarea-to-store sync
    mobile_navigation,  # Add mobile navigation callbacks
    settings_panel,  # Settings panel callbacks (auto-registers via @callback)  # noqa: F401
    # The 'export' module doesn't seem to exist and is causing an error
    # export,
    # scope_metrics,  # REMOVED: Orphaned callback with non-existent forecast-data-store
    settings,
    statistics,
    visualization,
)


def register_all_callbacks(app):
    """Register all callbacks for the application."""
    statistics.register(app)
    visualization.register(app)
    settings.register(app)
    # Remove this line since 'export' module doesn't exist
    # export.register(app)
    # REMOVED: scope_metrics.register(app) - orphaned callback causing scope tab bug
    # Scope metrics are now properly handled in visualization.py via _create_scope_tracking_tab_content
    mobile_navigation.register(app)  # Register mobile navigation callbacks
    jql_editor.register_jql_editor_callbacks(app)  # Register JQL editor sync
    bug_analysis.register(app)  # Register bug analysis callbacks (Feature 004)
    dashboard.register(app)  # Register dashboard callbacks (Feature 006, User Story 2)
    # Note: jira_config, settings_panel, and dora_flow_metrics callbacks auto-register via @callback decorator when imported
