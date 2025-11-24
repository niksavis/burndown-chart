"""Metric variable definitions catalog for DORA and Flow metrics.

This module defines all variables needed to calculate DORA and Flow metrics,
with default source configurations that users can customize via UI.

Reference: docs/metric_variable_mapping_spec.md
"""

from typing import Dict
from data.variable_mapping.models import (
    VariableMapping,
    VariableMappingCollection,
    SourceRule,
    MappingFilter,
    FieldValueSource,
    FieldValueMatchSource,
    ChangelogEventSource,
    ChangelogTimestampSource,
    FixVersionSource,
    CalculatedSource,
)


def create_default_dora_variables() -> Dict[str, VariableMapping]:
    """Create default variable mappings for DORA metrics.

    Returns:
        Dictionary mapping variable names to VariableMapping objects
    """
    return {
        # Deployment Frequency variables
        "deployment_event": VariableMapping(
            variable_name="deployment_event",
            variable_type="boolean",
            metric_category="dora",
            description="Indicates whether an issue represents a deployment occurrence",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="status.name",
                        operator="equals",
                        value="Deployed",
                    ),
                    filters=MappingFilter(
                        environment_field="customfield_10001",
                        environment_value="Production",
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=ChangelogEventSource(
                        type="changelog_event",
                        field="status",
                        condition={"transition_to": "Deployed"},
                    ),
                ),
                SourceRule(
                    priority=3,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="issuetype.name",
                        operator="equals",
                        value="Deployment",
                    ),
                ),
            ],
            fallback_source=SourceRule(
                priority=99,
                source=FieldValueMatchSource(
                    type="field_value_match",
                    field="fixVersions",
                    operator="not_equals",
                    value=[],
                ),
            ),
        ),
        "deployment_timestamp": VariableMapping(
            variable_name="deployment_timestamp",
            variable_type="datetime",
            metric_category="dora",
            description="When the deployment occurred",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={"transition_to": "Deployed"},
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=FixVersionSource(
                        type="fixversion_releasedate",
                        field="fixVersions",
                        selector="first",
                    ),
                ),
                SourceRule(
                    priority=3,
                    source=FieldValueSource(
                        type="field_value",
                        field="resolutiondate",
                        value_type="datetime",
                    ),
                ),
            ],
        ),
        "deployment_successful": VariableMapping(
            variable_name="deployment_successful",
            variable_type="boolean",
            metric_category="dora",
            description="Whether deployment succeeded (exclude failures from count)",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="status.name",
                        operator="not_in",
                        value=["Failed", "Rolled Back", "Deployment Failed"],
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="resolution.name",
                        operator="equals",
                        value="Deployed Successfully",
                    ),
                ),
            ],
            fallback_source=SourceRule(
                priority=99,
                source=FieldValueMatchSource(
                    type="field_value_match",
                    field="status.name",
                    operator="equals",
                    value="Done",  # Assume success if marked Done
                ),
            ),
        ),
        # Lead Time for Changes variables
        "commit_timestamp": VariableMapping(
            variable_name="commit_timestamp",
            variable_type="datetime",
            metric_category="dora",
            description="When code was committed",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={"transition_to": "In Development"},
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=FieldValueSource(
                        type="field_value", field="created", value_type="datetime"
                    ),
                ),
            ],
        ),
        # Change Failure Rate variables
        "is_incident": VariableMapping(
            variable_name="is_incident",
            variable_type="boolean",
            metric_category="dora",
            description="Whether issue is a production incident",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="issuetype.name",
                        operator="in",
                        value=["Incident", "Bug", "Defect"],
                    ),
                    filters=MappingFilter(
                        environment_field="customfield_10001",
                        environment_value="Production",
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="priority.name",
                        operator="in",
                        value=["Critical", "Blocker"],
                    ),
                ),
            ],
        ),
        "incident_start_timestamp": VariableMapping(
            variable_name="incident_start_timestamp",
            variable_type="datetime",
            metric_category="dora",
            description="When incident was detected/started",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(
                        type="field_value", field="created", value_type="datetime"
                    ),
                )
            ],
        ),
        "incident_resolved_timestamp": VariableMapping(
            variable_name="incident_resolved_timestamp",
            variable_type="datetime",
            metric_category="dora",
            description="When incident was resolved",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={"transition_to": "Resolved"},
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=FieldValueSource(
                        type="field_value",
                        field="resolutiondate",
                        value_type="datetime",
                    ),
                ),
            ],
        ),
        "related_deployment": VariableMapping(
            variable_name="related_deployment",
            variable_type="category",
            metric_category="dora",
            description="Deployment that caused the incident (for CFR calculation)",
            required=False,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(
                        type="field_value",
                        field="customfield_10020",  # Example: deployment link field
                    ),
                )
            ],
        ),
    }


def create_default_flow_variables() -> Dict[str, VariableMapping]:
    """Create default variable mappings for Flow metrics.

    Returns:
        Dictionary mapping variable names to VariableMapping objects
    """
    return {
        # Flow Velocity variables
        "is_completed": VariableMapping(
            variable_name="is_completed",
            variable_type="boolean",
            metric_category="flow",
            description="Whether work item is completed",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="status.name",
                        operator="in",
                        value=["Done", "Closed", "Resolved"],
                    ),
                )
            ],
        ),
        "completion_timestamp": VariableMapping(
            variable_name="completion_timestamp",
            variable_type="datetime",
            metric_category="flow",
            description="When work item was completed",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={"transition_to": "Done"},
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=FieldValueSource(
                        type="field_value",
                        field="resolutiondate",
                        value_type="datetime",
                    ),
                ),
            ],
        ),
        "work_item_size": VariableMapping(
            variable_name="work_item_size",
            variable_type="number",
            metric_category="flow",
            description="Size of work item (story points, hours, etc.)",
            required=False,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(
                        type="field_value",
                        field="customfield_10002",  # Common story points field
                        value_type="number",
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=FieldValueSource(
                        type="field_value",
                        field="timeoriginalestimate",
                        value_type="number",
                    ),
                ),
            ],
            fallback_source=SourceRule(
                priority=99,
                source=CalculatedSource(
                    type="calculated",
                    calculation="count_transitions",
                    inputs={"field": "status"},
                ),
            ),
        ),
        # Flow Time variables
        "work_started_timestamp": VariableMapping(
            variable_name="work_started_timestamp",
            variable_type="datetime",
            metric_category="flow",
            description="When work actually started",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={"transition_to": "In Progress"},
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={"transition_from": "To Do"},
                    ),
                ),
            ],
            fallback_source=SourceRule(
                priority=99,
                source=FieldValueSource(
                    type="field_value",
                    field="created",
                    value_type="datetime",
                ),
            ),
        ),
        "work_completed_timestamp": VariableMapping(
            variable_name="work_completed_timestamp",
            variable_type="datetime",
            metric_category="flow",
            description="When work was completed",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={"transition_to": "Done"},
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=FieldValueSource(
                        type="field_value",
                        field="resolutiondate",
                        value_type="datetime",
                    ),
                ),
            ],
        ),
        # Flow Efficiency variables
        "active_time": VariableMapping(
            variable_name="active_time",
            variable_type="duration",
            metric_category="flow",
            description="Total time in active work statuses",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=CalculatedSource(
                        type="calculated",
                        calculation="sum_changelog_durations",
                        inputs={
                            "field": "status",
                            "statuses": ["In Progress", "In Review", "Testing"],
                        },
                    ),
                )
            ],
        ),
        "total_time": VariableMapping(
            variable_name="total_time",
            variable_type="duration",
            metric_category="flow",
            description="Total cycle time from start to completion",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=CalculatedSource(
                        type="calculated",
                        calculation="timestamp_diff",
                        inputs={
                            "start": "work_started_timestamp",
                            "end": "work_completed_timestamp",
                        },
                    ),
                )
            ],
        ),
        # Flow Load variables
        "is_in_progress": VariableMapping(
            variable_name="is_in_progress",
            variable_type="boolean",
            metric_category="flow",
            description="Whether work item is currently in progress",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="status.name",
                        operator="in",
                        value=["In Progress", "In Review", "Testing", "Blocked"],
                    ),
                )
            ],
        ),
        # Flow Distribution variables
        "work_type_category": VariableMapping(
            variable_name="work_type_category",
            variable_type="category",
            metric_category="flow",
            description="Category of work (Feature, Bug, Tech Debt, Risk)",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(
                        type="field_value",
                        field="customfield_10010",  # Work type custom field
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=FieldValueSource(type="field_value", field="issuetype.name"),
                ),
            ],
            category_mapping={
                "Story": ["Feature"],
                "Epic": ["Feature"],
                "Task": ["Feature"],
                "Bug": ["Bug"],
                "Defect": ["Bug"],
                "Incident": ["Bug"],
                "Technical Debt": ["Tech Debt"],
                "Spike": ["Tech Debt"],
                "Risk": ["Risk"],
                "Security": ["Risk"],
            },
        ),
    }


def create_default_common_variables() -> Dict[str, VariableMapping]:
    """Create common variables used across multiple metrics.

    Returns:
        Dictionary mapping variable names to VariableMapping objects
    """
    return {
        "project_key": VariableMapping(
            variable_name="project_key",
            variable_type="category",
            metric_category="common",
            description="JIRA project key",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(type="field_value", field="project.key"),
                )
            ],
        ),
        "issue_type": VariableMapping(
            variable_name="issue_type",
            variable_type="category",
            metric_category="common",
            description="Type of issue",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(type="field_value", field="issuetype.name"),
                )
            ],
        ),
        "created_timestamp": VariableMapping(
            variable_name="created_timestamp",
            variable_type="datetime",
            metric_category="common",
            description="When issue was created",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(
                        type="field_value", field="created", value_type="datetime"
                    ),
                )
            ],
        ),
        "environment": VariableMapping(
            variable_name="environment",
            variable_type="category",
            metric_category="common",
            description="Environment (Production, Staging, etc.)",
            required=False,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(
                        type="field_value",
                        field="customfield_10001",  # Environment custom field
                    ),
                )
            ],
        ),
    }


def create_default_variable_collection() -> VariableMappingCollection:
    """Create complete default variable mapping collection.

    Returns:
        VariableMappingCollection with all default DORA, Flow, and common variables
    """
    all_mappings = {}
    all_mappings.update(create_default_dora_variables())
    all_mappings.update(create_default_flow_variables())
    all_mappings.update(create_default_common_variables())

    return VariableMappingCollection(mappings=all_mappings, version="1.0")


def get_variables_by_metric(metric_name: str) -> Dict[str, VariableMapping]:
    """Get variables required for a specific metric.

    Args:
        metric_name: Name of metric ("deployment_frequency", "lead_time", etc.)

    Returns:
        Dictionary of variable mappings needed for that metric
    """
    metric_variable_map = {
        "deployment_frequency": [
            "deployment_event",
            "deployment_timestamp",
            "deployment_successful",
            "project_key",
            "environment",
        ],
        "lead_time_for_changes": [
            "commit_timestamp",
            "deployment_timestamp",
            "project_key",
        ],
        "change_failure_rate": [
            "deployment_event",
            "deployment_timestamp",
            "is_incident",
            "incident_start_timestamp",
            "related_deployment",
            "project_key",
        ],
        "mean_time_to_recovery": [
            "is_incident",
            "incident_start_timestamp",
            "incident_resolved_timestamp",
            "project_key",
            "environment",
        ],
        "flow_velocity": [
            "is_completed",
            "completion_timestamp",
            "work_item_size",
            "work_type_category",
            "project_key",
        ],
        "flow_time": [
            "work_started_timestamp",
            "work_completed_timestamp",
            "is_completed",
            "project_key",
        ],
        "flow_efficiency": ["active_time", "total_time", "is_completed", "project_key"],
        "flow_load": ["is_in_progress", "work_item_size", "project_key"],
        "flow_distribution": [
            "is_completed",
            "work_type_category",
            "completion_timestamp",
            "project_key",
        ],
    }

    collection = create_default_variable_collection()
    variable_names = metric_variable_map.get(metric_name, [])

    result: Dict[str, VariableMapping] = {}
    for name in variable_names:
        mapping = collection.get_mapping(name)
        if mapping is not None:
            result[name] = mapping
    return result


def build_variable_collection_from_profile(
    profile_config: Dict,
) -> VariableMappingCollection:
    """Build variable collection using user's profile configuration.

    Replaces hardcoded status values in DEFAULT_VARIABLE_COLLECTION with
    user-configured statuses from profile.json.

    Args:
        profile_config: Profile.json configuration dict with project_classification section

    Returns:
        VariableMappingCollection with user-configured status values

    Raises:
        ValueError: If required status configuration is missing

    Example:
        >>> profile_config = {
        ...     "project_classification": {
        ...         "completion_statuses": ["Resolved", "Closed"],
        ...         "active_statuses": ["In Progress", "Patch Available"],
        ...         "flow_start_statuses": ["Open"],
        ...         "wip_statuses": ["In Progress", "Patch Available", "Reopened"]
        ...     }
        ... }
        >>> collection = build_variable_collection_from_profile(profile_config)
        >>> # Variable extraction will use "Resolved" instead of hardcoded "Done"
    """
    import logging

    logger = logging.getLogger(__name__)

    # Extract status configurations from profile
    project_classification = profile_config.get("project_classification", {})
    completion_statuses = project_classification.get("completion_statuses", [])
    active_statuses = project_classification.get("active_statuses", [])
    flow_start_statuses = project_classification.get("flow_start_statuses", [])
    wip_statuses = project_classification.get("wip_statuses", [])

    # Warn if configuration is empty (not an error - user may not have configured yet)
    if not completion_statuses:
        logger.warning(
            "No completion_statuses configured in profile. "
            "Please configure via UI: Configure JIRA Mappings → Status tab → Completion Statuses"
        )

    if not active_statuses:
        logger.warning(
            "No active_statuses configured in profile. "
            "Flow Efficiency metric will not calculate. "
            "Please configure via UI: Configure JIRA Mappings → Status tab → Active Statuses"
        )

    if not wip_statuses:
        logger.warning(
            "No wip_statuses configured in profile. "
            "Flow Load metric will not calculate. "
            "Please configure via UI: Configure JIRA Mappings → Status tab → WIP Statuses"
        )

    # Use first configured status for single-value transitions
    primary_completion = completion_statuses[0] if completion_statuses else None
    primary_flow_start = flow_start_statuses[0] if flow_start_statuses else None

    # Start with default collection
    base_collection = create_default_variable_collection()
    variables_dict = dict(base_collection.mappings)

    # Override status-dependent variables with profile configuration

    # 1. Completion check (is_completed)
    if "is_completed" in variables_dict and completion_statuses:
        variables_dict["is_completed"] = VariableMapping(
            variable_name="is_completed",
            variable_type="boolean",
            metric_category="flow",
            description="Whether work item is completed",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="status.name",
                        operator="in",
                        value=completion_statuses,  # USER CONFIGURED
                    ),
                )
            ],
        )

    # 2. Work completed timestamp
    if "work_completed_timestamp" in variables_dict and primary_completion:
        variables_dict["work_completed_timestamp"] = VariableMapping(
            variable_name="work_completed_timestamp",
            variable_type="datetime",
            metric_category="flow",
            description="When work was completed",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={
                            "transition_to": primary_completion
                        },  # USER CONFIGURED
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=FieldValueSource(
                        type="field_value",
                        field="resolutiondate",
                        value_type="datetime",
                    ),
                ),
            ],
        )

    # 3. Work started timestamp
    if "work_started_timestamp" in variables_dict:
        sources = []
        if primary_flow_start:
            sources.append(
                SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={
                            "transition_to": primary_flow_start
                        },  # USER CONFIGURED
                    ),
                )
            )
        # Fallback to created date
        sources.append(
            SourceRule(
                priority=99,
                source=FieldValueSource(
                    type="field_value",
                    field="created",
                    value_type="datetime",
                ),
            )
        )
        variables_dict["work_started_timestamp"] = VariableMapping(
            variable_name="work_started_timestamp",
            variable_type="datetime",
            metric_category="flow",
            description="When work started (moved to active status)",
            required=True,
            sources=sources,
        )

    # 4. Active time (for Flow Efficiency)
    if "active_time" in variables_dict and active_statuses:
        variables_dict["active_time"] = VariableMapping(
            variable_name="active_time",
            variable_type="duration",
            metric_category="flow",
            description="Total time in active work statuses",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=CalculatedSource(
                        type="calculated",
                        calculation="sum_changelog_durations",
                        inputs={
                            "field": "status",
                            "statuses": active_statuses,  # USER CONFIGURED
                        },
                    ),
                )
            ],
        )

    # 5. WIP status check (is_in_progress)
    if "is_in_progress" in variables_dict and wip_statuses:
        variables_dict["is_in_progress"] = VariableMapping(
            variable_name="is_in_progress",
            variable_type="boolean",
            metric_category="flow",
            description="Whether work item is currently in progress",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="status.name",
                        operator="in",
                        value=wip_statuses,  # USER CONFIGURED
                    ),
                )
            ],
        )

    # 6. Completion timestamp (alternative)
    if "completion_timestamp" in variables_dict and primary_completion:
        variables_dict["completion_timestamp"] = VariableMapping(
            variable_name="completion_timestamp",
            variable_type="datetime",
            metric_category="flow",
            description="When work item was completed",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={
                            "transition_to": primary_completion
                        },  # USER CONFIGURED
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=FieldValueSource(
                        type="field_value",
                        field="resolutiondate",
                        value_type="datetime",
                    ),
                ),
            ],
        )

    # 7. Deployment successful (DORA)
    if "deployment_successful" in variables_dict and completion_statuses:
        variables_dict["deployment_successful"] = VariableMapping(
            variable_name="deployment_successful",
            variable_type="boolean",
            metric_category="dora",
            description="Whether deployment was successful",
            required=True,
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(
                        type="field_value",
                        field="deployment_successful",
                        value_type="boolean",
                    ),
                ),
                SourceRule(
                    priority=99,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="status.name",
                        operator="in",
                        value=completion_statuses,  # USER CONFIGURED - assume completion = success
                    ),
                ),
            ],
        )

    # Create new collection with updated variables
    return VariableMappingCollection(mappings=variables_dict)


def build_variable_collection_from_field_mappings(
    profile_config: Dict,
) -> VariableMappingCollection:
    """Build variable collection using detected field mappings from auto-configure.

    This function updates the default variable collection to use custom fields
    detected by auto-configure, preserving fallback logic for undetected fields.

    Args:
        profile_config: Profile.json configuration dict with field_mappings section

    Returns:
        VariableMappingCollection with custom field mappings integrated

    Example:
        >>> profile_config = {
        ...     "field_mappings": {
        ...         "dora": {
        ...             "deployment_date": "customfield_12345",
        ...             "target_environment": "customfield_67890",
        ...             "severity_level": "customfield_11111"
        ...         },
        ...         "flow": {
        ...             "effort_category": "customfield_22222"
        ...         }
        ...     },
        ...     "project_classification": {
        ...         "completion_statuses": ["Done", "Resolved"],
        ...         "flow_start_statuses": ["In Progress"]
        ...     }
        ... }
        >>> collection = build_variable_collection_from_field_mappings(profile_config)
    """
    import logging

    logger = logging.getLogger(__name__)

    # Start with profile-based status configuration
    base_collection = build_variable_collection_from_profile(profile_config)
    variables_dict = dict(base_collection.mappings)

    # Extract field mappings
    field_mappings = profile_config.get("field_mappings", {})
    dora_fields = field_mappings.get("dora", {})
    flow_fields = field_mappings.get("flow", {})

    # Map detected fields to variable names
    # Format: {variable_name: (field_id, value_type)}
    field_variable_map = {}

    # DORA field mappings
    if dora_fields.get("deployment_date"):
        field_variable_map["deployment_timestamp"] = (
            dora_fields["deployment_date"],
            "datetime",
        )
    if dora_fields.get("target_environment"):
        field_variable_map["environment"] = (
            dora_fields["target_environment"],
            "string",
        )
    if dora_fields.get("code_commit_date"):
        field_variable_map["commit_timestamp"] = (
            dora_fields["code_commit_date"],
            "datetime",
        )
    if dora_fields.get("incident_detected_at"):
        field_variable_map["incident_start_timestamp"] = (
            dora_fields["incident_detected_at"],
            "datetime",
        )
    if dora_fields.get("incident_resolved_at"):
        field_variable_map["incident_resolved_timestamp"] = (
            dora_fields["incident_resolved_at"],
            "datetime",
        )
    if dora_fields.get("severity_level"):
        # Note: severity_level is not a direct variable but can be used for filtering
        pass
    if dora_fields.get("change_failure"):
        # Note: change_failure affects deployment_successful variable
        field_variable_map["deployment_successful_field"] = (
            dora_fields["change_failure"],
            "boolean",
        )

    # Flow field mappings
    if flow_fields.get("effort_category"):
        field_variable_map["work_type_category"] = (
            flow_fields["effort_category"],
            "string",
        )
    if flow_fields.get("work_started_date"):
        field_variable_map["work_started_timestamp"] = (
            flow_fields["work_started_date"],
            "datetime",
        )
    if flow_fields.get("work_completed_date"):
        field_variable_map["work_completed_timestamp"] = (
            flow_fields["work_completed_date"],
            "datetime",
        )
    if flow_fields.get("completed_date"):
        field_variable_map["completion_timestamp"] = (
            flow_fields["completed_date"],
            "datetime",
        )

    # Update variable sources with detected custom fields
    for var_name, (field_id, value_type) in field_variable_map.items():
        if var_name not in variables_dict:
            continue

        current_mapping = variables_dict[var_name]

        # Prepend custom field source with priority 1
        # Existing sources get shifted to lower priorities
        updated_sources = [
            SourceRule(
                priority=1,
                source=FieldValueSource(
                    type="field_value",
                    field=field_id,
                    value_type=value_type,
                ),
            )
        ]

        # Add existing sources with incremented priorities
        for existing_rule in current_mapping.sources:
            updated_sources.append(
                SourceRule(
                    priority=existing_rule.priority + 1,
                    source=existing_rule.source,
                    filters=existing_rule.filters,
                )
            )

        # Update the mapping
        variables_dict[var_name] = VariableMapping(
            variable_name=current_mapping.variable_name,
            variable_type=current_mapping.variable_type,
            metric_category=current_mapping.metric_category,
            description=current_mapping.description,
            required=current_mapping.required,
            sources=updated_sources,
            fallback_source=current_mapping.fallback_source,
            category_mapping=current_mapping.category_mapping,
        )

        logger.info(
            f"[VariableMapping] Added custom field '{field_id}' as priority 1 source for variable '{var_name}'"
        )

    return VariableMappingCollection(mappings=variables_dict)


# Export default collection for use in application
DEFAULT_VARIABLE_COLLECTION = create_default_variable_collection()
