from dash import html

ICON_MAP = {
    "add": "fa-plus",
    "delete": "fa-trash",
    "edit": "fa-edit",
    "save": "fa-save",
    "upload": "fa-upload",
    "download": "fa-download",
    "export": "fa-file-export",
    "import": "fa-file-import",
    "refresh": "fa-sync",
    "filter": "fa-filter",
    "search": "fa-search",
    "close": "fa-times",
    "cancel": "fa-ban",
    "settings": "fa-cog",
    "success": "fa-check-circle",
    "error": "fa-exclamation-circle",
    "warning": "fa-exclamation-triangle",
    "info": "fa-info-circle",
    "help": "fa-question-circle",
    "chart": "fa-chart-bar",
    "trend_up": "fa-chart-line",
    "trend_down": "fa-chart-line fa-flip-vertical",
    "points": "fa-chart-bar",
    "items": "fa-tasks",
    "forecast": "fa-chart-line",
    "burndown": "fa-chart-area",
    "deadline": "fa-calendar-day",
    "next": "fa-chevron-right",
    "previous": "fa-chevron-left",
    "expand": "fa-chevron-down",
    "collapse": "fa-chevron-up",
    "home": "fa-home",
    "calendar": "fa-calendar-alt",
    "time": "fa-clock",
    "user": "fa-user",
    "team": "fa-users",
    "task": "fa-clipboard-check",
    "story": "fa-sticky-note",
    "epic": "fa-bookmark",
    "document": "fa-file-alt",
    "code": "fa-code",
    "github": "fa-github",
}

ICON_SIZES = {
    "xs": "0.75em",
    "sm": "0.875em",
    "md": "1em",
    "lg": "1.25em",
    "xl": "1.5em",
    "xxl": "2em",
}


def get_icon_class(icon_name, solid=True):

    icon_style = "fas" if solid else "far"

    if icon_name in ICON_MAP:
        icon_class = ICON_MAP[icon_name]
    else:
        icon_class = icon_name

    return f"{icon_style} {icon_class}"


def create_icon(icon_name, size="md", color=None, className="", solid=True, style=None):

    icon_class = get_icon_class(icon_name, solid)

    icon_style = style or {}
    if size in ICON_SIZES:
        icon_style["fontSize"] = ICON_SIZES[size]
    if color:
        icon_style["color"] = color

    classes = f"{icon_class} {className}".strip()

    return html.I(className=classes, style=icon_style)


def create_icon_text(
    icon_name,
    text,
    size="md",
    color=None,
    spacing="0.5rem",
    className="",
    reverse=False,
    solid=True,
    style=None,
):

    container_style = {"display": "inline-flex", "alignItems": "center", "gap": spacing}

    if style:
        container_style.update(style)

    icon = create_icon(
        icon_name,
        size=size,
        color=color,
        solid=solid,
        style={"display": "inline-flex", "alignItems": "center"},
    )

    text_el = html.Span(text, style={"color": color} if color else {})

    children = [text_el, icon] if reverse else [icon, text_el]

    return html.Div(children, className=className, style=container_style)
