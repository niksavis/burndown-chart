import logging
from collections.abc import Callable

import requests

logger = logging.getLogger(__name__)


def _build_headers(config: dict) -> dict[str, str]:

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if config.get("token"):
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

    retry_count = 0
    response = None

    while retry_count < max_retries:
        try:
            response = requests.post(
                api_endpoint,
                headers=headers,
                json=body,
                timeout=90,
            )
            break
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
                logger.warning(
                    f"[JIRA] Returning partial results: "
                    f"{len(all_issues)}/{total_issues or 'unknown'}"
                )
                return None

    return response


def _extract_error_details(response: requests.Response) -> str:

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
