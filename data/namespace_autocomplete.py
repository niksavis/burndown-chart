import logging

from data.jira.metadata_fetcher import JiraMetadataFetcher

logger = logging.getLogger(__name__)


class NamespaceAutocompleteProvider:
    def __init__(self, metadata_fetcher: JiraMetadataFetcher):

        self.metadata = metadata_fetcher

    def get_suggestions(
        self, partial_path: str, cursor_position: int | None = None
    ) -> list[dict[str, str]]:

        if cursor_position is None:
            cursor_position = len(partial_path)

        working_path = partial_path[:cursor_position].strip()

        if not working_path:
            return self._suggest_projects("")

        parts = working_path.split(".")

        if len(parts) == 1:
            return self._suggest_projects(parts[0])
        elif len(parts) == 2:
            project_filter = parts[0]
            field_prefix = parts[1]
            return self._suggest_fields(project_filter, field_prefix)
        elif ":" in parts[-1]:
            return self._suggest_changelog_values(working_path)
        else:
            return self._suggest_properties(working_path)

    def _suggest_projects(self, prefix: str) -> list[dict[str, str]]:

        suggestions = []

        if prefix == "" or "*".startswith(prefix.lower()):
            suggestions.append(
                {
                    "label": "* (All Projects)",
                    "value": "*.",
                    "description": "Match issues from any project",
                }
            )

        try:
            projects = self.metadata.fetch_projects()

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

            return suggestions[:50]

        except Exception as e:
            logger.error(f"Failed to fetch projects for autocomplete: {e}")
            return suggestions[:1] if suggestions else []

    def _suggest_fields(
        self, project_filter: str, field_prefix: str
    ) -> list[dict[str, str]]:

        suggestions = []

        try:
            fields = self.metadata.fetch_fields()

            for field in fields:
                field_id = field.get("id", "")
                field_name = field.get("name", field_id)
                field_type = field.get("schema", {}).get("type", "unknown")

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

            return suggestions[:50]

        except Exception as e:
            logger.error(f"Failed to fetch fields for autocomplete: {e}")
            return []

    def _suggest_changelog_values(self, partial_path: str) -> list[dict[str, str]]:

        suggestions = []

        parts = partial_path.split(":")
        if len(parts) < 2:
            return []

        field_path = parts[0]
        value_prefix = parts[1].split(".")[0] if "." in parts[1] else parts[1]

        field_name = field_path.split(".")[-1].lower()

        try:
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

    def _suggest_properties(self, partial_path: str) -> list[dict[str, str]]:

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
            ],
            "components": ["name", "id", "description"],
            "labels": [],
        }

        parts = partial_path.split(".")
        if len(parts) >= 2:
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

    metadata = JiraMetadataFetcher(jira_url=jira_url, jira_token=jira_token)
    return NamespaceAutocompleteProvider(metadata)
