"""
Persistence layer public interface for Burndown application.

Architecture Pattern: Repository Pattern. Implementation is split across:
- _persistence_interface.py  -- PersistenceBackend ABC
- _persistence_errors.py     -- exception hierarchy
- _persistence_proxy.py      -- lazy backend proxy and adapter resolver
"""

from data.persistence._persistence_errors import (  # noqa: F401
    DatabaseCorruptionError,
    PersistenceError,
    ProfileNotFoundError,
    QueryNotFoundError,
    ValidationError,
)
from data.persistence._persistence_interface import PersistenceBackend  # noqa: F401
from data.persistence._persistence_proxy import backend  # noqa: F401
from data.persistence.adapters.app_settings import (  # noqa: E402
    load_app_settings,
    save_app_settings,
)
from data.persistence.adapters.jira_config import (  # noqa: E402
    load_jira_configuration,
    save_jira_configuration,
)
from data.persistence.adapters.legacy_data import (  # noqa: E402
    load_unified_project_data,
    save_jira_data_unified,
)

__all__ = [
    "PersistenceBackend",
    "backend",
    "load_app_settings",
    "save_app_settings",
    "load_jira_configuration",
    "save_jira_configuration",
    "load_unified_project_data",
    "save_jira_data_unified",
]


def __getattr__(name: str):
    from data.persistence._persistence_proxy import lazy_getattr

    return lazy_getattr(name)
