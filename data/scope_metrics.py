"""
Scope change metrics calculation functions.

SCOPE TERMINOLOGY AND DEFINITIONS
==================================

This module calculates scope change metrics for agile projects. Understanding the
terminology is critical for correct calculations:

**Initial Scope (Baseline)**
- Definition: The original project scope at the earliest data point, BEFORE any scope changes
- Calculation: completed_items + remaining_items (at project start)
- Example: If project starts with 100 items (50 completed, 50 remaining), initial_scope = 100
- Usage: This is the denominator for scope change rate calculations

**Current Total Scope**
- Definition: The current total project scope INCLUDING all scope changes
- Calculation: initial_scope + created_items
- Example: If initial_scope=100 and 20 items were added, current_total_scope = 120
- Usage: This represents the full scope of work to complete the project

**Created Items**
- Definition: New items added to the project after the initial scope was established
- Source: Sum of created_items column in statistics data
- Example: Items added due to new requirements, discovered work, etc.

**Scope Change Rate**
- Definition: Percentage increase in project scope relative to the initial baseline
- Formula: (created_items / initial_scope) × 100%
- Example: 20 items created on 100-item project = 20% scope change rate
- Interpretation: Measures how much the project has grown from its original size

CORRECT BASELINE USAGE
=======================

When calling scope metric functions, the baseline parameters MUST represent the
INITIAL scope (at project start), NOT the current total scope:

✅ CORRECT:
```python
# Calculate initial scope from earliest data point
initial_items = df.iloc[0]['remaining_items'] + df['completed_items'].sum()
initial_points = df.iloc[0]['remaining_points'] + df['completed_points'].sum()

# Use initial scope as baseline
scope_change_rate = calculate_scope_change_rate(df, initial_items, initial_points)
```

❌ WRONG:
```python
# Do NOT include created items in baseline
current_total = initial_items + df['created_items'].sum()  # This is current total, not baseline
scope_change_rate = calculate_scope_change_rate(df, current_total, ...)  # WRONG!
```

IMPLICATIONS FOR DECISION-MAKING
=================================

- **Scope Change Rate > 0%**: Project scope has grown beyond initial estimate
- **Scope Change Rate > 20%**: Significant scope growth, may impact timeline
- **Throughput Ratio > 1.0**: New work added faster than work completed (scope growing)
- **Throughput Ratio < 1.0**: Completing work faster than adding new work (scope stable)

"""

import pandas as pd
from datetime import datetime


def calculate_scope_change_rate(
    df, baseline_items, baseline_points, data_points_count=None
):
    """
    Calculate scope change rate as percentage of new items/points created over baseline.

    Formula:
    Scope Change Rate = (sum(created_items) / baseline) × 100%

    Where baseline = INITIAL project scope (completed + remaining at project start,
                     BEFORE any new items were created)

    IMPORTANT: baseline_items and baseline_points should represent the ORIGINAL scope
    at project start, NOT the current total scope (which includes created items).

    In agile projects, this tracks the rate of scope change rather than implying negative "creep".

    Args:
        df: DataFrame with project statistics (must include created_items, created_points columns)
        baseline_items: Initial scope in items (at project start, before scope changes)
        baseline_points: Initial scope in points (at project start, before scope changes)
        data_points_count: Optional parameter to limit data to most recent N data points

    Returns:
        Dict with:
        - items_rate: Scope change rate for items (%)
        - points_rate: Scope change rate for points (%)
        - throughput_ratio: Dict with items/points throughput ratios (created/completed)
    """
    # Apply data points filtering
    if (
        data_points_count is not None
        and data_points_count > 0
        and len(df) > data_points_count
    ):
        df = df.tail(data_points_count)

    # Get total created and completed items/points
    if df.empty:
        return {
            "items_rate": 0,
            "points_rate": 0,
            "throughput_ratio": {"items": 0, "points": 0},
        }

    total_created_items = df["created_items"].sum()
    total_created_points = df["created_points"].sum()
    total_completed_items = df["completed_items"].sum()
    total_completed_points = df["completed_points"].sum()

    # Calculate throughput ratios regardless of baseline values
    items_throughput_ratio = (
        total_created_items / total_completed_items
        if total_completed_items > 0
        else float("inf")
        if total_created_items > 0
        else 0
    )

    points_throughput_ratio = (
        total_created_points / total_completed_points
        if total_completed_points > 0
        else float("inf")
        if total_created_points > 0
        else 0
    )

    # Check if baselines are zero - if so, only calculate throughput ratios
    if baseline_items == 0 or baseline_points == 0:
        return {
            "items_rate": 0,
            "points_rate": 0,
            "throughput_ratio": {
                "items": round(items_throughput_ratio, 2),
                "points": round(points_throughput_ratio, 2),
            },
        }

    # Calculate scope change rates as percentage of created items over original baseline
    # Note: baseline_items/baseline_points represent the original total project scope
    # Do NOT add completed_items as that would double-count the work
    items_rate = (
        (total_created_items / baseline_items) * 100 if baseline_items > 0 else 0
    )
    points_rate = (
        (total_created_points / baseline_points) * 100 if baseline_points > 0 else 0
    )

    return {
        "items_rate": round(items_rate, 1),
        "points_rate": round(points_rate, 1),
        "throughput_ratio": {
            "items": round(items_throughput_ratio, 2),
            "points": round(points_throughput_ratio, 2),
        },
    }


# For backwards compatibility
def calculate_scope_creep_rate(
    df, baseline_items, baseline_points, data_points_count=None
):
    return calculate_scope_change_rate(
        df, baseline_items, baseline_points, data_points_count
    )


def calculate_total_project_scope(df, remaining_items, remaining_points):
    """
    Calculate the initial project scope (baseline) at a specific point in time.

    Formula:
    Initial Scope (Baseline) = Remaining Items + Completed Items

    This represents the project scope at the measurement point, BEFORE accounting
    for any scope changes (created items). This is the correct baseline value to
    use when calculating scope change rates.

    IMPORTANT: This does NOT include created_items/points, which represent scope
    changes added after the initial baseline was established.

    Example:
    - Completed items: 40
    - Remaining items: 60
    - Initial Scope: 100 items (this is the baseline)
    - If 20 items were later created, current total scope = 120, but baseline stays 100

    Args:
        df: DataFrame with project statistics including completed_items and completed_points
        remaining_items: Number of remaining items at the measurement point
        remaining_points: Number of remaining points at the measurement point

    Returns:
        Dictionary with total_items and total_points representing the initial project
        scope (baseline) to be used in scope change calculations
    """
    if df.empty:
        return {"total_items": remaining_items, "total_points": remaining_points}

    # Sum up completed items/points
    total_completed_items = df["completed_items"].sum()
    total_completed_points = df["completed_points"].sum()

    # Calculate total project scope (baseline)
    total_items = remaining_items + total_completed_items
    total_points = remaining_points + total_completed_points

    return {"total_items": int(total_items), "total_points": int(total_points)}


def calculate_weekly_scope_growth(df, data_points_count=None):
    """
    Calculate weekly scope growth (created - completed).

    Weekly Scope Growth = Weekly Created Items - Weekly Completed Items

    Args:
        df: DataFrame with project statistics
        data_points_count: Optional parameter to limit data to most recent N data points
    """
    # Apply data points filtering
    if (
        data_points_count is not None
        and data_points_count > 0
        and len(df) > data_points_count
    ):
        df = df.tail(data_points_count)

    if df.empty:
        return pd.DataFrame(columns=["week", "items_growth", "points_growth"])

    # Ensure date column is datetime
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Add week number column
    df["week"] = df["date"].dt.isocalendar().week
    df["year"] = df["date"].dt.isocalendar().year

    # Group by week and calculate weekly totals
    weekly = (
        df.groupby(["year", "week"])
        .agg(
            {
                "completed_items": "sum",
                "completed_points": "sum",
                "created_items": "sum",
                "created_points": "sum",
            }
        )
        .reset_index()
    )

    # Calculate growth
    weekly["items_growth"] = weekly["created_items"] - weekly["completed_items"]
    weekly["points_growth"] = weekly["created_points"] - weekly["completed_points"]

    # Format week label as ISO week format (e.g., "2023-W01")
    weekly["week_label"] = weekly.apply(
        lambda row: f"{row['year']}-W{row['week']:02d}", axis=1
    )

    # Create a proper start date for each week
    weekly["start_date"] = weekly.apply(
        lambda row: get_week_start_date(row["year"], row["week"]), axis=1
    )

    # Sort by date
    weekly = weekly.sort_values("start_date")

    # Return only the relevant columns
    result = weekly[["week_label", "items_growth", "points_growth", "start_date"]]

    return result


def get_week_start_date(year, week):
    """Get the start date (Monday) of a given ISO week."""
    # The %G and %V format codes are for ISO year and ISO week
    # %u gives day of week (1=Monday, 7=Sunday)
    first_day = datetime.strptime(f"{year}-{week}-1", "%G-%V-%u")
    return first_day


def calculate_scope_stability_index(
    df, baseline_items, baseline_points, data_points_count=None
):
    """
    Calculate scope stability index.

    Scope Stability Index = 1 - (created_items / current_total_scope)

    Higher value means more stability (less scope changes relative to total scope).

    Formula:
    - Current Total Scope = initial_scope (baseline) + created_items
    - Stability Index = 1 - (created_items / current_total_scope)

    Example:
    - Initial scope: 100 items
    - Created items: 20 items
    - Current total: 120 items
    - Stability: 1 - (20/120) = 0.83 (83% stable)

    Args:
        df: DataFrame with project statistics
        baseline_items: Initial scope in items (at project start, before scope changes)
        baseline_points: Initial scope in points (at project start, before scope changes)
        data_points_count: Optional parameter to limit data to most recent N data points

    Returns:
        Dict with items_stability and points_stability (0.0 to 1.0)
    """
    # Apply data points filtering
    if (
        data_points_count is not None
        and data_points_count > 0
        and len(df) > data_points_count
    ):
        df = df.tail(data_points_count)

    if df.empty or baseline_items == 0 or baseline_points == 0:
        return {"items_stability": 1.0, "points_stability": 1.0}

    # Total changes (all created items/points added after project start)
    total_created_items = df["created_items"].sum()
    total_created_points = df["created_points"].sum()

    # Calculate current total scope:
    # Current Total Scope = Initial Scope (baseline) + Created Items
    # This represents the full scope including all scope changes
    total_items = baseline_items + total_created_items
    total_points = baseline_points + total_created_points

    # Calculate stability index: 1 - (scope changes / current total scope)
    # Higher value = more stable (fewer changes relative to total scope)
    items_stability = 1 - (total_created_items / total_items) if total_items > 0 else 1
    points_stability = (
        1 - (total_created_points / total_points) if total_points > 0 else 1
    )

    return {
        "items_stability": round(max(0, min(1, items_stability)), 2),
        "points_stability": round(max(0, min(1, points_stability)), 2),
    }


def check_scope_change_threshold(scope_change_rate, threshold):
    """
    Check if scope change rate exceeds threshold.

    In agile, scope changes are normal - this function helps identify when the rate
    of change may affect delivery without judging the changes themselves.

    Returns a dict with status and message.
    """
    items_exceeded = scope_change_rate["items_rate"] > threshold
    points_exceeded = scope_change_rate["points_rate"] > threshold

    # Check throughput ratios - if > 1, scope is growing faster than completion
    items_throughput_concern = scope_change_rate["throughput_ratio"]["items"] > 1
    points_throughput_concern = scope_change_rate["throughput_ratio"]["points"] > 1

    # Only warn if both percentage threshold is exceeded AND throughput ratio > 1
    status = "info"
    if (items_exceeded or points_exceeded) and (
        items_throughput_concern or points_throughput_concern
    ):
        status = "warning"

    message = ""

    if status == "warning":
        parts = []
        if items_exceeded:
            parts.append(f"Items scope change ({scope_change_rate['items_rate']}%)")
        if points_exceeded:
            parts.append(f"Points scope change ({scope_change_rate['points_rate']}%)")

        if parts:
            message = f"{' and '.join(parts)} exceed threshold ({threshold}%)."

            # Add throughput insight
            if items_throughput_concern and points_throughput_concern:
                message += f" Scope is growing {scope_change_rate['throughput_ratio']['items']}x faster than items completion and {scope_change_rate['throughput_ratio']['points']}x faster than points completion."
            elif items_throughput_concern:
                message += f" Scope is growing {scope_change_rate['throughput_ratio']['items']}x faster than items completion."
            elif points_throughput_concern:
                message += f" Scope is growing {scope_change_rate['throughput_ratio']['points']}x faster than points completion."

    return {"status": status, "message": message}


# For backwards compatibility
check_scope_creep_threshold = check_scope_change_threshold
