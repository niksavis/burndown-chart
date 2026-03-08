"""Dashboard metric and PERT timeline calculations.

Computes aggregated project health metrics and PERT completion-date
ranges for the Dashboard landing view.
"""

from datetime import datetime, timedelta

import pandas as pd

from data.processing_core import calculate_velocity_from_dataframe


def calculate_dashboard_metrics(statistics: list, settings: dict) -> dict:
    """
    Calculate aggregated project health metrics for Dashboard display.

    This function supports User Story 2: Dashboard as Primary Landing View.
    It computes all key metrics needed for the Dashboard tab including completion
    forecast, velocity, remaining work, and trend analysis.

    Args:
        statistics: List of statistics dictionaries with date,
            completed_items, completed_points
        settings: Settings dictionary with pert_factor, deadline, scope values

    Returns:
        dict: DashboardMetrics with all computed values (see data-model.md Section 3.1)

    Example:
        >>> stats = [
        ...     {
        ...         "date": "2025-01-01",
        ...         "completed_items": 5,
        ...         "completed_points": 25,
        ...     }
        ... ]
        >>> settings = {"pert_factor": 1.5, "deadline": "2025-12-31"}
        >>> metrics = calculate_dashboard_metrics(stats, settings)
        >>> print(metrics['days_to_completion'])
        53
    """

    # Initialize default metrics
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

    # Early return if no data
    if not statistics or len(statistics) == 0:
        return metrics

    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    if df.empty:
        return metrics

    # Calculate remaining work
    total_items = settings.get("estimated_total_items", 0) or 0
    total_points = settings.get("estimated_total_points", 0) or 0

    completed_items = df["completed_items"].sum()
    completed_points = df["completed_points"].sum()

    metrics["remaining_items"] = max(0, int(total_items - completed_items))
    metrics["remaining_points"] = max(0.0, float(total_points - completed_points))

    # Calculate completion percentage
    if total_items > 0:
        metrics["completion_percentage"] = round(
            (completed_items / total_items) * 100, 1
        )

    # Calculate current velocity (10-week rolling average or all available data)
    # CRITICAL FIX: Filter by actual date range, not row count
    data_points_count = min(len(df), int(settings.get("data_points_count", 10)))

    # Filter by actual weeks instead of row count
    if data_points_count > 0 and not df.empty:
        latest_date = df["date"].max()
        cutoff_date = latest_date - timedelta(weeks=data_points_count)
        recent_data = df[df["date"] > cutoff_date]
    else:
        recent_data = df

    # Calculate velocity using actual number of weeks (not date range)
    # This fixes the bug where sparse data would deflate velocity
    if len(recent_data) > 0:
        metrics["current_velocity_items"] = calculate_velocity_from_dataframe(
            recent_data, "completed_items"
        )
        metrics["current_velocity_points"] = calculate_velocity_from_dataframe(
            recent_data, "completed_points"
        )

    # Calculate velocity trend (compare recent vs. older data)
    if len(df) >= 6:  # Need at least 6 data points for trend
        mid_point = len(df) // 2
        older_half = df.iloc[:mid_point]
        recent_half = df.iloc[mid_point:]

        # Calculate velocity for each half using actual weeks (not date range)
        # This ensures trend comparison is reliable even with sparse data
        older_velocity = calculate_velocity_from_dataframe(
            older_half, "completed_items"
        )
        recent_velocity = calculate_velocity_from_dataframe(
            recent_half, "completed_items"
        )

        # Determine trend (>10% change is significant)
        if older_velocity > 0:
            velocity_change = (recent_velocity - older_velocity) / older_velocity

            if velocity_change > 0.1:
                metrics["velocity_trend"] = "increasing"
            elif velocity_change < -0.1:
                metrics["velocity_trend"] = "decreasing"
            else:
                metrics["velocity_trend"] = "stable"

    # Calculate forecast completion date
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

        # Calculate confidence based on velocity consistency (std dev)
        if len(recent_data) >= 3:
            velocity_std = recent_data["completed_items"].std()
            velocity_mean = recent_data["completed_items"].mean()

            # Confidence decreases with higher variability
            if velocity_mean > 0:
                coefficient_of_variation = velocity_std / velocity_mean
                # Convert to confidence: low CoV = high confidence
                confidence = max(0, min(100, 100 - (coefficient_of_variation * 100)))
                metrics["completion_confidence"] = round(confidence, 1)

    # Calculate days to deadline
    deadline = settings.get("deadline")
    if deadline:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            days_to_deadline = (deadline_date - datetime.now()).days
            metrics["days_to_deadline"] = days_to_deadline
        except (ValueError, TypeError):
            pass

    return metrics


def calculate_pert_timeline(statistics: list, settings: dict) -> dict:
    """
    Calculate PERT timeline data for Dashboard visualization.

    This function supports User Story 2: Dashboard as Primary Landing View.
    It computes optimistic, pessimistic, and most likely completion dates
    based on current velocity and PERT estimation technique.

    Args:
        statistics: List of statistics dictionaries
        settings: Settings dictionary with pert_factor and scope values

    Returns:
        dict: PERTTimelineData with forecast dates (see data-model.md Section 3.2)

    Example:
        >>> timeline = calculate_pert_timeline(stats, settings)
        >>> print(timeline['pert_estimate_date'])
        '2025-12-18'
    """

    # Initialize default timeline
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

    # Early return if no data
    if not statistics or len(statistics) == 0:
        return timeline

    # Get dashboard metrics for velocity and remaining work
    metrics = calculate_dashboard_metrics(statistics, settings)

    if metrics["current_velocity_items"] <= 0 or metrics["remaining_items"] <= 0:
        return timeline

    # Get reference date (last data point)
    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    reference_date = df["date"].max()

    # Calculate base weeks remaining
    base_weeks = metrics["remaining_items"] / metrics["current_velocity_items"]

    # Apply PERT scenarios
    pert_factor = settings.get("pert_factor", 1.5)

    # Optimistic: best case (divide by PERT factor)
    optimistic_weeks = base_weeks / pert_factor
    optimistic_days = int(optimistic_weeks * 7)
    timeline["optimistic_days"] = optimistic_days
    timeline["optimistic_date"] = (
        reference_date + timedelta(days=optimistic_days)
    ).strftime("%Y-%m-%d")

    # Most likely: baseline scenario
    most_likely_days = int(base_weeks * 7)
    timeline["most_likely_days"] = most_likely_days
    timeline["most_likely_date"] = (
        reference_date + timedelta(days=most_likely_days)
    ).strftime("%Y-%m-%d")

    # Pessimistic: worst case (multiply by PERT factor)
    pessimistic_weeks = base_weeks * pert_factor
    pessimistic_days = int(pessimistic_weeks * 7)
    timeline["pessimistic_days"] = pessimistic_days
    timeline["pessimistic_date"] = (
        reference_date + timedelta(days=pessimistic_days)
    ).strftime("%Y-%m-%d")

    # PERT weighted average: (O + 4M + P) / 6
    pert_days = int((optimistic_days + 4 * most_likely_days + pessimistic_days) / 6)
    timeline["pert_estimate_date"] = (
        reference_date + timedelta(days=pert_days)
    ).strftime("%Y-%m-%d")

    # Confidence range
    timeline["confidence_range_days"] = pessimistic_days - optimistic_days

    return timeline
