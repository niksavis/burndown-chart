import pandas as pd

from data.schema import DEFAULT_SETTINGS
from utils.caching import memoize


@memoize(max_age_seconds=300)
def calculate_rates(
    grouped: pd.DataFrame,
    total_items: float,
    total_points: float,
    pert_factor: int,
    show_points: bool = True,
    performance_settings: dict | None = None,
) -> tuple[float, float, float, float, float, float]:

    if performance_settings is None:
        performance_settings = {
            "forecast_max_days": DEFAULT_SETTINGS.get("forecast_max_days", 730),
            "pessimistic_multiplier_cap": DEFAULT_SETTINGS.get(
                "pessimistic_multiplier_cap", 5
            ),
        }

    days_per_week = 7.0

    if grouped is None or len(grouped) == 0:
        return 0, 0, 0, 0, 0, 0

    grouped_items_filtered = grouped[grouped["completed_items"] > 0].copy()
    grouped_points_filtered = grouped[grouped["completed_points"] > 0].copy()

    has_items_data = len(grouped_items_filtered) > 0
    has_points_data = len(grouped_points_filtered) > 0

    if not has_items_data and not has_points_data:
        return 0, 0, 0, 0, 0, 0

    days_per_week = 7.0

    if has_items_data:
        valid_items_count = len(grouped_items_filtered)

        if valid_items_count <= 3:
            most_likely_items_rate = (
                grouped_items_filtered["completed_items"].mean() / days_per_week
            )
            optimistic_items_rate = most_likely_items_rate
            pessimistic_items_rate = most_likely_items_rate
        else:
            valid_pert_factor = int(min(pert_factor, max(1, valid_items_count // 3)))
            valid_pert_factor = max(valid_pert_factor, 1)

            optimistic_items_rate = (
                grouped_items_filtered["completed_items"]
                .nlargest(valid_pert_factor)
                .mean()
                / days_per_week
            )
            pessimistic_items_rate = (
                grouped_items_filtered["completed_items"]
                .nsmallest(valid_pert_factor)
                .mean()
                / days_per_week
            )
            most_likely_items_rate = (
                grouped_items_filtered["completed_items"].mean() / days_per_week
            )

        optimistic_items_rate = max(0.001, optimistic_items_rate)
        pessimistic_items_rate = max(0.001, pessimistic_items_rate)
        most_likely_items_rate = max(0.001, most_likely_items_rate)
    else:
        optimistic_items_rate = 0.001
        pessimistic_items_rate = 0.001
        most_likely_items_rate = 0.001

    if has_points_data:
        valid_points_count = len(grouped_points_filtered)

        if valid_points_count <= 3:
            most_likely_points_rate = (
                grouped_points_filtered["completed_points"].mean() / days_per_week
            )
            optimistic_points_rate = most_likely_points_rate
            pessimistic_points_rate = most_likely_points_rate
        else:
            valid_pert_factor = int(min(pert_factor, max(1, valid_points_count // 3)))
            valid_pert_factor = max(valid_pert_factor, 1)

            optimistic_points_rate = (
                grouped_points_filtered["completed_points"]
                .nlargest(valid_pert_factor)
                .mean()
                / days_per_week
            )
            pessimistic_points_rate = (
                grouped_points_filtered["completed_points"]
                .nsmallest(valid_pert_factor)
                .mean()
                / days_per_week
            )
            most_likely_points_rate = (
                grouped_points_filtered["completed_points"].mean() / days_per_week
            )

        optimistic_points_rate = max(0.001, optimistic_points_rate)
        pessimistic_points_rate = max(0.001, pessimistic_points_rate)
        most_likely_points_rate = max(0.001, most_likely_points_rate)
    else:
        optimistic_points_rate = 0.001
        pessimistic_points_rate = 0.001
        most_likely_points_rate = 0.001

    optimistic_time_items = (
        total_items / optimistic_items_rate if optimistic_items_rate else float("inf")
    )
    most_likely_time_items = (
        total_items / most_likely_items_rate if most_likely_items_rate else float("inf")
    )
    pessimistic_time_items = (
        total_items / pessimistic_items_rate if pessimistic_items_rate else float("inf")
    )

    optimistic_time_points = (
        total_points / optimistic_points_rate
        if optimistic_points_rate
        else float("inf")
    )
    most_likely_time_points = (
        total_points / most_likely_points_rate
        if most_likely_points_rate
        else float("inf")
    )
    pessimistic_time_points = (
        total_points / pessimistic_points_rate
        if pessimistic_points_rate
        else float("inf")
    )

    pert_time_items = (
        optimistic_time_items + 4 * most_likely_time_items + pessimistic_time_items
    ) / 6
    pert_time_points = (
        optimistic_time_points + 4 * most_likely_time_points + pessimistic_time_points
    ) / 6

    import logging  # noqa: PLC0415

    logger = logging.getLogger(__name__)
    logger.info(
        f"[PERT CALC] Inputs: total_items={total_items}, total_points={total_points}, "
        f"valid_data_weeks={len(grouped_items_filtered) if has_items_data else 0}"
    )
    logger.info(
        "[PERT CALC] Rates - Items: "
        f"opt={optimistic_items_rate:.4f}, "
        f"likely={most_likely_items_rate:.4f}, "
        f"pes={pessimistic_items_rate:.4f}"
    )
    logger.info(
        "[PERT CALC] Rates - Points: "
        f"opt={optimistic_points_rate:.4f}, "
        f"likely={most_likely_points_rate:.4f}, "
        f"pes={pessimistic_points_rate:.4f}"
    )
    logger.info(
        "[PERT CALC] Results: "
        f"pert_time_items={pert_time_items:.2f}, "
        f"pert_time_points={pert_time_points:.2f}"
    )

    MAX_ESTIMATED_DAYS = performance_settings.get("forecast_max_days", 730)
    pert_time_items = min(pert_time_items, MAX_ESTIMATED_DAYS)
    pert_time_points = min(pert_time_points, MAX_ESTIMATED_DAYS)

    MAX_PESSIMISTIC_MULTIPLIER = performance_settings.get(
        "pessimistic_multiplier_cap", 5
    )
    if optimistic_time_items > 0:
        max_pessimistic_items = optimistic_time_items * MAX_PESSIMISTIC_MULTIPLIER
        if pessimistic_time_items > max_pessimistic_items:
            pessimistic_time_items = max_pessimistic_items
            pert_time_items = (
                optimistic_time_items
                + 4 * most_likely_time_items
                + pessimistic_time_items
            ) / 6

    if optimistic_time_points > 0:
        max_pessimistic_points = optimistic_time_points * MAX_PESSIMISTIC_MULTIPLIER
        if pessimistic_time_points > max_pessimistic_points:
            pessimistic_time_points = max_pessimistic_points
            pert_time_points = (
                optimistic_time_points
                + 4 * most_likely_time_points
                + pessimistic_time_points
            ) / 6

    return (
        pert_time_items,
        optimistic_items_rate,
        pessimistic_items_rate,
        pert_time_points,
        optimistic_points_rate,
        pessimistic_points_rate,
    )
