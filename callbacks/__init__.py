"""
Callbacks Package

This package contains all callback functions organized by functionality.
"""

# Import all callbacks so they can be imported from the callbacks package
from callbacks.settings import register as register_settings_callbacks
from callbacks.statistics import register as register_statistics_callbacks
from callbacks.visualization import register as register_visualization_callbacks
from callbacks.error_examples import register as register_error_examples_callbacks


def register_all_callbacks(app):
    """
    Register all callbacks with the application.

    Args:
        app: Dash application instance
    """
    register_settings_callbacks(app)
    register_statistics_callbacks(app)
    register_visualization_callbacks(app)
    register_error_examples_callbacks(app)
