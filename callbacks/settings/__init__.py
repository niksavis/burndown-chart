"""
Settings Callbacks Package

This package contains all settings-related callbacks, organized into focused modules:
- helpers: Utility functions
- core_settings: Core settings management
- data_update: Data update and JIRA integration
- metrics: Automatic DORA/Flow metrics calculation
- jira_scope: Project scope calculation from JIRA
- query_profiles: JQL query profile management (CRUD operations)
- parameter_panel: Parameter panel UI (imported from main settings for now)

This module provides a single register() function that registers all callbacks.
"""

from . import core_settings, data_update, jira_scope, metrics, query_profiles


def register(app):
    """
    Register all settings-related callbacks.

    This function delegates to individual module register functions.

    Args:
        app: Dash application instance
    """
    # Register core settings callbacks
    core_settings.register(app)

    # Register data update callbacks
    data_update.register(app)

    # Register metrics calculation callbacks
    metrics.register(app)

    # Register JIRA scope calculation callback
    jira_scope.register(app)

    # Register JQL query profile management callbacks
    query_profiles.register(app)

    # TODO: After full refactoring, import and register other modules:
    # from . import parameter_panel
    # parameter_panel.register(app)
