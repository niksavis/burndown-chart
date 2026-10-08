import hashlib
import json
import logging
import os
import time
from datetime import datetime

import requests

from data.exceptions import JiraError, PersistenceError
from data.jira.validation import validate_jql_for_scriptrunner

logger = logging.getLogger(__name__)


JIRA_CACHE_FILE = "jira_cache.json"
JIRA_CHANGELOG_CACHE_FILE = "jira_changelog_cache.json"
DEFAULT_CACHE_MAX_SIZE_MB = 100

CACHE_VERSION = "2.0"
CHANGELOG_CACHE_VERSION = "2.0"

CACHE_EXPIRATION_HOURS = 24


def get_jira_config(settings_jql_query: str | None = None) -> dict:

    try:
        from data.persistence import (  # noqa: PLC0415
            load_app_settings,
            load_jira_configuration,
        )

        app_settings = load_app_settings()
    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        PersistenceError,
    ) as e:
        logger.debug(f"Failed to load app settings: {e}")
        app_settings = {}

    try:
        jira_config = load_jira_configuration()
    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        PersistenceError,
    ) as e:
        logger.debug(f"Failed to load jira configuration: {e}")
        jira_config = {}

    jql_query = (
        settings_jql_query
        or app_settings.get("jql_query", "")
        or os.getenv("JIRA_DEFAULT_JQL", "")
        or "project = JRASERVER"
    )

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
        "token": (jira_config.get("token", "") or os.getenv("JIRA_TOKEN", "") or ""),
        "story_points_field": (
            estimate_field
            or jira_config.get("points_field", "")
            or os.getenv("JIRA_STORY_POINTS_FIELD", "")
            or ""
        ),
        "cache_max_size_mb": int(
            jira_config.get("cache_size_mb", DEFAULT_CACHE_MAX_SIZE_MB)
            or os.getenv("JIRA_CACHE_MAX_SIZE_MB", DEFAULT_CACHE_MAX_SIZE_MB)
        ),
        "max_results": int(
            jira_config.get("max_results_per_call", 1000)
            or os.getenv("JIRA_MAX_RESULTS", 1000)
        ),
        "development_projects": app_settings.get("development_projects", []),
        "devops_projects": app_settings.get("devops_projects", []),
        "devops_task_types": app_settings.get("devops_task_types", []),
        "field_mappings": field_mappings,
    }

    return config


def validate_jira_config(config: dict) -> tuple[bool, str]:

    api_endpoint = config.get("api_endpoint", "")
    if not api_endpoint:
        return False, "JIRA API endpoint is required"

    if not config["jql_query"]:
        return False, "JQL query is required"

    jql_query = config["jql_query"].strip()
    if len(jql_query) < 5:
        return False, "JQL query is too short"

    if not api_endpoint.startswith(("http://", "https://")):
        return False, "JIRA API endpoint must be a valid URL (http:// or https://)"

    is_compatible, scriptrunner_warning = validate_jql_for_scriptrunner(jql_query)
    if not is_compatible:
        logger.warning(f"[JIRA] {scriptrunner_warning}")

    return True, "Configuration valid"


def generate_config_hash(config: dict, fields: str) -> str:

    config_str = json.dumps(
        {
            "jql": config.get("jql_query", ""),
            "fields": fields,
            "field_mappings": config.get("field_mappings", {}),
            "story_points_field": config.get("story_points_field", ""),
        },
        sort_keys=True,
    )

    return hashlib.md5(config_str.encode("utf-8"), usedforsecurity=False).hexdigest()


def build_sync_jira_config(
    jira_config: dict, settings_jql: str, app_settings: dict
) -> dict:

    base_url = jira_config.get("base_url", "https://jira.atlassian.com")
    api_version = jira_config.get("api_version", "v2")
    points_field_raw = jira_config.get("points_field", "")

    return {
        "api_endpoint": construct_jira_endpoint(base_url, api_version),
        "jql_query": settings_jql,
        "token": jira_config.get("token", ""),
        "story_points_field": points_field_raw
        if isinstance(points_field_raw, str)
        else "",
        "cache_max_size_mb": jira_config.get("cache_size_mb", 100),
        "max_results": jira_config.get("max_results_per_call", 1000),
        "development_projects": app_settings.get("development_projects", []),
        "devops_projects": app_settings.get("devops_projects", []),
        "devops_task_types": app_settings.get("devops_task_types", []),
        "field_mappings": app_settings.get("field_mappings", {}),
    }


def construct_jira_endpoint(base_url: str, api_version: str = "v2") -> str:

    clean_url = base_url.rstrip("/")

    if not clean_url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    if not clean_url:
        raise ValueError("URL cannot be empty")

    api_path = "/rest/api/2/search" if api_version == "v2" else "/rest/api/3/search"

    return f"{clean_url}{api_path}"


def test_jira_connection(base_url: str, token: str, api_version: str = "v2") -> dict:

    timestamp = datetime.now().isoformat()
    start_time = time.time()

    try:
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

        api_ver = api_version.replace("v", "")
        server_info_url = f"{clean_url}/rest/api/{api_ver}/serverInfo"

        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        logger.info(f"[JIRA] Testing connection to: {server_info_url}")
        response = requests.get(server_info_url, headers=headers, timeout=10)

        response_time_ms = int((time.time() - start_time) * 1000)

        if response.status_code == 200:
            server_info = response.json()

            search_endpoint = construct_jira_endpoint(base_url, api_version)
            logger.info(f"[JIRA] Verifying search endpoint: {search_endpoint}")

            test_jql = "order by created DESC"
            search_headers = headers.copy()
            search_response = requests.get(
                search_endpoint,
                headers=search_headers,
                params={"jql": test_jql, "maxResults": 1},
                timeout=10,
            )

            if search_response.status_code in (400, 404):
                api_version_name = "v3" if api_version == "v3" else "v2"
                opposite_version = "v2" if api_version == "v3" else "v3"

                logger.warning(
                    f"[JIRA] API {api_version_name} not available "
                    f"(status {search_response.status_code})"
                )
                try:
                    error_data = search_response.json()
                    logger.warning(f"[JIRA] Search endpoint error: {error_data}")
                except ValueError:
                    logger.warning(
                        "[JIRA] Search endpoint returned "
                        f"{search_response.status_code} without JSON body"
                    )

                return {
                    "success": False,
                    "message": (
                        f"Server connected but API {api_version_name} not available"
                    ),
                    "timestamp": timestamp,
                    "response_time_ms": response_time_ms,
                    "error_code": "api_version_mismatch",
                    "error_details": (
                        "Your JIRA server does not support REST API "
                        f"{api_version_name}. The search endpoint returned "
                        f"{search_response.status_code}. Try switching "
                        f"to API {opposite_version} in the configuration."
                    ),
                }

            if search_response.status_code == 200:
                try:
                    search_data = search_response.json()
                    if "issues" in search_data or "total" in search_data:
                        logger.info(
                            f"[JIRA] API {api_version} verified "
                            "(status 200, valid JSON)"
                        )
                        return {
                            "success": True,
                            "message": (
                                f"Connection successful (API {api_version} verified)"
                            ),
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
                        logger.warning(
                            f"[JIRA] API {api_version} returned JSON "
                            "with unexpected structure: "
                            f"{list(search_data.keys())}"
                        )
                except ValueError as json_error:
                    logger.warning(
                        f"[JIRA] API {api_version} returned 200 "
                        f"but invalid JSON: {json_error}"
                    )
                    logger.warning(
                        "[JIRA] Response body (first 200 chars): "
                        f"{search_response.text[:200]}"
                    )

                api_version_name = "v3" if api_version == "v3" else "v2"
                opposite_version = "v2" if api_version == "v3" else "v3"
                return {
                    "success": False,
                    "message": (
                        f"Server connected but API {api_version_name} not available"
                    ),
                    "timestamp": timestamp,
                    "response_time_ms": response_time_ms,
                    "error_code": "api_version_mismatch",
                    "error_details": (
                        "Your JIRA server does not properly support REST API "
                        f"{api_version_name} (returned 200 but invalid "
                        f"response). Try switching to API "
                        f"{opposite_version} in the configuration."
                    ),
                }

            api_version_name = "v3" if api_version == "v3" else "v2"
            opposite_version = "v2" if api_version == "v3" else "v3"

            logger.warning(
                f"[JIRA] API {api_version_name} not available "
                f"(unexpected status {search_response.status_code})"
            )

            return {
                "success": False,
                "message": (
                    f"Server connected but API {api_version_name} not available"
                ),
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "api_version_mismatch",
                "error_details": (
                    "Your JIRA server does not support REST API "
                    f"{api_version_name}. The search endpoint returned "
                    f"{search_response.status_code}. Try switching to API "
                    f"{opposite_version} in the configuration."
                ),
            }

        elif response.status_code == 401:
            return {
                "success": False,
                "message": "Authentication failed - invalid token",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "authentication_failed",
                "error_details": (
                    "401 Unauthorized: Invalid or expired token. "
                    "Please verify your personal access token in JIRA settings."
                ),
            }

        elif response.status_code == 403:
            return {
                "success": False,
                "message": "Access forbidden - insufficient permissions",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "authentication_failed",
                "error_details": (
                    "403 Forbidden: Token does not have sufficient "
                    "permissions to access JIRA API."
                ),
            }

        elif response.status_code == 404:
            return {
                "success": False,
                "message": "JIRA server not found - verify URL",
                "timestamp": timestamp,
                "response_time_ms": response_time_ms,
                "error_code": "server_unreachable",
                "error_details": (
                    "404 Not Found: The JIRA server could not be found "
                    "at this URL. Please verify the base URL is correct."
                ),
            }

        else:
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
            "error_details": (
                "Request timed out after 10 seconds. "
                "Check network connection, firewall settings, or VPN."
            ),
        }

    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "message": "Cannot reach JIRA server - verify URL",
            "timestamp": timestamp,
            "response_time_ms": None,
            "error_code": "server_unreachable",
            "error_details": (
                f"Connection error: {str(e)}. "
                "Check if the URL is correct and the server is accessible."
            ),
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

    except (ValueError, TypeError, RuntimeError, JiraError) as e:
        jira_error = JiraError("Unexpected JIRA configuration error")
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "timestamp": timestamp,
            "response_time_ms": None,
            "error_code": "unexpected_error",
            "error_details": (
                f"{type(jira_error).__name__}: {type(e).__name__}: {str(e)}"
            ),
        }
