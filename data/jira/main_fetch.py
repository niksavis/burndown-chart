import logging
import time
from datetime import UTC, datetime

import requests

from data.exceptions import JiraError, PersistenceError
from data.jira.cache_operations import cache_jira_response
from data.jira.config import CACHE_EXPIRATION_HOURS
from data.jira.delta_fetch import try_delta_fetch
from data.jira.fetch_utils import fetch_jira_paginated
from data.jira.field_utils import extract_jira_field_id
from data.jira.issue_counter import check_jira_issue_count
from data.jira.rate_limiter import get_rate_limiter, retry_with_backoff
from data.jira.two_phase_fetch import (
    fetch_jira_issues_two_phase,
    should_use_two_phase_fetch,
)
from data.task_progress import TaskProgress
from utils.datetime_utils import parse_iso_datetime

logger = logging.getLogger(__name__)


def get_backend():  # noqa: PLC0415
    from data.persistence.factory import (  # noqa: PLC0415
        get_backend as _get_backend,
    )

    return _get_backend()


def fetch_jira_issues(
    config: dict, max_results: int | None = None, force_refresh: bool = False
) -> tuple[bool, list[dict]]:

    start_time = time.time()

    try:
        jql = config["jql_query"]

        api_endpoint = config.get("api_endpoint", "")
        if not api_endpoint:
            logger.error("[JIRA] API endpoint not configured")
            return False, []

        if config.get("fields"):
            fields = config["fields"]
            logger.debug(f"[JIRA] Using caller-specified fields: {fields}")
        else:
            base_fields = (
                "key,summary,project,created,updated,resolutiondate,status,"
                "issuetype,assignee,priority,resolution,labels,components,"
                "fixVersions"
            )

            parent_field = (
                config.get("field_mappings", {}).get("general", {}).get("parent_field")
            )
            if parent_field:
                base_fields += f",{parent_field}"

            additional_fields = []
            if (
                config.get("story_points_field")
                and config["story_points_field"].strip()
            ):
                additional_fields.append(config["story_points_field"])

            field_mappings = config.get("field_mappings", {})
            for _category, mappings in field_mappings.items():
                if isinstance(mappings, dict):
                    for _field_name, field_id in mappings.items():
                        clean_field_id = extract_jira_field_id(field_id)
                        if clean_field_id and clean_field_id not in base_fields:
                            additional_fields.append(clean_field_id)

            if additional_fields:
                fields = f"{base_fields},{','.join(sorted(set(additional_fields)))}"
            else:
                fields = base_fields

        use_two_phase, two_phase_reason = should_use_two_phase_fetch(config)

        if use_two_phase:
            logger.info(f"[JIRA] Two-phase fetch activated: {two_phase_reason}")
        else:
            logger.debug(f"[JIRA] Using standard fetch: {two_phase_reason}")

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")
        last_fetch_key = None
        last_delta_key = None
        last_delta_keys_key = None

        if active_profile_id and active_query_id:
            last_fetch_key = f"last_fetch_time:{active_profile_id}:{active_query_id}"
            last_delta_key = (
                f"last_delta_changed_count:{active_profile_id}:{active_query_id}"
            )
            last_delta_keys_key = (
                f"last_delta_changed_keys:{active_profile_id}:{active_query_id}"
            )

        if force_refresh:
            logger.info(
                "[JIRA] Force refresh requested - bypassing incremental fetch cache"
            )
            is_valid = False
            cached_data = None
        else:
            logger.info("[JIRA] Checking if data has changed (incremental fetch)")

            is_valid = False
            cached_data = None

            if active_profile_id and active_query_id:
                try:
                    db_issues = backend.get_issues(active_profile_id, active_query_id)

                    if db_issues and len(db_issues) > 0:
                        first_issue = db_issues[0]
                        cache_timestamp = None
                        if last_fetch_key:
                            last_fetch_time = backend.get_app_state(last_fetch_key)
                            cache_timestamp = parse_iso_datetime(last_fetch_time)

                        if not cache_timestamp and "fetched_at" in first_issue:
                            cache_timestamp = parse_iso_datetime(
                                first_issue["fetched_at"]
                            )
                            if cache_timestamp and cache_timestamp.tzinfo is None:
                                cache_timestamp = cache_timestamp.replace(tzinfo=UTC)

                        if cache_timestamp:
                            now_utc = datetime.now(UTC)
                            age_hours = (
                                now_utc - cache_timestamp
                            ).total_seconds() / 3600

                            if age_hours <= CACHE_EXPIRATION_HOURS:
                                cached_data = db_issues
                                is_valid = True
                                logger.info(
                                    f"[JIRA] Cache valid: {len(cached_data)} "
                                    f"issues ({age_hours:.1f}h old)"
                                )
                            else:
                                logger.debug(
                                    f"[JIRA] Cache expired: {age_hours:.1f}h old "
                                    f"(max: {CACHE_EXPIRATION_HOURS}h)"
                                )
                        else:
                            logger.warning(
                                "[JIRA] Issues in database missing fetched_at timestamp"
                            )
                    else:
                        logger.info(
                            "[JIRA] No issues found in database - "
                            "will perform full fetch"
                        )
                except (
                    AttributeError,
                    KeyError,
                    PersistenceError,
                    TypeError,
                    ValueError,
                ) as e:
                    logger.warning(f"[JIRA] Database cache read error: {e}")
            else:
                logger.warning(
                    "[JIRA] No active profile/query - cannot check database cache"
                )

        if is_valid and cached_data:
            logger.info(
                f"[JIRA] Cache valid, checking for changes "
                f"({len(cached_data)} cached issues)"
            )

            if use_two_phase:
                logger.info(
                    "[JIRA] Two-phase fetch active, skipping count check, "
                    "trying delta fetch"
                )
                delta_success, merged_issues, changed_keys, delta_issues = (
                    try_delta_fetch(jql, config, cached_data, api_endpoint, start_time)
                )
                if delta_success:
                    cache_jira_response(
                        data=delta_issues,
                        jql_query=jql,
                        fields_requested=fields,
                        config=config,
                    )
                    if last_fetch_key and last_delta_key:
                        backend.set_app_state(
                            last_fetch_key,
                            datetime.now(UTC).isoformat(),
                        )
                        backend.set_app_state(
                            last_delta_key,
                            str(len(delta_issues)),
                        )
                        if last_delta_keys_key:
                            import json  # noqa: PLC0415

                            backend.set_app_state(
                                last_delta_keys_key,
                                json.dumps(changed_keys),
                            )
                    return True, merged_issues
            else:
                success, current_count = check_jira_issue_count(jql, config)

                if success:
                    cached_count = len(cached_data)
                    count_diff = abs(current_count - cached_count)

                    if count_diff > max(cached_count * 0.05, 5):
                        logger.info(
                            "[JIRA] Significant count change: "
                            f"{cached_count} -> {current_count} "
                            f"({count_diff} diff), full fetch"
                        )
                    elif current_count == cached_count:
                        delta_success, merged_issues, changed_keys, delta_issues = (
                            try_delta_fetch(
                                jql, config, cached_data, api_endpoint, start_time
                            )
                        )
                        if delta_success:
                            cache_jira_response(
                                data=delta_issues,
                                jql_query=jql,
                                fields_requested=fields,
                                config=config,
                            )
                            if last_fetch_key and last_delta_key:
                                backend.set_app_state(
                                    last_fetch_key,
                                    datetime.now(UTC).isoformat(),
                                )
                                backend.set_app_state(
                                    last_delta_key,
                                    str(len(delta_issues)),
                                )
                                if last_delta_keys_key:
                                    import json  # noqa: PLC0415

                                    backend.set_app_state(
                                        last_delta_keys_key,
                                        json.dumps(changed_keys),
                                    )
                            return True, merged_issues
                    else:
                        logger.info(
                            f"[JIRA] Small count change: {cached_count} "
                            f"-> {current_count}, trying delta fetch"
                        )
                        delta_success, merged_issues, changed_keys, delta_issues = (
                            try_delta_fetch(
                                jql, config, cached_data, api_endpoint, start_time
                            )
                        )
                        if delta_success:
                            cache_jira_response(
                                data=delta_issues,
                                jql_query=jql,
                                fields_requested=fields,
                                config=config,
                            )
                            if last_delta_keys_key:
                                import json  # noqa: PLC0415

                                backend.set_app_state(
                                    last_delta_keys_key,
                                    json.dumps(changed_keys),
                                )
                            return True, merged_issues
                else:
                    logger.warning(
                        "[JIRA] Count check failed, trying delta fetch anyway"
                    )
                    delta_success, merged_issues, changed_keys, delta_issues = (
                        try_delta_fetch(
                            jql, config, cached_data, api_endpoint, start_time
                        )
                    )
                    if delta_success:
                        cache_jira_response(
                            data=delta_issues,
                            jql_query=jql,
                            fields_requested=fields,
                            config=config,
                        )
                        if last_fetch_key and last_delta_key:
                            backend.set_app_state(
                                last_fetch_key,
                                datetime.now(UTC).isoformat(),
                            )
                            backend.set_app_state(
                                last_delta_key,
                                str(len(delta_issues)),
                            )
                            if last_delta_keys_key:
                                import json  # noqa: PLC0415

                                backend.set_app_state(
                                    last_delta_keys_key,
                                    json.dumps(changed_keys),
                                )
                        logger.info(
                            "[JIRA] Delta fetch succeeded despite count check failure"
                        )
                        return True, merged_issues
                    logger.warning(
                        "[JIRA] Count check and delta fetch failed, "
                        "proceeding with full fetch"
                    )
        else:
            if not is_valid:
                logger.warning(
                    f"[JIRA] Cache invalid (is_valid={is_valid}, "
                    f"has_data={cached_data is not None}), fetching from API"
                )
            else:
                logger.info("[JIRA] Cache miss, fetching from API")

        if use_two_phase:
            logger.info("[JIRA] Executing two-phase fetch...")

            success, all_issues = fetch_jira_issues_two_phase(
                config,
                max_results,
                force_refresh,
                fetch_paginated_func=fetch_jira_paginated,
            )
            if not success:
                logger.error("[JIRA] Two-phase fetch failed")
                return False, []

            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")
            active_query_id = backend.get_app_state("active_query_id")
            cache_jira_response(
                data=all_issues,
                jql_query=jql,
                fields_requested=fields,
                config=config,
            )
            if active_profile_id and active_query_id:
                backend.set_app_state(
                    f"last_fetch_time:{active_profile_id}:{active_query_id}",
                    datetime.now(UTC).isoformat(),
                )
                backend.set_app_state(
                    f"last_delta_changed_count:{active_profile_id}:{active_query_id}",
                    "-1",
                )
                backend.set_app_state(
                    f"last_delta_changed_keys:{active_profile_id}:{active_query_id}",
                    "[]",
                )
            return True, all_issues

        total_limit = max_results if max_results is not None else None
        page_size = min(total_limit or 1000, 1000)

        if page_size > 1000:
            logger.warning(
                f"[JIRA] Page size {page_size} exceeds API limit, using 1000"
            )
            page_size = 1000

        url = api_endpoint

        headers = {"Accept": "application/json"}
        if config["token"]:
            headers["Authorization"] = f"Bearer {config['token']}"

        all_issues = []
        start_at = 0
        total_issues = None

        logger.debug(f"[JIRA] Fetching from: {url}")
        logger.debug(f"[JIRA] JQL: {jql}")
        logger.debug(f"[JIRA] Page size: {page_size}, Fields: {fields}")

        rate_limiter = get_rate_limiter()

        while True:
            params = {
                "jql": jql,
                "maxResults": page_size,
                "startAt": start_at,
                "fields": fields,
            }

            logger.debug(
                f"[JIRA] Page at {start_at} (fetched {len(all_issues)} so far)"
            )

            try:
                is_cancelled = TaskProgress.is_task_cancelled()
                logger.debug(f"[JIRA] Cancellation check: is_cancelled={is_cancelled}")
                if is_cancelled:
                    logger.info(
                        f"[JIRA] Fetch cancelled by user after {len(all_issues)} issues"
                    )
                    TaskProgress.fail_task("update_data", "Operation cancelled by user")
                    return False, []

                if total_issues:
                    TaskProgress.update_progress(
                        "update_data",
                        "fetch",
                        current=len(all_issues),
                        total=total_issues,
                        message="Fetching issues from JIRA",
                    )
                else:
                    msg = (
                        "Connecting to JIRA..."
                        if start_at == 0
                        else f"Fetching issues ({len(all_issues)} so far)..."
                    )
                    TaskProgress.update_progress(
                        "update_data",
                        "fetch",
                        current=len(all_issues),
                        total=0,
                        message=msg,
                    )
            except (
                AttributeError,
                ImportError,
                RuntimeError,
                TypeError,
                ValueError,
            ) as e:
                logger.debug(f"Progress update/cancellation check failed: {e}")

            rate_limiter.wait_for_token()

            success, response = retry_with_backoff(
                requests.get, url, headers=headers, params=params, timeout=30
            )

            if not success:
                logger.error("[JIRA] Fetch failed after retries")
                return False, []

            if not response.ok:
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
                except TypeError, ValueError:
                    error_details = response.text[:500]

                if (
                    "issueFunction" in jql.lower()
                    or "scriptrunner" in error_details.lower()
                ):
                    logger.error(
                        f"[JIRA] ScriptRunner function error in JQL: {jql[:50]}..."
                    )
                    logger.error("[JIRA] ScriptRunner functions may not be available")
                    logger.error(f"[JIRA] API error details: {error_details}")
                else:
                    logger.error(
                        f"[JIRA] API error ({response.status_code}): {error_details}"
                    )

                return False, []

            data = response.json()
            issues_in_page = data.get("issues", [])

            if total_issues is None:
                total_issues = data.get("total", 0)
                logger.info(f"[JIRA] Query matched {total_issues} issues, paginating")

            if total_limit is not None:
                remaining_quota = total_limit - len(all_issues)
                issues_to_add = issues_in_page[:remaining_quota]
            else:
                issues_to_add = issues_in_page

            all_issues.extend(issues_to_add)

            if (
                len(issues_in_page) < page_size
                or start_at + len(issues_in_page) >= total_issues
                or (total_limit is not None and len(all_issues) >= total_limit)
            ):
                logger.info(
                    "[JIRA] Pagination complete: "
                    f"{len(all_issues)}/{total_issues} fetched"
                )
                break

            start_at += page_size

        elapsed_time = time.time() - start_time
        logger.info(
            f"[JIRA] Fetch complete: {len(all_issues)} issues in {elapsed_time:.2f}s"
        )

        cache_jira_response(
            data=all_issues,
            jql_query=jql,
            fields_requested=fields,
            config=config,
        )
        try:
            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")
            active_query_id = backend.get_app_state("active_query_id")
            if active_profile_id and active_query_id:
                backend.set_app_state(
                    f"last_fetch_time:{active_profile_id}:{active_query_id}",
                    datetime.now(UTC).isoformat(),
                )
                backend.set_app_state(
                    f"last_delta_changed_count:{active_profile_id}:{active_query_id}",
                    "-1",
                )
                backend.set_app_state(
                    f"last_delta_changed_keys:{active_profile_id}:{active_query_id}",
                    "[]",
                )
        except (AttributeError, PersistenceError, TypeError, ValueError) as e:
            logger.debug(f"[JIRA] Failed to update last_fetch_time: {e}")

        return True, all_issues

    except requests.exceptions.RequestException as e:
        logger.error(f"[JIRA] Network error: {e}")
        return False, []
    except (
        JiraError,
        KeyError,
        PersistenceError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as e:
        logger.error(f"[JIRA] Unexpected error: {e}")
        return False, []
