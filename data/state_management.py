"""
State Management Module

This module provides centralized state management functions for UI state containers.
Supports User Story 4: Unified Software Architecture with Clear Separation.

State Container Naming Conventions:
====================================

The application uses the following standardized dcc.Store components for state management:

1. **settings-store** (storage_type='local')
   - Purpose: User preferences and application settings
   - Persistence: Local storage (survives browser restart)
   - Usage: PERT factor, deadline, scope values, chart preferences
   - Access: Via load_app_settings() / save_app_settings()

2. **statistics-store** (storage_type='memory')
   - Purpose: Project statistics and historical data
   - Persistence: Session only (cleared on browser restart)
   - Usage: Weekly completion data, velocity metrics
   - Access: Via load_statistics() / save_statistics()

3. **ui-state-store** (storage_type='memory')
   - Purpose: Transient UI state (loading, errors, active elements)
   - Persistence: Session only
   - Usage: Loading spinners, error messages, modal states
   - Access: Direct callback updates

4. **nav-state-store** (storage_type='memory')
   - Purpose: Navigation and tab state
   - Persistence: Session only
   - Usage: Active tab, navigation history, mobile drawer state
   - Access: Via update_navigation_state()

5. **parameter-panel-state** (storage_type='local')
   - Purpose: Parameter panel collapse/expand state
   - Persistence: Local storage (user preference)
   - Usage: Panel open/closed state
   - Access: Direct callback updates

6. **mobile-nav-state** (storage_type='memory')
   - Purpose: Mobile navigation drawer state
   - Persistence: Session only
   - Usage: Drawer open/closed, swipe state
   - Access: Via mobile navigation callbacks

Usage Patterns:
===============

**Initializing State**:
```python
from data.state_management import initialize_navigation_state

nav_state = initialize_navigation_state(default_tab="tab-dashboard")
```

**Updating State**:
```python
from data.state_management import update_navigation_state

new_state = update_navigation_state(
    current_state=nav_state,
    new_tab="tab-burndown",
    add_to_history=True
)
```

**Validating State**:
```python
from data.state_management import validate_navigation_state

is_valid, errors = validate_navigation_state(nav_state)
if not is_valid:
    logger.error(f"Invalid navigation state: {errors}")
```

Architecture Guidelines:
========================

1. **Callbacks should NOT:**
   - Directly manipulate JSON structures
   - Implement complex state logic inline
   - Perform validation in callback body

2. **Callbacks SHOULD:**
   - Call state management functions
   - Pass state to/from dcc.Store
   - Handle UI updates only

3. **State Management Functions SHOULD:**
   - Validate all state updates
   - Return new state (immutable pattern)
   - Log state transitions
   - Be pure functions (no side effects)
"""

#######################################################################
# IMPORTS
#######################################################################
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


#######################################################################
# NAVIGATION STATE MANAGEMENT
#######################################################################


def initialize_navigation_state(default_tab: str = "tab-dashboard") -> Dict[str, Any]:
    """
    Initialize navigation state with default values.

    Args:
        default_tab: Default active tab ID

    Returns:
        dict: Initial navigation state

    Example:
        >>> nav_state = initialize_navigation_state()
        >>> nav_state['active_tab']
        'tab-dashboard'
    """
    return {
        "active_tab": default_tab,
        "tab_history": [default_tab],
        "last_updated": datetime.now().isoformat(),
    }


def update_navigation_state(
    current_state: Dict[str, Any],
    new_tab: str,
    add_to_history: bool = True,
) -> Dict[str, Any]:
    """
    Update navigation state with new active tab.

    This function follows data-model.md NavigationState specifications.

    Args:
        current_state: Current navigation state dict
        new_tab: New active tab ID
        add_to_history: Whether to add to navigation history

    Returns:
        dict: Updated navigation state

    Example:
        >>> state = initialize_navigation_state()
        >>> new_state = update_navigation_state(state, "tab-burndown")
        >>> new_state['active_tab']
        'tab-burndown'
    """
    # Create new state (immutable pattern)
    new_state = {
        **current_state,
        "active_tab": new_tab,
        "last_updated": datetime.now().isoformat(),
    }

    # Update history if requested
    if add_to_history:
        history = current_state.get("tab_history", []).copy()
        # Avoid duplicate consecutive entries
        if not history or history[-1] != new_tab:
            history.append(new_tab)
            # Limit history to last 10 tabs
            new_state["tab_history"] = history[-10:]

    logger.debug(
        f"Navigation state updated: {current_state.get('active_tab')} -> {new_tab}"
    )

    return new_state


def validate_navigation_state(state: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate navigation state structure and values.

    Args:
        state: Navigation state to validate

    Returns:
        tuple: (is_valid, list of error messages)

    Example:
        >>> state = {"active_tab": "tab-dashboard"}
        >>> is_valid, errors = validate_navigation_state(state)
        >>> is_valid
        True
    """
    errors = []

    # Check required fields
    if "active_tab" not in state:
        errors.append("Missing required field: active_tab")

    # Validate active_tab format
    if "active_tab" in state:
        active_tab = state["active_tab"]
        if not isinstance(active_tab, str):
            errors.append(f"active_tab must be string, got {type(active_tab)}")
        elif not active_tab.startswith("tab-"):
            errors.append(f"active_tab must start with 'tab-', got {active_tab}")

    # Validate tab_history if present
    if "tab_history" in state:
        history = state["tab_history"]
        if not isinstance(history, list):
            errors.append(f"tab_history must be list, got {type(history)}")

    return len(errors) == 0, errors


#######################################################################
# UI STATE MANAGEMENT
#######################################################################


def initialize_ui_state() -> Dict[str, Any]:
    """
    Initialize UI state with default values.

    Returns:
        dict: Initial UI state

    Example:
        >>> ui_state = initialize_ui_state()
        >>> ui_state['loading']
        False
    """
    return {
        "loading": False,
        "error": None,
        "last_action": None,
        "last_updated": datetime.now().isoformat(),
    }


def update_ui_state(
    current_state: Dict[str, Any],
    loading: Optional[bool] = None,
    error: Optional[str] = None,
    last_action: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update UI state with new values.

    Args:
        current_state: Current UI state dict
        loading: Optional loading state
        error: Optional error message
        last_action: Optional last action description

    Returns:
        dict: Updated UI state

    Example:
        >>> state = initialize_ui_state()
        >>> new_state = update_ui_state(state, loading=True)
        >>> new_state['loading']
        True
    """
    new_state = {
        **current_state,
        "last_updated": datetime.now().isoformat(),
    }

    if loading is not None:
        new_state["loading"] = loading

    if error is not None:
        new_state["error"] = error

    if last_action is not None:
        new_state["last_action"] = last_action

    return new_state


#######################################################################
# MOBILE NAVIGATION STATE MANAGEMENT
#######################################################################


def initialize_mobile_nav_state() -> Dict[str, Any]:
    """
    Initialize mobile navigation state with default values.

    Returns:
        dict: Initial mobile navigation state

    Example:
        >>> mobile_state = initialize_mobile_nav_state()
        >>> mobile_state['drawer_open']
        False
    """
    return {
        "drawer_open": False,
        "active_tab": "tab-dashboard",
        "swipe_enabled": True,
        "last_updated": datetime.now().isoformat(),
    }


def update_mobile_nav_state(
    current_state: Dict[str, Any],
    drawer_open: Optional[bool] = None,
    active_tab: Optional[str] = None,
    swipe_enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Update mobile navigation state.

    Args:
        current_state: Current mobile nav state dict
        drawer_open: Optional drawer open state
        active_tab: Optional active tab
        swipe_enabled: Optional swipe enabled state

    Returns:
        dict: Updated mobile nav state

    Example:
        >>> state = initialize_mobile_nav_state()
        >>> new_state = update_mobile_nav_state(state, drawer_open=True)
        >>> new_state['drawer_open']
        True
    """
    new_state = {
        **current_state,
        "last_updated": datetime.now().isoformat(),
    }

    if drawer_open is not None:
        new_state["drawer_open"] = drawer_open

    if active_tab is not None:
        new_state["active_tab"] = active_tab

    if swipe_enabled is not None:
        new_state["swipe_enabled"] = swipe_enabled

    return new_state


#######################################################################
# PARAMETER PANEL STATE MANAGEMENT
#######################################################################


def initialize_parameter_panel_state() -> Dict[str, Any]:
    """
    Initialize parameter panel state with default values.

    Returns:
        dict: Initial parameter panel state

    Example:
        >>> panel_state = initialize_parameter_panel_state()
        >>> panel_state['is_open']
        False
    """
    return {
        "is_open": False,
        "user_preference": False,  # Whether user manually toggled
        "last_updated": datetime.now().isoformat(),
    }


def update_parameter_panel_state(
    current_state: Dict[str, Any],
    is_open: Optional[bool] = None,
    user_preference: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Update parameter panel state.

    Args:
        current_state: Current panel state dict
        is_open: Optional open state
        user_preference: Optional user preference flag

    Returns:
        dict: Updated panel state

    Example:
        >>> state = initialize_parameter_panel_state()
        >>> new_state = update_parameter_panel_state(state, is_open=True, user_preference=True)
        >>> new_state['is_open']
        True
    """
    new_state = {
        **current_state,
        "last_updated": datetime.now().isoformat(),
    }

    if is_open is not None:
        new_state["is_open"] = is_open

    if user_preference is not None:
        new_state["user_preference"] = user_preference

    return new_state
