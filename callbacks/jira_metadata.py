import hashlib
import logging
from typing import Any

from dash import Input, Output, State, callback, ctx, no_update

from data.jira.metadata_fetcher import create_metadata_fetcher
from data.persistence import load_app_settings, load_jira_configuration

logger = logging.getLogger(__name__)


def _compute_config_hash(jira_config: dict[str, Any]) -> str:

    relevant_keys = ["base_url", "token", "api_version"]
    hash_input = "|".join(str(jira_config.get(key, "")) for key in relevant_keys)
    return hashlib.md5(hash_input.encode(), usedforsecurity=False).hexdigest()


def _fetch_jira_metadata(
    jira_config: dict[str, Any],
) -> tuple[dict[str, Any], str | None]:

    import time  # noqa: PLC0415

    try:
        if (
            not jira_config.get("base_url")
            or jira_config.get("base_url", "").strip() == ""
        ):
            logger.warning("[JiraMetadata] JIRA not configured, cannot fetch metadata")
            return {"error": "JIRA not configured"}, "JIRA not configured"

        fetcher = create_metadata_fetcher(
            jira_url=jira_config.get("base_url", ""),
            jira_token=jira_config.get("token", ""),
            api_version=jira_config.get("api_version", "v2"),
        )

        logger.info("[JiraMetadata] Fetching JIRA metadata...")
        start_time = time.time()

        fields = fetcher.fetch_fields()
        projects = fetcher.fetch_projects()
        issue_types = fetcher.fetch_issue_types()
        statuses = fetcher.fetch_statuses()

        auto_detected_types = fetcher.auto_detect_issue_types(issue_types)
        auto_detected_statuses = fetcher.auto_detect_statuses(statuses)

        settings = load_app_settings()

        dora_mappings = settings.get("field_mappings", {}).get("dora", {})
        affected_env_field = dora_mappings.get("affected_environment")
        target_env_field = dora_mappings.get("target_environment")

        env_options = []
        env_field_to_fetch = None

        if affected_env_field:
            env_field_to_fetch = affected_env_field.split("=")[0]
        elif target_env_field:
            env_field_to_fetch = target_env_field.split("=")[0]

        if env_field_to_fetch:
            env_options = fetcher.fetch_field_options(env_field_to_fetch)
            auto_detected_prod = fetcher.auto_detect_production_identifiers(env_options)
        else:
            auto_detected_prod = []

        flow_mappings = settings.get("field_mappings", {}).get("flow", {})
        effort_category_field = flow_mappings.get("effort_category")
        effort_category_options = []
        if effort_category_field:
            effort_category_options = fetcher.fetch_field_options(effort_category_field)

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
        Input("url", "pathname"),
        Input("jira-config-save-trigger", "data"),
        Input("profile-switch-trigger", "data"),
        Input("metrics-refresh-trigger", "data"),
    ],
    [
        State("jira-config-hash", "data"),
    ],
    prevent_initial_call=False,
)
def fetch_metadata_on_startup_or_config_change(
    pathname: str,
    config_save_trigger: Any,
    profile_switch_trigger: int,
    metrics_refresh_trigger: int,
    current_hash: str | None,
):

    triggered_id = ctx.triggered_id if ctx.triggered else None

    try:
        jira_config = load_jira_configuration()
    except Exception as e:
        logger.warning(f"[JiraMetadata] Could not load JIRA config: {e}")
        return {"error": "Could not load JIRA config"}, None

    new_hash = _compute_config_hash(jira_config)

    if triggered_id == "jira-config-save-trigger":
        logger.info("[JiraMetadata] JIRA config saved, refreshing metadata")
    elif current_hash == new_hash:
        logger.debug("[JiraMetadata] Config unchanged, skipping metadata fetch")
        return no_update, no_update
    else:
        logger.info("[JiraMetadata] Initial load or config changed, fetching metadata")

    metadata, error = _fetch_jira_metadata(jira_config)

    if error:
        logger.warning(f"[JiraMetadata] Fetch failed: {error}")
        return metadata, new_hash

    return metadata, new_hash
