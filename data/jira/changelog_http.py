"""JIRA changelog HTTP utilities.

Provides header construction, retry-aware HTTP fetching, and error detail
extraction for JIRA REST API requests.
"""

import logging
from collections.abc import Callable

import requests

logger = logging.getLogger(__name__)


def _build_headers(config: dict) -> dict[str, str]:
    """
    Build HTTP headers for JIRA API request.

    Args:
        config: Configuration dictionary with token

    Returns:
        Dictionary of HTTP headers
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",  # Required for POST with JSON body
    }
    if config.get("token"):  # Use .get() to safely handle missing token
        headers["Authorization"] = f"Bearer {config['token']}"
    return headers


def _fetch_with_retry(
    api_endpoint: str,
    headers: dict[str, str],
    body: dict,
    max_retries: int,
    start_at: int,
    all_issues: list[dict],
    total_issues: int | None,
    progress_callback: Callable[[str], None] | None,
) -> requests.Response | None:
    """
    Fetch with retry logic for network failures.

    Args:
        api_endpoint: JIRA API endpoint
        headers: HTTP headers
        body: Request body
        max_retries: Maximum number of retries
        start_at: Current pagination offset
        all_issues: List of issues fetched so far
        total_issues: Total number of issues (if known)
        progress_callback: Optional progress callback

    Returns:
        Response object or None if all retries failed
    """
    retry_count = 0
    response = None

    while retry_count < max_retries:
        try:
            # POST method avoids URL length limits (HTTP 414 errors)
            # Parameters go in request body instead of URL
            response = requests.post(
                api_endpoint,
                headers=headers,
                json=body,  # Send parameters in body, not URL
                timeout=90,  # Increased from 30s to 90s
            )
            break  # Success, exit retry loop
        except requests.exceptions.Timeout as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"[JIRA] Timeout at {start_at}, retry {retry_count}/{max_retries}"
                )
                if progress_callback:
                    progress_callback(
                        "[!] Timeout, retrying... "
                        f"(attempt {retry_count}/{max_retries})"
                    )
            else:
                logger.error(
                    f"[JIRA] Fetch failed at {start_at} "
                    f"after {max_retries} retries: {e}"
                )
                # Return partial results instead of complete failure
                logger.warning(
                    f"[JIRA] Returning partial results: "
                    f"{len(all_issues)}/{total_issues or 'unknown'}"
                )
                return None
        except requests.exceptions.RequestException as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(
                    f"[JIRA] Network error at {start_at}, "
                    f"retry {retry_count}/{max_retries}: {e}"
                )
                if progress_callback:
                    progress_callback(
                        "[!] Network error, retrying... "
                        f"(attempt {retry_count}/{max_retries})"
                    )
            else:
                logger.error(
                    f"[JIRA] Fetch failed at {start_at} "
                    f"after {max_retries} retries: {e}"
                )
                # Return partial results instead of complete failure
                logger.warning(
                    f"[JIRA] Returning partial results: "
                    f"{len(all_issues)}/{total_issues or 'unknown'}"
                )
                return None

    return response


def _extract_error_details(response: requests.Response) -> str:
    """
    Extract error details from JIRA API response.

    Args:
        response: Failed response object

    Returns:
        Error details string
    """
    error_details = ""
    try:
        error_json = response.json()
        if "errorMessages" in error_json:
            error_details = "; ".join(error_json["errorMessages"])
        elif "errors" in error_json:
            error_details = "; ".join(
                [f"{k}: {v}" for k, v in error_json["errors"].items()]
            )
        else:
            error_details = str(error_json)
    except Exception:
        error_details = response.text[:500]

    return error_details
