"""Auto-configuration for JIRA mappings.

Generates smart defaults for profile configuration based on JIRA metadata.
Maps JIRA status categories, issue types, and field values to application requirements.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from data.field_detector import detect_fields_from_issues

logger = logging.getLogger(__name__)


def generate_smart_defaults(
    metadata: Dict[str, Any],
    jql_query: Optional[str] = None,
    issues: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Generate smart default configuration from JIRA metadata.

    Automatically maps JIRA statuses, issue types, and projects to profile configuration
    based on JIRA conventions and best practices.

    Field Mapping Strategy (Namespace Syntax):
    - Uses changelog-based extraction for date fields via namespace syntax
    - Example: "status:In Progress.DateTime" extracts timestamp when status changed
    - Standard fields (created, resolutiondate, issuetype) used directly
    - Custom fields detected and added for optional enhancements

    Default Field Mappings (DORA):
    - deployment_date: status:{completion_status}.DateTime
    - code_commit_date: status:{flow_start_status}.DateTime
    - incident_detected_at: created
    - incident_resolved_at: resolutiondate
    - severity_level: priority
    - deployment_successful: (detected from issues if available)
    - change_failure: (detected from issues if available)
    - affected_environment: (detected from issues if available)
    - target_environment: (detected from issues if available)

    Default Field Mappings (Flow):
    - flow_item_type: issuetype
    - status: status
    - completed_date: resolutiondate
    - effort_category: (detected from issues if available)

    Note: Flow Time uses flow_start_statuses and flow_end_statuses lists
    from project_classification to find status transitions in changelog.

    Args:
        metadata: JIRA metadata dictionary with keys:
            - statuses: List of status dicts with 'name', 'statusCategory' keys
            - issue_types: List of issue type dicts with 'name' key
            - projects: List of project dicts with 'key', 'name' keys
            - fields: List of custom field dicts
        jql_query: Optional JQL query string to extract project filter
        issues: Optional list of recent JIRA issues for field detection

    Returns:
        Dict with auto-configured profile settings:
            {
                "project_classification": {
                    "flow_end_statuses": [...],
                    "active_statuses": [...],
                    "flow_start_statuses": [...],
                    "wip_statuses": [...],
                    "development_projects": [...],
                    "devops_projects": []
                },
                "flow_type_mappings": {
                    "Feature": [...],
                    "Defect": [...],
                    "TechnicalDebt": [...],
                    "Risk": []
                },
                "field_mappings": {
                    "dora": {
                        "deployment_date": "status:Done.DateTime",
                        "code_commit_date": "status:In Progress.DateTime",
                        ...
                    },
                    "general": {
                        "completed_date": "resolutiondate",  # OR "resolved" for Apache JIRA/JIRA Server
                        "created_date": "created",
                        "updated_date": "updated",
                    },
                    "flow": {
                        "flow_item_type": "issuetype",
                        ...
                    }
                },
                "points_field": "customfield_XXXXX"  # Stored separately for jira_config
            }
    """
    logger.info("[AutoConfigure] Generating smart defaults from JIRA metadata")

    # Extract components from metadata
    statuses = metadata.get("statuses", [])
    issue_types = metadata.get("issue_types", [])
    projects = metadata.get("projects", [])
    auto_detected = metadata.get("auto_detected", {})

    # Initialize defaults structure
    # Type: Dict can contain nested dicts (field_mappings), lists (project_classification), or strings (points_field)
    defaults: Dict[str, Any] = {
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

    # 1. Map statuses by category
    flow_end_statuses, active_statuses, wip_statuses = _map_statuses_by_category(
        statuses, auto_detected
    )
    defaults["project_classification"]["flow_end_statuses"] = flow_end_statuses
    defaults["project_classification"]["active_statuses"] = active_statuses
    defaults["project_classification"]["wip_statuses"] = wip_statuses

    # Flow start statuses = subset of WIP (typically "In Progress" or first WIP status)
    defaults["project_classification"]["flow_start_statuses"] = (
        _select_flow_start_statuses(wip_statuses)
    )

    logger.info(
        f"[AutoConfigure] Mapped {len(flow_end_statuses)} completion, {len(active_statuses)} active, {len(wip_statuses)} WIP statuses"
    )

    # 2. Map issue types to flow categories AND extract DevOps types
    flow_type_mappings, devops_task_types = _map_issue_types(issue_types, auto_detected)
    defaults["flow_type_mappings"] = flow_type_mappings

    # Extract bug_types from Defect category for incident tracking
    defaults["project_classification"]["bug_types"] = flow_type_mappings.get(
        "Defect", []
    )

    # Use DevOps task types from semantic analysis (for DORA Deployment Frequency)
    defaults["project_classification"]["devops_task_types"] = devops_task_types
    logger.info(
        f"[AutoConfigure] DevOps task types (DORA Deployment Frequency): {devops_task_types}"
    )

    logger.info(
        f"[AutoConfigure] Mapped issue types: Feature={len(flow_type_mappings['Feature'])}, Defect={len(flow_type_mappings['Defect'])}, TechnicalDebt={len(flow_type_mappings['Technical Debt'])}"
    )
    logger.info(
        f"[AutoConfigure] Incident types (bug_types): {defaults['project_classification']['bug_types']}"
    )

    # 3. Extract projects from JQL query (if provided)
    if jql_query:
        development_projects = _extract_projects_from_jql(jql_query, projects)
        defaults["project_classification"]["development_projects"] = (
            development_projects
        )
        logger.info(
            f"[AutoConfigure] Extracted {len(development_projects)} projects from JQL: {development_projects}"
        )
    else:
        logger.info(
            "[AutoConfigure] No JQL query provided, skipping project extraction"
        )

    # 4. Map fields using namespace syntax for changelog-based extraction
    # Custom field detection is OPTIONAL - only override if we find something better
    field_mappings: Dict[str, Any] = {}

    # Get flow start and completion statuses for namespace syntax
    # Flow start = typically "In Progress" or first WIP status
    flow_start_status = (
        defaults["project_classification"]["flow_start_statuses"][0]
        if defaults["project_classification"]["flow_start_statuses"]
        else "In Progress"
    )

    # Completion status = first completion status (typically "Done")
    completion_status = flow_end_statuses[0] if flow_end_statuses else "Done"

    # === DORA METRICS: Use namespace syntax for changelog-based extraction ===
    dora_mappings = {
        # Deployment Date: When work was deployed (completion status transition)
        # Namespace: status:Done.DateTime - extracts timestamp when status changed to Done
        "deployment_date": f"status:{completion_status}.DateTime",
        # Code Commit Date: When development started (flow start status transition)
        # Namespace: status:In Progress.DateTime - extracts timestamp when work began
        "code_commit_date": f"status:{flow_start_status}.DateTime",
        # Incident Detected At: When the incident was created
        # Standard field - always available in JIRA
        "incident_detected_at": "created",
        # Incident Resolved At: When the incident was resolved
        # Standard field - always available for resolved issues
        "incident_resolved_at": "resolutiondate",
        # Severity Level: Priority/severity of the issue
        # Standard field - available in all JIRA instances
        "severity_level": "priority",
    }

    # === GENERAL FIELDS: Standard fields used across all features ===
    general_mappings = {
        # Completion Date: When issue was resolved/completed
        # JIRA Cloud/Atlassian: "resolutiondate"
        # Apache JIRA/JIRA Server: "resolved"
        # Standard field - available in all JIRA instances (but name varies)
        "completed_date": "resolutiondate",  # Default to JIRA Cloud standard
        # Creation Date: When issue was created
        # Standard field - always "created" in all JIRA versions
        "created_date": "created",
        # Updated Date: When issue was last modified
        # Standard field - always "updated" in all JIRA versions
        "updated_date": "updated",
    }

    # === FLOW METRICS: Use standard fields (status lists are in project_classification) ===
    flow_mappings = {
        # Flow Item Type: Issue type classification
        # Standard field - always available in JIRA
        "flow_item_type": "issuetype",
        # Status: Current status (for WIP calculations)
        # Standard field - always available
        "status": "status",
        # NOTE: completed_date moved to general_mappings (used by velocity, budget, flow metrics)
    }

    logger.info(
        "[AutoConfigure] Flow metrics use status lists from project_classification: "
        "flow_start_statuses, flow_end_statuses (configured separately)"
    )

    # === OPTIONAL: Detect custom fields to ADD to mappings (not override) ===
    # These are fields that may have dedicated custom fields in some JIRA instances
    if issues:
        logger.info(
            f"[AutoConfigure] Analyzing {len(issues)} issues for custom field detection (optional enhancements)"
        )
        field_detections = detect_fields_from_issues(issues, metadata)

        # Add detected custom fields for DORA metrics (optional enhancements)
        optional_dora_fields = [
            (
                "deployment_successful",
                "deployment_successful",
            ),  # Checkbox: deployment success
            ("change_failure", "change_failure"),  # Select: deployment result
            ("target_environment", "target_environment"),  # Select: deployment target
            (
                "affected_environment",
                "target_environment",
            ),  # Reuse same field for incidents
        ]

        for field_name, detection_key in optional_dora_fields:
            if detection_key in field_detections:
                dora_mappings[field_name] = field_detections[detection_key]
                logger.info(
                    f"[AutoConfigure] Found custom {field_name} field - using {field_detections[detection_key]}"
                )

        # Add detected custom fields for Flow metrics (optional enhancements)
        optional_flow_fields = [
            ("effort_category", "effort_category"),  # Select: work classification
        ]

        for field_name, detection_key in optional_flow_fields:
            if detection_key in field_detections:
                flow_mappings[field_name] = field_detections[detection_key]
                logger.info(
                    f"[AutoConfigure] Found custom {field_name} field - using {field_detections[detection_key]}"
                )

        # Store points field for Estimate mapping (General Fields)
        if "points_field" in field_detections:
            defaults["points_field"] = field_detections["points_field"]
            general_mappings["estimate"] = field_detections["points_field"]
            logger.info(
                f"[AutoConfigure] Detected points field: {field_detections['points_field']}"
            )

        # Extract field values for dropdowns (effort_category, affected_environment)
        field_values = _extract_field_values(issues, field_detections)
        if field_values:
            defaults["field_values"] = field_values
            logger.info(
                f"[AutoConfigure] Extracted field values: {list(field_values.keys())}"
            )
    else:
        logger.info(
            "[AutoConfigure] No custom field detection (no issues provided). Using namespace syntax only."
        )

    # Always store field_mappings (standard fields + any detected custom overrides)
    field_mappings["general"] = general_mappings
    field_mappings["dora"] = dora_mappings
    field_mappings["flow"] = flow_mappings
    defaults["field_mappings"] = field_mappings

    logger.info(
        f"[AutoConfigure] Field mappings configured: "
        f"{len(general_mappings)} General fields, {len(dora_mappings)} DORA fields, {len(flow_mappings)} Flow fields"
    )

    return defaults


def _map_statuses_by_category(
    statuses: List[Dict], auto_detected: Dict
) -> tuple[List[str], List[str], List[str]]:
    """Map JIRA statuses to completion, active, and WIP categories.

    Uses JIRA status categories as primary source:
    - "done" category → flow_end_statuses
    - "indeterminate" category → active_statuses + wip_statuses
    - "new" category → typically not used for metrics

    Args:
        statuses: List of status dicts with 'name' and 'statusCategory' keys
        auto_detected: Auto-detected configurations from metadata

    Returns:
        Tuple of (flow_end_statuses, active_statuses, wip_statuses)
    """
    flow_end_statuses = []
    active_statuses = []
    wip_statuses = []

    # Use auto-detected if available (already categorized by metadata fetcher)
    if auto_detected.get("statuses"):
        detected = auto_detected["statuses"]
        flow_end_statuses = detected.get("flow_end_statuses", [])
        active_statuses = detected.get("active_statuses", [])
        wip_statuses = detected.get("wip_statuses", [])

        logger.info("[AutoConfigure] Using auto-detected statuses from metadata")
        return flow_end_statuses, active_statuses, wip_statuses

    # Fallback: Manual categorization by status category key
    for status in statuses:
        status_name = status.get("name", "")
        category = status.get("statusCategory", {})
        category_key = category.get("key", "").lower()

        if category_key == "done":
            # Done category = completion statuses
            flow_end_statuses.append(status_name)
        elif category_key == "indeterminate":
            # Indeterminate = active work
            active_statuses.append(status_name)
            # Also add to WIP unless it's a waiting/blocked status
            if not any(
                keyword in status_name.lower()
                for keyword in ["wait", "block", "hold", "pending"]
            ):
                wip_statuses.append(status_name)
        # "new" category (To Do, Backlog) - not used for metrics

    logger.info("[AutoConfigure] Manually categorized statuses by JIRA category")
    return flow_end_statuses, active_statuses, wip_statuses


def _select_flow_start_statuses(wip_statuses: List[str]) -> List[str]:
    """Select flow start statuses from WIP list.

    Flow start = when work actually begins (not just "selected" or "ready").
    Looks for "In Progress" or similar keywords.

    Args:
        wip_statuses: List of WIP status names

    Returns:
        List of flow start status names (subset of wip_statuses)
    """
    if not wip_statuses:
        return []

    # Priority order: "In Progress" > "In Development" > first WIP status
    start_keywords = ["in progress", "in dev", "progress", "developing"]

    for keyword in start_keywords:
        matching = [s for s in wip_statuses if keyword in s.lower()]
        if matching:
            logger.info(
                f"[AutoConfigure] Selected flow start status: {matching[0]} (matched '{keyword}')"
            )
            return [matching[0]]

    # Fallback: Use first WIP status
    if wip_statuses:
        logger.info(
            f"[AutoConfigure] Using first WIP status as flow start: {wip_statuses[0]}"
        )
        return [wip_statuses[0]]

    return []


def _semantic_categorize_issue_type(type_name_lower: str) -> str:
    """Semantically categorize issue type using pattern matching with word boundaries.

    Categories represent work intent and risk profile:
    - DevOps: Deployment, release, production changes (DORA Deployment Frequency)
    - Defect: Production issues, bugs, incidents (reactive work)
    - Technical Debt: Maintenance, refactoring, upgrades (reducing future cost)
    - Risk: Exploratory, uncertain outcomes, learning (high uncertainty)
    - Feature: New capabilities, enhancements (planned value delivery)

    Uses regex word boundaries to avoid false positives:
    - "task" matches "Task" but not "multitasking"
    - "upgrade" matches "Dependency Upgrade" but not "upgraded"

    Args:
        type_name_lower: Issue type name in lowercase

    Returns:
        Category name: "DevOps", "Feature", "Defect", "Technical Debt", or "Risk"
    """

    def matches_pattern(keywords):
        """Check if any keyword pattern matches with word boundaries."""
        for keyword in keywords:
            # Multi-word phrases: exact substring match
            if " " in keyword:
                if keyword in type_name_lower:
                    return True
            # Single words: word boundary match (avoid false positives)
            else:
                # Word boundary pattern: \b ensures whole word match
                if re.search(rf"\b{re.escape(keyword)}\b", type_name_lower):
                    return True
        return False

    # PRIORITY 0: DevOps/Deployment tasks (required for DORA Deployment Frequency)
    devops_keywords = [
        # Deployment and release (root words match variations)
        "deploy",
        "deployment",
        "release",
        "rollout",
        "publish",
        "go-live",
        "production release",
        "hotfix deploy",
        # Operations (catches "operation", "operations", "operational task", "ops task")
        "operation",
        "operational",
        "ops",
        # CI/CD specific
        "cd",
        "continuous deployment",
        "pipeline deploy",
        "automated deploy",
        # Environment promotion
        "promote to production",
        "production push",
        "prod deploy",
    ]
    if matches_pattern(devops_keywords):
        return "DevOps"

    # PRIORITY 1: Defects (production issues - highest priority)
    defect_keywords = [
        # Root words (matches "bug", "bug task", "bugfix")
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
        # Variations
        "fix",  # Catches "fix", "hotfix", "bugfix"
    ]
    if matches_pattern(defect_keywords):
        return "Defect"

    # PRIORITY 2: Risk (exploratory, uncertain, learning work)
    risk_keywords = [
        # Explicit risk/exploration (root words catch variations)
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
        # Questions and unknowns
        "question",
        "inquiry",
        "discovery",
        "discover",
        "analysis",
        "analyze",
        # High-uncertainty changes
        "migration",
        "migrate",
        "dependency upgrade",  # Multi-word phrase
        "framework upgrade",  # Multi-word phrase
        # Architecture decisions
        "architecture decision",
        "adr",
        "design decision",
        "trade-off",
    ]
    if matches_pattern(risk_keywords):
        return "Risk"

    # PRIORITY 3: Technical Debt (maintenance, improvement, paying down debt)
    tech_debt_keywords = [
        # Explicit debt/maintenance (root words catch variations)
        "tech debt",
        "technical debt",
        "refactor",
        "refactoring",
        "cleanup",
        "clean up",
        "maintenance",
        "maintain",
        # System improvements
        "optimization",
        "optimize",
        "performance",
        "security",
        "compliance",
        # Infrastructure and tooling
        "infrastructure",
        "tooling",
        "automation",
        "automate",
        "ci/cd",
        # Dependencies and upgrades (routine)
        "dependency",
        "dependencies",
        "library update",
        "package update",
        "version bump",
        "upgrade",
        # Code quality
        "code quality",
        "documentation",
        "document",
        "test coverage",
        "testing",
        "linting",
        # Generic tasks (checked last - often maintenance work)
        "chore",
        "improvement",
        "improve",
        "task",  # Last resort - catches generic "Task" type
    ]
    if matches_pattern(tech_debt_keywords):
        return "Technical Debt"

    # PRIORITY 4: Features (planned value delivery)
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

    # DEFAULT: Uncategorized types become Features
    return "Feature"


def _map_issue_types(
    issue_types: List[Dict], auto_detected: Dict
) -> tuple[Dict[str, List[str]], List[str]]:
    """Map JIRA issue types to Flow categories and identify DevOps task types.

    Issue types are mutually exclusive - each type belongs to exactly ONE category.
    DevOps task types are also identified for DORA Deployment Frequency metric.

    Priority order: Defect > Technical Debt > Risk > Feature

    Categorization rules:
    - Bug, Defect, Incident → Defect (highest priority - production issues)
    - Task, Tech Debt, Refactor, Improvement → Technical Debt
    - Spike, Investigation, Research → Risk
    - Story, Epic, Feature, Enhancement → Feature (default)
    - Deploy, Release, Deployment → DevOps (DORA Deployment Frequency)

    Args:
        issue_types: List of issue type dicts with 'name' key
        auto_detected: Auto-detected configurations from metadata

    Returns:
        Tuple of (flow_mappings_dict, devops_task_types_list)
    """
    mappings = {"Feature": [], "Defect": [], "Technical Debt": [], "Risk": []}
    devops_types = []

    # Track all categorized types to ensure mutual exclusivity
    categorized = set()

    # Log available issue types for debugging
    available_types = [it.get("name", "") for it in issue_types if it.get("name")]
    logger.info(f"[AutoConfigure] Available issue types in project: {available_types}")

    # Use auto-detected if available (prefer auto-detection for accuracy)
    if auto_detected.get("issue_types"):
        detected = auto_detected["issue_types"]

        # 0. DevOps types (DORA Deployment Frequency)
        # These are ALSO added to Technical Debt for Flow metrics
        for devops_type in detected.get("devops_task_types", []):
            if devops_type and devops_type not in categorized:
                devops_types.append(devops_type)
                mappings["Technical Debt"].append(devops_type)
                categorized.add(devops_type)
                logger.info(
                    f"[AutoConfigure] Auto-detected '{devops_type}' → DevOps (DORA) + Technical Debt (Flow)"
                )

        # 1. Defects (highest priority - production issues)
        for bug_type in detected.get("bug_types", []):
            if bug_type and bug_type not in categorized:
                mappings["Defect"].append(bug_type)
                categorized.add(bug_type)

        # 2. Technical Debt (tasks - but NOT devops, already handled above)
        for task_type in detected.get("task_types", []):
            if task_type and task_type not in categorized:
                mappings["Technical Debt"].append(task_type)
                categorized.add(task_type)

        # 3. Features (stories)
        for story_type in detected.get("story_types", []):
            if story_type and story_type not in categorized:
                mappings["Feature"].append(story_type)
                categorized.add(story_type)

        logger.info("[AutoConfigure] Using auto-detected issue types from metadata")
        logger.info(
            f"[AutoConfigure] Categorized {len(categorized)} types from auto-detection"
        )
        logger.info(f"[AutoConfigure] DevOps types from auto-detection: {devops_types}")

    # Semantic categorization for any unmapped types
    # Uses multi-keyword scoring to understand work intent and risk profile
    for issue_type in issue_types:
        type_name = issue_type.get("name", "")
        type_lower = type_name.lower()

        # Skip if already categorized
        if type_name in categorized:
            logger.debug(
                f"[AutoConfigure] Skipping '{type_name}' - already categorized"
            )
            continue

        # Score each category based on semantic meaning
        logger.debug(
            f"[AutoConfigure] Analyzing issue type: '{type_name}' (lowercase: '{type_lower}')"
        )
        category = _semantic_categorize_issue_type(type_lower)

        # Handle DevOps types specially - they populate both DevOps list and Technical Debt
        if category == "DevOps":
            devops_types.append(type_name)
            # DevOps tasks also count as Technical Debt for Flow metrics
            mappings["Technical Debt"].append(type_name)
            categorized.add(type_name)
            logger.info(
                f"[AutoConfigure] '{type_name}' → DevOps (DORA Deployment Frequency) + Technical Debt (Flow)"
            )
        else:
            # Regular Flow categories (mutually exclusive)
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
                    f"[AutoConfigure] '{type_name}' → Technical Debt (maintenance/improvement)"
                )

    # Log final distribution
    logger.info(
        f"[AutoConfigure] Issue type distribution: "
        f"Feature={len(mappings['Feature'])}, "
        f"Defect={len(mappings['Defect'])}, "
        f"TechnicalDebt={len(mappings['Technical Debt'])}, "
        f"Risk={len(mappings['Risk'])}, "
        f"DevOps={len(devops_types)}"
    )

    # Log details if DevOps types are empty (helps diagnose projects without deployment types)
    if len(devops_types) == 0:
        logger.info(
            "[AutoConfigure] No DevOps task types detected. This is normal if the project "
            "doesn't use dedicated issue types for deployments (e.g., deployments tracked "
            "via different mechanisms like git tags, CI/CD pipelines, or status transitions)."
        )
    else:
        logger.info(f"[AutoConfigure] DevOps task types found: {devops_types}")

    return mappings, devops_types


def _extract_field_values(
    issues: List[Dict], field_detections: Dict[str, str]
) -> Dict[str, List[str]]:
    """Extract unique values for detected fields (for dropdown population).

    Extracts values for:
    - effort_category: For Flow Type Classification dropdowns
    - target_environment: For Production Identifiers dropdown

    Args:
        issues: List of JIRA issues
        field_detections: Detected custom field IDs

    Returns:
        Dict mapping field names to lists of unique values
    """
    field_values = {}

    # Extract effort_category values
    if "effort_category" in field_detections:
        effort_field = field_detections["effort_category"]
        effort_values = set()

        for issue in issues:
            value = issue.get("fields", {}).get(effort_field)
            if value:
                # Handle both string and object values
                if isinstance(value, dict):
                    effort_values.add(value.get("value", ""))
                elif isinstance(value, str):
                    effort_values.add(value)

        if effort_values:
            field_values["effort_category"] = sorted(
                v for v in effort_values if v
            )  # Remove empty strings
            logger.info(
                f"[AutoConfigure] Extracted {len(field_values['effort_category'])} effort category values"
            )

    # Extract target_environment values (for production identifiers)
    if "target_environment" in field_detections:
        env_field = field_detections["target_environment"]
        env_values = set()

        # Java class patterns to filter out (from JIRA's Development panel field)
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
                # Handle both string and object values
                extracted_value = None
                if isinstance(value, dict):
                    extracted_value = value.get("value", "")
                elif isinstance(value, str):
                    extracted_value = value

                # Filter out Java class names (from JIRA's Development panel field)
                if extracted_value and not any(
                    pattern in extracted_value for pattern in java_class_patterns
                ):
                    env_values.add(extracted_value)

        if env_values:
            field_values["target_environment"] = sorted(v for v in env_values if v)
            logger.info(
                f"[AutoConfigure] Extracted {len(field_values['target_environment'])} environment values"
            )

    return field_values


def _extract_projects_from_jql(jql_query: str, projects: List[Dict]) -> List[str]:
    """Extract project keys from JQL query.

    Parses JQL for:
    - project = PROJ
    - project IN (PROJ1, PROJ2)
    - project in (PROJ1, PROJ2)

    Args:
        jql_query: JQL query string
        projects: List of available projects (for validation)

    Returns:
        List of project keys extracted from JQL
    """
    import re

    if not jql_query:
        return []

    # Available project keys for validation
    available_keys = {p.get("key", "") for p in projects}
    extracted = []

    # Pattern 1: project = KEY
    single_match = re.search(
        r'project\s*=\s*["\']?(\w+)["\']?', jql_query, re.IGNORECASE
    )
    if single_match:
        key = single_match.group(1)
        if key in available_keys:
            extracted.append(key)
            logger.info(f"[AutoConfigure] Extracted project from JQL (single): {key}")

    # Pattern 2: project IN (KEY1, KEY2, ...)
    list_match = re.search(r"project\s+in\s*\(([^)]+)\)", jql_query, re.IGNORECASE)
    if list_match:
        keys_str = list_match.group(1)
        # Parse comma-separated list, removing quotes and whitespace
        keys = [k.strip().strip('"').strip("'") for k in keys_str.split(",")]
        valid_keys = [k for k in keys if k in available_keys]
        extracted.extend(valid_keys)
        logger.info(f"[AutoConfigure] Extracted projects from JQL (list): {valid_keys}")

    # Deduplicate
    return list(set(extracted))
