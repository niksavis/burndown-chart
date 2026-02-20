"""Field mapping callbacks package.

Provides callbacks for JIRA field mapping configuration across multiple tabs.

This package was refactored from a single 2846-line file to improve maintainability
and comply with 500-line architectural guidelines.
"""

# Import all callback modules to register them with Dash
from . import (
    auto_config,
    helpers,
    modal_core,
    modal_loading,
    profile_management,
    save_load,
    state_tracking,
    status_indicator,
    status_validation,
    tab_rendering,
    validation_helpers,
)

__all__ = [
    "helpers",
    "state_tracking",
    "status_validation",
    "modal_core",
    "tab_rendering",
    "modal_loading",
    "auto_config",
    "validation_helpers",
    "save_load",
    "profile_management",
    "status_indicator",
]
