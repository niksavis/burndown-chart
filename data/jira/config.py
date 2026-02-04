"""
JIRA Configuration Management

Handles configuration loading, validation, and connection testing.
Configuration hierarchy: jira_config → Environment Variables → Defaults
"""

import hashlib
import json
import os
import time
from datetime import datetime
from typing import Dict, Tuple

import requests

from configuration import logger
from data.persistence import load_app_settings

#######################################################################
# CONFIGURATION CONSTANTS
#######################################################################

JIRA_CACHE_FILE = "jira_cache.json"
JIRA_CHANGELOG_CACHE_FILE = "jira_changelog_cache.json"
DEFAULT_CACHE_MAX_SIZE_MB = 100

# Cache version - increment when cache format changes or pagination logic changes
CACHE_VERSION = "2.0"  # v2.0: Pagination support added
CHANGELOG_CACHE_VERSION = "2.0"  # v2.0: Added critical fields for DORA metrics

# Cache expiration - invalidate cache after this duration
CACHE_EXPIRATION_HOURS = 24  # Cache expires after 24 hours


#######################################################################
# CONFIGURATION FUNCTIONS
#######################################################################


def get_jira_config(settings_jql_query: str | None = None) -> Dict:
    """
    Load JIRA configuration with priority hierarchy: jira_config → Environment → Default.

    This function reads from the jira_config structure in profile.json (managed via
    the JIRA Configuration modal). Falls back to environment variables if config not found.

    Args:
        settings_jql_query: JQL query parameter (highest priority for JQL only)

    Returns:
        Dictionary containing JIRA configuration with keys:
        - jql_query: JQL query string
        - api_endpoint: Full JIRA API endpoint URL
        - token: JIRA authentication token
        - story_points_field: Custom field ID for story points
        - cache_max_size_mb: Maximum cache size in MB
        - max_results: Maximum results per API call
        - devops_projects: List of DevOps project keys
        - devops_task_types: List of DevOps task type names
        - field_mappings: Field mappings for metrics
    """
    # Load app settings first
    try:
        app_settings = load_app_settings()
    except Exception as e:
        logger.debug(f"Failed to load app settings: {e}")
        app_settings = {}

    # Load jira_config structure (new configuration system)
    try:
        from data.persistence import load_jira_configuration

        jira_config = load_jira_configuration()
    except Exception as e:
        logger.debug(f"Failed to load jira configuration: {e}")
        jira_config = {}

    # Configuration hierarchy: Parameter → App settings → Environment → Default
    jql_query = (
        settings_jql_query  # JQL from parameter (highest priority)
        or app_settings.get("jql_query", "")  # App settings
        or os.getenv("JIRA_DEFAULT_JQL", "")  # Environment variable
        or "project = JRASERVER"  # Default fallback
    )

    # Build API endpoint from jira_config or environment
    base_url = jira_config.get("base_url") or os.getenv("JIRA_BASE_URL", "")
    api_version = jira_config.get("api_version") or os.getenv("JIRA_API_VERSION", "v2")

    if base_url:
        api_endpoint = construct_jira_endpoint(base_url, api_version)
    else:
        api_endpoint = os.getenv(
            "JIRA_API_ENDPOINT", "https://jira.atlassian.com/rest/api/2/search"
        )

    field_mappings = app_settings.get("field_mappings", {})
    estimate_field = (
        field_mappings.get("general", {}).get("estimate", "")
        if isinstance(field_mappings, dict)
        else ""
    )

    config = {
        "jql_query": jql_query,
        "api_endpoint": api_endpoint,
        "token": (
            jira_config.get("token", "")  # jira_config (new structure)
            or os.getenv("JIRA_TOKEN", "")  # Environment variable
            or ""  # Default
        ),
        "story_points_field": (
            estimate_field  # Field mappings (General > Estimate)
            or jira_config.get("points_field", "")  # jira_config (legacy)
            or os.getenv("JIRA_STORY_POINTS_FIELD", "")  # Environment variable
            or ""  # Default
        ),
        "cache_max_size_mb": int(
            jira_config.get(
                "cache_size_mb", DEFAULT_CACHE_MAX_SIZE_MB
            )  # jira_config (new structure)
            or os.getenv(
                "JIRA_CACHE_MAX_SIZE_MB", DEFAULT_CACHE_MAX_SIZE_MB
            )  # Environment variable
        ),
        "max_results": int(
            jira_config.get("max_results_per_call", 1000)  # jira_config (new structure)
            or os.getenv("JIRA_MAX_RESULTS", 1000)  # Environment variable
        ),
        "development_projects": app_settings.get(
            "development_projects", []
        ),  # Load development projects for filtering
        "devops_projects": app_settings.get(
            "devops_projects", []
        ),  # Load from app_settings
        "devops_task_types": app_settings.get(
            "devops_task_types", []
        ),  # Load DevOps task types
        "field_mappings": field_mappings,  # Load field mappings for metrics
    }

    return config


def validate_jira_config(config: Dict) -> Tuple[bool, str]:
    """
    Validate JIRA configuration and custom fields.

    Args:
        config: JIRA configuration dictionary

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
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

    # Check for ScriptRunner compatibility issues
    from data.jira.validation import validate_jql_for_scriptrunner

    is_compatible, scriptrunner_warning = validate_jql_for_scriptrunner(jql_query)
    if not is_compatible:
        # Return as warning, not blocking error - let user decide
        logger.warning(f"[JIRA] {scriptrunner_warning}")

    return True, "Configuration valid"


def generate_config_hash(config: Dict, fields: str) -> str:
    """
    Generate hash of configuration for cache validation.

    This hash ensures cache is invalidated when configuration changes.
    Includes: JQL query, fields requested, field mappings, time period

    Args:
        config: JIRA configuration dictionary
        fields: Fields requested in API call

    Returns:
        MD5 hash string of configuration
    """
    config_str = json.dumps(
        {
            "jql": config.get("jql_query", ""),
            "fields": fields,
            "field_mappings": config.get("field_mappings", {}),
            "story_points_field": config.get("story_points_field", ""),
        },
        sort_keys=True,
    )

    return hashlib.md5(config_str.encode("utf-8")).hexdigest()


def construct_jira_endpoint(base_url: str, api_version: str = "v2") -> str:
    """
    Construct full JIRA API endpoint from base URL and version.

    Args:
        base_url: Base JIRA URL (e.g., "https://company.atlassian.net")
        api_version: API version ("v2" or "v3")

    Returns:
        Full endpoint URL (e.g., "https://company.atlassian.net/rest/api/3/search")

    Raises:
        ValueError: If URL format is invalid
    """
    # Remove trailing slashes
    clean_url = base_url.rstrip("/")

    # Validate URL format
    if not clean_url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    if not clean_url:
        raise ValueError("URL cannot be empty")

    # Construct endpoint based on API version
    api_path = "/rest/api/2/search" if api_version == "v2" else "/rest/api/3/search"

    return f"{clean_url}{api_path}"


def test_jira_connection(base_url: str, token: str, api_version: str = "v2") -> Dict:
    """
    Test JIRA connection by calling serverInfo endpoint.

    This validates the base URL and token without requiring a JQL query.
    Uses the serverInfo endpoint which is lightweight and doesn't require authentication
    for connectivity check, but we include the token to verify authentication.

    Args:
        base_url: Base JIRA URL (e.g., "https://company.atlassian.net")
        token: Personal access token
        api_version: API version ("v2" or "v3")

    Returns:
        Dictionary with test results:
        {
            "success": bool,
            "message": str,
            "response_time_ms": int,
            "server_info": dict (if successful),
            "error_code": str (if failed),
            "error_details": str (if failed),
            "timestamp": str (ISO 8601)
        }
    """
    timestamp = datetime.now().isoformat()
    start_time = time.time()

    try:
        # Validate base URL format first
        clean_url = base_url.rstrip("/")
        if not clean_url.startswith(("http://", "https://")):
            return {
                "success": False,
                "message": "Please enter a valid JIRA URL starting with https://",
                "timestamp": timestamp,
                "response_time_ms": None,
                "error_code": "invalid_url_format",
                "error_details": "URL must start with http:// or https://",
            }

        # Construct serverInfo endpoint using configured API version
        api_ver = api_version.replace("v", "")  # Normalize "v2" or "2" to "2"
        server_info_url = f"{clean_url}/rest/api/{api_ver}/serverInfo"

        # Prepare headers with authentication
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Make request with timeout
        logger.info(f"[JIRA] Testing connection to: {server_info_url}")
        response = requests.get(server_info_url, headers=headers, timeout=10)

        response_time_ms = int((time.time() - start_time) * 1000)

        # Check response status
        if response.status_code == 200:
            server_info = response.json()

            # Additional check: Verify the search endpoint with specified API version
            search_endpoint = construct_jira_endpoint(base_url, api_version)
            logger.info(f"[JIRA] Verifying search endpoint: {search_endpoint}")

            # Test with a minimal JQL query (just get 1 result)
            test_jql = "order by created DESC"
            search_headers = headers.copy()
            search_response = requests.get(
                search_endpoint,
                headers=search_headers,
                params={"jql": test_jql, "maxResults": 1},
                timeout=10,
            )

            # If search endpoint fails, provide specific guidance
            if search_response.status_code in (400, 404):
                api_version_name = "v3" if api_version == "v3" else "v2"
                opposite_version = "v2" if api_version == "v3" else "v3"

                # Log the actual error for debugging
                logger.warning(
                    f"[JIRA] API {api_version_name} not available (status {search_response.status_code})"
                )
                try:
                    error_data = search_response.json()
                    logger.warning(f"[JIRA] Search endpoint error: {error_data}")
                except Exception:
                    logger.warning(
                        f"[JIRA] Search endpoint returned {search_response.status_code} without JSON body"
                    )

                return {
                    "success": False,
                    "message": f"Server connected but API {api_version_name} not available",
                    "timestamp": timestamp,
                    "response_time_ms": response_time_ms,
                    "error_code": "api_version_mismatch",
                    "error_details": f"Your JIRA server does not support REST API {api_version_name}. The search endpoint returned {search_response.status_code}. Try switching to API {opposite_version} in the configuration.",
                }

            # If search works, return full success (only accept 200 OK with valid JSON)
            if search_response.status_code == 200:
                # Verify response body is valid JSON
                try:
                    search_data = search_response.json()
                    # Verify it has expected structure
                    if "issues" in search_data or "total" in search_data:
                        logger.info(
                            f"[JIRA] API {api_version} verified (status 200, valid JSON)"
                        )
                        return {
                            "success": True,
                            "message": f"Connection successful (API {api_version} verified)",
                            "timestamp": timestamp,
                            "response_time_ms": response_time_ms,
                            "server_info": {
                                "version": server_info.get("version", "unknown"),
                                "serverTitle": server_info.get(
                                    "serverTitle", "JIRA Server"
                                ),
                                "baseUrl": server_info.get("baseUrl", clean_url),
                            },
                        }
                    else:
                        # Got JSON but wrong structure
                        logger.warning(
                            f"[JIRA] API {api_version} returned JSON with unexpected structure: {list(search_data.keys())}"
                        )
                except ValueError as json_error:
                    # Status 200 but body is not JSON - API version doesn't work
                    logger.warning(
                        f"[JIRA] API {api_version} returned 200 but invalid JSON: {json_error}"
                    )
                    logger.warning(
                        f"[JIRA] Response body (first 200 chars): {search_response.text[:200]}"
                    )

                # If we get here, API returns 200 but doesn't work properly
                api_version_name = "v3" if api_version == "v3" else "v2"
                opposite_version = "v2" if api_version == "v3" else "v3"
                return {
                    "success": False,
                    "message": f"Server connected but API {api_version_name} not available",
                    "timestamp": timestamp,
                    "response_time_ms": response_time_ms,
                    "error_code": "api_version_mismatch",
                    "error_details": f"Your JIRA server does not properly support REST API {api_version_name} (returned 200 but invalid response). Try switching to API {opposite_version} in the configuration.",
                }

            # Search endpoint returned any other error - treat as API version issue
            api_version_name = "v3" if api_version == "v3" else "v2"
            opposite_version = "v2" if api_version == "v3" else "v3"

            logger.warning(
                f"[JIRA] API {api_version_name} not available (unexpected status {search_response.status_code})"
            )

            return {
                "success": False,
                "message": f"Server connected but API {api_version_name} not available",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "api_version_mismatch",
                "error_details": f"Your JIRA server does not support REST API {api_version_name}. The search endpoint returned {search_response.status_code}. Try switching to API {opposite_version} in the configuration.",
            }

        elif response.status_code == 401:
            return {
                "success": False,
                "message": "Authentication failed - invalid token",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "authentication_failed",
                "error_details": "401 Unauthorized: Invalid or expired token. Please verify your personal access token in JIRA settings.",
            }

        elif response.status_code == 403:
            return {
                "success": False,
                "message": "Access forbidden - insufficient permissions",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "authentication_failed",
                "error_details": "403 Forbidden: Token does not have sufficient permissions to access JIRA API.",
            }

        elif response.status_code == 404:
            return {
                "success": False,
                "message": "JIRA server not found - verify URL",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "server_unreachable",
                "error_details": "404 Not Found: The JIRA server could not be found at this URL. Please verify the base URL is correct.",
            }

        else:
            # Generic HTTP error
            error_text = response.text[:200] if response.text else "No error details"
            return {
                "success": False,
                "message": f"Connection failed: HTTP {response.status_code}",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "unexpected_error",
                "error_details": f"HTTP {response.status_code}: {error_text}",
            }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "Connection timeout - check network and try again",
            "timestamp": timestamp,
            "response_time_ms": None,
            "error_code": "connection_timeout",
            "error_details": "Request timed out after 10 seconds. Check network connection, firewall settings, or VPN.",
        }

    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "message": "Cannot reach JIRA server - verify URL",
            "timestamp": timestamp,
            "response_time_ms": None,
            "error_code": "server_unreachable",
            "error_details": f"Connection error: {str(e)}. Check if the URL is correct and the server is accessible.",
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": "Network error occurred",
            "timestamp": timestamp,
            "response_time_ms": None,
            "error_code": "unexpected_error",
            "error_details": f"Request error: {str(e)}",
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "timestamp": timestamp,
            "response_time_ms": None,
            "error_code": "unexpected_error",
            "error_details": f"Exception: {type(e).__name__}: {str(e)}",
        }
