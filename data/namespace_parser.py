"""Namespace syntax parser for JIRA field mapping.

This module parses namespace paths (e.g., "DevOps.customfield_10100.name") and
translates them to SourceRule objects for the variable mapping system.

Supported syntax: [Project.]Field[.Property][:ChangelogValue][.Extractor]

Examples:
    - "*.created" → Creation date from any project
    - "DevOps.status.name" → Status name from DevOps project
    - "*.Status:Deployed.DateTime" → When status changed to Deployed
    - "DevOps|Platform.customfield_10100" → Field from multiple projects

Reference: specs/namespace-syntax-analysis.md
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Union

from data.variable_mapping.models import (
    ChangelogEventSource,
    ChangelogTimestampSource,
    FieldValueSource,
    MappingFilter,
    SourceRule,
)

logger = logging.getLogger(__name__)


@dataclass
class ParsedNamespace:
    """Parsed namespace path components."""

    project_filter: List[str]  # List of project keys or ["*"]
    field_name: str  # JIRA field ID (e.g., "customfield_10100", "status")
    property_path: Optional[str] = None  # Nested property (e.g., "name", "id")
    changelog_value: Optional[str] = None  # Changelog transition value
    extractor: Optional[str] = None  # Extractor type (DateTime, Occurred, etc.)
    value_type: Literal["datetime", "string", "number", "boolean"] = "string"

    def __repr__(self) -> str:
        parts = [f"{'/'.join(self.project_filter)}.{self.field_name}"]
        if self.property_path:
            parts.append(f".{self.property_path}")
        if self.changelog_value:
            parts.append(f":{self.changelog_value}")
        if self.extractor:
            parts.append(f".{self.extractor}")
        return "".join(parts)


class NamespaceParseError(Exception):
    """Exception raised when namespace syntax is invalid."""

    pass


class NamespaceParser:
    """Parser for namespace syntax to SourceRule objects."""

    # Regex patterns for parsing
    PROJECT_KEY_PATTERN = (
        r"[A-Z][A-Za-z0-9_]*"  # Start with uppercase, allow mixed case
    )
    FIELD_NAME_PATTERN = r"[a-zA-Z_][a-zA-Z0-9_]*"
    CUSTOM_FIELD_PATTERN = r"customfield_\d+"
    PROPERTY_PATTERN = r"[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)*"

    # Full namespace regex - Updated to handle mixed-case project keys
    # Project keys: Start with UPPERCASE, can contain mixed case (DevOps, Platform)
    # Disambiguation: If segment before dot starts with uppercase → project key
    #                 If segment starts with lowercase → field name
    NAMESPACE_REGEX = re.compile(
        r"^"
        # Project filter (optional): starts with uppercase or *, pipe-separated
        r"(?:(?P<project>(?:[A-Z][A-Za-z0-9_]*|\*)(?:\|(?:[A-Z][A-Za-z0-9_]*|\*))*)\.)?"
        # Field name: customfield_NNNNN or standard field name (can start lowercase)
        r"(?P<field>(?:customfield_\d+|[a-zA-Z_][a-zA-Z0-9_]*))"
        # Property path (optional): dot-separated nested properties
        r"(?:\.(?P<property>[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)*))?"
        # Changelog value (optional): colon followed by status/value name
        r"(?::(?P<changelog>[^.]+))?"
        # Extractor (optional): DateTime, Occurred, or Duration
        r"(?:\.(?P<extractor>DateTime|Occurred|Duration))?"
        r"$"
    )

    # Standard JIRA fields that are datetime type
    DATETIME_FIELDS = {
        "created",
        "updated",
        "resolutiondate",
        "duedate",
        "lastViewed",
        "statuscategorychangedate",
    }

    # Standard JIRA fields that are number type
    NUMBER_FIELDS = {
        "timeestimate",
        "timeoriginalestimate",
        "timespent",
        "aggregatetimeestimate",
    }

    # Standard JIRA object fields with common properties
    OBJECT_FIELDS = {
        "status": ["name", "id", "statusCategory"],
        "priority": ["name", "id"],
        "issuetype": ["name", "id"],
        "project": ["key", "name", "id"],
        "assignee": ["displayName", "emailAddress", "accountId"],
        "reporter": ["displayName", "emailAddress", "accountId"],
        "creator": ["displayName", "emailAddress", "accountId"],
        "resolution": ["name", "id"],
    }

    # Array fields with common properties
    ARRAY_FIELDS = {
        "fixVersions": ["name", "releaseDate", "released", "id"],
        "components": ["name", "id", "description"],
        "labels": [],  # Array of strings, no properties
    }

    def parse(self, namespace_path: str) -> ParsedNamespace:
        """Parse namespace path into components.

        Args:
            namespace_path: Namespace syntax string

        Returns:
            ParsedNamespace with extracted components

        Raises:
            NamespaceParseError: If syntax is invalid

        Examples:
            >>> parser = NamespaceParser()
            >>> parsed = parser.parse("*.created")
            >>> parsed.field_name
            'created'
            >>> parsed = parser.parse("DevOps.status.name")
            >>> parsed.project_filter
            ['DevOps']
            >>> parsed.field_name
            'status'
            >>> parsed.property_path
            'name'
        """
        if not namespace_path or not namespace_path.strip():
            raise NamespaceParseError("Namespace path cannot be empty")

        namespace_path = namespace_path.strip()

        # Pre-process to detect project prefix disambiguation
        # If first segment before dot is ALL CAPS or contains "|", treat as project prefix
        preprocessed_path = self._preprocess_project_prefix(namespace_path)

        match = self.NAMESPACE_REGEX.match(preprocessed_path)
        if not match:
            raise NamespaceParseError(
                f"Invalid namespace syntax: {namespace_path}. "
                f"Expected format: [Project.]Field[.Property][:ChangelogValue][.Extractor]"
            )

        # Extract matched groups
        project_str = match.group("project")
        field_name = match.group("field")
        property_path = match.group("property")
        changelog_value = match.group("changelog")
        extractor = match.group("extractor")

        # Parse project filter
        if project_str:
            # Split by pipe for multi-project
            project_filter = [p.strip() for p in project_str.split("|")]
        else:
            # No project specified means any project
            project_filter = ["*"]

        # Determine value type
        value_type = self._infer_value_type(
            field_name, property_path, changelog_value, extractor
        )

        return ParsedNamespace(
            project_filter=project_filter,
            field_name=field_name,
            property_path=property_path,
            changelog_value=changelog_value,
            extractor=extractor,
            value_type=value_type,
        )

    def _preprocess_project_prefix(self, namespace_path: str) -> str:
        """Detect and normalize project prefix in namespace path.

        Strategy: If the first segment (before first dot) is ALL UPPERCASE or contains pipe,
        treat it as a project filter and ensure it ends with a dot.

        Args:
            namespace_path: Original namespace path

        Returns:
            Preprocessed path with explicit project delimiter if needed

        Examples:
            "DevOps.customfield_10100" → "DevOps.customfield_10100" (already has dot)
            "status.name" → "status.name" (lowercase, not a project)
            "DevOps|Platform.field" → "DevOps|Platform.field" (pipe indicates projects)
            "created" → "created" (no dot, lowercase)
            "DEVOPS" → "DEVOPS" (no dot, but ALL CAPS - ambiguous, leave as-is)
        """
        # Check if path contains a dot
        if "." not in namespace_path:
            # No dot means it's just a field name (e.g., "created", "status")
            return namespace_path

        # Split by first dot to get potential project prefix
        first_segment = namespace_path.split(".", 1)[0]

        # Check if first segment looks like a project key
        # Project indicators: ALL UPPERCASE or contains pipe (multi-project)
        is_project_like = (
            first_segment.isupper()  # ALL CAPS like "DEVOPS", "PLATFORM"
            or "|" in first_segment  # Multi-project like "DevOps|Platform"
            or first_segment == "*"  # Wildcard
        )

        if is_project_like:
            # First segment looks like a project, regex will handle it correctly
            return namespace_path
        else:
            # First segment is lowercase/mixed case, not a project prefix
            # This is a field name like "status.name" or "customfield_10100.DateTime"
            return namespace_path

    def _infer_value_type(
        self,
        field_name: str,
        property_path: Optional[str],
        changelog_value: Optional[str],
        extractor: Optional[str],
    ) -> Literal["datetime", "string", "number", "boolean"]:
        """Infer value type from field name and context.

        Args:
            field_name: JIRA field name
            property_path: Property path (e.g., "name")
            changelog_value: Changelog transition value
            extractor: Extractor type

        Returns:
            Inferred value type
        """
        # Changelog extractors have specific types
        if extractor == "DateTime":
            return "datetime"
        elif extractor in ("Occurred", "Duration"):
            return "boolean" if extractor == "Occurred" else "number"

        # Standard datetime fields
        if field_name in self.DATETIME_FIELDS:
            return "datetime"

        # Standard number fields
        if field_name in self.NUMBER_FIELDS:
            return "number"

        # Property path determines type for object fields
        if property_path:
            # ID fields are typically numbers (but stored as strings in JIRA)
            if property_path.endswith(".id") or property_path == "id":
                return "string"  # JIRA IDs are strings
            # Release date is datetime
            if property_path == "releaseDate":
                return "datetime"
            # Released is boolean
            if property_path == "released":
                return "boolean"
            # Default for properties is string
            return "string"

        # Custom fields default to string (caller can override if needed)
        return "string"

    def translate_to_source_rule(
        self, parsed: ParsedNamespace, priority: int = 1
    ) -> SourceRule:
        """Translate parsed namespace to SourceRule object.

        Args:
            parsed: Parsed namespace components
            priority: Priority for this source rule (default: 1)

        Returns:
            SourceRule configured with appropriate source type

        Examples:
            >>> parser = NamespaceParser()
            >>> parsed = parser.parse("*.created")
            >>> rule = parser.translate_to_source_rule(parsed)
            >>> rule.source.type
            'field_value'
            >>> rule.source.field
            'created'
        """
        # Create project filter if not wildcard
        filters = None
        if parsed.project_filter != ["*"]:
            filters = MappingFilter(project=parsed.project_filter)

        # Build field path (field.property)
        field_path = parsed.field_name
        if parsed.property_path:
            field_path = f"{field_path}.{parsed.property_path}"

        # Determine source type
        if parsed.changelog_value:
            # Changelog-based source
            if parsed.extractor == "DateTime":
                # ChangelogTimestampSource
                source = ChangelogTimestampSource(
                    type="changelog_timestamp",
                    field=parsed.field_name,
                    condition={"transition_to": parsed.changelog_value},
                )
            elif parsed.extractor == "Occurred":
                # ChangelogEventSource
                source = ChangelogEventSource(
                    type="changelog_event",
                    field=parsed.field_name,
                    condition={"transition_to": parsed.changelog_value},
                )
            else:
                # Duration not yet implemented - fallback to event
                logger.warning(
                    f"Duration extractor not yet implemented for {parsed}, "
                    f"using event detection"
                )
                source = ChangelogEventSource(
                    type="changelog_event",
                    field=parsed.field_name,
                    condition={"transition_to": parsed.changelog_value},
                )
        else:
            # Standard field value source
            source = FieldValueSource(
                type="field_value",
                field=field_path,
                value_type=parsed.value_type,
            )

        return SourceRule(priority=priority, source=source, filters=filters)

    def translate_multiple(self, namespace_paths: List[str]) -> List[SourceRule]:
        """Translate multiple namespace paths to prioritized source rules.

        Args:
            namespace_paths: List of namespace paths in priority order

        Returns:
            List of SourceRule objects with sequential priorities

        Examples:
            >>> parser = NamespaceParser()
            >>> rules = parser.translate_multiple([
            ...     "DevOps.customfield_10100",
            ...     "*.resolutiondate"
            ... ])
            >>> len(rules)
            2
            >>> rules[0].priority
            1
            >>> rules[1].priority
            2
        """
        rules = []
        for i, path in enumerate(namespace_paths, start=1):
            try:
                parsed = self.parse(path)
                rule = self.translate_to_source_rule(parsed, priority=i)
                rules.append(rule)
            except NamespaceParseError as e:
                logger.error(f"Failed to parse namespace path '{path}': {e}")
                # Skip invalid paths
                continue

        return rules


# Convenience functions for common use cases


def parse_namespace(namespace_path: str) -> ParsedNamespace:
    """Parse namespace path (convenience function).

    Args:
        namespace_path: Namespace syntax string

    Returns:
        ParsedNamespace with extracted components

    Raises:
        NamespaceParseError: If syntax is invalid
    """
    parser = NamespaceParser()
    return parser.parse(namespace_path)


def namespace_to_source_rule(namespace_path: str, priority: int = 1) -> SourceRule:
    """Convert namespace path to SourceRule (convenience function).

    Args:
        namespace_path: Namespace syntax string
        priority: Priority for this source rule

    Returns:
        SourceRule configured with appropriate source type

    Raises:
        NamespaceParseError: If syntax is invalid
    """
    parser = NamespaceParser()
    parsed = parser.parse(namespace_path)
    return parser.translate_to_source_rule(parsed, priority)


def validate_namespace_syntax(namespace_path: str) -> Dict[str, Union[bool, str]]:
    """Validate namespace syntax without parsing.

    Args:
        namespace_path: Namespace syntax string

    Returns:
        Dict with 'valid' (bool) and 'error_message' (str) keys

    Examples:
        >>> result = validate_namespace_syntax("*.created")
        >>> result['valid']
        True
        >>> result = validate_namespace_syntax("invalid..path")
        >>> result['valid']
        False
    """
    parser = NamespaceParser()
    try:
        parser.parse(namespace_path)
        return {"valid": True, "error_message": ""}
    except NamespaceParseError as e:
        return {"valid": False, "error_message": str(e)}
