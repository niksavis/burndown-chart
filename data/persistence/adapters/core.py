import json
import os
import threading
from typing import Any

import pandas as pd

"""
Data Persistence Module

This module handles saving and loading application data to/from disk.
It provides functions for managing settings and statistics using JSON files.
"""

_file_locks: dict[str, threading.Lock] = {}
_lock_manager = threading.Lock()


def _get_file_lock(file_path: str) -> threading.Lock:
    with _lock_manager:
        if file_path not in _file_locks:
            _file_locks[file_path] = threading.Lock()
        return _file_locks[file_path]


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "isoformat"):
            return o.isoformat()
        if pd.isna(o):
            return None
        if hasattr(o, "item"):
            return o.item()
        return super().default(o)


def convert_timestamps_to_strings(data: Any) -> Any:

    if isinstance(data, dict):
        return {k: convert_timestamps_to_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_timestamps_to_strings(item) for item in data]
    elif hasattr(data, "isoformat"):
        return data.isoformat()
    elif pd.isna(data):
        return None
    elif hasattr(data, "item"):
        return data.item()
    return data


def should_sync_jira() -> bool:

    jira_url = os.getenv("JIRA_URL", "")
    jira_default_jql = os.getenv("JIRA_DEFAULT_JQL", "")

    return bool(jira_url and (jira_default_jql or True))
