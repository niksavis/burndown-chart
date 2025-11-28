"""Automatic profile migration system for Feature 012.

This module handles automatic migration of legacy field_mappings to the new
variable_mappings system. It runs on app startup and detects profiles that
need migration.

Migration Strategy:
1. Detect profiles with field_mappings but no variable_mappings
2. Convert field_mappings to variable_mappings using smart defaults
3. Preserve original field_mappings for backward compatibility (if needed)
4. Save updated profile with variable_mappings
5. Log migration actions for troubleshooting

Migration Mapping:
- deployment_date → deployment_timestamp variable
- work_started_date → work_started_timestamp variable
- work_completed_date → deployment_timestamp variable (for lead time)
- incident_start → incident_start_timestamp variable
- incident_resolved → incident_resolved_timestamp variable
- work_type → flow_type variable (Feature/Bug/Tech Debt/Risk)

Reference: specs/feature-012-rule-based-variable-mapping.md
"""

import logging
from typing import Dict, Any, Optional, Literal
import json

from data.profile_manager import (
    list_profiles,
    get_profile_file_path,
)
from data.variable_mapping.models import (
    VariableMapping,
    SourceRule,
    FieldValueSource,
)
from configuration.metric_variables import DEFAULT_VARIABLE_COLLECTION

logger = logging.getLogger(__name__)


def needs_migration(profile_data: Dict[str, Any]) -> bool:
    """Check if profile needs migration from field_mappings to variable_mappings.

    Args:
        profile_data: Profile configuration dictionary

    Returns:
        True if profile has field_mappings but no variable_mappings
    """
    has_field_mappings = bool(profile_data.get("field_mappings"))
    has_variable_mappings = bool(profile_data.get("variable_mappings"))

    # Only migrate if we have field_mappings but no variable_mappings
    return has_field_mappings and not has_variable_mappings


def migrate_field_mapping_to_variable(
    field_name: str,
    jira_field: str,
    variable_type: Literal[
        "datetime", "boolean", "number", "duration", "category", "count"
    ] = "datetime",
) -> Optional[VariableMapping]:
    """Convert a single field mapping to a variable mapping.

    Args:
        field_name: Variable name (e.g., "deployment_timestamp")
        jira_field: JIRA field identifier (e.g., "customfield_10001")
        variable_type: Variable type (datetime, boolean, number, etc.)

    Returns:
        VariableMapping object or None if conversion fails
    """
    try:
        # Map VariableMapping type to FieldValueSource type
        # VariableMapping types: datetime, boolean, number, duration, category, count
        # FieldValueSource types: datetime, string, number, boolean
        if variable_type in ["datetime"]:
            source_value_type = "datetime"
        elif variable_type in ["boolean"]:
            source_value_type = "boolean"
        elif variable_type in ["number", "duration", "count"]:
            source_value_type = "number"
        else:  # category
            source_value_type = "string"

        # Create simple field value source
        source = SourceRule(
            priority=1,
            source=FieldValueSource(
                type="field_value",
                field=jira_field,
                value_type=source_value_type,
            ),
        )

        mapping = VariableMapping(
            variable_name=field_name,
            variable_type=variable_type,
            metric_category="dora",  # Most legacy mappings are DORA
            description=f"Migrated from legacy field_mappings: {jira_field}",
            required=True,
            sources=[source],
        )

        return mapping

    except Exception as e:
        logger.error(f"Failed to migrate field mapping {field_name}: {e}")
        return None


def migrate_profile_field_mappings(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate field_mappings to variable_mappings for a profile.

    Args:
        profile_data: Profile configuration dictionary

    Returns:
        Updated profile data with variable_mappings
    """
    field_mappings = profile_data.get("field_mappings", {})
    if not field_mappings:
        logger.info("No field_mappings found, skipping migration")
        return profile_data

    logger.info(f"Migrating {len(field_mappings)} field mappings to variables")

    # Start with default variable collection
    variable_mappings = DEFAULT_VARIABLE_COLLECTION.model_dump()

    # Mapping table: field_mappings key → variable name
    migration_map = {
        # DORA metrics
        "deployment_date": "deployment_timestamp",
        "deployment_successful": "deployment_successful",
        "work_started_date": "work_started_timestamp",
        "work_completed_date": "deployment_timestamp",  # Same as deployment_date
        "incident_start": "incident_start_timestamp",
        "incident_resolved": "incident_resolved_timestamp",
        "incident_event": "incident_event",
        # Flow metrics
        "work_type": "flow_type",
        "work_item_size": "work_item_size",
    }

    migrated_count = 0
    for field_key, variable_name in migration_map.items():
        jira_field = field_mappings.get(field_key)
        if not jira_field:
            continue

        # Determine variable type based on field
        if "timestamp" in variable_name or "date" in variable_name:
            var_type: Literal[
                "datetime", "boolean", "number", "duration", "category", "count"
            ] = "datetime"
        elif "successful" in variable_name or "event" in variable_name:
            var_type = "boolean"
        elif "type" in variable_name:
            var_type = "category"
        elif "size" in variable_name:
            var_type = "number"
        else:
            var_type = "category"

        # Create variable mapping
        mapping = migrate_field_mapping_to_variable(variable_name, jira_field, var_type)
        if mapping:
            # Override default with migrated mapping
            variable_mappings["mappings"][variable_name] = mapping.model_dump()
            migrated_count += 1
            logger.info(
                f"Migrated {field_key} → {variable_name} (JIRA field: {jira_field})"
            )

    logger.info(f"Successfully migrated {migrated_count} field mappings")

    # Update profile with variable_mappings
    profile_data["variable_mappings"] = variable_mappings

    # Keep field_mappings for backward compatibility (commented out for now)
    # If we want to remove field_mappings entirely, uncomment this:
    # profile_data.pop("field_mappings", None)

    return profile_data


def migrate_profile(profile_id: str) -> bool:
    """Migrate a single profile from field_mappings to variable_mappings.

    Args:
        profile_id: Profile identifier

    Returns:
        True if migration succeeded, False otherwise
    """
    try:
        profile_path = get_profile_file_path(profile_id)

        if not profile_path.exists():
            logger.warning(f"Profile {profile_id} not found at {profile_path}")
            return False

        # Load profile data
        with open(profile_path, "r", encoding="utf-8") as f:
            profile_data = json.load(f)

        # Check if migration needed
        if not needs_migration(profile_data):
            logger.debug(f"Profile {profile_id} does not need migration")
            return True

        logger.info(f"Migrating profile {profile_id}...")

        # Perform migration
        updated_data = migrate_profile_field_mappings(profile_data)

        # Save updated profile
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully migrated profile {profile_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to migrate profile {profile_id}: {e}", exc_info=True)
        return False


def migrate_all_profiles() -> Dict[str, Any]:
    """Migrate all profiles that need migration.

    This function is called on app startup to automatically migrate profiles
    from legacy field_mappings to new variable_mappings system.

    Returns:
        Dictionary with migration results:
        {
            "total_profiles": int,
            "migrated": int,
            "skipped": int,
            "failed": int,
            "details": List[Dict]
        }
    """
    results = {
        "total_profiles": 0,
        "migrated": 0,
        "skipped": 0,
        "failed": 0,
        "details": [],
    }

    try:
        profiles = list_profiles()
        results["total_profiles"] = len(profiles)

        if not profiles:
            logger.info("No profiles found, skipping migration")
            return results

        logger.info(f"Checking {len(profiles)} profiles for migration...")

        for profile in profiles:
            profile_id = profile.get("id")
            if not profile_id:
                logger.warning("Profile missing ID, skipping")
                continue

            try:
                # Load profile data to check migration status
                profile_path = get_profile_file_path(profile_id)
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)

                if not needs_migration(profile_data):
                    results["skipped"] += 1
                    results["details"].append(
                        {
                            "profile_id": profile_id,
                            "status": "skipped",
                            "reason": "Already has variable_mappings or no field_mappings",
                        }
                    )
                    continue

                # Perform migration
                if migrate_profile(profile_id):
                    results["migrated"] += 1
                    results["details"].append(
                        {
                            "profile_id": profile_id,
                            "status": "success",
                            "reason": "Migrated field_mappings to variable_mappings",
                        }
                    )
                else:
                    results["failed"] += 1
                    results["details"].append(
                        {
                            "profile_id": profile_id,
                            "status": "failed",
                            "reason": "Migration function returned False",
                        }
                    )

            except Exception as e:
                results["failed"] += 1
                results["details"].append(
                    {
                        "profile_id": profile_id,
                        "status": "failed",
                        "reason": str(e),
                    }
                )
                logger.error(
                    f"Failed to process profile {profile_id}: {e}", exc_info=True
                )

        # Log summary
        logger.info(
            f"Migration complete: {results['migrated']} migrated, "
            f"{results['skipped']} skipped, {results['failed']} failed"
        )

        return results

    except Exception as e:
        logger.error(f"Failed to migrate profiles: {e}", exc_info=True)
        results["failed"] = results["total_profiles"]
        return results


def auto_migrate_on_startup() -> None:
    """Run automatic migration on app startup.

    This function is called from app.py to ensure all profiles are migrated
    before the app starts serving requests.
    """
    logger.info("Running automatic profile migration check...")

    try:
        results = migrate_all_profiles()

        if results["migrated"] > 0:
            logger.info(
                f"Auto-migration: Successfully migrated {results['migrated']} profile(s)"
            )

        if results["failed"] > 0:
            logger.warning(
                f"Auto-migration: Failed to migrate {results['failed']} profile(s)"
            )

        if results["total_profiles"] == 0:
            logger.debug("Auto-migration: No profiles to migrate")

    except Exception as e:
        logger.error(f"Auto-migration failed: {e}", exc_info=True)
        # Don't crash the app if migration fails - just log the error
