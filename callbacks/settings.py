"""
Settings Callbacks Module

This module provides unified access to all settings-related callbacks.
Core callbacks have been refactored into callbacks/settings/ package.
Remaining callbacks will be gradually migrated.
"""

# Import all from the refactored settings package
from callbacks.settings import register as register_core_settings

# Import remaining callback registration from legacy file
from callbacks.settings_remaining import register as register_remaining


def register(app):
    """
    Register all settings-related callbacks.

    This function combines:
    - Core settings callbacks (from callbacks/settings package)
    - Remaining callbacks (from settings_remaining.py, to be refactored)

    Args:
        app: Dash application instance
    """
    # Register core settings (refactored)
    register_core_settings(app)

    # Register remaining callbacks (to be refactored)
    register_remaining(app)
