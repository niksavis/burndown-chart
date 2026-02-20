"""Parameter panel components package.

Refactored from ui/parameter_panel.py to comply with 500-line architectural limit.
Provides collapsed and expanded parameter panels for dashboard configuration.
"""

from .collapsed_bar import create_parameter_bar_collapsed
from .expanded_panel import create_parameter_panel_expanded
from .mobile_components import (
    create_mobile_parameter_bottom_sheet,
    create_mobile_parameter_fab,
)
from .panel_controller import create_parameter_panel
from .settings_tab import create_settings_tab_content

__all__ = [
    "create_parameter_bar_collapsed",
    "create_settings_tab_content",
    "create_parameter_panel_expanded",
    "create_parameter_panel",
    "create_mobile_parameter_fab",
    "create_mobile_parameter_bottom_sheet",
]
