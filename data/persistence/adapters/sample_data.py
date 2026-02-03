"""Data persistence adapters - Sample data generation and cleaning."""

# Standard library imports
from datetime import datetime, timedelta

# Third-party library imports
import pandas as pd

# Application imports


def generate_realistic_sample_data():
    """
    Generate realistic sample data that spans multiple weeks for better visualization.
    This provides a more comprehensive dataset when no real data is available.

    Returns:
        DataFrame with sample data
    """
    # Start date will be 12 weeks ago
    end_date = datetime.now()
    start_date = end_date - timedelta(days=12 * 7)  # 12 weeks

    # Generate dates for each day in the range
    dates = []
    current_date = start_date
    while current_date <= end_date:
        # Skip weekends to simulate real work patterns
        if current_date.weekday() < 5:  # Monday to Friday
            dates.append(current_date)
        current_date += timedelta(days=1)

    # Generate realistic data with trends and variations
    n_dates = len(dates)

    # Create a base velocity with some randomness
    base_items = 3  # Base number of items per day
    base_points = 30  # Base number of points per day

    # Scope creep - base numbers (slightly lower than completion rate)
    base_created_items = 2  # Base number of items created per day
    base_created_points = 20  # Base number of points created per day

    # Generate data with realistic patterns:
    # 1. General improvement trend over time
    # 2. Occasional spikes and dips
    # 3. Correlation between items and points

    completed_items = []
    completed_points = []
    created_items = []
    created_points = []

    for i in range(n_dates):
        # Calculate progress factor (increases slightly over time)
        progress_factor = 1.0 + (i / n_dates) * 0.5

        # Weekly pattern (more productive mid-week)
        day_of_week = dates[i].weekday()
        day_factor = 0.8 + (1.4 - abs(day_of_week - 2) * 0.15)

        # Random factor (daily variation)
        random_factor = 0.5 + (1.0 * (i % 3)) if i % 10 < 8 else 0

        # Calculate completed items and points
        day_items = max(
            0, round(base_items * progress_factor * day_factor * random_factor)
        )

        # Points are correlated with items but have more variation
        points_per_item = base_points / base_items * (0.8 + random_factor * 0.4)
        day_points = max(0, round(day_items * points_per_item))

        completed_items.append(day_items)
        completed_points.append(day_points)

        # Calculate created items and points (scope creep)
        # Simulate realistic scope creep - higher in early and middle phases
        project_phase = i / n_dates  # 0 to 1 representing project timeline
        scope_creep_factor = (
            1.2 if project_phase < 0.7 else 0.6
        )  # More scope changes early/mid project

        # Occasional scope change spikes
        scope_spike = 3 if i % 14 == 0 else 1  # Occasional planning meetings add scope

        # Calculate created items and points
        day_created_items = max(
            0,
            round(
                base_created_items * scope_creep_factor * scope_spike * random_factor
            ),
        )

        # Points for created items
        created_points_per_item = (
            base_created_points / base_created_items * (0.9 + random_factor * 0.3)
        )
        day_created_points = max(0, round(day_created_items * created_points_per_item))

        created_items.append(day_created_items)
        created_points.append(day_created_points)

    # Create the dataframe
    sample_df = pd.DataFrame(
        {
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "completed_items": completed_items,
            "completed_points": completed_points,
            "created_items": created_items,
            "created_points": created_points,
        }
    )

    return sample_df


def read_and_clean_data(df):
    """
    Clean and validate statistics data.

    Args:
        df: Pandas DataFrame containing raw statistics data

    Returns:
        DataFrame with cleaned and formatted data
    """
    # Ensure required columns exist
    required_columns = ["date", "completed_items", "completed_points"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in data")

    # Check for scope tracking columns and add them if missing
    if "created_items" not in df.columns:
        df["created_items"] = 0
    if "created_points" not in df.columns:
        df["created_points"] = 0

    # Convert date to datetime format
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Drop rows with invalid dates
    df = df.dropna(subset=["date"])

    # Ensure all numeric columns are properly formatted
    numeric_columns = [
        "completed_items",
        "completed_points",
        "created_items",
        "created_points",
    ]
    for col in numeric_columns:
        if col in df.columns:  # Only process columns that exist
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Sort by date
    df = df.sort_values("date", ascending=True)

    # Convert date back to string format
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # Include all valid columns (required + scope tracking)
    valid_columns = required_columns + ["created_items", "created_points"]

    # Filter to only include columns that exist in the dataframe
    existing_columns = [col for col in valid_columns if col in df.columns]
    df = df[existing_columns]

    return df


#######################################################################
# UNIFIED DATA FUNCTIONS (v2.0)
#######################################################################
