"""PERT rate-calculation logic for the Burndown application.

Computes optimistic, most-likely, and pessimistic burn rates from
historical weekly throughput using agile-adapted PERT methodology.
"""

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
    """
    Calculate burn rates using PERT methodology adapted for agile empirical data.

    PERT METHODOLOGY ADAPTATION FOR AGILE TEAMS
    ===========================================

    This implementation adapts traditional PERT
    (Program Evaluation and Review Technique)
    to agile contexts by using **historical velocity data** instead of expert estimates:

    **Traditional PERT:**
    - Optimistic (O): Expert's best-case estimate
    - Most Likely (M): Expert's most probable estimate
    - Pessimistic (P): Expert's worst-case estimate
    - Formula: Expected Time = (O + 4M + P) / 6

    **Our Agile Adaptation:**
    - Optimistic: Average of top N performing weeks (e.g., best 3 weeks)
      → Represents "if we maintain our best pace"
    - Most Likely: Average of ALL weeks
      → Represents "if we maintain average pace"
    - Pessimistic: Average of bottom N performing weeks (e.g., worst 3 weeks)
      → Represents "if we experience slower periods like we have before"
    - Formula: Same PERT weighted average (O + 4M + P) / 6

    **Why This Adaptation:**
    1. **Data-Driven:** Uses actual team performance, not subjective guesses
    2. **Adaptive:** Automatically adjusts to team's velocity characteristics
    3. **Empirical:** Captures real historical variance and patterns
    4. **Agile-Friendly:** Teams value measurements over estimates

    **Limitations and Appropriate Use:**

    [OK] **RECOMMENDED FOR:**
    - Short to medium term forecasts (2-12 weeks)
    - Teams with stable composition and workload
    - Projects with consistent workflow patterns
    - Contexts where empirical data is preferred over expert judgment

    [!] **USE WITH CAUTION FOR:**
    - Long-term forecasts (>6 months) - patterns may change
    - Teams undergoing major changes (new members, tech stack changes)
    - Projects with highly variable requirements
    - Seasonal projects with known cyclical patterns not yet captured in data

    [X] **NOT SUITABLE FOR:**
    - Brand new teams with <4 weeks of history
    - Projects with fundamentally different future work than past
    - One-time initiatives without recurring patterns

    **Key Assumption:** Future velocity will follow historical patterns within the
    observed range. This assumption weakens as forecast horizon increases.

    **Confidence Window (pert_factor):**
    The 'pert_factor' parameter (labeled "Confidence Window" in UI) determines how many
    weeks to sample for best/worst cases:
    - Smaller values (e.g., 2-3): More sensitive to extremes, wider forecast range
    - Larger values (e.g., 5-6): More stable, smoother forecasts
    - Auto-adjusted to max 1/3 of available data to prevent overfitting

    Args:
        grouped: DataFrame with weekly aggregated data
            (completed_items, completed_points)
        total_items: Total number of items remaining to complete
        total_points: Total number of points remaining to complete
        pert_factor: Number of weeks to sample for best/worst case (confidence window)
        show_points: Whether points tracking is enabled (default: True)
        performance_settings: Dictionary with performance optimization settings
            - forecast_max_days: Maximum forecast horizon (default: 730 days)
                        - pessimistic_multiplier_cap: Max ratio of pessimistic to
                            optimistic (default: 5)

    Returns:
        Tuple of calculated values (all in days):
        (pert_time_items, optimistic_items_rate, pessimistic_items_rate,
         pert_time_points, optimistic_points_rate, pessimistic_points_rate)

    Example:
        >>> grouped = pd.DataFrame({
        ...     'completed_items': [5, 7, 4, 6, 8, 5, 9, 7, 3, 10]
        ... })
        >>> rates = calculate_rates(
        ...     grouped, total_items=50, total_points=250, pert_factor=3
        ... )
        >>> # Returns PERT forecast considering best 3, worst 3,
        >>> # and average of all weeks
    """
    # Set default performance settings if not provided
    if performance_settings is None:
        performance_settings = {
            "forecast_max_days": DEFAULT_SETTINGS.get("forecast_max_days", 730),
            "pessimistic_multiplier_cap": DEFAULT_SETTINGS.get(
                "pessimistic_multiplier_cap", 5
            ),
        }

    days_per_week = 7.0

    # If no data or empty dataframe, return safe default values
    if grouped is None or len(grouped) == 0:
        # Return zeros to avoid calculations with empty data
        return 0, 0, 0, 0, 0, 0

    # CRITICAL: Filter out zero-value weeks before any calculations
    # Zero weeks (often from _fill_missing_weeks) should never influence
    # rate calculations.
    # They would otherwise lower pessimistic rates and extend
    # forecasts unrealistically.
    # Filter separately for items and points to support projects
    # with only one tracking type.
    grouped_items_filtered = grouped[grouped["completed_items"] > 0].copy()
    grouped_points_filtered = grouped[grouped["completed_points"] > 0].copy()

    # Determine which filtering to use based on available data
    has_items_data = len(grouped_items_filtered) > 0
    has_points_data = len(grouped_points_filtered) > 0

    # If neither has data, return zeros (insufficient data for forecasting)
    if not has_items_data and not has_points_data:
        return 0, 0, 0, 0, 0, 0

    # Always calculate rates properly for both items and points
    # The show_points parameter should only affect UI display, not calculation logic
    days_per_week = 7.0

    # Calculate items rates if data exists
    if has_items_data:
        valid_items_count = len(grouped_items_filtered)

        # When data is limited, adjust strategy to ensure stable results
        if valid_items_count <= 3:
            # With very few data points (≤3 weeks), use mean for all estimates
            most_likely_items_rate = (
                grouped_items_filtered["completed_items"].mean() / days_per_week
            )
            optimistic_items_rate = most_likely_items_rate
            pessimistic_items_rate = most_likely_items_rate
        else:
            # Normal case with sufficient data (4+ weeks)
            # CRITICAL: Ensure valid_pert_factor is integer for
            # .nlargest()/.nsmallest() operations.
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

        # Prevent zero rates
        optimistic_items_rate = max(0.001, optimistic_items_rate)
        pessimistic_items_rate = max(0.001, pessimistic_items_rate)
        most_likely_items_rate = max(0.001, most_likely_items_rate)
    else:
        # No items data - set rates to minimal values
        optimistic_items_rate = 0.001
        pessimistic_items_rate = 0.001
        most_likely_items_rate = 0.001

    # Calculate points rates if data exists
    if has_points_data:
        valid_points_count = len(grouped_points_filtered)

        if valid_points_count <= 3:
            most_likely_points_rate = (
                grouped_points_filtered["completed_points"].mean() / days_per_week
            )
            optimistic_points_rate = most_likely_points_rate
            pessimistic_points_rate = most_likely_points_rate
        else:
            # CRITICAL: Ensure valid_pert_factor is integer for
            # .nlargest()/.nsmallest() operations.
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

        # Prevent zero rates
        optimistic_points_rate = max(0.001, optimistic_points_rate)
        pessimistic_points_rate = max(0.001, pessimistic_points_rate)
        most_likely_points_rate = max(0.001, most_likely_points_rate)
    else:
        # No points data - set rates to minimal values
        optimistic_points_rate = 0.001
        pessimistic_points_rate = 0.001
        most_likely_points_rate = 0.001

    # Calculate time estimates for items
    optimistic_time_items = (
        total_items / optimistic_items_rate if optimistic_items_rate else float("inf")
    )
    most_likely_time_items = (
        total_items / most_likely_items_rate if most_likely_items_rate else float("inf")
    )
    pessimistic_time_items = (
        total_items / pessimistic_items_rate if pessimistic_items_rate else float("inf")
    )

    # Calculate time estimates for points
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

    # Apply standard PERT formula: (Optimistic + 4×Most_Likely + Pessimistic) / 6
    # The factor "4" is fixed in PERT methodology (NOT user-adjustable)
    # This weights the most likely scenario at 66.7%,
    # with optimistic and pessimistic at 16.7% each.
    pert_time_items = (
        optimistic_time_items + 4 * most_likely_time_items + pessimistic_time_items
    ) / 6
    pert_time_points = (
        optimistic_time_points + 4 * most_likely_time_points + pessimistic_time_points
    ) / 6

    # DEBUG: Log PERT calculation details
    import logging

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

    # Cap estimated time to reasonable maximum to prevent performance issues
    # Use configurable maximum from performance settings
    #
    # RATIONALE FOR 730-DAY (2-YEAR) DEFAULT CAP:
    # 1. Agile Forecasting Validity: Historical velocity patterns become
    #    unreliable beyond 6-12 months.
    # 2. Team/Technology Changes: Most agile teams experience
    #    significant changes within 2 years.
    # 3. Requirements Evolution: Project scope and priorities often shift substantially
    # 4. Chart Performance: Very long forecasts create rendering performance issues
    # 5. Actionable Timeframes: Forecasts beyond 2 years are
    #    rarely actionable for agile teams.
    #
    # Can be increased via settings, but 10-year absolute maximum enforced downstream
    # to prevent extreme performance degradation
    MAX_ESTIMATED_DAYS = performance_settings.get("forecast_max_days", 730)
    pert_time_items = min(pert_time_items, MAX_ESTIMATED_DAYS)
    pert_time_points = min(pert_time_points, MAX_ESTIMATED_DAYS)

    # Additional optimization: If pessimistic forecast is much longer than optimistic,
    # cap it to avoid extreme chart scaling issues
    #
    # RATIONALE FOR 5X PESSIMISTIC MULTIPLIER CAP:
    # 1. Velocity Variance Analysis: Typical agile teams show
    #    CV (coefficient of variation) of 0.2-0.5.
    #    - CV = 0.2: velocity varies ±20%, pessimistic ~1.5-2x optimistic
    #    - CV = 0.4: velocity varies ±40%, pessimistic ~2-3x optimistic
    #    - CV = 0.6: velocity varies ±60%, pessimistic ~3-4x optimistic
    # 2. Statistical Outliers: CV > 1.0 (100% variance) suggests data quality issues or
    #    extreme outliers that shouldn't drive forecasts
    # 3. Chart Usability: Pessimistic forecasts >5x optimistic create
    #    unusable chart scales.
    # 4. Predictability: If pessimistic is >5x optimistic, the team's velocity is too
    #    unstable for reliable forecasting - recommend improving process consistency
    #
    # ALTERNATIVE: Could use dynamic cap based on actual CV:
    # max_multiplier = max(3, min(10, 2 + (CV * 10)))
    # This would allow 3-10x range based on measured variance, but adds complexity
    MAX_PESSIMISTIC_MULTIPLIER = performance_settings.get(
        "pessimistic_multiplier_cap", 5
    )
    if optimistic_time_items > 0:
        max_pessimistic_items = optimistic_time_items * MAX_PESSIMISTIC_MULTIPLIER
        if pessimistic_time_items > max_pessimistic_items:
            pessimistic_time_items = max_pessimistic_items
            # Recalculate PERT with capped pessimistic
            pert_time_items = (
                optimistic_time_items
                + 4 * most_likely_time_items
                + pessimistic_time_items
            ) / 6

    if optimistic_time_points > 0:
        max_pessimistic_points = optimistic_time_points * MAX_PESSIMISTIC_MULTIPLIER
        if pessimistic_time_points > max_pessimistic_points:
            pessimistic_time_points = max_pessimistic_points
            # Recalculate PERT with capped pessimistic
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
