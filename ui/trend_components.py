from dash import html

TREND_ICONS = {
    "stable": "fas fa-equals",
    "up": "fas fa-arrow-up",
    "down": "fas fa-arrow-down",
    "baseline": "fas fa-hourglass-half",
}

TREND_COLORS = {
    "stable": "#6c757d",
    "up": "#28a745",
    "down": "#dc3545",
}


def create_compact_trend_indicator(trend_data, metric_name="Items"):

    percent_change = trend_data.get("percent_change", 0)
    current_avg = trend_data.get("current_avg", 0)
    previous_avg = trend_data.get("previous_avg", 0)
    weeks_compared = trend_data.get("weeks_compared", 4)

    total_weeks_needed = 8
    total_weeks_available = weeks_compared * 2

    is_insufficient_data = (
        weeks_compared < 4 or total_weeks_available < total_weeks_needed
    )

    if is_insufficient_data:
        if weeks_compared < 4:
            total_weeks_available = weeks_compared * 2
        else:
            total_weeks_available = 0

        direction = "baseline"
        icon_class = TREND_ICONS.get("baseline", "fas fa-hourglass-half")
        text_color = "#6c757d"
        bg_color = "rgba(108, 117, 125, 0.1)"
        border_color = "rgba(108, 117, 125, 0.2)"
    elif abs(percent_change) < 5:
        direction = "stable"
        icon_class = TREND_ICONS["stable"]
        text_color = TREND_COLORS["stable"]
        bg_color = "rgba(108, 117, 125, 0.1)"
        border_color = "rgba(108, 117, 125, 0.2)"
    elif percent_change > 0:
        direction = "up"
        icon_class = TREND_ICONS["up"]
        text_color = TREND_COLORS["up"]
        bg_color = "rgba(40, 167, 69, 0.1)"
        border_color = "rgba(40, 167, 69, 0.2)"
    else:
        direction = "down"
        icon_class = TREND_ICONS["down"]
        text_color = TREND_COLORS["down"]
        bg_color = "rgba(220, 53, 69, 0.1)"
        border_color = "rgba(220, 53, 69, 0.2)"

    if direction == "baseline":
        if total_weeks_available == 0:
            trend_badge = "Building baseline..."
        else:
            trend_badge = (
                f"Building baseline ({total_weeks_available}"
                f" of {total_weeks_needed} weeks)"
            )
    else:
        trend_badge = f"{abs(percent_change):.0f}% {direction.capitalize()}"

    return html.Div(
        className="compact-trend-indicator d-flex align-items-center p-2 rounded mb-3",
        style={
            "backgroundColor": bg_color,
            "border": f"1px solid {border_color}",
            "maxWidth": "100%",
        },
        children=[
            html.Div(
                className=(
                    "trend-icon me-3 d-flex align-items-center "
                    "justify-content-center rounded-circle"
                ),
                style={
                    "width": "36px",
                    "height": "36px",
                    "backgroundColor": "white",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "flexShrink": 0,
                },
                children=html.I(
                    className=f"{icon_class}",
                    style={"color": text_color, "fontSize": "1rem"},
                ),
            ),
            html.Div(
                className="trend-info",
                style={"flexGrow": 1, "minWidth": 0},
                children=[
                    html.Div(
                        className="d-flex justify-content-between align-items-baseline",
                        children=[
                            html.Span(
                                f"Weekly {metric_name} Trend",
                                className="fw-medium",
                                style={"fontSize": "0.9rem"},
                            ),
                            html.Span(
                                trend_badge,
                                style={
                                    "color": text_color,
                                    "fontWeight": "500",
                                    "fontSize": "0.9rem",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        className=(
                            "d-flex justify-content-between align-items-baseline mt-1"
                        ),
                        style={"fontSize": "0.8rem", "color": "#6c757d"},
                        children=(
                            [
                                html.Span(
                                    "Collecting data to establish performance baseline",
                                    style={"fontStyle": "italic"},
                                ),
                            ]
                            if direction == "baseline"
                            else [
                                html.Span(
                                    f"4-week avg: {current_avg:.1f}"
                                    f" {metric_name.lower()}/week",
                                    style={"marginRight": "15px"},
                                ),
                                html.Span(
                                    f"Previous: {previous_avg:.1f}"
                                    f" {metric_name.lower()}/week",
                                    style={"marginLeft": "5px"},
                                ),
                            ]
                        ),
                    ),
                ],
            ),
        ],
    )


def create_trend_indicator(trend_data, metric_name="Items"):

    percent_change = trend_data.get("percent_change", 0)
    is_significant = trend_data.get("is_significant", False)
    weeks = trend_data.get("weeks_compared", 4)
    current_avg = trend_data.get("current_avg", 0)
    previous_avg = trend_data.get("previous_avg", 0)

    if abs(percent_change) < 5:
        direction = "stable"
    elif percent_change > 0:
        direction = "up"
    else:
        direction = "down"

    text_color = TREND_COLORS[direction]
    icon_class = TREND_ICONS[direction]

    font_weight = "bold" if is_significant else "normal"

    direction_label = (
        "Increase"
        if direction == "up"
        else "Decrease"
        if direction == "down"
        else "Change"
    )
    trend_word = (
        "increase"
        if direction == "up"
        else "decrease"
        if direction == "down"
        else "trend"
    )
    significance_text = (
        "statistically significant"
        if is_significant
        else "not statistically significant"
    )
    trend_class = (
        "text-success"
        if direction == "up" and is_significant
        else "text-danger"
        if direction == "down" and is_significant
        else "text-muted"
    )

    return html.Div(
        [
            html.H6(f"{metric_name} Trend (Last {weeks * 2} Weeks)", className="mb-2"),
            html.Div(
                [
                    html.I(
                        className=icon_class,
                        style={
                            "color": text_color,
                            "fontSize": "1.5rem",
                            "marginRight": "10px",
                        },
                    ),
                    html.Span(
                        f"{abs(percent_change)}% {direction_label}",
                        style={
                            "color": text_color,
                            "fontWeight": font_weight,
                            "fontSize": "1.2rem",
                        },
                    ),
                ],
                className="d-flex align-items-center mb-2",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Recent Average: ", className="font-weight-bold"),
                            html.Span(f"{current_avg} {metric_name.lower()}/week"),
                        ],
                        className="mr-3",
                    ),
                    html.Div(
                        [
                            html.Span(
                                "Previous Average: ", className="font-weight-bold"
                            ),
                            html.Span(f"{previous_avg} {metric_name.lower()}/week"),
                        ],
                    ),
                ],
                className="d-flex flex-wrap small text-muted",
            ),
            html.Div(
                html.Span(
                    f"This {trend_word} is {significance_text}.",
                    className=trend_class,
                ),
                className="mt-2 small",
                style={"display": "block" if is_significant else "none"},
            ),
        ],
        className="trend-indicator mb-4 p-3 border rounded",
        style={
            "backgroundColor": f"rgba({text_color.replace('#', '')}, 0.05)"
            if text_color.startswith("#")
            else "rgba(108, 117, 125, 0.05)",
        },
    )
