"""
JIRA API Integration Module

This module provides minimal JIRA API integration for the burndown chart application.
It fetches JIRA issues and transforms them to match the existing CSV statistics format.
"""

#######################################################################
# IMPORTS
#######################################################################
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import requests

from configuration import logger

#######################################################################
# CONFIGURATION
#######################################################################

JIRA_CACHE_FILE = "jira_cache.json"
DEFAULT_CACHE_MAX_SIZE_MB = 100

#######################################################################
# CORE JIRA FUNCTIONS
#######################################################################


def get_jira_config(settings_jql_query: str | None = None) -> Dict:
    """
    Load JIRA configuration with priority hierarchy: UI settings → App Settings → Environment → Default.

    Args:
        settings_jql_query: JQL query from UI settings (highest priority)

    Returns:
        Dictionary containing JIRA configuration
    """
    # Load app settings first
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
    except Exception:
        app_settings = {}

    # Configuration hierarchy: UI settings → App settings → Environment → Default
    jql_query = (
        settings_jql_query  # UI settings (highest priority)
        or app_settings.get("jql_query", "")  # App settings
        or os.getenv("JIRA_DEFAULT_JQL", "")  # Environment variable
        or "project = JRASERVER"  # Default fallback
    )

    config = {
        "jql_query": jql_query,
        "api_endpoint": (
            app_settings.get("jira_api_endpoint", "")  # App settings
            or os.getenv("JIRA_API_ENDPOINT", "")  # Environment variable
            or "https://jira.atlassian.com/rest/api/2/search"  # Default fallback
        ),
        "token": (
            app_settings.get("jira_token", "")  # App settings
            or os.getenv("JIRA_TOKEN", "")  # Environment variable
            or ""  # Default
        ),
        "story_points_field": (
            app_settings.get("jira_story_points_field", "")  # App settings
            or os.getenv("JIRA_STORY_POINTS_FIELD", "")  # Environment variable
            or ""  # Default
        ),
        "cache_max_size_mb": int(
            app_settings.get(
                "jira_cache_max_size", DEFAULT_CACHE_MAX_SIZE_MB
            )  # App settings
            or os.getenv(
                "JIRA_CACHE_MAX_SIZE_MB", DEFAULT_CACHE_MAX_SIZE_MB
            )  # Environment variable
        ),
    }

    return config


def validate_jira_config(config: Dict) -> Tuple[bool, str]:
    """Validate JIRA configuration and custom fields."""
    api_endpoint = config.get("api_endpoint", "")
    if not api_endpoint:
        return False, "JIRA API endpoint is required"

    if not config["jql_query"]:
        return False, "JQL query is required"

    # Basic JQL validation (optional - JQL is complex, so we do minimal validation)
    jql_query = config["jql_query"].strip()
    if len(jql_query) < 5:  # Minimum reasonable JQL length
        return False, "JQL query is too short"

    # Basic URL validation for API endpoint
    if not api_endpoint.startswith(("http://", "https://")):
        return False, "JIRA API endpoint must be a valid URL (http:// or https://)"

    return True, "Configuration valid"


def fetch_jira_issues(config: Dict, max_results: int = 1000) -> Tuple[bool, List[Dict]]:
    """Execute JQL query and return issues."""
    try:
        # Use the JQL query directly from configuration
        jql = config["jql_query"]

        # Get JIRA API endpoint (full URL)
        api_endpoint = config.get("api_endpoint", "")
        if not api_endpoint:
            logger.error("JIRA API endpoint not configured")
            return False, []

        # Use the full API endpoint directly
        url = api_endpoint

        # Headers
        headers = {"Accept": "application/json"}
        if config["token"]:
            headers["Authorization"] = f"Bearer {config['token']}"

        # Parameters - only fetch required fields
        # Include story points field only if specified
        base_fields = "key,created,resolutiondate,status"
        if config.get("story_points_field") and config["story_points_field"].strip():
            fields = f"{base_fields},{config['story_points_field']}"
        else:
            fields = base_fields

        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": fields,
        }

        logger.info(f"Fetching JIRA issues with JQL: {jql}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        issues = data.get("issues", [])

        logger.info(f"Fetched {len(issues)} JIRA issues")
        return True, issues

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching JIRA issues: {e}")
        return False, []


def cache_jira_response(
    data: List[Dict],
    jql_query: str = "",
    fields_requested: str = "",
    cache_file: str = JIRA_CACHE_FILE,
) -> bool:
    """Save raw JIRA JSON response to cache file with query and field tracking."""
    try:
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "jql_query": jql_query,  # Track which JQL query was used
            "fields_requested": fields_requested,  # Track which fields were requested
            "issues": data,
            "total_issues": len(data),
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        logger.info(
            f"Cached {len(data)} JIRA issues to {cache_file} (JQL: {jql_query}, Fields: {fields_requested})"
        )
        return True

    except Exception as e:
        logger.error(f"Error caching JIRA response: {e}")
        return False


def load_jira_cache(
    current_jql_query: str = "",
    current_fields: str = "",
    cache_file: str = JIRA_CACHE_FILE,
) -> Tuple[bool, List[Dict]]:
    """Load cached JIRA JSON response from file, checking if JQL query and fields match."""
    try:
        if not os.path.exists(cache_file):
            return False, []

        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        # Check if the cached query matches the current query
        cached_jql = cache_data.get("jql_query", "")
        if cached_jql != current_jql_query:
            logger.info(
                f"Cache JQL query mismatch. Cached: '{cached_jql}', Current: '{current_jql_query}'. Cache invalidated."
            )
            return False, []

        # Check if the cached fields match the current fields (NEW!)
        cached_fields = cache_data.get("fields_requested", "")
        if cached_fields and current_fields and cached_fields != current_fields:
            logger.info(
                f"Cache fields mismatch. Cached: '{cached_fields}', Current: '{current_fields}'. Cache invalidated."
            )
            return False, []

        # If no field info in old cache, check if current config needs story points field
        if not cached_fields and current_fields:
            # Extract story points field from current fields
            base_fields = "key,created,resolutiondate,status"
            if current_fields != base_fields:  # User has story points field configured
                logger.info(
                    "Cache has no field info, but story points field is configured. Cache invalidated for field compatibility."
                )
                return False, []

        issues = cache_data.get("issues", [])
        logger.info(
            f"Loaded {len(issues)} JIRA issues from cache (JQL: {cached_jql}, Fields: {cached_fields or 'base'})"
        )
        return True, issues

    except Exception as e:
        logger.error(f"Error loading JIRA cache: {e}")
        return False, []


def validate_cache_file(
    cache_file: str = JIRA_CACHE_FILE, max_size_mb: int = DEFAULT_CACHE_MAX_SIZE_MB
) -> bool:
    """Validate cache file size and integrity."""
    try:
        if not os.path.exists(cache_file):
            return True  # No cache file is valid

        # Check file size
        file_size_mb = os.path.getsize(cache_file) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            logger.warning(
                f"Cache file size ({file_size_mb:.2f} MB) exceeds limit ({max_size_mb} MB)"
            )
            return False

        # Check file integrity
        with open(cache_file, "r") as f:
            json.load(f)

        return True

    except Exception as e:
        logger.error(f"Cache file validation failed: {e}")
        return False


def get_cache_status(cache_file: str = JIRA_CACHE_FILE) -> str:
    """Get detailed cache status information."""
    try:
        if not os.path.exists(cache_file):
            return "No cache file found"

        file_size_mb = os.path.getsize(cache_file) / (1024 * 1024)

        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        timestamp = cache_data.get("timestamp", "Unknown")

        # Count issues per project
        issues = cache_data.get("issues", [])
        project_counts = {}
        for issue in issues:
            project_key = issue.get("key", "").split("-")[0]
            if project_key:
                project_counts[project_key] = project_counts.get(project_key, 0) + 1

        # Format project counts
        project_status = ", ".join(
            [f"{proj}: {count} issues" for proj, count in project_counts.items()]
        )

        return (
            f"Cache: {file_size_mb:.2f} MB, Updated: {timestamp[:16]}, {project_status}"
        )

    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        return "Error reading cache status"


def extract_story_points_value(story_points_value, field_name: str = "") -> float:
    """
    Extract numeric value from JIRA field, handling complex objects.

    Args:
        story_points_value: The raw value from JIRA field
        field_name: Name of the field (for logging/debugging)

    Returns:
        float: Numeric value to use for calculations
    """
    if not story_points_value:
        return 0.0

    # Handle complex objects (like votes field)
    if isinstance(story_points_value, dict):
        # For votes field: {"votes": 5, "hasVoted": false}
        if "votes" in story_points_value and isinstance(
            story_points_value["votes"], (int, float)
        ):
            return float(story_points_value["votes"])

        # For other complex fields, try common numeric properties
        for numeric_key in ["value", "points", "count", "total"]:
            if numeric_key in story_points_value and isinstance(
                story_points_value[numeric_key], (int, float)
            ):
                return float(story_points_value[numeric_key])

        # If no numeric value found in object, log warning and return 0
        logger.warning(
            f"Complex field '{field_name}' has no extractable numeric value: {story_points_value}"
        )
        return 0.0

    # Handle simple numeric values
    if isinstance(story_points_value, (int, float)):
        return float(story_points_value)

    # Handle string representations of numbers
    if isinstance(story_points_value, str):
        try:
            return float(story_points_value)
        except ValueError:
            logger.warning(
                f"Field '{field_name}' contains non-numeric string: '{story_points_value}'"
            )
            return 0.0

    # Unknown type
    logger.warning(
        f"Field '{field_name}' has unexpected type {type(story_points_value)}: {story_points_value}"
    )
    return 0.0


def jira_to_csv_format(issues: List[Dict], config: Dict) -> List[Dict]:
    """Transform JIRA issues to CSV statistics format."""
    try:
        if not issues:
            return []

        # Determine date range from actual issues data
        all_dates = []
        for issue in issues:
            if issue.get("fields", {}).get("created"):
                created_date = datetime.strptime(
                    issue["fields"]["created"][:10], "%Y-%m-%d"
                )
                all_dates.append(created_date)
            if issue.get("fields", {}).get("resolutiondate"):
                resolution_date = datetime.strptime(
                    issue["fields"]["resolutiondate"][:10], "%Y-%m-%d"
                )
                all_dates.append(resolution_date)

        if not all_dates:
            logger.warning("No valid dates found in JIRA issues")
            return []

        # Use actual data range, extending to full weeks
        date_from = min(all_dates)
        date_to = max(all_dates)

        # Extend range to ensure we capture all activity
        date_from = date_from - timedelta(days=date_from.weekday())  # Start of week
        date_to = date_to + timedelta(days=6 - date_to.weekday())  # End of week

        weekly_data = []
        current_date = date_from

        while current_date <= date_to:
            week_end = current_date + timedelta(days=6)
            week_end = min(week_end, date_to)

            # Count completed and created items for this week
            completed_items = 0
            completed_points = 0
            created_items = 0
            created_points = 0

            for issue in issues:
                # Check if item was completed this week
                if issue.get("fields", {}).get("resolutiondate"):
                    resolution_date = datetime.strptime(
                        issue["fields"]["resolutiondate"][:10], "%Y-%m-%d"
                    )
                    if current_date <= resolution_date <= week_end:
                        completed_items += 1
                        # Add story points if available and field is specified
                        story_points = 0
                        if (
                            config.get("story_points_field")
                            and config["story_points_field"].strip()
                        ):
                            story_points_value = issue.get("fields", {}).get(
                                config["story_points_field"]
                            )
                            story_points = extract_story_points_value(
                                story_points_value, config["story_points_field"]
                            )
                        completed_points += story_points

                # Check if item was created this week
                if issue.get("fields", {}).get("created"):
                    created_date = datetime.strptime(
                        issue["fields"]["created"][:10], "%Y-%m-%d"
                    )
                    if current_date <= created_date <= week_end:
                        created_items += 1
                        # Add story points if available and field is specified
                        story_points = 0
                        if (
                            config.get("story_points_field")
                            and config["story_points_field"].strip()
                        ):
                            story_points_value = issue.get("fields", {}).get(
                                config["story_points_field"]
                            )
                            story_points = extract_story_points_value(
                                story_points_value, config["story_points_field"]
                            )
                        created_points += story_points

            weekly_data.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "completed_items": completed_items,
                    "completed_points": completed_points,
                    "created_items": created_items,
                    "created_points": created_points,
                }
            )

            current_date = week_end + timedelta(days=1)

        logger.info(f"Generated {len(weekly_data)} weekly data points from JIRA")
        return weekly_data

    except Exception as e:
        logger.error(f"Error transforming JIRA data: {e}")
        return []


def sync_jira_scope_and_data(
    jql_query: str | None = None, ui_config: Dict | None = None
) -> Tuple[bool, str, Dict]:
    """Main sync function to get JIRA scope calculation and replace CSV data."""
    try:
        # Import scope calculator here to avoid circular imports
        from data.jira_scope_calculator import calculate_jira_project_scope

        # Load configuration with JQL query from settings or use provided UI config
        if ui_config:
            config = ui_config.copy()
            # Ensure jql_query parameter takes precedence if provided
            if jql_query:
                config["jql_query"] = jql_query
        else:
            config = get_jira_config(jql_query)

        # Validate configuration
        is_valid, message = validate_jira_config(config)
        if not is_valid:
            return False, f"Configuration invalid: {message}", {}

        # Validate cache file
        if not validate_cache_file(max_size_mb=config["cache_max_size_mb"]):
            return False, "Cache file validation failed", {}

        # Calculate current fields that would be requested
        base_fields = "key,created,resolutiondate,status"
        if config.get("story_points_field") and config["story_points_field"].strip():
            current_fields = f"{base_fields},{config['story_points_field']}"
        else:
            current_fields = base_fields

        # Try to load from cache first, checking if JQL query and fields match
        cache_loaded, issues = load_jira_cache(config["jql_query"], current_fields)

        if not cache_loaded or not issues:
            # Fetch fresh data from JIRA
            fetch_success, issues = fetch_jira_issues(config)
            if not fetch_success:
                return False, "Failed to fetch JIRA data", {}

            # Cache the response with the JQL query and fields used
            if not cache_jira_response(issues, config["jql_query"], current_fields):
                logger.warning("Failed to cache JIRA response")

        # Calculate JIRA-based project scope
        # Only use story_points_field if it's configured and not empty
        points_field = config.get("story_points_field", "").strip()
        if not points_field:
            # When no points field is configured, pass empty string instead of defaulting to "votes"
            points_field = ""
        scope_data = calculate_jira_project_scope(issues, points_field, config)
        if not scope_data:
            return False, "Failed to calculate JIRA project scope", {}

        # Transform to CSV format for statistics
        csv_data = jira_to_csv_format(issues, config)
        # Note: Empty list is valid when there are no issues, only None indicates error

        # Save both statistics and project scope to unified data structure
        from data.persistence import save_jira_data_unified

        if save_jira_data_unified(csv_data, scope_data, config):
            logger.info("JIRA scope calculation and data sync completed successfully")
            return (
                True,
                "JIRA sync and scope calculation completed successfully",
                scope_data,
            )
        else:
            return False, "Failed to save JIRA data to unified structure", {}

    except Exception as e:
        logger.error(f"Error in JIRA scope sync: {e}")
        return False, f"JIRA scope sync failed: {e}", {}


def sync_jira_data(
    jql_query: str | None = None, ui_config: Dict | None = None
) -> Tuple[bool, str]:
    """Legacy sync function - calls new scope sync and returns just success/message."""
    try:
        success, message, scope_data = sync_jira_scope_and_data(jql_query, ui_config)
        return success, message
    except Exception as e:
        logger.error(f"Error in JIRA data sync: {e}")
        return False, f"JIRA sync failed: {e}"
