import time
from functools import lru_cache

from ui.style_constants import HOVER_MODES, TOOLTIP_STYLES, TYPOGRAPHY


def get_tooltip_style(variant="default"):

    if variant in TOOLTIP_STYLES:
        return TOOLTIP_STYLES[variant]
    return TOOLTIP_STYLES["default"]


def create_hoverlabel_config(variant="default"):

    style = get_tooltip_style(variant)

    return {
        "bgcolor": style["bgcolor"],
        "bordercolor": style["bordercolor"],
        "font": {
            "family": TYPOGRAPHY["font_family"],
            "size": style["fontsize"],
            "color": style["fontcolor"],
        },
    }


def get_hover_mode(mode_key="standard"):

    return HOVER_MODES.get(mode_key, HOVER_MODES["standard"])


def format_hover_template(
    title=None, fields=None, extra_info=None, include_extra_tag=True
):

    template = []

    if title:
        template.append(f"<b>{title}</b><br>")

    if fields:
        for label, value in fields.items():
            template.append(f"{label}: {value}<br>")

    hover_text = "".join(template)

    if include_extra_tag:
        if extra_info:
            return f"{hover_text}<extra>{extra_info}</extra>"
        return f"{hover_text}<extra></extra>"

    return hover_text


def create_chart_layout_config(
    title=None, hover_mode="unified", tooltip_variant="dark"
):

    config = {
        "hovermode": get_hover_mode(hover_mode),
        "hoverlabel": create_hoverlabel_config(tooltip_variant),
        "margin": {"l": 40, "r": 40, "t": 60, "b": 40},
    }

    if title:
        config["title"] = {
            "text": title,
            "font": {"family": TYPOGRAPHY["font_family"]},
        }

    return config


_tooltip_cache = {}
_cache_timestamps = {}
_CACHE_TTL = 300


@lru_cache(maxsize=128)
def get_cached_tooltip_style(variant="default"):

    return get_tooltip_style(variant)


@lru_cache(maxsize=64)
def get_cached_hover_config(variant="default"):

    return create_hoverlabel_config(variant)


def cache_tooltip_content(key, content, ttl=None):

    ttl = ttl or _CACHE_TTL
    _tooltip_cache[key] = content
    _cache_timestamps[key] = time.time() + ttl


def get_cached_tooltip_content(key):

    if key not in _tooltip_cache:
        return None

    if key in _cache_timestamps and time.time() > _cache_timestamps[key]:
        del _tooltip_cache[key]
        del _cache_timestamps[key]
        return None

    return _tooltip_cache[key]


def clear_tooltip_cache():
    _tooltip_cache.clear()
    _cache_timestamps.clear()


def _is_mobile_context():

    return False


def get_smart_placement(preferred="top", mobile_override=None):

    if mobile_override and _is_mobile_context():
        return mobile_override

    return preferred


def get_responsive_placement(element_position="center"):

    placement_map = {
        "top": "bottom",
        "bottom": "top",
        "left": "right",
        "right": "left",
        "center": "top",
    }

    return placement_map.get(element_position, "top")


def create_adaptive_tooltip_config(base_delay=200, mobile_delay=300):

    if _is_mobile_context():
        return {"show": mobile_delay, "hide": mobile_delay // 2}

    return {"show": base_delay, "hide": base_delay // 2}
