from typing import Any
from unittest.mock import patch

import pandas as pd

import ui.dashboard.utils as health_boundary
from callbacks.visualization_helpers.dashboard_tab import _render_dashboard_tab
from data.persistence import load_app_settings, load_unified_project_data


def observe_mounted_health() -> dict:
    observed: dict[str, Any] = {}
    producer = health_boundary.calculate_comprehensive_project_health

    def calculate(**kwargs: Any) -> dict:
        observed["inputs"] = kwargs
        observed["result"] = producer(**kwargs)
        observed["available"] = {
            name: isinstance(value, dict) and value.get("has_data") is True
            for name, value in kwargs.items()
        }
        return observed["result"]

    frame = pd.DataFrame(load_unified_project_data()["statistics"])
    with patch.object(
        health_boundary, "calculate_comprehensive_project_health", side_effect=calculate
    ):
        _render_dashboard_tab(frame, load_app_settings(), show_points=True)
    if not observed:
        raise ValueError("Dashboard did not call the comprehensive health producer")
    return observed
