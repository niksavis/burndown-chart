from data.jira.query_profiles import load_query_profiles
from data.persistence import load_app_settings


def _get_default_data_source() -> str:

    try:
        app_settings = load_app_settings()
        data_source = app_settings.get("last_used_data_source", "JIRA")
        return data_source if data_source else "JIRA"
    except ImportError, Exception:
        return "JIRA"


def _get_default_jql_query() -> str:

    try:
        app_settings = load_app_settings()
        return app_settings.get("jql_query", "project = JRASERVER")
    except ImportError:
        return "project = JRASERVER"


def _get_default_jql_profile_id() -> str:

    try:
        app_settings = load_app_settings()
        return app_settings.get("active_jql_profile_id", "")
    except ImportError, Exception:
        return ""


def _get_default_jira_story_points_field() -> str:

    try:
        app_settings = load_app_settings()
        return app_settings.get("jira_story_points_field", "")
    except ImportError:
        return ""


def _get_default_jira_cache_max_size() -> int:

    try:
        app_settings = load_app_settings()
        return app_settings.get("jira_cache_max_size", 100)
    except ImportError:
        return 100


def _get_default_jira_max_results() -> int:

    try:
        app_settings = load_app_settings()
        return app_settings.get("jira_max_results", 1000)
    except ImportError:
        return 1000


def _get_query_profile_options() -> list[dict[str, str]]:

    try:
        profiles = load_query_profiles()
        options = []

        for profile in profiles:
            label = profile["name"]
            if profile.get("is_default", False):
                label += " [Default]"
            options.append(
                {
                    "label": label,
                    "value": profile["id"],
                }
            )

        return options

    except ImportError, Exception:
        return []
