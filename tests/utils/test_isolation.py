#!/usr/bin/env python3


import json
import os
import tempfile
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch


@contextmanager
def isolated_app_settings(initial_settings: dict[str, Any] | None = None):

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

        if initial_settings is None:
            initial_settings = {
                "pert_factor": 1.0,
                "deadline": "2025-12-31",
                "data_points_count": 6,
                "show_milestone": False,
                "milestone": None,
                "show_points": True,
                "jql_query": "project = TESTPROJECT",
                "jira_api_endpoint": "https://test-jira.example.com/rest/api/2/search",
                "jira_token": "test-token",
                "jira_story_points_field": "customfield_10002",
                "jira_cache_max_size": 100,
                "jira_max_results": 100,
                "last_used_data_source": "CSV",
                "active_jql_profile_id": "",
            }

        json.dump(initial_settings, f, indent=2)

    try:
        with patch("data.persistence.APP_SETTINGS_FILE", temp_file):
            yield temp_file
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@contextmanager
def isolated_project_data(initial_data: dict[str, Any] | None = None):

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

        if initial_data is None:
            initial_data = {
                "project_scope": {
                    "total_items": 0,
                    "total_points": 0,
                    "estimated_items": 0,
                    "estimated_points": 0,
                },
                "statistics": [],
                "metadata": {
                    "data_source": "CSV",
                    "last_updated": "2025-01-01T00:00:00",
                },
            }

        json.dump(initial_data, f, indent=2)

    try:
        with patch("data.persistence.PROJECT_DATA_FILE", temp_file):
            yield temp_file
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@contextmanager
def isolated_jira_cache(initial_cache: dict[str, Any] | None = None):

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

        if initial_cache is None:
            initial_cache = {
                "timestamp": "2025-01-01T00:00:00",
                "jql_query": "project = TESTPROJECT",
                "fields_requested": "key,created,resolutiondate,status",
                "issues": [],
            }

        json.dump(initial_cache, f, indent=2)

    try:
        with patch("data.jira_simple.JIRA_CACHE_FILE", temp_file):
            yield temp_file
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def mock_jira_api_calls():

    def mock_fetch_jira_issues(config, max_results=None):
        return True, [
            {
                "key": "TEST-1",
                "fields": {
                    "created": "2025-01-01T10:00:00.000Z",
                    "resolutiondate": "2025-01-15T10:00:00.000Z",
                    "status": {"name": "Done"},
                    "customfield_10002": 5,
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "created": "2025-01-05T10:00:00.000Z",
                    "resolutiondate": None,
                    "status": {"name": "In Progress"},
                    "customfield_10002": 3,
                },
            },
        ]

    return patch(
        "data.jira_simple.fetch_jira_issues", side_effect=mock_fetch_jira_issues
    )
