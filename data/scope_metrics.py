"""
Scope change metrics calculation functions.
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

    Where baseline = remaining total items + sum(completed_items)

    In agile projects, this tracks the rate of scope change rather than implying negative "creep".

    Args:
        df: DataFrame with project statistics
        baseline_items: Baseline number of items
        baseline_points: Baseline number of points
        data_points_count: Optional parameter to limit data to most recent N data points
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
    Calculate the total project scope without double-counting.

    The formula is:
    Total Scope = Remaining Items + Completed Items

    This represents the true baseline scope (completed work plus remaining work)
    without including created items/points, which may have already been counted in
    completed or remaining items.

    Args:
        df: DataFrame with project statistics including completed_items and completed_points
        remaining_items: Number of remaining items from forecast_settings.json
        remaining_points: Number of remaining points from forecast_settings.json

    Returns:
        Dictionary with total_items and total_points representing the actual project scope
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

    Scope Stability Index = 1 - (Number of Requirement Changes / Total Requirements)

    Higher value means more stability (less scope changes relative to total scope).

    Note: The total scope is calculated as:
    Total Scope = Remaining items + Created items

    This avoids double counting completed items that may overlap with created items.

    Args:
        df: DataFrame with project statistics
        baseline_items: Baseline number of items
        baseline_points: Baseline number of points
        data_points_count: Optional parameter to limit data to most recent N data points
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

    # Total changes (all created items/points)
    total_created_items = df["created_items"].sum()
    total_created_points = df["created_points"].sum()

    # Calculate current total scope correctly:
    # Total scope = Remaining items + Created items
    # No need to subtract completed items from baseline
    total_items = baseline_items + total_created_items
    total_points = baseline_points + total_created_points

    # Calculate stability index
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
