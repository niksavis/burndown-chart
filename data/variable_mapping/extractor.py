"""Variable extraction engine for JIRA issues.

This module implements the VariableExtractor class that uses the Pydantic models
to extract variable values from JIRA issues using priority-ordered source rules
with conditional filtering.

Reference: docs/mapping_architecture_proposal.md
"""

from typing import Any, Dict, List, Literal, Optional, Union
from datetime import datetime
import logging

from data.variable_mapping.models import (
    VariableMappingCollection,
    MappingFilter,
    FieldValueSource,
    FieldValueMatchSource,
    ChangelogEventSource,
    ChangelogTimestampSource,
    FixVersionSource,
    CalculatedSource,
)

logger = logging.getLogger(__name__)


class VariableExtractor:
    """Extract variable values from JIRA issues using configured mappings.

    The extractor processes issues through priority-ordered source rules,
    applying conditional filters and returning extracted values with
    metadata about which source was used.

    Example:
        >>> collection = VariableMappingCollection(mappings={...})
        >>> extractor = VariableExtractor(collection)
        >>> result = extractor.extract_variable("deployment_timestamp", issue)
        >>> if result["found"]:
        ...     print(f"Value: {result['value']}, Source: {result['source_priority']}")
    """

    def __init__(self, mapping_collection: VariableMappingCollection):
        """Initialize extractor with variable mapping collection.

        Args:
            mapping_collection: Collection of variable mappings to use
        """
        self.mappings = mapping_collection

    def extract_variable(
        self,
        variable_name: str,
        issue: Dict[str, Any],
        changelog: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Extract a single variable from a JIRA issue.

        Args:
            variable_name: Name of variable to extract
            issue: JIRA issue dict with fields
            changelog: Optional changelog history for the issue

        Returns:
            Dictionary with extraction result:
            {
                "found": bool,
                "value": Any (if found),
                "source_priority": int (if found),
                "source_type": str (if found),
                "error": str (if error occurred)
            }
        """
        mapping = self.mappings.get_mapping(variable_name)
        if not mapping:
            return {
                "found": False,
                "error": f"No mapping configured for variable '{variable_name}'",
            }

        # Try each source rule in priority order
        for rule in sorted(mapping.sources, key=lambda r: r.priority):
            # Check if filters match
            if rule.filters and not self._evaluate_filters(rule.filters, issue):
                continue

            # Try to extract value from this source
            result = self._extract_from_source(rule.source, issue, changelog)

            if result["found"]:
                return {
                    "found": True,
                    "value": result["value"],
                    "source_priority": rule.priority,
                    "source_type": rule.source.type,
                }

        # Try fallback source if configured
        if mapping.fallback_source:
            result = self._extract_from_source(
                mapping.fallback_source.source, issue, changelog
            )
            if result["found"]:
                return {
                    "found": True,
                    "value": result["value"],
                    "source_priority": mapping.fallback_source.priority,
                    "source_type": mapping.fallback_source.source.type,
                    "from_fallback": True,
                }

        return {"found": False}

    def extract_all_variables(
        self,
        issue: Dict[str, Any],
        changelog: Optional[List[Dict[str, Any]]] = None,
        category: Optional[Literal["dora", "flow", "common"]] = None,
    ) -> Dict[str, Any]:
        """Extract all configured variables from a JIRA issue.

        Args:
            issue: JIRA issue dict with fields
            changelog: Optional changelog history for the issue
            category: Optional category filter ("dora", "flow", "common")

        Returns:
            Dictionary mapping variable names to extracted values
        """
        results = {}

        # Get mappings to extract
        if category:
            mappings_dict = self.mappings.get_mappings_by_category(category)
        else:
            mappings_dict = self.mappings.mappings

        for var_name in mappings_dict:
            result = self.extract_variable(var_name, issue, changelog)
            if result["found"]:
                results[var_name] = result["value"]
            elif mappings_dict[var_name].required:
                logger.warning(
                    f"Required variable '{var_name}' could not be extracted from issue {issue.get('key')}"
                )

        return results

    def _evaluate_filters(self, filters: MappingFilter, issue: Dict[str, Any]) -> bool:
        """Evaluate whether issue matches filter conditions.

        Args:
            filters: Filter conditions to check
            issue: JIRA issue to evaluate

        Returns:
            True if issue matches all filter conditions, False otherwise
        """
        fields = issue.get("fields", {})

        # Check project filter
        if filters.project:
            project_key = issue.get("fields", {}).get("project", {}).get("key")
            if project_key not in filters.project:
                return False

        # Check issuetype filter
        if filters.issuetype:
            issuetype_name = fields.get("issuetype", {}).get("name")
            if issuetype_name not in filters.issuetype:
                return False

        # Check environment filter
        if filters.environment_field and filters.environment_value:
            env_value = self._get_field_value(fields, filters.environment_field)
            if env_value != filters.environment_value:
                return False

        # Check custom JQL filter (simplified - would need full JQL parser)
        # For now, we skip custom JQL evaluation
        if filters.custom_jql:
            logger.warning("Custom JQL filters not yet implemented, skipping")

        return True

    def _extract_from_source(
        self,
        source: Union[
            FieldValueSource,
            FieldValueMatchSource,
            ChangelogEventSource,
            ChangelogTimestampSource,
            FixVersionSource,
            CalculatedSource,
        ],
        issue: Dict[str, Any],
        changelog: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Extract value from a specific source type.

        Args:
            source: Source configuration
            issue: JIRA issue
            changelog: Optional changelog history

        Returns:
            {"found": bool, "value": Any (if found)}
        """
        if isinstance(source, FieldValueSource):
            return self._extract_field_value(source, issue)
        elif isinstance(source, FieldValueMatchSource):
            return self._extract_field_value_match(source, issue)
        elif isinstance(source, ChangelogEventSource):
            return self._extract_changelog_event(source, issue, changelog)
        elif isinstance(source, ChangelogTimestampSource):
            return self._extract_changelog_timestamp(source, issue, changelog)
        elif isinstance(source, FixVersionSource):
            return self._extract_fixversion(source, issue)
        elif isinstance(source, CalculatedSource):
            return self._extract_calculated(source, issue, changelog)
        else:
            logger.error(f"Unknown source type: {type(source)}")
            return {"found": False}

    def _extract_field_value(
        self, source: FieldValueSource, issue: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract direct field value from issue.

        Args:
            source: FieldValueSource configuration
            issue: JIRA issue

        Returns:
            {"found": bool, "value": Any (if found)}
        """
        fields = issue.get("fields", {})
        value = self._get_field_value(fields, source.field)

        if value is not None:
            return {"found": True, "value": value}
        return {"found": False}

    def _extract_field_value_match(
        self, source: FieldValueMatchSource, issue: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract boolean based on field value match.

        Args:
            source: FieldValueMatchSource configuration
            issue: JIRA issue

        Returns:
            {"found": bool, "value": bool (if found)}
        """
        fields = issue.get("fields", {})
        field_value = self._get_field_value(fields, source.field)

        if field_value is None:
            return {"found": False}

        # Evaluate operator
        match = False
        if source.operator == "equals":
            match = field_value == source.value
        elif source.operator == "not_equals":
            match = field_value != source.value
        elif source.operator == "in":
            match = (
                field_value in source.value if isinstance(source.value, list) else False
            )
        elif source.operator == "not_in":
            match = (
                field_value not in source.value
                if isinstance(source.value, list)
                else False
            )
        elif source.operator == "contains":
            match = (
                source.value in str(field_value)
                if isinstance(source.value, str)
                else False
            )

        return {"found": True, "value": match}

    def _extract_changelog_event(
        self,
        source: ChangelogEventSource,
        issue: Dict[str, Any],
        changelog: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Extract boolean based on changelog event occurrence.

        Args:
            source: ChangelogEventSource configuration
            issue: JIRA issue
            changelog: Changelog history

        Returns:
            {"found": bool, "value": bool (if found)}
        """
        if not changelog:
            return {"found": False}

        # Search changelog for matching transition
        for history_item in changelog:
            for item in history_item.get("items", []):
                if item.get("field") != source.field:
                    continue

                # Check transition conditions
                transition_to = source.condition.get("transition_to")
                transition_from = source.condition.get("transition_from")

                if transition_to and item.get("toString") == transition_to:
                    if transition_from:
                        if item.get("fromString") == transition_from:
                            return {"found": True, "value": True}
                    else:
                        return {"found": True, "value": True}

        return {"found": True, "value": False}

    def _extract_changelog_timestamp(
        self,
        source: ChangelogTimestampSource,
        issue: Dict[str, Any],
        changelog: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Extract timestamp when changelog event occurred.

        Args:
            source: ChangelogTimestampSource configuration
            issue: JIRA issue
            changelog: Changelog history

        Returns:
            {"found": bool, "value": str (ISO timestamp if found)}
        """
        if not changelog:
            return {"found": False}

        # Search changelog for matching transition
        for history_item in changelog:
            for item in history_item.get("items", []):
                if item.get("field") != source.field:
                    continue

                # Check transition conditions
                transition_to = source.condition.get("transition_to")
                transition_from = source.condition.get("transition_from")

                match = False
                if transition_to:
                    # Support both single value and list of values
                    to_string = item.get("toString")
                    if isinstance(transition_to, list):
                        # Check if transitioned to any status in the list
                        if to_string in transition_to:
                            if transition_from:
                                match = item.get("fromString") == transition_from
                            else:
                                match = True
                    else:
                        # Single value check (backward compatible)
                        if to_string == transition_to:
                            if transition_from:
                                match = item.get("fromString") == transition_from
                            else:
                                match = True

                if match:
                    timestamp = history_item.get("created")
                    if timestamp:
                        return {"found": True, "value": timestamp}

        return {"found": False}

    def _extract_fixversion(
        self, source: FixVersionSource, issue: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract release date from fixVersions.

        Args:
            source: FixVersionSource configuration
            issue: JIRA issue

        Returns:
            {"found": bool, "value": str (ISO date if found) or list of dates}
        """
        fields = issue.get("fields", {})
        fix_versions = fields.get("fixVersions", [])

        if not fix_versions:
            return {"found": False}

        # Extract release dates
        dates = []
        for version in fix_versions:
            release_date = version.get("releaseDate")
            if release_date:
                dates.append(release_date)

        if not dates:
            return {"found": False}

        # Apply selector
        if source.selector == "first":
            return {"found": True, "value": dates[0]}
        elif source.selector == "last":
            return {"found": True, "value": dates[-1]}
        elif source.selector == "all":
            return {"found": True, "value": dates}

        return {"found": False}

    def _extract_calculated(
        self,
        source: CalculatedSource,
        issue: Dict[str, Any],
        changelog: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Extract calculated/derived value.

        Args:
            source: CalculatedSource configuration
            issue: JIRA issue
            changelog: Changelog history

        Returns:
            {"found": bool, "value": Any (if found)}
        """
        # Implement specific calculations based on calculation type
        if source.calculation == "sum_changelog_durations":
            return self._calculate_changelog_duration_sum(source, changelog)
        elif source.calculation == "count_transitions":
            return self._calculate_transition_count(source, changelog)
        elif source.calculation == "timestamp_diff":
            return self._calculate_timestamp_diff(source, issue, changelog)
        else:
            logger.warning(f"Unknown calculation type: {source.calculation}")
            return {"found": False}

    def _calculate_changelog_duration_sum(
        self, source: CalculatedSource, changelog: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Calculate total time spent in specific statuses from changelog.

        Args:
            source: CalculatedSource with inputs
            changelog: Changelog history

        Returns:
            {"found": bool, "value": int (duration in seconds if found)}
        """
        if not changelog:
            return {"found": False}

        field = source.inputs.get("field")
        statuses = source.inputs.get("statuses", [])

        if not field or not statuses:
            return {"found": False}

        total_duration = 0
        current_status = None
        status_start_time = None

        for history_item in sorted(changelog, key=lambda x: x.get("created", "")):
            for item in history_item.get("items", []):
                if item.get("field") == field:
                    timestamp = history_item.get("created")

                    # Calculate duration in previous status
                    if current_status in statuses and status_start_time and timestamp:
                        duration = self._calculate_time_diff(
                            status_start_time, timestamp
                        )
                        if duration > 0:
                            total_duration += duration

                    # Update current status
                    current_status = item.get("toString")
                    status_start_time = timestamp

        return {"found": True, "value": total_duration}

    def _calculate_transition_count(
        self, source: CalculatedSource, changelog: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Count number of transitions for a field.

        Args:
            source: CalculatedSource with inputs
            changelog: Changelog history

        Returns:
            {"found": bool, "value": int (count if found)}
        """
        if not changelog:
            return {"found": True, "value": 0}

        field = source.inputs.get("field")
        count = 0

        for history_item in changelog:
            for item in history_item.get("items", []):
                if item.get("field") == field:
                    count += 1

        return {"found": True, "value": count}

    def _calculate_timestamp_diff(
        self,
        source: CalculatedSource,
        issue: Dict[str, Any],
        changelog: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Calculate difference between two timestamps.

        The inputs can be either:
        1. Variable names (e.g., "work_started_timestamp") - will be extracted recursively
        2. Field paths (e.g., "created", "resolutiondate") - looked up directly

        Args:
            source: CalculatedSource with inputs
            issue: JIRA issue
            changelog: Optional changelog history for recursive extraction

        Returns:
            {"found": bool, "value": int (difference in seconds if found)}
        """
        start_input = source.inputs.get("start")
        end_input = source.inputs.get("end")

        if not start_input or not end_input:
            return {"found": False}

        # Try to extract as variables first (recursive extraction)
        # Variables are named things like "work_started_timestamp"
        start_value = None
        end_value = None

        # Check if start_input is a variable name we can extract
        if start_input in self.mappings.mappings:
            start_result = self.extract_variable(start_input, issue, changelog)
            if start_result.get("found"):
                start_value = start_result.get("value")
        else:
            # Fallback: treat as field path
            start_value = self._get_field_value(issue.get("fields", {}), start_input)

        # Check if end_input is a variable name we can extract
        if end_input in self.mappings.mappings:
            end_result = self.extract_variable(end_input, issue, changelog)
            if end_result.get("found"):
                end_value = end_result.get("value")
        else:
            # Fallback: treat as field path
            end_value = self._get_field_value(issue.get("fields", {}), end_input)

        if not start_value or not end_value:
            return {"found": False}

        diff = self._calculate_time_diff(start_value, end_value)
        return {"found": True, "value": diff}

    def _get_field_value(self, fields: Dict[str, Any], field_path: str) -> Any:
        """Get nested field value using dot notation.

        Args:
            fields: JIRA issue fields dict
            field_path: Dot-separated field path (e.g., "status.name")

        Returns:
            Field value or None if not found
        """
        parts = field_path.split(".")
        current = fields

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return None
            else:
                return None

        return current

    def _calculate_time_diff(self, start: str, end: str) -> int:
        """Calculate time difference between two ISO timestamps.

        Args:
            start: Start timestamp (ISO format)
            end: End timestamp (ISO format)

        Returns:
            Difference in seconds, or 0 if parsing fails
        """
        try:
            # Parse timestamps (handle JIRA's ISO format)
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            diff = (end_dt - start_dt).total_seconds()
            return int(diff)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse timestamps: {e}")
            return 0
