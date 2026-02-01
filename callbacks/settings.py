"""
Settings Callbacks Module

This module provides unified access to all settings-related callbacks.
All callbacks have been successfully refactored into focused modules in the
callbacks/settings/ package following architectural guidelines (max 500 lines per file).

Package structure:
    - helpers.py: Shared utility functions (104 lines)
    - core_settings.py: Core settings management (338 lines, 5 callbacks)
    - data_update.py: JIRA data sync with threading (551 lines, 2 callbacks)
    - metrics.py: Automatic metrics calculation (256 lines, 1 callback)
    - jira_scope.py: Project scope calculation (235 lines, 1 callback)
    - query_profiles.py: JQL profile management (831 lines, 12 callbacks)
    - jql_test.py: JQL query testing (355 lines, 2 callbacks)
    - parameter_panel.py: Parameter panel UI (529 lines, 6 callbacks)

Total: 8 modules, 3,199 lines, 29 callbacks (reduced from original 3,126-line monolithic file)
"""

# Import all from the refactored settings package
from callbacks.settings import register as register_settings_package


def register(app):
    """
    Register all settings-related callbacks.

    This function delegates to the callbacks/settings package which contains
    all refactored callback modules organized by functionality.

    Args:
        app: Dash application instance
    """
    # Register all settings callbacks from the package
    register_settings_package(app)
