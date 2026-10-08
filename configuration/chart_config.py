from datetime import datetime
from typing import Any


def _build_image_filename(prefix: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def get_chart_config(
    responsive: bool = True,
    display_mode_bar: bool | None = None,
    display_logo: bool = False,
    mobile_friendly: bool = True,
    filename_prefix: str | None = None,
    **kwargs,
) -> dict[str, Any]:

    if display_mode_bar is None:
        display_mode_bar = True

    config = {
        "responsive": responsive,
        "displayModeBar": display_mode_bar,
        "displaylogo": display_logo,
        "modeBarButtonsToRemove": [
            "lasso2d",
            "select2d",
            "toggleSpikelines",
        ],
        "toImageButtonOptions": {
            "format": "png",
            "filename": _build_image_filename(filename_prefix or "chart"),
            "height": None,
            "width": None,
            "scale": 2,
        },
        "scrollZoom": False,
        "doubleClick": "reset+autosize",
    }

    if mobile_friendly:
        config.update(
            {
                "modeBarButtonsToAdd": [],
            }
        )

    config.update(kwargs)

    return config


def get_chart_layout_config(
    height: int | None = None,
    margin: dict[str, int] | None = None,
    font_size: int = 12,
    show_legend: bool = True,
    legend_position: str = "top",
    mobile_optimized: bool = True,
    **kwargs,
) -> dict[str, Any]:

    if margin is None:
        if mobile_optimized:
            margin = {"t": 40, "r": 20, "b": 50, "l": 60}
        else:
            margin = {"t": 60, "r": 40, "b": 60, "l": 80}

    legend_configs = {
        "top": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        "bottom": {
            "orientation": "h",
            "yanchor": "top",
            "y": -0.2,
            "xanchor": "center",
            "x": 0.5,
        },
        "left": {
            "orientation": "v",
            "yanchor": "top",
            "y": 1,
            "xanchor": "right",
            "x": -0.05,
        },
        "right": {
            "orientation": "v",
            "yanchor": "top",
            "y": 1,
            "xanchor": "left",
            "x": 1.02,
        },
    }

    legend_config = legend_configs.get(legend_position, legend_configs["top"])

    layout = {
        "font": {
            "size": font_size,
            "family": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
        },
        "margin": margin,
        "showlegend": show_legend,
        "legend": legend_config if show_legend else {},
        "hovermode": "closest",
        "paper_bgcolor": "white",
        "plot_bgcolor": "rgba(0,0,0,0.02)",
        "xaxis": {
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "zeroline": False,
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "zeroline": False,
        },
    }

    if height is not None:
        layout["height"] = height

    layout.update(kwargs)

    return layout


def get_burndown_chart_config(
    filename_prefix: str = "burndown_chart",
) -> dict[str, Any]:
    return get_chart_config(
        display_mode_bar=True,
        filename_prefix=filename_prefix,
        modeBarButtonsToRemove=[
            "lasso2d",
            "select2d",
            "toggleSpikelines",
        ],
    )


def get_weekly_chart_config(
    filename_prefix: str = "weekly_chart",
) -> dict[str, Any]:
    return get_chart_config(
        display_mode_bar=True,
        filename_prefix=filename_prefix,
        modeBarButtonsToRemove=[
            "lasso2d",
            "select2d",
            "toggleSpikelines",
        ],
    )


def get_scope_metrics_chart_config(
    filename_prefix: str = "scope_metrics",
) -> dict[str, Any]:
    return get_chart_config(
        display_mode_bar=True,
        filename_prefix=filename_prefix,
        modeBarButtonsToRemove=[
            "lasso2d",
            "select2d",
            "toggleSpikelines",
        ],
    )


def get_bug_analysis_chart_config(
    filename_prefix: str = "bug_analysis",
) -> dict[str, Any]:
    return get_chart_config(
        display_mode_bar=True,
        filename_prefix=filename_prefix,
        modeBarButtonsToRemove=[
            "lasso2d",
            "select2d",
            "toggleSpikelines",
        ],
    )


def is_mobile_viewport(width: int | None = None) -> bool:

    MOBILE_BREAKPOINT = 768

    if width is None:
        return False

    return width < MOBILE_BREAKPOINT
