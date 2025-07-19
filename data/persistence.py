"""
Data Persistence Module

This module handles saving and loading application data to/from disk.
It provides functions for managing settings (JSON) and statistics (CSV).
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import json
import os
from datetime import datetime, timedelta

# Third-party library imports
import pandas as pd

# Application imports
from configuration import (
    APP_SETTINGS_FILE,
    DEFAULT_DATA_POINTS_COUNT,
    DEFAULT_DEADLINE,
    DEFAULT_ESTIMATED_ITEMS,
    DEFAULT_ESTIMATED_POINTS,
    DEFAULT_PERT_FACTOR,
    DEFAULT_TOTAL_ITEMS,
    DEFAULT_TOTAL_POINTS,
    PROJECT_DATA_FILE,
    SETTINGS_FILE,
    STATISTICS_FILE,
    logger,
)

#######################################################################
# DATA PERSISTENCE FUNCTIONS
#######################################################################


def should_sync_jira():
    """
    Check if JIRA sync should be performed based on configuration.

    Returns:
        bool: True if JIRA is enabled and configured
    """
    import os

    # Check if JIRA is enabled via environment variables
    jira_url = os.getenv("JIRA_URL", "")
    jira_default_jql = os.getenv("JIRA_DEFAULT_JQL", "")

    return bool(
        jira_url and (jira_default_jql or True)
    )  # Always true if URL exists, JQL has default


def save_app_settings(
    pert_factor,
    deadline,
    data_points_count=None,
    show_milestone=None,
    milestone=None,
    show_points=None,
    jql_query=None,
    jira_url=None,
    jira_token=None,
    jira_story_points_field=None,
    jira_cache_max_size=None,
):
    """
    Save app-level settings to JSON file.

    Args:
        pert_factor: PERT factor value
        deadline: Deadline date string
        data_points_count: Number of data points to use for calculations
        show_milestone: Whether to show milestone on charts
        milestone: Milestone date string
        show_points: Whether to show points tracking and forecasting
        jql_query: JQL query for JIRA integration
        jira_url: JIRA URL for API calls
        jira_token: Personal access token for JIRA API
        jira_story_points_field: Custom field ID for story points
        jira_cache_max_size: Maximum cache size in MB
    """
    settings = {
        "pert_factor": pert_factor,
        "deadline": deadline,
        "data_points_count": data_points_count
        if data_points_count is not None
        else max(DEFAULT_DATA_POINTS_COUNT, pert_factor * 2),
        "show_milestone": show_milestone if show_milestone is not None else False,
        "milestone": milestone,
        "show_points": show_points if show_points is not None else False,
        "jql_query": jql_query if jql_query is not None else "project = JRASERVER",
        "jira_url": jira_url if jira_url is not None else "https://jira.atlassian.com",
        "jira_token": jira_token if jira_token is not None else "",
        "jira_story_points_field": jira_story_points_field
        if jira_story_points_field is not None
        else "",
        "jira_cache_max_size": jira_cache_max_size
        if jira_cache_max_size is not None
        else 100,
    }

    try:
        # Write to a temporary file first
        temp_file = f"{APP_SETTINGS_FILE}.tmp"
        with open(temp_file, "w") as f:
            json.dump(settings, f, indent=2)

        # Rename to final file (atomic operation)
        if os.path.exists(APP_SETTINGS_FILE):
            os.remove(APP_SETTINGS_FILE)
        os.rename(temp_file, APP_SETTINGS_FILE)

        logger.info(f"App settings saved to {APP_SETTINGS_FILE}")
    except Exception as e:
        logger.error(f"Error saving app settings: {e}")


def load_app_settings():
    """
    Load app-level settings from JSON file with automatic migration from legacy format.

    Returns:
        Dictionary containing app settings or default values if file not found
    """
    default_settings = {
        "pert_factor": DEFAULT_PERT_FACTOR,
        "deadline": DEFAULT_DEADLINE,
        "data_points_count": DEFAULT_DATA_POINTS_COUNT,
        "show_milestone": False,
        "milestone": None,
        "show_points": False,
        "jql_query": "project = JRASERVER",
        "jira_url": "https://jira.atlassian.com",
        "jira_token": "",
        "jira_story_points_field": "",
        "jira_cache_max_size": 100,
    }

    try:
        # Check if new app_settings.json exists
        if os.path.exists(APP_SETTINGS_FILE):
            with open(APP_SETTINGS_FILE, "r") as f:
                settings = json.load(f)
            logger.info(f"App settings loaded from {APP_SETTINGS_FILE}")

            # Add default values for new fields if they don't exist
            for key, default_value in default_settings.items():
                if key not in settings:
                    settings[key] = default_value

            return settings

        # Check if legacy forecast_settings.json exists and migrate
        elif os.path.exists(SETTINGS_FILE):
            logger.info(
                f"Migrating legacy settings from {SETTINGS_FILE} to new file structure"
            )
            with open(SETTINGS_FILE, "r") as f:
                legacy_settings = json.load(f)

            # Extract app-level settings from legacy format
            migrated_settings = {
                "pert_factor": legacy_settings.get("pert_factor", DEFAULT_PERT_FACTOR),
                "deadline": legacy_settings.get("deadline", DEFAULT_DEADLINE),
                "data_points_count": legacy_settings.get(
                    "data_points_count", DEFAULT_DATA_POINTS_COUNT
                ),
                "show_milestone": legacy_settings.get("show_milestone", False),
                "milestone": legacy_settings.get("milestone", None),
                "show_points": legacy_settings.get("show_points", True),
                "jql_query": "project = JRASERVER",  # Default JQL for migration
            }

            # Save migrated app settings
            save_app_settings(
                migrated_settings["pert_factor"],
                migrated_settings["deadline"],
                migrated_settings["data_points_count"],
                migrated_settings["show_milestone"],
                migrated_settings["milestone"],
                migrated_settings["show_points"],
                migrated_settings["jql_query"],
            )

            # Extract project data from legacy format and save separately
            project_data = {
                "total_items": legacy_settings.get("total_items", DEFAULT_TOTAL_ITEMS),
                "total_points": legacy_settings.get(
                    "total_points", DEFAULT_TOTAL_POINTS
                ),
                "estimated_items": legacy_settings.get(
                    "estimated_items", DEFAULT_ESTIMATED_ITEMS
                ),
                "estimated_points": legacy_settings.get(
                    "estimated_points", DEFAULT_ESTIMATED_POINTS
                ),
            }

            save_project_data(
                project_data["total_items"],
                project_data["total_points"],
                project_data["estimated_items"],
                project_data["estimated_points"],
                {
                    "migrated_from": SETTINGS_FILE,
                    "migration_date": datetime.now().isoformat(),
                },
            )

            logger.info("Legacy settings migration completed successfully")
            return migrated_settings

        else:
            logger.info("No existing settings files found, using defaults")
            return default_settings

    except Exception as e:
        logger.error(f"Error loading app settings: {e}")
        return default_settings


def save_project_data(
    total_items,
    total_points,
    estimated_items=None,
    estimated_points=None,
    metadata=None,
):
    """
    Save project-specific data to JSON file.

    Args:
        total_items: Total number of items
        total_points: Total number of points
        estimated_items: Number of items that have been estimated
        estimated_points: Number of points for the estimated items
        metadata: Additional project metadata (e.g., JIRA sync info)
    """
    project_data = {
        "total_items": total_items,
        "total_points": total_points,
        "estimated_items": estimated_items
        if estimated_items is not None
        else DEFAULT_ESTIMATED_ITEMS,
        "estimated_points": estimated_points
        if estimated_points is not None
        else DEFAULT_ESTIMATED_POINTS,
        "metadata": metadata if metadata is not None else {},
    }

    try:
        # Write to a temporary file first
        temp_file = f"{PROJECT_DATA_FILE}.tmp"
        with open(temp_file, "w") as f:
            json.dump(project_data, f, indent=2)

        # Rename to final file (atomic operation)
        if os.path.exists(PROJECT_DATA_FILE):
            os.remove(PROJECT_DATA_FILE)
        os.rename(temp_file, PROJECT_DATA_FILE)

        logger.info(f"Project data saved to {PROJECT_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving project data: {e}")


def load_project_data():
    """
    Load project-specific data from JSON file.

    Returns:
        Dictionary containing project data or default values if file not found
    """
    default_data = {
        "total_items": DEFAULT_TOTAL_ITEMS,
        "total_points": DEFAULT_TOTAL_POINTS,
        "estimated_items": DEFAULT_ESTIMATED_ITEMS,
        "estimated_points": DEFAULT_ESTIMATED_POINTS,
        "metadata": {},
    }

    try:
        if os.path.exists(PROJECT_DATA_FILE):
            with open(PROJECT_DATA_FILE, "r") as f:
                project_data = json.load(f)
            logger.info(f"Project data loaded from {PROJECT_DATA_FILE}")

            # Add default values for new fields if they don't exist
            for key, default_value in default_data.items():
                if key not in project_data:
                    project_data[key] = default_value

            return project_data
        else:
            logger.info("Project data file not found, using defaults")
            return default_data
    except Exception as e:
        logger.error(f"Error loading project data: {e}")
        return default_data


def save_settings(
    pert_factor,
    deadline,
    total_items,
    total_points,
    estimated_items=None,
    estimated_points=None,
    data_points_count=None,
    show_milestone=None,
    milestone=None,
    show_points=None,
):
    """
    Save user settings to JSON file.

    Args:
        pert_factor: PERT factor value
        deadline: Deadline date string
        total_items: Total number of items
        total_points: Total number of points
        estimated_items: Number of items that have been estimated
        estimated_points: Number of points for the estimated items
        data_points_count: Number of data points to use for calculations
        show_milestone: Whether to show milestone on charts
        milestone: Milestone date string
        show_points: Whether to show points tracking and forecasting
    """
    settings = {
        "pert_factor": pert_factor,
        "deadline": deadline,
        "total_items": total_items,
        "total_points": total_points,
        "estimated_items": estimated_items
        if estimated_items is not None
        else DEFAULT_ESTIMATED_ITEMS,
        "estimated_points": estimated_points
        if estimated_points is not None
        else DEFAULT_ESTIMATED_POINTS,
        "data_points_count": data_points_count
        if data_points_count is not None
        else max(DEFAULT_DATA_POINTS_COUNT, pert_factor * 2),
        "show_milestone": show_milestone if show_milestone is not None else False,
        "milestone": milestone,
        "show_points": show_points if show_points is not None else False,
    }

    try:
        # Write to a temporary file first
        temp_file = f"{SETTINGS_FILE}.tmp"
        with open(temp_file, "w") as f:
            json.dump(settings, f)

        # Rename to final file (atomic operation)
        if os.path.exists(SETTINGS_FILE):
            os.remove(SETTINGS_FILE)
        os.rename(temp_file, SETTINGS_FILE)

        logger.info(f"Settings saved to {SETTINGS_FILE}")
    except Exception as e:
        logger.error(f"Error saving settings: {e}")


def load_settings():
    """
    Load user settings from JSON file.

    Returns:
        Dictionary containing settings or default values if file not found
    """
    default_settings = {
        "pert_factor": DEFAULT_PERT_FACTOR,
        "deadline": DEFAULT_DEADLINE,
        "total_items": DEFAULT_TOTAL_ITEMS,
        "total_points": DEFAULT_TOTAL_POINTS,
        "estimated_items": DEFAULT_ESTIMATED_ITEMS,
        "estimated_points": DEFAULT_ESTIMATED_POINTS,
        "data_points_count": DEFAULT_DATA_POINTS_COUNT,
        "show_milestone": False,
        "milestone": None,
    }

    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
            logger.info(f"Settings loaded from {SETTINGS_FILE}")

            # Add default values for new fields if they don't exist
            if "estimated_items" not in settings:
                settings["estimated_items"] = DEFAULT_ESTIMATED_ITEMS
            if "estimated_points" not in settings:
                settings["estimated_points"] = DEFAULT_ESTIMATED_POINTS
            if "data_points_count" not in settings:
                # Default to 2x PERT factor or minimum default
                pert_factor = settings.get("pert_factor", DEFAULT_PERT_FACTOR)
                settings["data_points_count"] = max(
                    DEFAULT_DATA_POINTS_COUNT, pert_factor * 2
                )
            if "show_milestone" not in settings:
                settings["show_milestone"] = False
            if "milestone" not in settings:
                settings["milestone"] = None

            return settings
        else:
            logger.info("Settings file not found, using defaults")
            return default_settings
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return default_settings


def save_statistics(data):
    """
    Save statistics data to CSV file.

    Args:
        data: List of dictionaries containing statistics data
    """
    try:
        df = pd.DataFrame(data)

        # Ensure date column is in proper datetime format for sorting
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Sort by date in ascending order (oldest first)
        df = df.sort_values("date", ascending=True)

        # Convert back to string format for storage
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

        # Write to a temporary file first
        temp_file = f"{STATISTICS_FILE}.tmp"
        df.to_csv(temp_file, index=False)

        # Rename to final file (atomic operation)
        if os.path.exists(STATISTICS_FILE):
            os.remove(STATISTICS_FILE)
        os.rename(temp_file, STATISTICS_FILE)

        logger.info(f"Statistics saved to {STATISTICS_FILE}")
    except Exception as e:
        logger.error(f"Error saving statistics: {e}")


def load_statistics():
    """
    Load statistics data from CSV file.

    Returns:
        Tuple (data, is_sample) where:
        - data: List of dictionaries containing statistics data
        - is_sample: Boolean indicating if sample data is being used
    """
    try:
        # Note: JIRA sync is handled manually via UI "Refresh Cache" button
        # No automatic sync on app start to respect user control

        if os.path.exists(STATISTICS_FILE):
            df = pd.read_csv(STATISTICS_FILE)

            # Ensure date column is in proper datetime format for sorting
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            # Sort by date in ascending order (oldest first)
            df = df.sort_values("date", ascending=True)

            # Convert back to string format for display
            df["date"] = df["date"].dt.strftime("%Y-%m-%d")

            data = df.to_dict("records")
            logger.info(f"Statistics loaded from {STATISTICS_FILE}")
            return data, False  # Return data and flag that it's not sample data
        else:
            logger.info("Statistics file not found, using sample data")

            # Make sure sample data is also sorted by date
            sample_df = generate_realistic_sample_data()
            sample_df["date"] = pd.to_datetime(sample_df["date"], errors="coerce")
            sample_df = sample_df.sort_values("date", ascending=True)
            sample_df["date"] = sample_df["date"].dt.strftime("%Y-%m-%d")

            return sample_df.to_dict("records"), True  # Return sample data with flag
    except Exception as e:
        logger.error(f"Error loading statistics: {e}")

        # Make sure sample data is also sorted by date
        sample_df = generate_realistic_sample_data()
        sample_df["date"] = pd.to_datetime(sample_df["date"], errors="coerce")
        sample_df = sample_df.sort_values("date", ascending=True)
        sample_df["date"] = sample_df["date"].dt.strftime("%Y-%m-%d")

        return sample_df.to_dict("records"), True  # Return sample data with flag


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
