from datetime import datetime
from typing import Any


def get_mobile_first_config() -> dict[str, Any]:

    return {
        "displayModeBar": False,
        "staticPlot": False,
        "responsive": True,
        "toImageButtonOptions": {
            "format": "png",
            "filename": f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "height": 500,
            "width": 700,
            "scale": 1,
        },
        "displaylogo": False,
        "modeBarButtonsToRemove": [
            "zoom2d",
            "pan2d",
            "select2d",
            "lasso2d",
            "zoomIn2d",
            "zoomOut2d",
            "autoScale2d",
            "resetScale2d",
            "hoverClosestCartesian",
            "hoverCompareCartesian",
            "zoom3d",
            "pan3d",
            "resetCameraDefault3d",
            "resetCameraLastSave3d",
            "hoverClosest3d",
            "orbitRotation",
            "tableRotation",
            "zoomInGeo",
            "zoomOutGeo",
            "resetGeo",
            "hoverClosestGeo",
            "toImage",
            "sendDataToCloud",
            "hoverClosestGl2d",
            "hoverClosestPie",
            "toggleHover",
            "resetViews",
        ],
        "scrollZoom": False,
        "doubleClick": False,
        "showTips": False,
        "showAxisDragHandles": False,
        "showAxisRangeEntryBoxes": False,
        "editable": False,
    }


def get_mobile_first_layout(
    title: str, height: int = 300, show_performance_zones: bool = False
) -> dict[str, Any]:

    return {
        "height": height,
        "margin": dict(l=50, r=20, t=10, b=50),
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "hovermode": "x unified",
        "showlegend": False,
        "font": {"size": 12},
        "xaxis": {
            "title": "",
            "showgrid": True,
            "gridwidth": 1,
            "gridcolor": "rgba(0,0,0,0.1)",
            "tickfont": {"size": 10},
            "tickangle": 45,
        },
        "yaxis": {
            "title": "",
            "showgrid": True,
            "gridwidth": 1,
            "gridcolor": "rgba(0,0,0,0.1)",
            "tickfont": {"size": 10},
        },
    }


def get_performance_zones(metric_name: str) -> list[dict[str, Any]]:

    zones = {
        "deployment_frequency": [
            {
                "y0": 30,
                "y1": 1000,
                "color": "rgba(25, 135, 84, 0.1)",
                "label": "Elite (≥30/mo)",
            },
            {
                "y0": 7,
                "y1": 30,
                "color": "rgba(13, 110, 253, 0.1)",
                "label": "High (7-30/mo)",
            },
            {
                "y0": 1,
                "y1": 7,
                "color": "rgba(255, 193, 7, 0.1)",
                "label": "Medium (1-7/mo)",
            },
            {
                "y0": 0,
                "y1": 1,
                "color": "rgba(220, 53, 69, 0.1)",
                "label": "Low (<1/mo)",
            },
        ],
        "lead_time_for_changes": [
            {
                "y0": 0,
                "y1": 1,
                "color": "rgba(25, 135, 84, 0.1)",
                "label": "Elite (<1d)",
            },
            {
                "y0": 1,
                "y1": 7,
                "color": "rgba(13, 110, 253, 0.1)",
                "label": "High (1-7d)",
            },
            {
                "y0": 7,
                "y1": 30,
                "color": "rgba(255, 193, 7, 0.1)",
                "label": "Medium (1w-1mo)",
            },
            {
                "y0": 30,
                "y1": 365,
                "color": "rgba(220, 53, 69, 0.1)",
                "label": "Low (>1mo)",
            },
        ],
        "change_failure_rate": [
            {
                "y0": 0,
                "y1": 15,
                "color": "rgba(25, 135, 84, 0.1)",
                "label": "Elite (0-15%)",
            },
            {
                "y0": 15,
                "y1": 30,
                "color": "rgba(13, 110, 253, 0.1)",
                "label": "High (16-30%)",
            },
            {
                "y0": 30,
                "y1": 45,
                "color": "rgba(255, 193, 7, 0.1)",
                "label": "Medium (31-45%)",
            },
            {
                "y0": 45,
                "y1": 100,
                "color": "rgba(220, 53, 69, 0.1)",
                "label": "Low (>45%)",
            },
        ],
        "mttr": [
            {
                "y0": 0,
                "y1": 24,
                "color": "rgba(25, 135, 84, 0.1)",
                "label": "Elite (<1d)",
            },
            {
                "y0": 24,
                "y1": 168,
                "color": "rgba(13, 110, 253, 0.1)",
                "label": "High (1-7d)",
            },
            {
                "y0": 168,
                "y1": 720,
                "color": "rgba(255, 193, 7, 0.1)",
                "label": "Medium (1w-1mo)",
            },
            {
                "y0": 720,
                "y1": 8760,
                "color": "rgba(220, 53, 69, 0.1)",
                "label": "Low (>1mo)",
            },
        ],
    }

    return zones.get(metric_name, [])


def get_consistent_colors() -> dict[str, str]:

    return {
        "deployment_frequency": "#0d6efd",
        "lead_time_for_changes": "#198754",
        "change_failure_rate": "#dc3545",
        "mttr": "#fd7e14",
        "flow_velocity": "#6f42c1",
        "flow_time": "#6f42c1",
        "flow_efficiency": "#198754",
        "flow_load": "#6f42c1",
        "feature": "#198754",
        "defect": "#dc3545",
        "tech_debt": "#fd7e14",
        "risk": "#ffc107",
    }
