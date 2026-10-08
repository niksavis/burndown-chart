import json
import logging
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from data._import_export_types import ExportManifest
from data.profile_manager import (
    PROFILES_DIR,
    get_profile_file_path,
    load_profiles_metadata,
    save_profiles_metadata,
)
from data.query_manager import create_query

logger = logging.getLogger(__name__)


def import_profile_enhanced(
    import_path: str,
    target_profile_id: str | None = None,
    preserve_setup_status: bool = True,
    validate_dependencies: bool = True,
) -> tuple[bool, str, str | None]:

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with zipfile.ZipFile(import_path, "r") as zip_file:
                zip_file.extractall(temp_path)

            manifest_file = temp_path / "manifest.json"
            if not manifest_file.exists():
                return False, "Invalid export file - missing manifest", None

            with open(manifest_file) as f:
                manifest_data = json.load(f)
                _ = ExportManifest(**manifest_data)

            profile_file = temp_path / "profile.json"
            if not profile_file.exists():
                return False, "Invalid export file - missing profile data", None

            with open(profile_file) as f:
                profile_data = json.load(f)

            budget_data = None

            if not target_profile_id:
                base_name = profile_data.get("name", "Imported Profile")
                target_profile_id = _generate_unique_profile_id(base_name)

            setup_status = profile_data.get("setup_status", {})
            if preserve_setup_status and setup_status:
                migrated_status = _migrate_imported_setup_status(
                    setup_status, validate_dependencies
                )
                profile_data["setup_status"] = migrated_status

            success, new_profile_id = _create_profile_from_import(
                profile_data, target_profile_id, temp_path, budget_data
            )

            if not success:
                return False, f"Failed to create profile: {new_profile_id}", None

            logger.info(f"Successfully imported profile as '{new_profile_id}'")
            return (
                True,
                f"Profile imported successfully as '{new_profile_id}'",
                new_profile_id,
            )

    except Exception as e:
        logger.error(f"Failed to import profile: {e}")
        return False, f"Import failed: {e}", None


def _generate_unique_profile_id(base_name: str) -> str:

    base_id = base_name.lower().replace(" ", "-")
    base_id = "".join(c for c in base_id if c.isalnum() or c == "-")
    base_id = base_id.strip("-") or "imported-profile"

    if not get_profile_file_path(base_id).exists():
        return base_id

    counter = 2
    while get_profile_file_path(f"{base_id}-{counter}").exists():
        counter += 1

    return f"{base_id}-{counter}"


def _migrate_imported_setup_status(
    setup_status: dict[str, Any], validate_dependencies: bool
) -> dict[str, Any]:
    migrated_status = setup_status.copy()

    migrated_status["import_metadata"] = {
        "imported_at": datetime.now(UTC).isoformat(),
        "original_exported_at": setup_status.get("export_metadata", {}).get(
            "exported_at"
        ),
        "migration_applied": True,
        "validation_pending": validate_dependencies,
    }

    if validate_dependencies:
        migrated_status.update(
            {
                "jira_connected": False,
                "fields_mapped": False,
                "setup_complete": False,
                "current_step": "jira_connection",
                "last_validation": datetime.now(UTC).isoformat(),
            }
        )

    return migrated_status


def _create_profile_from_import(
    profile_data: dict[str, Any],
    profile_id: str,
    import_path: Path,
    budget_data: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    try:
        profile_name = profile_data.get("name", f"Imported Profile {profile_id}")

        profile_dir = PROFILES_DIR / profile_id
        queries_dir = profile_dir / "queries"
        profile_dir.mkdir(parents=True, exist_ok=True)
        queries_dir.mkdir(exist_ok=True)

        profile_data["id"] = profile_id
        profile_data["name"] = profile_name
        profile_data["created_at"] = datetime.now(UTC).isoformat()

        if "jira_config" in profile_data:
            jira_config = profile_data["jira_config"]
            if jira_config.get("token") == "<REDACTED_FOR_EXPORT>":
                jira_config["token"] = ""

        profile_path = get_profile_file_path(profile_id)
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=2)

        metadata = load_profiles_metadata()
        if "profiles" not in metadata:
            metadata["profiles"] = {}
        metadata["profiles"][profile_id] = profile_data
        save_profiles_metadata(metadata)

        queries_dir = import_path / "queries"
        if queries_dir.exists():
            _import_profile_queries(profile_id, queries_dir)

        cache_dir = import_path / "cache"
        if cache_dir.exists():
            _import_profile_cache(profile_id, cache_dir)

        return True, profile_id

    except Exception as e:
        logger.error(f"Failed to create profile from import: {e}")
        return False, str(e)


def _import_profile_queries(profile_id: str, queries_dir: Path) -> int:
    try:
        imported = 0
        for query_file in queries_dir.glob("*.json"):
            with open(query_file) as f:
                query_data = json.load(f)

            create_query(
                profile_id,
                query_data["name"],
                query_data["jql"],
            )
            imported += 1

        logger.info(f"Imported {imported} queries for profile '{profile_id}'")
        return imported

    except Exception as e:
        logger.warning(f"Failed to import queries: {e}")
        return 0


def _import_profile_cache(profile_id: str, cache_dir: Path) -> bool:
    try:
        target_dir = PROFILES_DIR / profile_id
        target_dir.mkdir(parents=True, exist_ok=True)

        imported = False
        for cache_file in cache_dir.glob("*.json"):
            target_file = target_dir / cache_file.name
            target_file.write_text(cache_file.read_text())
            imported = True

        return imported

    except Exception as e:
        logger.warning(f"Failed to import cache: {e}")
        return False


def import_shared_profile(
    import_path: str, team_member_name: str
) -> tuple[bool, str, str | None]:

    timestamp = datetime.now().strftime("%Y%m%d")
    target_profile_id = f"shared-{team_member_name.lower()}-{timestamp}"

    return import_profile_enhanced(
        import_path,
        target_profile_id=target_profile_id,
        preserve_setup_status=False,
        validate_dependencies=True,
    )
