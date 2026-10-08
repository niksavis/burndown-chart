from datetime import datetime
from typing import Any, Literal, TypedDict

STATISTICS_COLUMNS = [
    "date",
    "completed_items",
    "completed_points",
    "created_items",
    "created_points",
]


DEFAULT_STATISTICS = {
    "data": [],
    "baseline": {
        "items": 0,
        "points": 0,
        "date": "",
    },
    "timestamp": "",
}

DEFAULT_SETTINGS = {
    "scope_change_threshold": 20,
    "track_scope_changes": True,
    "scope_change_throughput_threshold": 1.2,
    "forecast_max_days": 3653,
    "forecast_max_points": 150,
    "pessimistic_multiplier_cap": 5,
}

DEFAULT_SETTINGS["scope_creep_threshold"] = DEFAULT_SETTINGS["scope_change_threshold"]


PROJECT_DATA_SCHEMA = {
    "project_scope": {
        "total_items": int,
        "total_points": int,
        "estimated_items": int,
        "estimated_points": int,
        "remaining_items": int,
        "remaining_points": int,
    },
    "statistics": [
        {
            "date": str,
            "completed_items": int,
            "completed_points": int,
            "created_items": int,
            "created_points": int,
            "velocity_items": int,
            "velocity_points": int,
        }
    ],
    "metadata": {
        "source": str,
        "last_updated": str,
        "version": str,
        "jira_query": str,
    },
}


JQL_QUERY_PROFILE_SCHEMA = {
    "id": str,
    "name": str,
    "jql": str,
    "description": str,
    "created_at": str,
    "last_used": str,
    "is_default": bool,
}

DEFAULT_JQL_PROFILES = [
    {
        "id": "default-all-open",
        "name": "All Open Issues",
        "jql": "project = MYPROJECT AND status != Done",
        "description": "All issues that are not completed",
        "is_default": True,
    },
    {
        "id": "default-recent-bugs",
        "name": "Recent Bugs (Last 2 Weeks)",
        "jql": "project = MYPROJECT AND type = Bug AND created >= -14d",
        "description": "Bugs created in the last 2 weeks",
        "is_default": True,
    },
    {
        "id": "default-current-sprint",
        "name": "Current Sprint",
        "jql": "sprint in openSprints() AND status != Done",
        "description": "Active sprint issues that are not completed",
        "is_default": True,
    },
]


def validate_project_data_structure(data: dict[str, Any]) -> bool:

    required_keys = ["project_scope", "statistics", "metadata"]

    if not all(key in data for key in required_keys):
        return False

    scope_keys = ["total_items", "total_points", "estimated_items", "estimated_points"]
    if not all(key in data["project_scope"] for key in scope_keys):
        return False

    if not isinstance(data["statistics"], list):
        return False

    for stat in data["statistics"]:
        if not isinstance(stat, dict):
            return False
        stat_keys = [
            "date",
            "completed_items",
            "completed_points",
            "created_items",
            "created_points",
        ]
        if not all(key in stat for key in stat_keys):
            return False

    if not isinstance(data["metadata"], dict):
        return False

    return True


def get_default_unified_data() -> dict[str, Any]:

    return {
        "project_scope": {
            "total_items": 0,
            "total_points": 0,
            "estimated_items": 0,
            "estimated_points": 0,
            "remaining_items": 0,
            "remaining_points": 0,
        },
        "statistics": [],
        "metadata": {
            "source": "manual",
            "last_updated": datetime.now().isoformat(),
            "version": "2.0",
            "jira_query": "",
        },
    }


def validate_query_profile(profile: dict[str, Any]) -> bool:

    required_keys = ["id", "name", "jql"]

    if not all(key in profile for key in required_keys):
        return False

    if not isinstance(profile["id"], str) or not profile["id"]:
        return False

    if not isinstance(profile["name"], str) or not profile["name"]:
        return False

    if not isinstance(profile["jql"], str):
        return False

    if "description" in profile and not isinstance(profile["description"], str):
        return False

    if "is_default" in profile and not isinstance(profile["is_default"], bool):
        return False

    return True


class NavigationState(TypedDict):
    active_tab: str
    tab_history: list[str]
    previous_tab: str
    session_start_tab: str


class ParameterPanelState(TypedDict):
    is_open: bool
    last_updated: str
    user_preference: bool


class MobileNavigationState(TypedDict):
    drawer_open: bool
    bottom_sheet_visible: bool
    swipe_enabled: bool
    viewport_width: int
    is_mobile: bool


class LayoutPreferences(TypedDict):
    theme: Literal["light", "dark"]
    compact_mode: bool
    show_help_icons: bool
    animation_enabled: bool
    preferred_chart_height: int


def get_default_navigation_state() -> NavigationState:

    return {
        "active_tab": "tab-dashboard",
        "tab_history": [],
        "previous_tab": "",
        "session_start_tab": "tab-dashboard",
    }


def get_default_parameter_panel_state() -> ParameterPanelState:

    return {
        "is_open": False,
        "last_updated": datetime.now().isoformat(),
        "user_preference": False,
    }


def get_default_mobile_navigation_state() -> MobileNavigationState:

    return {
        "drawer_open": False,
        "bottom_sheet_visible": False,
        "swipe_enabled": True,
        "viewport_width": 1024,
        "is_mobile": False,
    }


def get_default_layout_preferences() -> LayoutPreferences:

    return {
        "theme": "light",
        "compact_mode": False,
        "show_help_icons": True,
        "animation_enabled": True,
        "preferred_chart_height": 600,
    }


def validate_navigation_state(state: dict[str, Any]) -> bool:

    if "active_tab" not in state:
        return False

    import re  # noqa: PLC0415

    pattern = re.compile(r"^tab-[a-z-]+$")
    if not pattern.match(state["active_tab"]):
        return False

    if "tab_history" in state:
        if not isinstance(state["tab_history"], list):
            return False
        if len(state["tab_history"]) > 10:
            return False
        for tab_id in state["tab_history"]:
            if not pattern.match(tab_id):
                return False

    return True


def validate_parameter_panel_state(state: dict[str, Any]) -> bool:

    if "is_open" not in state or not isinstance(state["is_open"], bool):
        return False

    if "user_preference" in state and not isinstance(state["user_preference"], bool):
        return False

    return True


def validate_mobile_navigation_state(state: dict[str, Any]) -> bool:

    bool_fields = ["drawer_open", "bottom_sheet_visible", "swipe_enabled", "is_mobile"]

    for field in bool_fields:
        if field in state and not isinstance(state[field], bool):
            return False

    if "viewport_width" in state:
        if not isinstance(state["viewport_width"], int) or state["viewport_width"] <= 0:
            return False

    return True


def validate_layout_preferences(prefs: dict[str, Any]) -> bool:

    if "theme" in prefs and prefs["theme"] not in ["light", "dark"]:
        return False

    bool_fields = ["compact_mode", "show_help_icons", "animation_enabled"]
    for field in bool_fields:
        if field in prefs and not isinstance(prefs[field], bool):
            return False

    if "preferred_chart_height" in prefs:
        height = prefs["preferred_chart_height"]
        if not isinstance(height, int) or height < 300 or height > 1200:
            return False

    return True


BUG_ISSUE_SCHEMA = {
    "key": str,
    "type": str,
    "original_type": str,
    "created_date": str,
    "resolved_date": str,
    "status": str,
    "story_points": int,
    "week_created": str,
    "week_resolved": str,
}

WEEKLY_BUG_STATISTICS_SCHEMA = {
    "week": str,
    "week_start_date": str,
    "bugs_created": int,
    "bugs_resolved": int,
    "bugs_points_created": int,
    "bugs_points_resolved": int,
    "net_bugs": int,
    "net_points": int,
    "cumulative_open_bugs": int,
}

BUG_METRICS_SUMMARY_SCHEMA = {
    "total_bugs": int,
    "open_bugs": int,
    "closed_bugs": int,
    "resolution_rate": float,
    "avg_resolution_time_days": float,
    "bugs_created_last_4_weeks": int,
    "bugs_resolved_last_4_weeks": int,
    "trend_direction": str,
    "total_bug_points": int,
    "open_bug_points": int,
    "capacity_consumed_by_bugs": float,
}

QUALITY_INSIGHT_SCHEMA = {
    "id": str,
    "type": str,
    "severity": str,
    "title": str,
    "message": str,
    "metrics": dict[str, float],
    "actionable": bool,
    "action_text": str,
    "created_at": str,
}

BUG_FORECAST_SCHEMA = {
    "open_bugs": int,
    "avg_closure_rate": float,
    "optimistic_weeks": int,
    "pessimistic_weeks": int,
    "most_likely_weeks": int,
    "optimistic_date": str,
    "pessimistic_date": str,
    "most_likely_date": str,
    "confidence_level": float,
    "insufficient_data": bool,
}

BUG_ANALYSIS_DATA_SCHEMA = {
    "enabled": bool,
    "bug_issues": list,
    "weekly_bug_statistics": list,
    "bug_metrics_summary": dict[str, Any],
    "quality_insights": list,
    "bug_forecast": dict[str, Any],
    "last_updated": str,
}


def validate_bug_issue(issue: dict[str, Any]) -> bool:

    required_fields = ["key", "type", "created_date", "status"]

    if not all(field in issue for field in required_fields):
        return False

    if not isinstance(issue["key"], str) or "-" not in issue["key"]:
        return False

    return True


def validate_weekly_bug_statistics(stats: dict[str, Any]) -> bool:

    required_fields = [
        "week",
        "week_start_date",
        "bugs_created",
        "bugs_resolved",
        "bugs_points_created",
        "bugs_points_resolved",
        "net_bugs",
        "net_points",
        "cumulative_open_bugs",
    ]

    if not all(field in stats for field in required_fields):
        return False

    count_fields = [
        "bugs_created",
        "bugs_resolved",
        "bugs_points_created",
        "bugs_points_resolved",
        "cumulative_open_bugs",
    ]

    for field in count_fields:
        if not isinstance(stats[field], int) or stats[field] < 0:
            return False

    return True


def validate_bug_analysis_data(data: dict[str, Any]) -> bool:

    required_keys = [
        "enabled",
        "bug_issues",
        "weekly_bug_statistics",
        "bug_metrics_summary",
        "quality_insights",
        "bug_forecast",
        "last_updated",
    ]

    if not all(key in data for key in required_keys):
        return False

    if not isinstance(data["enabled"], bool):
        return False

    if not isinstance(data["bug_issues"], list):
        return False

    if not isinstance(data["weekly_bug_statistics"], list):
        return False

    return True


def get_default_bug_analysis_data() -> dict[str, Any]:

    return {
        "enabled": False,
        "bug_issues": [],
        "weekly_bug_statistics": [],
        "bug_metrics_summary": {},
        "quality_insights": [],
        "bug_forecast": {},
        "last_updated": datetime.now().isoformat(),
    }
