"""
Data schema for the burndown chart application.

Defines the structure of data used across the application.
"""

#######################################################################
# CSV SCHEMA
#######################################################################

STATISTICS_COLUMNS = [
    "date",  # Date of work (YYYY-MM-DD format)
    "completed_items",  # Number of items completed on that date
    "completed_points",  # Number of points completed on that date
    "created_items",  # Number of items created on that date (for scope creep tracking)
    "created_points",  # Number of points created on that date (for scope creep tracking)
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
    # Scope creep settings
    "scope_creep_threshold": 20,  # Default threshold for scope creep alerts (%)
    "track_scope_changes": True,  # Whether to track scope changes
}
