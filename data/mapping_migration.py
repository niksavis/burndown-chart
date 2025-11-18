"""Migration utilities for converting legacy field mappings to variable mappings.

This module provides tools to convert the old field_mappings format (used in
app_settings.json) to the new variable_mappings format, ensuring backward
compatibility while transitioning to the flexible variable mapping system.

Reference: docs/mapping_architecture_proposal.md - Migration Strategy
"""

import logging
from typing import Dict, Any, Optional, List
from data.variable_mapping.models import (
    VariableMapping,
    VariableMappingCollection,
    SourceRule,
    FieldValueSource,
    FieldValueMatchSource,
    ChangelogTimestampSource,
)
from data.persistence import load_app_settings
from configuration.metric_variables import create_default_variable_collection

logger = logging.getLogger(__name__)


# Legacy field mapping to variable mapping conversion rules
LEGACY_FIELD_TO_VARIABLE_MAP = {
    # DORA field mappings
    "deployment_date": "deployment_timestamp",
    "deployed_to_production_date": "deployment_timestamp",
    "code_commit_date": "commit_timestamp",
    "incident_detected_at": "incident_start_timestamp",
    "incident_resolved_at": "incident_resolved_timestamp",
    "deployment_successful": "deployment_successful",
    "target_environment": "environment",
    "production_impact": "is_incident",
    "severity_level": "is_incident",
    # Flow field mappings
    "work_started_date": "work_started_timestamp",
    "work_completed_date": "work_completed_timestamp",
    "completed_date": "completion_timestamp",
    "flow_item_type": "work_type_category",
    "status": "is_completed",
    "estimate": "work_item_size",
    # Common mappings
    "affected_environment": "environment",
    "effort_category": "work_type_category",
}


def migrate_legacy_field_mappings(
    legacy_mappings: Optional[Dict[str, str]] = None,
) -> VariableMappingCollection:
    """Convert legacy field_mappings to new variable_mappings format.

    Args:
        legacy_mappings: Optional dict of legacy field mappings.
                        If None, loads from app_settings.json

    Returns:
        VariableMappingCollection with migrated mappings

    Example:
        >>> legacy = {
        ...     "deployment_date": "customfield_10001",
        ...     "work_started_date": "customfield_10002"
        ... }
        >>> collection = migrate_legacy_field_mappings(legacy)
        >>> collection.get_mapping("deployment_timestamp")
    """
    # Load legacy mappings from settings if not provided
    if legacy_mappings is None:
        settings = load_app_settings()
        legacy_mappings = settings.get("field_mappings", {})

    if not legacy_mappings:
        logger.info("No legacy field mappings found, using defaults")
        return create_default_variable_collection()

    logger.info(f"Migrating {len(legacy_mappings)} legacy field mappings")

    # Start with default collection
    collection = create_default_variable_collection()

    # Override defaults with legacy mappings
    for legacy_field, jira_field in legacy_mappings.items():
        if not jira_field:
            continue

        # Map legacy field name to new variable name
        variable_name = LEGACY_FIELD_TO_VARIABLE_MAP.get(legacy_field)

        if not variable_name:
            logger.warning(f"Unknown legacy field: {legacy_field}, skipping")
            continue

        # Get existing variable mapping or skip if not found
        existing_mapping = collection.get_mapping(variable_name)
        if not existing_mapping:
            logger.warning(f"No default mapping for variable: {variable_name}")
            continue

        # Create migrated source with higher priority than defaults
        migrated_source = _create_migrated_source(
            jira_field, existing_mapping.variable_type, legacy_field
        )

        if migrated_source:
            # Insert migrated source at priority 1 (highest)
            updated_sources = [migrated_source]

            # Shift existing sources to lower priorities
            for rule in existing_mapping.sources:
                updated_sources.append(
                    SourceRule(
                        priority=rule.priority + 1,
                        source=rule.source,
                        filters=rule.filters,
                    )
                )

            # Update mapping with migrated source
            updated_mapping = VariableMapping(
                variable_name=existing_mapping.variable_name,
                variable_type=existing_mapping.variable_type,
                metric_category=existing_mapping.metric_category,
                description=existing_mapping.description,
                required=existing_mapping.required,
                sources=updated_sources,
                fallback_source=existing_mapping.fallback_source,
                validation_rules=existing_mapping.validation_rules,
                category_mapping=existing_mapping.category_mapping,
            )

            collection.mappings[variable_name] = updated_mapping
            logger.debug(
                f"Migrated {legacy_field} -> {variable_name} using {jira_field}"
            )

    return collection


def _create_migrated_source(
    jira_field: str, variable_type: str, legacy_field_name: str
) -> Optional[SourceRule]:
    """Create a SourceRule from legacy JIRA field mapping.

    Args:
        jira_field: JIRA field ID (e.g., "customfield_10001")
        variable_type: Target variable type (datetime, boolean, etc.)
        legacy_field_name: Original legacy field name for context

    Returns:
        SourceRule with priority 1 or None if conversion fails
    """
    # Determine source type based on variable type and field name
    if variable_type == "datetime":
        # Check if it's a changelog-based field
        if any(
            keyword in legacy_field_name
            for keyword in ["started", "completed", "resolved"]
        ):
            # Try to infer status transition
            transition_status = _infer_status_transition(legacy_field_name)
            if transition_status:
                return SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={"transition_to": transition_status},
                    ),
                )

        # Default to direct field access for datetime
        return SourceRule(
            priority=1,
            source=FieldValueSource(
                type="field_value", field=jira_field, value_type="datetime"
            ),
        )

    elif variable_type == "number":
        return SourceRule(
            priority=1,
            source=FieldValueSource(
                type="field_value", field=jira_field, value_type="number"
            ),
        )

    elif variable_type in ["category", "boolean"]:
        # Direct field access for category and boolean
        return SourceRule(
            priority=1,
            source=FieldValueSource(
                type="field_value", field=jira_field, value_type="string"
            ),
        )

    else:
        logger.warning(f"Unsupported variable type for migration: {variable_type}")
        return None


def _infer_status_transition(field_name: str) -> Optional[str]:
    """Infer target status from legacy field name.

    Args:
        field_name: Legacy field name (e.g., "work_started_date")

    Returns:
        Status name to transition to, or None
    """
    status_keywords = {
        "started": "In Progress",
        "completed": "Done",
        "resolved": "Resolved",
        "deployed": "Deployed",
        "detected": "Open",
    }

    for keyword, status in status_keywords.items():
        if keyword in field_name.lower():
            return status

    return None


def create_backward_compatible_field_mappings(
    collection: VariableMappingCollection,
) -> Dict[str, str]:
    """Convert variable mappings back to legacy field_mappings format.

    This allows the application to continue working with old code that
    expects field_mappings while using the new variable system internally.

    Args:
        collection: Variable mapping collection

    Returns:
        Dictionary in legacy field_mappings format

    Example:
        >>> collection = create_default_variable_collection()
        >>> legacy = create_backward_compatible_field_mappings(collection)
        >>> legacy["deployment_date"]  # Returns "customfield_XXXXX"
    """
    legacy_mappings = {}

    # Reverse mapping: variable name -> legacy field names
    variable_to_legacy = {}
    for legacy, variable in LEGACY_FIELD_TO_VARIABLE_MAP.items():
        if variable not in variable_to_legacy:
            variable_to_legacy[variable] = []
        variable_to_legacy[variable].append(legacy)

    # Convert each variable mapping to legacy format
    for variable_name, mapping in collection.mappings.items():
        legacy_field_names = variable_to_legacy.get(variable_name, [])

        if not legacy_field_names:
            continue

        # Get first source's field (highest priority)
        if mapping.sources:
            first_source = mapping.sources[0].source

            # Extract JIRA field from source (only for field-based sources)
            jira_field = None
            if isinstance(first_source, (FieldValueSource, FieldValueMatchSource)):
                jira_field = first_source.field

            if jira_field:
                # Map to all legacy field names for this variable
                for legacy_name in legacy_field_names:
                    legacy_mappings[legacy_name] = jira_field

    return legacy_mappings


def get_migration_report(
    legacy_mappings: Dict[str, str], migrated_collection: VariableMappingCollection
) -> Dict[str, Any]:
    """Generate a migration report showing what was converted.

    Args:
        legacy_mappings: Original legacy field mappings
        migrated_collection: Resulting variable mapping collection

    Returns:
        Dictionary with migration statistics and details
    """
    report = {
        "total_legacy_fields": len(legacy_mappings),
        "migrated_variables": 0,
        "skipped_fields": [],
        "unknown_fields": [],
        "mappings": [],
    }

    for legacy_field, jira_field in legacy_mappings.items():
        variable_name = LEGACY_FIELD_TO_VARIABLE_MAP.get(legacy_field)

        if not variable_name:
            report["unknown_fields"].append(legacy_field)
            continue

        mapping = migrated_collection.get_mapping(variable_name)

        if mapping and mapping.sources:
            # Check if migration source was added (priority 1)
            first_source = mapping.sources[0]
            if first_source.priority == 1:
                report["migrated_variables"] += 1
                report["mappings"].append(
                    {
                        "legacy_field": legacy_field,
                        "jira_field": jira_field,
                        "variable_name": variable_name,
                        "variable_type": mapping.variable_type,
                        "source_count": len(mapping.sources),
                    }
                )
            else:
                report["skipped_fields"].append(legacy_field)
        else:
            report["skipped_fields"].append(legacy_field)

    return report


def validate_migration(
    legacy_mappings: Dict[str, str], migrated_collection: VariableMappingCollection
) -> List[str]:
    """Validate that migration preserved all critical mappings.

    Args:
        legacy_mappings: Original legacy field mappings
        migrated_collection: Migrated variable collection

    Returns:
        List of validation errors (empty if successful)
    """
    errors = []

    # Check critical fields are present
    critical_legacy_fields = [
        "deployment_date",
        "work_started_date",
        "work_completed_date",
    ]

    for legacy_field in critical_legacy_fields:
        if legacy_field in legacy_mappings:
            variable_name = LEGACY_FIELD_TO_VARIABLE_MAP.get(legacy_field)
            if not variable_name:
                errors.append(f"No variable mapping for critical field: {legacy_field}")
                continue

            mapping = migrated_collection.get_mapping(variable_name)
            if not mapping:
                errors.append(f"Missing variable mapping: {variable_name}")
            elif not mapping.sources:
                errors.append(f"Variable {variable_name} has no sources")

    # Check for duplicate priorities
    for variable_name, mapping in migrated_collection.mappings.items():
        priorities = [rule.priority for rule in mapping.sources]
        if len(priorities) != len(set(priorities)):
            errors.append(f"Variable {variable_name} has duplicate source priorities")

    return errors


def save_migrated_collection(
    collection: VariableMappingCollection, output_file: str = "variable_mappings.json"
) -> None:
    """Save migrated variable mapping collection to JSON file.

    Args:
        collection: Variable mapping collection to save
        output_file: Path to output JSON file
    """
    import json
    from pathlib import Path

    data = collection.model_dump()

    output_path = Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved migrated variable mappings to {output_path}")
