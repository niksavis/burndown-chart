import dash_bootstrap_components as dbc
from dash import html


def add_aria_label_to_icon_button(component, label, options=None):

    options = options or {}

    default_options = {
        "role": "button",
        "include_tooltip": True,
        "tooltip_placement": "top",
    }

    for key, value in default_options.items():
        if key not in options:
            options[key] = value

    if not hasattr(component, "className"):
        component.className = ""

    component.className += " has-aria-label"
    component.role = options["role"]

    if not isinstance(component.children, list):
        component.children = [component.children]

    if hasattr(component, "children"):
        pass

    if not hasattr(component, "title") or component.title is None:
        component.title = label

    if options["include_tooltip"] and hasattr(component, "id"):
        tooltip = dbc.Tooltip(
            label,
            target=component.id,
            placement=options["tooltip_placement"],
            trigger="click",
            autohide=True,
        )
        return [component, tooltip]

    return component


def enhance_checkbox(component, label):

    if not hasattr(component, "className"):
        component.className = ""

    component.className += " has-aria-label"
    component.role = "checkbox"

    if hasattr(component, "checked"):
        component["aria-checked"] = bool(component.checked)

    return component


def create_screen_reader_only(text):

    return html.Span(
        text,
        style={
            "position": "absolute",
            "width": "1px",
            "height": "1px",
            "padding": "0",
            "margin": "-1px",
            "overflow": "hidden",
            "clip": "rect(0, 0, 0, 0)",
            "whiteSpace": "nowrap",
            "borderWidth": "0",
        },
    )


def enhance_data_table(table_component, options=None):

    options = options or {}

    table_component.role = "table"

    if "caption" in options:
        caption = None
        children = (
            table_component.children
            if isinstance(table_component.children, list)
            else [table_component.children]
        )

        for _i, child in enumerate(children):
            if isinstance(child, html.Caption):
                caption = child
                caption.children = options["caption"]
                break

        if not caption:
            caption = html.Caption(options["caption"])
            children.insert(0, caption)
            table_component.children = children

    def process_table_children(element):
        if not element or not isinstance(element, html.Base):
            return element

        if isinstance(element, html.Thead):
            element.role = "rowgroup"  # type: ignore[attr-defined]
        elif isinstance(element, html.Tbody):
            element.role = "rowgroup"  # type: ignore[attr-defined]
        elif isinstance(element, html.Tr):
            element.role = "row"  # type: ignore[attr-defined]
        elif isinstance(element, html.Th):
            element.role = "columnheader"  # type: ignore[attr-defined]
        elif isinstance(element, html.Td):
            element.role = "cell"  # type: ignore[attr-defined]

        if hasattr(element, "children"):
            if isinstance(element.children, list):
                element.children = [
                    process_table_children(child) for child in element.children
                ]
            else:
                element.children = process_table_children(element.children)

        return element

    if hasattr(table_component, "children"):
        if isinstance(table_component.children, list):
            table_component.children = [
                process_table_children(child) for child in table_component.children
            ]
        else:
            table_component.children = process_table_children(table_component.children)

    return table_component
