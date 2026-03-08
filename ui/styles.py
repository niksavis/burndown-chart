"""Backward-compatible re-export shim for ui.styles.

The implementation has been split into focused modules:
  - styles_tokens.py     -- design token constants and responsive utilities
  - styles_components.py -- component style builders (inputs, headings, progress)
  - styles_cards.py      -- card and metric card component builders
  - styles_layout.py     -- vertical rhythm, content sections, loading styles

All callers of ``ui.styles`` continue to work unchanged.
"""

from ui.style_constants import NEUTRAL_COLORS, TYPOGRAPHY  # noqa: F401
from ui.styles_cards import (  # noqa: F401
    create_card_header_with_tooltip,
    create_metric_card_header,
    create_standardized_card,
)
from ui.styles_components import (  # noqa: F401
    create_card_style,
    create_datepicker_style,
    create_form_feedback_style,
    create_heading_style,
    create_input_group_style,
    create_input_style,
    create_label_style,
    create_progress_bar,
    create_progress_bar_style,
    create_slider_style,
    create_text_style,
)
from ui.styles_layout import (  # noqa: F401
    FORM_VALIDATION_STATES,
    LOADING_STYLES,
    SKELETON_ANIMATION,
    SPINNER_SIZES,
    apply_content_spacing,
    apply_vertical_rhythm,
    create_content_section,
    create_loading_style,
    create_rhythm_text,
    create_vertical_spacer,
    update_heading_style,
)
from ui.styles_tokens import (  # noqa: F401
    BOOTSTRAP_SPACING,
    BREAKPOINTS,
    COMPONENT_SPACING,
    DEFAULT_ICON_STYLES,
    ICON_SIZES,
    MEDIA_QUERIES,
    SEMANTIC_ICONS,
    SPACING,
    VERTICAL_RHYTHM,
    create_responsive_container,
    create_responsive_style,
    create_responsive_text,
    get_breakpoint_range,
    get_breakpoint_value,
    get_color,
    get_font_size,
    get_font_weight,
    get_media_query,
    get_spacing,
    get_vertical_rhythm,
    next_breakpoint,
)

__all__ = [
    # Tokens
    "BOOTSTRAP_SPACING",
    "BREAKPOINTS",
    "COMPONENT_SPACING",
    "DEFAULT_ICON_STYLES",
    "ICON_SIZES",
    "MEDIA_QUERIES",
    "SEMANTIC_ICONS",
    "SPACING",
    "VERTICAL_RHYTHM",
    # Token accessors
    "get_breakpoint_range",
    "get_breakpoint_value",
    "get_color",
    "get_font_size",
    "get_font_weight",
    "get_media_query",
    "get_spacing",
    "next_breakpoint",
    # Responsive utilities
    "create_responsive_container",
    "create_responsive_style",
    "create_responsive_text",
    # Component styles
    "create_card_style",
    "create_datepicker_style",
    "create_form_feedback_style",
    "create_heading_style",
    "create_input_group_style",
    "create_input_style",
    "create_label_style",
    "create_progress_bar",
    "create_progress_bar_style",
    "create_slider_style",
    "create_text_style",
    # Card builders
    "create_card_header_with_tooltip",
    "create_metric_card_header",
    "create_standardized_card",
    # Layout / rhythm
    "FORM_VALIDATION_STATES",
    "LOADING_STYLES",
    "SKELETON_ANIMATION",
    "SPINNER_SIZES",
    "apply_content_spacing",
    "apply_vertical_rhythm",
    "create_content_section",
    "create_loading_style",
    "create_rhythm_text",
    "create_vertical_spacer",
    "get_vertical_rhythm",
    "update_heading_style",
]
