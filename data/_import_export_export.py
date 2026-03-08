"""
Export functions for the import/export system.

T009: Profile export with setup status migration
T013: Enhanced export with mode support (CONFIG_ONLY, FULL_DATA)
Team sharing exports
"""

import json
import logging
import tempfile
import zipfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from data._import_export_types import ExportManifest
from data._import_export_validation import strip_credentials
from data.exceptions import PersistenceError

logger = logging.getLogger(__name__)


# ============================================================================
# T009: Profile Export System with Setup Status Migration
# ============================================================================


def export_profile_enhanced(
    profile_id: str,
    export_path: str,
    include_cache: bool = False,
    include_queries: bool = True,
    export_type: str = "backup",
) -> tuple[bool, str]:
    """Export profile with T009 setup status migration capabilities.

    Args:
        profile_id: Profile ID to export
        export_path: Output file path
        include_cache: Whether to include cached JIRA data
        include_queries: Whether to include saved queries
        export_type: Type of export (backup/sharing/migration)

    Returns:
        Tuple of (success, message)
    """
    try:
        # Load profile data
        from data.profile_manager import get_profile, get_profile_file_path

        profile_path = get_profile_file_path(profile_id)
        if not profile_path.exists():
            return False, f"Profile '{profile_id}' not found"

        profile_data = get_profile(profile_id)
        if not profile_data:
            return False, f"Failed to load profile '{profile_id}'"

        # Create temporary directory for export
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Prepare profile data for export
            export_data = _prepare_profile_for_export(profile_data, export_type)

            # Create export manifest
            manifest = ExportManifest(
                version="1.0",
                created_at=datetime.now(UTC).isoformat(),
                created_by=f"burndown-chart-{export_type}",
                export_type=export_type,
                profiles=[profile_id],
                includes_cache=include_cache,
                includes_queries=include_queries,
                includes_setup_status=True,
            )

            # Write files to temp directory
            with open(temp_path / "manifest.json", "w") as f:
                json.dump(asdict(manifest), f, indent=2)

            with open(temp_path / "profile.json", "w") as f:
                json.dump(export_data, f, indent=2)

            # Export queries if requested
            queries_exported = 0
            if include_queries:
                queries_exported = _export_profile_queries(profile_id, temp_path)

            # Export cache if requested
            cache_exported = False
            if include_cache:
                cache_exported = _export_profile_cache(profile_id, temp_path)

            # Create ZIP file
            with zipfile.ZipFile(export_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in temp_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        zip_file.write(file_path, arcname)

        # Build success message
        components = [f"profile '{profile_id}'"]
        if queries_exported > 0:
            components.append(f"{queries_exported} queries")
        if cache_exported:
            components.append("cached data")

        message = f"Exported {', '.join(components)} to {export_path}"
        logger.info(message)

        return True, message

    except (
        PersistenceError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
    ) as e:
        logger.error(f"Failed to export profile '{profile_id}': {e}")
        return False, f"Export failed: {e}"


def _prepare_profile_for_export(
    profile_data: dict[str, Any], export_type: str
) -> dict[str, Any]:
    """Prepare profile data for export with setup status handling."""
    # Deep copy to avoid modifying original
    profile_data = json.loads(json.dumps(profile_data))

    # Enhance setup status for export
    if "setup_status" not in profile_data:
        # Create minimal setup status for legacy profiles
        profile_data["setup_status"] = {
            "setup_complete": False,
            "current_step": "jira_connection",
            "export_metadata": {
                "exported_at": datetime.now(UTC).isoformat(),
                "source_version": "3.0",
                "was_legacy_profile": True,
            },
        }
    else:
        # Add export metadata to existing setup status
        profile_data["setup_status"]["export_metadata"] = {
            "exported_at": datetime.now(UTC).isoformat(),
            "source_version": "3.0",
            "original_setup_complete": profile_data["setup_status"].get(
                "setup_complete", False
            ),
        }

    # Clean sensitive data
    if "jira_config" in profile_data:
        # Remove sensitive fields but keep structure
        jira_config = profile_data["jira_config"].copy()
        if "token" in jira_config:
            jira_config["token"] = "<REDACTED_FOR_EXPORT>"
        profile_data["jira_config"] = jira_config

    return profile_data


def _export_profile_queries(profile_id: str, export_dir: Path) -> int:
    """Export all queries for a profile."""
    try:
        from data.query_manager import list_queries_for_profile

        queries = list_queries_for_profile(profile_id)
        queries_dir = export_dir / "queries"
        queries_dir.mkdir()

        for query in queries:
            query_file = queries_dir / f"{query['id']}.json"
            with open(query_file, "w") as f:
                json.dump(query, f, indent=2)

        return len(queries)

    except (
        PersistenceError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
    ) as e:
        logger.warning(f"Failed to export queries: {e}")
        return 0


def _export_profile_cache(profile_id: str, export_dir: Path) -> bool:
    """Export cached data for a profile (LEGACY - most data now in database).

    Note: This function is primarily for backward compatibility.
    Most cache data is now stored in SQLite database and exported separately.
    """
    try:
        from data.profile_manager import PROFILES_DIR

        profile_dir = PROFILES_DIR / profile_id
        # Legacy cache files - most data now in database
        cache_files = [
            "app_settings.json",
            "project_data.json",
            "jira_cache.json",  # LEGACY - now in database
            "jira_changelog_cache.json",  # LEGACY - now in database
            "metrics_snapshots.json",
        ]

        cache_dir = export_dir / "cache"
        cache_dir.mkdir()

        exported = False
        for cache_file in cache_files:
            source = profile_dir / cache_file
            if source.exists():
                dest = cache_dir / cache_file
                dest.write_text(source.read_text())
                exported = True

        return exported

    except (
        PersistenceError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
    ) as e:
        logger.warning(f"Failed to export cache: {e}")
        return False


# ============================================================================
# T013: Export with Mode Support
# ============================================================================


def export_profile_with_mode(
    profile_id: str,
    query_id: str,
    export_mode: str,
    include_token: bool = False,
    include_budget: bool = False,
    include_changelog: bool = False,
) -> dict[str, Any]:
    """Export FULL profile with ALL queries and their data.

    Args:
        profile_id: Profile identifier (e.g., "default")
        query_id: Active query identifier (used for manifest metadata, but all
            queries exported)
        export_mode: One of "CONFIG_ONLY", "FULL_DATA"
        include_token: Whether to include JIRA token (default: False)
        include_budget: Whether to include budget data (default: False)
        include_changelog: Whether to include changelog entries (default: False)

    Returns:
        Export package dictionary with structure:
        {
            "manifest": ExportManifest,
            "profile_data": dict,
            "query_data": {
                "query_id_1": {
                    query_metadata, project_data, jira_cache, metrics_snapshots
                },
                "query_id_2": {...},
                ...
            }
        }

    Raises:
        ValueError: If profile_id or query_id not found
        ValueError: If export_mode invalid
        FileNotFoundError: If profile/query files missing

    Example:
        >>> package = export_profile_with_mode(
        ...     "default", "sprint-123", "CONFIG_ONLY", False
        ... )
        >>> package["manifest"]["export_mode"]
        'CONFIG_ONLY'
        >>> len(package["query_data"])  # All queries exported
        3
    """
    # Validate export mode
    if export_mode not in ["CONFIG_ONLY", "FULL_DATA"]:
        raise ValueError(
            f"Invalid export_mode: {export_mode}. Must be 'CONFIG_ONLY' or 'FULL_DATA'"
        )

    # Load profile data from database
    from data.persistence import factory

    backend = factory.get_backend()
    profile_data = backend.get_profile(profile_id)

    if not profile_data:
        raise FileNotFoundError(f"Profile '{profile_id}' not found in database")

    # Strip credentials if not including token
    if not include_token:
        profile_data = strip_credentials(profile_data)

    # Create manifest
    manifest = ExportManifest(
        version="2.0",
        created_at=datetime.now(UTC).isoformat(),
        created_by="burndown-chart-enhanced",
        export_type="sharing",
        profiles=[profile_id],
        includes_cache=(export_mode == "FULL_DATA"),
        includes_queries=True,
        includes_setup_status=True,
        export_mode=export_mode,
        includes_token=include_token,
        includes_changelog=(export_mode == "FULL_DATA" and include_changelog),
    )

    # Build export package
    export_package: dict[str, Any] = {
        "manifest": asdict(manifest),
        "profile_data": profile_data,
    }

    # Export ALL queries (not just the active one) - True full-profile export
    all_queries_data = {}
    exported_query_count = 0

    # Get all queries for this profile from database
    queries = backend.list_queries(profile_id)

    for query_info in queries:
        current_query_id = query_info["id"]
        query_data = _export_single_query(
            backend,
            profile_id,
            current_query_id,
            query_info,
            profile_data,
            export_mode,
            include_budget,
            include_changelog,
        )
        all_queries_data[current_query_id] = query_data
        exported_query_count += 1

    if exported_query_count == 0:
        logger.warning(f"No queries found to export for profile '{profile_id}'")
        export_package["query_data"] = None
    else:
        export_package["query_data"] = all_queries_data
        logger.info(
            f"Exported {exported_query_count} queries for profile '{profile_id}'"
        )

    logger.info(
        f"Exported profile '{profile_id}' with {exported_query_count} queries, "
        f"mode='{export_mode}', token={include_token}, budget={include_budget}, "
        f"changelog={include_changelog}"
    )

    return export_package


def _export_single_query(
    backend: Any,
    profile_id: str,
    current_query_id: str,
    query_info: dict[str, Any],
    profile_data: dict[str, Any],
    export_mode: str,
    include_budget: bool,
    include_changelog: bool,
) -> dict[str, Any]:
    """Build the export payload for one query."""
    query_data: dict[str, Any] = {}

    # Query metadata is required for both modes
    query_data["query_metadata"] = {
        "id": query_info["id"],
        "name": query_info["name"],
        "jql": query_info["jql"],
        "created_at": query_info["created_at"],
        "last_used": query_info["last_used"],
    }

    if export_mode == "FULL_DATA":
        _attach_full_data(
            backend,
            profile_id,
            current_query_id,
            profile_data,
            query_data,
            include_changelog,
        )

    if include_budget:
        _attach_budget_data(backend, profile_id, current_query_id, query_data)

    return query_data


def _attach_full_data(
    backend: Any,
    profile_id: str,
    current_query_id: str,
    profile_data: dict[str, Any],
    query_data: dict[str, Any],
    include_changelog: bool,
) -> None:
    """Attach full JIRA and metrics data to a query export payload (in-place)."""
    # Get issues (replaces jira_cache.json)
    issues = backend.get_issues(profile_id, current_query_id, limit=100000)
    if issues:
        query_data["jira_cache"] = {"issues": issues}

    # Get statistics (replaces project_data.json and metrics_snapshots.json)
    statistics = backend.get_statistics(profile_id, current_query_id, limit=100000)
    if statistics:
        query_data["statistics"] = statistics

    # Get project scope (for forecasting context in AI prompts)
    project_scope = backend.get_scope(profile_id, current_query_id)
    if project_scope:
        query_data["project_scope"] = project_scope
        logger.info(f"Exported project scope for query '{current_query_id}'")

    # Get metrics data points (DORA, Flow, Bug metrics)
    metrics = backend.get_metric_values(profile_id, current_query_id, limit=100000)
    if metrics:
        query_data["metrics"] = metrics
        logger.info(
            f"Exported {len(metrics)} metrics data points for query "
            f"'{current_query_id}'"
        )

    if include_changelog:
        from data.import_export_changelog import collect_changelog_entries

        sprint_field = (
            profile_data.get("field_mappings", {})
            .get("general", {})
            .get("sprint_field")
        )
        changelog_entries = collect_changelog_entries(
            backend, profile_id, current_query_id, sprint_field
        )
        if changelog_entries:
            query_data["changelog_entries"] = changelog_entries
            logger.info(
                f"Exported {len(changelog_entries)} changelog entries "
                f"for query '{current_query_id}'"
            )


def _attach_budget_data(
    backend: Any,
    profile_id: str,
    current_query_id: str,
    query_data: dict[str, Any],
) -> None:
    """Attach budget settings and revisions to a query export payload (in-place)."""
    budget_settings = backend.get_budget_settings(profile_id, current_query_id)
    if budget_settings:
        query_data["budget_settings"] = budget_settings
        logger.info(f"Exported budget settings for query '{current_query_id}'")

    budget_revisions = backend.get_budget_revisions(profile_id, current_query_id)
    if budget_revisions:
        query_data["budget_revisions"] = budget_revisions
        logger.info(
            f"Exported {len(budget_revisions)} budget revisions for "
            f"query '{current_query_id}'"
        )


# ============================================================================
# T009: Team Sharing Export
# ============================================================================


def export_for_team_sharing(
    profile_id: str,
    export_path: str,
    share_level: str = "configuration",  # "configuration", "with_queries", "full"
) -> tuple[bool, str]:
    """Export profile for team sharing with appropriate data filtering.

    Args:
        profile_id: Profile to export
        export_path: Export file path
        share_level: Level of data sharing (configuration/with_queries/full)

    Returns:
        Tuple of (success, message)
    """
    include_cache = share_level == "full"
    include_queries = share_level in ["with_queries", "full"]

    return export_profile_enhanced(
        profile_id,
        export_path,
        include_cache=include_cache,
        include_queries=include_queries,
        export_type="team_sharing",
    )
