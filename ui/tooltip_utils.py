"""
Tooltip Utilities Module

Re-export shim: preserves the original public API while delegating
implementation to the focused sub-modules:
  - ui.tooltip_utils_core  (hoverlabel/template/cache/positioning)
  - ui.tooltip_utils_cards (card/metric tooltip builders)
  - ui.tooltip_utils_charts (chart-specific tooltip builders)
"""

#######################################################################
# RE-EXPORTS
#######################################################################
from ui.tooltip_utils_cards import (  # noqa: F401
    _create_interactive_content,
    create_contextual_help,
    create_dismissible_tooltip,
    create_enhanced_tooltip,
    create_expandable_tooltip,
    create_form_help_tooltip,
    create_help_icon,
    create_info_tooltip,
    create_tooltip,
)
from ui.tooltip_utils_charts import (  # noqa: F401
    create_calculation_step_tooltip,
    create_chart_tooltip_bundle,
    create_formula_tooltip,
    create_lazy_tooltip,
    create_responsive_tooltip_system,
    create_statistical_context_tooltip,
    create_tooltip_with_settings_integration,
)
from ui.tooltip_utils_core import (  # noqa: F401
    _is_mobile_context,
    cache_tooltip_content,
    clear_tooltip_cache,
    create_adaptive_tooltip_config,
    create_chart_layout_config,
    get_cached_hover_config,
    get_cached_tooltip_content,
    get_cached_tooltip_style,
    get_hover_mode,
    get_responsive_placement,
    get_smart_placement,
    get_tooltip_style,
)
from utils.chart_tooltip_utils import (  # noqa: F401
    create_hoverlabel_config,
    format_hover_template,
)
