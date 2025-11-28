"""Autocomplete provider for namespace syntax.

This module provides context-aware autocomplete suggestions for namespace paths
using JIRA metadata fetched from the configured JIRA instance.

Reference: specs/namespace-syntax-analysis.md - Intellisense/Autocomplete Support
"""

import logging
from typing import Dict, List, Optional

from data.jira_metadata import JiraMetadataFetcher

logger = logging.getLogger(__name__)


class NamespaceAutocompleteProvider:
    """Provides autocomplete suggestions for namespace syntax based on JIRA metadata."""

    def __init__(self, metadata_fetcher: JiraMetadataFetcher):
        """Initialize autocomplete provider.

        Args:
            metadata_fetcher: JiraMetadataFetcher instance for retrieving JIRA metadata
        """
        self.metadata = metadata_fetcher

    def get_suggestions(
        self, partial_path: str, cursor_position: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Get autocomplete suggestions for partial namespace path.

        Args:
            partial_path: User's partial input (e.g., "DevOps.cust")
            cursor_position: Position of cursor in string (default: end of string)

        Returns:
            List of suggestion dicts with 'label', 'value', 'description'

        Examples:
            >>> provider = NamespaceAutocompleteProvider(metadata)
            >>> suggestions = provider.get_suggestions("Dev")
            >>> suggestions
            [
                {'label': 'DevOps - DevOps Team', 'value': 'DevOps', 'description': 'DevOps Team'},
                {'label': 'Development - Development', 'value': 'Development', 'description': 'Development'}
            ]
        """
        if cursor_position is None:
            cursor_position = len(partial_path)

        # Work with the partial path up to cursor
        working_path = partial_path[:cursor_position].strip()

        if not working_path:
            # Empty input - suggest projects and wildcard
            return self._suggest_projects("")

        # Parse partial path to determine what to suggest
        parts = working_path.split(".")

        if len(parts) == 1:
            # Suggesting project or wildcard
            return self._suggest_projects(parts[0])
        elif len(parts) == 2:
            # Suggesting field name
            project_filter = parts[0]
            field_prefix = parts[1]
            return self._suggest_fields(project_filter, field_prefix)
        elif ":" in parts[-1]:
            # Suggesting changelog value
            return self._suggest_changelog_values(working_path)
        else:
            # Suggesting property path
            return self._suggest_properties(working_path)

    def _suggest_projects(self, prefix: str) -> List[Dict[str, str]]:
        """Suggest project keys matching prefix.

        Args:
            prefix: Project key prefix to match

        Returns:
            List of project suggestions
        """
        suggestions = []

        # Always include wildcard as first option
        if prefix == "" or "*".startswith(prefix.lower()):
            suggestions.append(
                {
                    "label": "* (All Projects)",
                    "value": "*.",
                    "description": "Match issues from any project",
                }
            )

        # Fetch projects from JIRA
        try:
            projects = self.metadata.fetch_projects()

            # Add matching projects
            for project in projects:
                key = project.get("key", "")
                name = project.get("name", key)

                if key.upper().startswith(prefix.upper()):
                    suggestions.append(
                        {
                            "label": f"{key} - {name}",
                            "value": f"{key}.",
                            "description": name,
                        }
                    )

            # Limit to 50 results
            return suggestions[:50]

        except Exception as e:
            logger.error(f"Failed to fetch projects for autocomplete: {e}")
            # Return wildcard only if project fetch fails
            return suggestions[:1] if suggestions else []

    def _suggest_fields(
        self, project_filter: str, field_prefix: str
    ) -> List[Dict[str, str]]:
        """Suggest field names matching prefix.

        Args:
            project_filter: Project filter (e.g., "DevOps", "*")
            field_prefix: Field name prefix to match

        Returns:
            List of field suggestions
        """
        suggestions = []

        try:
            fields = self.metadata.fetch_fields()

            for field in fields:
                field_id = field.get("id", "")
                field_name = field.get("name", field_id)
                field_type = field.get("schema", {}).get("type", "unknown")

                # Match on field ID or field name
                if field_id.lower().startswith(field_prefix.lower()) or (
                    field_name and field_name.lower().startswith(field_prefix.lower())
                ):
                    label = field_id
                    if field_name and field_name != field_id:
                        label = f"{field_id} ({field_name})"

                    suggestions.append(
                        {
                            "label": label,
                            "value": f"{project_filter}.{field_id}",
                            "description": f"Type: {field_type}",
                        }
                    )

            # Limit to 50 results
            return suggestions[:50]

        except Exception as e:
            logger.error(f"Failed to fetch fields for autocomplete: {e}")
            return []

    def _suggest_changelog_values(self, partial_path: str) -> List[Dict[str, str]]:
        """Suggest changelog transition values.

        Args:
            partial_path: Partial path with changelog syntax (e.g., "*.Status:Dep")

        Returns:
            List of changelog value suggestions
        """
        suggestions = []

        # Extract field name and value prefix from path
        parts = partial_path.split(":")
        if len(parts) < 2:
            return []

        field_path = parts[0]
        value_prefix = parts[1].split(".")[0] if "." in parts[1] else parts[1]

        # Determine field name (e.g., "status" from "*.Status")
        field_name = field_path.split(".")[-1].lower()

        try:
            # Status field - fetch all statuses
            if field_name in ("status", "status.name"):
                statuses = self.metadata.fetch_statuses()

                for status in statuses:
                    status_name = status.get("name", "")
                    if status_name.lower().startswith(value_prefix.lower()):
                        suggestions.append(
                            {
                                "label": f"{field_path}:{status_name}.DateTime",
                                "value": f"{field_path}:{status_name}",
                                "description": f"When status changed to {status_name}",
                            }
                        )

                return suggestions[:50]

            # For other fields, suggest extractor suffixes if prefix matches
            if value_prefix == "" or "DateTime".startswith(value_prefix):
                suggestions.append(
                    {
                        "label": f"{field_path}:{value_prefix}.DateTime",
                        "value": f"{field_path}:{value_prefix}.DateTime",
                        "description": "Timestamp when change occurred",
                    }
                )
            if value_prefix == "" or "Occurred".startswith(value_prefix):
                suggestions.append(
                    {
                        "label": f"{field_path}:{value_prefix}.Occurred",
                        "value": f"{field_path}:{value_prefix}.Occurred",
                        "description": "Boolean: did change occur?",
                    }
                )

            return suggestions

        except Exception as e:
            logger.error(f"Failed to fetch changelog values for autocomplete: {e}")
            return []

    def _suggest_properties(self, partial_path: str) -> List[Dict[str, str]]:
        """Suggest property paths for complex objects.

        Args:
            partial_path: Partial path with field (e.g., "*.status.nam")

        Returns:
            List of property suggestions
        """
        # Common property suggestions based on field type
        common_properties = {
            "status": ["name", "id", "statusCategory.key", "statusCategory.name"],
            "priority": ["name", "id"],
            "issuetype": ["name", "id"],
            "project": ["key", "name", "id"],
            "assignee": ["displayName", "emailAddress", "accountId"],
            "reporter": ["displayName", "emailAddress", "accountId"],
            "creator": ["displayName", "emailAddress", "accountId"],
            "fixVersions": ["name", "releaseDate", "released", "id"],
            "fixversions": [
                "name",
                "releaseDate",
                "released",
                "id",
            ],  # lowercase variant
            "components": ["name", "id", "description"],
            "labels": [],  # Array of strings, no properties
        }

        parts = partial_path.split(".")
        if len(parts) >= 2:
            # Extract field name (might include changelog syntax)
            field_name = parts[1].split(":")[0].lower()

            if field_name in common_properties:
                property_prefix = parts[-1] if len(parts) > 2 else ""
                base_path = ".".join(parts[:-1]) if len(parts) > 2 else partial_path

                suggestions = []
                for prop in common_properties[field_name]:
                    if prop.lower().startswith(property_prefix.lower()):
                        suggestions.append(
                            {
                                "label": f"{base_path}.{prop}",
                                "value": f"{base_path}.{prop}",
                                "description": f"Property: {prop}",
                            }
                        )
                return suggestions[:50]

        return []


def create_autocomplete_provider(
    jira_url: str, jira_token: str
) -> NamespaceAutocompleteProvider:
    """Create autocomplete provider with JIRA metadata fetcher.

    Args:
        jira_url: JIRA instance base URL
        jira_token: JIRA API token for authentication

    Returns:
        NamespaceAutocompleteProvider instance

    Example:
        >>> provider = create_autocomplete_provider(
        ...     "https://jira.example.com",
        ...     "api-token-here"
        ... )
        >>> suggestions = provider.get_suggestions("Dev")
    """
    metadata = JiraMetadataFetcher(jira_url=jira_url, jira_token=jira_token)
    return NamespaceAutocompleteProvider(metadata)
