"""Data persistence adapters - File locking, JSON encoding, helper functions."""

# Standard library imports
import json
import os
import threading
from typing import Any

# Third-party library imports
import pandas as pd

# Application imports

"""
Data Persistence Module

This module handles saving and loading application data to/from disk.
It provides functions for managing settings and statistics using JSON files.
"""

#######################################################################
# FILE LOCKING
#######################################################################
# Application imports - lazy import constants to avoid circular import
# Constants are imported inside functions to break circular dependency:
# configuration.settings -> logging_config -> data.installation_context -> data -> adapters
# Logger is safe to import at module level (doesn't trigger the chain)
# File locking to prevent race conditions during concurrent writes
_file_locks: dict[str, threading.Lock] = {}
_lock_manager = threading.Lock()


def _get_file_lock(file_path: str) -> threading.Lock:
    """Get or create a lock for a specific file path."""
    with _lock_manager:
        if file_path not in _file_locks:
            _file_locks[file_path] = threading.Lock()
        return _file_locks[file_path]


#######################################################################
# JSON SERIALIZATION HELPERS
#######################################################################


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and pandas Timestamp objects."""

    def default(self, o):
        """Convert non-serializable objects to JSON-compatible formats."""
        # Handle pandas Timestamp
        if hasattr(o, "isoformat"):
            return o.isoformat()
        # Handle pandas NaT (Not a Time)
        if pd.isna(o):
            return None
        # Handle numpy integers
        if hasattr(o, "item"):
            return o.item()
        return super().default(o)


def convert_timestamps_to_strings(data: Any) -> Any:
    """
    Recursively convert pandas Timestamp objects to ISO format strings.

    Args:
        data: Data structure that may contain Timestamp objects

    Returns:
        Data with all Timestamps converted to strings
    """
    if isinstance(data, dict):
        return {k: convert_timestamps_to_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_timestamps_to_strings(item) for item in data]
    elif hasattr(data, "isoformat"):
        # pandas Timestamp or datetime
        return data.isoformat()
    elif pd.isna(data):
        # pandas NaT or NaN
        return None
    elif hasattr(data, "item"):
        # numpy scalar types
        return data.item()
    return data


#######################################################################
# DATA PERSISTENCE FUNCTIONS
#######################################################################


def should_sync_jira() -> bool:
    """
    Check if JIRA sync should be performed based on configuration.

    Returns:
        bool: True if JIRA is enabled and configured
    """
    # Check if JIRA is enabled via environment variables
    jira_url = os.getenv("JIRA_URL", "")
    jira_default_jql = os.getenv("JIRA_DEFAULT_JQL", "")

    return bool(
        jira_url and (jira_default_jql or True)
    )  # Always true if URL exists, JQL has default
