"""
Scope creep metrics calculation functions.
"""

import pandas as pd
from datetime import datetime


def calculate_scope_creep_rate(df, baseline_items, baseline_points):
    """
    Calculate scope creep rate as percentage of new items/points created over baseline.

    Formula:
    Scope Creep Rate = (sum(created_items) / baseline) × 100%

    Where baseline = remaining total items + sum(completed_items)
    """
    if df.empty or baseline_items == 0 or baseline_points == 0:
        return {"items_rate": 0, "points_rate": 0}

    # Get total created and completed items/points
    total_created_items = df["created_items"].sum()
    total_created_points = df["created_points"].sum()
    total_completed_items = df["completed_items"].sum()
    total_completed_points = df["completed_points"].sum()

    # Calculate the true baseline (remaining items + completed items)
    actual_baseline_items = baseline_items + total_completed_items
    actual_baseline_points = baseline_points + total_completed_points

    # Calculate scope creep rates as percentage of created items over baseline
    items_rate = (
        (total_created_items / actual_baseline_items) * 100
        if actual_baseline_items > 0
        else 0
    )
    points_rate = (
        (total_created_points / actual_baseline_points) * 100
        if actual_baseline_points > 0
        else 0
    )

    return {"items_rate": round(items_rate, 1), "points_rate": round(points_rate, 1)}


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


def calculate_weekly_scope_growth(df):
    """
    Calculate weekly scope growth (created - completed).

    Weekly Scope Growth = Weekly Created Items - Weekly Completed Items
    """
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


def calculate_scope_stability_index(df, baseline_items, baseline_points):
    """
    Calculate scope stability index.

    Scope Stability Index = 1 - (Number of Requirement Changes / Total Requirements)

    Higher value means more stability (less scope changes relative to total scope).
    """
    if df.empty or baseline_items == 0 or baseline_points == 0:
        return {"items_stability": 1.0, "points_stability": 1.0}

    # Total changes (all created items/points)
    total_created_items = df["created_items"].sum()
    total_created_points = df["created_points"].sum()

    # Calculate current total scope (baseline + created - completed)
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


def check_scope_creep_threshold(scope_creep_rate, threshold):
    """
    Check if scope creep rate exceeds threshold.

    Returns a dict with status and message.
    """
    items_exceeded = scope_creep_rate["items_rate"] > threshold
    points_exceeded = scope_creep_rate["points_rate"] > threshold

    status = "warning" if items_exceeded or points_exceeded else "ok"
    message = ""

    if items_exceeded and points_exceeded:
        message = f"Both items ({scope_creep_rate['items_rate']}%) and points ({scope_creep_rate['points_rate']}%) scope creep exceed threshold ({threshold}%)."
    elif items_exceeded:
        message = f"Items scope creep ({scope_creep_rate['items_rate']}%) exceeds threshold ({threshold}%)."
    elif points_exceeded:
        message = f"Points scope creep ({scope_creep_rate['points_rate']}%) exceeds threshold ({threshold}%)."

    return {"status": status, "message": message}
