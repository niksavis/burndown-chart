"""Daily forecast generators for burndown and burnup charts.

Produces (dates, values) point sequences for both burndown
(remaining → 0) and burnup (current → target) trajectories.
"""

from datetime import datetime, timedelta


def daily_forecast(
    start_val: float,
    daily_rate: float,
    start_date: datetime,
    max_days: int = 3653,
    max_points: int = 150,
) -> tuple[list[datetime], list[float]]:
    """
    Generate daily forecast values from start to completion with adaptive sampling.

    Args:
        start_val: Starting value (remaining items/points)
        daily_rate: Daily completion rate
        start_date: Starting date for the forecast
        max_days: Maximum forecast horizon in days (default: 730)
        max_points: Maximum data points to generate (default: 150)

    Returns:
        Tuple of (x_values, y_values) for plotting
    """
    # If rate is too small, we'll hit timestamp limits; enforce a minimum
    if daily_rate < 0.001:
        daily_rate = 0.001

    # If rate is still effectively zero, return just the start point
    if daily_rate <= 0:
        return [start_date], [start_val]

    # ABSOLUTE HARD CAP: Never forecast beyond today + 10 years
    #
    # RATIONALE FOR 10-YEAR (3653-DAY) ABSOLUTE MAXIMUM:
    # 1. **Performance Protection**: Prevents app from becoming unresponsive when users
    #    accidentally configure extreme scenarios
    #    (e.g., 1 item/year velocity = 160+ year forecast).
    # 2. **Reality Check**: Any software forecast beyond 10 years is meaningless given:
    #    - Technology evolution cycles (3-5 years)
    #    - Team/organization changes
    #    - Product pivots and market shifts
    #    - Methodology improvements
    # 3. **Chart Usability**: Time axes beyond 10 years create
    #    unusable date labels and zoom ranges.
    # 4. **Data Validity**: Historical velocity data becomes
    #    irrelevant for such long horizons.
    # 5. **Industry Standards**: Most agile/project management tools cap at 1-5 years
    #
    # This is a HARD LIMIT that cannot be overridden to prevent
    # denial-of-service scenarios.
    # where bad data causes infinite-length chart rendering attempts
    today = datetime.now()
    absolute_max_date = today + timedelta(
        days=3653
    )  # 10 years from today (accounting for leap years)
    MAX_FORECAST_DAYS = min(max_days, 3653)  # Enforce 10-year absolute maximum

    x_vals, y_vals = [], []
    val = start_val
    current_date = start_date

    # Calculate expected end date
    days_needed = val / daily_rate if daily_rate > 0 else 0

    # STRICT ENFORCEMENT: Cap at 10 years absolute maximum for performance
    # This prevents visualization of 160+ year forecasts that make the app unresponsive
    if days_needed > MAX_FORECAST_DAYS:
        days_needed = MAX_FORECAST_DAYS

    # Performance optimization: Use adaptive sampling for long forecasts
    MAX_POINTS = max_points  # Use configurable maximum points

    if days_needed > MAX_FORECAST_DAYS:
        # For very long forecasts, cap strictly at maximum
        days_needed = MAX_FORECAST_DAYS

    # Determine sampling interval based on forecast length
    if days_needed > MAX_POINTS:
        # Use weekly sampling for long forecasts
        sample_interval = max(7, int(days_needed / MAX_POINTS))
    else:
        # Use daily sampling for shorter forecasts
        sample_interval = 1

    # Generate forecast with strict 10-year cap for visualization performance
    days_elapsed = 0
    while val > 0 and days_elapsed <= days_needed and current_date <= absolute_max_date:
        x_vals.append(current_date)
        y_vals.append(val)

        # Move forward by sample interval
        days_elapsed += sample_interval
        val -= daily_rate * sample_interval
        current_date += timedelta(days=sample_interval)

        # Safety check to prevent infinite loops and UI performance issues
        if len(x_vals) > MAX_POINTS:
            break

    # Add final zero point if we completed the forecast naturally (didn't hit limits)
    # and haven't exceeded the 10-year cap
    if val <= 0 and current_date <= absolute_max_date and len(x_vals) <= MAX_POINTS:
        # Add final zero point at the calculated completion date
        final_date = start_date + timedelta(days=min(days_needed, MAX_FORECAST_DAYS))
        if final_date <= absolute_max_date:
            x_vals.append(final_date)
            y_vals.append(0)

    return x_vals, y_vals


def daily_forecast_burnup(
    current,
    daily_rate,
    start_date,
    target_scope,
    max_days: int = 3653,
    max_points: int = 150,
):
    """
    Generate a daily burnup forecast from current completed work
    to target scope with adaptive sampling.

    Args:
        current: Current completed value (starting point)
        daily_rate: Daily completion rate
        start_date: Starting date for forecast
        target_scope: Target scope value to reach (upper limit)
        max_days: Maximum forecast horizon in days (default: 730)
        max_points: Maximum data points to generate (default: 150)

    Returns:
        Tuple of (dates, values) for the forecast
    """
    # If we've already reached target, return just the start point
    if current >= target_scope:
        return ([start_date], [current])

    # If rate is zero, return just the start point to match daily_forecast behavior
    if daily_rate <= 0:
        return ([start_date], [current])

    # If rate is too small, enforce a minimum to prevent overflow
    if daily_rate < 0.001:
        daily_rate = 0.001

    # ABSOLUTE HARD CAP: Never forecast beyond today + 10 years
    today = datetime.now()
    absolute_max_date = today + timedelta(
        days=3653
    )  # 10 years from today (accounting for leap years)

    # Calculate days needed to reach target scope
    remaining = target_scope - current
    days_needed = int(remaining / daily_rate) + 1  # Add 1 to ensure we reach target

    # Performance optimization: Use adaptive sampling and cap forecast horizon
    MAX_FORECAST_DAYS = min(max_days, 3653)  # Enforce 10-year absolute maximum
    MAX_POINTS = max_points  # Use configurable maximum points

    if days_needed > MAX_FORECAST_DAYS:
        # Cap at maximum forecast days
        days_needed = MAX_FORECAST_DAYS

    # Determine sampling interval based on forecast length
    if days_needed > MAX_POINTS:
        # Use weekly sampling for long forecasts
        sample_interval = max(7, int(days_needed / MAX_POINTS))
    else:
        # Use daily sampling for shorter forecasts
        sample_interval = 1

    # Generate forecast with strict 10-year cap for visualization performance
    dates = []
    values = []

    days_elapsed = 0
    while days_elapsed <= days_needed:
        forecast_date = start_date + timedelta(days=days_elapsed)

        # STRICT DATE CAP: Stop if we would exceed today + 10 years
        if forecast_date > absolute_max_date:
            break

        forecast_val = min(target_scope, current + (daily_rate * days_elapsed))

        dates.append(forecast_date)
        values.append(forecast_val)

        # If we've reached target scope, stop
        if forecast_val >= target_scope:
            break

        # Move forward by sample interval
        days_elapsed += sample_interval

        # Safety check to prevent too many points
        if len(dates) > MAX_POINTS:
            break

    # Ensure the last value reaches exactly the target scope if not already
    if values and values[-1] < target_scope:
        # Add final point at target scope
        final_date = start_date + timedelta(days=min(days_needed, MAX_FORECAST_DAYS))
        dates.append(final_date)
        values.append(target_scope)

    # Debug logging
    import logging

    logger = logging.getLogger(__name__)
    if dates:
        logger.info(
            "[BURNUP FORECAST] "
            f"start={start_date.strftime('%Y-%m-%d')}, "
            f"end={dates[-1].strftime('%Y-%m-%d')}, "
            f"days={(dates[-1] - start_date).days}, "
            f"target={target_scope:.1f}, daily_rate={daily_rate:.4f}, "
            f"sample_interval={sample_interval}, points_generated={len(dates)}"
        )

    return (dates, values)
