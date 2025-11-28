"""Pydantic data models for variable mapping system.

This module defines the data structures for the rule-based variable mapping
system, enabling flexible JIRA field extraction with multiple sources,
conditional filters, and priority ordering.

Reference: docs/mapping_architecture_proposal.md
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


class FieldValueSource(BaseModel):
    """Extract direct field value from JIRA issue.

    Example:
        >>> source = FieldValueSource(
        ...     type="field_value",
        ...     field="customfield_10100",
        ...     value_type="datetime"
        ... )
    """

    type: Literal["field_value"]
    field: str = Field(
        ..., description="JIRA field ID (e.g., 'customfield_10100' or 'status')"
    )
    value_type: Literal["datetime", "string", "number", "boolean"] = Field(
        default="string", description="Expected data type of field value"
    )


class FieldValueMatchSource(BaseModel):
    """Check if field value matches condition (returns boolean).

    Example:
        >>> source = FieldValueMatchSource(
        ...     type="field_value_match",
        ...     field="status.name",
        ...     operator="equals",
        ...     value="Deployed"
        ... )
    """

    type: Literal["field_value_match"]
    field: str = Field(
        ..., description="JIRA field path (supports nested like 'status.name')"
    )
    operator: Literal["equals", "not_equals", "in", "not_in", "contains"] = Field(
        ..., description="Comparison operator"
    )
    value: Union[str, int, float, bool, List[str]] = Field(
        ..., description="Value or list of values to match against"
    )


class ChangelogEventSource(BaseModel):
    """Detect if changelog event occurred (returns boolean).

    Example:
        >>> source = ChangelogEventSource(
        ...     type="changelog_event",
        ...     field="status",
        ...     condition={"transition_to": "Deployed"}
        ... )
    """

    type: Literal["changelog_event"]
    field: str = Field(..., description="Field that transitioned")
    condition: Dict[str, str] = Field(
        ..., description="Transition conditions (e.g., {'transition_to': 'Done'})"
    )


class ChangelogTimestampSource(BaseModel):
    """Extract timestamp when changelog event occurred.

    Example:
        >>> source = ChangelogTimestampSource(
        ...     type="changelog_timestamp",
        ...     field="status",
        ...     condition={"transition_to": "Deployed to Production"}
        ... )
        >>> # Or with multiple target statuses
        >>> source = ChangelogTimestampSource(
        ...     type="changelog_timestamp",
        ...     field="status",
        ...     condition={"transition_to": ["Done", "Resolved", "Closed"]}
        ... )
    """

    type: Literal["changelog_timestamp"]
    field: str = Field(..., description="Field that transitioned")
    condition: Dict[str, Union[str, List[str]]] = Field(
        ..., description="Transition conditions to match"
    )


class FixVersionSource(BaseModel):
    """Extract release date from fixVersions array.

    Example:
        >>> source = FixVersionSource(
        ...     type="fixversion_releasedate",
        ...     field="fixVersions",
        ...     selector="first"
        ... )
    """

    type: Literal["fixversion_releasedate"]
    field: Literal["fixVersions"] = Field(
        default="fixVersions", description="Must be 'fixVersions'"
    )
    selector: Literal["first", "last", "all"] = Field(
        default="first", description="Which version date to extract"
    )


class CalculatedSource(BaseModel):
    """Calculate derived value from other sources.

    Example:
        >>> source = CalculatedSource(
        ...     type="calculated",
        ...     calculation="sum_changelog_durations",
        ...     inputs={"field": "status", "statuses": ["In Progress", "In Review"]},
        ...     parameters={}
        ... )
    """

    type: Literal["calculated"]
    calculation: str = Field(
        ...,
        description="Calculation type (e.g., 'sum_changelog_durations', 'timestamp_diff')",
    )
    inputs: Dict[str, Any] = Field(..., description="Input parameters for calculation")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Additional calculation parameters"
    )


# Union type for all source types
SourceType = Union[
    FieldValueSource,
    FieldValueMatchSource,
    ChangelogEventSource,
    ChangelogTimestampSource,
    FixVersionSource,
    CalculatedSource,
]


class MappingFilter(BaseModel):
    """Conditional filters for when mapping applies.

    Example:
        >>> filter = MappingFilter(
        ...     project=["DEVOPS", "BACKEND"],
        ...     issuetype=["Deployment"],
        ...     environment_field="customfield_10200",
        ...     environment_value="Production"
        ... )
    """

    project: Optional[List[str]] = Field(
        default=None, description="Filter by project keys"
    )
    issuetype: Optional[List[str]] = Field(
        default=None, description="Filter by issue type names"
    )
    environment_field: Optional[str] = Field(
        default=None, description="JIRA field containing environment value"
    )
    environment_value: Optional[str] = Field(
        default=None, description="Required environment value (e.g., 'Production')"
    )
    custom_jql: Optional[str] = Field(
        default=None, description="Custom JQL filter expression"
    )


class SourceRule(BaseModel):
    """Single source with priority ordering.

    Example:
        >>> rule = SourceRule(
        ...     priority=1,
        ...     source=FieldValueSource(
        ...         type="field_value",
        ...         field="customfield_10100",
        ...         value_type="datetime"
        ...     ),
        ...     filters=MappingFilter(project=["DEVOPS"])
        ... )
    """

    priority: int = Field(..., description="Lower number = higher priority", ge=1)
    source: SourceType = Field(..., description="Source configuration")
    filters: Optional[MappingFilter] = Field(
        default=None, description="Conditional filters for this source"
    )


class VariableMapping(BaseModel):
    """Complete variable mapping definition.

    Example:
        >>> mapping = VariableMapping(
        ...     variable_name="deployment_timestamp",
        ...     variable_type="datetime",
        ...     metric_category="dora",
        ...     description="When deployment occurred",
        ...     required=True,
        ...     sources=[
        ...         SourceRule(
        ...             priority=1,
        ...             source=FieldValueSource(
        ...                 type="field_value",
        ...                 field="customfield_10100",
        ...                 value_type="datetime"
        ...             )
        ...         )
        ...     ]
        ... )
    """

    variable_name: str = Field(..., description="Unique variable identifier")
    variable_type: Literal[
        "datetime", "boolean", "number", "duration", "category", "count"
    ] = Field(..., description="Expected data type of extracted value")
    metric_category: Literal["dora", "flow", "common"] = Field(
        ..., description="Which metrics use this variable"
    )
    description: str = Field(
        ..., description="Human-readable explanation of variable purpose"
    )
    required: bool = Field(
        default=True,
        description="Whether this variable is required for metric calculation",
    )
    sources: List[SourceRule] = Field(
        ..., description="Priority-ordered list of source rules", min_length=1
    )
    fallback_source: Optional[SourceRule] = Field(
        default=None, description="Fallback source if all primary sources fail"
    )
    validation_rules: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional validation rules"
    )
    category_mapping: Optional[Dict[str, List[str]]] = Field(
        default=None, description="Category mapping for work type categorization"
    )

    @field_validator("sources")
    @classmethod
    def validate_unique_priorities(cls, v: List[SourceRule]) -> List[SourceRule]:
        """Ensure all sources have unique priorities."""
        priorities = [rule.priority for rule in v]
        if len(priorities) != len(set(priorities)):
            raise ValueError("All source rules must have unique priorities")
        return v


class VariableMappingCollection(BaseModel):
    """Collection of variable mappings for a profile.

    This is the root structure stored in app_settings.json.

    Example:
        >>> collection = VariableMappingCollection(
        ...     mappings={
        ...         "deployment_timestamp": VariableMapping(...),
        ...         "work_type_category": VariableMapping(...)
        ...     }
        ... )
    """

    mappings: Dict[str, VariableMapping] = Field(
        default_factory=dict,
        description="Dictionary of variable name -> mapping configuration",
    )
    version: str = Field(
        default="1.0", description="Schema version for future compatibility"
    )

    def get_mapping(self, variable_name: str) -> Optional[VariableMapping]:
        """Get mapping by variable name."""
        return self.mappings.get(variable_name)

    def add_mapping(self, mapping: VariableMapping) -> None:
        """Add or update variable mapping."""
        self.mappings[mapping.variable_name] = mapping

    def remove_mapping(self, variable_name: str) -> bool:
        """Remove variable mapping. Returns True if mapping existed."""
        if variable_name in self.mappings:
            del self.mappings[variable_name]
            return True
        return False

    def get_mappings_by_category(
        self, category: Literal["dora", "flow", "common"]
    ) -> Dict[str, VariableMapping]:
        """Get all mappings for a specific metric category."""
        return {
            name: mapping
            for name, mapping in self.mappings.items()
            if mapping.metric_category == category
        }

    def get_required_mappings(self) -> Dict[str, VariableMapping]:
        """Get all required variable mappings."""
        return {
            name: mapping for name, mapping in self.mappings.items() if mapping.required
        }
