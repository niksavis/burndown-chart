import logging
import re
from typing import Any

from data.field_detector_core import detect_fields_from_issues

logger = logging.getLogger(__name__)


def generate_smart_defaults(
    metadata: dict[str, Any],
    jql_query: str | None = None,
    issues: list[dict] | None = None,
) -> dict[str, Any]:

    logger.info("[AutoConfigure] Generating smart defaults from JIRA metadata")

    statuses = metadata.get("statuses", [])
    issue_types = metadata.get("issue_types", [])
    projects = metadata.get("projects", [])
    auto_detected = metadata.get("auto_detected", {})

    defaults: dict[str, Any] = {
        "project_classification": {
            "flow_end_statuses": [],
            "active_statuses": [],
            "flow_start_statuses": [],
            "wip_statuses": [],
            "development_projects": [],
            "devops_projects": [],
            "devops_task_types": [],
            "bug_types": [],
        },
        "flow_type_mappings": {
            "Feature": [],
            "Defect": [],
            "TechnicalDebt": [],
            "Risk": [],
        },
    }

    flow_end_statuses, active_statuses, wip_statuses = _map_statuses_by_category(
        statuses, auto_detected
    )
    defaults["project_classification"]["flow_end_statuses"] = flow_end_statuses
    defaults["project_classification"]["active_statuses"] = active_statuses
    defaults["project_classification"]["wip_statuses"] = wip_statuses

    defaults["project_classification"]["flow_start_statuses"] = (
        _select_flow_start_statuses(wip_statuses)
    )

    logger.info(
        f"[AutoConfigure] Mapped {len(flow_end_statuses)} completion, "
        f"{len(active_statuses)} active, {len(wip_statuses)} WIP statuses"
    )

    flow_type_mappings, devops_task_types = _map_issue_types(issue_types, auto_detected)
    defaults["flow_type_mappings"] = flow_type_mappings

    defaults["project_classification"]["bug_types"] = flow_type_mappings.get(
        "Defect", []
    )

    defaults["project_classification"]["devops_task_types"] = devops_task_types
    logger.info(
        "[AutoConfigure] DevOps task types "
        f"(DORA Deployment Frequency): {devops_task_types}"
    )

    logger.info(
        f"[AutoConfigure] Mapped issue types: "
        f"Feature={len(flow_type_mappings['Feature'])}, "
        f"Defect={len(flow_type_mappings['Defect'])}, "
        f"TechnicalDebt={len(flow_type_mappings['Technical Debt'])}"
    )
    logger.info(
        f"[AutoConfigure] Incident types (bug_types): "
        f"{defaults['project_classification']['bug_types']}"
    )

    if jql_query:
        development_projects = _extract_projects_from_jql(jql_query, projects)
        defaults["project_classification"]["development_projects"] = (
            development_projects
        )
        logger.info(
            f"[AutoConfigure] Extracted {len(development_projects)} projects "
            f"from JQL: {development_projects}"
        )
    else:
        logger.info(
            "[AutoConfigure] No JQL query provided, skipping project extraction"
        )

    field_mappings: dict[str, Any] = {}

    flow_start_status = (
        defaults["project_classification"]["flow_start_statuses"][0]
        if defaults["project_classification"]["flow_start_statuses"]
        else "In Progress"
    )

    completion_status = flow_end_statuses[0] if flow_end_statuses else "Done"

    dora_mappings = {
        "deployment_date": f"status:{completion_status}.DateTime",
        "code_commit_date": f"status:{flow_start_status}.DateTime",
        "incident_detected_at": "created",
        "incident_resolved_at": "resolutiondate",
        "severity_level": "priority",
    }

    general_mappings = {
        "completed_date": "resolutiondate",
        "created_date": "created",
        "updated_date": "updated",
    }

    flow_mappings = {
        "flow_item_type": "issuetype",
        "status": "status",
    }

    logger.info(
        "[AutoConfigure] Flow metrics use status lists from project_classification: "
        "flow_start_statuses, flow_end_statuses (configured separately)"
    )

    if issues:
        logger.info(
            f"[AutoConfigure] Analyzing {len(issues)} issues "
            f"for custom field detection (optional enhancements)"
        )
        field_detections = detect_fields_from_issues(issues, metadata)

        optional_dora_fields = [
            (
                "deployment_successful",
                "deployment_successful",
            ),
            ("change_failure", "change_failure"),
            ("target_environment", "target_environment"),
            (
                "affected_environment",
                "target_environment",
            ),
        ]

        for field_name, detection_key in optional_dora_fields:
            if detection_key in field_detections:
                dora_mappings[field_name] = field_detections[detection_key]
                logger.info(
                    f"[AutoConfigure] Found custom {field_name} field - "
                    f"using {field_detections[detection_key]}"
                )

        optional_flow_fields = [
            ("effort_category", "effort_category"),
        ]

        for field_name, detection_key in optional_flow_fields:
            if detection_key in field_detections:
                flow_mappings[field_name] = field_detections[detection_key]
                logger.info(
                    f"[AutoConfigure] Found custom {field_name} field - "
                    f"using {field_detections[detection_key]}"
                )

        if "points_field" in field_detections:
            defaults["points_field"] = field_detections["points_field"]
            general_mappings["estimate"] = field_detections["points_field"]
            logger.info(
                f"[AutoConfigure] Detected points field: "
                f"{field_detections['points_field']}"
            )

        field_values = _extract_field_values(issues, field_detections)
        if field_values:
            defaults["field_values"] = field_values
            logger.info(
                f"[AutoConfigure] Extracted field values: {list(field_values.keys())}"
            )
    else:
        logger.info(
            "[AutoConfigure] No custom field detection "
            "(no issues provided). Using namespace syntax only."
        )

    field_mappings["general"] = general_mappings
    field_mappings["dora"] = dora_mappings
    field_mappings["flow"] = flow_mappings
    defaults["field_mappings"] = field_mappings

    logger.info(
        f"[AutoConfigure] Field mappings configured: "
        f"{len(general_mappings)} General fields, "
        f"{len(dora_mappings)} DORA fields, "
        f"{len(flow_mappings)} Flow fields"
    )

    return defaults


def _map_statuses_by_category(
    statuses: list[dict], auto_detected: dict
) -> tuple[list[str], list[str], list[str]]:

    flow_end_statuses = []
    active_statuses = []
    wip_statuses = []

    if auto_detected.get("statuses"):
        detected = auto_detected["statuses"]
        flow_end_statuses = detected.get("flow_end_statuses", [])
        active_statuses = detected.get("active_statuses", [])
        wip_statuses = detected.get("wip_statuses", [])

        logger.info("[AutoConfigure] Using auto-detected statuses from metadata")
        return flow_end_statuses, active_statuses, wip_statuses

    for status in statuses:
        status_name = status.get("name", "")
        category = status.get("statusCategory", {})
        category_key = category.get("key", "").lower()

        if category_key == "done":
            flow_end_statuses.append(status_name)
        elif category_key == "indeterminate":
            active_statuses.append(status_name)
            if not any(
                keyword in status_name.lower()
                for keyword in ["wait", "block", "hold", "pending"]
            ):
                wip_statuses.append(status_name)

    logger.info("[AutoConfigure] Manually categorized statuses by JIRA category")
    return flow_end_statuses, active_statuses, wip_statuses


def _select_flow_start_statuses(wip_statuses: list[str]) -> list[str]:

    if not wip_statuses:
        return []

    start_keywords = ["in progress", "in dev", "progress", "developing"]

    for keyword in start_keywords:
        matching = [s for s in wip_statuses if keyword in s.lower()]
        if matching:
            logger.info(
                f"[AutoConfigure] Selected flow start status: "
                f"{matching[0]} (matched '{keyword}')"
            )
            return [matching[0]]

    if wip_statuses:
        logger.info(
            f"[AutoConfigure] Using first WIP status as flow start: {wip_statuses[0]}"
        )
        return [wip_statuses[0]]

    return []


def _semantic_categorize_issue_type(type_name_lower: str) -> str:

    def matches_pattern(keywords):
        for keyword in keywords:
            if " " in keyword:
                if keyword in type_name_lower:
                    return True
            else:
                if re.search(rf"\b{re.escape(keyword)}\b", type_name_lower):
                    return True
        return False

    devops_keywords = [
        "deploy",
        "deployment",
        "release",
        "rollout",
        "publish",
        "go-live",
        "production release",
        "hotfix deploy",
        "operation",
        "operational",
        "ops",
        "cd",
        "continuous deployment",
        "pipeline deploy",
        "automated deploy",
        "promote to production",
        "production push",
        "prod deploy",
    ]
    if matches_pattern(devops_keywords):
        return "DevOps"

    defect_keywords = [
        "bug",
        "defect",
        "incident",
        "problem",
        "error",
        "failure",
        "hotfix",
        "critical",
        "production issue",
        "outage",
        "fix",
    ]
    if matches_pattern(defect_keywords):
        return "Defect"

    risk_keywords = [
        "spike",
        "investigation",
        "investigate",
        "research",
        "explore",
        "exploratory",
        "proof of concept",
        "poc",
        "experiment",
        "experimental",
        "prototype",
        "feasibility",
        "evaluation",
        "evaluate",
        "question",
        "inquiry",
        "discovery",
        "discover",
        "analysis",
        "analyze",
        "migration",
        "migrate",
        "dependency upgrade",
        "framework upgrade",
        "architecture decision",
        "adr",
        "design decision",
        "trade-off",
    ]
    if matches_pattern(risk_keywords):
        return "Risk"

    tech_debt_keywords = [
        "tech debt",
        "technical debt",
        "refactor",
        "refactoring",
        "cleanup",
        "clean up",
        "maintenance",
        "maintain",
        "optimization",
        "optimize",
        "performance",
        "security",
        "compliance",
        "infrastructure",
        "tooling",
        "automation",
        "automate",
        "ci/cd",
        "dependency",
        "dependencies",
        "library update",
        "package update",
        "version bump",
        "upgrade",
        "code quality",
        "documentation",
        "document",
        "test coverage",
        "testing",
        "linting",
        "chore",
        "improvement",
        "improve",
        "task",
    ]
    if matches_pattern(tech_debt_keywords):
        return "Technical Debt"

    feature_keywords = [
        "story",
        "user story",
        "epic",
        "feature",
        "enhancement",
        "capability",
        "requirement",
        "functionality",
        "development",
        "new",
        "add",
        "implement",
        "create",
        "build",
    ]
    if matches_pattern(feature_keywords):
        return "Feature"

    return "Feature"


def _map_issue_types(
    issue_types: list[dict], auto_detected: dict
) -> tuple[dict[str, list[str]], list[str]]:

    mappings = {"Feature": [], "Defect": [], "Technical Debt": [], "Risk": []}
    devops_types = []

    categorized = set()

    available_types = [it.get("name", "") for it in issue_types if it.get("name")]
    logger.info(f"[AutoConfigure] Available issue types in project: {available_types}")

    if auto_detected.get("issue_types"):
        detected = auto_detected["issue_types"]

        for devops_type in detected.get("devops_task_types", []):
            if devops_type and devops_type not in categorized:
                devops_types.append(devops_type)
                mappings["Technical Debt"].append(devops_type)
                categorized.add(devops_type)
                logger.info(
                    f"[AutoConfigure] Auto-detected '{devops_type}' → "
                    "DevOps (DORA) + Technical Debt (Flow)"
                )

        for bug_type in detected.get("bug_types", []):
            if bug_type and bug_type not in categorized:
                mappings["Defect"].append(bug_type)
                categorized.add(bug_type)

        for task_type in detected.get("task_types", []):
            if task_type and task_type not in categorized:
                mappings["Technical Debt"].append(task_type)
                categorized.add(task_type)

        for story_type in detected.get("story_types", []):
            if story_type and story_type not in categorized:
                mappings["Feature"].append(story_type)
                categorized.add(story_type)

        logger.info("[AutoConfigure] Using auto-detected issue types from metadata")
        logger.info(
            f"[AutoConfigure] Categorized {len(categorized)} types from auto-detection"
        )
        logger.info(f"[AutoConfigure] DevOps types from auto-detection: {devops_types}")

    for issue_type in issue_types:
        type_name = issue_type.get("name", "")
        type_lower = type_name.lower()

        if type_name in categorized:
            logger.debug(
                f"[AutoConfigure] Skipping '{type_name}' - already categorized"
            )
            continue

        logger.debug(
            f"[AutoConfigure] Analyzing issue type: '{type_name}' "
            f"(lowercase: '{type_lower}')"
        )
        category = _semantic_categorize_issue_type(type_lower)

        if category == "DevOps":
            devops_types.append(type_name)
            mappings["Technical Debt"].append(type_name)
            categorized.add(type_name)
            logger.info(
                f"[AutoConfigure] '{type_name}' → DevOps "
                "(DORA Deployment Frequency) + Technical Debt (Flow)"
            )
        else:
            mappings[category].append(type_name)
            categorized.add(type_name)

            if category == "Feature":
                logger.debug(
                    f"[AutoConfigure] '{type_name}' → Feature (new capability)"
                )
            elif category == "Risk":
                logger.info(
                    f"[AutoConfigure] '{type_name}' → Risk (exploratory/uncertain work)"
                )
            elif category == "Technical Debt":
                logger.info(
                    f"[AutoConfigure] '{type_name}' → Technical Debt "
                    "(maintenance/improvement)"
                )

    logger.info(
        f"[AutoConfigure] Issue type distribution: "
        f"Feature={len(mappings['Feature'])}, "
        f"Defect={len(mappings['Defect'])}, "
        f"TechnicalDebt={len(mappings['Technical Debt'])}, "
        f"Risk={len(mappings['Risk'])}, "
        f"DevOps={len(devops_types)}"
    )

    if len(devops_types) == 0:
        logger.info(
            "[AutoConfigure] No DevOps task types detected. "
            "This is normal if the project doesn't use dedicated issue "
            "types for deployments (e.g., deployments tracked via "
            "different mechanisms like git tags, CI/CD pipelines, or "
            "status transitions)."
        )
    else:
        logger.info(f"[AutoConfigure] DevOps task types found: {devops_types}")

    return mappings, devops_types


def _extract_field_values(
    issues: list[dict], field_detections: dict[str, str]
) -> dict[str, list[str]]:

    field_values = {}

    if "effort_category" in field_detections:
        effort_field = field_detections["effort_category"]
        effort_values = set()

        for issue in issues:
            value = issue.get("fields", {}).get(effort_field)
            if value:
                if isinstance(value, dict):
                    effort_values.add(value.get("value", ""))
                elif isinstance(value, str):
                    effort_values.add(value)

        if effort_values:
            field_values["effort_category"] = sorted(v for v in effort_values if v)
            logger.info(
                f"[AutoConfigure] Extracted "
                f"{len(field_values['effort_category'])} effort category values"
            )

    if "target_environment" in field_detections:
        env_field = field_detections["target_environment"]
        env_values = set()

        java_class_patterns = [
            "com.atlassian",
            "java.lang",
            "beans.",
            "Summary/ItemBean",
            "BranchOverall",
            "DeploymentOverall",
            "PullRequestOverall",
            "RepositoryOverall",
        ]

        for issue in issues:
            value = issue.get("fields", {}).get(env_field)
            if value:
                extracted_value = None
                if isinstance(value, dict):
                    extracted_value = value.get("value", "")
                elif isinstance(value, str):
                    extracted_value = value

                if extracted_value and not any(
                    pattern in extracted_value for pattern in java_class_patterns
                ):
                    env_values.add(extracted_value)

        if env_values:
            field_values["target_environment"] = sorted(v for v in env_values if v)
            logger.info(
                f"[AutoConfigure] Extracted "
                f"{len(field_values['target_environment'])} environment values"
            )

    return field_values


def _extract_projects_from_jql(jql_query: str, projects: list[dict]) -> list[str]:

    import re  # noqa: PLC0415

    if not jql_query:
        return []

    available_keys = {p.get("key", "") for p in projects}
    extracted = []

    single_match = re.search(
        r'project\s*=\s*["\']?(\w+)["\']?', jql_query, re.IGNORECASE
    )
    if single_match:
        key = single_match.group(1)
        if key in available_keys:
            extracted.append(key)
            logger.info(f"[AutoConfigure] Extracted project from JQL (single): {key}")

    list_match = re.search(r"project\s+in\s*\(([^)]+)\)", jql_query, re.IGNORECASE)
    if list_match:
        keys_str = list_match.group(1)
        keys = [k.strip().strip('"').strip("'") for k in keys_str.split(",")]
        valid_keys = [k for k in keys if k in available_keys]
        extracted.extend(valid_keys)
        logger.info(f"[AutoConfigure] Extracted projects from JQL (list): {valid_keys}")

    return list(set(extracted))
