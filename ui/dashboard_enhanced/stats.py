"""
Dashboard Enhanced - Statistical Helper Functions

Provides velocity statistics, forecast confidence intervals,
deadline probability, and project health assessments.
"""

import pandas as pd
from scipy import stats


def _calculate_velocity_statistics(
    statistics_df: pd.DataFrame, metric_type: str = "items"
) -> dict:
    """Calculate comprehensive velocity statistics."""
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

    # Recent performance (last 4 weeks)
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
    """
    Calculate forecast confidence intervals using statistical distribution.

    IMPORTANT: These are TRUE STATISTICAL CONFIDENCE INTERVALS based on
    velocity variance, NOT the optimistic/pessimistic dates from the
    burndown chart (which use best/worst N weeks).

    Mathematical Basis:
    - Uses normal distribution approximation
        - Calculates coefficient of variation (CV = std_dev / mean)
            to measure velocity uncertainty
    - Applies standard statistical confidence levels (percentiles)

    Confidence Interval Calculations (One-Sided Percentiles):
    - 50th percentile: PERT forecast (median estimate)
      This is the expected completion date with 50% probability
      Formula: pert_days

    - 80th percentile: PERT forecast + (0.84sigma) - 80% chance of completion
      by this date
      Common project management buffer level
      Formula: pert_days + (0.84 x forecast_std)

    - 95th percentile: PERT forecast + (1.65sigma) - 95% chance of completion
      by this date
      Conservative estimate with substantial buffer
      Formula: pert_days + (1.65 x forecast_std)

    Interpretation:
    - 50%: Median forecast - 50% probability of completing by this date
    - 80%: Good confidence - 80% probability of completing by this date
    - 95%: High confidence - 95% probability of completing by this date (safe estimate)
    - Wider spread between percentiles = higher velocity uncertainty
    - These are DIFFERENT from optimistic/pessimistic on burndown chart!

    Args:
        pert_forecast_days: Expected completion days from PERT calculation
        velocity_mean: Average historical velocity (items/week)
        velocity_std: Standard deviation of historical velocity
        remaining_work: Remaining items/points to complete

    Returns:
        dict with ci_50, ci_80, ci_95 (days to completion)
    """
    if velocity_mean == 0 or velocity_std == 0:
        return {
            "ci_50": pert_forecast_days,
            "ci_80": pert_forecast_days,
            "ci_95": pert_forecast_days,
        }

    # Coefficient of variation (CV = std_dev / mean)
    cv = velocity_std / velocity_mean

    # Calculate forecast standard deviation
    # This represents the uncertainty in the forecast due to velocity variability
    forecast_std = cv * pert_forecast_days

    # Calculate confidence intervals using standard normal distribution percentiles
    # These are one-sided "completion by" dates, not two-sided ranges
    ci_50 = pert_forecast_days  # 50th percentile (median)
    ci_80 = pert_forecast_days + (0.84 * forecast_std)  # 80th percentile (z=0.84)
    ci_95 = pert_forecast_days + (1.65 * forecast_std)  # 95th percentile (z=1.65)

    return {"ci_50": max(0, ci_50), "ci_80": max(0, ci_80), "ci_95": max(0, ci_95)}


def _calculate_deadline_probability(
    days_to_deadline: float,
    pert_forecast_days: float,
    velocity_std: float,
    velocity_mean: float,
) -> float:
    """
    Calculate probability of meeting deadline using normal distribution.

    This is the "On-Track Probability" shown on forecast cards.

    Mathematical Basis:
    - Assumes velocity follows a normal (bell curve) distribution
    - Uses standard deviation of historical velocity to estimate forecast uncertainty
        - Calculates Z-score: how many standard deviations the deadline is
            from expected completion
    - Converts Z-score to probability using cumulative distribution function (CDF)

    Calculation Steps:
    1. Calculate coefficient of variation: CV = velocity_std / velocity_mean
    2. Estimate forecast uncertainty: forecast_std = CV x pert_forecast_days
    3. Calculate Z-score: z = (deadline_days - pert_forecast_days) / forecast_std
    4. Convert to probability: P = CDF(z) x 100%

    Interpretation:
    - 100%: Deadline is well after expected completion - Very likely to meet deadline
    - 80%: Deadline is after expected completion - Good chance of meeting deadline
    - 50%: Deadline equals expected completion - Coin flip odds
    - 20%: Deadline is before expected completion - Risky, likely to miss
    - 0%: Deadline is well before expected completion - Very unlikely to meet

    Example:
    - Expected completion: 100 days
    - Deadline: 110 days (10 days buffer)
    - Forecast std dev: 15 days
    - Z-score: (110-100)/15 = 0.67
    - Probability: CDF(0.67) = ~75% chance of meeting deadline

    Args:
        days_to_deadline: Days remaining until deadline
        pert_forecast_days: Expected completion days from PERT
        velocity_std: Standard deviation of velocity
        velocity_mean: Average velocity

    Returns:
        float: Probability (0-100%) of meeting the deadline
    """
    if velocity_mean == 0:
        return 50.0

    # Calculate coefficient of variation and forecast standard deviation
    cv = velocity_std / velocity_mean
    forecast_std_days = cv * pert_forecast_days

    # Edge case: deterministic (no variance)
    if forecast_std_days == 0:
        return 100.0 if days_to_deadline >= pert_forecast_days else 0.0

    # Calculate Z-score: how many standard deviations the deadline is from expected
    z = (days_to_deadline - pert_forecast_days) / forecast_std_days

    # Convert to probability using normal CDF
    probability = float(stats.norm.cdf(z)) * 100

    return max(0.0, min(100.0, probability))


def _assess_project_health(
    velocity_cv: float,
    days_to_deadline: float,
    pert_forecast_days: float,
    recent_velocity_change: float,
    capacity_gap_percent: float,
) -> dict:
    """Assess overall project health and return structured score."""
    factors = []

    # Factor 1: Velocity Predictability
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

    # Factor 2: Schedule Status
    schedule_delta = pert_forecast_days - days_to_deadline
    if schedule_delta <= 0:
        factors.append({"name": "On Schedule", "status": "good", "icon": "[OK]"})
    elif schedule_delta <= 14:
        factors.append({"name": "Slightly Behind", "status": "warning", "icon": "[!]"})
    else:
        factors.append({"name": "Behind Schedule", "status": "bad", "icon": "[X]"})

    # Factor 3: Velocity Trend
    if recent_velocity_change >= 5:
        factors.append({"name": "Velocity Improving", "status": "good", "icon": "[OK]"})
    elif recent_velocity_change >= -5:
        factors.append({"name": "Velocity Stable", "status": "good", "icon": "[OK]"})
    else:
        factors.append(
            {"name": "Velocity Declining", "status": "warning", "icon": "[!]"}
        )

    # Factor 4: Capacity
    if capacity_gap_percent >= -10:
        factors.append({"name": "Adequate Capacity", "status": "good", "icon": "[OK]"})
    elif capacity_gap_percent >= -25:
        factors.append(
            {"name": "Capacity Stretched", "status": "warning", "icon": "[!]"}
        )
    else:
        factors.append({"name": "Capacity Shortfall", "status": "bad", "icon": "[X]"})

    # Calculate overall health score
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
