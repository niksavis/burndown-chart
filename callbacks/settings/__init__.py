"""
Settings Callbacks Package

This package contains all settings-related callbacks, organized into focused modules:
- helpers: Utility functions
- core_settings: Core settings management
- data_update: Data update and JIRA integration (imported from main settings for now)
- query_profiles: JQL query profile management (imported from main settings for now)
- parameter_panel: Parameter panel UI (imported from main settings for now)

This module provides a single register() function that registers all callbacks.
"""

from . import core_settings


def register(app):
    """
    Register all settings-related callbacks.

    This function delegates to individual module register functions.

    Args:
        app: Dash application instance
    """
    # Register core settings callbacks
    core_settings.register(app)

    # TODO: After full refactoring, import and register other modules:
    # from . import data_update, query_profiles, parameter_panel
    # data_update.register(app)
    # query_profiles.register(app)
    # parameter_panel.register(app)
