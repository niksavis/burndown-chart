import pandas as pd

from data.persistence import load_unified_project_data
from data.scope_metrics import (
    calculate_scope_change_rate,
    calculate_scope_stability_index,
    calculate_weekly_scope_growth,
    check_scope_change_threshold,
)


def scope_calculations(source: str) -> dict:
    frame = pd.DataFrame(load_unified_project_data()["statistics"])
    if source == "scope-zero-baseline":
        return {
            "growth": calculate_scope_change_rate(frame, 0, 0, 8),
            "stability": calculate_scope_stability_index(frame, 0, 0, 8),
        }
    if source == "scope-threshold-calibration":
        growth = calculate_scope_change_rate(frame, 48, 96, 8)
        return {"growth": growth, "threshold": check_scope_change_threshold(growth, 25)}
    if source == "scope-weekly-growth":
        return {
            row["week_label"]: row
            for row in calculate_weekly_scope_growth(frame, 8).to_dict("records")
        }
    raise ValueError(f"Unknown scope diagnostic source: {source}")
