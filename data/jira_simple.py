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
from data.persistence import save_statistics

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
    Load JIRA configuration with priority hierarchy: UI settings → Environment → Default.

    Args:
        settings_jql_query: JQL query from UI settings (highest priority)

    Returns:
        Dictionary containing JIRA configuration
    """
    # Configuration hierarchy: UI settings → Environment → Default
    jql_query = (
        settings_jql_query  # UI settings (highest priority)
        or os.getenv("JIRA_DEFAULT_JQL", "")  # Environment variable
        or "project = JRASERVER"  # Default fallback
    )

    config = {
        "url": os.getenv("JIRA_URL", ""),
        "jql_query": jql_query,
        "token": os.getenv("JIRA_TOKEN", ""),
        "story_points_field": os.getenv("JIRA_STORY_POINTS_FIELD", ""),
        "cache_max_size_mb": int(
            os.getenv("JIRA_CACHE_MAX_SIZE_MB", DEFAULT_CACHE_MAX_SIZE_MB)
        ),
    }

    return config


def validate_jira_config(config: Dict) -> Tuple[bool, str]:
    """Validate JIRA configuration and custom fields."""
    if not config["url"]:
        return False, "JIRA_URL is required"

    if not config["jql_query"]:
        return False, "JQL query is required"

    # Basic JQL validation (optional - JQL is complex, so we do minimal validation)
    jql_query = config["jql_query"].strip()
    if len(jql_query) < 5:  # Minimum reasonable JQL length
        return False, "JQL query is too short"

    return True, "Configuration valid"


def fetch_jira_issues(config: Dict, max_results: int = 1000) -> Tuple[bool, List[Dict]]:
    """Execute JQL query and return issues."""
    try:
        # Use the JQL query directly from configuration
        jql = config["jql_query"]

        # API endpoint
        url = f"{config['url']}/rest/api/2/search"

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


def cache_jira_response(data: List[Dict], cache_file: str = JIRA_CACHE_FILE) -> bool:
    """Save raw JIRA JSON response to cache file."""
    try:
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "issues": data,
            "total_issues": len(data),
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        logger.info(f"Cached {len(data)} JIRA issues to {cache_file}")
        return True

    except Exception as e:
        logger.error(f"Error caching JIRA response: {e}")
        return False


def load_jira_cache(cache_file: str = JIRA_CACHE_FILE) -> Tuple[bool, List[Dict]]:
    """Load cached JIRA JSON response from file."""
    try:
        if not os.path.exists(cache_file):
            return False, []

        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        issues = cache_data.get("issues", [])
        logger.info(f"Loaded {len(issues)} JIRA issues from cache")
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
                            if story_points_value:
                                story_points = story_points_value
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
                            if story_points_value:
                                story_points = story_points_value
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


def sync_jira_data(
    jql_query: str | None = None, ui_config: Dict | None = None
) -> Tuple[bool, str]:
    """Main sync function to replace CSV data with JIRA data."""
    try:
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
            return False, f"Configuration invalid: {message}"

        # Validate cache file
        if not validate_cache_file(max_size_mb=config["cache_max_size_mb"]):
            return False, "Cache file validation failed"

        # Try to load from cache first
        cache_loaded, issues = load_jira_cache()

        if not cache_loaded or not issues:
            # Fetch fresh data from JIRA
            fetch_success, issues = fetch_jira_issues(config)
            if not fetch_success:
                return False, "Failed to fetch JIRA data"

            # Cache the response
            if not cache_jira_response(issues):
                logger.warning("Failed to cache JIRA response")

        # Transform to CSV format
        csv_data = jira_to_csv_format(issues, config)
        if not csv_data:
            return False, "Failed to transform JIRA data"

        # Save to statistics file
        save_statistics(csv_data)

        logger.info("JIRA data sync completed successfully")
        return True, "JIRA sync completed successfully"

    except Exception as e:
        logger.error(f"Error in JIRA sync: {e}")
        return False, f"JIRA sync failed: {e}"
