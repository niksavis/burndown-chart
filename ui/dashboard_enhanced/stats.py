import pandas as pd
from scipy import stats


def _calculate_velocity_statistics(
    statistics_df: pd.DataFrame, metric_type: str = "items"
) -> dict:
    if statistics_df.empty:
        return {
            "mean": 0,
            "median": 0,
            "std_dev": 0,
            "cv": 0,
            "recent_avg": 0,
            "recent_change": 0,
            "sparkline_data": [],
        }

    col_name = f"completed_{metric_type}"
    if col_name not in statistics_df.columns:
        return {
            "mean": 0,
            "median": 0,
            "std_dev": 0,
            "cv": 0,
            "recent_avg": 0,
            "recent_change": 0,
            "sparkline_data": [],
        }

    data = statistics_df[col_name]
    mean_vel = data.mean()
    std_dev = data.std()
    cv = (std_dev / mean_vel * 100) if mean_vel > 0 else 0

    recent_avg = data.tail(4).mean() if len(data) >= 4 else mean_vel
    historical_avg = data.head(-4).mean() if len(data) > 4 else mean_vel
    recent_change = (
        ((recent_avg - historical_avg) / historical_avg * 100)
        if historical_avg > 0
        else 0
    )

    return {
        "mean": mean_vel,
        "median": data.median(),
        "std_dev": std_dev,
        "cv": cv,
        "recent_avg": recent_avg,
        "recent_change": recent_change,
        "sparkline_data": list(data.tail(10)),
    }


def _calculate_confidence_intervals(
    pert_forecast_days: float,
    velocity_mean: float,
    velocity_std: float,
    remaining_work: float,
) -> dict:

    if velocity_mean == 0 or velocity_std == 0:
        return {
            "ci_50": pert_forecast_days,
            "ci_80": pert_forecast_days,
            "ci_95": pert_forecast_days,
        }

    cv = velocity_std / velocity_mean

    forecast_std = cv * pert_forecast_days

    ci_50 = pert_forecast_days
    ci_80 = pert_forecast_days + (0.84 * forecast_std)
    ci_95 = pert_forecast_days + (1.65 * forecast_std)

    return {"ci_50": max(0, ci_50), "ci_80": max(0, ci_80), "ci_95": max(0, ci_95)}


def _calculate_deadline_probability(
    days_to_deadline: float,
    pert_forecast_days: float,
    velocity_std: float,
    velocity_mean: float,
) -> float:

    if velocity_mean == 0:
        return 50.0

    cv = velocity_std / velocity_mean
    forecast_std_days = cv * pert_forecast_days

    if forecast_std_days == 0:
        return 100.0 if days_to_deadline >= pert_forecast_days else 0.0

    z = (days_to_deadline - pert_forecast_days) / forecast_std_days

    probability = float(stats.norm.cdf(z)) * 100

    return max(0.0, min(100.0, probability))


def _assess_project_health(
    velocity_cv: float,
    days_to_deadline: float,
    pert_forecast_days: float,
    recent_velocity_change: float,
    capacity_gap_percent: float,
) -> dict:
    factors = []

    if velocity_cv < 25:
        factors.append(
            {"name": "Velocity Predictable", "status": "good", "icon": "[OK]"}
        )
    elif velocity_cv < 40:
        factors.append(
            {"name": "Velocity Moderately Stable", "status": "warning", "icon": "[!]"}
        )
    else:
        factors.append(
            {"name": "Velocity Unpredictable", "status": "bad", "icon": "[X]"}
        )

    schedule_delta = pert_forecast_days - days_to_deadline
    if schedule_delta <= 0:
        factors.append({"name": "On Schedule", "status": "good", "icon": "[OK]"})
    elif schedule_delta <= 14:
        factors.append({"name": "Slightly Behind", "status": "warning", "icon": "[!]"})
    else:
        factors.append({"name": "Behind Schedule", "status": "bad", "icon": "[X]"})

    if recent_velocity_change >= 5:
        factors.append({"name": "Velocity Improving", "status": "good", "icon": "[OK]"})
    elif recent_velocity_change >= -5:
        factors.append({"name": "Velocity Stable", "status": "good", "icon": "[OK]"})
    else:
        factors.append(
            {"name": "Velocity Declining", "status": "warning", "icon": "[!]"}
        )

    if capacity_gap_percent >= -10:
        factors.append({"name": "Adequate Capacity", "status": "good", "icon": "[OK]"})
    elif capacity_gap_percent >= -25:
        factors.append(
            {"name": "Capacity Stretched", "status": "warning", "icon": "[!]"}
        )
    else:
        factors.append({"name": "Capacity Shortfall", "status": "bad", "icon": "[X]"})

    good_count = sum(1 for f in factors if f["status"] == "good")
    bad_count = sum(1 for f in factors if f["status"] == "bad")

    if good_count >= 3:
        overall = {
            "level": "healthy",
            "color": "#28a745",
            "emoji": "[OK]",
            "label": "HEALTHY",
        }
    elif bad_count >= 2:
        overall = {
            "level": "at_risk",
            "color": "#dc3545",
            "emoji": "[X]",
            "label": "AT RISK",
        }
    else:
        overall = {
            "level": "moderate",
            "color": "#ffc107",
            "emoji": "[!]",
            "label": "MODERATE",
        }

    return {"overall": overall, "factors": factors}
