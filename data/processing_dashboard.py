from datetime import datetime, timedelta

import pandas as pd

from data.processing_core import calculate_velocity_from_dataframe


def calculate_dashboard_metrics(statistics: list, settings: dict) -> dict:

    metrics = {
        "completion_forecast_date": None,
        "completion_confidence": None,
        "days_to_completion": None,
        "days_to_deadline": None,
        "completion_percentage": 0.0,
        "remaining_items": 0,
        "remaining_points": 0.0,
        "current_velocity_items": 0.0,
        "current_velocity_points": 0.0,
        "velocity_trend": "unknown",
        "last_updated": datetime.now().isoformat(),
    }

    if not statistics or len(statistics) == 0:
        return metrics

    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    if df.empty:
        return metrics

    total_items = settings.get("estimated_total_items", 0) or 0
    total_points = settings.get("estimated_total_points", 0) or 0

    completed_items = df["completed_items"].sum()
    completed_points = df["completed_points"].sum()

    metrics["remaining_items"] = max(0, int(total_items - completed_items))
    metrics["remaining_points"] = max(0.0, float(total_points - completed_points))

    if total_items > 0:
        metrics["completion_percentage"] = round(
            (completed_items / total_items) * 100, 1
        )

    data_points_count = min(len(df), int(settings.get("data_points_count", 10)))

    if data_points_count > 0 and not df.empty:
        latest_date = df["date"].max()
        cutoff_date = latest_date - timedelta(weeks=data_points_count)
        recent_data = df[df["date"] > cutoff_date]
    else:
        recent_data = df

    if len(recent_data) > 0:
        metrics["current_velocity_items"] = calculate_velocity_from_dataframe(
            recent_data, "completed_items"
        )
        metrics["current_velocity_points"] = calculate_velocity_from_dataframe(
            recent_data, "completed_points"
        )

    if len(df) >= 6:
        mid_point = len(df) // 2
        older_half = df.iloc[:mid_point]
        recent_half = df.iloc[mid_point:]

        older_velocity = calculate_velocity_from_dataframe(
            older_half, "completed_items"
        )
        recent_velocity = calculate_velocity_from_dataframe(
            recent_half, "completed_items"
        )

        if older_velocity > 0:
            velocity_change = (recent_velocity - older_velocity) / older_velocity

            if velocity_change > 0.1:
                metrics["velocity_trend"] = "increasing"
            elif velocity_change < -0.1:
                metrics["velocity_trend"] = "decreasing"
            else:
                metrics["velocity_trend"] = "stable"

    if metrics["current_velocity_items"] > 0 and metrics["remaining_items"] > 0:
        pert_factor = settings.get("pert_factor", 1.5)
        weeks_remaining = (
            metrics["remaining_items"] / metrics["current_velocity_items"]
        ) * pert_factor
        days_remaining = int(weeks_remaining * 7)

        last_date = df["date"].max()
        forecast_date = last_date + timedelta(days=days_remaining)

        metrics["completion_forecast_date"] = forecast_date.strftime("%Y-%m-%d")
        metrics["days_to_completion"] = days_remaining

        if len(recent_data) >= 3:
            velocity_std = recent_data["completed_items"].std()
            velocity_mean = recent_data["completed_items"].mean()

            if velocity_mean > 0:
                coefficient_of_variation = velocity_std / velocity_mean
                confidence = max(0, min(100, 100 - (coefficient_of_variation * 100)))
                metrics["completion_confidence"] = round(confidence, 1)

    deadline = settings.get("deadline")
    if deadline:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            days_to_deadline = (deadline_date - datetime.now()).days
            metrics["days_to_deadline"] = days_to_deadline
        except ValueError, TypeError:
            pass

    return metrics


def calculate_pert_timeline(statistics: list, settings: dict) -> dict:

    timeline = {
        "optimistic_date": None,
        "pessimistic_date": None,
        "most_likely_date": None,
        "pert_estimate_date": None,
        "optimistic_days": 0,
        "pessimistic_days": 0,
        "most_likely_days": 0,
        "confidence_range_days": 0,
    }

    if not statistics or len(statistics) == 0:
        return timeline

    metrics = calculate_dashboard_metrics(statistics, settings)

    if metrics["current_velocity_items"] <= 0 or metrics["remaining_items"] <= 0:
        return timeline

    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    reference_date = df["date"].max()

    base_weeks = metrics["remaining_items"] / metrics["current_velocity_items"]

    pert_factor = settings.get("pert_factor", 1.5)

    optimistic_weeks = base_weeks / pert_factor
    optimistic_days = int(optimistic_weeks * 7)
    timeline["optimistic_days"] = optimistic_days
    timeline["optimistic_date"] = (
        reference_date + timedelta(days=optimistic_days)
    ).strftime("%Y-%m-%d")

    most_likely_days = int(base_weeks * 7)
    timeline["most_likely_days"] = most_likely_days
    timeline["most_likely_date"] = (
        reference_date + timedelta(days=most_likely_days)
    ).strftime("%Y-%m-%d")

    pessimistic_weeks = base_weeks * pert_factor
    pessimistic_days = int(pessimistic_weeks * 7)
    timeline["pessimistic_days"] = pessimistic_days
    timeline["pessimistic_date"] = (
        reference_date + timedelta(days=pessimistic_days)
    ).strftime("%Y-%m-%d")

    pert_days = int((optimistic_days + 4 * most_likely_days + pessimistic_days) / 6)
    timeline["pert_estimate_date"] = (
        reference_date + timedelta(days=pert_days)
    ).strftime("%Y-%m-%d")

    timeline["confidence_range_days"] = pessimistic_days - optimistic_days

    return timeline
