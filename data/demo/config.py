from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any

from utils.business_time import DEFAULT_DEMO_AS_OF

START = datetime(2025, 12, 8, tzinfo=UTC)
AS_OF = datetime.fromisoformat(DEFAULT_DEMO_AS_OF)
SEED_VERSION = "eight-weeks-v1"
SCENARIOS = (
    "complete",
    "empty",
    "singleton",
    "zero-delivery",
    "stalled",
    "sparse",
    "fractional-points",
    "completed",
    "reopened",
    "missing-signals",
    "no-points",
    "no-deadline",
    "past-deadline",
    "due-today",
    "scope-change",
    "unmapped-fields",
)
FIELD_MAPPINGS = {
    "general": {
        "estimate": "customfield_10001",
        "created_date": "created",
        "updated_date": "updated",
        "completed_date": "resolutiondate",
        "parent_field": "parent",
        "parent_issue_types": ["Epic"],
        "sprint_field": "customfield_10002",
    },
    "flow": {
        "flow_item_type": "issuetype",
        "status": "status",
        "completed_date": "resolutiondate",
    },
    "dora": {
        "deployment_date": "fixVersions",
        "code_commit_date": "status:In Progress.DateTime",
        "incident_detected_at": "created",
        "incident_resolved_at": "resolutiondate",
        "target_environment": "customfield_10003=PROD",
        "affected_environment": "customfield_10003=PROD",
        "change_failure": "customfield_10004=Yes",
        "severity_level": "priority",
    },
}
PROJECT_CLASSIFICATION = {
    "development_projects": ["DEMO"],
    "devops_projects": ["OPS"],
    "devops_task_types": ["Operational Task"],
    "bug_types": ["Bug"],
    "flow_end_statuses": ["Done"],
    "active_statuses": ["In Progress", "Testing"],
    "wip_statuses": ["In Progress", "Review", "Testing"],
    "flow_start_statuses": ["In Progress"],
    "production_environment_values": ["PROD"],
}
FLOW_TYPE_MAPPINGS = {
    category: {"issue_types": [issue_type], "effort_categories": []}
    for category, issue_type in [
        ("Feature", "Story"),
        ("Defect", "Bug"),
        ("Technical Debt", "Task"),
        ("Risk", "Risk"),
    ]
}


def profile_config(scenario: str) -> dict[str, Any]:
    deadline = (AS_OF + timedelta(weeks=4)).date().isoformat()
    if scenario == "no-deadline":
        deadline = None
    elif scenario == "past-deadline":
        deadline = (AS_OF - timedelta(days=7)).date().isoformat()
    elif scenario == "due-today":
        deadline = AS_OF.date().isoformat()
    profile: dict[str, Any] = {
        "id": f"demo-{scenario}",
        "name": f"Acme Corp - {scenario}",
        "description": "Synthetic eight-week offline scenario",
        "created_at": START.isoformat(),
        "last_used": AS_OF.isoformat(),
        "jira_config": {
            "base_url": "",
            "token": "",
            "configured": False,
            "points_field": "customfield_10001",
        },
        "forecast_settings": {
            "pert_factor": 3,
            "data_points_count": 8,
            "deadline": deadline,
        },
        "field_mappings": deepcopy(FIELD_MAPPINGS),
        "project_classification": deepcopy(PROJECT_CLASSIFICATION),
        "flow_type_mappings": deepcopy(FLOW_TYPE_MAPPINGS),
        "show_points": scenario != "no-points",
        "show_milestone": False,
    }
    if scenario == "unmapped-fields":
        profile["field_mappings"] = {"general": {}, "flow": {}, "dora": {}}
    return profile
