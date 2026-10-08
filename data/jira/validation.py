import logging

import requests

logger = logging.getLogger(__name__)


def validate_jql_for_scriptrunner(jql_query: str) -> tuple[bool, str]:

    if not jql_query:
        return True, ""

    scriptrunner_functions = [
        "issueFunction",
        "subtasksOf",
        "epicsOf",
        "linkedIssuesOf",
        "parentEpicsOf",
        "subtaskOf",
        "portfolioChildrenOf",
        "portfolioParentsOf",
        "portfolioSiblingsOf",
    ]

    query_lower = jql_query.lower()
    found_functions = []

    for func in scriptrunner_functions:
        if func.lower() in query_lower:
            found_functions.append(func)

    if found_functions:
        warning = (
            "Warning: JQL query contains ScriptRunner functions: "
            f"{', '.join(found_functions)}. "
            "These functions require the ScriptRunner add-on and "
            "may not be available on all JIRA instances. "
            "If you get 'failed to fetch jira data' errors, "
            "try simplifying the query or verify ScriptRunner is installed."
        )
        return False, warning

    return True, ""


def test_jql_query(config: dict) -> tuple[bool, str]:

    try:
        jql = config["jql_query"]
        api_endpoint = config.get("api_endpoint", "")

        if not api_endpoint:
            return False, "JIRA API endpoint not configured"

        headers = {"Accept": "application/json"}
        if config["token"]:
            headers["Authorization"] = f"Bearer {config['token']}"

        params = {
            "jql": jql,
            "maxResults": 1,
            "fields": "key",
        }

        logger.info(f"[JIRA] Testing JQL query: {jql[:100]}...")
        response = requests.get(
            api_endpoint, headers=headers, params=params, timeout=10
        )

        if not response.ok:
            error_details = ""
            try:
                error_json = response.json()
                if "errorMessages" in error_json:
                    error_details = "; ".join(error_json["errorMessages"])
                elif "errors" in error_json:
                    error_details = "; ".join(
                        [f"{k}: {v}" for k, v in error_json["errors"].items()]
                    )
                else:
                    error_details = str(error_json)
            except Exception:
                error_details = response.text[:200]

            if "issueFunction" in jql.lower() and (
                "function" in error_details.lower()
                or "scriptrunner" in error_details.lower()
            ):
                return (
                    False,
                    "ScriptRunner function error: "
                    f"{error_details}. "
                    "This JIRA instance may not have ScriptRunner installed "
                    "or you may not have permission to use these functions.",
                )

            return False, f"JQL query invalid: {error_details}"

        try:
            data = response.json()
            total = data.get("total", 0)
            logger.info(f"[JIRA] Query valid - would return {total} issues")
            return True, f"JQL query is valid (would return {total} issues)"
        except ValueError as json_error:
            logger.error(f"[JIRA] HTTP 200 but invalid JSON: {json_error}")
            logger.error(
                f"[JIRA] Response body (first 200 chars): {response.text[:200]}"
            )
            return (
                False,
                "JIRA API returned invalid response (HTTP 200 but not JSON). "
                "Your JIRA server may not support this API version. "
                "Try switching to API v2 in Configure JIRA.",
            )

    except requests.exceptions.RequestException as e:
        return False, f"Network error testing JQL query: {e}"
    except Exception as e:
        return False, f"Error testing JQL query: {e}"
