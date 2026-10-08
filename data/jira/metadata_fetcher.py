import logging

import requests

from data.exceptions import JiraError

logger = logging.getLogger(__name__)


class JiraMetadataFetcher:
    def __init__(self, jira_url: str, jira_token: str, api_version: str = "v2"):

        self.jira_url = jira_url.rstrip("/")
        self.api_version = api_version.replace("v", "")
        self.jira_token = jira_token
        self.headers = {"Accept": "application/json"}
        if jira_token:
            self.headers["Authorization"] = f"Bearer {jira_token}"

        self._fields_cache: list[dict] | None = None
        self._projects_cache: list[dict] | None = None
        self._issue_types_cache: list[dict] | None = None
        self._statuses_cache: list[dict] | None = None
        self._field_options_cache: dict[str, list[str]] = {}

    def fetch_fields(self, force_refresh: bool = False) -> list[dict]:

        if self._fields_cache is not None and not force_refresh:
            return self._fields_cache

        try:
            url = f"{self.jira_url}/rest/api/{self.api_version}/field"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            fields = response.json()
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
            logger.info(f"[JIRA] Fetched {len(normalized)} fields")
            return normalized

        except requests.exceptions.RequestException as e:
            logger.error(f"[JIRA] Failed to fetch fields: {e}")
            return []

    def fetch_projects(self, force_refresh: bool = False) -> list[dict]:

        if self._projects_cache is not None and not force_refresh:
            return self._projects_cache

        try:
            url = f"{self.jira_url}/rest/api/{self.api_version}/project"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            projects = response.json()
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
            logger.info(f"[JIRA] Fetched {len(normalized)} projects")
            return normalized

        except requests.exceptions.RequestException as e:
            logger.error(f"[JIRA] Failed to fetch projects: {e}")
            return []

    def fetch_issue_types(self, force_refresh: bool = False) -> list[dict]:

        if self._issue_types_cache is not None and not force_refresh:
            return self._issue_types_cache

        try:
            url = f"{self.jira_url}/rest/api/{self.api_version}/issuetype"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            issue_types = response.json()
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
            logger.info(f"[JIRA] Fetched {len(normalized)} issue types")
            return normalized

        except requests.exceptions.RequestException as e:
            logger.error(f"[JIRA] Failed to fetch issue types: {e}")
            return []

    def fetch_statuses(self, force_refresh: bool = False) -> list[dict]:

        if self._statuses_cache is not None and not force_refresh:
            return self._statuses_cache

        try:
            url = f"{self.jira_url}/rest/api/{self.api_version}/status"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            statuses = response.json()
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
            logger.info(f"[JIRA] Fetched {len(normalized)} statuses")
            return normalized

        except requests.exceptions.RequestException as e:
            logger.error(f"[JIRA] Failed to fetch statuses: {e}")
            return []

    def fetch_field_options(
        self, field_id: str, force_refresh: bool = False
    ) -> list[str]:

        if field_id in self._field_options_cache and not force_refresh:
            return self._field_options_cache[field_id]

        try:
            url = (
                f"{self.jira_url}/rest/api/{self.api_version}/field/{field_id}/context"
            )
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                contexts = response.json().get("values", [])
                logger.info(
                    f"[JIRA] Found {len(contexts)} contexts for field {field_id}"
                )

                all_options = set()
                for context in contexts:
                    context_id = context.get("id")
                    context_name = context.get("name", "unknown")
                    logger.info(
                        f"[JIRA] Processing context {context_id} ({context_name})"
                    )

                    if context_id:
                        start_at = 0
                        max_results = 100
                        has_more = True

                        while has_more:
                            options_url = (
                                f"{self.jira_url}/rest/api/{self.api_version}/field/"
                                f"{field_id}/context/{context_id}/option"
                            )
                            params = {"startAt": start_at, "maxResults": max_results}
                            options_response = requests.get(
                                options_url,
                                headers=self.headers,
                                params=params,
                                timeout=10,
                            )

                            if options_response.status_code == 200:
                                options_data = options_response.json()
                                options = options_data.get("values", [])
                                total = options_data.get("total", len(options))
                                is_last = options_data.get("isLast", True)

                                logger.info(
                                    f"[JIRA] Context {context_id}: Retrieved "
                                    f"{len(options)} options "
                                    f"(startAt={start_at}, total={total})"
                                )

                                for option in options:
                                    option_value = option.get("value")
                                    is_disabled = option.get("disabled", False)

                                    if option_value:
                                        all_options.add(option_value)
                                        if is_disabled:
                                            logger.info(
                                                "[JIRA]   - Disabled option: "
                                                f"{option_value}"
                                            )

                                if is_last or len(options) < max_results:
                                    has_more = False
                                else:
                                    start_at += len(options)
                            else:
                                logger.warning(
                                    f"[JIRA] Failed to fetch options for context "
                                    f"{context_id}: {options_response.status_code}"
                                )
                                has_more = False

                if all_options:
                    values = sorted(all_options)
                    self._field_options_cache[field_id] = values
                    logger.info(
                        f"[JIRA] Fetched {len(values)} total options "
                        f"for field {field_id} from all contexts: {values}"
                    )
                    return values

            url = f"{self.jira_url}/rest/api/{self.api_version}/field/{field_id}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                field_data = response.json()
                schema = field_data.get("schema", {})
                custom_data = schema.get("custom", "")

                allowed_values = field_data.get("allowedValues", [])
                if not allowed_values:
                    allowed_values = schema.get("allowedValues", [])

                if allowed_values:
                    values = []
                    for val in allowed_values:
                        if isinstance(val, str):
                            values.append(val)
                        elif isinstance(val, dict):
                            value = (
                                val.get("value") or val.get("name") or val.get("label")
                            )
                            if value:
                                values.append(value)

                    if values:
                        self._field_options_cache[field_id] = values
                        logger.info(
                            f"[JIRA] Fetched {len(values)} options "
                            f"for field {field_id} from schema: {values}"
                        )
                        return values
                else:
                    logger.debug(
                        f"[JIRA] No allowedValues in schema for {field_id} "
                        f"(type: {custom_data})"
                    )

            url = (
                f"{self.jira_url}/rest/api/{self.api_version}/"
                f"customFieldOption/{field_id}"
            )
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    values = [opt.get("value", "") for opt in data.get("values", [])]
                elif isinstance(data, list):
                    values = [opt.get("value", "") for opt in data]
                else:
                    values = []

                if values:
                    self._field_options_cache[field_id] = values
                    logger.info(
                        f"[JIRA] Fetched {len(values)} options for field {field_id} "
                        f"from legacy endpoint"
                    )
                    return values

        except requests.exceptions.RequestException as e:
            logger.debug(f"[JIRA] Field config API failed for {field_id}: {e}")

        logger.info(f"[JIRA] Trying to extract {field_id} values from jira_cache.json")
        try:
            import json  # noqa: PLC0415
            import os  # noqa: PLC0415

            cache_file = "jira_cache.json"
            if os.path.exists(cache_file):
                with open(cache_file, encoding="utf-8") as f:
                    cache_data = json.load(f)

                issues = cache_data.get("issues", [])
                logger.info(
                    f"[JIRA] Found {len(issues)} cached issues, "
                    f"extracting {field_id} values"
                )

                unique_values = set()
                for issue in issues:
                    field_value = issue.get("fields", {}).get(field_id)

                    if field_value is None:
                        continue

                    if isinstance(field_value, str):
                        unique_values.add(field_value)
                    elif isinstance(field_value, dict):
                        if "value" in field_value:
                            unique_values.add(field_value["value"])
                        elif "name" in field_value:
                            unique_values.add(field_value["name"])
                    elif isinstance(field_value, list):
                        for item in field_value:
                            if isinstance(item, str):
                                unique_values.add(item)
                            elif isinstance(item, dict):
                                if "value" in item:
                                    unique_values.add(item["value"])
                                elif "name" in item:
                                    unique_values.add(item["name"])

                if unique_values:
                    values = sorted(unique_values)
                    self._field_options_cache[field_id] = values
                    logger.info(
                        f"[JIRA] Extracted {len(values)} unique values "
                        f"from cache: {values}"
                    )
                    return values
                else:
                    logger.info(f"[JIRA] No values found for {field_id} in cache")
            else:
                logger.info(f"[JIRA] Cache file {cache_file} not found")

        except (OSError, TypeError, ValueError) as e:
            logger.warning(f"[JIRA] Failed to extract from cache: {e}")

        logger.info(
            f"[JIRA] Fetching {field_id} values via JQL query "
            "(sampling up to 1000 issues from development projects)"
        )
        try:
            values = self._fetch_field_values_from_issues(
                field_id, scoped=True, max_results=1000
            )

            if values:
                self._field_options_cache[field_id] = values
                logger.info(
                    f"[JIRA] Extracted {len(values)} unique values "
                    f"from issues: {values}"
                )
                return values
            else:
                logger.warning(f"[JIRA] No values found for field {field_id}")
                return []

        except (JiraError, KeyError, RuntimeError, TypeError, ValueError) as e:
            logger.error(f"[JIRA] Failed to fetch values for field {field_id}: {e}")
            return []

    def _fetch_field_values_from_issues(
        self, field_id: str, max_results: int = 1000, scoped: bool = True
    ) -> list[str]:

        try:
            logger.info(
                f"[JIRA] Attempting to fetch field values from issues: "
                f"{field_id} (scoped={scoped})"
            )

            field_name = None
            if self._fields_cache:
                for field in self._fields_cache:
                    if field.get("id") == field_id:
                        field_name = field.get("name")
                        break

            if scoped:
                from data.persistence import load_app_settings  # noqa: PLC0415

                settings = load_app_settings()
                dev_projects = settings.get("development_projects", [])

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
            else:
                if field_name:
                    jql = f'"{field_name}" IS NOT EMPTY'
                else:
                    jql = f"{field_id} IS NOT EMPTY"

            jql_with_order = f"{jql} ORDER BY created DESC"
            logger.info(
                f"[JIRA] Executing JQL: {jql_with_order} (max {max_results} - SAMPLING)"
            )
            url = f"{self.jira_url}/rest/api/{self.api_version}/search"

            params = {
                "jql": jql_with_order,
                "fields": field_id,
                "maxResults": min(max_results, 1000),
            }

            response = requests.get(
                url, headers=self.headers, params=params, timeout=30
            )

            if response.status_code != 200:
                logger.warning(
                    f"[JIRA] JQL with IS NOT EMPTY failed ({response.status_code}), "
                    f"trying simpler query"
                )
                from data.persistence import load_app_settings  # noqa: PLC0415

                settings = load_app_settings()
                dev_projects = settings.get("development_projects", [])
                if not dev_projects:
                    dev_projects = settings.get("project_classification", {}).get(
                        "development_projects", []
                    )
                if dev_projects:
                    simple_jql = (
                        f"project IN ({','.join(dev_projects)}) ORDER BY created DESC"
                    )
                    logger.info(f"[JIRA] Fallback JQL with projects: {simple_jql}")
                else:
                    simple_jql = "ORDER BY created DESC"
                    logger.info(
                        "[JIRA] No development projects configured, "
                        "trying unscoped fallback JQL"
                    )

                params["jql"] = simple_jql
                response = requests.get(
                    url, headers=self.headers, params=params, timeout=30
                )

            if response.status_code != 200:
                logger.warning(
                    f"[JIRA] Issue search failed for {field_id} ({field_name}): "
                    f"{response.status_code}"
                )
                return []

            data = response.json()
            issues = data.get("issues", [])
            logger.info(f"[JIRA] Query returned {len(issues)} issues")

            if not issues:
                logger.warning(f"[JIRA] No issues found with {field_id}")
                return []

            unique_values = set()
            for issue in issues:
                if issue is None:
                    continue
                fields = issue.get("fields")
                if fields is None:
                    continue
                field_value = fields.get(field_id)

                if field_value is None:
                    continue

                if isinstance(field_value, str):
                    unique_values.add(field_value)
                elif isinstance(field_value, dict):
                    if "value" in field_value:
                        unique_values.add(field_value["value"])
                    elif "name" in field_value:
                        unique_values.add(field_value["name"])
                elif isinstance(field_value, list):
                    for item in field_value:
                        if isinstance(item, str):
                            unique_values.add(item)
                        elif isinstance(item, dict):
                            if "value" in item:
                                unique_values.add(item["value"])
                            elif "name" in item:
                                unique_values.add(item["name"])

            sorted_values = sorted(unique_values)
            logger.info(
                f"[JIRA] Found {len(sorted_values)} unique values for {field_id}: "
                f"{sorted_values}"
            )
            return sorted_values

        except requests.exceptions.RequestException as e:
            logger.error(f"[JIRA] Failed to query issues for {field_id}: {e}")
            return []
        except (JiraError, KeyError, RuntimeError, TypeError, ValueError) as e:
            logger.error(
                f"[JIRA] Error extracting values from issues for {field_id}: {e}"
            )
            return []

    def auto_detect_devops_projects(
        self, projects: list[dict], issue_types: list[dict]
    ) -> list[str]:

        devops_patterns = ["operational", "deployment", "release", "devops", "ops"]

        devops_type_names = set()
        for issue_type in issue_types:
            name_lower = issue_type["name"].lower()
            if any(pattern in name_lower for pattern in devops_patterns):
                devops_type_names.add(issue_type["name"])

        if not devops_type_names:
            logger.info("[JIRA] No DevOps-related issue types found")
            return []

        logger.info(f"[JIRA] Found potential DevOps issue types: {devops_type_names}")
        return []

    def auto_detect_issue_types(self, issue_types: list[dict]) -> dict[str, list[str]]:

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

            if any(pattern in name_lower for pattern in devops_patterns):
                categories["devops_task_types"].append(name)
            elif any(pattern in name_lower for pattern in bug_patterns):
                categories["bug_types"].append(name)
            elif any(pattern in name_lower for pattern in story_patterns):
                categories["story_types"].append(name)
            elif any(pattern in name_lower for pattern in task_patterns):
                categories["task_types"].append(name)

        logger.info(f"[JIRA] Auto-detected issue type categories: {categories}")
        return categories

    def auto_detect_statuses(self, statuses: list[dict]) -> dict[str, list[str]]:

        categories = {
            "flow_end_statuses": [],
            "active_statuses": [],
            "flow_start_statuses": [],
            "wip_statuses": [],
        }

        for status in statuses:
            name = status["name"]
            category_key = status.get("category_key", "undefined")

            if category_key == "done":
                categories["flow_end_statuses"].append(name)
            elif category_key == "indeterminate":
                categories["active_statuses"].append(name)
                categories["flow_start_statuses"].append(name)
                categories["wip_statuses"].append(name)
            elif category_key == "new":
                categories["wip_statuses"].append(name)

        logger.info(f"[JIRA] Auto-detected status categories: {categories}")
        return categories

    def auto_detect_production_identifiers(self, field_options: list[str]) -> list[str]:

        prod_patterns = ["prod", "production", "live", "prd"]

        production_values = []
        for value in field_options:
            value_lower = value.lower()
            if any(pattern in value_lower for pattern in prod_patterns):
                production_values.append(value)

        logger.info(f"[JIRA] Auto-detected production identifiers: {production_values}")
        return production_values

    def clear_cache(self):
        self._fields_cache = None
        self._projects_cache = None
        self._issue_types_cache = None
        self._statuses_cache = None
        self._field_options_cache = {}
        logger.info("[JIRA] Cleared metadata cache")


def create_metadata_fetcher(
    jira_url: str, jira_token: str, api_version: str = "v2"
) -> JiraMetadataFetcher:

    return JiraMetadataFetcher(jira_url, jira_token, api_version)
