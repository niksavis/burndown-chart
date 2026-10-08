from datetime import datetime, timedelta


def daily_forecast(
    start_val: float,
    daily_rate: float,
    start_date: datetime,
    max_days: int = 3653,
    max_points: int = 150,
) -> tuple[list[datetime], list[float]]:

    if daily_rate < 0.001:
        daily_rate = 0.001

    if daily_rate <= 0:
        return [start_date], [start_val]

    today = datetime.now()
    absolute_max_date = today + timedelta(days=3653)
    MAX_FORECAST_DAYS = min(max_days, 3653)

    x_vals, y_vals = [], []
    val = start_val
    current_date = start_date

    days_needed = val / daily_rate if daily_rate > 0 else 0

    if days_needed > MAX_FORECAST_DAYS:
        days_needed = MAX_FORECAST_DAYS

    MAX_POINTS = max_points

    if days_needed > MAX_FORECAST_DAYS:
        days_needed = MAX_FORECAST_DAYS

    if days_needed > MAX_POINTS:
        sample_interval = max(7, int(days_needed / MAX_POINTS))
    else:
        sample_interval = 1

    days_elapsed = 0
    while val > 0 and days_elapsed <= days_needed and current_date <= absolute_max_date:
        x_vals.append(current_date)
        y_vals.append(val)

        days_elapsed += sample_interval
        val -= daily_rate * sample_interval
        current_date += timedelta(days=sample_interval)

        if len(x_vals) > MAX_POINTS:
            break

    if val <= 0 and current_date <= absolute_max_date and len(x_vals) <= MAX_POINTS:
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

    if current >= target_scope:
        return ([start_date], [current])

    if daily_rate <= 0:
        return ([start_date], [current])

    if daily_rate < 0.001:
        daily_rate = 0.001

    today = datetime.now()
    absolute_max_date = today + timedelta(days=3653)

    remaining = target_scope - current
    days_needed = int(remaining / daily_rate) + 1

    MAX_FORECAST_DAYS = min(max_days, 3653)
    MAX_POINTS = max_points

    if days_needed > MAX_FORECAST_DAYS:
        days_needed = MAX_FORECAST_DAYS

    if days_needed > MAX_POINTS:
        sample_interval = max(7, int(days_needed / MAX_POINTS))
    else:
        sample_interval = 1

    dates = []
    values = []

    days_elapsed = 0
    while days_elapsed <= days_needed:
        forecast_date = start_date + timedelta(days=days_elapsed)

        if forecast_date > absolute_max_date:
            break

        forecast_val = min(target_scope, current + (daily_rate * days_elapsed))

        dates.append(forecast_date)
        values.append(forecast_val)

        if forecast_val >= target_scope:
            break

        days_elapsed += sample_interval

        if len(dates) > MAX_POINTS:
            break

    if values and values[-1] < target_scope:
        final_date = start_date + timedelta(days=min(days_needed, MAX_FORECAST_DAYS))
        dates.append(final_date)
        values.append(target_scope)

    import logging  # noqa: PLC0415

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
