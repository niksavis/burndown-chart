"""
Data schema for the Burndown application.

Defines the structure of data used across the application.
"""

from typing import Any, Literal, TypedDict

#######################################################################
# CSV SCHEMA
#######################################################################

STATISTICS_COLUMNS = [
    "date",  # Date of work (YYYY-MM-DD format)
    "completed_items",  # Number of items completed on that date
    "completed_points",  # Number of points completed on that date
    "created_items",  # Number of items created on that date (for scope change tracking)
    "created_points",  # Number of points created on that date (for scope change tracking)
]

#######################################################################
# DATA STRUCTURES
#######################################################################

# Default empty statistics data structure
DEFAULT_STATISTICS = {
    "data": [],
    "baseline": {
        "items": 0,  # Initial scope (items) at project start
        "points": 0,  # Initial scope (points) at project start
        "date": "",  # Date when baseline was established
    },
    "timestamp": "",  # Last update timestamp
}

# Default settings structure
DEFAULT_SETTINGS = {
    # Scope change settings
    "scope_change_threshold": 20,  # Default threshold for scope change alerts (%)
    "track_scope_changes": True,  # Whether to track scope changes
    "scope_change_throughput_threshold": 1.2,  # Alert when scope grows 20% faster than throughput
    # Performance optimization settings
    "forecast_max_days": 3653,  # Maximum forecast horizon in days (10 years absolute cap)
    "forecast_max_points": 150,  # Maximum data points per forecast line
    "pessimistic_multiplier_cap": 5,  # Max ratio of pessimistic to optimistic forecast
}

# For backwards compatibility
DEFAULT_SETTINGS["scope_creep_threshold"] = DEFAULT_SETTINGS["scope_change_threshold"]

#######################################################################
# UNIFIED JSON DATA SCHEMA (v2.0)
#######################################################################

# JSON Schema for unified project data
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
            "date": str,  # ISO format YYYY-MM-DD
            "completed_items": int,
            "completed_points": int,
            "created_items": int,
            "created_points": int,
            "velocity_items": int,  # Weekly completion rate
            "velocity_points": int,  # Weekly point completion rate
        }
    ],
    "metadata": {
        "source": str,  # "jira_calculated", "manual", "csv_import"
        "last_updated": str,  # ISO datetime
        "version": str,  # Data format version
        "jira_query": str,  # JQL used for calculation
    },
}

#######################################################################
# JQL QUERY PROFILE SCHEMA
#######################################################################

# Schema for JQL query profiles
JQL_QUERY_PROFILE_SCHEMA = {
    "id": str,  # UUID for the profile
    "name": str,  # User-friendly name
    "jql": str,  # JQL query string
    "description": str,  # Optional description
    "created_at": str,  # ISO datetime when created
    "last_used": str,  # ISO datetime when last used
    "is_default": bool,  # Whether this is a default/system profile
}

# Default JQL query profiles
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
    """
    Validate project data structure against the schema.

    Args:
        data: Project data dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
    required_keys = ["project_scope", "statistics", "metadata"]

    if not all(key in data for key in required_keys):
        return False

    # Validate project_scope structure
    scope_keys = ["total_items", "total_points", "estimated_items", "estimated_points"]
    if not all(key in data["project_scope"] for key in scope_keys):
        return False

    # Validate statistics structure
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

    # Validate metadata structure
    if not isinstance(data["metadata"], dict):
        return False

    return True


def get_default_unified_data() -> dict[str, Any]:
    """
    Return default unified data structure.

    Returns:
        Dict: Default unified project data structure
    """
    from datetime import datetime

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
    """
    Validate JQL query profile structure.

    Args:
        profile: Query profile dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
    required_keys = ["id", "name", "jql"]

    if not all(key in profile for key in required_keys):
        return False

    # Validate types
    if not isinstance(profile["id"], str) or not profile["id"]:
        return False

    if not isinstance(profile["name"], str) or not profile["name"]:
        return False

    if not isinstance(profile["jql"], str):
        return False

    # Optional fields
    if "description" in profile and not isinstance(profile["description"], str):
        return False

    if "is_default" in profile and not isinstance(profile["is_default"], bool):
        return False

    return True


#######################################################################
# UI STATE SCHEMAS (Phase 006-ux-ui-redesign)
#######################################################################


class NavigationState(TypedDict):
    """
    Navigation state tracking active tab and history.

    Follows data-model.md Section 1.2 NavigationState specification.
    Persistence: Session-level dcc.Store (memory storage type).
    """

    active_tab: str  # Currently active tab ID (e.g., "tab-dashboard")
    tab_history: list[str]  # Last N visited tabs for back navigation (max 10)
    previous_tab: str  # Tab user was on before current
    session_start_tab: str  # First tab loaded in current session


class ParameterPanelState(TypedDict):
    """
    Parameter panel collapse state and user preferences.

    Follows data-model.md Section 1.1 ParameterPanelState specification.
    Persistence: Client-side localStorage via dcc.Store.
    """

    is_open: bool  # Whether parameter panel is expanded or collapsed
    last_updated: str  # When state was last modified (ISO 8601 format)
    user_preference: bool  # Whether user manually set state (vs. default)


class MobileNavigationState(TypedDict):
    """
    Mobile-specific navigation drawer and bottom sheet state.

    Follows data-model.md Section 1.3 MobileNavigationState specification.
    Persistence: Client-side dcc.Store (memory storage, resets on page load).
    """

    drawer_open: bool  # Whether mobile navigation drawer is open
    bottom_sheet_visible: bool  # Whether parameter bottom sheet is visible
    swipe_enabled: bool  # Whether swipe gestures are enabled
    viewport_width: int  # Current viewport width in pixels
    is_mobile: bool  # Computed flag if viewport < 768px


class LayoutPreferences(TypedDict):
    """
    User's preferred layout configuration and display options.

    Follows data-model.md Section 1.4 LayoutPreferences specification.
    Persistence: Client-side localStorage via dcc.Store.
    """

    theme: Literal["light", "dark"]  # UI theme (currently only "light")
    compact_mode: bool  # Whether to use compact spacing
    show_help_icons: bool  # Whether to show contextual help icons
    animation_enabled: bool  # Whether to enable UI animations
    preferred_chart_height: int  # User's preferred chart height in pixels (300-1200)


def get_default_navigation_state() -> NavigationState:
    """
    Return default navigation state.

    Returns:
        NavigationState: Default state with dashboard as active tab
    """
    return {
        "active_tab": "tab-dashboard",
        "tab_history": [],
        "previous_tab": "",
        "session_start_tab": "tab-dashboard",
    }


def get_default_parameter_panel_state() -> ParameterPanelState:
    """
    Return default parameter panel state.

    Returns:
        ParameterPanelState: Default state with panel collapsed
    """
    from datetime import datetime

    return {
        "is_open": False,
        "last_updated": datetime.now().isoformat(),
        "user_preference": False,
    }


def get_default_mobile_navigation_state() -> MobileNavigationState:
    """
    Return default mobile navigation state.

    Returns:
        MobileNavigationState: Default state for mobile navigation
    """
    return {
        "drawer_open": False,
        "bottom_sheet_visible": False,
        "swipe_enabled": True,
        "viewport_width": 1024,
        "is_mobile": False,
    }


def get_default_layout_preferences() -> LayoutPreferences:
    """
    Return default layout preferences.

    Returns:
        LayoutPreferences: Default user preferences
    """
    return {
        "theme": "light",
        "compact_mode": False,
        "show_help_icons": True,
        "animation_enabled": True,
        "preferred_chart_height": 600,
    }


def validate_navigation_state(state: dict[str, Any]) -> bool:
    """
    Validate navigation state structure.

    Args:
        state: Navigation state dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if "active_tab" not in state:
        return False

    # Validate tab ID pattern
    import re

    pattern = re.compile(r"^tab-[a-z-]+$")
    if not pattern.match(state["active_tab"]):
        return False

    # Validate tab history if present
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
    """
    Validate parameter panel state structure.

    Args:
        state: Parameter panel state dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if "is_open" not in state or not isinstance(state["is_open"], bool):
        return False

    if "user_preference" in state and not isinstance(state["user_preference"], bool):
        return False

    return True


def validate_mobile_navigation_state(state: dict[str, Any]) -> bool:
    """
    Validate mobile navigation state structure.

    Args:
        state: Mobile navigation state dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
    bool_fields = ["drawer_open", "bottom_sheet_visible", "swipe_enabled", "is_mobile"]

    for field in bool_fields:
        if field in state and not isinstance(state[field], bool):
            return False

    if "viewport_width" in state:
        if not isinstance(state["viewport_width"], int) or state["viewport_width"] <= 0:
            return False

    return True


def validate_layout_preferences(prefs: dict[str, Any]) -> bool:
    """
    Validate layout preferences structure.

    Args:
        prefs: Layout preferences dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
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


#######################################################################
# BUG ANALYSIS SCHEMA
#######################################################################

# Bug Issue type definition (matches data-model.md)
BUG_ISSUE_SCHEMA = {
    "key": str,  # JIRA issue key (e.g., "PROJ-123")
    "type": str,  # Mapped issue type ("Bug", "Defect", "Incident")
    "original_type": str,  # Original JIRA type name
    "created_date": str,  # Creation timestamp (ISO format)
    "resolved_date": str,  # Resolution timestamp (ISO format, None if open)
    "status": str,  # JIRA status name
    "story_points": int,  # Story points (None if not estimated)
    "week_created": str,  # Week identifier (ISO format: "2025-W01")
    "week_resolved": str,  # Week resolved (None if open)
}

# Weekly Bug Statistics type definition (matches data-model.md)
WEEKLY_BUG_STATISTICS_SCHEMA = {
    "week": str,  # ISO week identifier (e.g., "2025-W03")
    "week_start_date": str,  # ISO date of week start (e.g., "2025-01-13")
    "bugs_created": int,  # Count of bugs created this week
    "bugs_resolved": int,  # Count of bugs resolved this week
    "bugs_points_created": int,  # Story points created this week
    "bugs_points_resolved": int,  # Story points resolved this week
    "net_bugs": int,  # bugs_created - bugs_resolved
    "net_points": int,  # bugs_points_created - bugs_points_resolved
    "cumulative_open_bugs": int,  # Running total of open bugs
}

# Bug Metrics Summary type definition (matches data-model.md)
BUG_METRICS_SUMMARY_SCHEMA = {
    "total_bugs": int,  # Total bugs in project
    "open_bugs": int,  # Currently open bugs
    "closed_bugs": int,  # Resolved bugs
    "resolution_rate": float,  # closed_bugs / total_bugs (0.0-1.0)
    "avg_resolution_time_days": float,  # Average days to close a bug
    "bugs_created_last_4_weeks": int,  # Recent bug creation rate
    "bugs_resolved_last_4_weeks": int,  # Recent bug resolution rate
    "trend_direction": str,  # "improving" | "stable" | "degrading"
    "total_bug_points": int,  # Total story points for bugs
    "open_bug_points": int,  # Points for open bugs
    "capacity_consumed_by_bugs": float,  # Percentage of capacity (0.0-1.0)
}

# Quality Insight type definition (matches data-model.md)
QUALITY_INSIGHT_SCHEMA = {
    "id": str,  # Unique insight ID (e.g., "LOW_RESOLUTION_RATE")
    "type": str,  # Insight type: "warning", "recommendation", "positive"
    "severity": str,  # Severity: "critical", "high", "medium", "low"
    "title": str,  # Short title (max 60 chars)
    "message": str,  # Detailed message (max 200 chars)
    "metrics": dict[str, float],  # Supporting metrics
    "actionable": bool,  # Whether insight has recommended action
    "action_text": str,  # Recommended action (if actionable)
    "created_at": str,  # When insight was generated (ISO format)
}

# Bug Forecast type definition (matches data-model.md)
BUG_FORECAST_SCHEMA = {
    "open_bugs": int,  # Current open bug count
    "avg_closure_rate": float,  # Average bugs closed per week
    "optimistic_weeks": int,  # Best-case weeks to resolution
    "pessimistic_weeks": int,  # Worst-case weeks to resolution
    "most_likely_weeks": int,  # Most likely weeks to resolution
    "optimistic_date": str,  # Best-case completion date (ISO)
    "pessimistic_date": str,  # Worst-case completion date (ISO)
    "most_likely_date": str,  # Most likely completion date (ISO)
    "confidence_level": float,  # Statistical confidence (0.0-1.0)
    "insufficient_data": bool,  # True if not enough history
}

# Bug Analysis Data Container (extends unified data structure)
BUG_ANALYSIS_DATA_SCHEMA = {
    "enabled": bool,  # Feature toggle
    "bug_issues": list,  # List[BugIssue]
    "weekly_bug_statistics": list,  # List[WeeklyBugStatistics]
    "bug_metrics_summary": dict[str, Any],  # BugMetricsSummary
    "quality_insights": list,  # List[QualityInsight]
    "bug_forecast": dict[str, Any],  # BugForecast
    "last_updated": str,  # ISO timestamp
}


def validate_bug_issue(issue: dict[str, Any]) -> bool:
    """Validate a bug issue matches schema.

    Args:
        issue: Bug issue dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ["key", "type", "created_date", "status"]

    if not all(field in issue for field in required_fields):
        return False

    # Validate key format (basic check)
    if not isinstance(issue["key"], str) or "-" not in issue["key"]:
        return False

    return True


def validate_weekly_bug_statistics(stats: dict[str, Any]) -> bool:
    """Validate weekly bug statistics matches schema.

    Args:
        stats: Weekly bug statistics dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
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

    # Validate counts are non-negative
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
    """Validate bug analysis data structure.

    Args:
        data: Bug analysis data dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
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

    # Validate types
    if not isinstance(data["enabled"], bool):
        return False

    if not isinstance(data["bug_issues"], list):
        return False

    if not isinstance(data["weekly_bug_statistics"], list):
        return False

    return True


def get_default_bug_analysis_data() -> dict[str, Any]:
    """Return default bug analysis data structure.

    Returns:
        Dict: Default bug analysis data structure
    """
    from datetime import datetime

    return {
        "enabled": False,
        "bug_issues": [],
        "weekly_bug_statistics": [],
        "bug_metrics_summary": {},
        "quality_insights": [],
        "bug_forecast": {},
        "last_updated": datetime.now().isoformat(),
    }
