"""Data persistence adapters - Parameter panel state management."""

# Standard library imports
import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Third-party library imports
import pandas as pd

# Application imports
from configuration.settings import logger

def load_parameter_panel_state() -> dict:
    """
    Load parameter panel state from app settings.

    This function supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
    The parameter panel state is stored in localStorage via dcc.Store on the client side,
    but this function provides a server-side default state for initialization.

    Returns:
        dict: Parameter panel state with keys:
            - is_open (bool): Whether panel is expanded
            - last_updated (str): ISO 8601 timestamp
            - user_preference (bool): Whether state was manually set by user

    Example:
        >>> state = load_parameter_panel_state()
        >>> print(state['is_open'])
        False
    """
    from data.schema import get_default_parameter_panel_state

    try:
        app_settings = load_app_settings()

        # Check if parameter_panel_state exists in settings
        if "parameter_panel_state" in app_settings:
            panel_state = app_settings["parameter_panel_state"]

            # Validate required fields
            if isinstance(panel_state, dict) and "is_open" in panel_state:
                return panel_state

        # Return default state if not found or invalid
        return dict(get_default_parameter_panel_state())

    except Exception as e:
        logger.warning(f"[Config] Error loading parameter panel state: {e}")
        return dict(get_default_parameter_panel_state())


def save_parameter_panel_state(is_open: bool, user_preference: bool = True) -> bool:
    """
    Save parameter panel state to app settings.

    This function supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
    The parameter panel state is primarily managed client-side via dcc.Store,
    but this function persists the state to profile.json for session continuity.

    Args:
        is_open: Whether the parameter panel should be expanded
        user_preference: Whether this state was explicitly set by the user (vs. default)

    Returns:
        bool: True if save successful, False otherwise

    Example:
        >>> save_parameter_panel_state(is_open=True, user_preference=True)
        True
    """
    try:
        # Create parameter panel state dict
        panel_state = {
            "is_open": bool(is_open),
            "last_updated": datetime.now().isoformat(),
            "user_preference": bool(user_preference),
        }

        # Update app settings via backend
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Store panel state in app_state table (UI preference) as JSON string
        import json

        backend.set_app_state("parameter_panel_state", json.dumps(panel_state))

        logger.debug(
            f"[Config] Parameter panel state saved to database: is_open={is_open}"
        )
        return True

    except Exception as e:
        logger.error(f"[Config] Error saving parameter panel state: {e}")
        return False
