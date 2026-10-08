import logging
from datetime import UTC, datetime, timedelta

from data.cache_manager import (
    generate_cache_key,
    generate_jira_data_cache_key,
    load_cache_with_validation,
)
from data.exceptions import CacheError, PersistenceError

logger = logging.getLogger(__name__)


def cache_jira_response(
    data: list[dict],
    jql_query: str = "",
    fields_requested: str = "",
    cache_file: str = "",
    config: dict | None = None,
    generate_config_hash_func=None,
) -> bool:

    try:
        try:
            from data.persistence.factory import get_backend  # noqa: PLC0415

            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")
            active_query_id = backend.get_app_state("active_query_id")

            if active_profile_id and active_query_id:
                field_mappings = config.get("field_mappings", {}) if config else {}
                cache_key = generate_cache_key(
                    jql_query=jql_query,
                    field_mappings=field_mappings,
                    time_period_days=30,
                )

                utc_now = datetime.now(UTC)
                expires_at = utc_now + timedelta(hours=24)

                backend.save_issues_batch(
                    profile_id=active_profile_id,
                    query_id=active_query_id,
                    cache_key=cache_key,
                    issues=data,
                    expires_at=expires_at,
                )

                logger.info(
                    "[Database] Saved "
                    f"{len(data)} issues to database for "
                    f"{active_profile_id}/{active_query_id}"
                )

                if config and generate_config_hash_func:
                    config_hash = generate_config_hash_func(config, fields_requested)
                    try:
                        from data.persistence import (  # noqa: PLC0415
                            load_app_settings,
                            save_app_settings,
                        )

                        current_settings = load_app_settings()
                        cache_metadata = {
                            "last_cache_key": cache_key,
                            "last_cache_timestamp": utc_now.isoformat(),
                            "cache_config_hash": config_hash,
                        }
                        save_app_settings(
                            pert_factor=current_settings.get("pert_factor", 3.0),
                            deadline=current_settings.get("deadline", "2025-12-31"),
                            data_points_count=current_settings.get("data_points_count"),
                            show_milestone=current_settings.get("show_milestone"),
                            milestone=current_settings.get("milestone"),
                            show_points=current_settings.get("show_points"),
                            jql_query=current_settings.get("jql_query"),
                            last_used_data_source=current_settings.get(
                                "last_used_data_source"
                            ),
                            active_jql_profile_id=current_settings.get(
                                "active_jql_profile_id"
                            ),
                            cache_metadata=cache_metadata,
                        )
                        logger.debug(f"[Cache] Metadata saved: {cache_key[:8]}...")
                    except (
                        PersistenceError,
                        CacheError,
                        KeyError,
                        TypeError,
                        ValueError,
                    ) as metadata_error:
                        logger.warning(
                            f"[Cache] Failed to save metadata: {metadata_error}"
                        )

            else:
                logger.warning(
                    "[Database] No active profile/query - skipping database save"
                )

        except (
            PersistenceError,
            CacheError,
            KeyError,
            TypeError,
            ValueError,
        ) as db_error:
            logger.error(
                f"[Database] Failed to save issues to database: {db_error}",
                exc_info=True,
            )

        return True

    except (
        PersistenceError,
        CacheError,
        KeyError,
        TypeError,
        ValueError,
    ) as e:
        logger.error(f"[Cache] Error saving response: {e}", exc_info=True)
        return False


def load_jira_cache(
    current_jql_query: str = "",
    current_fields: str = "",
    cache_file: str = "",
    config: dict | None = None,
    generate_config_hash_func=None,
    cache_version: str = "1.0",
    cache_expiration_hours: int = 24,
) -> tuple[bool, list[dict]]:

    if not config:
        logger.debug("[Cache] No config provided, cache miss")
        return False, []

    try:
        cache_key = generate_jira_data_cache_key(
            jql_query=current_jql_query,
            time_period_days=30,
        )

        if generate_config_hash_func:
            config_hash = generate_config_hash_func(config, current_fields)
        else:
            config_hash = ""

        is_valid, cached_data = load_cache_with_validation(
            cache_key=cache_key,
            config_hash=config_hash,
            max_age_hours=cache_expiration_hours,
            cache_dir="cache",
        )

        if is_valid and cached_data:
            logger.info(f"[Cache] Hit: Loaded {len(cached_data)} issues from cache")
            return True, cached_data

        logger.debug("[Cache] Miss: No valid cache found")
        return False, []

    except (CacheError, PersistenceError, KeyError, TypeError, ValueError) as e:
        logger.error(f"[Cache] Error loading: {e}", exc_info=True)
        return False, []


def load_changelog_cache(
    current_jql_query: str = "",
    current_fields: str = "",
    cache_file: str = "",
    changelog_cache_version: str = "1.0",
    cache_expiration_hours: int = 24,
) -> tuple[bool, list[dict]]:

    try:
        from data.persistence.factory import get_backend  # noqa: PLC0415

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.debug("[Cache] No active profile/query for changelog")
            return False, []

        issues = backend.get_issues(
            profile_id=active_profile_id, query_id=active_query_id
        )

        if not issues:
            logger.debug("[Cache] No issues with changelog in database")
            return False, []

        first_issue = issues[0]
        if "fetched_at" in first_issue:
            cache_timestamp = datetime.fromisoformat(first_issue["fetched_at"])
            cache_age = datetime.now(UTC) - cache_timestamp

            if cache_age > timedelta(hours=cache_expiration_hours):
                logger.debug(
                    "[Cache] Changelog expired: "
                    f"{cache_age.total_seconds() / 3600:.1f}h"
                )
                return False, []

            cache_age_str = f"{cache_age.total_seconds() / 3600:.1f}h old"
        else:
            cache_age_str = "unknown age"

        logger.info(
            "[Cache] Loaded "
            f"{len(issues)} issues with changelog from database ({cache_age_str})"
        )
        return True, issues

    except (PersistenceError, CacheError, KeyError, TypeError, ValueError) as e:
        logger.error(f"[Cache] Error loading changelog from database: {e}")
        return False, []
