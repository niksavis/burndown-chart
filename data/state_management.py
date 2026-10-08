import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def initialize_navigation_state(default_tab: str = "tab-dashboard") -> dict[str, Any]:

    return {
        "active_tab": default_tab,
        "tab_history": [default_tab],
        "last_updated": datetime.now().isoformat(),
    }


def update_navigation_state(
    current_state: dict[str, Any],
    new_tab: str,
    add_to_history: bool = True,
) -> dict[str, Any]:

    new_state = {
        **current_state,
        "active_tab": new_tab,
        "last_updated": datetime.now().isoformat(),
    }

    if add_to_history:
        history = current_state.get("tab_history", []).copy()
        if not history or history[-1] != new_tab:
            history.append(new_tab)
            new_state["tab_history"] = history[-10:]

    logger.debug(
        f"Navigation state updated: {current_state.get('active_tab')} -> {new_tab}"
    )

    return new_state


def validate_navigation_state(state: dict[str, Any]) -> tuple[bool, list[str]]:

    errors = []

    if "active_tab" not in state:
        errors.append("Missing required field: active_tab")

    if "active_tab" in state:
        active_tab = state["active_tab"]
        if not isinstance(active_tab, str):
            errors.append(f"active_tab must be string, got {type(active_tab)}")
        elif not active_tab.startswith("tab-"):
            errors.append(f"active_tab must start with 'tab-', got {active_tab}")

    if "tab_history" in state:
        history = state["tab_history"]
        if not isinstance(history, list):
            errors.append(f"tab_history must be list, got {type(history)}")

    return len(errors) == 0, errors


def initialize_ui_state() -> dict[str, Any]:

    return {
        "loading": False,
        "error": None,
        "last_action": None,
        "last_updated": datetime.now().isoformat(),
    }


def update_ui_state(
    current_state: dict[str, Any],
    loading: bool | None = None,
    error: str | None = None,
    last_action: str | None = None,
) -> dict[str, Any]:

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


def initialize_mobile_nav_state() -> dict[str, Any]:

    return {
        "drawer_open": False,
        "active_tab": "tab-dashboard",
        "swipe_enabled": True,
        "last_updated": datetime.now().isoformat(),
    }


def update_mobile_nav_state(
    current_state: dict[str, Any],
    drawer_open: bool | None = None,
    active_tab: str | None = None,
    swipe_enabled: bool | None = None,
) -> dict[str, Any]:

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


def initialize_parameter_panel_state() -> dict[str, Any]:

    return {
        "is_open": False,
        "user_preference": False,
        "last_updated": datetime.now().isoformat(),
    }


def update_parameter_panel_state(
    current_state: dict[str, Any],
    is_open: bool | None = None,
    user_preference: bool | None = None,
) -> dict[str, Any]:

    new_state = {
        **current_state,
        "last_updated": datetime.now().isoformat(),
    }

    if is_open is not None:
        new_state["is_open"] = is_open

    if user_preference is not None:
        new_state["user_preference"] = user_preference

    return new_state
