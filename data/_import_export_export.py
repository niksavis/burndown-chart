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
from data.import_export_changelog import collect_changelog_entries
from data.persistence.factory import get_backend
from data.profile_manager import PROFILES_DIR, get_profile, get_profile_file_path
from data.query_manager import list_queries_for_profile

logger = logging.getLogger(__name__)


def export_profile_enhanced(
    profile_id: str,
    export_path: str,
    include_cache: bool = False,
    include_queries: bool = True,
    export_type: str = "backup",
) -> tuple[bool, str]:

    try:
        profile_path = get_profile_file_path(profile_id)
        if not profile_path.exists():
            return False, f"Profile '{profile_id}' not found"

        profile_data = get_profile(profile_id)
        if not profile_data:
            return False, f"Failed to load profile '{profile_id}'"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            export_data = _prepare_profile_for_export(profile_data, export_type)

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

            with open(temp_path / "manifest.json", "w") as f:
                json.dump(asdict(manifest), f, indent=2)

            with open(temp_path / "profile.json", "w") as f:
                json.dump(export_data, f, indent=2)

            queries_exported = 0
            if include_queries:
                queries_exported = _export_profile_queries(profile_id, temp_path)

            cache_exported = False
            if include_cache:
                cache_exported = _export_profile_cache(profile_id, temp_path)

            with zipfile.ZipFile(export_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in temp_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_path)
                        zip_file.write(file_path, arcname)

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
    profile_data = json.loads(json.dumps(profile_data))

    if "setup_status" not in profile_data:
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
        profile_data["setup_status"]["export_metadata"] = {
            "exported_at": datetime.now(UTC).isoformat(),
            "source_version": "3.0",
            "original_setup_complete": profile_data["setup_status"].get(
                "setup_complete", False
            ),
        }

    if "jira_config" in profile_data:
        jira_config = profile_data["jira_config"].copy()
        if "token" in jira_config:
            jira_config["token"] = "<REDACTED_FOR_EXPORT>"
        profile_data["jira_config"] = jira_config

    return profile_data


def _export_profile_queries(profile_id: str, export_dir: Path) -> int:
    try:
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

    try:
        profile_dir = PROFILES_DIR / profile_id
        cache_files = [
            "app_settings.json",
            "project_data.json",
            "jira_cache.json",
            "jira_changelog_cache.json",
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


def export_profile_with_mode(
    profile_id: str,
    query_id: str,
    export_mode: str,
    include_token: bool = False,
    include_budget: bool = False,
    include_changelog: bool = False,
) -> dict[str, Any]:

    if export_mode not in ["CONFIG_ONLY", "FULL_DATA"]:
        raise ValueError(
            f"Invalid export_mode: {export_mode}. Must be 'CONFIG_ONLY' or 'FULL_DATA'"
        )

    backend = get_backend()
    profile_data = backend.get_profile(profile_id)

    if not profile_data:
        raise FileNotFoundError(f"Profile '{profile_id}' not found in database")

    if not include_token:
        profile_data = strip_credentials(profile_data)

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

    export_package: dict[str, Any] = {
        "manifest": asdict(manifest),
        "profile_data": profile_data,
    }

    all_queries_data = {}
    exported_query_count = 0

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
    query_data: dict[str, Any] = {}

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
    issues = backend.get_issues(profile_id, current_query_id, limit=100000)
    if issues:
        query_data["jira_cache"] = {"issues": issues}

    statistics = backend.get_statistics(profile_id, current_query_id, limit=100000)
    if statistics:
        query_data["statistics"] = statistics

    project_scope = backend.get_scope(profile_id, current_query_id)
    if project_scope:
        query_data["project_scope"] = project_scope
        logger.info(f"Exported project scope for query '{current_query_id}'")

    metrics = backend.get_metric_values(profile_id, current_query_id, limit=100000)
    if metrics:
        query_data["metrics"] = metrics
        logger.info(
            f"Exported {len(metrics)} metrics data points for query "
            f"'{current_query_id}'"
        )

    if include_changelog:
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


def export_for_team_sharing(
    profile_id: str,
    export_path: str,
    share_level: str = "configuration",
) -> tuple[bool, str]:

    include_cache = share_level == "full"
    include_queries = share_level in ["with_queries", "full"]

    return export_profile_enhanced(
        profile_id,
        export_path,
        include_cache=include_cache,
        include_queries=include_queries,
        export_type="team_sharing",
    )
