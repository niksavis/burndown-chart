"""
JIRA API Integration Module

Provides JIRA API integration for the burndown chart application.
This module is refactored from the monolithic jira_simple.py (3,593 lines)
into focused, maintainable sub-modules following architectural guidelines.

Public API:
- Configuration: get_jira_config, validate_jira_config, test_jira_connection
- Data fetching: fetch_jira_issues, fetch_jira_issues_with_changelog
- Synchronization: sync_jira_scope_and_data, sync_jira_data, fetch_changelog_on_demand
- Transformation: jira_to_csv_format
"""

# Configuration management
from data.jira.config import (
    get_jira_config,
    validate_jira_config,
    construct_jira_endpoint,
    test_jira_connection,
    generate_config_hash,
    JIRA_CACHE_FILE,
    JIRA_CHANGELOG_CACHE_FILE,
    DEFAULT_CACHE_MAX_SIZE_MB,
    CACHE_VERSION,
    CHANGELOG_CACHE_VERSION,
    CACHE_EXPIRATION_HOURS,
)

# Field utilities
from data.jira.field_utils import (
    extract_jira_field_id,
    extract_story_points_value,
)

# Validation
from data.jira.validation import (
    validate_jql_for_scriptrunner,
    test_jql_query,
)

# Cache validation
from data.jira.cache_validator import (
    validate_cache_file,
    get_cache_status,
    invalidate_changelog_cache,
)

# Issue counter
from data.jira.issue_counter import check_jira_issue_count

__all__ = [
    # Configuration
    "get_jira_config",
    "validate_jira_config",
    "construct_jira_endpoint",
    "test_jira_connection",
    "generate_config_hash",
    # Field utilities
    "extract_jira_field_id",
    "extract_story_points_value",
    # Validation
    "validate_jql_for_scriptrunner",
    "test_jql_query",
    # Cache validation
    "validate_cache_file",
    "get_cache_status",
    "invalidate_changelog_cache",
    # Issue counter
    "check_jira_issue_count",
    # Constants
    "JIRA_CACHE_FILE",
    "JIRA_CHANGELOG_CACHE_FILE",
    "DEFAULT_CACHE_MAX_SIZE_MB",
    "CACHE_VERSION",
    "CHANGELOG_CACHE_VERSION",
    "CACHE_EXPIRATION_HOURS",
]
