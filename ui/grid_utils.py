import dash_bootstrap_components as dbc
from dash import html

from ui.styles import (
    get_vertical_rhythm,
)

BOOTSTRAP_BREAKPOINTS = ["xs", "sm", "md", "lg", "xl", "xxl"]


def create_responsive_row(
    children,
    className="",
    style=None,
    row_class_by_breakpoint=None,
    alignment_by_breakpoint=None,
    gutters_by_breakpoint=None,
):

    classes = [className] if className else []

    if row_class_by_breakpoint:
        for bp, cls in row_class_by_breakpoint.items():
            if bp == "xs":
                classes.append(cls)
            else:
                classes.append(f"{cls}-{bp}")

    if alignment_by_breakpoint:
        for bp, align in alignment_by_breakpoint.items():
            if bp == "xs":
                classes.append(align)
            else:
                classes.append(f"{align}-{bp}")

    if gutters_by_breakpoint:
        for bp, gutter in gutters_by_breakpoint.items():
            if bp == "xs":
                classes.append(f"g-{gutter}")
            else:
                classes.append(f"g-{bp}-{gutter}")

    row_class = " ".join(classes)

    return dbc.Row(children, className=row_class, style=style)


def create_responsive_column(
    content,
    xs=12,
    sm=None,
    md=None,
    lg=None,
    xl=None,
    xxl=None,
    className="",
    style=None,
    order_by_breakpoint=None,
    visibility_by_breakpoint=None,
    padding_by_breakpoint=None,
):

    width_config = {}
    if xs is not None:
        width_config["xs"] = xs
    if sm is not None:
        width_config["sm"] = sm
    if md is not None:
        width_config["md"] = md
    if lg is not None:
        width_config["lg"] = lg
    if xl is not None:
        width_config["xl"] = xl
    if xxl is not None:
        width_config["xxl"] = xxl

    classes = [className] if className else []

    if order_by_breakpoint:
        for bp, order in order_by_breakpoint.items():
            if bp == "xs":
                classes.append(f"order-{order}")
            else:
                classes.append(f"order-{bp}-{order}")

    if visibility_by_breakpoint:
        for bp, visible in visibility_by_breakpoint.items():
            if bp == "xs":
                classes.append(f"d-{'block' if visible else 'none'}")
            else:
                classes.append(f"d-{bp}-{'block' if visible else 'none'}")

    if padding_by_breakpoint:
        for bp, padding in padding_by_breakpoint.items():
            if bp == "xs":
                classes.append(f"p-{padding}")
            else:
                classes.append(f"p-{bp}-{padding}")

    col_class = " ".join(classes)

    return dbc.Col(content, **width_config, className=col_class, style=style)


def create_container(content, fluid=True, className="", style=None):

    return dbc.Container(
        content,
        fluid=fluid,
        className=className,
        style=style,
    )


def apply_grid_rhythm(component, rhythm_type="section", extra_classes=None):

    margin_bottom = get_vertical_rhythm(rhythm_type)

    classes = extra_classes.split() if extra_classes else []

    style = {"marginBottom": margin_bottom}

    if hasattr(component, "className") and component.className:
        classes.append(component.className)

    if hasattr(component, "style") and component.style:
        style.update(component.style)

    component.className = " ".join(classes) if classes else None
    component.style = style

    return component


def create_multi_column_layout(
    columns_content,
    column_widths=None,
    breakpoint="md",
    spacing="standard",
    className="",
):

    if not columns_content:
        return html.Div()

    num_columns = len(columns_content)
    if column_widths is None:
        col_width = 12 // num_columns
        column_widths = [col_width] * num_columns

    if spacing == "compact":
        gutter = {"xs": "1", breakpoint: "2"}
    elif spacing == "wide":
        gutter = {"xs": "2", breakpoint: "4"}
    else:
        gutter = {"xs": "2", breakpoint: "3"}

    margin_bottom = get_vertical_rhythm("section")
    row_style = {"marginBottom": margin_bottom}

    cols = []
    for i, content in enumerate(columns_content):
        widths = {"xs": 12}

        if breakpoint != "xs":
            widths[breakpoint] = column_widths[i] if i < len(column_widths) else 12

        col_class = f"mb-4 mb-{breakpoint}-0" if i < num_columns - 1 else ""

        cols.append(create_responsive_column(content, className=col_class, **widths))

    return create_responsive_row(
        cols, className=className, gutters_by_breakpoint=gutter, style=row_style
    )


def create_two_column_layout(
    left_content,
    right_content,
    left_width=6,
    right_width=6,
    breakpoint="md",
    className="",
):

    return create_multi_column_layout(
        [left_content, right_content],
        [left_width, right_width],
        breakpoint=breakpoint,
        className=className,
    )


def create_three_column_layout(
    left,
    middle,
    right,
    left_width=4,
    middle_width=4,
    right_width=4,
    breakpoint="md",
    className="",
):

    return create_multi_column_layout(
        [left, middle, right],
        [left_width, middle_width, right_width],
        breakpoint=breakpoint,
        className=className,
    )


def create_stacked_to_horizontal(
    left_content,
    right_content,
    stack_until="md",
    left_width=6,
    right_width=6,
    equal_height=True,
    className="",
):

    bp_order = BOOTSTRAP_BREAKPOINTS
    try:
        stack_index = bp_order.index(stack_until)
    except ValueError:
        stack_index = 1

    left_widths = {"xs": 12}
    right_widths = {"xs": 12}

    for bp in bp_order[stack_index + 1 :]:
        left_widths[bp] = left_width
        right_widths[bp] = right_width

    left_margin_classes = ["mb-4"]
    for bp in bp_order[stack_index + 1 :]:
        left_margin_classes.append(f"mb-{bp}-0")

    left_column = create_responsive_column(
        left_content,
        className=" ".join(left_margin_classes) + (" h-100" if equal_height else ""),
        **left_widths,
    )

    right_column = create_responsive_column(
        right_content, className=("h-100" if equal_height else ""), **right_widths
    )

    margin_bottom = get_vertical_rhythm("section")
    base_style = {"marginBottom": margin_bottom}

    return create_responsive_row(
        [left_column, right_column], className=className, style=base_style
    )


def create_responsive_grid(
    items,
    cols_by_breakpoint=None,
    breakpoints=None,
    item_class="",
    row_class="",
    container_class="",
):

    if breakpoints is None:
        breakpoints = ["xs", "sm", "md", "lg", "xl", "xxl"]
    if not items:
        return html.Div()

    if cols_by_breakpoint is None:
        cols_by_breakpoint = {
            "xs": 1,
            "md": 2,
            "lg": 3,
        }

    column_widths = {}
    for breakpoint, num_cols in cols_by_breakpoint.items():
        if num_cols > 0:
            column_widths[breakpoint] = 12 // num_cols

    columns = []
    for item in items:
        width_config = {}
        for breakpoint in breakpoints:
            if breakpoint in column_widths:
                width_config[breakpoint] = column_widths[breakpoint]

        columns.append(
            create_responsive_column(
                html.Div(item, className=f"grid-item {item_class}"),
                className="mb-4",
                **width_config,
            )
        )

    grid = create_responsive_row(columns, className=row_class)

    return html.Div(grid, className=f"responsive-grid-container {container_class}")


def create_content_sidebar_layout(
    content,
    sidebar,
    sidebar_position="right",
    sidebar_width=4,
    content_width=8,
    stack_until="md",
    spacing="standard",
):

    if sidebar_position == "left":
        left_content = sidebar
        right_content = content
        left_width = sidebar_width
        right_width = content_width
    else:
        left_content = content
        right_content = sidebar
        left_width = content_width
        right_width = sidebar_width

    return create_stacked_to_horizontal(
        left_content=left_content,
        right_content=right_content,
        stack_until=stack_until,
        left_width=left_width,
        right_width=right_width,
        equal_height=True,
    )


def create_dashboard_layout(
    main_content,
    side_content,
    secondary_content=None,
    stack_until="lg",
    main_width=8,
    side_width=4,
    secondary_display_breakpoint="xl",
):

    main_column_props = {"xs": 12}

    bp_order = BOOTSTRAP_BREAKPOINTS
    stack_index = bp_order.index("lg")
    try:
        stack_index = bp_order.index(stack_until)
        for bp in bp_order[stack_index + 1 :]:
            main_column_props[bp] = main_width
    except ValueError:
        main_column_props["lg"] = main_width

    side_column_props = {"xs": 12}

    try:
        for bp in bp_order[stack_index + 1 :]:
            side_column_props[bp] = side_width
    except ValueError:
        side_column_props["lg"] = side_width

    secondary_visibility = {}
    secondary_column = None

    if secondary_content:
        try:
            sec_index = bp_order.index(secondary_display_breakpoint)
            for i, bp in enumerate(bp_order):
                secondary_visibility[bp] = i >= sec_index
        except ValueError:
            secondary_visibility = {
                "xs": False,
                "sm": False,
                "md": False,
                "lg": False,
                "xl": True,
                "xxl": True,
            }

        secondary_column = create_responsive_column(
            secondary_content,
            xs=12,
            className="mb-4",
            visibility_by_breakpoint=secondary_visibility,
        )

    main_column = create_responsive_column(
        main_content, **main_column_props, className="mb-4"
    )

    side_column = create_responsive_column(
        side_content, **side_column_props, className="mb-4"
    )

    columns = [main_column, side_column]
    if secondary_column:
        columns.append(secondary_column)

    return dbc.Row(columns)


def create_card_grid(cards, cols_by_breakpoint=None, equal_height=True):

    if cols_by_breakpoint is None:
        cols_by_breakpoint = {"xs": 1, "md": 2, "lg": 3}
    if not cards:
        return html.Div()

    col_widths = {}
    for bp, cols in cols_by_breakpoint.items():
        col_widths[bp] = 12 // cols

    columns = []
    for card in cards:
        card_container_class = "mb-4" + (" h-100" if equal_height else "")

        columns.append(
            create_responsive_column(
                html.Div(card, className=card_container_class), **col_widths
            )
        )

    return dbc.Row(columns, className="card-deck")


def create_form_row(form_groups, columns=None):

    if columns is None:
        col_width = 12 // len(form_groups)
        columns = [col_width] * len(form_groups)

    cols = []
    for i, form_group in enumerate(form_groups):
        cols.append(dbc.Col(form_group, width=12, md=columns[i]))

    margin_bottom = get_vertical_rhythm("form_element")

    return dbc.Row(cols, style={"marginBottom": margin_bottom})


def create_responsive_table_wrapper(table_component, max_height=None, className=""):

    container_style = {
        "overflowX": "auto",
        "width": "100%",
        "WebkitOverflowScrolling": "touch",
    }

    if max_height:
        container_style["maxHeight"] = max_height
        container_style["overflowY"] = "auto"

    return html.Div(
        table_component,
        className=f"table-responsive {className}",
        style=container_style,
    )


def create_form_section(title, components, help_text=None):

    section_components = []

    section_components.append(
        html.H5(
            title,
            className="border-bottom pb-2",
            style={"marginBottom": get_vertical_rhythm("heading.h5")},
        )
    )

    if help_text:
        section_components.append(
            html.P(
                help_text,
                className="text-muted",
                style={"marginBottom": get_vertical_rhythm("paragraph")},
            )
        )

    section_components.extend(components)

    margin_bottom = get_vertical_rhythm("section")

    return html.Div(section_components, style={"marginBottom": margin_bottom})


def create_breakpoint_visibility_examples():

    examples = [
        html.Div(
            "Visible on extra small screens only (xs)",
            className="bg-primary text-white p-2 d-block d-sm-none",
        ),
        html.Div(
            "Visible on small screens and up (sm+)",
            className="bg-secondary text-white p-2 d-none d-sm-block",
        ),
        html.Div(
            "Visible on medium screens and up (md+)",
            className="bg-success text-white p-2 d-none d-md-block",
        ),
        html.Div(
            "Visible on large screens and up (lg+)",
            className="bg-info text-white p-2 d-none d-lg-block",
        ),
        html.Div(
            "Visible on extra large screens and up (xl+)",
            className="bg-warning p-2 d-none d-xl-block",
        ),
        html.Div(
            "Visible on extra extra large screens only (xxl)",
            className="bg-danger text-white p-2 d-none d-xxl-block",
        ),
        html.Div(
            "Visible on mobile only (xs and sm)",
            className="bg-dark text-white p-2 d-block d-md-none",
        ),
        html.Div(
            "Visible on tablet only (md)",
            className="bg-light p-2 d-none d-md-block d-lg-none",
        ),
    ]

    return html.Div(examples, className="mb-4")


def create_mobile_container(content, expanded_height="auto", className=""):

    container = html.Div(
        content,
        className=f"mobile-collapsible-container d-md-block {className}",
    )

    return container


def create_tab_content(content, padding=None):

    if padding is None:
        padding = "p-3"

    return html.Div(content, className=f"{padding} border border-top-0 rounded-bottom")


def create_full_width_layout(content, row_class=None):

    margin_bottom = get_vertical_rhythm("section")
    row_style = {"marginBottom": margin_bottom}

    combined_class = row_class if row_class else ""

    return dbc.Row(
        [
            dbc.Col(content, width=12),
        ],
        className=combined_class,
        style=row_style,
    )


def create_two_cards_layout(
    card1, card2, card1_width=6, card2_width=6, equal_height=True
):

    card1_class = "h-100" if equal_height else ""
    card2_class = "h-100" if equal_height else ""

    card1 = html.Div(card1, className=card1_class)
    card2 = html.Div(card2, className=card2_class)

    return create_two_column_layout(
        left_content=card1,
        right_content=card2,
        left_width=card1_width,
        right_width=card2_width,
    )
