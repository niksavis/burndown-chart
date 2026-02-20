"""
JIRA cache operations module.

This module handles loading and saving JIRA response data to database cache.
"""

import logging
from datetime import UTC, datetime, timedelta

from data.cache_manager import (
    generate_cache_key,
    load_cache_with_validation,
)
from data.persistence import load_app_settings, save_app_settings

logger = logging.getLogger(__name__)


def cache_jira_response(
    data: list[dict],
    jql_query: str = "",
    fields_requested: str = "",
    cache_file: str = "",
    config: dict | None = None,
    generate_config_hash_func=None,
) -> bool:
    """
    Save JIRA response to DATABASE using persistence backend.

    After database migration, this function:
    1. Saves normalized issues to database (backend.save_issues_batch())
    2. Maintains legacy JSON file for backward compatibility
    3. Saves cache metadata for audit trail

    Args:
        data: JIRA issues to cache
        jql_query: JQL query used
        fields_requested: Fields requested in API call
        cache_file: Legacy parameter (maintains backward compatibility)
        config: JIRA configuration for generating cache key and hash
        generate_config_hash_func: Function to generate config hash

    Returns:
        True if cached successfully
    """
    try:
        # PHASE 1: Save to DATABASE (primary storage after migration)
        try:
            from data.persistence.factory import get_backend

            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")
            active_query_id = backend.get_app_state("active_query_id")

            if active_profile_id and active_query_id:
                # Generate cache key for database storage
                field_mappings = config.get("field_mappings", {}) if config else {}
                cache_key = generate_cache_key(
                    jql_query=jql_query,
                    field_mappings=field_mappings,
                    time_period_days=30,  # Default time period
                )

                # Set expiration (24 hours)
                utc_now = datetime.now(UTC)
                expires_at = utc_now + timedelta(hours=24)

                # Save issues to database using backend
                # This normalizes data and stores in jira_issues table
                backend.save_issues_batch(
                    profile_id=active_profile_id,
                    query_id=active_query_id,
                    cache_key=cache_key,
                    issues=data,
                    expires_at=expires_at,
                )

                logger.info(
                    f"[Database] Saved {len(data)} issues to database for {active_profile_id}/{active_query_id}"
                )

                # Save cache metadata to app settings for audit trail
                if config and generate_config_hash_func:
                    config_hash = generate_config_hash_func(config, fields_requested)
                    try:
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
                    except Exception as metadata_error:
                        logger.warning(
                            f"[Cache] Failed to save metadata: {metadata_error}"
                        )

            else:
                logger.warning(
                    "[Database] No active profile/query - skipping database save"
                )

        except Exception as db_error:
            logger.error(
                f"[Database] Failed to save issues to database: {db_error}",
                exc_info=True,
            )

        return True

    except Exception as e:
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
    """
    Load cached JIRA JSON response using new cache_manager.

    Args:
        current_jql_query: Current JQL query for cache validation
        current_fields: Current fields for cache validation
        cache_file: Legacy parameter (now uses cache/ directory)
        config: JIRA configuration for generating cache key and hash
        generate_config_hash_func: Function to generate config hash
        cache_version: Cache version for validation
        cache_expiration_hours: Cache expiration time in hours

    Returns:
        Tuple of (cache_hit: bool, issues: List[Dict])
    """
    # If no config provided, cannot validate cache
    if not config:
        logger.debug("[Cache] No config provided, cache miss")
        return False, []

    try:
        # Generate cache key from configuration
        # CRITICAL FIX: Use generate_jira_data_cache_key() which excludes field_mappings
        # This allows field mapping changes (like WIP states) to reuse cached JIRA data
        from data.cache_manager import generate_jira_data_cache_key

        cache_key = generate_jira_data_cache_key(
            jql_query=current_jql_query,
            time_period_days=30,  # Default time period for now
        )

        # Generate config hash for validation (but it doesn't affect cache key anymore)
        if generate_config_hash_func:
            config_hash = generate_config_hash_func(config, current_fields)
        else:
            config_hash = ""

        # Try to load from new cache system
        is_valid, cached_data = load_cache_with_validation(
            cache_key=cache_key,
            config_hash=config_hash,
            max_age_hours=cache_expiration_hours,
            cache_dir="cache",
        )

        if is_valid and cached_data:
            logger.info(f"[Cache] Hit: Loaded {len(cached_data)} issues from cache")
            return True, cached_data

        # No cache available
        logger.debug("[Cache] Miss: No valid cache found")
        return False, []

    except Exception as e:
        logger.error(f"[Cache] Error loading: {e}", exc_info=True)
        return False, []


def load_changelog_cache(
    current_jql_query: str = "",
    current_fields: str = "",
    cache_file: str = "",
    changelog_cache_version: str = "1.0",
    cache_expiration_hours: int = 24,
) -> tuple[bool, list[dict]]:
    """
    Load cached JIRA issues with changelog from DATABASE.

    Cache is invalidated if:
    - Cache is older than cache_expiration_hours
    - No issues found in database

    Args:
        current_jql_query: Ignored (for backward compatibility)
        current_fields: Ignored (for backward compatibility)
        cache_file: Ignored (legacy parameter)
        changelog_cache_version: Ignored (for backward compatibility)
        cache_expiration_hours: Cache expiration time in hours

    Returns:
        Tuple of (cache_loaded: bool, issues: List[Dict])
    """
    try:
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.debug("[Cache] No active profile/query for changelog")
            return False, []

        # Load issues with changelog from database
        issues = backend.get_issues(
            profile_id=active_profile_id, query_id=active_query_id
        )

        if not issues:
            logger.debug("[Cache] No issues with changelog in database")
            return False, []

        # Check cache age from first issue's fetched_at timestamp
        first_issue = issues[0]
        if "fetched_at" in first_issue:
            cache_timestamp = datetime.fromisoformat(first_issue["fetched_at"])
            cache_age = datetime.now(UTC) - cache_timestamp

            if cache_age > timedelta(hours=cache_expiration_hours):
                logger.debug(
                    f"[Cache] Changelog expired: {cache_age.total_seconds() / 3600:.1f}h"
                )
                return False, []

            cache_age_str = f"{cache_age.total_seconds() / 3600:.1f}h old"
        else:
            cache_age_str = "unknown age"

        logger.info(
            f"[Cache] Loaded {len(issues)} issues with changelog from database ({cache_age_str})"
        )
        return True, issues

    except Exception as e:
        logger.error(f"[Cache] Error loading changelog from database: {e}")
        return False, []
