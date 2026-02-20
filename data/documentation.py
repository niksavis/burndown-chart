"""
T008: Documentation System Integration

Integrates contextual documentation that adapts to the user's current setup progress.
Documentation is shown at the right time with the right level of detail, reducing
cognitive load while providing comprehensive guidance when needed.

Key Features:
- Progressive documentation disclosure based on setup step
- Interactive help tooltips and guided tours
- Context-sensitive help panels that adapt to current state
- Integration with T006 smart defaults and T007 error handling
- Mobile-friendly help system with quick access patterns
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HelpContent:
    """Structured help content for T008 documentation system."""

    title: str
    summary: str
    content: str
    level: str  # "beginner", "intermediate", "advanced"
    tags: list[str]
    related_topics: list[str]
    examples: list[dict[str, str]] | None = None
    troubleshooting: list[dict[str, str]] | None = None


# ============================================================================
# T008: Progressive Documentation System
# ============================================================================


def get_contextual_documentation(
    setup_step: str, setup_status: dict[str, Any], user_level: str = "beginner"
) -> dict[str, Any]:
    """Get contextual documentation for current setup step (T008).

    Args:
        setup_step: Current setup step
        setup_status: Profile setup status
        user_level: User experience level (beginner/intermediate/advanced)

    Returns:
        Documentation content adapted to context
    """
    documentation = {
        "profile_creation": _get_profile_creation_docs(user_level),
        "jira_connection": _get_jira_connection_docs(user_level, setup_status),
        "field_mapping": _get_field_mapping_docs(user_level, setup_status),
        "query_creation": _get_query_creation_docs(user_level, setup_status),
    }

    current_docs = documentation.get(setup_step, _get_default_docs())

    # Add contextual enhancements based on setup status
    current_docs = _enhance_docs_with_context(current_docs, setup_status, user_level)

    return current_docs


def _get_profile_creation_docs(user_level: str) -> dict[str, Any]:
    """Documentation for profile creation step."""
    if user_level == "beginner":
        return {
            "title": "[Start] Creating Your First Workspace",
            "summary": "Profiles organize your JIRA analysis projects",
            "sections": [
                {
                    "title": "What is a Profile?",
                    "content": "A profile is like a workspace that contains all settings for analyzing a specific JIRA project or team. You can have multiple profiles for different projects.",
                    "level": "essential",
                },
                {
                    "title": "Choosing a Name",
                    "content": "Pick a descriptive name like 'Sprint Analysis 2025' or 'Team Alpha Dashboard'. This helps you identify the right profile when you have multiple projects.",
                    "level": "essential",
                },
                {
                    "title": "Next Steps",
                    "content": "After creating your profile, you'll connect it to JIRA, configure any special fields, and create queries to analyze your data.",
                    "level": "essential",
                },
            ],
            "examples": [
                {
                    "name": "Project Alpha Analysis",
                    "description": "Main development project tracking",
                },
                {
                    "name": "Sprint Retrospective Q4",
                    "description": "Team performance analysis",
                },
            ],
            "quick_tips": [
                "Start with a simple, descriptive name",
                "You can always rename profiles later",
                "Each profile has isolated settings",
            ],
        }
    else:
        return {
            "title": "Profile Management",
            "summary": "Advanced profile configuration and management",
            "sections": [
                {
                    "title": "Profile Architecture",
                    "content": "Profiles provide data isolation with dedicated cache directories and independent JIRA configurations.",
                    "level": "advanced",
                },
                {
                    "title": "Bulk Operations",
                    "content": "Import/export profiles for team sharing and backup purposes.",
                    "level": "advanced",
                },
            ],
            "api_reference": [
                {
                    "function": "create_profile()",
                    "description": "Programmatic profile creation",
                },
                {"function": "export_profile()", "description": "Profile data export"},
            ],
        }


def _get_jira_connection_docs(
    user_level: str, setup_status: dict[str, Any]
) -> dict[str, Any]:
    """Documentation for JIRA connection step."""
    base_docs = {
        "title": "Connecting to JIRA",
        "summary": "Securely connect to your JIRA instance for data analysis",
        "sections": [
            {
                "title": "JIRA URL",
                "content": "Enter your complete JIRA URL. For Atlassian Cloud, this is usually https://your-company.atlassian.net. For JIRA Server, use your organization's JIRA URL.",
                "level": "essential",
            },
            {
                "title": "API Token Security",
                "content": "API tokens are safer than passwords and can be revoked if needed. Generate one at: Atlassian Account Settings → Security → API tokens.",
                "level": "essential",
            },
            {
                "title": "Testing Connection",
                "content": "Always test your connection before proceeding. This verifies your credentials and checks API access.",
                "level": "essential",
            },
        ],
        "troubleshooting": [
            {
                "problem": "Connection timeout or unreachable",
                "solution": "Verify URL is correct and accessible. Check network/VPN settings.",
            },
            {
                "problem": "401 Unauthorized error",
                "solution": "Check email address and API token. Generate a fresh token if needed.",
            },
            {
                "problem": "403 Forbidden error",
                "solution": "Your account may lack necessary permissions. Contact JIRA admin.",
            },
        ],
    }

    # Add advanced sections for experienced users
    if user_level in ["intermediate", "advanced"]:
        base_docs["sections"].append(
            {
                "title": "API Version Selection",
                "content": "JIRA REST API v2 is recommended for stability. v3 offers newer features but may have compatibility issues.",
                "level": "advanced",
            }
        )

    return base_docs


def _get_field_mapping_docs(
    user_level: str, setup_status: dict[str, Any]
) -> dict[str, Any]:
    """Documentation for field mapping step."""
    return {
        "title": " Mapping JIRA Fields",
        "summary": "Configure custom fields to enable DORA and Flow metrics",
        "sections": [
            {
                "title": "Why Map Fields?",
                "content": "Field mapping enables advanced metrics like DORA (DevOps Research & Assessment) and Flow metrics by telling the system which JIRA fields contain specific data.",
                "level": "essential",
            },
            {
                "title": "Finding Custom Field IDs",
                "content": "View any JIRA issue, right-click → View Source, and search for 'customfield_'. The format is always customfield_XXXXX where X is a number.",
                "level": "essential",
            },
            {
                "title": "Optional vs Required",
                "content": "Field mapping is entirely optional. You can skip this step and still get basic burndown charts and velocity metrics.",
                "level": "essential",
            },
        ],
        "examples": [
            {
                "field": "Story Points",
                "id": "customfield_10002",
                "description": "Most common story points field",
            },
            {
                "field": "Epic Link",
                "id": "customfield_10014",
                "description": "Links issues to epics",
            },
        ],
        "field_finder_tip": "Look for fields in JIRA Admin → Issues → Custom Fields, or examine issue view source code.",
    }


def _get_query_creation_docs(
    user_level: str, setup_status: dict[str, Any]
) -> dict[str, Any]:
    """Documentation for query creation step."""
    jira_connected = setup_status.get("jira_connected", False)

    docs = {
        "title": "Creating JQL Queries",
        "summary": "Define JQL queries to analyze specific sets of JIRA issues",
        "sections": [
            {
                "title": "What is JQL?",
                "content": "JIRA Query Language (JQL) lets you search for issues using structured queries. Think of it like SQL for JIRA data.",
                "level": "essential",
            },
            {
                "title": "Basic Query Structure",
                "content": "Queries follow the pattern: project = PROJECT_KEY AND field = value ORDER BY created DESC",
                "level": "essential",
            },
        ],
        "examples": [
            {
                "name": "All Project Issues",
                "jql": "project = YOUR_PROJECT ORDER BY created DESC",
                "description": "Every issue in your project, newest first",
            },
            {
                "name": "Recent Work",
                "jql": "project = YOUR_PROJECT AND created >= -30d",
                "description": "Issues created in the last 30 days",
            },
            {
                "name": "In Progress Items",
                "jql": "project = YOUR_PROJECT AND status IN ('In Progress', 'In Review')",
                "description": "Currently active work items",
            },
        ],
        "jql_tips": [
            "Use JIRA's issue search to build and test queries",
            "Copy working queries from JIRA into the dashboard",
            "Start simple and add filters gradually",
        ],
    }

    # Add connection-specific guidance
    if not jira_connected:
        docs["prerequisites"] = {
            "title": "[!] JIRA Connection Required",
            "content": "You need to configure JIRA connection before creating queries. The system needs to validate query syntax against your JIRA instance.",
            "action": "Complete JIRA configuration first",
        }

    return docs


def _get_default_docs() -> dict[str, Any]:
    """Default documentation when step is unknown."""
    return {
        "title": "Setup Guide",
        "summary": "Follow the step-by-step setup process",
        "sections": [
            {
                "title": "Getting Started",
                "content": "Follow each setup step in order to configure your JIRA analysis dashboard.",
                "level": "essential",
            }
        ],
    }


def _enhance_docs_with_context(
    docs: dict[str, Any], setup_status: dict[str, Any], user_level: str
) -> dict[str, Any]:
    """Enhance documentation with contextual information."""
    # Add progress indicator
    completed_steps = sum(
        1
        for key, value in setup_status.items()
        if key.endswith("_ready")
        or key.endswith("_connected")
        or key.endswith("_mapped")
        or key.endswith("_created")
        if value
    )

    docs["progress"] = {
        "completed_steps": completed_steps,
        "total_steps": 4,
        "percentage": int((completed_steps / 4) * 100),
    }

    # Add next steps guidance
    current_step = setup_status.get("current_step", "profile_creation")
    docs["next_action"] = _get_next_action_guidance(current_step, setup_status)

    return docs


def _get_next_action_guidance(
    current_step: str, setup_status: dict[str, Any]
) -> dict[str, str]:
    """Get guidance for next action based on current step."""
    actions = {
        "profile_creation": {
            "title": "Create Your Profile",
            "description": "Choose a name and description for your workspace",
            "button_text": "Create Profile",
        },
        "jira_connection": {
            "title": "Configure JIRA Connection",
            "description": "Enter your JIRA URL and API credentials",
            "button_text": "Configure JIRA",
        },
        "field_mapping": {
            "title": "Map JIRA Fields (Optional)",
            "description": "Configure custom fields for advanced metrics",
            "button_text": "Map Fields",
        },
        "query_creation": {
            "title": "Create Your First Query",
            "description": "Define a JQL query to analyze your issues",
            "button_text": "Create Query",
        },
        "completed": {
            "title": "Setup Complete!",
            "description": "Your dashboard is ready to use",
            "button_text": "View Dashboard",
        },
    }

    return actions.get(current_step, actions["profile_creation"])


# ============================================================================
# T008: Interactive Help System
# ============================================================================


def get_tooltip_content(
    element_id: str, context: dict[str, Any]
) -> dict[str, str] | None:
    """Get tooltip content for UI elements (T008).

    Args:
        element_id: ID of UI element needing tooltip
        context: Current application context

    Returns:
        Tooltip content or None if not available
    """
    tooltips = {
        "jira-url-input": {
            "title": "JIRA Instance URL",
            "content": "Full URL to your JIRA instance, including https://",
            "example": "https://your-company.atlassian.net",
        },
        "api-token-input": {
            "title": "API Token",
            "content": "Secure token for API access. Generate at: Account Settings → Security → API tokens",
            "warning": "Keep this token secret - it provides full account access",
        },
        "points-field-input": {
            "title": "Story Points Field",
            "content": "Custom field ID for story points (usually customfield_10002)",
            "help_link": "#finding-field-ids",
        },
        "jql-query-input": {
            "title": "JQL Query",
            "content": "JIRA Query Language for filtering issues",
            "example": "project = PROJ AND created >= -30d",
        },
    }

    return tooltips.get(element_id)


def get_guided_tour_steps(setup_status: dict[str, Any]) -> list[dict[str, Any]]:
    """Get guided tour steps based on current setup progress (T008).

    Args:
        setup_status: Current profile setup status

    Returns:
        List of tour steps for current context
    """
    current_step = setup_status.get("current_step", "profile_creation")

    tour_sequences = {
        "profile_creation": [
            {
                "target": "#profile-name-input",
                "title": "Choose Profile Name",
                "content": "Pick a descriptive name for this workspace",
                "position": "bottom",
            },
            {
                "target": "#create-profile-btn",
                "title": "Create Profile",
                "content": "Click here to create your new workspace",
                "position": "bottom",
            },
        ],
        "jira_connection": [
            {
                "target": "#jira-url-input",
                "title": "Enter JIRA URL",
                "content": "Your JIRA instance URL (e.g., https://company.atlassian.net)",
                "position": "bottom",
            },
            {
                "target": "#api-token-input",
                "title": "Add API Token",
                "content": "Generate this in Atlassian Account Settings → Security → API tokens",
                "position": "bottom",
            },
            {
                "target": "#test-connection-btn",
                "title": "Test Connection",
                "content": "Always test your connection before proceeding",
                "position": "bottom",
            },
        ],
        "query_creation": [
            {
                "target": "#query-name-input",
                "title": "Query Name",
                "content": "Descriptive name for this query (e.g., 'Sprint Issues')",
                "position": "bottom",
            },
            {
                "target": "#jql-input",
                "title": "JQL Query",
                "content": "Use JQL to filter issues (start with: project = YOUR_PROJECT)",
                "position": "bottom",
            },
        ],
    }

    return tour_sequences.get(current_step, [])


# ============================================================================
# T008: Mobile-Friendly Help System
# ============================================================================


def get_mobile_help_content(setup_step: str) -> dict[str, Any]:
    """Get mobile-optimized help content (T008).

    Args:
        setup_step: Current setup step

    Returns:
        Mobile-friendly help content
    """
    mobile_help = {
        "jira_connection": {
            "title": "Connect JIRA",
            "steps": [
                "[Edit] Enter your JIRA URL",
                "[Key] Add API token",
                "[Test] Test connection",
                "[OK] Save settings",
            ],
            "quick_tip": "Generate API tokens in Atlassian Account Settings",
            "time_estimate": "2-3 minutes",
        },
        "field_mapping": {
            "title": "Map Fields",
            "steps": [
                "[Search] Find field IDs in JIRA",
                "[List] Copy field names",
                "[Edit] Enter in mapping form",
                "[OK] Save mappings",
            ],
            "quick_tip": "Field mapping is optional - skip if unsure",
            "time_estimate": "5-10 minutes",
        },
        "query_creation": {
            "title": "Create Query",
            "steps": [
                "[Edit] Name your query",
                "[Search] Write JQL filter",
                "[Test] Test in JIRA first",
                "[OK] Save query",
            ],
            "quick_tip": "Start with: project = YOUR_PROJECT",
            "time_estimate": "1-2 minutes",
        },
    }

    return mobile_help.get(
        setup_step,
        {
            "title": "Setup Step",
            "steps": ["Follow the setup process"],
            "time_estimate": "A few minutes",
        },
    )


def generate_help_search_index() -> dict[str, list[str]]:
    """Generate search index for help content (T008).

    Returns:
        Search index mapping terms to help topics
    """
    return {
        "jira": ["jira_connection", "api_token", "connection_test"],
        "connection": ["jira_connection", "network_issues", "authentication"],
        "fields": ["field_mapping", "custom_fields", "story_points"],
        "query": ["query_creation", "jql", "filters"],
        "jql": ["query_creation", "jql_syntax", "jql_examples"],
        "error": ["troubleshooting", "common_issues", "error_handling"],
        "setup": ["getting_started", "setup_guide", "configuration"],
        "profile": ["profile_creation", "workspace", "profile_management"],
        "api": ["api_token", "authentication", "jira_api"],
        "metrics": ["dora_metrics", "flow_metrics", "field_mapping"],
    }
