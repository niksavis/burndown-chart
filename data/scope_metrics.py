"""
Scope creep metrics calculation functions.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def calculate_scope_creep_rate(df, baseline_items, baseline_points):
    """
    Calculate scope creep rate as percentage of new items/points created over baseline.

    Scope Creep Rate = (New Items Created / Original Items) × 100%
    """
    if df.empty or baseline_items == 0 or baseline_points == 0:
        return {"items_rate": 0, "points_rate": 0}

    # Ensure we have the created columns
    if "cum_created_items" not in df.columns:
        df["cum_created_items"] = df.get("created_items", 0).cumsum()
    if "cum_created_points" not in df.columns:
        df["cum_created_points"] = df.get("created_points", 0).cumsum()

    # Get the latest values
    last_row = df.iloc[-1]
    total_created_items = last_row.get("cum_created_items", 0)
    total_created_points = last_row.get("cum_created_points", 0)

    # Calculate scope creep rates
    items_rate = (
        (total_created_items / baseline_items) * 100 if baseline_items > 0 else 0
    )
    points_rate = (
        (total_created_points / baseline_points) * 100 if baseline_points > 0 else 0
    )

    return {"items_rate": round(items_rate, 1), "points_rate": round(points_rate, 1)}


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
