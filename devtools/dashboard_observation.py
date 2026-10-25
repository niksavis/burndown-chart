from unittest.mock import patch

import pandas as pd

import ui.dashboard as dashboard
from data.persistence import load_app_settings, load_unified_project_data
from ui.dashboard_enhanced.stats import _calculate_velocity_statistics


def observe_mounted_confidence() -> dict:
    frame = pd.DataFrame(load_unified_project_data()["statistics"])
    frame["date"] = pd.to_datetime(frame["date"])
    items = _calculate_velocity_statistics(frame)
    points = _calculate_velocity_statistics(frame, "points")
    days = 28 if items["mean"] > 0 else 0
    deadline = load_app_settings().get("deadline")
    renderer = dashboard.create_forecast_analytics_section
    with patch.object(
        dashboard, "create_forecast_analytics_section", wraps=renderer
    ) as observed:
        dashboard.create_comprehensive_dashboard(
            frame,
            frame,
            days,
            days,
            items["mean"],
            points["mean"],
            items["median"],
            points["median"],
            28 if deadline else 0,
            16,
            32,
            deadline,
            show_points=True,
            data_points_count=len(frame),
        )
    return observed.call_args.args[1]
