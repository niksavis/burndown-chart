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


# Export default collection for use in application
DEFAULT_VARIABLE_COLLECTION = create_default_variable_collection()
