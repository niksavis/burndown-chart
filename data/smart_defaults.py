import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def get_smart_jira_defaults() -> dict[str, Any]:

    defaults = {
        "base_url": {
            "suggestions": [
                "https://your-company.atlassian.net",
                "https://jira.your-company.com",
                "https://your-company.jira.com",
            ],
            "placeholder": "https://your-company.atlassian.net",
            "help": "Your JIRA instance URL (typically Atlassian Cloud or self-hosted)",
        },
        "api_token": {
            "help": "Generate at: Atlassian Account Settings → Security → API tokens",
            "validation": "Required for API access",
        },
        "api_version": {
            "default": "v2",
            "options": ["v2", "v3"],
            "recommendation": "v2 (stable, widely supported)",
        },
        "points_field": {
            "common_values": [
                "customfield_10002",
                "customfield_10004",
                "customfield_10016",
                "customfield_10020",
                "customfield_10024",
            ],
            "help": "Story Points custom field ID (find in JIRA field configuration)",
            "detection_tip": "Look for 'Story Points' in your JIRA issue view source",
        },
    }

    return defaults


def get_smart_field_mapping_defaults() -> dict[str, Any]:

    defaults = {
        "deployment_date": {
            "common_ids": [
                "customfield_10030",
                "customfield_10031",
                "customfield_10032",
                "customfield_10050",
            ],
            "field_types": ["datetime", "date"],
            "help": "When deployment occurred (for Deployment Frequency)",
        },
        "deployment_successful": {
            "common_ids": [
                "customfield_10033",
                "customfield_10034",
                "customfield_10051",
            ],
            "field_types": ["checkbox", "boolean"],
            "help": "Whether deployment was successful (for Change Failure Rate)",
        },
        "work_started_date": {
            "fallback": "created",
            "common_ids": [
                "customfield_10040",
                "customfield_10041",
            ],
            "help": "When work began (for Flow Time calculation)",
        },
        "work_completed_date": {
            "fallback": "resolutiondate",
            "common_ids": [
                "customfield_10042",
                "customfield_10043",
            ],
            "help": "When work was finished (for Flow Time calculation)",
        },
        "work_type": {
            "common_ids": [
                "customfield_10035",
                "customfield_10036",
                "issuetype",
            ],
            "values": ["Feature", "Bug", "Technical Debt", "Risk"],
            "help": "Type of work item (for Flow Distribution)",
        },
    }

    return defaults


def get_smart_query_suggestions(profile_id: str) -> dict[str, str]:

    return _get_generic_query_suggestions()


def _get_generic_query_suggestions() -> dict[str, str]:
    return {
        "basic": "project = YOUR_PROJECT ORDER BY created DESC",
        "recent_work": (
            "project = YOUR_PROJECT AND created >= -30d ORDER BY created DESC"
        ),
        "active_work": (
            "project = YOUR_PROJECT "
            "AND status NOT IN (Done, Closed) ORDER BY priority DESC"
        ),
        "completed_work": (
            "project = YOUR_PROJECT AND status = Done ORDER BY updated DESC"
        ),
    }


def get_smart_profile_defaults() -> dict[str, Any]:

    now = datetime.now()

    defaults = {
        "name": {
            "suggestions": [
                f"Project Analysis {now.strftime('%Y')}",
                f"Sprint Analysis {now.strftime('%B %Y')}",
                f"Team Dashboard {now.strftime('%Y-%m')}",
                "Main Project Dashboard",
            ],
            "placeholder": "My Project Dashboard",
        },
        "description": {
            "templates": [
                "JIRA analysis dashboard for project tracking and metrics",
                "Sprint retrospective and team performance analytics",
                "DORA metrics and flow analysis for development team",
                "Project burndown and completion forecasting dashboard",
            ],
            "placeholder": "Description of this workspace (optional)",
        },
        "forecast_settings": {
            "pert_factor": {
                "default": 1.5,
                "range": [1.0, 3.0],
                "recommendations": {
                    1.2: "Conservative (low risk tolerance)",
                    1.5: "Balanced (recommended for most teams)",
                    2.0: "Aggressive (high risk tolerance)",
                },
            },
            "data_points_count": {
                "default": 12,
                "options": [8, 12, 16, 20],
                "recommendations": {
                    8: "Short-term focus (2 months)",
                    12: "Standard (3 months)",
                    16: "Extended (4 months)",
                    20: "Long-term (5 months)",
                },
            },
        },
    }

    return defaults


def get_contextual_help_for_step(
    step: str, setup_status: dict[str, Any]
) -> dict[str, str]:

    help_content = {
        "profile_creation": {
            "title": "[Start] Create Your Workspace",
            "description": "Set up a new profile to organize your JIRA analysis",
            "tips": [
                "Choose a descriptive name for easy identification",
                "Multiple profiles can track different projects",
                "Settings are isolated between profiles",
            ],
        },
        "jira_connection": {
            "title": "Connect to JIRA",
            "description": "Configure connection to your JIRA instance",
            "tips": [
                "Use API tokens instead of passwords for security",
                "Test connection before proceeding to next step",
                "Both Cloud and Server instances are supported",
            ],
        },
        "field_mapping": {
            "title": "Map JIRA Fields",
            "description": "Configure custom fields for DORA and Flow metrics",
            "tips": [
                "Field mapping is optional but enables advanced metrics",
                "Story points field is commonly customfield_10002",
                "You can find field IDs in JIRA issue view source",
            ],
        },
        "query_creation": {
            "title": "Create JQL Queries",
            "description": "Define queries to analyze specific sets of issues",
            "tips": [
                "Start with a simple project filter",
                "Use JQL autocomplete in JIRA to build queries",
                "Multiple queries can show different views of data",
            ],
        },
    }

    return help_content.get(
        step,
        {
            "title": "Setup Step",
            "description": "Complete this configuration step",
            "tips": ["Follow the guided setup process"],
        },
    )


def validate_jira_url(url: str) -> tuple[bool, str]:

    if not url:
        return False, "JIRA URL is required"

    if not url.startswith(("http://", "https://")):
        return False, "URL must start with http:// or https://"

    valid_patterns = [
        ".atlassian.net",
        ".jira.com",
        "jira.",
    ]

    if any(pattern in url.lower() for pattern in valid_patterns):
        return True, "URL format looks correct"

    if "." in url and len(url.split(".")) >= 2:
        return True, "URL format appears valid"

    return False, "URL format doesn't look like a typical JIRA instance"


def validate_custom_field_id(field_id: str) -> tuple[bool, str]:

    if not field_id:
        return True, ""

    if field_id.startswith("customfield_") and field_id[12:].isdigit():
        return True, "Custom field ID format is correct"

    built_in_fields = [
        "created",
        "updated",
        "resolutiondate",
        "assignee",
        "reporter",
        "status",
        "priority",
        "issuetype",
    ]

    if field_id.lower() in built_in_fields:
        return True, f"Built-in field '{field_id}' is valid"

    return (
        False,
        "Field ID should be in format 'customfield_XXXXX' or a built-in field name",
    )


def get_next_recommended_action(
    setup_status: dict[str, Any],
) -> dict[str, str] | None:

    if not setup_status.get("profile_ready", False):
        return {
            "action": "create_profile",
            "title": "Create Profile",
            "description": "Set up a new workspace for your JIRA analysis",
            "priority": "high",
        }

    if not setup_status.get("jira_connected", False):
        return {
            "action": "configure_jira",
            "title": "Connect to JIRA",
            "description": "Configure your JIRA connection to start importing data",
            "priority": "high",
        }

    if not setup_status.get("queries_created", False):
        return {
            "action": "create_query",
            "title": "Create First Query",
            "description": "Define a JQL query to analyze your issues",
            "priority": "medium",
        }

    if not setup_status.get("fields_mapped", False):
        return {
            "action": "configure_fields",
            "title": "Map JIRA Fields",
            "description": (
                "Optional: Enable DORA and Flow metrics by mapping custom fields"
            ),
            "priority": "low",
        }

    return None


def get_setup_completion_percentage(setup_status: dict[str, Any]) -> int:

    required_steps = [
        "profile_ready",
        "jira_connected",
        "queries_created",
    ]

    optional_steps = [
        "fields_mapped",
    ]

    completed_required = sum(
        1 for step in required_steps if setup_status.get(step, False)
    )
    completed_optional = sum(
        1 for step in optional_steps if setup_status.get(step, False)
    )

    required_percentage = (completed_required / len(required_steps)) * 80
    optional_percentage = (completed_optional / len(optional_steps)) * 20

    return int(required_percentage + optional_percentage)
