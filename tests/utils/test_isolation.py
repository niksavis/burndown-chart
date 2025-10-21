#!/usr/bin/env python3
"""
Test utilities to ensure tests never modify real app configuration

This module provides utilities for tests to use temporary configuration
without affecting the real app_settings.json and project_data.json files.
"""

import json
import os
import tempfile
from contextlib import contextmanager
from typing import Any, Dict, Optional
from unittest.mock import patch


@contextmanager
def isolated_app_settings(initial_settings: Optional[Dict[str, Any]] = None):
    """
    Context manager that creates isolated app settings for testing.

    This ensures tests never modify the real app_settings.json file.

    Args:
        initial_settings: Optional dict to initialize the temporary settings

    Usage:
        with isolated_app_settings({"pert_factor": 2.0}) as temp_settings_file:
            # Your test code here
            # All app settings operations will use temp_settings_file
            pass
    """

    # Create temporary settings file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

        # Initialize with provided settings or defaults
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
        # Patch the settings file path
        with patch("data.persistence.SETTINGS_FILE", temp_file):
            yield temp_file
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@contextmanager
def isolated_project_data(initial_data: Optional[Dict[str, Any]] = None):
    """
    Context manager that creates isolated project data for testing.

    This ensures tests never modify the real project_data.json file.

    Args:
        initial_data: Optional dict to initialize the temporary project data

    Usage:
        with isolated_project_data({"statistics": []}) as temp_data_file:
            # Your test code here
            # All project data operations will use temp_data_file
            pass
    """

    # Create temporary project data file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

        # Initialize with provided data or defaults
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
        # Patch the project data file path
        with patch("data.persistence.PROJECT_DATA_FILE", temp_file):
            yield temp_file
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@contextmanager
def isolated_jira_cache(initial_cache: Optional[Dict[str, Any]] = None):
    """
    Context manager that creates isolated JIRA cache for testing.

    This ensures tests never modify the real jira_cache.json file.

    Args:
        initial_cache: Optional dict to initialize the temporary cache

    Usage:
        with isolated_jira_cache() as temp_cache_file:
            # Your test code here
            # All JIRA cache operations will use temp_cache_file
            pass
    """

    # Create temporary cache file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_file = f.name

        # Initialize with provided cache or defaults
        if initial_cache is None:
            initial_cache = {
                "timestamp": "2025-01-01T00:00:00",
                "jql_query": "project = TESTPROJECT",
                "fields_requested": "key,created,resolutiondate,status",
                "issues": [],
            }

        json.dump(initial_cache, f, indent=2)

    try:
        # Patch the cache file path
        with patch("data.jira_simple.JIRA_CACHE_FILE", temp_file):
            yield temp_file
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def mock_jira_api_calls():
    """
    Decorator or context manager to mock all JIRA API calls.

    This prevents tests from making real HTTP requests to JIRA servers.

    Usage as decorator:
        @mock_jira_api_calls()
        def test_my_function():
            pass

    Usage as context manager:
        with mock_jira_api_calls():
            # Your test code here
            pass
    """

    def mock_fetch_jira_issues(config, max_results=None):
        """Mock implementation that returns test data instead of making API calls"""
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
