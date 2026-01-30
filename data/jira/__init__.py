"""
JIRA API Integration Module

Provides JIRA API integration for the burndown chart application.
This module is refactored from the monolithic jira_simple.py (3,593 lines)
into focused, maintainable sub-modules following architectural guidelines.

Public API:
- Configuration: get_jira_config, validate_jira_config, test_jira_connection
- Data transformation: jira_to_csv_format
- Field utilities: extract_jira_field_id, extract_story_points_value
- Cache management: validate_cache_file, get_cache_status, invalidate_changelog_cache
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

# Data transformation
from data.jira.data_transformer import jira_to_csv_format

# Two-phase fetch
from data.jira.two_phase_fetch import (
    should_use_two_phase_fetch,
    fetch_jira_issues_two_phase,
)

# Phase 7: Main fetch and sync operations
from data.jira.main_fetch import fetch_jira_issues
from data.jira.scope_sync import sync_jira_scope_and_data, sync_jira_data
from data.jira.changelog_fetcher import (
    fetch_jira_issues_with_changelog,
    fetch_changelog_on_demand,
)

# Fetch utilities (paginated fetch helper)
from data.jira.fetch_utils import fetch_jira_paginated

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
    # Data transformation
    "jira_to_csv_format",
    # Two-phase fetch
    "should_use_two_phase_fetch",
    "fetch_jira_issues_two_phase",
    # Phase 7: Main operations
    "fetch_jira_issues",
    "sync_jira_scope_and_data",
    "sync_jira_data",
    "fetch_jira_issues_with_changelog",
    "fetch_changelog_on_demand",
    # Fetch utilities
    "fetch_jira_paginated",
    # Constants
    "JIRA_CACHE_FILE",
    "JIRA_CHANGELOG_CACHE_FILE",
    "DEFAULT_CACHE_MAX_SIZE_MB",
    "CACHE_VERSION",
    "CHANGELOG_CACHE_VERSION",
    "CACHE_EXPIRATION_HOURS",
]
