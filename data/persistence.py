"""
Data Persistence Module

This module handles saving and loading application data to/from disk.
It provides functions for managing settings and statistics using JSON files.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any

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
    jira_api_endpoint=None,
    jira_token=None,
    jira_story_points_field=None,
    jira_cache_max_size=None,
    jira_max_results=None,
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
        jira_api_endpoint: Full JIRA API endpoint URL
        jira_token: Personal access token for JIRA API
        jira_story_points_field: Custom field ID for story points
        jira_cache_max_size: Maximum cache size in MB
        jira_max_results: Maximum number of results to fetch from JIRA API
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
        "jira_api_endpoint": jira_api_endpoint
        if jira_api_endpoint is not None
        else "https://jira.atlassian.com/rest/api/2/search",
        "jira_token": jira_token if jira_token is not None else "",
        "jira_story_points_field": jira_story_points_field
        if jira_story_points_field is not None
        else "",
        "jira_cache_max_size": jira_cache_max_size
        if jira_cache_max_size is not None
        else 100,
        "jira_max_results": jira_max_results if jira_max_results is not None else 1000,
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
        "jira_api_endpoint": "https://jira.atlassian.com/rest/api/2/search",
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
                "https://jira.atlassian.com/rest/api/2/search",  # Default API endpoint for migration
                "",  # Empty JIRA token for migration
                "",  # Empty story points field for migration
                100,  # Default cache size for migration
                1000,  # Default max results for migration
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
    Save statistics data to unified JSON file.

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

        # Convert back to list of dictionaries
        statistics_data = df.to_dict("records")

        # Load current unified data
        unified_data = load_unified_project_data()

        # Update statistics in unified data
        unified_data["statistics"] = statistics_data

        # Update metadata - preserve existing source and jira_query unless explicitly overriding
        unified_data["metadata"].update(
            {
                "last_updated": datetime.now().isoformat(),
            }
        )

        # Save the unified data
        save_unified_project_data(unified_data)

        logger.info(f"Statistics saved to {PROJECT_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving statistics: {e}")


def save_statistics_from_csv_import(data):
    """
    Save statistics data from CSV import to unified JSON file.
    This function specifically handles CSV imports and sets appropriate metadata.

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

        # Convert back to list of dictionaries
        statistics_data = df.to_dict("records")

        # Load current unified data
        unified_data = load_unified_project_data()

        # Update statistics in unified data
        unified_data["statistics"] = statistics_data

        # Update metadata specifically for CSV import
        unified_data["metadata"].update(
            {
                "source": "csv_import",  # Set proper source for CSV uploads
                "last_updated": datetime.now().isoformat(),
                "jira_query": "",  # Clear JIRA-specific fields for CSV import
            }
        )

        # Save the unified data
        save_unified_project_data(unified_data)

        logger.info(f"Statistics from CSV import saved to {PROJECT_DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving CSV import statistics: {e}")


def load_statistics():
    """
    Load statistics data from unified project data JSON file.

    Returns:
        Tuple (data, is_sample) where:
        - data: List of dictionaries containing statistics data
        - is_sample: Boolean indicating if sample data is being used
    """
    try:
        # Load from unified project data JSON
        project_data = load_project_data()

        if "statistics" in project_data and len(project_data["statistics"]) > 0:
            # Load statistics from project data
            statistics = project_data["statistics"]

            # Ensure data is sorted by date (already should be from JIRA sync)
            statistics_df = pd.DataFrame(statistics)
            statistics_df["date"] = pd.to_datetime(
                statistics_df["date"], errors="coerce"
            )
            statistics_df = statistics_df.sort_values("date", ascending=True)
            statistics_df["date"] = statistics_df["date"].dt.strftime("%Y-%m-%d")

            data = statistics_df.to_dict("records")
            logger.info(f"Statistics loaded from {PROJECT_DATA_FILE}")
            return data, False  # Return data and flag that it's not sample data
        else:
            logger.info("No statistics found in project data, using sample data")

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


#######################################################################
# UNIFIED DATA FUNCTIONS (v2.0)
#######################################################################


def load_unified_project_data():
    """
    Load unified project data (Phase 3).

    Returns:
        Dict: Unified project data structure
    """
    from data.schema import get_default_unified_data, validate_project_data_structure

    try:
        if not os.path.exists(PROJECT_DATA_FILE):
            return get_default_unified_data()

        with open(PROJECT_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate and migrate if necessary
        if not data.get("metadata", {}).get("version"):
            data = _migrate_legacy_project_data(data)

        # Validate structure
        if not validate_project_data_structure(data):
            logger.warning("⚠️ Invalid unified data structure, using defaults")
            return get_default_unified_data()

        return data

    except Exception as e:
        logger.error(f"❌ Error loading unified project data: {e}")
        return get_default_unified_data()


def save_unified_project_data(data):
    """
    Save unified project data (Phase 3).

    Args:
        data: Unified project data dictionary
    """
    try:
        with open(PROJECT_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("✅ Saved unified project data")
    except Exception as e:
        logger.error(f"❌ Error saving unified project data: {e}")
        raise


def _migrate_legacy_project_data(data):
    """
    Migrate legacy project data format to v2.0.

    Args:
        data: Legacy project data structure

    Returns:
        Dict: Migrated v2.0 data structure
    """
    from data.schema import get_default_unified_data

    unified_data = get_default_unified_data()

    # Migrate existing project scope data if present
    if isinstance(data, dict):
        unified_data["project_scope"].update(
            {
                "total_items": data.get("total_items", 0),
                "total_points": data.get("total_points", 0),
                "estimated_items": data.get("estimated_items", 0),
                "estimated_points": data.get("estimated_points", 0),
                "remaining_items": data.get("total_items", 0),
                "remaining_points": data.get("total_points", 0),
            }
        )

        # Preserve any existing metadata
        if "metadata" in data:
            unified_data["metadata"].update(data["metadata"])

    unified_data["metadata"]["source"] = "legacy_migration"
    unified_data["metadata"]["version"] = "2.0"
    unified_data["metadata"]["last_updated"] = datetime.now().isoformat()

    return unified_data


def get_project_statistics():
    """
    Get statistics from unified data structure.

    Returns:
        List[Dict]: Statistics array
    """
    unified_data = load_unified_project_data()
    return unified_data.get("statistics", [])


def get_project_scope():
    """
    Get project scope from unified data structure.

    Returns:
        Dict: Project scope data
    """
    unified_data = load_unified_project_data()
    return unified_data.get("project_scope", {})


def update_project_scope(scope_data):
    """
    Update project scope in unified data structure.

    Args:
        scope_data: Dictionary with scope fields to update
    """
    unified_data = load_unified_project_data()
    unified_data["project_scope"].update(scope_data)
    unified_data["metadata"]["last_updated"] = datetime.now().isoformat()
    save_unified_project_data(unified_data)


def update_project_scope_from_jira(
    jql_query: str | None = None, ui_config: dict | None = None
):
    """
    Update project scope using JIRA scope calculation.

    Args:
        jql_query: Optional JQL query to use for JIRA sync
        ui_config: Optional UI configuration to use

    Returns:
        Tuple (success: bool, message: str)
    """
    try:
        from data.jira_simple import sync_jira_scope_and_data

        # Get JIRA scope data
        success, message, scope_data = sync_jira_scope_and_data(jql_query, ui_config)

        if not success:
            return success, message

        # Update project scope with JIRA data
        if scope_data:
            # Add metadata to indicate JIRA source
            scope_data["source"] = "jira"
            scope_data["last_jira_sync"] = datetime.now().isoformat()
            update_project_scope(scope_data)

        return True, f"Project scope updated from JIRA: {message}"

    except Exception as e:
        logger.error(f"Error updating project scope from JIRA: {e}")
        return False, f"Failed to update scope from JIRA: {e}"


def calculate_project_scope_from_jira(
    jql_query: str | None = None, ui_config: dict | None = None
):
    """
    Calculate project scope from JIRA without saving to file.
    This is used for "Calculate Scope" action which should only display results.

    Args:
        jql_query: Optional JQL query to use for JIRA sync
        ui_config: Optional UI configuration to use

    Returns:
        Tuple (success: bool, message: str, scope_data: dict)
    """
    try:
        from data.jira_simple import (
            get_jira_config,
            validate_jira_config,
            fetch_jira_issues,
        )
        from data.jira_scope_calculator import calculate_jira_project_scope

        # Load configuration
        if ui_config:
            config = ui_config.copy()
            if jql_query:
                config["jql_query"] = jql_query
        else:
            config = get_jira_config(jql_query)

        # Validate configuration
        is_valid, message = validate_jira_config(config)
        if not is_valid:
            return False, f"Configuration invalid: {message}", {}

        # Fetch issues from JIRA (or cache)
        fetch_success, issues = fetch_jira_issues(config)
        if not fetch_success:
            return False, "Failed to fetch JIRA data", {}

        # Calculate scope (no saving to file!)
        points_field = config.get("story_points_field", "").strip()
        if not points_field:
            points_field = ""

        scope_data = calculate_jira_project_scope(issues, points_field, config)
        if not scope_data:
            return False, "Failed to calculate JIRA project scope", {}

        return True, "Project scope calculated successfully", scope_data

    except Exception as e:
        logger.error(f"Error calculating project scope from JIRA: {e}")
        return False, f"Failed to calculate scope from JIRA: {e}", {}


def add_project_statistic(stat_data):
    """
    Add a new statistic entry to unified data structure.

    Args:
        stat_data: Dictionary with statistic fields
    """
    unified_data = load_unified_project_data()
    unified_data["statistics"].append(stat_data)
    unified_data["metadata"]["last_updated"] = datetime.now().isoformat()
    save_unified_project_data(unified_data)


#######################################################################
# LEGACY COMPATIBILITY LAYER
#######################################################################


def load_statistics_legacy():
    """
    Legacy function that loads statistics in old format for backward compatibility.

    Returns:
        Tuple (data, is_sample): Statistics data and sample flag
    """
    # First try to load from unified format
    try:
        statistics = get_project_statistics()
        if statistics:
            # Convert unified format back to legacy format
            legacy_data = []
            for stat in statistics:
                legacy_data.append(
                    {
                        "date": stat.get("date", ""),
                        "completed_items": stat.get("completed_items", 0),
                        "completed_points": stat.get("completed_points", 0),
                        "created_items": stat.get("created_items", 0),
                        "created_points": stat.get("created_points", 0),
                    }
                )
            return legacy_data, False
    except Exception as e:
        logger.warning(f"Could not load from unified format: {e}")

    # Fall back to original CSV loading
    return load_statistics()


def load_project_data_legacy():
    """
    Legacy function that loads project data in old format for backward compatibility.

    Returns:
        Dict: Project data in legacy format
    """
    # First try to load from unified format
    try:
        scope = get_project_scope()
        if scope:
            return {
                "total_items": scope.get("total_items", 0),
                "total_points": scope.get("total_points", 0),
                "estimated_items": scope.get("estimated_items", 0),
                "estimated_points": scope.get("estimated_points", 0),
            }
    except Exception as e:
        logger.warning(f"Could not load from unified format: {e}")

    # Fall back to original project data loading
    return load_project_data()


def save_jira_data_unified(statistics_data, project_scope_data, jira_config=None):
    """
    Save both JIRA statistics and project scope to unified data structure.

    This replaces the old CSV-based approach with unified JSON storage.

    Args:
        statistics_data: List of dictionaries containing statistics data
        project_scope_data: Dictionary containing project scope data
        jira_config: Optional JIRA configuration dictionary for metadata
    """
    try:
        # Load current unified data
        unified_data = load_unified_project_data()

        # Update statistics
        unified_data["statistics"] = statistics_data

        # Update project scope
        unified_data["project_scope"] = project_scope_data

        # Extract JQL query from config or fallback
        jql_query = ""
        if jira_config:
            jql_query = jira_config.get(
                "jql_query", ""
            )  # Update metadata with proper JIRA information
        unified_data["metadata"].update(
            {
                "source": "jira_calculated",  # Correct source for JIRA data
                "last_updated": datetime.now().isoformat(),
                "version": "2.0",
                "jira_query": jql_query,
                # Remove calculation_method - it's redundant with project_scope.calculation_metadata.method
            }
        )

        # Save the unified data
        save_unified_project_data(unified_data)

        logger.info("✅ JIRA data saved to unified project data structure")
        return True

    except Exception as e:
        logger.error(f"❌ Error saving JIRA data to unified structure: {e}")
        return False


def migrate_csv_to_json() -> Dict[str, Any]:
    """
    Migrate existing CSV data to unified JSON format.

    Returns:
        Dict: The migrated unified data structure
    """
    # Load existing data
    csv_data, is_sample = load_statistics()
    project_data = load_project_data()

    # Convert CSV to statistics array
    statistics = []
    if csv_data and isinstance(csv_data, list):
        for row in csv_data:
            statistics.append(
                {
                    "date": str(row.get("date", "")),
                    "completed_items": int(row.get("completed_items", 0)),
                    "completed_points": int(row.get("completed_points", 0)),
                    "created_items": int(row.get("created_items", 0)),
                    "created_points": int(row.get("created_points", 0)),
                    "velocity_items": int(
                        row.get("completed_items", 0)
                    ),  # Use completed as velocity
                    "velocity_points": int(row.get("completed_points", 0)),
                }
            )

    # Create unified structure
    unified_data = {
        "project_scope": {
            "total_items": project_data.get("total_items", 0),
            "total_points": project_data.get("total_points", 0),
            "estimated_items": project_data.get("estimated_items", 0),
            "estimated_points": project_data.get("estimated_points", 0),
            "remaining_items": project_data.get("total_items", 0),  # Default to total
            "remaining_points": project_data.get("total_points", 0),
        },
        "statistics": statistics,
        "metadata": {
            "source": "csv_import" if not is_sample else "sample_data",
            "last_updated": datetime.now().isoformat(),
            "version": "2.0",
            "jira_query": "",
        },
    }

    # Save unified data
    save_unified_project_data(unified_data)

    # Create backup of old files if not sample data
    if not is_sample:
        _backup_legacy_files()

    return unified_data


def _backup_legacy_files() -> None:
    """Create backup copies of CSV and old JSON files."""
    import shutil

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if os.path.exists("forecast_statistics.csv"):
        backup_name = f"backup_forecast_statistics_{timestamp}.csv"
        shutil.copy2("forecast_statistics.csv", backup_name)
        print(f"📁 Created backup: {backup_name}")

    # Note: Don't backup project_data.json as we're updating it in place
    # The legacy migration preserves existing data
