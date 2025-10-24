"""
Callbacks module for the burndown chart application.
"""

from callbacks import (
    bug_analysis,  # Bug analysis metrics callbacks (Feature 004)
    dashboard,  # Dashboard metrics and PERT timeline callbacks (Feature 006, User Story 2)
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

# Auto-registration note: jira_config and settings_modal use @callback decorator
# and register automatically on import (no explicit register() call needed)


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
    # Note: jira_config and settings_panel callbacks auto-register via @callback decorator when imported
