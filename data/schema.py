"""
Data schema for the burndown chart application.

Defines the structure of data used across the application.
"""

from typing import Dict, Any

#######################################################################
# CSV SCHEMA
#######################################################################

STATISTICS_COLUMNS = [
    "date",  # Date of work (YYYY-MM-DD format)
    "completed_items",  # Number of items completed on that date
    "completed_points",  # Number of points completed on that date
    "created_items",  # Number of items created on that date (for scope change tracking)
    "created_points",  # Number of points created on that date (for scope change tracking)
]

#######################################################################
# DATA STRUCTURES
#######################################################################

# Default empty statistics data structure
DEFAULT_STATISTICS = {
    "data": [],
    "baseline": {
        "items": 0,  # Initial scope (items) at project start
        "points": 0,  # Initial scope (points) at project start
        "date": "",  # Date when baseline was established
    },
    "timestamp": "",  # Last update timestamp
}

# Default settings structure
DEFAULT_SETTINGS = {
    # Scope change settings
    "scope_change_threshold": 20,  # Default threshold for scope change alerts (%)
    "track_scope_changes": True,  # Whether to track scope changes
    "scope_change_throughput_threshold": 1.2,  # Alert when scope grows 20% faster than throughput
    # Performance optimization settings
    "forecast_max_days": 3653,  # Maximum forecast horizon in days (10 years absolute cap)
    "forecast_max_points": 150,  # Maximum data points per forecast line
    "pessimistic_multiplier_cap": 5,  # Max ratio of pessimistic to optimistic forecast
}

# For backwards compatibility
DEFAULT_SETTINGS["scope_creep_threshold"] = DEFAULT_SETTINGS["scope_change_threshold"]

#######################################################################
# UNIFIED JSON DATA SCHEMA (v2.0)
#######################################################################

# JSON Schema for unified project data
PROJECT_DATA_SCHEMA = {
    "project_scope": {
        "total_items": int,
        "total_points": int,
        "estimated_items": int,
        "estimated_points": int,
        "remaining_items": int,
        "remaining_points": int,
    },
    "statistics": [
        {
            "date": str,  # ISO format YYYY-MM-DD
            "completed_items": int,
            "completed_points": int,
            "created_items": int,
            "created_points": int,
            "velocity_items": int,  # Weekly completion rate
            "velocity_points": int,  # Weekly point completion rate
        }
    ],
    "metadata": {
        "source": str,  # "jira_calculated", "manual", "csv_import"
        "last_updated": str,  # ISO datetime
        "version": str,  # Data format version
        "jira_query": str,  # JQL used for calculation
    },
}


def validate_project_data_structure(data: Dict[str, Any]) -> bool:
    """
    Validate project data structure against the schema.

    Args:
        data: Project data dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
    required_keys = ["project_scope", "statistics", "metadata"]

    if not all(key in data for key in required_keys):
        return False

    # Validate project_scope structure
    scope_keys = ["total_items", "total_points", "estimated_items", "estimated_points"]
    if not all(key in data["project_scope"] for key in scope_keys):
        return False

    # Validate statistics structure
    if not isinstance(data["statistics"], list):
        return False

    for stat in data["statistics"]:
        if not isinstance(stat, dict):
            return False
        stat_keys = [
            "date",
            "completed_items",
            "completed_points",
            "created_items",
            "created_points",
        ]
        if not all(key in stat for key in stat_keys):
            return False

    # Validate metadata structure
    if not isinstance(data["metadata"], dict):
        return False

    return True


def get_default_unified_data() -> Dict[str, Any]:
    """
    Return default unified data structure.

    Returns:
        Dict: Default unified project data structure
    """
    from datetime import datetime

    return {
        "project_scope": {
            "total_items": 0,
            "total_points": 0,
            "estimated_items": 0,
            "estimated_points": 0,
            "remaining_items": 0,
            "remaining_points": 0,
        },
        "statistics": [],
        "metadata": {
            "source": "manual",
            "last_updated": datetime.now().isoformat(),
            "version": "2.0",
            "jira_query": "",
        },
    }
