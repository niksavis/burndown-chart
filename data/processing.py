"""
Data Processing Module

This module handles all data transformation, calculation logic, and
forecasting algorithms for the burndown chart application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from datetime import datetime, timedelta

# Third-party library imports
import pandas as pd

# Application imports
from utils.caching import memoize

#######################################################################
# DATA PROCESSING FUNCTIONS
#######################################################################


def calculate_total_points(
    total_items: float,
    estimated_items: float,
    estimated_points: float,
    statistics_data: list[dict] | None = None,
    use_fallback: bool = True,
) -> tuple[float, float]:
    """
    Calculate the total points based on estimated points and items.

    Args:
        total_items: Total number of items in the project
        estimated_items: Number of items that have been estimated
        estimated_points: Number of points for the estimated items
        statistics_data: Optional historical data to use as fallback
        use_fallback: Whether to use fallback calculation when no estimates provided

    Returns:
        Tuple of (estimated_total_points, avg_points_per_item)
    """
    # Fix for edge case: When user explicitly sets estimated items/points to 0
    # and fallback is disabled, respect their intent and return 0
    if not use_fallback and estimated_items == 0 and estimated_points == 0:
        # User explicitly indicated no estimates available and no fallback wanted
        return 0.0, 0.0

    # Basic validation to prevent division by zero
    if estimated_items <= 0:
        # Use fallback behavior (historical data or defaults)
        if statistics_data and len(statistics_data) > 0:
            # Calculate average points per item from historical data
            df = pd.DataFrame(statistics_data)
            df["completed_items"] = pd.to_numeric(
                df["completed_items"], errors="coerce"
            ).fillna(0)
            df["completed_points"] = pd.to_numeric(
                df["completed_points"], errors="coerce"
            ).fillna(0)

            total_completed_items = df["completed_items"].sum()
            total_completed_points = df["completed_points"].sum()

            if total_completed_items > 0:
                avg_points_per_item = total_completed_points / total_completed_items
                estimated_total_points = total_items * avg_points_per_item
                return estimated_total_points, avg_points_per_item

        # Default to 10 points per item if no data available and fallback enabled
        if use_fallback:
            return total_items * 10, 10
        else:
            # No fallback - return zeros when no estimates provided
            return 0.0, 0.0

    # Calculate average points per item based on estimates
    avg_points_per_item = estimated_points / estimated_items

    # Calculate total points using the average
    estimated_total_points = total_items * avg_points_per_item

    return estimated_total_points, avg_points_per_item


def read_and_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare the input dataframe for analysis.

    Args:
        df: Pandas DataFrame with raw data

    Returns:
        Cleaned DataFrame with proper types and no missing values
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df.dropna(subset=["date"], inplace=True)
    df.sort_values("date", inplace=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")  # type: ignore[attr-defined]
    df["completed_items"] = pd.to_numeric(df["completed_items"], errors="coerce")
    df["completed_points"] = pd.to_numeric(df["completed_points"], errors="coerce")
    df.dropna(subset=["completed_items", "completed_points"], inplace=True)
    return df


def compute_cumulative_values(
    df: pd.DataFrame, total_items: float, total_points: float
) -> pd.DataFrame:
    """
    Compute cumulative values for items and points for burndown tracking.

    Args:
        df: DataFrame with historical data
        total_items: Total number of items to complete
        total_points: Total number of points to complete

    Returns:
        DataFrame with added cumulative columns
    """
    df = df.copy()

    # Make sure data is sorted by date in ascending order
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=True)

    # Convert to numeric in case there are any string values
    df["completed_items"] = pd.to_numeric(
        df["completed_items"], errors="coerce"
    ).fillna(0)
    df["completed_points"] = pd.to_numeric(
        df["completed_points"], errors="coerce"
    ).fillna(0)

    # Calculate cumulative sums from the end to the beginning
    # This gives us the remaining items/points at each data point
    # We reverse the dataframe, calculate cumulative sum, then reverse back
    reversed_items = df["completed_items"][::-1].cumsum()[::-1]
    reversed_points = df["completed_points"][::-1].cumsum()[::-1]

    # Calculate remaining items and points by adding the total to the reverse cumsum
    df["cum_items"] = reversed_items + total_items
    df["cum_points"] = reversed_points + total_points

    return df


def calculate_velocity_from_dataframe(
    df: pd.DataFrame, column: str = "completed_items"
) -> float:
    """Calculate velocity as items per week using actual number of weeks with data.

    This method counts the actual number of distinct weeks present in the data,
    rather than calculating the date range span. This produces accurate velocity
    when data is sparse or has gaps.

    **Why This Matters:**
    - Date range method: 2 weeks of data across 10-week span = items/10 (WRONG - deflates velocity)
    - Actual weeks method: 2 weeks of data = items/2 (CORRECT - accurate velocity)

    **Example:**
    ```
    Week 1: 10 items
    Week 10: 10 items
    Total: 20 items

    Date range method: 20 items / 9 weeks = 2.2 items/week [X]
    Actual weeks method: 20 items / 2 weeks = 10 items/week [OK]
    ```

    Args:
        df: DataFrame with 'date' column (datetime type) and data column
        column: Name of column to calculate velocity for (default: "completed_items")

    Returns:
        Velocity as items per week (rounded to 1 decimal place)

    Raises:
        KeyError: If df doesn't have 'date' or specified column

    Examples:
        >>> df = pd.DataFrame({
        ...     "date": pd.to_datetime(["2025-01-01", "2025-01-08", "2025-03-15"]),
        ...     "completed_items": [10, 15, 12]
        ... })
        >>> calculate_velocity_from_dataframe(df)
        12.3  # 37 items / 3 weeks
    """
    if df.empty or len(df) == 0:
        return 0.0

    # Validate required columns
    if "date" not in df.columns:
        raise KeyError("DataFrame must have 'date' column")
    if column not in df.columns:
        raise KeyError(f"DataFrame must have '{column}' column")

    # Count actual number of distinct weeks with data
    df_with_week = df.copy()
    # Use ISO week format: YYYY-WW (Monday-based weeks)
    df_with_week["week_year"] = df_with_week["date"].dt.strftime("%Y-%U")  # type: ignore[attr-defined]
    unique_weeks = df_with_week["week_year"].nunique()

    if unique_weeks == 0:
        return 0.0

    total = df[column].sum()
    return round(total / unique_weeks, 1)


def compute_weekly_throughput(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily data to weekly throughput for more stable calculations.

    Args:
        df: DataFrame with daily completion data

    Returns:
        DataFrame with weekly aggregated data
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["week"] = df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
    df["year"] = df["date"].dt.year  # type: ignore[attr-defined]
    df["year_week"] = df.apply(lambda r: f"{r['year']}-{r['week']}", axis=1)

    grouped = (
        df.groupby("year_week")
        .agg({"completed_items": "sum", "completed_points": "sum"})
        .reset_index()
    )
    return grouped


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

    This implementation adapts traditional PERT (Program Evaluation and Review Technique)
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
        grouped: DataFrame with weekly aggregated data (completed_items, completed_points)
        total_items: Total number of items remaining to complete
        total_points: Total number of points remaining to complete
        pert_factor: Number of weeks to sample for best/worst case (confidence window)
        show_points: Whether points tracking is enabled (default: True)
        performance_settings: Dictionary with performance optimization settings
            - forecast_max_days: Maximum forecast horizon (default: 730 days)
            - pessimistic_multiplier_cap: Max ratio of pessimistic to optimistic (default: 5)

    Returns:
        Tuple of calculated values (all in days):
        (pert_time_items, optimistic_items_rate, pessimistic_items_rate,
         pert_time_points, optimistic_points_rate, pessimistic_points_rate)

    Example:
        >>> grouped = pd.DataFrame({
        ...     'completed_items': [5, 7, 4, 6, 8, 5, 9, 7, 3, 10]
        ... })
        >>> rates = calculate_rates(grouped, total_items=50, total_points=250, pert_factor=3)
        >>> # Returns PERT forecast considering best 3, worst 3, and average of all weeks
    """
    # Set default performance settings if not provided
    if performance_settings is None:
        from data.schema import DEFAULT_SETTINGS

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

    # Always calculate rates properly for both items and points
    # The show_points parameter should only affect UI display, not calculation logic
    days_per_week = 7.0
    valid_data_count = len(grouped)

    # When data is limited, adjust strategy to ensure stable results
    if valid_data_count <= 3:
        # With very few data points (≤3 weeks), use mean for all estimates
        # This prevents unreliable forecasts when confidence window exceeds available data
        most_likely_items_rate = grouped["completed_items"].mean() / days_per_week
        most_likely_points_rate = grouped["completed_points"].mean() / days_per_week

        # Use the same value for optimistic and pessimistic to avoid erratic forecasts
        # with tiny datasets (no meaningful best/worst case distinction possible)
        optimistic_items_rate = most_likely_items_rate
        pessimistic_items_rate = most_likely_items_rate
        optimistic_points_rate = most_likely_points_rate
        pessimistic_points_rate = most_likely_points_rate
    else:
        # Normal case with sufficient data (4+ weeks)
        # Adjust confidence window to be at most 1/3 of available data for stable results
        # This ensures we're sampling meaningful best/worst cases without overfitting
        valid_pert_factor = min(pert_factor, max(1, valid_data_count // 3))
        valid_pert_factor = max(valid_pert_factor, 1)  # Ensure at least 1

        # Calculate daily rates for items using sampled weeks
        # Optimistic: Average of N best performing weeks
        optimistic_items_rate = (
            grouped["completed_items"].nlargest(valid_pert_factor).mean()
            / days_per_week
        )
        # Pessimistic: Average of N worst performing weeks
        pessimistic_items_rate = (
            grouped["completed_items"].nsmallest(valid_pert_factor).mean()
            / days_per_week
        )
        # Most Likely: Average of ALL weeks (not sampled)
        most_likely_items_rate = grouped["completed_items"].mean() / days_per_week

        # Calculate daily rates for points (same approach)
        optimistic_points_rate = (
            grouped["completed_points"].nlargest(valid_pert_factor).mean()
            / days_per_week
        )
        pessimistic_points_rate = (
            grouped["completed_points"].nsmallest(valid_pert_factor).mean()
            / days_per_week
        )
        most_likely_points_rate = grouped["completed_points"].mean() / days_per_week

    # Prevent any zero or negative rates that would cause division by zero errors
    # or negative time forecasts
    optimistic_items_rate = max(0.001, optimistic_items_rate)
    pessimistic_items_rate = max(0.001, pessimistic_items_rate)
    most_likely_items_rate = max(0.001, most_likely_items_rate)
    optimistic_points_rate = max(0.001, optimistic_points_rate)
    pessimistic_points_rate = max(0.001, pessimistic_points_rate)
    most_likely_points_rate = max(0.001, most_likely_points_rate)

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
    # This weights the most likely scenario at 66.7%, with optimistic and pessimistic at 16.7% each
    pert_time_items = (
        optimistic_time_items + 4 * most_likely_time_items + pessimistic_time_items
    ) / 6
    pert_time_points = (
        optimistic_time_points + 4 * most_likely_time_points + pessimistic_time_points
    ) / 6

    # Cap estimated time to reasonable maximum to prevent performance issues
    # Use configurable maximum from performance settings
    #
    # RATIONALE FOR 730-DAY (2-YEAR) DEFAULT CAP:
    # 1. Agile Forecasting Validity: Historical velocity patterns become unreliable beyond 6-12 months
    # 2. Team/Technology Changes: Most agile teams experience significant changes within 2 years
    # 3. Requirements Evolution: Project scope and priorities often shift substantially
    # 4. Chart Performance: Very long forecasts create rendering performance issues
    # 5. Actionable Timeframes: Forecasts beyond 2 years are rarely actionable for agile teams
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
    # 1. Velocity Variance Analysis: Typical agile teams show CV (coefficient of variation) of 0.2-0.5
    #    - CV = 0.2: velocity varies ±20%, pessimistic ~1.5-2x optimistic
    #    - CV = 0.4: velocity varies ±40%, pessimistic ~2-3x optimistic
    #    - CV = 0.6: velocity varies ±60%, pessimistic ~3-4x optimistic
    # 2. Statistical Outliers: CV > 1.0 (100% variance) suggests data quality issues or
    #    extreme outliers that shouldn't drive forecasts
    # 3. Chart Usability: Pessimistic forecasts >5x optimistic create unusable chart scales
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
    #    accidentally configure extreme scenarios (e.g., 1 item/year velocity = 160+ year forecast)
    # 2. **Reality Check**: Any software forecast beyond 10 years is meaningless given:
    #    - Technology evolution cycles (3-5 years)
    #    - Team/organization changes
    #    - Product pivots and market shifts
    #    - Methodology improvements
    # 3. **Chart Usability**: Time axes beyond 10 years create unusable date labels and zoom ranges
    # 4. **Data Validity**: Historical velocity data becomes irrelevant for such long horizons
    # 5. **Industry Standards**: Most agile/project management tools cap at 1-5 years
    #
    # This is a HARD LIMIT that cannot be overridden to prevent denial-of-service scenarios
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
    Generate a daily burnup forecast from current completed work to target scope with adaptive sampling.

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

    return (dates, values)


def calculate_weekly_averages(
    statistics_data: list[dict] | pd.DataFrame,
    data_points_count: int | None = None,  # NEW PARAMETER
) -> tuple[float, float, float, float]:
    """
    Calculate average and median weekly items and points for the last 10 weeks.

    Args:
        statistics_data: List of dictionaries containing statistics data
        data_points_count: Optional parameter to limit data to most recent N data points

    Returns:
        Tuple of (avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points)
    """
    # Ensure data_points_count is an integer (could be float from UI slider)
    if data_points_count is not None:
        data_points_count = int(data_points_count)

    # Check if statistics_data is empty or None
    if (
        statistics_data is None
        or (isinstance(statistics_data, pd.DataFrame) and statistics_data.empty)
        or (not isinstance(statistics_data, pd.DataFrame) and len(statistics_data) == 0)
    ):
        return 0, 0, 0, 0

    # Apply data points filtering before calculations
    if data_points_count is not None and data_points_count > 0:
        if (
            isinstance(statistics_data, list)
            and len(statistics_data) > data_points_count
        ):
            statistics_data = statistics_data[-data_points_count:]  # Take most recent
        elif (
            isinstance(statistics_data, pd.DataFrame)
            and len(statistics_data) > data_points_count
        ):
            statistics_data = statistics_data.tail(data_points_count)

    # Create DataFrame and ensure numeric types
    df = pd.DataFrame(statistics_data)
    df["completed_items"] = pd.to_numeric(
        df["completed_items"], errors="coerce"
    ).fillna(0)
    df["completed_points"] = pd.to_numeric(
        df["completed_points"], errors="coerce"
    ).fillna(0)

    # Convert date to datetime and ensure it's sorted chronologically
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])  # Remove rows with invalid dates
    df = df.sort_values("date", ascending=True)

    # Group by week to ensure consistent weekly aggregation
    df["week"] = df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
    df["year"] = df["date"].dt.year  # type: ignore[attr-defined]
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(
            items=("completed_items", "sum"),
            points=("completed_points", "sum"),
            start_date=("date", "min"),
        )
        .reset_index()
    )

    # Sort by date again to ensure chronological order after grouping
    weekly_df = weekly_df.sort_values("start_date")

    # Apply the 10-week limit only if data_points_count wasn't already applied
    # When data_points_count is specified, we already filtered the input data,
    # so use all the filtered weekly data
    if data_points_count is not None:
        recent_data = weekly_df  # Use all weeks from the filtered input
    else:
        # Legacy behavior: limit to last 10 weeks when no filtering specified
        recent_data = weekly_df.tail(10)

    # Calculate averages and medians
    avg_weekly_items = recent_data["items"].mean()
    avg_weekly_points = recent_data["points"].mean()
    med_weekly_items = recent_data["items"].median()
    med_weekly_points = recent_data[
        "points"
    ].median()  # Always round up to 2 decimal places (as float, not int)

    def round_up_2(x):
        # Ensure we're working with a float and preserve 2 decimal places
        return round(float(x), 2) if pd.notnull(x) else 0.0

    return (
        round_up_2(avg_weekly_items),
        round_up_2(avg_weekly_points),
        round_up_2(med_weekly_items),
        round_up_2(med_weekly_points),
    )


@memoize(max_age_seconds=300)
def generate_weekly_forecast(
    statistics_data: list[dict] | pd.DataFrame,
    pert_factor: int = 3,
    forecast_weeks: int = 1,
    data_points_count: int | None = None,  # NEW PARAMETER
) -> dict:
    """
    Generate a weekly forecast for items and points per week using PERT methodology.

    Args:
        statistics_data: List of dictionaries containing statistics data
        pert_factor: Number of data points to use for optimistic/pessimistic scenarios
        forecast_weeks: Number of weeks to forecast (default: 1)
        data_points_count: Optional parameter to limit data to most recent N data points

    Returns:
        Dictionary containing forecast data for items and points
    """
    # Ensure data_points_count is an integer (could be float from UI slider)
    if data_points_count is not None:
        data_points_count = int(data_points_count)

    # Apply data points filtering before forecast calculations
    if data_points_count is not None and data_points_count > 0:
        if (
            isinstance(statistics_data, list)
            and len(statistics_data) > data_points_count
        ):
            statistics_data = statistics_data[-data_points_count:]
        elif (
            isinstance(statistics_data, pd.DataFrame)
            and len(statistics_data) > data_points_count
        ):
            statistics_data = statistics_data.tail(data_points_count)

    # Create DataFrame from statistics data
    df = pd.DataFrame(statistics_data).copy()
    if df.empty:
        # Return empty forecast data if no historical data
        return {
            "items": {
                "dates": [],
                "most_likely": [],
                "optimistic": [],
                "pessimistic": [],
            },
            "points": {
                "dates": [],
                "most_likely": [],
                "optimistic": [],
                "pessimistic": [],
            },
        }

    # Convert date to datetime and ensure proper format
    df["date"] = pd.to_datetime(df["date"])

    # Ensure data is sorted chronologically
    df = df.sort_values("date", ascending=True)

    # Add week and year columns for grouping
    df["week"] = df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
    df["year"] = df["date"].dt.year  # type: ignore[attr-defined]
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(
            items=("completed_items", "sum"),
            points=("completed_points", "sum"),
            start_date=("date", "min"),
        )
        .reset_index()
    )

    # Sort by date
    weekly_df = weekly_df.sort_values("start_date")

    # Calculate PERT estimates for weekly items
    if len(weekly_df) > 0:
        valid_data_count = len(weekly_df)

        # Special handling for very small datasets
        if valid_data_count <= 3:
            # With very few data points, just use the mean for all estimates
            # This prevents crashes when pert_factor is 3 but we only have 1-3 data points
            most_likely_items = weekly_df["items"].mean()
            most_likely_points = weekly_df["points"].mean()

            # Use the same values for optimistic and pessimistic to avoid erratic forecasts
            # with tiny datasets
            optimistic_items = most_likely_items * 1.2  # Slightly optimistic
            pessimistic_items = max(
                0.1, most_likely_items * 0.8
            )  # Slightly pessimistic but positive

            optimistic_points = most_likely_points * 1.2  # Slightly optimistic
            pessimistic_points = max(
                0.1, most_likely_points * 0.8
            )  # Slightly pessimistic but positive
        else:
            # Adjust PERT factor to be at most 1/3 of available data for stable results
            # CRITICAL: Ensure valid_pert_factor is integer for .nlargest()/.nsmallest() operations
            valid_pert_factor = int(min(pert_factor, max(1, valid_data_count // 3)))
            valid_pert_factor = max(valid_pert_factor, 1)  # Ensure at least 1

            # Most likely: average of all data
            most_likely_items = weekly_df["items"].mean()

            # Optimistic: average of best performing weeks
            optimistic_items = weekly_df["items"].nlargest(valid_pert_factor).mean()

            # Pessimistic: average of worst performing weeks (excluding zeros)
            non_zero_items = weekly_df[weekly_df["items"] > 0]["items"]
            if len(non_zero_items) >= valid_pert_factor:
                pessimistic_items = non_zero_items.nsmallest(valid_pert_factor).mean()
            else:
                # If we don't have enough non-zero values, use min value or a percentage of most_likely
                pessimistic_items = (
                    non_zero_items.min()
                    if len(non_zero_items) > 0
                    else max(0.1, most_likely_items * 0.5)
                )

            # Same calculations for points
            most_likely_points = weekly_df["points"].mean()
            optimistic_points = weekly_df["points"].nlargest(valid_pert_factor).mean()

            non_zero_points = weekly_df[weekly_df["points"] > 0]["points"]
            if len(non_zero_points) >= valid_pert_factor:
                pessimistic_points = non_zero_points.nsmallest(valid_pert_factor).mean()
            else:
                # If we don't have enough non-zero values, use min value or a percentage of most_likely
                pessimistic_points = (
                    non_zero_points.min()
                    if len(non_zero_points) > 0
                    else max(0.1, most_likely_points * 0.5)
                )

        # Get the last date from historical data as starting point
        last_date = weekly_df["start_date"].max()

        # Generate the next week forecast date (ensuring proper progression)
        next_date = last_date + timedelta(weeks=1)

        # Format date for display - clear indication this is the next week
        formatted_date = next_date.strftime("%b %d")

        # Create forecast values for items (single week)
        most_likely_items_forecast = [most_likely_items]
        optimistic_items_forecast = [optimistic_items]
        pessimistic_items_forecast = [pessimistic_items]

        # Create forecast values for points (single week)
        most_likely_points_forecast = [most_likely_points]
        optimistic_points_forecast = [optimistic_points]
        pessimistic_points_forecast = [pessimistic_points]

        return {
            "items": {
                "dates": [formatted_date],
                "most_likely": most_likely_items_forecast,
                "optimistic": optimistic_items_forecast,
                "pessimistic": pessimistic_items_forecast,
                "most_likely_value": most_likely_items,
                "optimistic_value": optimistic_items,
                "pessimistic_value": pessimistic_items,
                "next_date": next_date,  # Include the actual date object for proper date progression
            },
            "points": {
                "dates": [formatted_date],
                "most_likely": most_likely_points_forecast,
                "optimistic": optimistic_points_forecast,  # Fixed: use optimistic_points_forecast instead of most_likely_points_forecast
                "pessimistic": pessimistic_points_forecast,
                "most_likely_value": most_likely_points,
                "optimistic_value": optimistic_points,
                "pessimistic_value": pessimistic_points,
                "next_date": next_date,  # Include the actual date object for proper date progression
            },
        }
    else:
        return {
            "items": {
                "dates": [],
                "most_likely": [],
                "optimistic": [],
                "pessimistic": [],
            },
            "points": {
                "dates": [],
                "most_likely": [],
                "optimistic": [],
                "pessimistic": [],
            },
        }


def calculate_performance_trend(
    statistics_data: list[dict] | pd.DataFrame,
    metric: str = "completed_items",
    weeks_to_compare: int = 4,
    data_points_count: int | None = None,  # NEW PARAMETER
) -> dict:
    """
    Calculate performance trend indicators based on historical data.

    Args:
        statistics_data: List of dictionaries containing statistics data
        metric: The metric to calculate trend for ("completed_items" or "completed_points")
        weeks_to_compare: Number of weeks to use for trend calculation
        data_points_count: Optional parameter to limit data to most recent N data points

    Returns:
        Dictionary containing trend data:
        - trend_direction: "up", "down", or "stable"
        - percent_change: Percentage change between periods
        - current_avg: Average value for current period
        - previous_avg: Average value for previous period
        - is_significant: True if change is >20%
    """
    # Ensure data_points_count is an integer (could be float from UI slider)
    if data_points_count is not None:
        data_points_count = int(data_points_count)

    # Apply data points filtering before trend calculations
    if data_points_count is not None and data_points_count > 0:
        if (
            isinstance(statistics_data, list)
            and len(statistics_data) > data_points_count
        ):
            statistics_data = statistics_data[-data_points_count:]
        elif (
            isinstance(statistics_data, pd.DataFrame)
            and len(statistics_data) > data_points_count
        ):
            statistics_data = statistics_data.tail(data_points_count)

    # Check if statistics_data is empty or None
    if (
        statistics_data is None
        or (isinstance(statistics_data, pd.DataFrame) and statistics_data.empty)
        or (
            not isinstance(statistics_data, pd.DataFrame)
            and len(statistics_data) < weeks_to_compare * 2
        )
    ):
        return {
            "trend_direction": "stable",
            "percent_change": 0,
            "current_avg": 0,
            "previous_avg": 0,
            "is_significant": False,
            "weeks_compared": weeks_to_compare,
        }

    # Create DataFrame and ensure proper date format
    df = pd.DataFrame(statistics_data).copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["date"])  # Remove rows with invalid dates

    # Ensure chronological order
    df = df.sort_values("date", ascending=True)

    # Convert metric values to numeric
    df[metric] = pd.to_numeric(df[metric], errors="coerce").fillna(0)

    # Group by week for consistent weekly aggregation
    df["week"] = df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
    df["year"] = df["date"].dt.year  # type: ignore[attr-defined]
    df["year_week"] = df.apply(lambda r: f"{r['year']}-W{r['week']:02d}", axis=1)

    # Aggregate by week
    weekly_df = (
        df.groupby("year_week")
        .agg(
            metric_sum=(metric, "sum"),
            start_date=("date", "min"),
        )
        .reset_index()
    )

    # Sort by date again to ensure chronological order
    weekly_df = weekly_df.sort_values("start_date")

    # Make sure we have enough weeks for comparison
    if len(weekly_df) < weeks_to_compare * 2:
        return {
            "trend_direction": "stable",
            "percent_change": 0,
            "current_avg": 0,
            "previous_avg": 0,
            "is_significant": False,
            "weeks_compared": len(weekly_df) // 2 if len(weekly_df) > 1 else 1,
        }

    # Get the latest data points for comparison
    recent_data = weekly_df.tail(weeks_to_compare * 2)

    # Split into current and previous periods
    current_period = recent_data.tail(weeks_to_compare)
    previous_period = recent_data.head(weeks_to_compare)

    # Calculate averages for each period
    current_avg = current_period["metric_sum"].mean()
    previous_avg = previous_period["metric_sum"].mean()

    # Calculate percentage change
    if previous_avg > 0:
        percent_change = ((current_avg - previous_avg) / previous_avg) * 100
    else:
        # If previous average is 0, use current average as the change
        percent_change = current_avg * 100 if current_avg > 0 else 0

    # Determine trend direction
    if abs(percent_change) < 5:
        trend_direction = "stable"
    elif percent_change > 0:
        trend_direction = "up"
    else:
        trend_direction = "down"  # Check if change is significant (>20%)
    is_significant = abs(percent_change) >= 20

    return {
        "trend_direction": trend_direction,
        "percent_change": round(percent_change, 1),
        "current_avg": round(current_avg, 2),
        "previous_avg": round(previous_avg, 2),
        "is_significant": is_significant,
        "weeks_compared": weeks_to_compare,
    }


def process_statistics_data(
    data: list[dict] | pd.DataFrame, settings: dict
) -> pd.DataFrame:
    """Process statistics data for visualization and analysis.

    Args:
        data: Statistics data as list of dictionaries or DataFrame
        settings: Dictionary with project settings including baseline

    Returns:
        DataFrame with processed statistics data including cumulative values
    """
    # Convert data to DataFrame if not already
    if isinstance(data, list):
        if not data:  # Empty list
            return pd.DataFrame(
                columns=[
                    "date",
                    "completed_items",
                    "completed_points",
                    "created_items",
                    "created_points",
                ]
            )
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    # Ensure all required columns exist
    for col in ["date", "completed_items", "completed_points"]:
        if col not in df.columns:
            df[col] = 0 if col != "date" else ""

    # Add scope tracking columns if they don't exist
    for col in ["created_items", "created_points"]:
        if col not in df.columns:
            df[col] = 0

    # Convert date to datetime
    df["date"] = pd.to_datetime(df["date"])

    # Sort by date
    df = df.sort_values("date")

    # Fill missing values with 0
    numeric_cols = [
        "completed_items",
        "completed_points",
        "created_items",
        "created_points",
    ]
    df[numeric_cols] = df[numeric_cols].fillna(0).astype(int)

    # Add cumulative columns for both completed and created items/points
    df["cum_completed_items"] = df["completed_items"].cumsum()
    df["cum_completed_points"] = df["completed_points"].cumsum()
    df["cum_created_items"] = df["created_items"].cumsum()
    df["cum_created_points"] = df["created_points"].cumsum()

    # Calculate total scope (baseline + created)
    baseline_items = settings.get("baseline", {}).get("items", 0) or 0
    baseline_points = settings.get("baseline", {}).get("points", 0) or 0

    df["total_scope_items"] = baseline_items + df["cum_created_items"]
    df["total_scope_points"] = baseline_points + df["cum_created_points"]

    return df


def establish_baseline(statistics_data: dict | None) -> dict:
    """Establish a baseline from initial scope.

    Args:
        statistics_data: Dictionary containing statistics data and baseline info

    Returns:
        Dictionary with baseline items, points, and date
    """
    if not statistics_data or not statistics_data.get("data"):
        return {"items": 0, "points": 0, "date": datetime.now().strftime("%Y-%m-%d")}

    # Get the earliest date in the dataset
    df = pd.DataFrame(statistics_data["data"])
    if "date" not in df.columns or df.empty:
        return {"items": 0, "points": 0, "date": datetime.now().strftime("%Y-%m-%d")}

    earliest_date = pd.to_datetime(df["date"]).min()

    # Return baseline info
    return {
        "items": statistics_data.get("baseline", {}).get("items", 0),
        "points": statistics_data.get("baseline", {}).get("points", 0),
        "date": earliest_date.strftime("%Y-%m-%d"),
    }


#######################################################################
# DASHBOARD CALCULATIONS (User Story 2)
#######################################################################


def calculate_dashboard_metrics(statistics: list, settings: dict) -> dict:
    """
    Calculate aggregated project health metrics for Dashboard display.

    This function supports User Story 2: Dashboard as Primary Landing View.
    It computes all key metrics needed for the Dashboard tab including completion
    forecast, velocity, remaining work, and trend analysis.

    Args:
        statistics: List of statistics dictionaries with date, completed_items, completed_points
        settings: Settings dictionary with pert_factor, deadline, scope values

    Returns:
        dict: DashboardMetrics with all computed values (see data-model.md Section 3.1)

    Example:
        >>> stats = [{"date": "2025-01-01", "completed_items": 5, "completed_points": 25}]
        >>> settings = {"pert_factor": 1.5, "deadline": "2025-12-31"}
        >>> metrics = calculate_dashboard_metrics(stats, settings)
        >>> print(metrics['days_to_completion'])
        53
    """
    from datetime import datetime, timedelta

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
    data_points_count = min(len(df), int(settings.get("data_points_count", 10)))
    recent_data = df.tail(data_points_count)

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
    from datetime import timedelta

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
