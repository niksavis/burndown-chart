"""
JIRA Metadata Fetching and Auto-Detection

This module provides functions to fetch JIRA metadata (projects, issue types, statuses, field options)
and auto-detect optimal configuration based on the JIRA instance setup.

Designed for the comprehensive mappings configuration UI to enable generic JIRA support.
"""

import logging
from typing import Dict, List, Optional
import requests

logger = logging.getLogger(__name__)


class JiraMetadataFetcher:
    """Fetch and cache JIRA metadata for configuration UI."""

    def __init__(self, jira_url: str, jira_token: str, api_version: str = "v2"):
        """
        Initialize metadata fetcher with JIRA credentials.

        Args:
            jira_url: JIRA instance URL (e.g., https://your-domain.atlassian.net)
            jira_token: JIRA API token or password
            api_version: JIRA API version to use ("v2" or "v3", default: "v2")
        """
        self.jira_url = jira_url.rstrip("/")
        self.api_version = api_version.replace("v", "")  # Normalize "v2" or "2" to "2"
        self.jira_token = jira_token
        self.headers = {"Accept": "application/json"}
        if jira_token:
            self.headers["Authorization"] = f"Bearer {jira_token}"

        # Session-level cache
        self._fields_cache: Optional[List[Dict]] = None
        self._projects_cache: Optional[List[Dict]] = None
        self._issue_types_cache: Optional[List[Dict]] = None
        self._statuses_cache: Optional[List[Dict]] = None
        self._field_options_cache: Dict[str, List[str]] = {}

    def fetch_fields(self, force_refresh: bool = False) -> List[Dict]:
        """
        Fetch all available JIRA fields (standard and custom).

        Args:
            force_refresh: Force API call even if cached

        Returns:
            List of field dictionaries with id, name, type, custom flag
        """
        if self._fields_cache is not None and not force_refresh:
            return self._fields_cache

        try:
            url = f"{self.jira_url}/rest/api/{self.api_version}/field"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            fields = response.json()
            # Normalize field data
            normalized = []
            for field in fields:
                normalized.append(
                    {
                        "id": field.get("id", ""),
                        "name": field.get("name", ""),
                        "type": field.get("schema", {}).get("type", "string"),
                        "custom": field.get("custom", False),
                    }
                )

            self._fields_cache = normalized
            logger.info(f"Fetched {len(normalized)} JIRA fields")
            return normalized

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch JIRA fields: {e}")
            return []

    def fetch_projects(self, force_refresh: bool = False) -> List[Dict]:
        """
        Fetch all accessible JIRA projects.

        Args:
            force_refresh: Force API call even if cached

        Returns:
            List of project dictionaries with key, name, and issue type info
        """
        if self._projects_cache is not None and not force_refresh:
            return self._projects_cache

        try:
            url = f"{self.jira_url}/rest/api/{self.api_version}/project"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            projects = response.json()
            # Normalize project data
            normalized = []
            for project in projects:
                normalized.append(
                    {
                        "key": project.get("key", ""),
                        "name": project.get("name", ""),
                        "id": project.get("id", ""),
                    }
                )

            self._projects_cache = normalized
            logger.info(f"Fetched {len(normalized)} JIRA projects")
            return normalized

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch JIRA projects: {e}")
            return []

    def fetch_issue_types(self, force_refresh: bool = False) -> List[Dict]:
        """
        Fetch all available JIRA issue types.

        Args:
            force_refresh: Force API call even if cached

        Returns:
            List of issue type dictionaries with id, name, description
        """
        if self._issue_types_cache is not None and not force_refresh:
            return self._issue_types_cache

        try:
            url = f"{self.jira_url}/rest/api/{self.api_version}/issuetype"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            issue_types = response.json()
            # Normalize issue type data
            normalized = []
            for issue_type in issue_types:
                normalized.append(
                    {
                        "id": issue_type.get("id", ""),
                        "name": issue_type.get("name", ""),
                        "description": issue_type.get("description", ""),
                        "subtask": issue_type.get("subtask", False),
                    }
                )

            self._issue_types_cache = normalized
            logger.info(f"Fetched {len(normalized)} JIRA issue types")
            return normalized

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch JIRA issue types: {e}")
            return []

    def fetch_statuses(self, force_refresh: bool = False) -> List[Dict]:
        """
        Fetch all available JIRA workflow statuses.

        Args:
            force_refresh: Force API call even if cached

        Returns:
            List of status dictionaries with id, name, and category
        """
        if self._statuses_cache is not None and not force_refresh:
            return self._statuses_cache

        try:
            url = f"{self.jira_url}/rest/api/{self.api_version}/status"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            statuses = response.json()
            # Normalize status data
            normalized = []
            for status in statuses:
                category = status.get("statusCategory", {})
                normalized.append(
                    {
                        "id": status.get("id", ""),
                        "name": status.get("name", ""),
                        "description": status.get("description", ""),
                        "category_key": category.get("key", "undefined"),
                        "category_name": category.get("name", "Undefined"),
                    }
                )

            self._statuses_cache = normalized
            logger.info(f"Fetched {len(normalized)} JIRA statuses")
            return normalized

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch JIRA statuses: {e}")
            return []

    def fetch_field_options(
        self, field_id: str, force_refresh: bool = False
    ) -> List[str]:
        """
        Fetch possible values for a select list field.

        Tries multiple strategies:
        1. Field configuration API (for predefined options)
        2. Extract unique values from actual issues (fallback)

        Args:
            field_id: JIRA field ID (e.g., customfield_11309)
            force_refresh: Force API call even if cached

        Returns:
            List of possible values for the field
        """
        if field_id in self._field_options_cache and not force_refresh:
            return self._field_options_cache[field_id]

        # Try field configuration endpoints first
        try:
            url = f"{self.jira_url}/rest/api/{self.api_version}/field/{field_id}/context/defaultValue"
            response = requests.get(url, headers=self.headers, timeout=10)

            # If context endpoint fails, try options endpoint
            if response.status_code == 404:
                url = f"{self.jira_url}/rest/api/{self.api_version}/customFieldOption/{field_id}"
                response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Extract values based on response structure
                if isinstance(data, dict):
                    values = [opt.get("value", "") for opt in data.get("values", [])]
                elif isinstance(data, list):
                    values = [opt.get("value", "") for opt in data]
                else:
                    values = []

                if values:
                    self._field_options_cache[field_id] = values
                    logger.info(
                        f"Fetched {len(values)} options for field {field_id} from field config"
                    )
                    return values

        except requests.exceptions.RequestException as e:
            logger.debug(f"Field config API failed for {field_id}: {e}")

        # Fallback: Extract unique values from actual issues
        logger.info(f"Trying to extract unique values for {field_id} from issues")
        try:
            values = self._fetch_field_values_from_issues(field_id)
            if values:
                self._field_options_cache[field_id] = values
                logger.info(
                    f"Extracted {len(values)} unique values for field {field_id} from issues"
                )
                return values
            else:
                logger.warning(f"No values found for field {field_id} in issues")
                return []

        except Exception as e:
            logger.error(f"Failed to fetch values for field {field_id}: {e}")
            return []

    def _fetch_field_values_from_issues(
        self, field_id: str, max_results: int = 1000
    ) -> List[str]:
        """
        Extract unique values for a field from actual JIRA issues.

        This is a fallback method when field configuration API doesn't work.

        Args:
            field_id: JIRA field ID (e.g., customfield_11309)
            max_results: Maximum issues to query (default: 1000)

        Returns:
            List of unique values found in issues
        """
        try:
            from data.persistence import load_app_settings

            logger.info(
                f"Attempting to fetch field values from issues for field: {field_id}"
            )

            # Load configured development projects to scope the query
            # Use only development projects (not devops) because:
            # - Users may not have full access to devops projects
            # - Custom fields may not exist in devops projects
            settings = load_app_settings()
            dev_projects = settings.get("development_projects", [])

            # Get field name for JQL query (some JIRA instances require field name, not ID)
            field_name = None
            if self._fields_cache:
                for field in self._fields_cache:
                    if field.get("id") == field_id:
                        field_name = field.get("name")
                        break

            # Build JQL query with project scope if available
            # Try field name in quotes first (works better in some JIRA instances)
            if dev_projects:
                project_clause = f"project IN ({','.join(dev_projects)}) AND "
                if field_name:
                    jql = f'{project_clause}"{field_name}" IS NOT EMPTY'
                else:
                    jql = f"{project_clause}{field_id} IS NOT EMPTY"
            else:
                if field_name:
                    jql = f'"{field_name}" IS NOT EMPTY'
                else:
                    jql = f"{field_id} IS NOT EMPTY"

            logger.info(f"Executing JQL query: {jql} (max {max_results} results)")
            url = f"{self.jira_url}/rest/api/{self.api_version}/search"

            params = {
                "jql": jql,
                "fields": field_id,
                "maxResults": max_results,
            }

            response = requests.get(
                url, headers=self.headers, params=params, timeout=30
            )

            if response.status_code != 200:
                logger.warning(
                    f"Issue search failed for field {field_id} ({field_name}): {response.status_code} - {response.text}"
                )
                return []

            data = response.json()
            issues = data.get("issues", [])
            logger.info(f"Query returned {len(issues)} issues")

            if not issues:
                logger.warning(f"No issues found with {field_id}")
                return []

            # Extract unique values
            unique_values = set()
            for issue in issues:
                field_value = issue.get("fields", {}).get(field_id)

                if field_value is None:
                    continue

                # Handle different field types
                if isinstance(field_value, str):
                    unique_values.add(field_value)
                elif isinstance(field_value, dict):
                    # For select/option fields
                    if "value" in field_value:
                        unique_values.add(field_value["value"])
                    elif "name" in field_value:
                        unique_values.add(field_value["name"])
                elif isinstance(field_value, list):
                    # For multi-select fields
                    for item in field_value:
                        if isinstance(item, str):
                            unique_values.add(item)
                        elif isinstance(item, dict):
                            if "value" in item:
                                unique_values.add(item["value"])
                            elif "name" in item:
                                unique_values.add(item["name"])

            # Sort and return as list
            sorted_values = sorted(unique_values)
            logger.info(
                f"Found {len(sorted_values)} unique values for {field_id}: {sorted_values}"
            )
            return sorted_values

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to query issues for {field_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error extracting values from issues for {field_id}: {e}")
            return []

    def auto_detect_devops_projects(
        self, projects: List[Dict], issue_types: List[Dict]
    ) -> List[str]:
        """
        Auto-detect projects that likely contain DevOps tasks.

        Strategy: Check for projects with issue types matching common DevOps patterns.

        Args:
            projects: List of project dictionaries
            issue_types: List of issue type dictionaries

        Returns:
            List of project keys likely to contain DevOps tasks
        """
        devops_patterns = ["operational", "deployment", "release", "devops", "ops"]

        # Find issue types matching DevOps patterns
        devops_type_names = set()
        for issue_type in issue_types:
            name_lower = issue_type["name"].lower()
            if any(pattern in name_lower for pattern in devops_patterns):
                devops_type_names.add(issue_type["name"])

        if not devops_type_names:
            logger.info("No DevOps-related issue types found")
            return []

        # For simplicity, return empty list since we'd need to query each project
        # This would require expensive API calls per project
        logger.info(f"Found potential DevOps issue types: {devops_type_names}")
        return []

    def auto_detect_issue_types(self, issue_types: List[Dict]) -> Dict[str, List[str]]:
        """
        Auto-detect and categorize issue types based on common patterns.

        Args:
            issue_types: List of issue type dictionaries

        Returns:
            Dictionary with categorized issue type names
        """
        categories = {
            "devops_task_types": [],
            "bug_types": [],
            "story_types": [],
            "task_types": [],
        }

        devops_patterns = ["operational", "deployment", "release", "devops", "ops"]
        bug_patterns = ["bug", "defect", "incident", "issue"]
        story_patterns = ["story", "user story", "feature"]
        task_patterns = ["task", "sub-task", "subtask", "to do", "todo"]

        for issue_type in issue_types:
            name = issue_type["name"]
            name_lower = name.lower()

            # Categorize based on patterns
            if any(pattern in name_lower for pattern in devops_patterns):
                categories["devops_task_types"].append(name)
            elif any(pattern in name_lower for pattern in bug_patterns):
                categories["bug_types"].append(name)
            elif any(pattern in name_lower for pattern in story_patterns):
                categories["story_types"].append(name)
            elif any(pattern in name_lower for pattern in task_patterns):
                categories["task_types"].append(name)

        logger.info(f"Auto-detected issue type categories: {categories}")
        return categories

    def auto_detect_statuses(self, statuses: List[Dict]) -> Dict[str, List[str]]:
        """
        Auto-detect and categorize statuses based on status categories.

        Args:
            statuses: List of status dictionaries with category info

        Returns:
            Dictionary with categorized status names
        """
        categories = {
            "completion_statuses": [],
            "active_statuses": [],
            "flow_start_statuses": [],
            "wip_statuses": [],
        }

        for status in statuses:
            name = status["name"]
            category_key = status.get("category_key", "undefined")

            # Map JIRA status categories to our categories
            if category_key == "done":
                categories["completion_statuses"].append(name)
            elif category_key == "indeterminate":  # In Progress category
                categories["active_statuses"].append(name)
                categories["flow_start_statuses"].append(name)
                categories["wip_statuses"].append(name)
            elif category_key == "new":  # To Do category
                categories["wip_statuses"].append(name)

        logger.info(f"Auto-detected status categories: {categories}")
        return categories

    def auto_detect_production_identifiers(self, field_options: List[str]) -> List[str]:
        """
        Auto-detect production environment identifiers from field values.

        Args:
            field_options: List of environment field values

        Returns:
            List of values likely representing production
        """
        prod_patterns = ["prod", "production", "live", "prd"]

        production_values = []
        for value in field_options:
            value_lower = value.lower()
            if any(pattern in value_lower for pattern in prod_patterns):
                production_values.append(value)

        logger.info(f"Auto-detected production identifiers: {production_values}")
        return production_values

    def clear_cache(self):
        """Clear all cached metadata."""
        self._fields_cache = None
        self._projects_cache = None
        self._issue_types_cache = None
        self._statuses_cache = None
        self._field_options_cache = {}
        logger.info("Cleared metadata cache")


def create_metadata_fetcher(
    jira_url: str, jira_token: str, api_version: str = "v2"
) -> JiraMetadataFetcher:
    """
    Factory function to create a metadata fetcher instance.

    Args:
        jira_url: JIRA instance URL
        jira_token: JIRA API token
        api_version: JIRA API version ("v2" or "v3", default: "v2")

    Returns:
        Configured JiraMetadataFetcher instance
    """
    return JiraMetadataFetcher(jira_url, jira_token, api_version)
