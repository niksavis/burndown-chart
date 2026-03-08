"""
Loading Skeleton Private Helper Module

Private implementation of create_skeleton_loader, extracted for size
compliance. Import via ui.loading_utils_core or ui.loading_utils only.
"""

# Third-party library imports
from dash import html

# Application imports
from ui.style_constants import NEUTRAL_COLORS


def create_skeleton_loader(
    type="text", lines=1, width="100%", height=None, className=""
):
    """
    Creates a skeleton loading placeholder element.

    Args:
        type (str, optional): The type of skeleton element
            ("text", "card", "avatar", etc.).
            Defaults to "text". Determines base styling.
        lines (int, optional): Number of lines for text-type skeletons. Defaults to 1.
        width (str, optional): CSS width of the skeleton element. Defaults to "100%".
        height (str, optional): CSS height of the skeleton element.
            Defaults to None (auto).
        className (str, optional): Additional CSS classes to apply. Defaults to "".

    Returns:
        html.Div: A Div representing the skeleton loader.
    """
    base_style = {
        "backgroundColor": NEUTRAL_COLORS.get("gray-200"),
        "borderRadius": "0.25rem",
        "animation": "skeleton-loading 1.5s infinite ease-in-out",
    }

    if type == "text":
        # Create multiple text lines with varying widths
        items = []
        for i in range(lines):
            # Make some lines shorter for a more realistic text effect
            line_width = width
            if i == lines - 1:  # Last line
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
        # Circular skeleton (for avatars, icons)
        return html.Div(
            style={
                **base_style,
                "width": width,
                "height": width,  # Equal width and height
                "borderRadius": "50%",  # Make it circular
            },
            className=className,
        )

    elif type == "card":
        return html.Div(
            [
                # Card header
                html.Div(
                    style={
                        **base_style,
                        "width": "50%",
                        "height": "1.5rem",
                        "marginBottom": "1rem",
                    }
                ),
                # Card content
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
                # Card footer
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
        # Chart skeleton with axes and bars/lines
        chart_height = height or "200px"

        return html.Div(
            [
                # Y-axis
                html.Div(
                    style={
                        **base_style,
                        "width": "10%",
                        "height": chart_height,
                        "float": "left",
                        "marginRight": "5%",
                    }
                ),
                # Chart content
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
                # X-axis
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
        # Image placeholder
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

    else:  # Default rectangle
        return html.Div(
            style={**base_style, "width": width, "height": height or "2rem"},
            className=className,
        )
