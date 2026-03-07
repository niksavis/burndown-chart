"""
Validation and conflict resolution for the import/export system.

T005-T006: Credential stripping
T008: Import data validation
T010-T012: Profile conflict resolution strategies
"""

import copy
import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def strip_credentials(profile: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive fields from profile configuration.

    Creates a deep copy of the profile and removes all credential fields.
    Does NOT mutate the input dictionary.

    Args:
        profile: Profile configuration dictionary from profile.json

    Returns:
        Deep copy of profile with credentials removed

    Raises:
        ValueError: If credential patterns detected in output (validation failure)

    Example:
        >>> profile = {"jira_token": "secret", "jira_url": "https://example.com"}
        >>> safe = strip_credentials(profile)
        >>> "jira_token" in safe
        False
        >>> "jira_url" in safe
        True
    """
    # Create deep copy to avoid mutating input
    safe_profile = copy.deepcopy(profile)

    # Remove all credential fields
    SENSITIVE_FIELDS = ["jira_token", "jira_api_key", "api_secret", "token"]
    for field in SENSITIVE_FIELDS:
        safe_profile.pop(field, None)

    # Also check nested jira_config
    if "jira_config" in safe_profile and isinstance(safe_profile["jira_config"], dict):
        for field in SENSITIVE_FIELDS:
            safe_profile["jira_config"].pop(field, None)

    # Validate no credentials remain
    serialized = json.dumps(safe_profile).lower()
    FORBIDDEN_PATTERNS = ["token", "secret", "password", "api_key"]

    # Check for actual values, not just the word "token" in field names
    found_patterns = []
    for pattern in FORBIDDEN_PATTERNS:
        # Look for pattern followed by value (e.g., "token": "abc123")
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
    """Validate imported data for compatibility.

    Performs multi-stage validation:
    1. Format validation (JSON structure, required keys)
    2. Version compatibility (major version match)
    3. Schema validation (required profile fields)
    4. Integrity checks (manifest consistency)

    Args:
        data: Parsed JSON data from uploaded file

    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if all validation stages passed
        - error_messages: List of validation errors (empty if valid)

    Example:
        >>> data = {"manifest": {...}, "profile_data": {...}}
        >>> valid, errors = validate_import_data(data)
        >>> if not valid:
        ...     print("Errors:", errors)
    """
    errors = []

    # Stage 1: Format validation
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

    # Stage 2: Version compatibility
    version = manifest.get("version", "")
    if not version:
        errors.append("Missing version in manifest")
    else:
        try:
            major_version = int(version.split(".")[0])
            # Support version 1.x and 2.x
            if major_version < 1 or major_version > 2:
                errors.append(f"Unsupported version {version}. Expected 1.x or 2.x")
        except (ValueError, IndexError):
            errors.append(f"Invalid version format: {version}")

    # Stage 3: Schema validation
    required_fields = ["profile_id", "jira_url", "jira_email"]
    for field in required_fields:
        if field not in profile_data:
            errors.append(f"Missing required field in profile_data: {field}")

    # Validate queries structure if present
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

    # Stage 4: Integrity checks (warnings, not errors)
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
    """Resolve profile name conflict with user-selected strategy.

    Args:
        profile_id: Original profile identifier from import
        strategy: One of "overwrite", "merge", "rename"
        imported_data: Profile data from uploaded file
        existing_data: Existing profile data from filesystem

    Returns:
        Tuple of (final_profile_id, merged_data)
        - final_profile_id: Profile ID after resolution (may be renamed)
        - merged_data: Profile data after applying strategy

    Raises:
        ValueError: If strategy invalid

    Example:
        >>> final_id, merged = resolve_profile_conflict(
        ...     "default", "merge", imported, existing
        ... )
        >>> merged["jira_token"]  # Preserved from existing
        'LOCAL_TOKEN'
        >>> len(merged["queries"])  # Combined from both
        3
    """
    if strategy not in ["overwrite", "merge", "rename"]:
        raise ValueError(
            f"Invalid strategy: {strategy}. Must be 'overwrite', 'merge', or 'rename'"
        )

    # Strategy: Overwrite - replace existing with imported
    if strategy == "overwrite":
        logger.info(f"Overwriting profile '{profile_id}' with imported data")
        return profile_id, imported_data

    # Strategy: Merge - combine with precedence rules
    if strategy == "merge":
        logger.info(f"Merging profile '{profile_id}' with imported data")
        merged = copy.deepcopy(imported_data)

        # Preserve local credentials (never overwrite)
        if "jira_token" in existing_data:
            merged["jira_token"] = existing_data["jira_token"]
        if "jira_email" in existing_data:
            merged["jira_email"] = existing_data["jira_email"]
        if "jira_url" in existing_data:
            merged["jira_url"] = existing_data["jira_url"]

        # Preserve jira_config credentials
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

        # Combine queries (deduplicate by query_id)
        existing_queries = existing_data.get("queries", [])
        imported_queries = merged.get("queries", [])

        # Create map of existing queries by ID
        query_map = {q.get("query_id"): q for q in existing_queries if "query_id" in q}

        # Add/update with imported queries
        for query in imported_queries:
            if "query_id" in query:
                query_map[query["query_id"]] = query

        merged["queries"] = list(query_map.values())

        return profile_id, merged

    # Strategy: Rename - create new profile with timestamp suffix
    if strategy == "rename":
        # Use friendly name instead of technical ID for better UX
        friendly_name = imported_data.get("name", profile_id)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_profile_name = f"{friendly_name} (imported {timestamp})"
        # ID still needs to be unique, use timestamp-based ID
        new_profile_id = f"{profile_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(
            f"Renaming imported profile to '{new_profile_name}' (ID: {new_profile_id})"
        )

        # Update ID and name fields in the data (support both old and new field names)
        renamed_data = copy.deepcopy(imported_data)
        renamed_data["id"] = new_profile_id
        renamed_data["name"] = new_profile_name
        # Also update profile_id for backward compatibility
        if "profile_id" in renamed_data:
            renamed_data["profile_id"] = new_profile_id

        return new_profile_id, renamed_data

    # Should never reach here due to strategy validation at start
    raise ValueError(f"Unsupported conflict resolution strategy: {strategy}")
