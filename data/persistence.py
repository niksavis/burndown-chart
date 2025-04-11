"""
Data Persistence Module

This module handles saving and loading application data to/from disk.
It provides functions for managing settings (JSON) and statistics (CSV).
"""

#######################################################################
# IMPORTS
#######################################################################
import os
import json
import pandas as pd

# Import from configuration
from configuration import (
    logger,
    SETTINGS_FILE,
    STATISTICS_FILE,
    SAMPLE_DATA,
    DEFAULT_PERT_FACTOR,
    DEFAULT_TOTAL_ITEMS,
    DEFAULT_TOTAL_POINTS,
    DEFAULT_DEADLINE,
    DEFAULT_ESTIMATED_ITEMS,
    DEFAULT_ESTIMATED_POINTS,
)

#######################################################################
# DATA PERSISTENCE FUNCTIONS
#######################################################################


def save_settings(
    pert_factor,
    deadline,
    total_items,
    total_points,
    estimated_items=None,
    estimated_points=None,
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
        List of dictionaries containing statistics data or sample data if file not found
    """
    try:
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
            return data
        else:
            logger.info("Statistics file not found, using sample data")

            # Make sure sample data is also sorted by date
            sample_df = SAMPLE_DATA.copy()
            sample_df["date"] = pd.to_datetime(sample_df["date"], errors="coerce")
            sample_df = sample_df.sort_values("date", ascending=True)
            sample_df["date"] = sample_df["date"].dt.strftime("%Y-%m-%d")

            return sample_df.to_dict("records")
    except Exception as e:
        logger.error(f"Error loading statistics: {e}")

        # Make sure sample data is also sorted by date
        sample_df = SAMPLE_DATA.copy()
        sample_df["date"] = pd.to_datetime(sample_df["date"], errors="coerce")
        sample_df = sample_df.sort_values("date", ascending=True)
        sample_df["date"] = sample_df["date"].dt.strftime("%Y-%m-%d")

        return sample_df.to_dict("records")
