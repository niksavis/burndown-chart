import copy
import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def strip_credentials(profile: dict[str, Any]) -> dict[str, Any]:

    safe_profile = copy.deepcopy(profile)

    SENSITIVE_FIELDS = ["jira_token", "jira_api_key", "api_secret", "token"]
    for field in SENSITIVE_FIELDS:
        safe_profile.pop(field, None)

    if "jira_config" in safe_profile and isinstance(safe_profile["jira_config"], dict):
        for field in SENSITIVE_FIELDS:
            safe_profile["jira_config"].pop(field, None)

    serialized = json.dumps(safe_profile).lower()
    FORBIDDEN_PATTERNS = ["token", "secret", "password", "api_key"]

    found_patterns = []
    for pattern in FORBIDDEN_PATTERNS:
        if (
            f'"{pattern}":' in serialized
            and f'"{pattern}": ""' not in serialized
            and f'"{pattern}": null' not in serialized
        ):
            found_patterns.append(pattern)

    if found_patterns:
        logger.warning(f"Potential credential leak: {found_patterns} found in export")

    return safe_profile


def validate_import_data(data: dict[str, Any]) -> tuple[bool, list[str]]:

    errors = []

    if not isinstance(data, dict):
        return False, ["Invalid format: data must be a dictionary"]

    if "manifest" not in data:
        errors.append("Missing 'manifest' key")
    if "profile_data" not in data:
        errors.append("Missing 'profile_data' key")

    if errors:
        return False, errors

    manifest = data.get("manifest", {})
    profile_data = data.get("profile_data", {})

    version = manifest.get("version", "")
    if not version:
        errors.append("Missing version in manifest")
    else:
        try:
            major_version = int(version.split(".")[0])
            if major_version < 1 or major_version > 2:
                errors.append(f"Unsupported version {version}. Expected 1.x or 2.x")
        except ValueError, IndexError:
            errors.append(f"Invalid version format: {version}")

    required_fields = ["profile_id", "jira_url", "jira_email"]
    for field in required_fields:
        if field not in profile_data:
            errors.append(f"Missing required field in profile_data: {field}")

    if "queries" in profile_data:
        queries = profile_data["queries"]
        if not isinstance(queries, list):
            errors.append("'queries' must be an array")
        else:
            for i, query in enumerate(queries):
                if not isinstance(query, dict):
                    errors.append(f"Invalid query at index {i}: must be an object")
                elif "query_id" not in query or "jql" not in query:
                    errors.append(
                        f"Invalid query at index {i}: missing query_id or jql"
                    )

    if manifest.get("includes_cache") and "query_data" not in data:
        logger.warning("Manifest claims includes_cache=true but query_data missing")

    if manifest.get("includes_token"):
        has_token = "jira_token" in profile_data and bool(
            profile_data.get("jira_token")
        )
        if not has_token:
            logger.warning(
                "Manifest claims includes_token=true but token missing or empty"
            )

    return (len(errors) == 0, errors)


def resolve_profile_conflict(
    profile_id: str,
    strategy: str,
    imported_data: dict[str, Any],
    existing_data: dict[str, Any],
) -> tuple[str, dict[str, Any]]:

    if strategy not in ["overwrite", "merge", "rename"]:
        raise ValueError(
            f"Invalid strategy: {strategy}. Must be 'overwrite', 'merge', or 'rename'"
        )

    if strategy == "overwrite":
        logger.info(f"Overwriting profile '{profile_id}' with imported data")
        return profile_id, imported_data

    if strategy == "merge":
        logger.info(f"Merging profile '{profile_id}' with imported data")
        merged = copy.deepcopy(imported_data)

        if "jira_token" in existing_data:
            merged["jira_token"] = existing_data["jira_token"]
        if "jira_email" in existing_data:
            merged["jira_email"] = existing_data["jira_email"]
        if "jira_url" in existing_data:
            merged["jira_url"] = existing_data["jira_url"]

        if "jira_config" in existing_data:
            if "jira_config" not in merged:
                merged["jira_config"] = {}
            merged["jira_config"].update(
                {
                    k: v
                    for k, v in existing_data["jira_config"].items()
                    if k in ["token", "jira_token", "api_key"]
                }
            )

        existing_queries = existing_data.get("queries", [])
        imported_queries = merged.get("queries", [])

        query_map = {q.get("query_id"): q for q in existing_queries if "query_id" in q}

        for query in imported_queries:
            if "query_id" in query:
                query_map[query["query_id"]] = query

        merged["queries"] = list(query_map.values())

        return profile_id, merged

    if strategy == "rename":
        friendly_name = imported_data.get("name", profile_id)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_profile_name = f"{friendly_name} (imported {timestamp})"
        new_profile_id = f"{profile_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(
            f"Renaming imported profile to '{new_profile_name}' (ID: {new_profile_id})"
        )

        renamed_data = copy.deepcopy(imported_data)
        renamed_data["id"] = new_profile_id
        renamed_data["name"] = new_profile_name
        if "profile_id" in renamed_data:
            renamed_data["profile_id"] = new_profile_id

        return new_profile_id, renamed_data

    raise ValueError(f"Unsupported conflict resolution strategy: {strategy}")
