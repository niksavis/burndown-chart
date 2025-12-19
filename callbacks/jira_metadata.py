"""
JIRA Metadata Callbacks

This module handles app-level JIRA metadata fetching and caching.
Metadata is fetched once on app startup/page refresh and whenever
JIRA configuration changes. This prevents repeated API calls when
opening the field mapping modal.

Architecture:
- jira-metadata-store: App-level store containing fields, projects, statuses
- jira-config-hash: Tracks config version to detect changes
- Metadata fetch triggered by: app init, JIRA config save, page refresh
"""

import hashlib
import logging
from typing import Dict, Any, Tuple, Optional

from dash import callback, Output, Input, State, no_update, ctx

logger = logging.getLogger(__name__)


def _compute_config_hash(jira_config: Dict[str, Any]) -> str:
    """Compute hash of JIRA config to detect changes.

    Args:
        jira_config: JIRA configuration dictionary

    Returns:
        MD5 hash of config values that affect metadata fetching
    """
    # Only hash values that affect metadata fetching
    relevant_keys = ["base_url", "token", "api_version"]
    hash_input = "|".join(str(jira_config.get(key, "")) for key in relevant_keys)
    return hashlib.md5(hash_input.encode()).hexdigest()


def _fetch_jira_metadata(
    jira_config: Dict[str, Any],
) -> Tuple[Dict[str, Any], Optional[str]]:
    """Fetch all JIRA metadata for field mapping.

    Args:
        jira_config: JIRA configuration with base_url, token, api_version

    Returns:
        Tuple of (metadata_dict, error_message)
        - metadata_dict contains fields, projects, issue_types, statuses, auto_detected
        - error_message is None on success, error string on failure
    """
    from data.jira_metadata import create_metadata_fetcher
    from data.persistence import load_app_settings
    import time

    try:
        # Check if JIRA is configured
        if (
            not jira_config.get("base_url")
            or jira_config.get("base_url", "").strip() == ""
        ):
            logger.warning("[JiraMetadata] JIRA not configured, cannot fetch metadata")
            return {"error": "JIRA not configured"}, "JIRA not configured"

        # Create fetcher
        fetcher = create_metadata_fetcher(
            jira_url=jira_config.get("base_url", ""),
            jira_token=jira_config.get("token", ""),
            api_version=jira_config.get("api_version", "v2"),
        )

        logger.info("[JiraMetadata] Fetching JIRA metadata...")
        start_time = time.time()

        # Fetch all metadata types
        fields = fetcher.fetch_fields()
        projects = fetcher.fetch_projects()
        issue_types = fetcher.fetch_issue_types()
        statuses = fetcher.fetch_statuses()

        # Auto-detect configurations
        auto_detected_types = fetcher.auto_detect_issue_types(issue_types)
        auto_detected_statuses = fetcher.auto_detect_statuses(statuses)

        # Load current settings for field mappings
        settings = load_app_settings()

        # Fetch environment field options if mapped
        dora_mappings = settings.get("field_mappings", {}).get("dora", {})
        affected_env_field = dora_mappings.get("affected_environment")
        target_env_field = dora_mappings.get("target_environment")

        env_options = []
        env_field_to_fetch = None

        if affected_env_field:
            # Strip =Value suffix if present (e.g., "customfield_11309=PROD" -> "customfield_11309")
            env_field_to_fetch = affected_env_field.split("=")[0]
        elif target_env_field:
            env_field_to_fetch = target_env_field.split("=")[0]

        if env_field_to_fetch:
            env_options = fetcher.fetch_field_options(env_field_to_fetch)
            auto_detected_prod = fetcher.auto_detect_production_identifiers(env_options)
        else:
            auto_detected_prod = []

        # Fetch effort category field options if mapped
        # Note: effort_category is under field_mappings.flow, not at root level
        flow_mappings = settings.get("field_mappings", {}).get("flow", {})
        effort_category_field = flow_mappings.get("effort_category")
        effort_category_options = []
        if effort_category_field:
            effort_category_options = fetcher.fetch_field_options(effort_category_field)

        # Build field_options dictionary
        field_options_dict = {}
        if env_field_to_fetch and env_options:
            field_options_dict[env_field_to_fetch] = env_options

        if effort_category_field:
            field_options_dict[effort_category_field] = effort_category_options

        elapsed = time.time() - start_time
        metadata = {
            "fields": fields,
            "projects": projects,
            "issue_types": issue_types,
            "statuses": statuses,
            "field_options": field_options_dict,
            "auto_detected": {
                "issue_types": auto_detected_types,
                "statuses": auto_detected_statuses,
                "production_identifiers": auto_detected_prod,
            },
            "fetched_at": time.time(),
        }

        logger.info(
            f"[JiraMetadata] Fetched metadata in {elapsed:.2f}s: "
            f"{len(fields)} fields, {len(projects)} projects, "
            f"{len(issue_types)} issue types, {len(statuses)} statuses"
        )

        return metadata, None

    except Exception as e:
        logger.error(f"[JiraMetadata] Error fetching metadata: {e}")
        return {"error": str(e)}, str(e)


@callback(
    [
        Output("jira-metadata-store", "data"),
        Output("jira-config-hash", "data"),
    ],
    [
        Input("url", "pathname"),  # Trigger on page load/refresh
        Input("jira-config-save-trigger", "data"),  # Trigger on JIRA config save
        Input("profile-switch-trigger", "data"),  # Trigger on profile switch
        Input("metrics-refresh-trigger", "data"),  # Trigger on data refresh (import)
    ],
    [
        State("jira-config-hash", "data"),
    ],
    prevent_initial_call=False,  # Allow initial call to load metadata on startup
)
def fetch_metadata_on_startup_or_config_change(
    pathname: str,
    config_save_trigger: Any,
    profile_switch_trigger: int,
    metrics_refresh_trigger: int,
    current_hash: Optional[str],
):
    """Fetch JIRA metadata on app startup or when JIRA config changes.

    This callback runs:
    1. On initial page load (pathname input)
    2. When JIRA configuration is saved (config_save_trigger)
    3. When profile is switched (profile_switch_trigger)
    4. When data is refreshed after import (metrics_refresh_trigger)

    Args:
        pathname: Current URL path (triggers on page load)
        config_save_trigger: Trigger from JIRA config save callback
        profile_switch_trigger: Trigger from profile switch callback
        metrics_refresh_trigger: Trigger from import/data refresh callback
        current_hash: Current config hash to detect changes

    Returns:
        Tuple of (metadata_dict, config_hash)
    """
    from data.persistence import load_jira_configuration

    triggered_id = ctx.triggered_id if ctx.triggered else None

    # Load current JIRA config
    try:
        jira_config = load_jira_configuration()
    except Exception as e:
        logger.warning(f"[JiraMetadata] Could not load JIRA config: {e}")
        return {"error": "Could not load JIRA config"}, None

    # Compute config hash
    new_hash = _compute_config_hash(jira_config)

    # Check if config changed or if this is initial load
    if triggered_id == "jira-config-save-trigger":
        # Config was saved, force refresh
        logger.info("[JiraMetadata] JIRA config saved, refreshing metadata")
    elif current_hash == new_hash:
        # Config unchanged, skip fetch (use cached)
        logger.debug("[JiraMetadata] Config unchanged, skipping metadata fetch")
        return no_update, no_update
    else:
        # Initial load or config changed externally
        logger.info("[JiraMetadata] Initial load or config changed, fetching metadata")

    # Fetch metadata
    metadata, error = _fetch_jira_metadata(jira_config)

    if error:
        logger.warning(f"[JiraMetadata] Fetch failed: {error}")
        return metadata, new_hash

    return metadata, new_hash


# Note: The jira-config-save-trigger store needs to be added to layout.py
# and updated by the JIRA config save callback
