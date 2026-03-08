"""
Loading Utilities Module

Re-export shim: preserves the original public API while delegating
implementation to the focused sub-modules:
  - ui.loading_utils_core     (spinners, overlays, skeleton loaders)
  - ui.loading_utils_patterns (placeholders, loading-state factory, async containers)
"""

#######################################################################
# RE-EXPORTS
#######################################################################
from ui.loading_utils_core import (  # noqa: F401
    LOADING_STYLES,
    SKELETON_ANIMATION,
    SPINNER_SIZES,
    create_bootstrap_spinner,
    create_fullscreen_loading,
    create_growing_spinner,
    create_loading_overlay,
    create_skeleton_loader,
    create_spinner,
    create_spinner_style,
    get_loading_style,
)
from ui.loading_utils_patterns import (  # noqa: F401
    create_async_content,
    create_content_placeholder,
    create_data_loading_section,
    create_lazy_loading_tabs,
    create_loading_state,
)
