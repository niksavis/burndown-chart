import logging
from datetime import datetime

from data.exceptions import ConfigurationError, PersistenceError
from data.persistence.adapters.app_settings import load_app_settings
from data.persistence.factory import get_backend
from data.schema import get_default_parameter_panel_state

logger = logging.getLogger(__name__)


def load_parameter_panel_state() -> dict:

    try:
        app_settings = load_app_settings()

        if "parameter_panel_state" in app_settings:
            panel_state = app_settings["parameter_panel_state"]

            if isinstance(panel_state, dict) and "is_open" in panel_state:
                return panel_state

        return dict(get_default_parameter_panel_state())

    except (
        ConfigurationError,
        KeyError,
        PersistenceError,
        TypeError,
        ValueError,
    ) as e:
        logger.warning(f"[Config] Error loading parameter panel state: {e}")
        return dict(get_default_parameter_panel_state())


def save_parameter_panel_state(is_open: bool, user_preference: bool = True) -> bool:

    try:
        panel_state = {
            "is_open": bool(is_open),
            "last_updated": datetime.now().isoformat(),
            "user_preference": bool(user_preference),
        }

        backend = get_backend()

        import json  # noqa: PLC0415

        backend.set_app_state("parameter_panel_state", json.dumps(panel_state))

        logger.debug(
            f"[Config] Parameter panel state saved to database: is_open={is_open}"
        )
        return True

    except (
        ConfigurationError,
        KeyError,
        PersistenceError,
        TypeError,
        ValueError,
    ) as e:
        logger.error(f"[Config] Error saving parameter panel state: {e}")
        return False
