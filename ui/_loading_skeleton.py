from dash import html

from ui.style_constants import NEUTRAL_COLORS


def create_skeleton_loader(
    type="text", lines=1, width="100%", height=None, className=""
):

    base_style = {
        "backgroundColor": NEUTRAL_COLORS.get("gray-200"),
        "borderRadius": "0.25rem",
        "animation": "skeleton-loading 1.5s infinite ease-in-out",
    }

    if type == "text":
        items = []
        for i in range(lines):
            line_width = width
            if i == lines - 1:
                line_width = "70%" if width == "100%" else width

            items.append(
                html.Div(
                    style={
                        **base_style,
                        "width": line_width,
                        "height": "1rem",
                        "marginBottom": "0.5rem" if i < lines - 1 else "0",
                    }
                )
            )
        return html.Div(items, className=className)

    elif type == "circle":
        return html.Div(
            style={
                **base_style,
                "width": width,
                "height": width,
                "borderRadius": "50%",
            },
            className=className,
        )

    elif type == "card":
        return html.Div(
            [
                html.Div(
                    style={
                        **base_style,
                        "width": "50%",
                        "height": "1.5rem",
                        "marginBottom": "1rem",
                    }
                ),
                html.Div(
                    [
                        html.Div(
                            style={
                                **base_style,
                                "width": "100%",
                                "height": "0.75rem",
                                "marginBottom": "0.5rem",
                            }
                        )
                        for _ in range(4)
                    ]
                ),
                html.Div(
                    style={
                        **base_style,
                        "width": "30%",
                        "height": "1rem",
                        "marginTop": "1rem",
                    }
                ),
            ],
            style={
                "width": width,
                "padding": "1rem",
                "border": f"1px solid {NEUTRAL_COLORS.get('gray-200')}",
                "borderRadius": "0.5rem",
            },
            className=className,
        )

    elif type == "chart":
        chart_height = height or "200px"

        return html.Div(
            [
                html.Div(
                    style={
                        **base_style,
                        "width": "10%",
                        "height": chart_height,
                        "float": "left",
                        "marginRight": "5%",
                    }
                ),
                html.Div(
                    [
                        html.Div(
                            style={
                                **base_style,
                                "width": "10%",
                                "height": f"{30 + (i * 15 % 40)}%",
                                "display": "inline-block",
                                "marginRight": "5%",
                            }
                        )
                        for i in range(5)
                    ],
                    style={
                        "width": "85%",
                        "height": chart_height,
                        "float": "left",
                        "display": "flex",
                        "alignItems": "flex-end",
                    },
                ),
                html.Div(
                    style={
                        **base_style,
                        "width": "85%",
                        "height": "10px",
                        "marginTop": "10px",
                        "marginLeft": "15%",
                        "clear": "both",
                    }
                ),
            ],
            style={"width": width, "clear": "both"},
            className=className,
        )

    elif type == "image":
        image_height = height or "200px"

        return html.Div(
            html.Div(
                html.I(className="fas fa-image text-muted"),
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "height": "100%",
                },
            ),
            style={
                **base_style,
                "width": width,
                "height": image_height,
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
            },
            className=className,
        )

    else:
        return html.Div(
            style={**base_style, "width": width, "height": height or "2rem"},
            className=className,
        )
